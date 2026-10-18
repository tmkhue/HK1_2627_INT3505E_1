from datetime import datetime, time
import base64
import binascii
import json
from flask import Flask, request
from marshmallow import ValidationError
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError

from models import Author, Book, Category, Customer, RentalItem, RentalOrder, Review, book_author, book_category, db
from schemas import (
    AuthorSchema,
    BookSchema,
    CategorySchema,
    CustomerSchema,
    RentalOrderCreateSchema,
    RentalOrderSchema,
    ReviewCreateSchema,
    ReviewSchema,
)

app = Flask(__name__)
book_schema = BookSchema()
author_schema = AuthorSchema()
category_schema = CategorySchema()
customer_schema = CustomerSchema()
rental_create_schema = RentalOrderCreateSchema()
rental_order_schema = RentalOrderSchema()
review_create_schema = ReviewCreateSchema()
review_schema = ReviewSchema()

ALLOWED_SORT_FIELDS = {"title", "price", "bookId", "customerId", "orderId", "authorId", "category"}

SORT_EXPRESSIONS = {
    "title": func.coalesce(Book.title, ""),
    "price": func.coalesce(Book.price, -1),
    "bookId": func.coalesce(Book.book_id, -1),
    "authorId": func.coalesce(
        select(Author.author_id)
        .join(book_author, Author.author_id == book_author.c.author_id)
        .where(book_author.c.book_id == Book.book_id)
        .order_by(Author.author_id)
        .limit(1)
        .scalar_subquery(),
        -1,
    ),
    "category": func.coalesce(
        select(Category.name)
        .join(book_category, book_category.c.categories == Category.name)
        .where(book_category.c.bookId == Book.book_id)
        .order_by(Category.name)
        .limit(1)
        .scalar_subquery(),
        "",
    ),
    "orderId": func.coalesce(
        select(RentalItem.order_id)
        .where(RentalItem.book_id == Book.book_id)
        .order_by(RentalItem.order_id)
        .limit(1)
        .scalar_subquery(),
        -1,
    ),
    "customerId": func.coalesce(
        select(RentalOrder.customer_id)
        .join(RentalItem, RentalItem.order_id == RentalOrder.order_id)
        .where(RentalItem.book_id == Book.book_id)
        .order_by(RentalOrder.customer_id)
        .limit(1)
        .scalar_subquery(),
        -1,
    ),
}

def load_json(schema, partial=False):
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValidationError({"_schema": ["A JSON object is required."]})
    return schema.load(data, partial=partial)


def resolve_authors(author_inputs):
    authors = []
    for author_input in author_inputs:
        name = author_input["name"].strip()
        author = db.session.scalar(select(Author).where(Author.name == name))
        if author is None:
            author = Author(name=name, biography=author_input.get("biography"))
            db.session.add(author)
        elif author_input.get("biography") and not author.biography:
            author.biography = author_input["biography"]
        authors.append(author)
    return authors


def get_categories(names):
    categories = []
    for value in names:
        name = value.strip()
        category = db.session.get(Category, name)
        if category is None:
            category = Category(name=name)
            db.session.add(category)
        categories.append(category)
    return categories


def commit_or_conflict():
    try:
        db.session.commit()
        return None
    except IntegrityError:
        db.session.rollback()
        return {"error": "Database constraint violation"}, 409


def parse_sort(sort_value):
    sort_keys = []
    for entry in sort_value.split(","):
        entry = entry.strip()
        if not entry:
            raise ValueError("Sort keys cannot be empty")
        if ":" in entry:
            field, direction = entry.rsplit(":", 1)
            if direction.lower() not in {"asc", "desc"}:
                raise ValueError("Sort direction must be asc or desc")
            descending = direction.lower() == "desc"
        else:
            descending = entry.startswith("-")
            field = entry[1:] if entry[:1] in {"-", "+"} else entry
        if field not in ALLOWED_SORT_FIELDS:
            raise ValueError(f"Unsupported sort field: {field}")
        if field in {name for name, _ in sort_keys}:
            raise ValueError(f"Duplicate sort field: {field}")
        sort_keys.append((field, descending))
    if "bookId" not in {field for field, _ in sort_keys}:
        sort_keys.append(("bookId", False))
    return sort_keys


def encode_cursor(values, sort_keys, category):
    payload = json.dumps(
        {
            "values": values,
            "sort": [[field, "desc" if descending else "asc"] for field, descending in sort_keys],
            "genre": category,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(token, sort_keys, genre):
    try:
        padded = token + "=" * (-len(token) % 4)
        values = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ValueError("Invalid cursor")
    expected_sort = [[field, "desc" if descending else "asc"] for field, descending in sort_keys]
    if not isinstance(values, dict) or values.get("sort") != expected_sort or values.get("genre") != genre:
        raise ValueError("Cursor does not match the selected sort keys")
    cursor_values = values.get("values")
    if not isinstance(cursor_values, list) or len(cursor_values) != len(sort_keys):
        raise ValueError("Invalid cursor values")
    return cursor_values


@app.get("/books")
def list_books():
    strategy = request.args.get("strategy", "offset").lower()
    if strategy not in {"offset", "cursor"}:
        return {"error": "strategy must be offset or cursor"}, 400
    try:
        limit = int(request.args.get("limit", 20))
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        sort_keys = parse_sort(request.args.get("sort", "bookId"))
    except ValueError as error:
        return {"error": str(error)}, 400

    expressions = [SORT_EXPRESSIONS[field] for field, _ in sort_keys]
    ordering = [
        expression.desc() if descending else expression.asc()
        for expression, (_, descending) in zip(expressions, sort_keys)
    ]
    query = select(Book, *expressions)
    genre = request.args.get("genre")
    if genre is not None:
        genre = genre.strip()
        if not genre:
            return {"error": "genre cannot be empty"}, 400
        query = query.where(Book.categories.any(Category.name == genre))

    if strategy == "offset":
        try:
            offset = int(request.args.get("offset", 0))
            if offset < 0:
                raise ValueError("offset must be zero or greater")
        except ValueError as error:
            return {"error": str(error)}, 400
        rows = db.session.execute(
            query.order_by(*ordering).offset(offset).limit(limit + 1)
        ).all()
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": book_schema.dump([row[0] for row in rows], many=True),
            "pagination": {
                "strategy": "offset",
                "limit": limit,
                "offset": offset,
                "hasMore": has_more,
                "nextOffset": offset + limit if has_more else None,
            },
        }, 200

    token = request.args.get("cursor")
    if token:
        try:
            last_values = decode_cursor(token, sort_keys, genre)
        except ValueError as error:
            return {"error": str(error)}, 400
        after_cursor = []
        preceding_equalities = []
        for expression, (_, descending), last_value in zip(expressions, sort_keys, last_values):
            comparison = expression < last_value if descending else expression > last_value
            after_cursor.append(and_(*preceding_equalities, comparison))
            preceding_equalities.append(expression == last_value)
        query = query.where(or_(*after_cursor))

    rows = db.session.execute(query.order_by(*ordering).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = encode_cursor(list(rows[-1][1:]), sort_keys, genre) if has_more and rows else None
    return {
        "items": book_schema.dump([row[0] for row in rows], many=True),
        "pagination": {
            "strategy": "cursor",
            "limit": limit,
            "hasMore": has_more,
            "nextCursor": next_cursor,
        },
    }, 200


@app.post("/books")
def create_book():
    try:
        data = load_json(book_schema)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    book = Book(
        title=data["title"],
        price=data["price"],
        description=data.get("description"),
        authors=resolve_authors(data["authors_input"]),
        categories=get_categories(data.get("categories_input", [])),
    )
    db.session.add(book)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return book_schema.dump(book), 201


@app.get("/books/<book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return {"message": "Book not found"}, 404
    return book_schema.dump(book), 200


@app.put("/books/<book_id>")
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return {"message": "Book not found"}, 404
    try:
        data = load_json(book_schema, partial=True)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    for field in ("title", "price", "description"):
        if field in data:
            setattr(book, field, data[field])
    if "authors_input" in data:
        book.authors = resolve_authors(data["authors_input"])
    if "categories_input" in data:
        book.categories = get_categories(data["categories_input"])
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return book_schema.dump(book), 200


@app.delete("/books/<book_id>")
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return {"message": "Book not found"}, 404
    if book.rental_items:
        return {"error": "Cannot delete a book referenced by rental orders"}, 409
    db.session.delete(book)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return {"message": "Book deleted"}, 200


@app.get("/authors")
def get_authors():
    authors = db.session.scalars(select(Author)).all()
    return author_schema.dump(authors, many=True), 200


@app.post("/authors")
def create_author():
    try:
        data = load_json(author_schema)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    author = Author(name=data["name"].strip(), biography=data.get("biography"))
    db.session.add(author)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return author_schema.dump(author), 201


@app.get("/authors/<author_id>")
def get_author(author_id):
    author = db.session.get(Author, author_id)
    if author is None:
        return {"message": "Author not found"}, 404
    return author_schema.dump(author), 200


@app.put("/authors/<author_id>")
def update_author(author_id):
    author = db.session.get(Author, author_id)
    if author is None:
        return {"message": "Author not found"}, 404
    try:
        data = load_json(author_schema, partial=True)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    for field in ("name", "biography"):
        if field in data:
            setattr(author, field, data[field])
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return author_schema.dump(author), 200


@app.delete("/authors/<author_id>")
def delete_author(author_id):
    author = db.session.get(Author, author_id)
    if author is None:
        return {"message": "Author not found"}, 404
    db.session.delete(author)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return {"message": "Author deleted"}, 200


@app.get("/authors/<author_id>/books")
def get_author_books(author_id):
    author = db.session.get(Author, author_id)
    if author is None:
        return {"message": "Author not found"}, 404
    return book_schema.dump(author.books, many=True), 200


@app.get("/categories")
def get_categories_route():
    categories = db.session.scalars(select(Category)).all()
    return category_schema.dump(categories, many=True), 200


@app.get("/categories/<path:category_name>/books")
def get_category_books(category_name):
    category = db.session.get(Category, category_name)
    if category is None:
        return {"message": "Category not found"}, 404
    return book_schema.dump(category.books, many=True), 200


@app.get("/customers")
def get_customers():
    customers = db.session.scalars(select(Customer)).all()
    return customer_schema.dump(customers, many=True), 200


@app.post("/customers")
def create_customer():
    try:
        data = load_json(customer_schema)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    customer = Customer(name=data["name"].strip(), email=data["email"], password=data.get("password"))
    db.session.add(customer)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return customer_schema.dump(customer), 201


@app.get("/customers/<customer_id>")
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return {"message": "Customer not found"}, 404
    return customer_schema.dump(customer), 200


@app.put("/customers/<customer_id>")
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return {"message": "Customer not found"}, 404
    try:
        data = load_json(customer_schema, partial=True)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    for field in ("name", "email", "password"):
        if field in data:
            setattr(customer, field, data[field])
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return customer_schema.dump(customer), 200


@app.delete("/customers/<customer_id>")
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return {"message": "Customer not found"}, 404
    db.session.delete(customer)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return {"message": "Customer deleted"}, 200


@app.get("/customers/<customer_id>/rentals")
def get_customer_rentals(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return {"message": "Customer not found"}, 404
    return rental_order_schema.dump(customer.rental_orders, many=True), 200


@app.post("/rentals")
def create_rental_order():
    try:
        data = load_json(rental_create_schema)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    customer = db.session.get(Customer, data["customer_id"])
    if customer is None:
        return {"message": "Customer not found"}, 404
    order = RentalOrder(
        customer=customer,
        rental_date=datetime.combine(data["rental_date"], time.min),
        return_date=datetime.combine(data["return_date"], time.min),
        status="BORROWED",
        total_price=0,
    )
    for item_data in data["items"]:
        book = db.session.get(Book, item_data["book_id"])
        if book is None:
            return {"message": f"Book {item_data['book_id']} not found"}, 404
        order.items.append(RentalItem(book=book, quantity=item_data["quantity"], unit_price=book.price))
        order.total_price += book.price * item_data["quantity"]
    db.session.add(order)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return rental_order_schema.dump(order), 201


@app.get("/rentals/<order_id>")
def get_rental_order(order_id):
    order = db.session.get(RentalOrder, order_id)
    if order is None:
        return {"message": "Rental order not found"}, 404
    return rental_order_schema.dump(order), 200


@app.patch("/rentals/<order_id>")
def update_rental_order(order_id):
    order = db.session.get(RentalOrder, order_id)
    if order is None:
        return {"message": "Rental order not found"}, 404
    data = request.get_json()
    allowed_fields = {"status", "returnDate"}
    if not isinstance(data, dict) or not data or not set(data).issubset(allowed_fields):
        return {"error": "Provide status and/or returnDate"}, 400
    if "status" in data:
        allowed_statuses = {"PENDING", "BORROWED", "RETURNED", "OVERDUE", "CANCELLED"}
        if data["status"] not in allowed_statuses:
            return {"error": "Invalid status"}, 400
        order.status = data["status"]
    if "returnDate" in data:
        try:
            from datetime import date

            return_date = date.fromisoformat(data["returnDate"])
        except (TypeError, ValueError):
            return {"error": "Invalid date; use YYYY-MM-DD"}, 400
        return_datetime = datetime.combine(return_date, time.min)
        if return_datetime < order.rental_date:
            return {"error": "Return date precedes rental date"}, 400
        order.return_date = return_datetime
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return rental_order_schema.dump(order), 200


@app.delete("/rentals/<order_id>")
def delete_rental_order(order_id):
    order = db.session.get(RentalOrder, order_id)
    if order is None:
        return {"message": "Rental order not found"}, 404
    db.session.delete(order)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return {"message": "Rental order deleted"}, 200


@app.get("/books/<book_id>/reviews")
def get_book_reviews(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return {"message": "Book not found"}, 404
    return review_schema.dump(book.reviews, many=True), 200


@app.post("/books/<book_id>/reviews")
def create_review(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return {"message": "Book not found"}, 404
    try:
        data = load_json(review_create_schema)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    customer = db.session.get(Customer, data["customer_id"])
    if customer is None:
        return {"message": "Customer not found"}, 404
    review = Review(
        book=book,
        customer=customer,
        reviewer_name=customer.name,
        rating=data["rating"],
        comment=data.get("comment"),
    )
    db.session.add(review)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return review_schema.dump(review), 201


@app.get("/reviews/<review_id>")
def get_review(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        return {"message": "Review not found"}, 404
    result = review_schema.dump(review)
    result["reviewerName"] = review.customer.name
    return result, 200


@app.put("/reviews/<review_id>")
def update_review(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        return {"message": "Review not found"}, 404
    try:
        data = load_json(review_create_schema, partial=True)
    except ValidationError as error:
        return {"errors": error.messages}, 400
    if "rating" in data:
        review.rating = data["rating"]
    if "comment" in data:
        review.comment = data["comment"]
    if "customer_id" in data:
        customer = db.session.get(Customer, data["customer_id"])
        if customer is None:
            return {"message": "Customer not found"}, 404
        review.customer = customer
        review.reviewer_name = customer.name
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return review_schema.dump(review), 200


@app.delete("/reviews/<review_id>")
def delete_review(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        return {"message": "Review not found"}, 404
    db.session.delete(review)
    conflict = commit_or_conflict()
    if conflict:
        return conflict
    return {"message": "Review deleted"}, 200


@app.get("/customers/<customer_id>/reviews")
def get_customer_reviews(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return {"message": "Customer not found"}, 404
    return review_schema.dump(customer.reviews, many=True), 200
