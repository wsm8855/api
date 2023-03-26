from typing import List
from pydantic import BaseModel


class TextRequest(BaseModel):
    text: str


class CategoricalRequest(BaseModel):
    age: List[int]
    ethnicities: List[str]
    genders: List[str]
    states: List[str]
