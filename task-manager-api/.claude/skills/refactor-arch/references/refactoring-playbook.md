# Playbook de Refatoração: Padrões de Transformação

Cada padrão abaixo corresponde a um item do `anti-patterns-catalog.md`. Use os exemplos como referência de estilo, mas aplique a transformação no código real do projeto (nomes de variáveis, domínio e linguagem reais). Nunca cole o exemplo literalmente.

---

## 1. God Class → Models e Controllers por domínio

**Antes** (`models.py` cuidando de produtos, usuários e pedidos no mesmo arquivo):
```python
# models.py
def get_todos_produtos(): ...
def criar_usuario(nome, email, senha): ...
def criar_pedido(usuario_id, itens): ...
```

**Depois** (um arquivo por domínio, cada um só com o que é seu):
```python
# models/produto_model.py
def get_todos_produtos(): ...
def criar_produto(nome, descricao, preco, estoque, categoria): ...

# models/usuario_model.py
def criar_usuario(nome, email, senha): ...

# models/pedido_model.py
def criar_pedido(usuario_id, itens): ...
```
Cada domínio ganha também seu próprio controller (`controllers/produto_controller.py`, etc.), que importa apenas o model correspondente.

---

## 2. Credenciais hardcoded → Config via variável de ambiente

**Antes:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef" };
```

**Depois:**
```python
# config/settings.py
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
```
```js
// config/settings.js
module.exports = {
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: process.env.PORT || 3000,
};
```
Adicione um `.env.example` documentando as variáveis esperadas, e garanta que `.env` real está no `.gitignore`.

---

## 3. SQL Injection → Queries parametrizadas

**Antes:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

**Depois:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```
Em ORMs, use os métodos de query do próprio ORM (`Model.query.get(id)`, `Model.query.filter_by(...)`) em vez de montar SQL manualmente. Em Node com `sqlite3`, sempre passe os valores como array de parâmetros (`db.get("... WHERE id = ?", [id], cb)`), nunca com template string.

---

## 4. Endpoint administrativo perigoso → Removido ou protegido

**Antes:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)  # executa qualquer SQL enviado pelo cliente
```

**Depois:** remover o endpoint de execução de SQL arbitrário (não existe caso de uso legítimo de API pública para isso). Os demais endpoints administrativos (reset, exclusão de usuário, relatórios financeiros, logs de auditoria) **continuam existindo, mas protegidos**: o `require_admin` precisa ser implementado de verdade, não só citado.

Se o projeto já tem um sistema de autenticação (JWT, sessão), reaproveite e cheque o papel de admin. Se não tem nenhum, crie o mínimo: um token de administrador vindo da config (`ADMIN_TOKEN`), enviado no header `Authorization: Bearer <token>`, comparado em tempo constante e com **falha fechada** (sem token configurado, a rota fica bloqueada).

Python/Flask:
```python
# middlewares/auth.py
import hmac
from functools import wraps
from flask import current_app, jsonify, request

def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        provided = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not expected or not hmac.compare_digest(provided, expected):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)
    return wrapper

# rota de reset: protegida e restrita a desenvolvimento
@require_admin
def reset_database():
    if not current_app.config["DEBUG"]:
        return jsonify({"erro": "Disponível apenas em desenvolvimento"}), 403
    ...
```

Node/Express:
```js
// middlewares/requireAdmin.js
const crypto = require('crypto');
const settings = require('../config/settings');

function requireAdmin(req, res, next) {
    const expected = Buffer.from(settings.adminToken || '');
    const provided = Buffer.from((req.get('Authorization') || '').replace(/^Bearer\s+/i, ''));
    if (!expected.length || provided.length !== expected.length || !crypto.timingSafeEqual(provided, expected)) {
        return res.status(401).json({ error: 'Não autorizado' });
    }
    next();
}

// routes: o middleware entra antes do handler
router.delete('/users/:id', requireAdmin, userController.deleteUser);
router.get('/admin/financial-report', requireAdmin, reportController.financialReport);
```

---

## 4b. Exclusão que deixa registros órfãos → Cascata dentro de transação

**Antes:**
```js
db.run("DELETE FROM users WHERE id = ?", [id]); // matrículas e pagamentos ficam órfãos
```

**Depois:** apagar (ou anonimizar) os dependentes e o registro principal numa única transação, para nunca sobrar estado parcial se uma das etapas falhar:
```js
await db.transaction(async () => {
    const enrollments = await enrollmentModel.findByUserId(id);
    await paymentModel.deleteByEnrollmentIds(enrollments.map((e) => e.id));
    await enrollmentModel.deleteByUserId(id);
    await userModel.delete(id);
});
```
```python
with db.session.begin():
    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
```

---

## 5. Lógica de negócio no Controller → Model/Service

**Antes** (controller calculando total e regra de estoque diretamente):
```python
def criar_pedido():
    dados = request.get_json()
    total = 0
    for item in dados["itens"]:
        produto = models.get_produto_por_id(item["produto_id"])
        total += produto["preco"] * item["quantidade"]
    ...
```

**Depois** (controller magro, regra de negócio no model):
```python
# controllers/pedido_controller.py
def criar_pedido():
    dados = request.get_json()
    resultado = pedido_model.criar_pedido(dados["usuario_id"], dados["itens"])
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"]}), 400
    return jsonify({"dados": resultado, "sucesso": True}), 201

# models/pedido_model.py
def criar_pedido(usuario_id, itens):
    total = _calcular_total(itens)
    ...
```

---

## 6. Acoplamento forte → Injeção de Dependência

**Antes:**
```js
class AppManager {
    constructor() {
        this.db = new sqlite3.Database(':memory:'); // cria a própria dependência
    }
}
```

**Depois:**
```js
class AppManager {
    constructor(db) {
        this.db = db; // recebida de fora, pode ser trocada/mockada em teste
    }
}

// composition root
const db = new sqlite3.Database(process.env.DB_PATH || ':memory:');
const manager = new AppManager(db);
```

---

## 7. Estado global mutável → Estado encapsulado

**Antes:**
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
```

**Depois:**
```js
// services/cacheService.js
class CacheService {
    constructor() { this._store = new Map(); }
    set(key, value) { this._store.set(key, value); }
    get(key) { return this._store.get(key); }
}
module.exports = new CacheService(); // instância única, mas encapsulada e testável
```

---

## 8. Callback hell → async/await

**Antes:**
```js
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        this.db.run("INSERT INTO enrollments ...", [], function(err) {
            self.db.run("INSERT INTO payments ...", [], function(err) { ... });
        });
    });
});
```

**Depois:**
```js
async function checkout(courseId, email, cardNumber) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError("Curso não encontrado");

    const user = await userModel.findOrCreateByEmail(email);
    const payment = await paymentService.charge(cardNumber, course.price);
    const enrollment = await enrollmentModel.create(user.id, course.id, payment.status);
    return enrollment;
}
```
Envolva a chamada no controller em um único `try/catch` que delega ao error handler central, em vez de checar `err` em cada callback aninhado.

---

## 9. Hash de senha inadequado → bcrypt (ou equivalente)

**Antes:**
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
```

**Depois:**
```python
import bcrypt

def set_password(self, pwd):
    self.password = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_password(self, pwd):
    return bcrypt.checkpw(pwd.encode(), self.password.encode())
```
Adicione `bcrypt` (ou `argon2-cffi`) às dependências do projeto.

---

## 10. N+1 queries → Busca em lote / eager loading

**Antes:**
```python
for item in itens_pedido:
    cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**Depois (SQL puro, com IN):**
```python
ids = [item["produto_id"] for item in itens_pedido]
placeholders = ",".join("?" for _ in ids)
cursor.execute(f"SELECT id, nome FROM produtos WHERE id IN ({placeholders})", ids)
produtos_por_id = {row["id"]: row["nome"] for row in cursor.fetchall()}
```
**Depois (ORM, com eager loading):**
```python
tasks = Task.query.options(db.joinedload(Task.user), db.joinedload(Task.category)).all()
```

---

## 11. Tratamento de erro disperso → Middleware central

**Antes:** cada rota repete seu próprio `try/except`/`try/catch` com formatos de erro diferentes.

**Depois:**
```python
# middlewares/error_handler.py
@app.errorhandler(Exception)
def handle_error(e):
    code = getattr(e, "code", 500)
    return jsonify({"erro": str(e), "sucesso": False}), code
```
```js
// middlewares/errorHandler.js
app.use((err, req, res, next) => {
    console.error(err);
    res.status(err.status || 500).json({ error: err.message });
});
```
Os controllers deixam de formatar erro individualmente e apenas lançam/propagam a exceção.

---

## 12. Magic numbers → Constantes nomeadas

**Antes:**
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
```

**Depois:**
```python
# config/business_rules.py
DESCONTO_FAIXA_ALTA = (10000, 0.10)
DESCONTO_FAIXA_MEDIA = (5000, 0.05)

def calcular_desconto(faturamento):
    limite, taxa = DESCONTO_FAIXA_ALTA
    if faturamento > limite:
        return faturamento * taxa
    limite, taxa = DESCONTO_FAIXA_MEDIA
    if faturamento > limite:
        return faturamento * taxa
    return 0
```

---

## Ordem sugerida de aplicação na Fase 3

1. Criar a estrutura de pastas alvo (vazia).
2. Extrair config (padrão 2). Isso já remove os findings CRITICAL de credenciais.
3. Corrigir SQL injection e endpoints perigosos (padrões 3 e 4).
4. Separar models por domínio (padrão 1), movendo o acesso a dados já parametrizado.
5. Criar/ajustar controllers magros (padrão 5) e rotas.
6. Aplicar os padrões restantes (DI, estado global, hash de senha, N+1, error handler, magic numbers) conforme os findings específicos daquele projeto.
7. Validar boot + endpoints (ver `architecture-guidelines.md`, critério de "pronto").
