from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class AuthorInputSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    biography = fields.String(allow_none=True, load_default=None)


class AuthorSchema(AuthorInputSchema):
    id = fields.String(attribute="author_id", dump_only=True)


class CategorySchema(Schema):
    name = fields.String(dump_only=True)


class BookSchema(Schema):
    id = fields.String(attribute="book_id", dump_only=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    price = fields.Integer(required=True, validate=validate.Range(min=0))
    description = fields.String(allow_none=True, load_default=None)
    authors_input = fields.List(
        fields.Nested(AuthorInputSchema),
        data_key="authors",
        load_only=True,
        required=True,
        validate=validate.Length(min=1),
    )
    authors = fields.List(fields.Nested(AuthorSchema), dump_only=True)
    categories_input = fields.List(
        fields.String(validate=validate.Length(min=1, max=50)),
        data_key="categories",
        load_only=True,
        load_default=list,
    )
    categories = fields.List(fields.Nested(CategorySchema), dump_only=True)


class CustomerSchema(Schema):
    id = fields.String(attribute="customer_id", dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=6, max=100))


class RentalItemInputSchema(Schema):
    book_id = fields.String(required=True, data_key="bookId")
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))


class RentalItemSchema(RentalItemInputSchema):
    unit_price = fields.Integer(attribute="unit_price", dump_only=True, data_key="unitPrice")


class RentalOrderCreateSchema(Schema):
    customer_id = fields.String(required=True, data_key="customerId")
    rental_date = fields.Date(required=True, data_key="rentalDate")
    return_date = fields.Date(required=True, data_key="returnDate")
    items = fields.List(
        fields.Nested(RentalItemInputSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if data["return_date"] < data["rental_date"]:
            raise ValidationError({"returnDate": ["Return date must be on or after rental date."]})


class RentalOrderSchema(Schema):
    id = fields.String(attribute="order_id", dump_only=True)
    customer_id = fields.String(data_key="customerId")
    rental_date = fields.Date(data_key="rentalDate")
    return_date = fields.Date(data_key="returnDate")
    status = fields.String(validate=validate.OneOf(["PENDING", "BORROWED", "RETURNED", "OVERDUE", "CANCELLED"]))
    total_price = fields.Integer(data_key="totalPrice")
    items = fields.List(fields.Nested(RentalItemSchema))


class ReviewCreateSchema(Schema):
    customer_id = fields.String(required=True, data_key="customerId")
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.String(allow_none=True, load_default=None)


class ReviewSchema(Schema):
    id = fields.String(attribute="review_id", dump_only=True)
    book_id = fields.String(data_key="bookId")
    customer_id = fields.String(data_key="customerId")
    reviewer_name = fields.String(dump_only=True, data_key="reviewerName")
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.String(allow_none=True)
