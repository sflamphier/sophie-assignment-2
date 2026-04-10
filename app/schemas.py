import re
from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE
from app.models import Category


class CategorySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    color = fields.Str(load_default=None)

#checking color
# When i was debugging here, it said that the validate_color method is receiving an unexpected data_key argument so we fix this with kwargs
    @validates("color")
    def validate_color(self, value, **kwargs):
        if value is not None and not re.match(r"^#[0-9A-Fa-f]{6}$", value): #using regex to find hex color
            raise ValidationError("Must be a valid hex color code (like this: #FF5733).")

#checking unique name
    @validates("name")
    def validate_unique_name(self, value, **kwargs):
        existing = Category.query.filter_by(name=value).first()
        if existing:
            raise ValidationError("Category with this name already exists.")

# summary schema
class CategorySummarySchema(Schema):
    id = fields.Int()
    name = fields.Str()
    color = fields.Str()

# task schema
class TaskSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(load_default=None, validate=validate.Length(max=500))
    completed = fields.Bool(load_default=False)
    due_date = fields.DateTime(load_default=None, format="iso")
    category_id = fields.Int(load_default=None)
    category = fields.Nested(CategorySummarySchema, dump_only=True)
    created_at = fields.DateTime(dump_only=True, format="iso")
    updated_at = fields.DateTime(dump_only=True, format="iso")

# update schema
class TaskUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(max=500))
    completed = fields.Bool()
    due_date = fields.DateTime(format="iso", allow_none=True)
    category_id = fields.Int(allow_none=True)
