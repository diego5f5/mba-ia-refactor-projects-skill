# Catálogo de Anti-Patterns

Use este catálogo na Fase 2 (Auditoria). Para cada item: o que é, como detectar (sinais concretos no código, não "código ruim"), e a severidade padrão. A severidade pode subir um nível se o impacto observado for maior que o caso típico (ex.: credencial hardcoded que dá acesso a produção real), mas nunca invente uma categoria fora da escala CRITICAL/HIGH/MEDIUM/LOW definida no desafio.

---

## CRITICAL

### 1. God Class / God Method
**Detecção:** um único arquivo/módulo/classe concentra queries de banco, regra de negócio, validação e formatação de resposta para múltiplos domínios diferentes (ex.: produtos, usuários e pedidos no mesmo `models.py`; ou uma classe `AppManager` que ao mesmo tempo cria tabelas, define rotas, processa pagamento e faz log). Sinal objetivo: contar quantos domínios/entidades distintos um mesmo arquivo manipula. 3 ou mais é forte indício.
**Por quê é crítico:** impossível testar em isolamento, qualquer mudança tem efeito colateral amplo, viola completamente a separação MVC.

### 2. Hardcoded Credentials / Secrets
**Detecção:** strings literais de `SECRET_KEY`, senha, chave de API, connection string ou token diretamente no código-fonte (`app.config["SECRET_KEY"] = "..."`, `dbPass: "senha..."`, `paymentGatewayKey: "pk_live_..."`). Também conta expor esse valor em uma resposta HTTP (ex.: endpoint de health check devolvendo a secret key no JSON).
**Por quê é crítico:** exposição de dados sensíveis; qualquer pessoa com acesso ao repositório ou à resposta da API tem a credencial.

### 3. SQL Injection
**Detecção:** montagem de query por concatenação de string com dado vindo da requisição (`"SELECT * FROM produtos WHERE id = " + str(id)`, template strings sem parâmetro bindado). Contraste com uso correto de placeholders (`?`, `%s`, parâmetros nomeados): se a query usa `+` ou f-string/template literal para inserir um valor de entrada do usuário, é injection.
**Por quê é crítico:** permite leitura, alteração ou exclusão arbitrária de dados; em APIs que expõem um endpoint de query livre (ex.: `/admin/query` executando SQL enviado no corpo da requisição) o risco é ainda mais direto.

### 4. Endpoint de administração sem controle de acesso
**Detecção:** rotas que resetam o banco, deletam dados em massa, excluem usuários, expõem relatórios financeiros/logs de auditoria ou executam comandos arbitrários (`/admin/reset-db`, `/admin/query`, `DELETE /users/:id`, `/admin/financial-report`) sem nenhuma checagem de autenticação/autorização antes de executar a ação. Sinal objetivo: na definição da rota não aparece nenhum middleware/decorator de auth antes do handler (ex.: `router.delete('/users/:id', handler)` direto, ou função Flask sem `@require_admin`).
**Por quê é crítico:** qualquer requisição não autenticada pode destruir dados de produção.

---

## HIGH

### 5. Lógica de negócio pesada dentro de Controllers/Routes
**Detecção:** a função que trata a rota HTTP também calcula totais, aplica regras de desconto, decide fluxo de pagamento ou itera sobre múltiplas entidades relacionadas, em vez de delegar isso a uma camada de serviço/model. Sinal: a função do controller tem mais de ~20-30 linhas misturando `request.get_json()`, cálculo de negócio e chamada direta ao banco.
**Por quê:** dificulta testar a regra de negócio sem subir um servidor HTTP; viola separação de responsabilidades do MVC.

### 5b. Acoplamento forte sem Injeção de Dependência
**Detecção:** uma classe cria suas próprias dependências internamente (`this.db = new sqlite3.Database(...)` dentro do construtor) em vez de recebê-las de fora; funções chamam `get_db()`/conexão global diretamente ao invés de receber a conexão/repositório como parâmetro.
**Por quê:** impossível substituir a dependência em teste (ex.: mockar banco), qualquer mudança na forma de conectar exige alterar todas as classes que a instanciam.

### 6. Estado global mutável
**Detecção:** variáveis no escopo de módulo que são lidas e escritas por múltiplas funções/rotas (`global db_connection`, `let globalCache = {}`, contadores de módulo como `let totalRevenue = 0`).
**Por quê:** efeitos colaterais não previsíveis, condições de corrida em ambiente concorrente, dificulta reset de estado em testes.

### 7. Callback hell / fluxo assíncrono não estruturado
**Detecção (Node/JS principalmente):** callbacks aninhados 3+ níveis para operações sequenciais de banco, sem uso de `async/await` ou Promises encadeadas, e sem tratamento de erro consistente em cada nível (`if (err) ...` ausente em algum callback).
**Por quê:** difícil de ler, testar e tratar erros; um erro esquecido em um nível interno pode travar a resposta HTTP (request nunca respondida).

### 8. Criptografia/hash inadequado para senhas
**Detecção:** uso de `hashlib.md5`, hash "caseiro" feito manualmente (loop concatenando base64), ou qualquer coisa que não seja um algoritmo de hash de senha reconhecido (bcrypt, scrypt, argon2, PBKDF2).
**Por quê:** MD5 e implementações caseiras são reversíveis/quebráveis rapidamente; senhas de usuários ficam expostas em caso de vazamento do banco.

---

## MEDIUM

### 9. Queries N+1
**Detecção:** um loop `for` que, a cada iteração, dispara uma nova query ao banco para buscar dados relacionados (ex.: para cada pedido, buscar itens; para cada item, buscar o nome do produto em uma query separada dentro do mesmo loop).
**Por quê:** degrada performance proporcionalmente ao volume de dados; deveria ser resolvido com JOIN, `IN (...)` ou eager loading do ORM.

### 10. Validação ausente ou inconsistente nas rotas
**Detecção:** endpoints que aceitam `request.get_json()` e usam os campos diretamente sem checar tipo/presença (ex.: comparar `preco < 0` sem antes garantir que `preco` é numérico), ou validações que existem em um endpoint (`criar_produto`) mas faltam em outro equivalente (`atualizar_produto`).
**Por quê:** gera erros 500 inesperados e abre brecha para dados inconsistentes no banco.

### 11. APIs / dependências deprecated
**Detecção:** dependências fixadas em versões antigas que já têm sucessoras recomendadas pelo próprio ecossistema (ex.: uma versão de framework com EOL anunciado, uso de métodos marcados como deprecated na documentação oficial do framework instalado, uso de callback-style de uma lib que hoje oferece Promise/async nativo, `request` no lugar de `fetch`/`axios` em Node, `flask.ext.*` no lugar do import direto em Flask). Compare a versão declarada no manifesto de dependências com a última versão estável conhecida da mesma major/minor line.
**Recomendação:** sempre aponte o equivalente moderno (ex.: "atualizar Flask para 3.x e usar `from flask_cors import CORS` no lugar de `flask.ext.cors`", "substituir callback de `sqlite3` por wrapper com Promises/`util.promisify`").
**Por quê:** APIs deprecated podem ser removidas em versões futuras, muitas vezes carregam vulnerabilidades já corrigidas nas versões novas.

### 12. Uso inadequado de middlewares / CORS aberto demais
**Detecção:** `CORS(app)` ou `app.use(cors())` sem nenhuma restrição de origem em uma API que expõe dados sensíveis; ausência de middleware de log/erro centralizado, fazendo cada rota implementar seu próprio `try/except`/`try/catch` repetido.
**Por quê:** superfície de ataque desnecessariamente ampla; duplicação de tratamento de erro é fonte de inconsistência.

---

## LOW

### 13. Nomenclatura ruim / inconsistente
**Detecção:** nomes de variáveis de uma letra ou abreviações obscuras em contexto não trivial (`u`, `e`, `cid`, `cc` para usuário/email/curso-id/cartão de crédito), mistura de idioma (português e inglês no mesmo arquivo) sem padrão.
**Por quê:** aumenta o tempo de leitura e a chance de erro ao dar manutenção.

### 14. Magic numbers / strings soltos no código
**Detecção:** valores literais com significado de negócio embutidos direto na lógica sem constante nomeada (`if faturamento > 10000: desconto = faturamento * 0.1`, limites de tamanho de string como `200`/`3` repetidos em vários lugares).
**Por quê:** dificulta entender a regra de negócio e alterar o valor de forma consistente em todos os lugares que o usam.

### 15. `print`/`console.log` como estratégia de log
**Detecção:** uso de `print(...)`/`console.log(...)` espalhado pelo código como único mecanismo de observabilidade, inclusive para erros (`print("ERRO: " + str(e))`), sem logger configurável ou níveis de log.
**Por quê:** não escala para produção (sem níveis, sem destino configurável, sem correlação de request), embora não seja um risco imediato como os itens acima.

---

## Como aplicar este catálogo

1. Percorra cada arquivo relevante do projeto e confronte com os sinais de detecção acima.
2. Um mesmo arquivo pode acumular vários findings diferentes. Registre cada um separadamente, com sua própria localização (arquivo:linha).
3. Nunca copie o texto deste catálogo literalmente no relatório. Adapte a Description/Impact/Recommendation ao trecho de código real encontrado, citando nomes de variáveis, rotas e valores reais.
4. Se encontrar um problema real que não se encaixa em nenhum item acima, ainda assim reporte, escolhendo a severidade por analogia com a definição do desafio (CRITICAL/HIGH/MEDIUM/LOW).
