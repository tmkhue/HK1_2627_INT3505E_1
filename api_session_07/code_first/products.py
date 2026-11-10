from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort

from schemas import ProductSchema

app = Flask(__name__)

# OpenAPI configuration
app.config["API_TITLE"] = "Product API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"

app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = (
    "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"
)

api = Api(app)

# Blueprint
blp = Blueprint(
    "Products",
    "products",
    url_prefix="/products",
    description="Product operations"
)

products = [
    {"id": 1, "name": "Laptop", "price": 1500},
    {"id": 2, "name": "Mouse", "price": 20}
]


@blp.route("/")
class ProductList(MethodView):

    @blp.response(200, ProductSchema(many=True))
    def get(self):
        """Get all products"""
        return products

    @blp.arguments(ProductSchema)
    @blp.response(201, ProductSchema)
    def post(self, data):
        """Create a product"""
        product = {
            "id": len(products) + 1,
            **data
        }

        products.append(product)
        return product


@blp.route("/<int:product_id>")
class ProductDetail(MethodView):

    @blp.response(200, ProductSchema)
    def get(self, product_id):
        """Get product by ID"""
        product = next(
            (p for p in products if p["id"] == product_id),
            None
        )

        if product is None:
            abort(404, message="Product not found")

        return product

# Register Blueprint
api.register_blueprint(blp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)