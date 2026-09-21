# Guidelines de Arquitetura: Padrão MVC Alvo

Este arquivo descreve a estrutura e as responsabilidades que a Fase 3 deve produzir, independentemente da linguagem. Adapte apenas a sintaxe/convenção de nomenclatura de arquivos ao ecossistema (Python usa `snake_case.py`, Node costuma usar `camelCase.js` ou `kebab-case.js`), mas as camadas e responsabilidades abaixo são as mesmas.

## Estrutura de diretórios alvo

```
src/
├── config/          # configuração da aplicação (env vars, constantes, conexão de banco)
├── models/          # entidades de domínio + acesso a dados, um arquivo por domínio
├── controllers/      # orquestram a requisição: chamam models/services e formatam a resposta
├── views/  (ou routes/)   # definição das rotas HTTP e ligação rota -> controller
├── middlewares/       # cross-cutting concerns: error handler, auth, logging
└── app.py / app.js    # composition root: monta a aplicação a partir das peças acima
```

Se o projeto já tiver uma estrutura parecida com pastas em outro nível (ex.: `models/`, `routes/`, `services/`, `utils/` na raiz, como no task-manager-api), não é obrigatório mover tudo para dentro de `src/`. O importante é que as **responsabilidades abaixo estejam corretamente separadas**, respeitando a convenção que o projeto já usa. Prefira o menor diff que resolve os problemas reais encontrados na auditoria a uma reescrita completa.

## Responsabilidades por camada

### Models
- Representam uma entidade de domínio (Produto, Usuário, Pedido, Task, Course...).
- Concentram todo o acesso a dados daquela entidade: queries/ORM, criação, atualização, exclusão, busca.
- Podem conter validações de invariantes do próprio dado (ex.: um preço não pode ser negativo), mas não decidem fluxo de requisição HTTP.
- Um model nunca deve conhecer o objeto `request`/`response` do framework web.
- Um domínio = um arquivo de model. Não misture Produto e Usuário no mesmo arquivo.

### Views / Routes
- Definem apenas o mapeamento entre método HTTP + path e a função de controller correspondente.
- Não contêm lógica de negócio nem acesso a dados, apenas roteamento (e, quando aplicável, serialização simples de entrada/saída).
- Em frameworks com blueprints/routers (Flask Blueprint, Express Router), cada domínio deve ter seu próprio arquivo de rotas.

### Controllers
- Recebem a requisição já roteada, extraem e validam os dados de entrada (ou delegam a validação a uma função utilitária/serviço).
- Chamam o(s) model(s) ou serviço(s) necessários para executar a operação.
- Formatam a resposta HTTP (status code, corpo JSON) de forma consistente.
- Não devem conter queries SQL/ORM diretamente, nem regra de negócio complexa de múltiplos passos. Isso pertence ao model ou a uma camada de serviço, se o domínio justificar.
- Um controller "magro": extrai dados → valida → chama camada de domínio → responde. Nada além disso.

### Config
- Centraliza leitura de variáveis de ambiente e valores de configuração (secret key, connection string, chaves de API, porta).
- Nenhum valor sensível deve estar hardcoded fora deste módulo; use variáveis de ambiente com um valor de fallback seguro apenas para desenvolvimento local (nunca para produção).

### Middlewares
- Error handler centralizado: um único ponto que captura exceções não tratadas e devolve uma resposta de erro padronizada, em vez de cada rota reimplementar seu próprio try/except.
- Outros cross-cutting concerns (logging estruturado, autenticação) também vivem aqui, se o projeto já tiver ou precisar deles.

### Composition Root (entry point)
- Único arquivo responsável por instanciar a aplicação, registrar config, conectar models/rotas/middlewares e subir o servidor.
- Não deve conter lógica de negócio nem definição de rota inline, apenas montagem.

## Princípios SOLID aplicados na refatoração

- **Single Responsibility:** cada model/controller/rota cuida de um único domínio ou responsabilidade.
- **Dependency Inversion:** dependências (conexão de banco, serviços externos) são recebidas de fora (parâmetro, injeção) em vez de instanciadas dentro da classe que as usa, sempre que isso não exigir reescrever todo o framework.
- **Open/Closed:** adicionar um novo domínio deve significar adicionar novos arquivos de model/controller/rota, não editar um arquivo gigante existente.

## Critério de "pronto"

A Fase 3 só está completa quando:
1. A estrutura de pastas reflete as camadas acima.
2. Nenhuma credencial ou configuração sensível está hardcoded no código.
3. A aplicação sobe sem erros com o comando padrão do projeto.
4. Os endpoints originais continuam respondendo com o mesmo contrato (mesmo path, mesmo método, resposta equivalente).
5. Os findings CRITICAL e HIGH da auditoria foram eliminados ou mitigados; os que restarem devem ser justificados explicitamente no resumo final.
