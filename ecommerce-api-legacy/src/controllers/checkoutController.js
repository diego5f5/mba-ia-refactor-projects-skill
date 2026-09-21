const CourseModel = require('../models/courseModel');
const UserModel = require('../models/userModel');
const EnrollmentModel = require('../models/enrollmentModel');
const PaymentModel = require('../models/paymentModel');
const AuditLogModel = require('../models/auditLogModel');
const paymentService = require('../services/paymentService');
const cacheService = require('../services/cacheService');

class CheckoutController {
    constructor(db) {
        this.courseModel = new CourseModel(db);
        this.userModel = new UserModel(db);
        this.enrollmentModel = new EnrollmentModel(db);
        this.paymentModel = new PaymentModel(db);
        this.auditLogModel = new AuditLogModel(db);
    }

    checkout = async (req, res, next) => {
        try {
            const { usr: userName, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

            if (!userName || !email || !courseId || !cardNumber) {
                return res.status(400).json({ error: 'Dados obrigatórios ausentes' });
            }

            const course = await this.courseModel.findActiveById(courseId);
            if (!course) {
                return res.status(404).json({ error: 'Curso não encontrado' });
            }

            const userId = await this.userModel.findOrCreateByEmail(userName, email, password);

            const existingEnrollment = await this.enrollmentModel.findByUserAndCourse(userId, courseId);
            if (existingEnrollment) {
                return res.status(409).json({ error: 'Usuário já matriculado neste curso' });
            }

            const payment = paymentService.charge(cardNumber, course.price);
            if (payment.status === 'DENIED') {
                return res.status(400).json({ error: 'Pagamento recusado' });
            }

            const enrollmentId = await this.enrollmentModel.create(userId, courseId);
            await this.paymentModel.create(enrollmentId, course.price, payment.status);
            await this.auditLogModel.log(`Checkout curso ${courseId} por ${userId}`);

            cacheService.set(`last_checkout_${userId}`, course.title);

            return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (err) {
            next(err);
        }
    };
}

module.exports = CheckoutController;
