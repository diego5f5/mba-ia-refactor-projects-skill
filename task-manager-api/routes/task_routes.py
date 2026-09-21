from flask import Blueprint, jsonify, request

from controllers import task_controller

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    data, error, status = task_controller.list_tasks()
    return jsonify(data if error is None else {'error': error}), status


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    data, error, status = task_controller.get_task(task_id)
    return jsonify(data if error is None else {'error': error}), status


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json(silent=True) or {}
    result, error, status = task_controller.create_task(data)
    return jsonify(result if error is None else {'error': error}), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    result, error, status = task_controller.update_task(task_id, data)
    return jsonify(result if error is None else {'error': error}), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    result, error, status = task_controller.delete_task(task_id)
    return jsonify(result if error is None else {'error': error}), status


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    query = request.args.get('q', '')
    status_param = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')
    result, error, status = task_controller.search_tasks(query, status_param, priority, user_id)
    return jsonify(result if error is None else {'error': error}), status


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    result, error, status = task_controller.task_stats()
    return jsonify(result if error is None else {'error': error}), status
