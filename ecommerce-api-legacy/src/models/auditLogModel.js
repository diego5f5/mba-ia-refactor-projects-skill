class AuditLogModel {
    constructor(db) {
        this.db = db;
    }

    log(action) {
        return this.db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
    }

    findAll() {
        return this.db.all('SELECT id, action, created_at FROM audit_logs ORDER BY id DESC');
    }
}

module.exports = AuditLogModel;
