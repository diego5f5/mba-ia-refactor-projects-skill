const bcrypt = require('bcryptjs');

class UserModel {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email) {
        return this.db.get('SELECT * FROM users WHERE email = ?', [email]);
    }

    findById(id) {
        return this.db.get('SELECT * FROM users WHERE id = ?', [id]);
    }

    async create(name, email, plainPassword) {
        const hash = bcrypt.hashSync(plainPassword, 10);
        const result = await this.db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, hash]);
        return result.lastID;
    }

    async findOrCreateByEmail(name, email, plainPassword) {
        const existing = await this.findByEmail(email);
        if (existing) return existing.id;
        return this.create(name, email, plainPassword || '123456');
    }

    delete(id) {
        return this.db.run('DELETE FROM users WHERE id = ?', [id]);
    }
}

module.exports = UserModel;
