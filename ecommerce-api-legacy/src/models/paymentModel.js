class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    create(enrollmentId, amount, status) {
        return this.db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]);
    }

    findByEnrollmentId(enrollmentId) {
        return this.db.get('SELECT amount, status FROM payments WHERE enrollment_id = ?', [enrollmentId]);
    }

    deleteByEnrollmentIds(enrollmentIds) {
        if (!enrollmentIds.length) return Promise.resolve();
        const placeholders = enrollmentIds.map(() => '?').join(',');
        return this.db.run(`DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
    }
}

module.exports = PaymentModel;
