import os
import openai
import difflib as dl

from dotenv import load_dotenv
from typing import List, Optional, Tuple
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
        """
        Converts the Change object to a dictionary.
        """
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
    The 'original' field cannot be an empty string.
    When adding new code, include original code to determine where to put the new code.
    The 'updated' field can be blank if you want to delete the old code.
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

    def apply_changes(self, changes: List[Change], content: str) -> str:
        """
        Applies the given changes to the content.
        """
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
                continue
            else:
                content = new_content
        return content

    def count_spaces(self, line: str) -> int:
        """
        Counts the leading spaces in a line of code.
        """
        spaces = 0
        for char in line:
            if char == " ":
                spaces += 1
            else:
                break
        return spaces

    def execute(self) -> str:
        """
        Executes the changes on the file and returns a diff.
        """
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
        # TODO: This could be a point to retry.

        # Return the diff back to the UI
        diff = dl.unified_diff(
            current_contents.splitlines(),
            new_text.splitlines(),
            fromfile="a",
            tofile="b",
            n=0,
        )

        self.save(new_text, file_path)
        return "\n\n```diff\n" + "\n".join(str(d) for d in diff) + "\n```\n\n"

    def save(self, new_text: str, file_path: str) -> None:
        """
        Saves the new text to the file at the given path.
        """
        with open(file_path, "w") as f:
            f.write(new_text)

    def replace_part_with_missing_leading_whitespace(
        self, whole_lines, part_lines, replace_lines
    ):
        """
        This function replaces a part of the original code with new code, while preserving the leading whitespace.
        It first matches the part of the original code that needs to be replaced, then removes the old lines and inserts the new lines with adjusted indentation.
        If no match is found for the part to be replaced, no changes are made.

        Args:
            whole_lines (List[str]): The original lines of code.
            part_lines (List[str]): The lines of code that need to be replaced.
            replace_lines (List[str]): The new lines of code that will replace the old ones.

        Returns:
            str: The updated code with the replaced part.
        """
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

    def match_partial(
        self, original_lines: List[str], partial_lines: List[str]
    ) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        This function matches a part of the original code with a given part.

        Args:
            original_lines (List[str]): The original lines of code.
            partial_lines (List[str]): The lines of code that need to be matched.

        Returns:
            Tuple[Optional[int], Optional[int], Optional[int]]: The start and end indices of the match in the original code and the number of leading spaces in the matched part.
        """
        start = None
        for i, line in enumerate(original_lines):
            if line.lstrip() == partial_lines[0].lstrip():
                spaces = self.count_spaces(line) - self.count_spaces(partial_lines[0])
                start = i
                break
        if start is None:
            return (None, None, None)
        end = start + len(partial_lines)
        # verify the rest of the lines match before returning
        for i, line in enumerate(original_lines[start:end]):
            if line.lstrip() != partial_lines[i].lstrip():
                return (None, None, None)
        return (start, end, spaces)
