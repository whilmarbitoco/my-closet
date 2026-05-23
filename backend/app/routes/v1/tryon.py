from flask import Blueprint, request
from app.extensions import limiter
from app.errors.handlers import ValidationError
from app.modules.tryon.service import TryOnService
from app.modules.tryon.schemas import TryOnResultResponseSchema

tryon_bp = Blueprint("tryon", __name__, url_prefix="/api/try-on")
result_schema = TryOnResultResponseSchema(many=True)


@tryon_bp.route("", methods=["POST"])
@limiter.limit("10 per minute")
def try_on():
    data = request.json or {}
    session_id = data.get("session_id")
    clothing_id = data.get("clothing_id")
    category = data.get("category")

    if not session_id:
        raise ValidationError(message="session_id is required")
    if not clothing_id:
        raise ValidationError(message="clothing_id is required")
    if not category:
        raise ValidationError(message="category is required")

    service = TryOnService()
    result = service.try_on(session_id, clothing_id, category)
    return result, 200


@tryon_bp.route("/<session_id>", methods=["GET"])
@limiter.limit("30 per minute")
def get_results(session_id):
    service = TryOnService()
    results = service.get_results(session_id)
    return {"results": result_schema.dump(results)}, 200
