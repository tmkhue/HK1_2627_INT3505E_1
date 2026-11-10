from marshmallow import Schema, fields, validate

# output
class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    price_cents = fields.Float()
    qty_in_stock = fields.Int()
    description = fields.Str(allow_none=True)
    archived = fields.Bool()

#input
class ProductIn(Schema):
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, validate=validate.Range(min=0))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    archived = fields.Bool()

class ProductPatch(Schema):
    sku = fields.Str(allow_none=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(allow_none=True, validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(allow_none=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(allow_none=True, validate=validate.Range(min=0))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    archived = fields.Bool(allow_none=True, )

class ReserveIn(Schema):
    qty = fields.Int(required=True, validate=validate.Range(min=1))

# Pagination schema
class ProductPaginationOut(Schema):
    items = fields.List(fields.Nested(ProductOut))
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    size = fields.Int(load_default=5, validate=validate.Range(min=1, max=100))
    total = fields.Int()
    pages = fields.Int()

class PaginationSchema(Schema):
    page = fields.Int(
        load_default=1,
        validate=validate.Range(min=1)
    )
    size = fields.Int(
        load_default=20,
        validate=validate.Range(min=1, max=100)
    )