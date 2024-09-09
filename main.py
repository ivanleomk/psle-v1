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


class Answer(BaseModel):
    label: str
    answer: Trend | Integer | Float | Fraction | String | TrueFalsePredictions


class MultipleChoiceAnswer(BaseModel):
    label: str
    answer: Literal[1, 2, 3, 4]


answers = [2, 3, 2, 4, 1, 1, 4, 2, 2, 4, 4, 2, 3, 3, 2]

labels = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
]

with open("answers.jsonl", "w") as f:
    for label, answer in zip(labels, answers):
        answer_object = MultipleChoiceAnswer(label=label, answer=answer)

        f.write(answer_object.model_dump_json() + "\n")
