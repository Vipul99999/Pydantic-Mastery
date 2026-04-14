from typing import Generic, TypeVar, Union, Literal, List
from pydantic import BaseModel, Field, Discriminator

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int

class Cat(BaseModel):
    pet_type: Literal["cat"]
    meows: int

class Dog(BaseModel):
    pet_type: Literal["dog"]
    barks: float

PetType = Annotated[Union[Cat, Dog], Field(discriminator="pet_type")]

class Owner(BaseModel):
    name: str
    pet: PetType