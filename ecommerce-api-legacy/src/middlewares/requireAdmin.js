const crypto = require('crypto');
const settings = require('../config/settings');

function requireAdmin(req, res, next) {
    const expected = Buffer.from(settings.adminToken);
    const provided = Buffer.from((req.get('Authorization') || '').replace(/^Bearer\s+/i, ''));

    // Sem ADMIN_TOKEN configurado a rota fica bloqueada (falha fechada)
    if (!expected.length || provided.length !== expected.length || !crypto.timingSafeEqual(provided, expected)) {
        return res.status(401).json({ error: 'Não autorizado' });
    }
    next();
}

module.exports = requireAdmin;
