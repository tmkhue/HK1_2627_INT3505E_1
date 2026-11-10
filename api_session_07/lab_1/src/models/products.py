from dataclasses import asdict
from datetime import datetime
from typing import Optional
from flask.views import MethodView
from marshmallow import Schema, fields, validate
from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from ..api.schemas import ProductIn, ProductPatch, ProductOut, ProductPaginationOut
from ..extensions import db
from flask_smorest import Blueprint
from ..errors import ProductNotFoundError, ProductOutOfStockError

product_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")

class PaginationSchema(Schema):
    page = fields.Int(
        load_default=1,
        validate=validate.Range(min=1)
    )

    size = fields.Int(
        load_default=20,
        validate=validate.Range(min=1, max=100)
    )

class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_in_stock: Mapped[int] = mapped_column(Integer, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

@product_bp.route("/")
class list_products(MethodView):
    @product_bp.arguments(PaginationSchema, location="query")
    @product_bp.response(200, ProductPaginationOut)
    def get(self, pagination_args):
        page = pagination_args["page"]
        size = pagination_args["size"]

        base = db.select(Product).where(Product.archived == False)
        total = db.session.scalar(db.select(func.count()).select_from(Product).where(Product.archived == False))
        stmt = base.order_by(Product.id).offset((page - 1) * size).limit(size)
        rows = db.session.execute(stmt).scalars().all()

        return {
            "items": rows,
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size
        }

@product_bp.route("/<int:product_id>")
class get_product(MethodView):
    @product_bp.response(200, ProductOut)
    def get(self, product_id):
        product = db.session.get(Product, product_id)
        if not product or product.archived:
            raise ProductNotFoundError()
        return product

@product_bp.route("/")
class create_product(MethodView):
    @product_bp.arguments(ProductIn)
    @product_bp.response(201, ProductOut)
    def post(self, product_data):
        product = Product(**asdict(product_data))
        db.session.add(product)
        db.session.commit()
        return product

@product_bp.route("/<int:product_id>/reserve")
class reserve_product(MethodView):
    @product_bp.response(200, ProductOut)
    def post(self, product_id):
        product = db.session.get(Product, product_id)
        if not product or product.archived:
            raise ProductNotFoundError()
        if product.qty_in_stock <= 0:
            raise ProductOutOfStockError()
        product.qty_in_stock -= 1
        db.session.commit()
        return product

@product_bp.route("/<int:product_id>")
class update_product(MethodView):
    @product_bp.arguments(ProductPatch, location="json")
    @product_bp.response(200, ProductOut)
    def patch(self, product_data, product_id):
        product = db.session.get(Product, product_id)
        if not product or product.archived:
            raise ProductNotFoundError()
        for key, value in product_data.items():
            setattr(product, key, value)
        db.session.commit()
        return product

@product_bp.route("/<int:product_id>")
class delete_product(MethodView):
    @product_bp.response(204)
    def delete(self, product_id):
        product = db.session.get(Product, product_id)
        if not product or product.archived:
            raise ProductNotFoundError()
        product.archived = True
        db.session.commit()
        return ""
