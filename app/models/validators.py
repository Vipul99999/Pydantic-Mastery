from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Self

class UserWithValidators(BaseModel):
    email: str
    password: str = Field(min_length=8)
    confirm_password: str
    age: int = Field(ge=13)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def check_passwords(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords must match")
        return self