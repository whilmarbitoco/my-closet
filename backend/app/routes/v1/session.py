from flask import Blueprint
from app.extensions import limiter
from app.modules.tryon.service import TryOnService
from app.modules.tryon.schemas import SessionResponseSchema
from app.extensions import db

session_bp = Blueprint("session", __name__, url_prefix="/api/session")
response_schema = SessionResponseSchema()


@session_bp.route("", methods=["POST"])
@limiter.limit("10 per minute")
def create_session():
    service = TryOnService()
    session = service.create_session()
    db.session.add(session)
    db.session.commit()
    return response_schema.dump(session), 201
