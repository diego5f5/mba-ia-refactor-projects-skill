const AuditLogModel = require('../models/auditLogModel');

class ReportController {
    constructor(db) {
        this.db = db;
        this.auditLogModel = new AuditLogModel(db);
    }

    auditLogs = async (req, res, next) => {
        try {
            return res.json(await this.auditLogModel.findAll());
        } catch (err) {
            next(err);
        }
    };

    financialReport = async (req, res, next) => {
        try {
            const rows = await this.db.all(`
                SELECT c.id AS course_id, c.title AS course_title,
                       u.name AS student_name,
                       p.amount AS paid_amount, p.status AS payment_status
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN payments p ON p.enrollment_id = e.id
                ORDER BY c.id
            `);

            const reportByCourse = new Map();
            for (const row of rows) {
                if (!reportByCourse.has(row.course_id)) {
                    reportByCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
                }
                const entry = reportByCourse.get(row.course_id);
                if (row.student_name) {
                    entry.students.push({ student: row.student_name, paid: row.paid_amount || 0 });
                    if (row.payment_status === 'PAID') {
                        entry.revenue += row.paid_amount;
                    }
                }
            }

            return res.json(Array.from(reportByCourse.values()));
        } catch (err) {
            next(err);
        }
    };
}

module.exports = ReportController;
