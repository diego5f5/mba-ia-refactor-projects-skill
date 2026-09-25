const UserModel = require('../models/userModel');
const EnrollmentModel = require('../models/enrollmentModel');
const PaymentModel = require('../models/paymentModel');

class UserController {
    constructor(db) {
        this.db = db;
        this.userModel = new UserModel(db);
        this.enrollmentModel = new EnrollmentModel(db);
        this.paymentModel = new PaymentModel(db);
    }

    deleteUser = async (req, res, next) => {
        try {
            const { id } = req.params;

            const user = await this.userModel.findById(id);
            if (!user) {
                return res.status(404).json({ error: 'Usuário não encontrado' });
            }

            await this.db.transaction(async () => {
                const enrollments = await this.enrollmentModel.findByUserId(id);
                await this.paymentModel.deleteByEnrollmentIds(enrollments.map((e) => e.id));
                await this.enrollmentModel.deleteByUserId(id);
                await this.userModel.delete(id);
            });

            return res.json({ message: 'Usuário e registros relacionados removidos com sucesso' });
        } catch (err) {
            next(err);
        }
    };
}

module.exports = UserController;
