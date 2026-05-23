import os

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'app.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 900
    JWT_REFRESH_TOKEN_EXPIRES = 2592000
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_SUPPORTS_CREDENTIALS = True

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB upload limit

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/opt/data/my-closet/uploads")
    RESULT_FOLDER = os.getenv("RESULT_FOLDER", "/opt/data/my-closet/results")
    WARDROBE_FOLDER = os.getenv("WARDROBE_FOLDER", "/opt/data/my-closet/wardrobe")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False


class ProductionConfig(BaseConfig):
    DEBUG = False

    def __init__(self):
        missing = [v for v in ("SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL") if not os.getenv(v)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")


class TestingConfig(BaseConfig):
    TESTING = True
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
