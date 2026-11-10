import os

from flask import Flask
from flask_smorest import Api

from .config import DefaultConfig, ProductionConfig, TestingConfig
from .errors import register_error_handlers
from .extensions import db, migrate
from .logging_config import configure_json_logging, register_request_logging
from .models.products import product_bp


CONFIGS = {
    "default": DefaultConfig,
    "development": DefaultConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def create_app(config=None):
    app = Flask(__name__)

    # config can be a known environment name, a config class/object, or a dict.
    selected_config = config if config is not None else os.getenv("APP_CONFIG", "default")
    if isinstance(selected_config, str):
        config_class = CONFIGS.get(selected_config.lower())
        if config_class is None:
            raise ValueError(
                "Unknown APP_CONFIG. Choose default, development, testing, or production."
            )
        app.config.from_object(config_class)
        is_production = selected_config.lower() == "production"
    elif isinstance(selected_config, dict):
        app.config.from_mapping(selected_config)
        is_production = False
    else:
        app.config.from_object(selected_config)
        is_production = selected_config is ProductionConfig

    if is_production and not os.getenv("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set when APP_CONFIG=production.")

    # Flask-Smorest / OpenAPI settings are application settings, not database
    # environment settings, so they belong here rather than in config.py.
    app.config.setdefault("API_TITLE", "Product API")
    app.config.setdefault("API_VERSION", "v1")
    app.config.setdefault("OPENAPI_VERSION", "3.0.3")
    app.config.setdefault("OPENAPI_URL_PREFIX", "/docs")
    app.config.setdefault("OPENAPI_SWAGGER_UI_PATH", "/swagger-ui")
    app.config.setdefault(
        "OPENAPI_SWAGGER_UI_URL",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/",
    )

    configure_json_logging(app)
    register_request_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)

    api = Api(app)
    api.register_blueprint(product_bp)
    register_error_handlers(app)

    # The lab has no migration scripts yet; create the table for local use.
    with app.app_context():
        db.create_all()

    return app
