import os
import uuid
from flask import Flask, jsonify, g, request
from app.errors.handlers import APIError
from app.core.logging import configure_logging
from app.core.config import config_map
from app.routes.v1.session import session_bp
from app.routes.v1.user import user_bp
from app.routes.v1.wardrobe import wardrobe_bp
from app.routes.v1.tryon import tryon_bp
from app.routes.health import health_bp
from .extensions import db, cors, limiter

env = os.getenv("FLASK_ENV", "development")


def create_app():
    app = Flask(__name__)
    app.config.from_object(config_map[env])

    configure_logging()

    @app.before_request
    def set_correlation_id():
        g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    @app.after_request
    def add_correlation_header(response):
        response.headers["X-Correlation-ID"] = getattr(g, "correlation_id", "")
        return response

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return jsonify(error.to_json()), error.status_code

    db.init_app(app)
    cors.init_app(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"],
    )
    limiter.init_app(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(wardrobe_bp)
    app.register_blueprint(tryon_bp)

    return app
