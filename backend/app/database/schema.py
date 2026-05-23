from datetime import datetime, timezone
from app.extensions import db
import uuid


def _uuid():
    return str(uuid.uuid4())


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_photo = db.Column(db.String(255), nullable=True)
    keypoints = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    wardrobe_items = db.relationship("WardrobeItem", backref="session", lazy="dynamic", cascade="all, delete-orphan")
    results = db.relationship("TryOnResult", backref="session", lazy="dynamic", cascade="all, delete-orphan")


class WardrobeItem(db.Model):
    __tablename__ = "wardrobe_items"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    session_id = db.Column(db.String(36), db.ForeignKey("sessions.id"), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # top, bottom, dress, jacket
    original_filename = db.Column(db.String(255), nullable=False)
    no_bg_filename = db.Column(db.String(255), nullable=True)
    background_removed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class TryOnResult(db.Model):
    __tablename__ = "try_on_results"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    session_id = db.Column(db.String(36), db.ForeignKey("sessions.id"), nullable=False)
    clothing_id = db.Column(db.String(36), db.ForeignKey("wardrobe_items.id"), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    clothing = db.relationship("WardrobeItem")
