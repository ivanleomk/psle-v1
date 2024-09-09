from pathlib import Path
import base64
from typing import Literal
from pydantic import BaseModel
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from instructor import from_openai, from_anthropic
from helpers.models import Answer, answer_types
from asyncio import run, Semaphore
from tqdm.asyncio import tqdm_asyncio as asyncio
import json

# client = from_openai(AsyncOpenAI())
client = from_anthropic(AsyncAnthropic())

prompt = """
You are an expert at solving open ended questions from images. Analyze the given image and answer all questions present in it. Clearly state out the train of thought that you went through to solve the question

Only give the final answer. 

Eg. if the answer is 141232 km/min, just return 141232
"""

multiple_choice_prompt = """
You are an expert at solving multiple choice questions from images. Analyze the given image and answer all questions present in it. Clearly state out the train of thought that you went through to solve the question

Only give the final answer. 

Give the answer as a number between 1 and 4 corresponding to the answer choice.
"""


class PredictedAnswer(BaseModel):
    chain_of_thought: str
    answer: answer_types


class PredictedMultipleChoiceAnswer(BaseModel):
    chain_of_thought: str
    answer: Literal[1, 2, 3, 4]


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def encode_images_in_folder(path):
    image_files = Path(path).glob("*.png")
    image_data = {}
    for img_file in image_files:
        encoded_image = encode_image(img_file)

        id = img_file.name.split(".")[0].split("-")[-1]
        image_data[id] = {
            "filename": id,
            "path": str(img_file),
            "base64_image": encoded_image,
        }

    return image_data


def read_jsonl_file(file_path):
    data = {}
    with open(file_path, "r") as file:
        for line in file:
            json_data = json.loads(line.strip())
            answer = Answer(**json_data)
            data[answer.label] = answer.answer
    return data


async def generate_claude_response(
    image_data, semaphore: Semaphore, is_multiple_choice: bool = False
):
    chosen_prompt = multiple_choice_prompt if is_multiple_choice else prompt
    async with semaphore:
        return await client.chat.completions.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            response_model=PredictedMultipleChoiceAnswer
            if is_multiple_choice
            else PredictedAnswer,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": chosen_prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data["base64_image"],
                            },
                        },
                    ],
                }
            ],
        )


async def generate_oai_response(
    image_data, semaphore: Semaphore, is_multiple_choice: bool = False
):
    chosen_prompt = multiple_choice_prompt if is_multiple_choice else prompt
    async with semaphore:
        return await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": chosen_prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data['base64_image']}"
                            },
                        },
                    ],
                },
            ],
            response_model=PredictedAnswer
            if not is_multiple_choice
            else PredictedMultipleChoiceAnswer,
        )


async def generate_answers(
    images: dict[str, dict], is_multiple_choice: bool
) -> dict[str, PredictedAnswer | PredictedMultipleChoiceAnswer]:
    sem = Semaphore(5)
    tasks = [
        generate_claude_response(images[image_id], sem, is_multiple_choice)
        for image_id in images.keys()
    ]
    results = await asyncio.gather(*tasks)
    return {image_id: result for image_id, result in zip(images.keys(), results)}


def score_answers(
    predicted_answers: dict[str, PredictedAnswer | PredictedMultipleChoiceAnswer],
    answers: Answer,
):
    correct = 0
    incorrect = []
    for answer_id in answers.keys():
        predicted_answer = predicted_answers[answer_id]

        if predicted_answer.answer == answers[answer_id]:
            correct += 1
        else:
            incorrect.append(
                {
                    "id": answer_id,
                    "predicted": predicted_answer.answer,
                    "actual": answers[answer_id],
                    "chain_of_thought": predicted_answer.chain_of_thought,
                }
            )
    return correct, incorrect


if __name__ == "__main__":
    for config in ["B"]:
        PATH = f"./data/2023/{config}"
        image_df = encode_images_in_folder(PATH)

        answers = read_jsonl_file(f"{PATH}/answers.jsonl")
        predicted_answers = run(
            generate_answers(image_df, is_multiple_choice=config == "A")
        )

        correct, incorrect = score_answers(predicted_answers, answers)
        print(
            f"Score {config}: {correct/len(predicted_answers)} - {correct}/{len(predicted_answers)}"
        )
        print(f"Incorrect: {len(incorrect)}")


# # Claude : 12/18 for the Open Ended Questions MCQ : 10/15
# # GPT : 12/18 for the Open Ended Questions MCQ : 7/15
