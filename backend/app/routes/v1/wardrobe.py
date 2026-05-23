from flask import Blueprint, request
from app.extensions import limiter
from app.modules.tryon.service import TryOnService
from app.modules.tryon.schemas import WardrobeItemResponseSchema
from app.errors.handlers import ValidationError

wardrobe_bp = Blueprint("wardrobe", __name__, url_prefix="/api/wardrobe")
item_schema = WardrobeItemResponseSchema(many=True)


@wardrobe_bp.route("/upload", methods=["POST"])
@limiter.limit("20 per minute")
def upload_clothing():
    session_id = request.form.get("session_id")
    category = request.form.get("category", "top")

    if not session_id:
        raise ValidationError(message="session_id is required")

    file = request.files.get("file")
    service = TryOnService()
    result = service.upload_clothing(session_id, category, file)
    return result, 200


@wardrobe_bp.route("/<session_id>", methods=["GET"])
@limiter.limit("30 per minute")
def get_wardrobe(session_id):
    service = TryOnService()
    items = service.get_wardrobe(session_id)
    return {"wardrobe": item_schema.dump(items)}, 200
