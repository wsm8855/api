from typing import List, Optional
from pydantic import BaseModel


class TextRequest(BaseModel):
    text: Optional[str]
    questionUno: Optional[str]


class CategoricalRequest(BaseModel):
    categories: List[str]
    age: List[int]
    ethnicities: List[str]
    genders: List[str]
    states: List[str]
