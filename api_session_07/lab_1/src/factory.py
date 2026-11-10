from flask import Flask
from flask_smorest import Api
from .extensions import db, migrate
from .models.products import product_bp

def create_app(config=None):
    app = Flask(__name__)
    # Database configuration
    app.config["API_TITLE"] = "Product API"
    app.config["API_VERSION"] = "v1"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    api = Api(app)
    api.register_blueprint(product_bp)

    # This lab has no migration scripts yet; create the SQLite table on startup.
    with app.app_context():
        db.create_all()

    return app

app = create_app()
