================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   15 analyzed | ~950 lines de código

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 5 | LOW: 3

> Nota: o item marcado como "revisão" abaixo foi acrescentado numa segunda leitura, depois de rodar `seed.py` e reparar no warning de depreciação no console.

## Findings

### [CRITICAL] Hardcoded Credentials (SECRET_KEY)
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` fixo no código, apesar do projeto já ter `python-dotenv` nas dependências (requirements.txt:6) e nunca usar (nenhum `load_dotenv()` no projeto).
Impact: Qualquer pessoa com acesso ao repositório tem a chave usada para assinar sessão/cookies da aplicação.
Recommendation: Carregar via variável de ambiente com `python-dotenv`, já que a dependência já está instalada e simplesmente não é usada.

### [CRITICAL] Credenciais de SMTP hardcoded
File: services/notification_service.py:9-10
Description: `self.email_user = 'taskmanager@gmail.com'` e `self.email_password = 'senha123'` fixos no construtor de `NotificationService`.
Impact: Credencial real de e-mail exposta no repositório; qualquer um pode autenticar como esse remetente.
Recommendation: Mover para variáveis de ambiente lidas em um módulo de config.

### [CRITICAL] Hash de senha exposto nas respostas da API
File: models/user.py:16-25 (`to_dict` inclui `self.password` na linha 21); usado em routes/user_routes.py:86, 129 e 209
Description: O método `to_dict()` do model `User` devolve o campo `password` (o hash) junto com os demais dados, e é usado diretamente nas respostas de criação de usuário, atualização e login.
Impact: O hash da senha de qualquer usuário fica visível para quem tiver acesso à resposta HTTP (inclusive o próprio usuário autenticado vendo seus dados, ou um admin listando outros usuários caso o mesmo padrão se espalhe).
Recommendation: `to_dict()` nunca deve incluir o campo de senha; se necessário, criar um `to_public_dict()` separado sem esse campo.

### [CRITICAL] Token de autenticação previsível
File: routes/user_routes.py:207-211
Description: O login devolve `'token': 'fake-jwt-token-' + str(user.id)`: não é um JWT real, não é assinado, não expira e é trivialmente previsível a partir do ID do usuário.
Impact: Qualquer pessoa pode "autenticar-se" como qualquer usuário apenas montando a string `fake-jwt-token-<id>`, sem saber a senha.
Recommendation: Emitir um JWT real assinado (ex.: `PyJWT`) com expiração, ou outro mecanismo de sessão seguro.

### [HIGH] Hash de senha com MD5
File: models/user.py:27-32
Description: `set_password`/`check_password` usam `hashlib.md5(pwd.encode()).hexdigest()`, um algoritmo de hash rápido e quebrável por força bruta/rainbow table, não adequado para senhas.
Impact: Em caso de vazamento do banco, as senhas dos usuários podem ser recuperadas rapidamente.
Recommendation: Trocar por bcrypt (ou argon2/scrypt), conforme padrão 9 do playbook de refatoração.

### [HIGH] Lógica de negócio duplicada em vez de reutilizar o model
File: routes/task_routes.py:30-39, 71-80; routes/report_routes.py:32-44; routes/user_routes.py:171-180
Description: O cálculo de "task atrasada" (`due_date < agora` e `status not in (done, cancelled)`) está reimplementado manualmente em quatro lugares diferentes das rotas, apesar de `Task.is_overdue()` já existir e centralizar exatamente essa regra em `models/task.py:50-60`.
Impact: Qualquer mudança na regra de negócio (ex.: adicionar um novo status que conta como "concluído") precisa ser replicada manualmente em 4 pontos, com alto risco de ficar inconsistente.
Recommendation: Substituir todas as reimplementações por chamadas a `task.is_overdue()`.

### [HIGH] Validação de status/prioridade duplicada em vez de reutilizar o model
File: routes/task_routes.py:110-114, 177-184
Description: `create_task` e `update_task` reimplementam a checagem de status válido e prioridade válida inline, apesar de `Task.validate_status()` e `Task.validate_priority()` já existirem em `models/task.py:38-48` e nunca serem chamados em lugar nenhum do projeto.
Impact: As duas validações podem divergir com o tempo (ex.: alguém atualiza uma e esquece a outra), e o código do model fica morto.
Recommendation: Chamar `task.validate_status(...)`/`task.validate_priority(...)` a partir dos controllers em vez de duplicar a lista de valores válidos.

### [MEDIUM] Queries N+1
File: routes/task_routes.py:41-57 (busca `User`/`Category` dentro do loop de tasks); routes/report_routes.py:53-68 (busca tasks de cada usuário dentro do loop de usuários)
Description: Em ambos os casos, uma query adicional é disparada por iteração do loop em vez de usar `join`/eager loading do SQLAlchemy.
Impact: O tempo de resposta cresce proporcionalmente ao número de tasks/usuários, degradando com o crescimento da base.
Recommendation: Usar `db.joinedload` para trazer `user`/`category` junto da query principal, e agregações (`GROUP BY`) para as estatísticas por usuário.

### [MEDIUM] Módulo utilitário duplicado e não utilizado
File: utils/helpers.py (funções `validate_email`, `calculate_percentage`, `format_date`, `process_task_data`); dependências `marshmallow` e `requests` no requirements.txt nunca importadas em nenhum arquivo
Description: `report_routes.py:7` importa `format_date` e `calculate_percentage` de `utils/helpers.py`, mas nenhuma das duas é de fato chamada. O cálculo de porcentagem e formatação de data são refeitos manualmente inline. `validate_email` também existe em `utils/helpers.py:19-23` mas a validação de e-mail é reimplementada com a mesma regex diretamente em `user_routes.py:61` e `user_routes.py:106`.
Impact: Código utilitário morto que ninguém mantém junto da lógica real, e duplicação de regra (regex de e-mail) em dois lugares que podem divergir.
Recommendation: Ou usar de fato as funções de `utils/helpers.py` nas rotas, ou removê-las se não fizerem mais sentido. Nunca manter as duas versões (duplicada e não usada) ao mesmo tempo.

### [MEDIUM] Tratamento de erro genérico e disperso
File: routes/task_routes.py:62, 137, 204, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221
Description: Doze blocos `except:` (sem tipo de exceção, sem log) espalhados pelas três rotas, cada um formatando a resposta de erro de um jeito ligeiramente diferente.
Impact: Qualquer exceção inesperada é silenciada sem registro algum, dificultando diagnosticar problemas em produção; formato de erro inconsistente para quem consome a API.
Recommendation: Registrar um error handler central (`@app.errorhandler(Exception)`) e deixar as rotas propagarem a exceção em vez de capturá-la genericamente.

### [MEDIUM] CORS liberado sem restrição de origem
File: app.py:15
Description: `CORS(app)` aplicado sem nenhuma configuração de origem permitida.
Impact: Amplia a superfície de ataque de uma API que expõe dados de usuários (incluindo, como visto acima, hash de senha).
Recommendation: Restringir `CORS` às origens confiáveis via configuração explícita.

### [MEDIUM] API deprecated: `datetime.utcnow()` (achado de revisão)
File: models/task.py:15-16, 52; models/user.py:15; models/category.py:11; routes/task_routes.py:215; routes/report_routes.py:34,40,57,71; seed.py (múltiplas linhas)
Description: `datetime.utcnow()` é usado em todo o projeto (default de coluna, comparação de `overdue`, timestamps de relatório). Confirmado com evidência real: rodar `python seed.py` imprime `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version` no console (Python 3.12+).
Impact: Comportamento que hoje é só um aviso pode virar erro de execução em uma versão futura do Python, quebrando o boot da aplicação sem aviso prévio.
Recommendation: Trocar por `datetime.now(timezone.utc)` (ajustando para naive se o restante do código comparar com datas naive vindas do SQLite, como é o caso aqui).

### [LOW] Serviço de notificação nunca conectado à aplicação
File: services/notification_service.py:1-49
Description: A classe `NotificationService` (com `notify_task_assigned`, `notify_task_overdue`) existe mas não é importada nem instanciada em nenhuma rota do projeto. A funcionalidade de notificação simplesmente não roda.
Impact: Funcionalidade aparentemente planejada nunca é exercitada; fica como código morto que pode confundir quem for dar manutenção.
Recommendation: Conectar o serviço ao fluxo de criação/atualização de task, ou remover se não fizer mais parte do escopo.

### [LOW] Imports não utilizados
File: routes/task_routes.py:7 (`os, sys, time` nunca usados); routes/report_routes.py:8 (`json` nunca usado)
Description: Módulos importados no topo do arquivo sem nenhum uso no corpo do código.
Impact: Ruído para quem lê o arquivo tentando entender as dependências reais.
Recommendation: Remover os imports não utilizados.

### [LOW] Verbosidade desnecessária em métodos booleanos
File: models/user.py:34-38 (`is_admin`); models/task.py:38-48 (`validate_status`, `validate_priority`)
Description: Métodos que retornam `True`/`False` usando `if/else` explícito em vez de retornar a expressão booleana diretamente (ex.: `return self.role == 'admin'`).
Impact: Não é um bug, mas adiciona linhas sem necessidade e reduz a legibilidade.
Recommendation: Simplificar para retorno direto da expressão booleana.

================================
Total: 15 findings
================================
