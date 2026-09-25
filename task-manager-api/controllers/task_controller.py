from datetime import datetime

from flask import current_app

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import utc_now


def _notify_assignment(task):
    if task.user:
        current_app.extensions['notification_service'].notify_task_assigned(task.user, task)


def list_tasks():
    tasks = Task.query.options(db.joinedload(Task.user), db.joinedload(Task.category)).all()
    result = []
    for t in tasks:
        data = t.to_dict()
        data['user_name'] = t.user.name if t.user else None
        data['category_name'] = t.category.name if t.category else None
        result.append(data)
    return result, None, 200


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return None, 'Task não encontrada', 404
    return task.to_dict(), None, 200


def create_task(data):
    title = data.get('title')
    errors = []

    if not title:
        errors.append('Título é obrigatório')
    elif len(title) < 3:
        errors.append('Título muito curto')
    elif len(title) > 200:
        errors.append('Título muito longo')

    status = data.get('status', 'pending')
    if not Task.validate_status(status):
        errors.append('Status inválido')

    priority = data.get('priority', 3)
    if not Task.validate_priority(priority):
        errors.append('Prioridade deve ser entre 1 e 5')

    user_id = data.get('user_id')
    if user_id and not User.query.get(user_id):
        errors.append('Usuário não encontrado')

    category_id = data.get('category_id')
    if category_id and not Category.query.get(category_id):
        errors.append('Categoria não encontrada')

    if errors:
        return None, errors[0], 400

    task = Task()
    task.title = title
    task.description = data.get('description', '')
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    if data.get('due_date'):
        try:
            task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            return None, 'Formato de data inválido. Use YYYY-MM-DD', 400

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    _notify_assignment(task)
    return task.to_dict(), None, 201


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        return None, 'Task não encontrada', 404
    previous_user_id = task.user_id

    if 'title' in data:
        if len(data['title']) < 3:
            return None, 'Título muito curto', 400
        if len(data['title']) > 200:
            return None, 'Título muito longo', 400
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if not Task.validate_status(data['status']):
            return None, 'Status inválido', 400
        task.status = data['status']

    if 'priority' in data:
        if not Task.validate_priority(data['priority']):
            return None, 'Prioridade deve ser entre 1 e 5', 400
        task.priority = data['priority']

    if 'user_id' in data:
        if data['user_id'] and not User.query.get(data['user_id']):
            return None, 'Usuário não encontrado', 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not Category.query.get(data['category_id']):
            return None, 'Categoria não encontrada', 404
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return None, 'Formato de data inválido', 400
        else:
            task.due_date = None

    if 'tags' in data:
        tags = data['tags']
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    task.updated_at = utc_now()
    db.session.commit()
    if task.user_id and task.user_id != previous_user_id:
        _notify_assignment(task)
    return task.to_dict(), None, 200


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return None, 'Task não encontrada', 404
    db.session.delete(task)
    db.session.commit()
    return {'message': 'Task deletada com sucesso'}, None, 200


def search_tasks(query, status, priority, user_id):
    tasks = Task.query
    if query:
        tasks = tasks.filter(db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%')))
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority:
        tasks = tasks.filter(Task.priority == int(priority))
    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))
    return [t.to_dict() for t in tasks.all()], None, 200


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()
    overdue = sum(1 for t in Task.query.all() if t.is_overdue())

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }, None, 200
