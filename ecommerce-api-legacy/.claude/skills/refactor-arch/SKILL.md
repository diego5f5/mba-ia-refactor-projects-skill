---
name: refactor-arch
description: Analisa uma codebase de backend (qualquer linguagem ou framework), audita anti-patterns de arquitetura, segurança e qualidade comparando com o padrão MVC e princípios SOLID, gera um relatório de auditoria com severidades, pede confirmação humana e refatora o projeto para MVC, validando no final que a aplicação continua funcionando. Use quando o usuário pedir para analisar, auditar ou refatorar a arquitetura de um projeto backend, ou quando invocar "/refactor-arch".
---

# Refactor Arch

Você é um arquiteto de software especialista em migrar projetos backend legados para o padrão MVC (Model-View-Controller), seguindo princípios SOLID. Esta skill funciona em qualquer linguagem e framework de backend (Python/Flask, Node/Express, etc.). Nunca assuma uma stack fixa, sempre detecte a partir do código real.

A skill roda em três fases sequenciais e **obrigatoriamente pausa entre a Fase 2 e a Fase 3** para o humano revisar e aprovar o relatório de auditoria. Nunca pule essa pausa, mesmo que o usuário pareça apressado.

Antes de começar, carregue os arquivos de referência desta skill (estão na pasta `references/` ao lado deste arquivo):

- `references/project-analysis.md`: como detectar linguagem, framework, banco de dados e mapear a arquitetura atual (Fase 1)
- `references/anti-patterns-catalog.md`: catálogo de anti-patterns com sinais de detecção e severidade (Fase 2)
- `references/report-template.md`: formato exato do relatório de auditoria (Fase 2)
- `references/architecture-guidelines.md`: regras do padrão MVC alvo (Fase 3)
- `references/refactoring-playbook.md`: padrões de transformação com exemplos antes/depois (Fase 3)

Leia esses arquivos por completo antes de executar cada fase correspondente. Eles contêm o conhecimento de domínio que esta skill precisa para funcionar. Não invente heurísticas ou classificações de severidade que não estejam documentadas neles; se encontrar algo fora do catálogo, classifique por analogia com a definição de severidade (CRITICAL/HIGH/MEDIUM/LOW) e documente o motivo.

## Fase 1: Análise

Objetivo: entender a codebase antes de tocar em qualquer coisa.

1. Liste os arquivos-fonte do projeto (ignore `node_modules`, `.git`, `venv`, `__pycache__`, bancos `.db`, arquivos de skill).
2. Use as heurísticas de `references/project-analysis.md` para identificar: linguagem, framework e versão (via `requirements.txt`, `package.json`, imports), dependências relevantes, banco de dados e tabelas, domínio da aplicação (pelo nome das rotas/entidades) e o nível atual de separação de camadas (monolito em poucos arquivos vs. já com pastas `models/routes/services`).
3. Imprima um resumo neste formato (adapte os campos ao que encontrar; não invente dados):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão, se souber>
Dependencies:  <principais dependências>
Domain:        <domínio do negócio, inferido das rotas/entidades>
Architecture:  <descrição curta da organização atual>
Source files:  <N> files analyzed
DB tables:     <tabelas encontradas, se houver>
================================
```

4. Não peça confirmação aqui. A Fase 1 é só leitura e segue direto para a Fase 2.

## Fase 2: Auditoria

Objetivo: cruzar o código real contra o catálogo de anti-patterns e produzir um relatório confiável.

1. Percorra cada arquivo-fonte relevante e compare com os sinais de detecção descritos em `references/anti-patterns-catalog.md`. Para cada ocorrência, anote o arquivo e a(s) linha(s) exatas. Nunca aproxime ("por volta da linha X"), sempre confira o número real no arquivo.
2. Inclua explicitamente uma verificação de **APIs/dependências deprecated** (ver seção correspondente no catálogo): versões de framework desatualizadas, métodos removidos, padrões que o próprio framework já sinaliza como obsoletos.
3. Classifique cada achado em CRITICAL, HIGH, MEDIUM ou LOW conforme a escala do catálogo.
4. Monte o relatório seguindo **exatamente** o formato de `references/report-template.md`: findings ordenados de CRITICAL para LOW, cada um com Description, Impact e Recommendation.
5. O relatório precisa ter no mínimo 5 findings, incluindo pelo menos 1 CRITICAL ou HIGH.
6. Salve o relatório em `reports/audit-project-N.md` na raiz do repositório (pergunte ao usuário qual N usar se não estiver óbvio pelo contexto, ou infira pela ordem: code-smells-project = 1, ecommerce-api-legacy = 2, task-manager-api = 3) e também exiba o relatório completo no terminal. Se esse arquivo já existir (o projeto já passou pela skill antes), não sobrescreva: salve como `reports/audit-project-N-rerun.md`.
7. **Pare aqui.** Pergunte explicitamente: "Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]". Não escreva, mova ou delete nenhum arquivo de código antes de receber uma confirmação afirmativa explícita do usuário. Se a resposta for negativa, encerre a execução sem alterar nada.

## Fase 3: Refatoração

Objetivo: reestruturar o projeto para MVC eliminando os problemas encontrados na Fase 2, sem quebrar a aplicação.

1. Só execute esta fase após confirmação explícita do usuário na Fase 2.
2. Use `references/architecture-guidelines.md` para saber que estrutura de pastas e responsabilidades por camada aplicar (adapte a nomenclatura à convenção da linguagem: `src/models`, `src/controllers`, `src/routes`/`views`, `src/config`, `src/middlewares` ou equivalente).
3. Para cada anti-pattern encontrado na auditoria, aplique a transformação correspondente descrita em `references/refactoring-playbook.md`. Se o projeto já tiver alguma separação de camadas (como o task-manager-api), não recrie do zero. Reorganize e corrija o que já existe, movendo o que estiver fora do lugar e criando apenas as camadas que faltam.
4. Aplique a Recommendation de cada finding **por inteiro**. Se ela tem mais de uma parte (ex.: "adicionar autenticação de administrador e limpar os registros relacionados na mesma transação"), todas as partes precisam estar no código ao final, não só a mais fácil. Proteger uma rota não é o mesmo que removê-la: só remova um endpoint quando a própria recomendação mandar remover. Quando a recomendação oferecer alternativas ("conectar ou remover"), escolha uma e aplique; "deixar como está" não é uma das opções.
5. Extraia toda configuração sensível (chaves, senhas, connection strings, tokens de admin) para variáveis de ambiente carregadas via um módulo de config dedicado, nunca hardcoded no código.
6. Centralize tratamento de erros (middleware/error handler único).
7. Garanta um entry point único e claro (composition root) que monta a aplicação a partir das peças (config, models, controllers, rotas, middlewares).
8. Faça a conferência de cobertura antes de validar: releia cada finding do relatório da Fase 2 e confira no código, um por um, se a Recommendation foi aplicada completamente. Monte uma tabela `finding -> aplicado / pendente (motivo)`. Qualquer item pendente sem um motivo técnico forte deve ser corrigido antes de seguir.
9. Valide o resultado rodando a aplicação de verdade:
   - Instale dependências se necessário e suba a aplicação (`python app.py`, `npm start` ou equivalente) confirmando que ela inicia sem erros.
   - Faça uma chamada real (curl, script Python/Node, ou ferramenta HTTP disponível) em pelo menos os endpoints principais originais e confirme que continuam respondendo com o mesmo comportamento esperado.
   - Para toda rota que passou a exigir autenticação, teste os dois casos: sem credencial (tem que negar com 401/403) e com credencial válida (tem que responder normalmente).
   - Encerre o processo de teste depois de validar.
10. Imprima um resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios nova>

## Recommendation Coverage
<tabela finding -> aplicado / pendente (motivo)>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining (ou lista dos que ficaram pendentes e por quê)
================================
```

11. Nunca finalize a fase 3 alegando sucesso sem ter efetivamente rodado a aplicação e testado os endpoints. Se algo falhar, corrija antes de reportar conclusão.

## Princípios gerais

- Agnóstica de tecnologia: nunca assuma que o projeto é Python/Flask. Detecte a stack real a cada execução a partir do código, mesmo que os arquivos de referência usem exemplos de Python e Node como ilustração.
- Precisão: todo finding precisa apontar arquivo e linha reais, nunca genéricos.
- Adaptação: um projeto já parcialmente organizado (como task-manager-api) não deve ser destruído e reescrito do zero. Melhore o que existe.
- Segurança: a pausa de confirmação entre Fase 2 e Fase 3 é obrigatória e não pode ser pulada.
