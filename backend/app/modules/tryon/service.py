import os
import uuid
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import db
from app.database.schema import Session, WardrobeItem, TryOnResult
from app.errors.handlers import NotFoundError, ValidationError, InternalServerError
from app.modules.tryon.engine import detect_body, warp_clothing_to_body, composite_images, simple_bg_remove


class TryOnService:
    def __init__(self, upload_folder=None, result_folder=None, wardrobe_folder=None):
        if upload_folder is None or result_folder is None or wardrobe_folder is None:
            self.upload_folder = current_app.config["UPLOAD_FOLDER"]
            self.result_folder = current_app.config["RESULT_FOLDER"]
            self.wardrobe_folder = current_app.config["WARDROBE_FOLDER"]
        else:
            self.upload_folder = upload_folder
            self.result_folder = result_folder
            self.wardrobe_folder = wardrobe_folder
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.result_folder, exist_ok=True)
        os.makedirs(self.wardrobe_folder, exist_ok=True)

    # ── Session ──

    def create_session(self) -> Session:
        return Session()

    def get_session(self, session_id: str) -> Session:
        session = db.session.get(Session, session_id)
        if not session:
            raise NotFoundError(message="Session not found")
        return session

    # ── User Photo ──

    def upload_user_photo(self, session_id: str, file) -> dict:
        session = self.get_session(session_id)

        if not file or not file.filename:
            raise ValidationError(message="No file provided")

        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise ValidationError(message="File must be an image")

        # Read & validate size
        contents = file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise ValidationError(message="File too large (max 10MB)")

        ext = secure_filename(file.filename).rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"user_{session_id}.{ext}"
        filepath = os.path.join(self.upload_folder, filename)

        with open(filepath, "wb") as f:
            f.write(contents)

        # Detect body
        keypoints = detect_body(filepath)
        if keypoints is None:
            os.remove(filepath)
            raise ValidationError(message="Could not detect body. Use a clear full-body photo.")

        session.user_photo = filename
        session.keypoints = keypoints
        db.session.commit()

        return {"filename": filename, "keypoints_detected": True}

    # ── Wardrobe ──

    def upload_clothing(self, session_id: str, category: str, file) -> dict:
        session = self.get_session(session_id)

        if category not in ("top", "bottom", "dress", "jacket"):
            raise ValidationError(message="Invalid category")

        if not file or not file.filename:
            raise ValidationError(message="No file provided")

        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise ValidationError(message="File must be an image")

        clothing_id = str(uuid.uuid4())
        ext = secure_filename(file.filename).rsplit(".", 1)[-1] if "." in file.filename else "png"
        filename = f"{clothing_id}.{ext}"
        filepath = os.path.join(self.wardrobe_folder, filename)

        contents = file.read()
        with open(filepath, "wb") as f:
            f.write(contents)

        # Background removal
        no_bg_path = os.path.join(self.wardrobe_folder, f"{clothing_id}_nobg.png")
        bg_removed = simple_bg_remove(filepath, no_bg_path)

        item = WardrobeItem(
            id=clothing_id,
            session_id=session_id,
            category=category,
            original_filename=filename,
            no_bg_filename=f"{clothing_id}_nobg.png" if bg_removed else None,
            background_removed=bg_removed,
        )
        db.session.add(item)
        db.session.commit()

        return {
            "clothing_id": clothing_id,
            "category": category,
            "background_removed": bg_removed,
        }

    def get_wardrobe(self, session_id: str) -> list[WardrobeItem]:
        session = self.get_session(session_id)
        return session.wardrobe_items.all()

    # ── Try-On ──

    def try_on(self, session_id: str, clothing_id: str, category: str) -> dict:
        session = self.get_session(session_id)

        if not session.user_photo:
            raise ValidationError(message="Upload a user photo first")

        if category not in ("top", "bottom", "dress", "jacket"):
            raise ValidationError(message="Invalid category")

        clothing_item = db.session.get(WardrobeItem, clothing_id)
        if not clothing_item or clothing_item.session_id != session_id:
            raise NotFoundError(message="Clothing item not found")

        # Load images
        user_path = os.path.join(self.upload_folder, session.user_photo)
        if clothing_item.no_bg_filename:
            clothing_path = os.path.join(self.wardrobe_folder, clothing_item.no_bg_filename)
        else:
            clothing_path = os.path.join(self.wardrobe_folder, clothing_item.original_filename)

        user_img = cv2.imread(user_path)
        clothing_img = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)

        if user_img is None:
            raise InternalServerError(message="Failed to load user image")
        if clothing_img is None:
            raise InternalServerError(message="Failed to load clothing image")

        keypoints = session.keypoints
        if not keypoints:
            raise InternalServerError(message="No body data. Re-upload user photo.")

        # Process
        warped = warp_clothing_to_body(user_img, clothing_img, keypoints, category)
        result_img = composite_images(user_img, warped)

        result_id = str(uuid.uuid4())
        result_filename = f"{result_id}.jpg"
        result_path = os.path.join(self.result_folder, result_filename)
        cv2.imwrite(result_path, result_img)

        result = TryOnResult(
            id=result_id,
            session_id=session_id,
            clothing_id=clothing_id,
            category=category,
            filename=result_filename,
        )
        db.session.add(result)
        db.session.commit()

        return {
            "result_id": result_id,
            "image_url": f"/static/{result_filename}",
        }

    def get_results(self, session_id: str) -> list[TryOnResult]:
        session = self.get_session(session_id)
        return session.results.all()
