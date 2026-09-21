================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 4 | LOW: 4

> Nota: os itens marcados como "revisão" abaixo foram acrescentados numa segunda leitura, depois da primeira versão deste relatório.

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-315
Description: Um único arquivo concentra todo o acesso a dados e regra de negócio de três domínios diferentes (produtos, usuários, pedidos), incluindo cálculo de total de pedido, controle de estoque e geração de relatório de vendas.
Impact: Impossível testar cada domínio isoladamente; qualquer alteração em um domínio corre o risco de quebrar os outros dois.
Recommendation: Separar em `models/produto_model.py`, `models/usuario_model.py` e `models/pedido_model.py`, cada um cuidando apenas do seu domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:7
Description: `SECRET_KEY` fixo no código-fonte (`"minha-chave-super-secreta-123"`). O mesmo valor ainda é devolvido em texto puro pelo endpoint `/health` (controllers.py:289).
Impact: Qualquer pessoa com acesso ao repositório, ou que chame `/health`, obtém a chave usada para assinar sessões/tokens da aplicação.
Recommendation: Mover para variável de ambiente lida em `config/settings.py`, nunca devolver a chave em uma resposta HTTP.

### [CRITICAL] SQL Injection
File: models.py:28, 43-50, 58-61, 68, 92, 109-111, 126-129, 140, 149-151, 155-166, 174, 188, 192, 206, 220, 224, 280, 289-297
Description: Praticamente todas as queries do arquivo são montadas por concatenação de string com dados vindos direto da requisição (ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` em `login_usuario`, linha 109-111).
Impact: Um atacante pode manipular parâmetros como `email`, `nome` ou `termo` de busca para ler, alterar ou apagar dados arbitrários do banco, incluindo bypass de login.
Recommendation: Trocar toda concatenação por placeholders (`?`) com parâmetros bindados, conforme padrão 3 do playbook de refatoração.

### [CRITICAL] Endpoints administrativos sem autenticação
File: app.py:47-78
Description: `/admin/reset-db` apaga todas as tabelas do banco e `/admin/query` executa qualquer SQL enviado no corpo da requisição (`dados.get("sql", "")` seguido de `cursor.execute(query)`), ambos sem nenhuma checagem de autenticação/autorização.
Impact: Qualquer requisição não autenticada pode destruir o banco de produção ou executar comandos SQL arbitrários.
Recommendation: Remover o endpoint de execução de SQL livre; proteger o reset com autenticação de administrador e restringir a ambientes de desenvolvimento.

### [HIGH] Estado global mutável para conexão de banco
File: database.py:4-11
Description: `db_connection` é uma variável global de módulo, alterada via `global db_connection` dentro de `get_db()`.
Impact: Qualquer parte do código pode alterar o estado da conexão de forma implícita; dificulta testes isolados e reuso da conexão de forma controlada.
Recommendation: Encapsular a conexão em uma classe/factory de configuração injetada onde for necessária, em vez de depender de estado global de módulo.

### [HIGH] Acoplamento forte sem injeção de dependência
File: models.py:5-6 (padrão repetido em todas as funções do arquivo)
Description: Toda função de acesso a dados chama `get_db()` diretamente, importado de `database.py`, em vez de receber a conexão/repositório como parâmetro.
Impact: Impossível substituir a fonte de dados em testes automatizados sem monkeypatch; qualquer mudança na forma de conectar exige editar todas as funções.
Recommendation: Receber a conexão (ou um repositório) como parâmetro/injeção na camada de model.

### [HIGH] Debug habilitado e dados sensíveis expostos no health check
File: app.py:8, 88; controllers.py:264-292
Description: `app.config["DEBUG"] = True` e `app.run(..., debug=True)` ficam ativos incondicionalmente, e o endpoint `/health` devolve `"debug": True`, `"db_path": "loja.db"` e a própria `secret_key` no JSON de resposta.
Impact: Em produção, debug ligado expõe stack traces detalhados ao cliente e um endpoint público revela informações internas da infraestrutura.
Recommendation: Ler `DEBUG` de variável de ambiente com default `False`, remover dados sensíveis do payload de health check.

### [HIGH] Efeitos colaterais de notificação hardcoded no controller
File: controllers.py:208-210, 247-250
Description: O controller de pedidos imprime diretamente mensagens simulando envio de e-mail, SMS e push (`print("ENVIANDO EMAIL: ...")`) e decide regras de notificação por status inline, sem nenhuma camada de serviço.
Impact: Lógica de notificação misturada ao fluxo HTTP; impossível trocar o canal de notificação ou testar essa regra sem subir a rota inteira.
Recommendation: Extrair para um serviço de notificação dedicado, chamado pelo model/controller após a operação de negócio.

### [MEDIUM] Queries N+1 ao montar pedidos
File: models.py:171-201, 203-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` fazem um loop por pedido, dentro dele um loop por item do pedido, e para cada item uma nova query para buscar o nome do produto (`cursor3.execute("SELECT nome FROM produtos WHERE id = " + ...)`).
Impact: O número de queries cresce proporcionalmente a pedidos × itens; em um catálogo grande isso degrada a performance rapidamente.
Recommendation: Buscar os nomes de produto em lote com `WHERE id IN (...)` ou usar JOIN entre pedidos, itens_pedido e produtos.

### [MEDIUM] Validação inconsistente entre criar e atualizar produto
File: controllers.py:24-58, 64-96
Description: `criar_produto` valida tamanho do nome (2-200 caracteres) e categoria contra uma lista de categorias válidas; `atualizar_produto` recebe os mesmos campos mas não repete nenhuma dessas duas validações.
Impact: É possível atualizar um produto para um nome inválido ou categoria inexistente, mesmo que a criação bloqueie isso.
Recommendation: Extrair a validação para uma função compartilhada usada por ambos os endpoints.

### [MEDIUM] CORS liberado sem restrição de origem
File: app.py:9
Description: `CORS(app)` é aplicado sem nenhuma configuração de origem permitida, liberando qualquer domínio a chamar a API.
Impact: Amplia desnecessariamente a superfície de ataque para uma API que já expõe dados de usuários e permite login.
Recommendation: Restringir `CORS` às origens confiáveis via configuração explícita.

### [MEDIUM] Falta de validação na criação de pedido (achado de revisão)
File: controllers.py:188-220 (função `criar_pedido`); models.py:133-169
Description: O corpo de `/pedidos` é aceito sem checar se cada item tem `produto_id`/`quantidade` do tipo certo, nem se `quantidade` é positiva. Um item malformado (ex.: `quantidade` negativa ou ausente) chega direto no model.
Impact: `quantidade` negativa gera total negativo e incremento de estoque em vez de decremento (`estoque - quantidade` com quantidade negativa soma estoque); item sem `produto_id`/`quantidade` derruba a request com um 500 genérico em vez de um erro de validação claro.
Recommendation: Validar a forma de cada item (tipo inteiro, quantidade > 0) antes de chamar o model.

### [LOW] `print` como estratégia de log
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: Toda a observabilidade da aplicação depende de `print`, inclusive para registrar erros (`print("ERRO: " + str(e))`).
Impact: Sem níveis de log, sem destino configurável, difícil de correlacionar com uma requisição específica em produção.
Recommendation: Substituir por um logger configurável (`logging` no Python) com níveis apropriados.

### [LOW] Magic numbers na regra de desconto e validação
File: controllers.py:47-50; models.py:256-262
Description: Limites de tamanho de nome (`2`, `200`) e faixas de desconto por faturamento (`10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02`) estão soltos como literais no meio da lógica.
Impact: Dificulta entender e alterar a regra de negócio de forma consistente; o mesmo limite pode precisar ser mudado em vários lugares.
Recommendation: Extrair para constantes nomeadas em um módulo de configuração/regras de negócio.

### [LOW] Variável `id` sombreando builtin do Python
File: controllers.py:56, 64
Description: A variável local `id` (ex.: `id = models.criar_produto(...)`) sombreia a função builtin `id()` do Python dentro do mesmo escopo.
Impact: Reduz a legibilidade e pode confundir quem for dar manutenção, embora não cause erro funcional neste caso.
Recommendation: Renomear para `produto_id`.

### [LOW] Construção de dicionário duplicada em 3 funções (achado de revisão)
File: models.py:9-22, 30-41, 301-314
Description: `get_todos_produtos`, `get_produto_por_id` e `buscar_produtos` reconstroem manualmente o mesmo dicionário de produto (`id`, `nome`, `descricao`, `preco`, `estoque`, `categoria`, `ativo`, `criado_em`) linha por linha, em vez de reaproveitar uma função só.
Impact: Qualquer mudança no formato do produto (adicionar/remover campo) precisa ser replicada em 3 lugares.
Recommendation: Extrair para uma função `_row_to_dict` única, reaproveitada pelas três funções.
Status: já corrigido como efeito colateral da Fase 3. `src/models/produto_model.py` já nasceu com `_row_to_dict` único, sem precisar de mudança adicional.

================================
Total: 16 findings
================================
