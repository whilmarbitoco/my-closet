from app.extensions import db
from app.database.schema import Session


class SessionRepository:
    def get_by_id(self, session_id: str) -> Session | None:
        return db.session.get(Session, session_id)

    def create(self) -> Session:
        session = Session()
        db.session.add(session)
        db.session.commit()
        return session

    def update_photo(self, session_id: str, filename: str, keypoints: dict) -> Session | None:
        session = self.get_by_id(session_id)
        if not session:
            return None
        session.user_photo = filename
        session.keypoints = keypoints
        db.session.commit()
        return session
