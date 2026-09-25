try {
    require('dotenv').config();
} catch (e) {
    // dotenv é opcional; se não estiver instalado, seguimos com process.env puro
}

module.exports = {
    dbUser: process.env.DB_USER || 'admin_master',
    dbPass: process.env.DB_PASS || '',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    smtpUser: process.env.SMTP_USER || '',
    adminToken: process.env.ADMIN_TOKEN || '',
    port: process.env.PORT || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
};
