# Template do Relatório de Auditoria

Use exatamente esta estrutura ao gerar a saída da Fase 2. Preencha os campos entre `<>` com dados reais do projeto analisado. Nunca deixe um placeholder no relatório final.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<M> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERIDADE>] <Nome curto do anti-pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: <o que foi encontrado, citando código/nomes reais>
Impact: <consequência concreta se não for corrigido>
Recommendation: <o que fazer, referenciando a transformação do playbook quando aplicável>

### [<SEVERIDADE>] <próximo finding>
...

================================
Total: <N> findings
================================
```

## Regras de preenchimento

- **Ordenação:** findings sempre em ordem decrescente de severidade, todos os CRITICAL primeiro, depois HIGH, depois MEDIUM, depois LOW. Dentro da mesma severidade, ordene pela ordem em que aparecem no código (arquivo, depois linha).
- **File:** sempre caminho relativo à raiz do projeto (ex.: `models.py:28`, `src/AppManager.js:37-78`). Se o problema cobrir um intervalo, use `inicio-fim`. Nunca escreva "vários lugares" sem listar pelo menos os principais arquivos/linhas.
- **Summary:** os números precisam bater exatamente com a contagem de findings listados abaixo. Confira antes de finalizar.
- **Total:** mesmo número da soma do Summary.
- **Mínimo:** pelo menos 5 findings no total, sendo ao menos 1 CRITICAL ou HIGH. Se a auditoria encontrar menos que isso, revise o código com mais atenção antes de fechar o relatório. Normalmente há mais problemas do que parece à primeira vista.
- **Fonte da verdade:** cada finding deve ser rastreável ao `anti-patterns-catalog.md` (ou justificado por analogia, ver regra 4 daquele arquivo).
- Depois de montar o relatório, salve-o em `reports/audit-project-N.md` (criando a pasta `reports/` na raiz do repositório se não existir) e também imprima o conteúdo completo no terminal antes de pedir a confirmação da Fase 3.
