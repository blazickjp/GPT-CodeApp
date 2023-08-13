import os
import openai
import difflib as dl

from dotenv import load_dotenv
from typing import List
from pydantic import Field, field_validator
from openai_function_call import OpenAISchema
import re

load_dotenv()
DIRECTORY = os.getenv("PROJECT_DIRECTORY")


class Change(OpenAISchema):
    """
    The correct changes to make to a file.
    Be mindful of formatting and include the proper newline characters.

    Args:
        original (str): The full code block to be replaced; formatted as a string.
        updated (str): Correct new code to insert; formatted as a string.
    """

    original: str = Field(..., description="Code to be replaced.")
    updated: str = Field(..., description="New code.")

    @field_validator("original")
    def original_must_not_be_blank(cls, v):
        if v == "":
            raise ValueError("Original cannot be blank.")
        return v

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "updated": self.updated,
        }


class Changes(OpenAISchema):
    """
    A list of changes to make to a file.
    Think step by step and ensure the changes cover all requests. Changes will be processed similar to a diff
    of the format:
    >>>>>> ORIGINAL
    old code
    =========
    new code
    <<<<<< UPDATED

    All you need to provide is the old code and new code. The system will handle the rest.
    The original field must not be blank. The updated field can be blank if you want to delete the old code.
    Always use the relative path from the root of the codebase.

    Args:
        file_name (str): The name of the file to be changed. This needs to be the relative path from the root of the codebase.
        thought (str): A description of your thought process.
        changes (List[Change]): A list of Change Objects that represent all the changes you want to make to this file.
    """

    file_name: str = Field(..., description="The name of the file to be changed.")
    thought: str = Field(..., description="A description of your thought process.")
    changes: List[Change] = Field(..., description="A list of Change objects.")

    def to_dict(self) -> dict:
        return [change.to_dict() for change in self.changes]

    def apply_changes(self, changes, content):
        for change in changes:
            # Use regex to find and replace the old string
            if content:
                print("Content exists!!!!!!!!")
                print(f"Type: {type(content)}")
            new_content = self.replace_part_with_missing_leading_whitespace(
                whole_lines=content.split("\n"),
                part_lines=change.original.splitlines(),
                replace_lines=change.updated.splitlines(),
            )
            if not new_content:
                print(f"Failed on change: {change.to_dict()}")
                raise Exception("Failed to apply changes.")

            if new_content == content:
                print("Warning: Expected content not found. No changes made.")
                print(f"Expected: {change.original}")
                print(f"Actual: {content}")
                return None
            else:
                content = new_content
        return content

    def fuzzy_replace(target_text, old_string, new_string):
        # Normalize the old_string by converting all whitespace to spaces
        normalized_old_string = re.sub(r"\s", " ", old_string)

        # Create a search pattern that treats spaces, tabs, and newlines interchangeably
        search_pattern = re.sub(r" +", r"\\s+", normalized_old_string)
        # Replace using the flexible pattern
        result_text = re.sub(search_pattern, new_string, target_text)

        return result_text

    def count_spaces(self, line):
        spaces = 0
        for char in line:
            if char == " ":
                spaces += 1
            else:
                break
        return spaces

    def execute(self) -> None:
        relative_path = self.file_name.lstrip("/")
        file_path = os.path.join(DIRECTORY, relative_path)
        print(f"Directory: {DIRECTORY}")
        print(f"File Path: {file_path}")
        try:
            with open(file_path, "r") as f:
                current_contents = f.read()
                current_contents_with_line_numbers = "\n".join(
                    [
                        f"{i+1} {line}"
                        for i, line in enumerate(current_contents.splitlines())
                    ]
                )
        except FileNotFoundError:
            print(
                f"Error: File {self.file_name} not found at file_path: {file_path}\nDirectory: {DIRECTORY}"
            )
            return "Invalid File Name. Files should be named relative to the root of the codebase and already exist."
        except Exception as e:
            print(e)
            return "Error: File could not be read. Please try again."

        new_text = self.apply_changes(self.changes, current_contents)
        # if not new_text:
        # raise
        # print("\n\n*****   First attempt failed... retrying! *****\n\n")
        # prompt = f"""
        # Line numbers have been added to the Current File to aid in your response. They are not part of the actual file.
        # File Name:
        # {self.file_name}
        # Current File:
        # {current_contents_with_line_numbers}
        # Changes Requested:
        # {self.changes}
        # """

        # messages = [
        #     {
        #         "role": "system",
        #         "content": prompt,
        #     },
        #     {
        #         "role": "user",
        #         "content": """
        #         Reply with the correct changes. Make sure you include any and all new imports.
        #         There should be one Change Object for each block of code you are changing.
        #         Adhere to standard formatting conventions and avoid putting all new code at the
        #         end of the file.
        #         """,
        #     },
        # ]
        # try:
        #     completion = openai.ChatCompletion.create(
        #         model="gpt-4",
        #         temperature=0,
        #         functions=[Changes.openai_schema],
        #         function_call={"name": Changes.openai_schema["name"]},
        #         messages=messages,
        #         max_tokens=1000,
        #     )
        # except openai.error.OpenAIError as e:
        #     print(e)
        #     print(e.response)
        #     return "Error: OpenAI API Error. Please try again."

        # changes = Changes.from_response(completion).changes
        # print([change.to_dict() for change in changes])
        # new_text = self.apply_changes(changes)

        # Return the diff back to the UI
        diff = dl.unified_diff(
            current_contents.splitlines(),
            new_text.splitlines(),
            fromfile="a",
            tofile="b",
            n=0,
        )

        self.save(new_text, file_path)
        return "\n```diff\n" + "\n".join(str(d) for d in diff) + "\n```\n\n"

    def save(self, new_text, file_path) -> None:
        with open(file_path, "w") as f:
            f.write(new_text)

    def replace_part_with_missing_leading_whitespace(
        self, whole_lines, part_lines, replace_lines
    ):
        start, end, spaces = self.match_partial(whole_lines, part_lines)
        if start is None:
            print("No match found, not making changes")
            return "\n".join(whole_lines)

        # remove old lines
        del whole_lines[start:end]
        # add new lines and adjust indentation
        for i, line in enumerate(replace_lines):
            whole_lines.insert(start + i, spaces * " " + line)

        return "\n".join(whole_lines)

    def match_partial(self, original_lines, partial_lines):
        for i, line in enumerate(original_lines):
            if line.lstrip() == partial_lines[0].lstrip():
                spaces = self.count_spaces(line) - self.count_spaces(partial_lines[0])
                start = i
                break
        if not start:
            return (None, None, None)
        end = start + len(partial_lines)
        # verify the rest of the lines match before returning
        for i, line in enumerate(original_lines[start:end]):
            if line.lstrip() != partial_lines[i].lstrip():
                return (None, None, None)
        return (start, end, spaces)
