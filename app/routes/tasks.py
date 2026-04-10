import os
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from redis import Redis
from rq import Queue

from app import db
from app.models import Task, Category
from app.schemas import TaskSchema, TaskUpdateSchema

tasks_bp = Blueprint("tasks", __name__)
task_schema = TaskSchema()
task_update_schema = TaskUpdateSchema()

# This is where we get the queue
def get_queue():
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    conn = Redis.from_url(redis_url)
    return Queue(connection=conn)

@tasks_bp.route("/tasks", methods=["GET"])
def get_tasks():
    completed_param = request.args.get("completed")
    query = Task.query

    if completed_param is not None:
        if completed_param.lower() == "true":
            query = query.filter_by(completed=True)
        elif completed_param.lower() == "false":
            query = query.filter_by(completed=False)

    tasks = query.all()
    result = []
    for task in tasks:
        data = task_schema.dump(task)
        if task.category:
            data["category"] = {"id": task.category.id, "name": task.category.name, "color": task.category.color}
        else:
            data["category"] = None
        result.append(data)

    return jsonify({"tasks": result}), 200

# get single task
@tasks_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    data = task_schema.dump(task)
    if task.category:
        data["category"] = {"id": task.category.id, "name": task.category.name, "color": task.category.color}
    else:
        data["category"] = None

    return jsonify(data), 200

# create a task and queue task
@tasks_bp.route("/tasks", methods=["POST"])
def create_task():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"errors": {"json": ["No input data provided."]}}), 400

    try:
        data = task_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    if data.get("category_id") is not None:
        category = Category.query.get(data["category_id"])
        if category is None:
            return jsonify({"errors": {"category_id": ["Category not found."]}}), 400

    task = Task(
        title=data["title"],
        description=data.get("description"),
        completed=data.get("completed", False),
        due_date=data.get("due_date"),
        category_id=data.get("category_id"),
    )
    db.session.add(task)
    db.session.commit()

    notification_queued = False
    if task.due_date:
        now = datetime.now(timezone.utc)
        due = task.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if now < due <= now + timedelta(hours=24):
            try:
                from app.jobs import send_due_date_notification
                q = get_queue()
                q.enqueue(send_due_date_notification, task.title)
                notification_queued = True
            except Exception:
                pass

    result = task_schema.dump(task)
    result["notification_queued"] = notification_queued

    return jsonify({"task": result}), 201

# This is where we will update and delete routes for tasks
@tasks_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"errors": {"json": ["No input data provided."]}}), 400

    try:
        data = task_update_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    if "category_id" in data and data["category_id"] is not None:
        category = Category.query.get(data["category_id"])
        if category is None:
            return jsonify({"errors": {"category_id": ["Category not found."]}}), 400

    for field, value in data.items():
        setattr(task, field, value)

    task.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    result = task_schema.dump(task)
    if task.category:
        result["category"] = {"id": task.category.id, "name": task.category.name, "color": task.category.color}
    else:
        result["category"] = None

    return jsonify(result), 200

# delete task
@tasks_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"}), 200
