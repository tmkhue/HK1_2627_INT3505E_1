from sqlalchemy import event

from src.extensions import db
from src.models.orders import Order, OrderItem
from src.models.products import Product


def test_post_creates_order_with_multiple_product_items(client, app):
    with app.app_context():
        db.session.add_all([
            Product(sku="BOOK-1", name="Book", price_cents=1200, qty_in_stock=10),
            Product(sku="PEN-1", name="Pen", price_cents=250, qty_in_stock=10),
        ])
        db.session.commit()

    response = client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 3}]},
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert len(payload["items"]) == 2
    assert {item["product"]["sku"] for item in payload["items"]} == {"BOOK-1", "PEN-1"}
    assert {item["quantity"] for item in payload["items"]} == {2, 3}
    with app.app_context():
        assert db.session.query(Order).count() == 1
        assert db.session.query(OrderItem).count() == 2


def test_get_orders_eager_loads_items_and_products_without_n_plus_one(client, app):
    with app.app_context():
        products = [
            Product(sku=f"SKU-{i}", name=f"Product {i}", price_cents=100 + i, qty_in_stock=5)
            for i in range(4)
        ]
        orders = []
        for product in products:
            order = Order()
            order.items.append(OrderItem(product=product, quantity=1, unit_price_cents=product.price_cents))
            orders.append(order)
        db.session.add_all(orders)
        db.session.commit()

        statements = []
        engine = db.engine
        def record_select(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)

        event.listen(engine, "before_cursor_execute", record_select)
        try:
            response = client.get("/api/v1/orders/")
        finally:
            event.remove(engine, "before_cursor_execute", record_select)

    assert response.status_code == 200
    assert len(response.get_json()) == 4
    assert sum("FROM orders" in sql for sql in statements) == 1
    assert sum("FROM order_items" in sql for sql in statements) == 1
    assert len(statements) == 2
