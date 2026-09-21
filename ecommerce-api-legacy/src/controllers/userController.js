const UserModel = require('../models/userModel');
const EnrollmentModel = require('../models/enrollmentModel');
const PaymentModel = require('../models/paymentModel');

class UserController {
    constructor(db) {
        this.userModel = new UserModel(db);
        this.enrollmentModel = new EnrollmentModel(db);
        this.paymentModel = new PaymentModel(db);
    }

    deleteUser = async (req, res, next) => {
        try {
            const { id } = req.params;

            const enrollments = await this.enrollmentModel.findByUserId(id);
            const enrollmentIds = enrollments.map((e) => e.id);

            await this.paymentModel.deleteByEnrollmentIds(enrollmentIds);
            await this.enrollmentModel.deleteByUserId(id);
            await this.userModel.delete(id);

            return res.json({ message: 'Usuário e registros relacionados removidos com sucesso' });
        } catch (err) {
            next(err);
        }
    };
}

module.exports = UserController;
