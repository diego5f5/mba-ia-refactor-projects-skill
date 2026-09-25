const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');
const settings = require('./settings');

class Database {
    constructor(dbPath) {
        this.dbPath = dbPath || settings.dbPath;
        this.db = new sqlite3.Database(this.dbPath);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.get(sql, params, (err, row) => {
                if (err) return reject(err);
                resolve(row);
            });
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.all(sql, params, (err, rows) => {
                if (err) return reject(err);
                resolve(rows || []);
            });
        });
    }

    async transaction(work) {
        await this.run('BEGIN');
        try {
            const result = await work();
            await this.run('COMMIT');
            return result;
        } catch (err) {
            await this.run('ROLLBACK');
            throw err;
        }
    }

    async init() {
        await this.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
        await this.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
        await this.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
        await this.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
        await this.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
        await this._seed();
    }

    async _seed() {
        const existing = await this.get('SELECT COUNT(*) as count FROM users');
        if (existing && existing.count > 0) return;

        const hash = bcrypt.hashSync('123', 10);
        await this.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', hash]);

        const course1 = await this.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', ['Clean Architecture', 997.0]);
        await this.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', ['Docker', 497.0]);

        const enrollment = await this.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, ?)', [course1.lastID]);
        await this.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollment.lastID, 997.0, 'PAID']);
    }
}

module.exports = Database;
