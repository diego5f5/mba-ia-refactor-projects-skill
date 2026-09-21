from flask import Blueprint, jsonify, request

from controllers import user_controller

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    data, error, status = user_controller.list_users()
    return jsonify(data if error is None else {'error': error}), status


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    data, error, status = user_controller.get_user(user_id)
    return jsonify(data if error is None else {'error': error}), status


@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json(silent=True) or {}
    result, error, status = user_controller.create_user(data)
    return jsonify(result if error is None else {'error': error}), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    result, error, status = user_controller.update_user(user_id, data)
    return jsonify(result if error is None else {'error': error}), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    result, error, status = user_controller.delete_user(user_id)
    return jsonify(result if error is None else {'error': error}), status


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    result, error, status = user_controller.get_user_tasks(user_id)
    return jsonify(result if error is None else {'error': error}), status


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    result, error, status = user_controller.authenticate(data.get('email'), data.get('password'))
    return jsonify(result if error is None else {'error': error}), status
