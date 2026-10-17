from datetime import datetime, time

from flask import Flask, request
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import Author, Book, Category, Customer, RentalItem, RentalOrder, Review, db
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


@app.get("/books")
def get_books():
    books = db.session.scalars(select(Book)).all()
    return book_schema.dump(books, many=True), 200


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
