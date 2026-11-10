from dataclasses import dataclass

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    pre_load,
    validate,
    validates,
    validates_schema,
)


@dataclass(frozen=True)
class ProductData:
    sku: str
    name: str
    price_cents: int
    qty_in_stock: int = 0
    description: str | None = None
    archived: bool = False


class ProductOut(Schema):
    id = fields.Int(dump_only=True)
    sku = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    price_cents = fields.Int(dump_only=True)
    qty_in_stock = fields.Int(dump_only=True)
    description = fields.Str(allow_none=True, dump_only=True)
    archived = fields.Bool(dump_only=True)


class ProductIn(Schema):
    sku = fields.Str(
        required=True,
        validate=validate.And(
            validate.Length(min=3, max=32),
            validate.Regexp(r"^[A-Z0-9-]+$"),
        ),
    )
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, validate=validate.Range(min=0))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    archived = fields.Bool(load_default=False)

    @pre_load
    def normalize_input(self, data, **kwargs):
        if not isinstance(data, dict):
            return data

        normalized = data.copy()
        if isinstance(normalized.get("sku"), str):
            normalized["sku"] = normalized["sku"].strip().upper()
        if isinstance(normalized.get("name"), str):
            normalized["name"] = normalized["name"].strip()
        if isinstance(normalized.get("description"), str):
            normalized["description"] = normalized["description"].strip()
        return normalized

    @validates("name")
    def validate_name(self, value, **kwargs):
        if not value:
            raise ValidationError("Name cannot be empty or whitespace.")

    @validates_schema
    def validate_product_rules(self, data, **kwargs):
        # Archived products are unavailable for sale, so they cannot be seeded
        # with sellable stock through the create endpoint.
        if data.get("archived") and data.get("qty_in_stock", 0) > 0:
            raise ValidationError(
                "An archived product cannot have stock in the request.",
                field_name="qty_in_stock",
            )

    @post_load
    def make_product_data(self, data, **kwargs):
        """Convert the validated request dictionary into a domain object."""
        return ProductData(**data)


class ProductPatch(Schema):
    sku = fields.Str(
        validate=validate.And(
            validate.Length(min=3, max=32),
            validate.Regexp(r"^[A-Z0-9-]+$"),
        )
    )
    name = fields.Str(validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(validate=validate.Range(min=0))
    qty_in_stock = fields.Int(validate=validate.Range(min=0))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    archived = fields.Bool()

    @pre_load
    def normalize_input(self, data, **kwargs):
        if not isinstance(data, dict):
            return data

        normalized = data.copy()
        if isinstance(normalized.get("sku"), str):
            normalized["sku"] = normalized["sku"].strip().upper()
        if isinstance(normalized.get("name"), str):
            normalized["name"] = normalized["name"].strip()
        if isinstance(normalized.get("description"), str):
            normalized["description"] = normalized["description"].strip()
        return normalized

    @validates("name")
    def validate_name(self, value, **kwargs):
        if not value:
            raise ValidationError("Name cannot be empty or whitespace.")

    @validates_schema
    def validate_product_rules(self, data, **kwargs):
        if data.get("archived") is True and data.get("qty_in_stock", 0) > 0:
            raise ValidationError(
                "An archived product cannot have stock in the request.",
                field_name="qty_in_stock",
            )


class ReserveIn(Schema):
    qty = fields.Int(required=True, validate=validate.Range(min=1))


class ProductPaginationOut(Schema):
    items = fields.List(fields.Nested(ProductOut), dump_only=True)
    page = fields.Int(dump_only=True)
    size = fields.Int(dump_only=True)
    total = fields.Int(dump_only=True)
    pages = fields.Int(dump_only=True)
