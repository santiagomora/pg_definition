from pydantic import BaseModel, validator, ValidationError


class StrictInt:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, validation_info):
        if not isinstance(value, int):
            raise TypeError(f"Value must be an int4, got {type(value).__name__}")
        return value


class MyModel(BaseModel):
    strict_int: StrictInt


# Example Usage
try:
    m = MyModel(strict_int="123")  # Will raise a validation error
except ValidationError as e:
    print("Validation error:", e)

try:
    m = MyModel(strict_int=123.0)  # Will also raise a validation error
except ValidationError as e:
    print("Validation error:", e)

# Correct usage
m = MyModel(strict_int=123)
print("Valid instance:", m)
