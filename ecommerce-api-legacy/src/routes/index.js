const express = require('express');
const CheckoutController = require('../controllers/checkoutController');
const ReportController = require('../controllers/reportController');
const UserController = require('../controllers/userController');

function registerRoutes(app, db) {
    const checkoutController = new CheckoutController(db);
    const reportController = new ReportController(db);
    const userController = new UserController(db);

    const router = express.Router();
    router.post('/checkout', checkoutController.checkout);
    router.get('/admin/financial-report', reportController.financialReport);
    router.delete('/users/:id', userController.deleteUser);

    app.use('/api', router);
}

module.exports = registerRoutes;
