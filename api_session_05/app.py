from werkzeug.exceptions import HTTPException
from sqlalchemy import inspect, text
from models import db
from routes import app

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return {
        "error": e.name,
        "message": e.description,
        "status": e.code
    }, e.code

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///library.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    order_columns = {column["name"] for column in inspect(db.engine).get_columns("orders")}
    if "status" not in order_columns:
        db.session.execute(
            text("ALTER TABLE orders ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'BORROWED'")
        )
        db.session.commit()
    review_columns = {column["name"] for column in inspect(db.engine).get_columns("reviews")}
    if "customer_id" not in review_columns:
        db.session.execute(
            text("ALTER TABLE reviews ADD COLUMN customer_id INTEGER REFERENCES customers(customerId)")
        )
        db.session.commit()

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
