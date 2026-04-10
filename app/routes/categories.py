from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from app import db
from app.models import Category, Task
from app.schemas import CategorySchema

categories_bp = Blueprint("categories", __name__)
category_schema = CategorySchema()

# these are the routes for categories
@categories_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    result = []
    for cat in categories:
        result.append({
            "id": cat.id,
            "name": cat.name,
            "color": cat.color,
            "task_count": len(cat.tasks),
        })
    return jsonify({"categories": result}), 200

# get category by id and its tasks
@categories_bp.route("/categories/<int:category_id>", methods=["GET"])
def get_category(category_id):
    cat = Category.query.get(category_id)
    if cat is None:
        return jsonify({"error": "Category not found"}), 404

    tasks = [{"id": t.id, "title": t.title, "completed": t.completed} for t in cat.tasks]
    return jsonify({
        "id": cat.id,
        "name": cat.name,
        "color": cat.color,
        "tasks": tasks,
    }), 200 

# create a new category
@categories_bp.route("/categories", methods=["POST"])
def create_category():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"errors": {"json": ["No input data provided."]}}), 400

    try:
        data = category_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    cat = Category(name=data["name"], color=data.get("color"))
    db.session.add(cat)
    db.session.commit()

    return jsonify({
        "id": cat.id,
        "name": cat.name,
        "color": cat.color,
    }), 201

# delete a category (only if it has no tasks)
@categories_bp.route("/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    cat = Category.query.get(category_id)
    if cat is None:
        return jsonify({"error": "This category is not found"}), 404

    if len(cat.tasks) > 0:
        return jsonify({"error": "Cannot delete category with existing tasks. YOu need to first move or delete tasks."}), 400

    db.session.delete(cat)
    db.session.commit()

    return jsonify({"message": "Category has been deleted"}), 200
