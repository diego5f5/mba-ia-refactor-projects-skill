class CacheService {
    constructor() {
        this._store = new Map();
    }

    set(key, value) {
        this._store.set(key, value);
    }

    get(key) {
        return this._store.get(key);
    }
}

module.exports = new CacheService();
