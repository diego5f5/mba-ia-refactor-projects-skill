const logger = require('../services/loggerService');

function errorHandler(err, req, res, next) {
    logger.error(err.stack || err.message);
    const status = err.status || 500;
    res.status(status).json({ error: err.message || 'Erro interno' });
}

module.exports = errorHandler;
