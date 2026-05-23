from flask import Blueprint, request
from app.extensions import limiter
from app.modules.tryon.service import TryOnService
from app.errors.handlers import ValidationError

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


@user_bp.route("/upload", methods=["POST"])
@limiter.limit("10 per minute")
def upload_photo():
    session_id = request.form.get("session_id")
    if not session_id:
        raise ValidationError(message="session_id is required")

    file = request.files.get("file")
    service = TryOnService()
    result = service.upload_user_photo(session_id, file)
    return result, 200
