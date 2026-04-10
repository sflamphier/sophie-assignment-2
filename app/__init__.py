import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/taskmanager"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.tasks import tasks_bp
    from app.routes.categories import categories_bp

    app.register_blueprint(tasks_bp)
    app.register_blueprint(categories_bp)

    return app
