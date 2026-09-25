================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy (rerun sobre o código já refatorado)
Stack:   Node.js + Express 4.18.2
Files:   16 analyzed | ~400 lines of code

## Summary
CRITICAL: 1 | HIGH: 1 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] Rotas administrativas sem autenticação
File: src/routes/index.js:13-14
Description: `GET /api/admin/financial-report` e `DELETE /api/users/:id` são registradas direto no router, sem nenhum middleware de autenticação antes do handler. O relatório expõe nome de aluno e valor pago por curso, e a exclusão apaga usuário, matrículas e pagamentos.
Impact: Qualquer requisição anônima consegue ler dados financeiros e apagar usuários da base.
Recommendation: Criar um middleware `requireAdmin` com token de administrador vindo da config (`ADMIN_TOKEN`, header `Authorization: Bearer`), comparação em tempo constante e falha fechada, e registrá-lo antes dos handlers dessas rotas (padrão 4 do playbook).

### [HIGH] Exclusão em cascata fora de transação
File: src/controllers/userController.js:16-21
Description: A exclusão de usuário roda três `DELETE` independentes (pagamentos, matrículas, usuário). Se qualquer um falhar no meio, o banco fica em estado parcial, exatamente o problema de registros órfãos que a primeira auditoria apontou.
Impact: Integridade dos dados depende de nenhuma das três operações falhar; não há como desfazer o que já foi apagado.
Recommendation: Executar as três exclusões dentro de uma única transação (`BEGIN`/`COMMIT`, com `ROLLBACK` em caso de erro), conforme padrão 4b do playbook, e responder 404 quando o usuário não existir.

### [MEDIUM] Validação de entrada ainda fraca no checkout
File: src/controllers/checkoutController.js:22-24; src/services/paymentService.js:6
Description: O checkout continua conferindo só a presença dos campos. Não valida formato do e-mail nem se o cartão tem só dígitos e tamanho plausível (13 a 19), e o mock de pagamento aprova qualquer string que comece com `"4"`.
Impact: E-mail inválido vira usuário no banco, e um "cartão" como `4abc` é aprovado.
Recommendation: Validar formato de e-mail e de cartão no controller antes de criar usuário ou cobrar, retornando 400 com mensagem clara.

### [MEDIUM] Express 4 com versão estável mais nova disponível
File: package.json:12
Description: O projeto depende de `express ^4.18.2`, enquanto a linha estável atual é a 5.x (5.2.1). O Express 5 passou a encaminhar para o error handler as rejeições de handlers `async`, que é justamente o padrão usado nos controllers deste projeto.
Impact: Continuar na 4.x obriga cada handler a ter `try/catch` + `next(err)` manual; esquecer um deixa a requisição pendurada.
Recommendation: Atualizar para `express@^5` e validar todas as rotas depois da troca.

### [LOW] Trilha de auditoria gravada e nunca lida
File: src/models/auditLogModel.js:7; src/controllers/checkoutController.js:45
Description: Todo checkout grava em `audit_logs`, mas nenhuma rota consulta essa tabela.
Impact: O custo de manter a trilha existe e o benefício não, porque ninguém consegue ler o histórico pela API.
Recommendation: Expor `GET /api/admin/audit-logs` protegido pelo mesmo `requireAdmin`.

### [LOW] Cache em memória só de escrita
File: src/services/cacheService.js:15; src/controllers/checkoutController.js:47
Description: `cacheService` é uma instância única de módulo que recebe `set` a cada checkout, mas `get` não é chamado em lugar nenhum do projeto.
Impact: Estado mutável que cresce a cada venda sem nenhum uso, herdado do `globalCache` original.
Recommendation: Remover o serviço de cache e a chamada no checkout, já que não existe consumidor para esse dado.

================================
Total: 6 findings
================================
