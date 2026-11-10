from datetime import datetime

from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate
from sqlalchemy import DateTime, ForeignKey, Integer, func, select
from sqlalchemy.orm import Mapped, joinedload, mapped_column, relationship, selectinload

from ..extensions import db
from ..errors import ProductNotFoundError, ProductOutOfStockError
from .products import Product

order_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="raise"
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship(back_populates="items", lazy="raise")
    product: Mapped["Product"] = relationship(lazy="raise")


class OrderItemIn(Schema):
    product_id = fields.Int(required=True, validate=validate.Range(min=1))
    quantity = fields.Int(required=True, validate=validate.Range(min=1))


class OrderIn(Schema):
    items = fields.List(fields.Nested(OrderItemIn), required=True, validate=validate.Length(min=1))


class ProductSummaryOut(Schema):
    id = fields.Int(dump_only=True)
    sku = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)


class OrderItemOut(Schema):
    id = fields.Int(dump_only=True)
    product = fields.Nested(ProductSummaryOut, dump_only=True)
    quantity = fields.Int(dump_only=True)
    unit_price_cents = fields.Int(dump_only=True)


class OrderOut(Schema):
    id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    items = fields.List(fields.Nested(OrderItemOut), dump_only=True)


@order_bp.route("/")
class OrdersResource(MethodView):
    @order_bp.arguments(OrderIn)
    @order_bp.response(201, OrderOut)
    def post(self, order_data):
        order = Order()
        for item_data in order_data["items"]:
            product = db.session.get(Product, item_data["product_id"])
            if product is None or product.archived:
                raise ProductNotFoundError(f"Product {item_data['product_id']} not found or unavailable")
            if product.qty_in_stock < item_data["quantity"]:
                raise ProductOutOfStockError(f"Insufficient stock for product {product.id}")
            product.qty_in_stock -= item_data["quantity"]
            order.items.append(
                OrderItem(
                    product=product,
                    quantity=item_data["quantity"],
                    unit_price_cents=product.price_cents,
                )
            )
        db.session.add(order)
        db.session.commit()
        return order

    @order_bp.response(200, OrderOut(many=True))
    def get(self):
        statement = (
            select(Order)
            .options(selectinload(Order.items).joinedload(OrderItem.product))
            .order_by(Order.id)
        )
        return db.session.execute(statement).scalars().all()
