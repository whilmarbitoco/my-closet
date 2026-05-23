import logging
import json
from flask import g


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record),
        }
        correlation_id = getattr(g, "correlation_id", None) if _has_app_context() else None
        if correlation_id:
            log["correlation_id"] = correlation_id
        return json.dumps(log)


def _has_app_context():
    try:
        from flask import current_app
        current_app._get_current_object()
        return True
    except RuntimeError:
        return False


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]
