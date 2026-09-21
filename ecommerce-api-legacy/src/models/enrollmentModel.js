class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async create(userId, courseId) {
        const result = await this.db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
        return result.lastID;
    }

    findByCourseId(courseId) {
        return this.db.all('SELECT * FROM enrollments WHERE course_id = ?', [courseId]);
    }

    findByUserId(userId) {
        return this.db.all('SELECT * FROM enrollments WHERE user_id = ?', [userId]);
    }

    findByUserAndCourse(userId, courseId) {
        return this.db.get('SELECT * FROM enrollments WHERE user_id = ? AND course_id = ?', [userId, courseId]);
    }

    deleteByUserId(userId) {
        return this.db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
    }
}

module.exports = EnrollmentModel;
