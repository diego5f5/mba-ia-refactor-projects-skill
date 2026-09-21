const express = require('express');
const Database = require('./config/database');
const settings = require('./config/settings');
const registerRoutes = require('./routes/index');
const errorHandler = require('./middlewares/errorHandler');
const logger = require('./services/loggerService');

async function createApp() {
    const app = express();
    app.use(express.json());

    const db = new Database();
    await db.init();

    registerRoutes(app, db);
    app.use(errorHandler);

    return app;
}

if (require.main === module) {
    createApp().then((app) => {
        app.listen(settings.port, () => {
            logger.info(`Frankenstein LMS rodando na porta ${settings.port}...`);
        });
    });
}

module.exports = createApp;
