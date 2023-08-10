import os
import openai

from dotenv import load_dotenv
from pydantic import Field
from openai_function_call import OpenAISchema
from typing import List


load_dotenv()
DIRECTORY = os.getenv("PROJECT_DIRECTORY")


class NewFile(OpenAISchema):
    """
    Correctly named file with contents
    """

    name: str = Field(
        ...,
        description="The name of the file. Name should be a path from the root of the codebase.",
    )
    description: str = Field(
        ...,
        description="Describe the contents of the file in natural language. Add clarifying details when necessary. Think before you write!",
    )
    reference_files: List[str] = Field(
        ...,
        description="""
        A list of reference files which already exist.
        These files will be provided to the AI to aid in creating the new file you are requesting.
        """,
    )

    def save(self) -> None:
        """
        Save the file to the codebase
        """
        relevent_file_contents = ""
        for file in self.reference_files:
            path = os.path.join(DIRECTORY, file)
            with open(path, "r") as f:
                contents = f.read()
                relevent_file_contents += path + "\n" + contents + "\n\n"

        prompt = f"""
        New File Name: {self.name}
        Relevant Files:
        {relevent_file_contents}
        Description of new file content:
        {self.description}
        New File Content:
        """

        messages = [
            {
                "role": "system",
                "content": """
                You are an AI programmer. You are being requested to create a new file within a codebase in support of a new feature
                and will be provided with the file name and a description of what the contents of that file should be. Respond back with
                the entire contents of the new file. Please make sure to write clear, concise, and correct code.
                """,
            },
            {"role": "user", "content": prompt},
        ]
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0.2,
            messages=messages,
            max_tokens=3000,
        )
        new_contents = completion["choices"][0]["message"]["content"]
        path = os.path.join(DIRECTORY, self.name)
        with open(path, "w") as f:
            f.write(new_contents)
