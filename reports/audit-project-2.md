================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 3

> Nota: os itens marcados como "revisão" abaixo foram acrescentados numa segunda leitura, depois da primeira versão deste relatório.

## Findings

### [CRITICAL] Hardcoded Credentials
File: src/utils.js:2-6
Description: Objeto `config` traz `dbPass`, `paymentGatewayKey` e `smtpUser` como strings literais no código-fonte (ex.: `paymentGatewayKey: "pk_live_1234567890abcdef"`).
Impact: Qualquer pessoa com acesso ao repositório tem a chave real de um gateway de pagamento e a senha de banco de produção.
Recommendation: Mover para variáveis de ambiente lidas em um módulo `config/settings.js`.

### [CRITICAL] Criptografia de senha quebrada/caseira
File: src/utils.js:17-23 (uso em src/AppManager.js:68)
Description: `badCrypto` "hasheia" a senha concatenando 10 mil vezes um trecho fixo do base64 da própria senha e cortando para 10 caracteres. Não é um algoritmo de hash reconhecido, é reversível/adivinhável com trivial esforço.
Impact: Senhas de usuários ficam praticamente em texto claro; qualquer vazamento do banco expõe credenciais reais.
Recommendation: Usar bcrypt (ou argon2/scrypt) para hash de senha, conforme padrão 9 do playbook.

### [CRITICAL] Dados sensíveis expostos em log
File: src/AppManager.js:45
Description: `console.log` imprime o número completo do cartão de crédito do cliente junto com a chave secreta do gateway de pagamento na mesma linha (`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`).
Impact: Qualquer sistema de coleta de log passa a armazenar dado de cartão (PCI) e a credencial do gateway em texto plano.
Recommendation: Nunca logar PAN de cartão nem segredos; logar no máximo um identificador não sensível (ex.: últimos 4 dígitos).

### [CRITICAL] God Class
File: src/AppManager.js:1-142
Description: A classe `AppManager` cria a conexão de banco, define todas as tabelas, registra todas as rotas HTTP e executa a regra de negócio de checkout (validação, cobrança, matrícula, auditoria) inteiramente dentro de si mesma.
Impact: Impossível testar checkout, relatório financeiro ou exclusão de usuário isoladamente; qualquer mudança em uma rota arrisca as outras.
Recommendation: Separar em models (`courseModel`, `userModel`, `enrollmentModel`, `paymentModel`), controllers por domínio e rotas dedicadas.

### [HIGH] Estado global mutável
File: src/utils.js:9-10
Description: `globalCache` e `totalRevenue` são variáveis de módulo alteradas por múltiplas funções (`logAndCache`) sem nenhum encapsulamento.
Impact: Estado compartilhado sem controle de acesso, propenso a condição de corrida e impossível de resetar entre testes.
Recommendation: Encapsular em uma classe/serviço de cache com sua própria instância controlada.

### [HIGH] Acoplamento forte sem injeção de dependência
File: src/AppManager.js:6-8
Description: O construtor de `AppManager` cria sua própria conexão SQLite internamente (`this.db = new sqlite3.Database(':memory:')`), em vez de recebê-la de fora.
Impact: Impossível trocar a fonte de dados (ex.: mockar em teste, usar banco persistente em produção) sem editar a classe.
Recommendation: Receber a conexão de banco como parâmetro do construtor/composition root.

### [HIGH] Callback hell / fluxo assíncrono não estruturado
File: src/AppManager.js:28-78
Description: A rota de checkout aninha 5 níveis de callbacks (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`) para executar uma sequência de operações que é fundamentalmente sequencial.
Impact: Código difícil de ler e manter; um erro esquecido em um nível interno (ex.: falha silenciosa) pode deixar a requisição HTTP pendurada sem resposta.
Recommendation: Reescrever com `async/await` sobre uma versão promisificada do driver, conforme padrão 8 do playbook.

### [HIGH] Exclusão sem integridade referencial e sem autenticação
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` remove o usuário mas deixa matrículas e pagamentos órfãos (o próprio texto da resposta admite isso, `"...ficaram sujos no banco"`), e não há nenhuma checagem de autenticação/autorização antes de executar a exclusão.
Impact: Qualquer requisição não autenticada apaga um usuário e corrompe a integridade dos dados de matrícula/pagamento.
Recommendation: Adicionar autenticação de administrador e, ao excluir o usuário, tratar (excluir ou anonimizar) os registros relacionados na mesma transação.

### [MEDIUM] Queries N+1 no relatório financeiro
File: src/AppManager.js:80-129
Description: Para cada curso, busca as matrículas; para cada matrícula, busca o usuário e o pagamento em queries separadas dentro do loop (`courses.forEach` → `this.db.all("... WHERE course_id")` → `enrollments.forEach` → `this.db.get(...)` duas vezes).
Impact: O número de queries cresce proporcionalmente a cursos × matrículas, tornando o endpoint cada vez mais lento com o crescimento da base.
Recommendation: Substituir por uma única query com JOIN entre courses, enrollments, users e payments.

### [MEDIUM] Tratamento de erro disperso e inconsistente
File: src/AppManager.js:37-137 (cada rota repete seu próprio `if (err) return res.status(...)`)
Description: Não existe nenhum middleware de erro central no Express; cada rota decide seu próprio formato de resposta de erro (`res.status(400).send("Bad Request")`, `res.status(500).send("Erro DB")`), sem padronização.
Impact: Respostas de erro inconsistentes para o cliente da API; qualquer exceção não prevista quebra a requisição sem resposta formatada.
Recommendation: Registrar um middleware de erro único (`app.use((err, req, res, next) => ...)`) e propagar erros via `next(err)`.

### [MEDIUM] APIs/dependências deprecated
File: package.json:10-11
Description: O driver `sqlite3` (`^5.1.6`) usado é o modelo callback-based; a própria comunidade recomenda `sqlite3` com wrapper de Promises (`util.promisify` ou pacotes como `sqlite`) para código novo. `express` está fixado em `^4.18.2`; o Express 5 (estável) já resolve nativamente o problema de erros não capturados em handlers assíncronos que este projeto sofre no padrão de callback atual.
Impact: Seguir com a API antiga mantém o código preso ao padrão de callback (fonte direta do finding de callback hell acima) e fora das correções/tratamentos de erro que as versões atuais já resolvem.
Recommendation: Migrar as chamadas de `sqlite3` para uma interface baseada em Promise/async-await; avaliar migração para Express 5 ao modernizar o projeto.

### [MEDIUM] Validação de entrada fraca no checkout
File: src/AppManager.js:29-35, 46
Description: O checkout só verifica se os campos existem (`if (!u || !e || !cid || !cc)`) e decide aprovação de pagamento apenas checando se o número do cartão começa com `"4"` (`cc.startsWith("4")`), sem validar formato de e-mail, tamanho/formato de cartão ou CVV.
Impact: Dados inconsistentes podem ser persistidos e a "regra de aprovação" de pagamento é trivialmente previsível, sem nenhuma validação real.
Recommendation: Validar e-mail e formato de cartão antes de processar, delegando a decisão de aprovação a um serviço de pagamento real (ou mock com regras mais robustas para ambiente de teste).

### [MEDIUM] Checkout permite matrícula duplicada no mesmo curso (achado de revisão)
File: src/AppManager.js:37-78
Description: O checkout nunca checa se o usuário já está matriculado no curso antes de inserir uma nova linha em `enrollments`. Repetir o mesmo checkout gera múltiplas matrículas (e múltiplos pagamentos) para o mesmo par usuário/curso.
Impact: Relatório financeiro conta receita duplicada, e o usuário pode ser cobrado mais de uma vez pelo mesmo curso.
Recommendation: Checar `enrollments` por `user_id` + `course_id` antes de processar o pagamento; recusar ou reaproveitar a matrícula existente.

### [LOW] Nomenclatura ruim
File: src/AppManager.js:29-33
Description: Variáveis de uma letra para dados de negócio importantes (`u`, `e`, `p`, `cid`, `cc` para usuário, e-mail, senha, id do curso e cartão de crédito).
Impact: Aumenta o tempo de leitura e a chance de trocar um parâmetro por outro sem perceber.
Recommendation: Renomear para nomes descritivos (`userName`, `email`, `courseId`, `cardNumber`).

### [LOW] `console.log` como estratégia de log
File: src/AppManager.js:45, 59; src/utils.js:13
Description: Toda a observabilidade do serviço depende de `console.log`, sem níveis, sem destino configurável e (como já apontado) às vezes logando dado sensível.
Impact: Não escala para produção; difícil de filtrar ou correlacionar com uma requisição específica.
Recommendation: Substituir por um logger configurável (ex.: `pino`, `winston`) com níveis apropriados.

### [LOW] Tabela de auditoria gravada mas nunca lida (achado de revisão)
File: src/AppManager.js:57 (grava em `audit_logs`); nenhuma rota do projeto faz `SELECT` nessa tabela
Description: Todo checkout grava uma linha em `audit_logs`, mas não existe nenhum endpoint que exponha ou consulte esse histórico. É um recurso write-only.
Impact: O esforço de manter a trilha de auditoria não gera valor nenhum hoje, porque ninguém consegue lê-la pela API.
Recommendation: Adicionar um endpoint de leitura (protegido por autenticação) ou remover a gravação se o recurso não fizer parte do escopo. Mantive como limitação documentada nesta entrega, no mesmo espírito da decisão tomada para o `NotificationService` do projeto 3.

================================
Total: 16 findings
================================
