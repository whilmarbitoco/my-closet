from flask import Blueprint, jsonify
from app.extensions import db
from sqlalchemy import text

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def liveness():
    return jsonify({"status": "ok"}), 200


@health_bp.route("/ready", methods=["GET"])
def readiness():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "unavailable", "detail": str(e)}), 503
