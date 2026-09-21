from database import db
from models.category import Category
from models.task import Task


def list_categories():
    counts = dict(
        db.session.query(Task.category_id, db.func.count(Task.id)).group_by(Task.category_id).all()
    )
    result = []
    for c in Category.query.all():
        data = c.to_dict()
        data['task_count'] = counts.get(c.id, 0)
        result.append(data)
    return result, None, 200


def create_category(data):
    name = data.get('name')
    if not name:
        return None, 'Nome é obrigatório', 400

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', '#000000')

    db.session.add(category)
    db.session.commit()
    return category.to_dict(), None, 201


def update_category(cat_id, data):
    cat = Category.query.get(cat_id)
    if not cat:
        return None, 'Categoria não encontrada', 404

    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']

    db.session.commit()
    return cat.to_dict(), None, 200


def delete_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        return None, 'Categoria não encontrada', 404

    db.session.delete(cat)
    db.session.commit()
    return {'message': 'Categoria deletada'}, None, 200
