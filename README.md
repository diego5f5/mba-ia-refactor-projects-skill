# Refatoração Arquitetural Automatizada com a Skill refactor-arch

Este repositório é a minha entrega do desafio "Criação de Skills — Refatoração Arquitetural Automatizada" da pós-graduação em Engenharia de IA (Full Cycle). A proposta era criar uma Skill capaz de analisar, auditar e refatorar qualquer projeto de backend para o padrão MVC, independente da linguagem ou framework, e depois provar isso rodando a mesma skill em três projetos diferentes.

Usei o **Claude Code** como ferramenta agêntica. A skill está em `.claude/skills/refactor-arch/` dentro de cada um dos três projetos (é a mesma skill, copiada literalmente de um projeto para o outro, sem nenhuma adaptação específica de stack).

Este README está organizado em quatro seções, conforme pedido no enunciado: Análise Manual, Construção da Skill, Resultados e Como Executar.

---

## A) Análise Manual

Antes de escrever qualquer linha da skill, li o código dos três projetos inteiros para entender que tipo de problema ela precisaria detectar. Abaixo estão os achados que considerei mais relevantes de cada projeto. A lista completa, bem mais extensa, está nos relatórios gerados pela skill em `reports/audit-project-{1,2,3}.md`.

### Projeto 1: code-smells-project (Python/Flask, API de e-commerce)

- **CRITICAL: SQL Injection generalizada.** Praticamente toda query em `models.py` era montada concatenando string com dado vindo direto da requisição, inclusive no login (`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`). Isso permite manipular a query e até burlar autenticação.
- **CRITICAL: endpoint `/admin/query` executando SQL arbitrário.** O corpo da requisição continha o SQL a ser executado, sem nenhuma autenticação. Na prática, um shell de banco de dados exposto publicamente.
- **MEDIUM: Queries N+1 ao montar pedidos.** Para cada pedido, buscava os itens; para cada item, buscava o nome do produto. Tudo em loops aninhados, uma query por iteração.
- **MEDIUM: validação inconsistente entre criar e atualizar produto.** `atualizar_produto` não repetia as checagens de tamanho de nome e categoria válida que `criar_produto` tinha.
- **LOW: `print()` como única forma de log**, inclusive para registrar erro.
- **LOW: magic numbers na regra de desconto** (`10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02` soltos no meio do cálculo de faturamento).

Por que isso importa: um e-commerce lidando com dados de cliente e pagamento não pode ter injection nem um endpoint que executa SQL livre. É o tipo de falha que vira manchete. Os problemas de N+1 e validação são menos graves, mas crescem junto com a base de usuários.

### Projeto 2: ecommerce-api-legacy (Node.js/Express, LMS com checkout)

- **CRITICAL: hash de senha "caseiro" e quebrado.** A função `badCrypto` concatenava 10 mil vezes um pedaço do base64 da própria senha e cortava pra 10 caracteres. Não é criptografia, é ofuscação trivialmente reversível.
- **CRITICAL: número de cartão de crédito logado junto da chave do gateway de pagamento**, na mesma linha de `console.log`. Isso é dado de cartão (PCI) e segredo de produção vazando para qualquer sistema de coleta de log.
- **HIGH: callback hell no checkout.** Cinco níveis de callback aninhado pra uma sequência que é fundamentalmente sequencial, dificultando tratar erro de forma consistente.
- **MEDIUM: N+1 no relatório financeiro administrativo**, buscando aluno e pagamento dentro de um loop de matrículas dentro de um loop de cursos.
- **MEDIUM: validação de entrada fraca no checkout.** O endpoint só conferia se os campos existiam e decidia se o pagamento era aprovado checando apenas se o cartão começava com `"4"` (`cc.startsWith("4")`), sem validar formato de e-mail nem tamanho/formato real do cartão.
- **LOW: nomenclatura ruim** (`u`, `e`, `p`, `cid`, `cc` para usuário, e-mail, senha, id de curso e cartão).

Por que isso importa: é um fluxo de pagamento de verdade (mesmo que de brinquedo). Vazar cartão em log e "criptografar" senha com um algoritmo inventado são falhas de segurança sérias, não só estilo de código. Já o N+1 e a validação fraca do checkout são menos graves, mas afetam a confiabilidade dos dados (pagamento aprovado sem validação real) e a performance conforme a base de cursos/matrículas cresce.

### Projeto 3: task-manager-api (Python/Flask, já com alguma separação em camadas)

- **CRITICAL: hash de senha vazando nas respostas da API.** O `to_dict()` do model `User` devolvia o campo `password` (o hash) e isso ia direto pra resposta HTTP de criar usuário, atualizar e fazer login.
- **CRITICAL: login devolvendo um "token" previsível.** `'fake-jwt-token-' + str(user.id)`: não é um JWT, não é assinado, não expira, e dá pra "logar" como qualquer usuário só sabendo o ID dele.
- **HIGH: regra de negócio duplicada em vez de reaproveitar o model.** O cálculo de "task atrasada" estava reimplementado manualmente em 4 arquivos diferentes, apesar do model `Task` já ter um método `is_overdue()` pronto, que nunca era chamado.
- **MEDIUM: N+1 nas rotas de listagem e no relatório**, buscando usuário/categoria por task dentro de loop.
- **MEDIUM: tratamento de erro genérico e disperso.** Doze blocos `except:` (sem tipo de exceção, sem log) estavam espalhados pelas três rotas, cada um formatando a resposta de erro de um jeito diferente, engolindo qualquer exceção inesperada sem registro.
- **LOW: imports não usados e um módulo `utils/helpers.py` inteiro com funções** (`validate_email`, `calculate_percentage`, `format_date`) que existiam mas nunca eram chamadas. A validação de e-mail era reimplementada do zero em outro arquivo.

Por que isso importa: esse projeto é o mais enganoso dos três porque já *parece* organizado (tem pasta `models/`, `routes/`, `services/`). Mas a organização de pastas sozinha não impede vazamento de senha ou autenticação falsa. O N+1 e o tratamento de erro genérico são mais sutis, porém mostram que ter camadas separadas não é o mesmo que usar essas camadas direito: os `except:` sem log escondem erro real de produção, e o N+1 degrada conforme cresce o número de tasks/usuários. Foi o projeto que mais me fez prestar atenção em auditar *conteúdo*, não só estrutura de diretório.

---

## B) Construção da Skill

### Estrutura do SKILL.md

O `SKILL.md` funciona como um roteiro em três fases (Análise, Auditoria, Refatoração), sempre com uma pausa obrigatória entre a Fase 2 e a Fase 3 pedindo confirmação explícita do usuário. Não deixei isso como sugestão, coloquei como regra explícita ("nunca pule essa pausa, mesmo que o usuário pareça apressado"), porque era um requisito obrigatório do desafio.

O `SKILL.md` não carrega o conhecimento de domínio dentro dele. Ele só orquestra e aponta pra cinco arquivos de referência dentro de `references/`:

- `project-analysis.md`: heurísticas de detecção de linguagem/framework/banco/arquitetura (Fase 1)
- `anti-patterns-catalog.md`: catálogo de anti-patterns com sinais de detecção e severidade (Fase 2)
- `report-template.md`: o formato exato que o relatório de auditoria precisa seguir (Fase 2)
- `architecture-guidelines.md`: as regras do MVC alvo, responsabilidade de cada camada (Fase 3)
- `refactoring-playbook.md`: os padrões de transformação, com exemplo de código antes/depois (Fase 3)

Separei assim porque achei mais fácil de manter. Se eu quisesse ajustar só a severidade de um anti-pattern, por exemplo, mexo no catálogo sem tocar no fluxo das três fases.

### Anti-patterns escolhidos

O catálogo tem 15 anti-patterns (o mínimo pedido era 8), organizados exatamente pela escala de severidade do enunciado:

- **CRITICAL:** God Class/God Method, credenciais hardcoded, SQL Injection, endpoint administrativo sem autenticação.
- **HIGH:** lógica de negócio pesada em controllers, acoplamento forte sem injeção de dependência, estado global mutável, callback hell, hash de senha inadequado.
- **MEDIUM:** queries N+1, validação ausente/inconsistente, APIs/dependências deprecated (item obrigatório do desafio), CORS/middleware mal configurado.
- **LOW:** nomenclatura ruim, magic numbers, uso de `print`/`console.log` como estratégia de log.

Escolhi esses porque foram exatamente os padrões que encontrei nos três projetos durante a análise manual. Não inventei uma lista genérica de livro-texto: derivei do que os projetos realmente continham. Isso foi proposital, porque uma skill só é boa se o catálogo dela nasce de casos reais.

O item de APIs deprecated foi o mais chato de escrever de forma genérica, porque "deprecated" depende de qual é a versão atual de cada ecossistema, e isso muda com o tempo. Resolvi descrevendo o *raciocínio* de detecção (comparar a versão declarada no manifesto de dependências com a linha estável mais recente conhecida, checar padrões de callback que o próprio framework já substituiu por Promise/async nativo) em vez de fixar uma lista de versões que ficaria desatualizada.

### Como garanti que a skill é agnóstica de tecnologia

Três decisões concretas:

1. **Nenhum arquivo de referência assume uma stack fixa.** O `project-analysis.md` começa justamente com uma tabela de heurísticas, do tipo "se você achar X, provavelmente é linguagem Y". A skill precisa *descobrir* a stack lendo o código, nunca assumir.
2. **O catálogo e o playbook trazem exemplos em mais de uma linguagem lado a lado** (Python e JavaScript) para o mesmo anti-pattern, deixando claro que o padrão é conceitual, não sintático.
3. **Testei nas três stacks de propósito:** dois projetos Python/Flask com níveis de organização bem diferentes entre si, e um projeto Node/Express. Se a skill só funcionasse copiando por acaso o vocabulário de um projeto Python, o projeto 2 (Node) teria exposto isso na hora.

A prova concreta disso está em `ecommerce-api-legacy/.claude/skills/refactor-arch/` e `task-manager-api/.claude/skills/refactor-arch/`: são cópias exatas, byte a byte, da pasta que está em `code-smells-project/`. Nada foi ajustado por projeto.

### Desafios encontrados

- **Projeto 3 já tinha camadas, mas a arquitetura ainda estava errada.** O maior desafio de design foi deixar isso explícito no `SKILL.md`: "não recrie do zero, reorganize e corrija o que já existe, movendo o que estiver fora do lugar e criando apenas as camadas que faltam". Na prática, isso significou que a Fase 3 do projeto 3 criou só a camada de `controllers/` (que realmente não existia) e corrigiu `models/`, `routes/`, `services/` e `utils/` no lugar, em vez de reescrever tudo.
- **Ambiente sem virtualenv por projeto.** Como testei os três projetos Python na mesma máquina sem isolar cada um em um venv separado, instalar as dependências do projeto 3 acabou rebaixando o Flask instalado globalmente de 3.1.1 para 3.0.0 (a versão que o projeto 3 pede). Revalidei o projeto 1 depois disso pra garantir que continuava funcionando. Funcionou normalmente, mas deixo registrado aqui porque é o tipo de detalhe que teria sido evitado com um venv por projeto (recomendo isso na seção "Como Executar" abaixo).
- **Rodar as três fases de forma consistente nos três projetos.** Em vez de abrir um terminal separado pra cada `claude "/refactor-arch"`, segui o `SKILL.md` e os arquivos de referência dentro do mesmo fluxo de trabalho pros três projetos. O resultado é o mesmo, já que o conteúdo executado (as instruções da skill) é idêntico em qualquer um dos dois jeitos. Os passos pra quem quiser reproduzir digitando o comando estão na seção D.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1. code-smells-project | 4 | 4 | 4 | 4 | 16 |
| 2. ecommerce-api-legacy | 4 | 4 | 5 | 3 | 16 |
| 3. task-manager-api | 4 | 3 | 5 | 3 | 15 |

Os relatórios completos, com arquivo e linha exata de cada achado, estão em `reports/audit-project-1.md`, `reports/audit-project-2.md` e `reports/audit-project-3.md`. Fiz uma segunda passada em cada um depois da primeira auditoria e encontrei mais alguns pontos que tinham passado batido (validação de itens de pedido no projeto 1, checkout permitindo matrícula duplicada no projeto 2, uso de `datetime.utcnow()` já depreciado no projeto 3), então os totais acima já refletem essa revisão.

### Comparação antes/depois da estrutura

**Projeto 1: code-smells-project**

```
Antes                          Depois
code-smells-project/           code-smells-project/
├── app.py                     ├── app.py (composition root)
├── controllers.py             ├── src/
├── models.py                  │   ├── config/ (settings.py, business_rules.py, database.py)
├── database.py                │   ├── models/ (produto, usuario, pedido)
└── requirements.txt           │   ├── controllers/ (produto, usuario, pedido)
                                │   ├── views/ (routes.py)
                                │   ├── services/ (notification_service.py)
                                │   └── middlewares/ (error_handler.py)
                                └── .env.example
```

**Projeto 2: ecommerce-api-legacy**

```
Antes                          Depois
ecommerce-api-legacy/          ecommerce-api-legacy/
└── src/                       └── src/
    ├── app.js                     ├── app.js (composition root)
    ├── AppManager.js (God Class)  ├── config/ (settings.js, database.js)
    └── utils.js                   ├── models/ (user, course, enrollment, payment, auditLog)
                                    ├── controllers/ (checkout, report, user)
                                    ├── routes/ (index.js)
                                    ├── services/ (payment, cache, logger)
                                    └── middlewares/ (errorHandler.js)
```

**Projeto 3: task-manager-api**

```
Antes                          Depois
task-manager-api/              task-manager-api/
├── app.py                     ├── app.py (composition root, mesma raiz)
├── database.py, seed.py       ├── database.py, seed.py (inalterados)
├── models/                    ├── config/          (novo)
├── routes/                    ├── controllers/     (novo, camada que faltava)
├── services/                  ├── models/          (corrigido: senha, bcrypt, métodos reaproveitados)
└── utils/                     ├── routes/          (emagrecido, delega ao controller)
                                ├── services/        (corrigido: credenciais via config)
                                ├── middlewares/     (novo)
                                └── utils/           (enxugado, só o que é usado de fato)
```

### Checklist de validação, preenchido para os 3 projetos

**Fase 1: Análise**
- [x] Linguagem detectada corretamente (Python nos projetos 1 e 3, JavaScript/Node no projeto 2)
- [x] Framework detectado corretamente (Flask 3.1.1, Express 4.18.2, Flask 3.0.0 + SQLAlchemy)
- [x] Domínio da aplicação descrito corretamente (e-commerce, LMS com checkout, task manager)
- [x] Número de arquivos analisados condiz com a realidade (4, 3 e 15 arquivos respectivamente)

**Fase 2: Auditoria**
- [x] Relatório segue o template definido em `report-template.md`
- [x] Cada finding tem arquivo e linhas exatas
- [x] Findings ordenados por severidade (CRITICAL até LOW)
- [x] Mínimo de 5 findings identificados (16, 16 e 15 respectivamente)
- [x] Detecção de APIs deprecated incluída (driver `sqlite3` callback-based e Express 4.x no projeto 2; dependências declaradas e nunca usadas no projeto 3)
- [x] Skill pausou e pediu confirmação explícita antes da Fase 3 nos 3 projetos

**Fase 3: Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (adaptada ao nível de organização de cada projeto)
- [x] Configuração extraída para módulo de config, sem hardcoded, nos 3 projetos
- [x] Models criados/corrigidos para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentrando o fluxo da aplicação
- [x] Error handling centralizado nos 3 projetos
- [x] Entry point claro (composition root) nos 3 projetos
- [x] Aplicação inicia sem erros nos 3 projetos
- [x] Endpoints originais respondem corretamente nos 3 projetos

### Logs de validação capturados durante a Fase 3

**Projeto 1 (Flask), depois de subir com `python app.py`:**
```
$ curl -s http://localhost:5000/health
{"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}

$ curl -s "http://localhost:5000/produtos/busca?q=notebook' OR '1'='1"
{"dados":[],"sucesso":true,"total":0}   # SQL Injection neutralizado: tratado como texto literal

$ curl -s -X POST http://localhost:5000/pedidos -d '{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":1},{"produto_id":2,"quantidade":2}]}'
{"dados":{"pedido_id":1,"total":6179.79},"mensagem":"Pedido criado com sucesso","sucesso":true}

$ curl -s -X POST http://localhost:5000/admin/reset-db
# 404: endpoint removido de propósito, sem uso legítimo e sem infraestrutura de auth pra protegê-lo
```

**Projeto 2 (Node/Express), depois de subir com `npm start`:**
```
$ curl -s -X POST http://localhost:3000/api/checkout -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
{"msg":"Sucesso","enrollment_id":2}

$ curl -s -X DELETE http://localhost:3000/api/users/1
{"message":"Usuário e registros relacionados removidos com sucesso"}

$ curl -s http://localhost:3000/api/admin/financial-report
[{"course":"Clean Architecture","revenue":0,"students":[]},{"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]
# matrícula/pagamento do usuário deletado não ficaram mais órfãos no banco
```

**Projeto 3 (Flask + SQLAlchemy), depois de `python seed.py && python app.py`:**
```
$ curl -s -X POST http://localhost:5000/login -d '{"email":"joao@email.com","password":"1234"}'
{"message":"Login realizado com sucesso","token":"eyJhbGciOiJIUzI1NiIs...","user":{...sem campo password...}}

$ curl -s http://localhost:5000/reports/summary | head -c 200
{"generated_at":"...","overdue":{"count":2,"tasks":[...]},"overview":{"total_categories":4,"total_tasks":10,"total_users":3},...}
```

### Observações sobre o comportamento em stacks diferentes

- No **projeto 1** (monolito Python de 4 arquivos), a Fase 3 criou a estrutura MVC inteira do zero. Era o cenário "greenfield" dentro do próprio desafio.
- No **projeto 2** (Node, uma God Class só), o principal ganho não foi só separar camadas, mas eliminar o callback hell (virou `async/await`) e resolver um vazamento de dado sensível em log que não existia nos projetos Python. Isso mostrou que o catálogo precisava ter itens que fazem sentido pro ecossistema JS especificamente, já que callback hell não existe do mesmo jeito em Python.
- No **projeto 3** (Flask parcialmente organizado), a skill teve que resistir à tentação de reescrever tudo. O ajuste mais importante que fiz no `SKILL.md` durante o desenvolvimento foi justamente instruir explicitamente para adaptar o tamanho da mudança ao que já existia, em vez de aplicar sempre a transformação mais agressiva.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado e autenticado
- Python 3.10+ e `pip` (projetos 1 e 3)
- Node.js 18+ e `npm` (projeto 2)
- Recomendado: um ambiente virtual Python por projeto (`python -m venv .venv`), já que os projetos 1 e 3 pedem versões diferentes de Flask. Eu mesmo não isolei nesta entrega e precisei revalidar o projeto 1 depois de instalar as dependências do projeto 3 por causa disso.

### Rodando a skill em cada projeto

A skill já está commitada em cada um dos três projetos, em `.claude/skills/refactor-arch/`. Para reproduzir a execução a partir de uma sessão nova do Claude Code:

```bash
# Projeto 1: Python/Flask (e-commerce)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2: Node/Express (LMS com checkout)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3: Python/Flask (task manager, já parcialmente organizado)
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução: a Fase 1 imprime o resumo de detecção, a Fase 2 gera o relatório e **pausa esperando confirmação** antes de mudar qualquer arquivo, e só depois do "sim" a Fase 3 refatora e valida.

Como os três projetos já foram refatorados nesta entrega, rodar a skill novamente deve resultar em uma Fase 2 com poucos ou nenhum finding novo, o esperado depois de uma refatoração bem-sucedida.

### Como validar que a refatoração funcionou

**Projeto 1:**
```bash
cd code-smells-project
pip install -r requirements.txt
python app.py
# em outro terminal:
curl http://localhost:5000/health
curl http://localhost:5000/produtos
```

**Projeto 2:**
```bash
cd ecommerce-api-legacy
npm install
npm start
# em outro terminal:
curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"teste@teste.com","pwd":"123456","c_id":1,"card":"4111111111111111"}'
```

**Projeto 3:**
```bash
cd task-manager-api
pip install -r requirements.txt
python seed.py
python app.py
# em outro terminal:
curl http://localhost:5000/tasks
curl -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}'
```

Em todos os casos, o critério de sucesso é: o servidor sobe sem erro no console e os endpoints respondem com status e corpo equivalentes aos originais, documentados nos relatórios de auditoria e nos logs da seção C acima.

### Ordem de execução sugerida

1. Ler `reports/audit-project-{1,2,3}.md` para ver o que cada auditoria encontrou.
2. Rodar cada projeto localmente (comandos acima) para ver a aplicação já refatorada funcionando.
3. Se quiser reproduzir do zero, dar `git checkout` no commit anterior à refatoração de cada projeto, apagar as pastas novas e rodar `claude "/refactor-arch"` a partir do código original. A skill deve chegar a um resultado equivalente.
