import os
import openai
import pexpect
import numpy as np

from dotenv import load_dotenv
from enum import Enum
from typing import Optional, List, Generator
from pydantic import Field, field_validator
from openai_function_call import OpenAISchema
from diff_match_patch import diff_match_patch


load_dotenv()
DIRECTORY = os.getenv("PROJECT_DIRECTORY")
shell = None


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
        Description of contents:
        {self.description}
        Contents:
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


class Change(OpenAISchema):
    """
    The correct changes to make to a file

    Args:
        line (int): The line number of the change.
        old_string (str): The old string.
        new_string (str): The new string.
    """

    line: int = Field(..., description="The line number of the change.")
    old_string: str = Field(..., description="The old string.")
    new_string: str = Field(..., description="The new string.")

    def __lt__(self, other):
        return self.line < other.line


class Changes(OpenAISchema):
    """
    A list of changes to make to a file.

    Args:
        changes (List[Change]): A list of Change Objects.
    """

    changes: List[Change] = Field(..., description="A list of Change objects.")


class FileChange(OpenAISchema):
    """
    Correctly named file and description of changes.
    Args:
        name (str): The correct name of the file. Name should be a path from the root of the codebase.
        changes (str): A detailed and robust natural language description of the correct changes to be made. Do not write code here.
    """

    name: str = Field(
        ...,
        description="The correct name of the file. Name should be a path from the root of the codebase.",
    )
    changes: str = Field(
        ...,
        description="A detailed and robust natural language description of the correct changes to be made. Do not write code here.",
    )

    def to_dict(self) -> dict:
        return {"name": self.name, "changes": self.changes}

    def apply_changes(self, changes):
        file_path = os.path.join(DIRECTORY, self.name)
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Normalize tabs to spaces (assuming 4 spaces for a tab)
        # This can be adjusted based on the file's style
        lines = [line.replace("\t", "    ") for line in lines]

        for change in sorted(changes):
            # Check for line number mismatch
            if change.line > len(lines):
                # Append changes to file
                lines.append(change.new_string + "\n")
                return "".join(lines)

            # Count the spaces at the beginning of the line
            spaces = 0
            for char in lines[change.line - 1]:
                if char == " ":
                    spaces += 1
                else:
                    break

            # Check if the expected old_string matches the content of the specified line
            if change.old_string.strip() == lines[change.line - 1].strip():
                # Replace the line with the new_string
                lines[change.line - 1] = " " * spaces + change.new_string + "\n"
            else:
                print(
                    f"Warning: Expected content not found at line {change.line}. No changes made."
                )

        # Write the modified content back to the file
        return "".join(lines)

    def save(self) -> None:
        file_path = os.path.join(DIRECTORY, self.name)
        try:
            with open(file_path, "r") as f:
                current_contents = f.read()
                current_contents_with_line_numbers = "\n".join(
                    f"{i+1}: {line}"
                    for i, line in enumerate(current_contents.split("\n"))
                )
        except FileNotFoundError:
            print(
                f"Error: File {self.name} not found at file_path: {file_path}\nDirectory: {DIRECTORY}"
            )
            raise

        prompt = f"""
        Line numbers have been added to the Current File to aid in your response. They are not part of the actual file.
        File Name: {self.name}
        Current File:
        {current_contents_with_line_numbers}
        Changes Requested:
        {self.changes}
        """

        messages = [
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": "Reply with the correct GNU style git patch."},
        ]
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0,
            functions=[Changes.openai_schema],
            function_call={"name": Changes.openai_schema["name"]},
            messages=messages,
            max_tokens=1000,
        )

        changes = Changes.from_response(completion).changes
        new_text = self.apply_changes(changes)

        with open(file_path, "w") as f:
            f.write(new_text)

        # TODO: We should return the diff back to the UI
        dmp = diff_match_patch()
        diff = dmp.patch_make(current_contents, new_text, False)
        return "\n".join(str(d) for d in diff)


class CommandType(Enum):
    BASH_COMMAND = "bash"
    FILE_CHANGE = "file_change"
    NEW_FILE = "new_file"


class CommandResult(OpenAISchema):
    command_id: int
    output: str


class CommandResults(OpenAISchema):
    results: List[CommandResult]


class Command(OpenAISchema):
    id: int = Field(..., description="Unique id of the command")
    command_type: CommandType = Field(..., description="Type of the command")
    dependent_commands: List[int] = Field(
        default_factory=list,
        description="List of the IDs of commands that need to be completed before this command can be executed.",
    )
    command_line: Optional[str] = Field(None, description="Command to execute")
    file_change: Optional[FileChange] = Field(
        None, description="File name and changes you would like to request"
    )
    new_file: Optional[NewFile] = Field(
        None,
        description="""File name (path from root directory), description, and reference
        files (path from root directory) which provide additional context to the AI.""",
    )

    @field_validator("file_change")
    def check_file_change(cls, v, values):
        if (
            "command_type" in values
            and values["command_type"] == CommandType.FILE_CHANGE
            and v is None
        ):
            raise ValueError("file_change is required when command_type is FILE_CHANGE")
        return v

    @field_validator("new_file")
    def check_new_file(cls, v, values):
        if (
            "command_type" in values
            and values["command_type"] == CommandType.NEW_FILE
            and v is None
        ):
            raise ValueError("new_file is required when command_type is FILE_CHANGE")
        return v

    @field_validator("command_line")
    def check_command(cls, v, values):
        if (
            "command_type" in values
            and values["command_type"] == CommandType.BASH_COMMAND
            and v is None
        ):
            raise ValueError("Command is required when command_type is BASH_COMMAND")
        return v

    def execute(self, with_results: CommandResults) -> CommandResult:
        # If a program is set for this command and the command type is PROGRAM, execute the program
        if self.command_type == CommandType.FILE_CHANGE:
            self.file_change.save()
            output = "changes complete"

        if self.command_type == CommandType.NEW_FILE:
            self.new_file.save()
            output = "file created"

        # If the command type is SHELL, execute the command line
        if self.command_type == CommandType.BASH_COMMAND:
            global shell
            if shell is None:
                shell = pexpect.spawn("/bin/bash", timeout=600)
                shell.sendline(f"cd {DIRECTORY}")  # set the working directory

            # Check for potentially dangerous commands
            dangerous_commands = ["rm -rf /", "mkfs", "shutdown", "reboot"]
            if any(command in self.command_line for command in dangerous_commands):
                raise ValueError(
                    "Command cannot contain potentially dangerous commands"
                )

            shell.sendline(self.command_line)
            shell.expect("\\$")  # wait for the command to finish
            output = shell.before.decode()  # get command output

        return CommandResult(command_id=self.id, output=output)


class CommandPlan(OpenAISchema):
    command_graph: List[Command] = Field(
        ...,
        description="List of commands that need to be done to complete the main task.",
    )

    # ... rest of the CommandPlan class ...

    def _get_execution_order(self) -> List[int]:
        """
        Returns the order in which the tasks should be executed using topological sort.
        Inspired by https://gitlab.com/ericvsmith/toposort/-/blob/master/src/toposort.py
        """
        tmp_dep_graph = {
            item.id: set(item.dependent_commands) for item in self.command_graph
        }

        def topological_sort(
            dep_graph: dict[int, set[int]]
        ) -> Generator[set[int], None, None]:
            while True:
                ordered = set(item for item, dep in dep_graph.items() if len(dep) == 0)
                if not ordered:
                    break
                yield ordered
                dep_graph = {
                    item: (dep - ordered)
                    for item, dep in dep_graph.items()
                    if item not in ordered
                }
            if len(dep_graph) != 0:
                raise ValueError(
                    f"Circular dependencies exist among these items: {{{', '.join(f'{key}:{value}' for key, value in dep_graph.items())}}}"
                )

        result = []
        for d in topological_sort(tmp_dep_graph):
            result.extend(sorted(d))
        return result

    def execute(self) -> dict[int, CommandResult]:
        """
        Executes the tasks in the task plan in the correct order using asyncio and chunks with answered dependencies.
        """
        execution_order = self._get_execution_order()
        tasks = {q.id: q for q in self.command_graph}
        task_results = {}
        while True:
            ready_to_execute = [
                tasks[task_id]
                for task_id in execution_order
                if task_id not in task_results
                and all(
                    subtask_id in task_results
                    for subtask_id in tasks[task_id].dependent_commands
                )
            ]
            # prints chunks to visualize execution order
            print(ready_to_execute)
            computed_answers = [
                q.execute(
                    with_results=CommandResults(
                        results=[
                            result
                            for result in task_results.values()
                            if result.command_id in q.dependent_commands
                        ]
                    )
                )
                for q in ready_to_execute
            ]
            for answer in computed_answers:
                task_results[answer.command_id] = answer
            if len(task_results) == len(execution_order):
                break
        return task_results
