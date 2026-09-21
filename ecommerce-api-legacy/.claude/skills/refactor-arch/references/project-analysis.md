# Análise de Projeto: Heurísticas de Detecção

Este arquivo orienta a Fase 1 (Análise). O objetivo é caracterizar a codebase sem depender de suposições sobre a stack. Tudo deve ser confirmado lendo arquivos reais do projeto.

## 1. Detectar linguagem

| Sinal | Linguagem provável |
|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml`, arquivos `.py` | Python |
| `package.json`, arquivos `.js`/`.ts` | Node.js / JavaScript ou TypeScript |
| `pom.xml`, `build.gradle`, arquivos `.java` | Java |
| `go.mod`, arquivos `.go` | Go |
| `Gemfile`, arquivos `.rb` | Ruby |

Abra o arquivo de manifesto de dependências (`requirements.txt`, `package.json`, etc.). Ele geralmente já revela linguagem e framework em uma única leitura.

## 2. Detectar framework e versão

- Python: procure `flask`, `django`, `fastapi` no `requirements.txt` (a versão vem junto, ex.: `flask==3.1.1`). Confirme no código com `from flask import Flask` / `import django` / `from fastapi import FastAPI`.
- Node: procure em `dependencies` do `package.json` por `express`, `koa`, `fastify`, `nestjs`. A versão está ao lado (ex.: `"express": "^4.18.2"`).
- Sempre reporte a versão exata quando disponível. Isso também alimenta a checagem de APIs deprecated (ver `anti-patterns-catalog.md`).

## 3. Detectar banco de dados

- Procure strings de conexão, imports de driver (`sqlite3`, `psycopg2`, `pymongo`, `mysql`, `sqlalchemy`, `sequelize`, `mongoose`, `prisma`) e arquivos `.db`/`.sqlite`.
- Liste as tabelas/coleções lendo os `CREATE TABLE` (SQL puro) ou as classes de model (ORMs como SQLAlchemy, Sequelize, Mongoose). O nome da classe/tabela geralmente aparece em `__tablename__`, `db.Model`, `Schema(...)`, ou em `CREATE TABLE nome (...)`.
- Se o banco for criado em memória ou recriado a cada boot (ex.: `sqlite3.Database(':memory:')`), anote isso. É relevante tanto para a análise quanto depois para validação (o estado não persiste entre reinícios).

## 4. Detectar domínio de negócio

Infira o domínio pelos nomes de rotas, entidades/tabelas e mensagens do código, não pelo nome da pasta do projeto:

- Rotas como `/produtos`, `/pedidos`, `/usuarios` → e-commerce.
- Rotas como `/courses`, `/enrollments`, `/checkout` → LMS / cursos online.
- Rotas como `/tasks`, `/categories`, `/reports` → gestão de tarefas / produtividade.

Descreva o domínio em uma frase curta e cite as entidades principais entre parênteses, como no exemplo do enunciado (`E-commerce API (produtos, pedidos, usuários)`).

## 5. Mapear a arquitetura atual

Classifique o nível de organização em um destes perfis (ou um intermediário, descrevendo em texto):

1. **Monolito de poucos arquivos**: toda a lógica (rotas, regras de negócio, acesso a dados) concentrada em 2–5 arquivos na raiz, sem pastas de camadas. Sinal: um único `models.py`/`app.js` com centenas de linhas fazendo tudo.
2. **Camada única confusa**: existe alguma tentativa de separação (ex.: um arquivo "manager" ou "controller"), mas uma classe/módulo ainda mistura banco de dados, regra de negócio e HTTP no mesmo lugar.
3. **Parcialmente organizado**: já existem pastas como `models/`, `routes/`, `services/`, `utils/`, mas as responsabilidades vazam entre elas (regra de negócio dentro da rota, queries dentro do controller, validação duplicada).
4. **MVC completo**: models, controllers e rotas/views bem separados, configuração externa, error handling centralizado. Este é o alvo da Fase 3, não o estado inicial esperado.

Para chegar à classificação, conte quantos arquivos-fonte existem (exclua dependências, cache e bancos gerados) e observe se uma mesma função/arquivo mistura: definição de rota HTTP + query SQL/ORM + regra de negócio + formatação de resposta. Quanto mais dessas responsabilidades estiverem no mesmo lugar, mais próximo do perfil 1.

## 6. Contar arquivos-fonte

Ao reportar "Source files: N files analyzed", conte apenas arquivos de código-fonte do projeto (não conte `node_modules`, ambientes virtuais, bancos `.db`, arquivos de configuração de skill, nem o próprio relatório). Liste os nomes se o total for pequeno (até ~10 arquivos) para facilitar a conferência.

## 7. Saída da Fase 1

Sempre finalize com o bloco de resumo definido no `SKILL.md`. Não avance para a Fase 2 sem antes ter examinado o conteúdo de cada arquivo-fonte relevante. A auditoria depende disso.
