from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

book_author = db.Table(
    "book_author",
    db.Column("book_id", db.Integer, db.ForeignKey("books.bookId"), primary_key=True),
    db.Column("author_id", db.Integer, db.ForeignKey("authors.authorId"), primary_key=True),
)

book_category = db.Table(
    "book_category",
    db.Column("bookId", db.Integer, db.ForeignKey("books.bookId"), primary_key=True),
    db.Column("categories", db.String(50), db.ForeignKey("categories.category"), primary_key=True),
)


class Book(db.Model):
    __tablename__ = "books"

    book_id = db.Column("bookId", db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    authors = db.relationship("Author", secondary=book_author, back_populates="books")
    categories = db.relationship("Category", secondary=book_category, back_populates="books")
    rental_items = db.relationship("RentalItem", back_populates="book")
    reviews = db.relationship("Review", back_populates="book", cascade="all, delete-orphan")


class Author(db.Model):
    __tablename__ = "authors"

    author_id = db.Column("authorId", db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    biography = db.Column(db.Text)
    books = db.relationship("Book", secondary=book_author, back_populates="authors")


class Category(db.Model):
    __tablename__ = "categories"

    name = db.Column("category", db.String(50), primary_key=True)
    books = db.relationship("Book", secondary=book_category, back_populates="categories")


class Customer(db.Model):
    __tablename__ = "customers"

    customer_id = db.Column("customerId", db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    rental_orders = db.relationship("RentalOrder", back_populates="customer")
    reviews = db.relationship("Review", back_populates="customer", cascade="all, delete-orphan")


class RentalOrder(db.Model):
    __tablename__ = "orders"

    order_id = db.Column("orderId", db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.customerId"), nullable=False)
    rental_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default="BORROWED")
    total_price = db.Column(db.Integer, nullable=False, default=0)
    customer = db.relationship("Customer", back_populates="rental_orders")
    items = db.relationship("RentalItem", back_populates="order", cascade="all, delete-orphan")


class RentalItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.orderId"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.bookId"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column("price", db.Integer, nullable=False)
    order = db.relationship("RentalOrder", back_populates="items")
    book = db.relationship("Book", back_populates="rental_items")


class Review(db.Model):
    __tablename__ = "reviews"

    review_id = db.Column("id", db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.bookId"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.customerId"), nullable=True)
    reviewer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    book = db.relationship("Book", back_populates="reviews")
    customer = db.relationship("Customer", back_populates="reviews")
