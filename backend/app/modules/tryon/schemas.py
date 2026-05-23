from marshmallow import Schema, fields, validate


class WardrobeUploadSchema(Schema):
    category = fields.Str(
        required=True,
        validate=validate.OneOf(["top", "bottom", "dress", "jacket"]),
    )


class TryOnRequestSchema(Schema):
    session_id = fields.Str(required=True)
    clothing_id = fields.Str(required=True)
    category = fields.Str(
        required=True,
        validate=validate.OneOf(["top", "bottom", "dress", "jacket"]),
    )


class SessionResponseSchema(Schema):
    id = fields.Str(dump_only=True)
    user_photo = fields.Str(dump_only=True)
    keypoints = fields.Dict(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class WardrobeItemResponseSchema(Schema):
    id = fields.Str(dump_only=True)
    category = fields.Str(dump_only=True)
    original_filename = fields.Str(dump_only=True)
    background_removed = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class TryOnResultResponseSchema(Schema):
    id = fields.Str(dump_only=True)
    clothing_id = fields.Str(dump_only=True)
    category = fields.Str(dump_only=True)
    filename = fields.Str(dump_only=True)
    image_url = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
