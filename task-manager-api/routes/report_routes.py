from flask import Blueprint, jsonify, request

from controllers import category_controller, report_controller

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    data, error, status = report_controller.user_report(user_id)
    return jsonify(data if error is None else {'error': error}), status


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    data, error, status = category_controller.list_categories()
    return jsonify(data if error is None else {'error': error}), status


@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json(silent=True) or {}
    result, error, status = category_controller.create_category(data)
    return jsonify(result if error is None else {'error': error}), status


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json(silent=True) or {}
    result, error, status = category_controller.update_category(cat_id, data)
    return jsonify(result if error is None else {'error': error}), status


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    result, error, status = category_controller.delete_category(cat_id)
    return jsonify(result if error is None else {'error': error}), status
