import os
import openai
import difflib as dl

from dotenv import load_dotenv
from typing import List
from pydantic import Field
from openai_function_call import OpenAISchema

load_dotenv()
DIRECTORY = os.getenv("PROJECT_DIRECTORY")


class Change(OpenAISchema):
    """
    The correct changes to make to a file. Use the line numbers from the given context

    Args:
        starting_line (int): The first line number of the change.
        old_string (str): The full and correct code block to be replaced; formatted as a string.
        new_string (str): Correct new code to insert; formatted as a string.
    """

    starting_line: int = Field(..., description="The first line number of the change.")
    old_string: str = Field(..., description="The old string.")
    new_string: str = Field(..., description="The new string.")

    def __lt__(self, other):
        return self.starting_line < other.starting_line

    def to_dict(self) -> dict:
        return {
            "line": self.starting_line,
            "old_string": self.old_string,
            "new_string": self.new_string,
        }


class Changes(OpenAISchema):
    """
    A list of changes to make to a file.
    Make sure the old_string matches the current content.
    Think step by step and ensure the changes cover all requests.


    Args:
        file_name (str): The name of the file to be changed.
        thought (str): A description of your thought process.
        changes (List[Change]): A list of Change Objects that represent all the changes you want to make to this file.
    """

    file_name: str = Field(..., description="The name of the file to be changed.")
    thought: str = Field(..., description="A description of your thought process.")
    changes: List[Change] = Field(..., description="A list of Change objects.")

    def to_dict(self) -> dict:
        return [change.to_dict() for change in self.changes]

    def apply_changes(self, changes):
        # Normalize tabs to spaces (assuming 4 spaces for a tab)
        # This can be adjusted based on the file's style
        relative_path = self.file_name.lstrip("/")
        file_path = os.path.join(DIRECTORY, relative_path)
        with open(file_path, "r") as f:
            lines = f.readlines()

        for change in sorted(changes):
            # Check for line number mismatch
            if change.starting_line > len(lines):
                # Append changes to file
                lines.append(change.new_string + "\n")
                return "".join(lines)

            lines = [line.replace("\t", "    ") for line in lines]

            # Attempt to apply changes with the original line number
            lines, success = self.apply_changes_with_line_number(
                lines, change.starting_line, change.new_string, change.old_string
            )

            if not success:
                # Retry with an offset of +1
                lines, success = self.apply_changes_with_line_number(
                    lines,
                    change.starting_line + 1,
                    change.new_string,
                    change.old_string,
                )

            if not success:
                # Retry with an offset of -1
                lines, success = self.apply_changes_with_line_number(
                    lines,
                    change.starting_line - 1,
                    change.new_string,
                    change.old_string,
                )

            if not success:
                # Handle the case where all retries failed
                # You can raise an exception or log an error message here
                return None

        # Write the modified content back to the file
        return "".join(lines)

    def apply_changes_with_line_number(
        self, lines, starting_line, new_string, old_string
    ):
        # Check for a match to the old string
        if lines[starting_line - 1].strip() != old_string.strip():
            print(f"Found Text: {lines[starting_line - 1]}")
            print(f"Expected Text: {old_string}")
            return lines, False

        # Adjust the line numbering based on the code block length
        spaces = self.count_spaces(lines[starting_line - 1])
        old_code_block_lines = len(old_string.strip().split("\n"))

        # remove the old code block
        del lines[starting_line - 1 : starting_line - 1 + old_code_block_lines]

        # Insert the new code block
        lines = (
            lines[: starting_line - 1]
            + [" " * spaces + new_string.lstrip() + "\n"]
            + lines[starting_line - 1 :]
        )

        # Check if the changes were successfully applied
        # You can add your own logic here based on your requirements
        return lines, True

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
        except FileNotFoundError:
            print(
                f"Error: File {self.file_name} not found at file_path: {file_path}\nDirectory: {DIRECTORY}"
            )
            return "Invalid File Name. Files should be named relative to the root of the codebase and already exist."

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
        print([change.to_dict() for change in self.changes])
        new_text = self.apply_changes(self.changes)

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
