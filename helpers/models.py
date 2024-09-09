from pydantic import BaseModel
from typing import Literal


class Fraction(BaseModel):
    """
    A fraction with a whole number, numerator, and denominator. It can also be called a Mixed Number

    Eg. 3 1/2 has whole number 3, numerator 1, and denominator 2.
    Eg. 2/3 has whole number 0, numerator 2, and denominator 3.
    """

    whole: int
    numerator: int
    denominator: int


class Float(BaseModel):
    """
    This is used when the question prompts you for a decimal answer
    """

    value: float


class Integer(BaseModel):
    """
    This is used when the question prompts you for a numeric answer or numerals.
    """

    value: int


class String(BaseModel):
    """
    This is used when the question prompts you for a label or the response has to be generated as a string(s)
    """

    value: list[str]


class Trend(BaseModel):
    """
    This is used when the question asks you to identify a trend.
    """

    trend: Literal["increase", "decrease", "no change"]


class TrueFalsePredictions(BaseModel):
    """
    This is used when the question asks you to make a prediction about the truthfulness of a set of statement.


    """

    predictions: list[Literal["True", "False", "Not Possible To Tell"]]


answer_types = Trend | Integer | Float | Fraction | String | TrueFalsePredictions


class Answer(BaseModel):
    label: str
    answer: answer_types | Literal[1, 2, 3, 4]
