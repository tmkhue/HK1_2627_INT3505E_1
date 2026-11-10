import os
class DefaultConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")
    JSON_SORT_KEYS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///products.db")
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

class TestingConfig(DefaultConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    LOG_LEVEL = "WARNING"

class ProductionConfig(DefaultConfig):
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 10, "max_overflow": 20,
                                 "pool_pre_ping": True, "pool_recycle": 1800}
    LOG_LEVEL = "WARNING"