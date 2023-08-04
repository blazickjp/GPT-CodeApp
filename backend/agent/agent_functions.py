import os
from dotenv import load_dotenv
import openai
import pexpect
import subprocess
import difflib

from typing import Optional, List, Generator
from database.my_codebase import get_git_root
from pydantic import Field, validator
from openai_function_call import OpenAISchema, openai_function
from enum import Enum


load_dotenv()
DIRECTORY = os.getenv("PROJECT_DIRECTORY")
ROOT = get_git_root(DIRECTORY)
shell = None


class CommandType(Enum):
    BASH_COMMAND = "bash"
    FILE_CHANGE = "file_change"
    NEW_FILE = "new_file"


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
        description="Describe what the file should do and what it should contain.",
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
            path = os.path.join(ROOT, file)
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
        path = os.path.join(ROOT, self.name)
        with open(path, "w") as f:
            f.write(new_contents)


class FileChange(OpenAISchema):
    """
    Correctly named file with contents
    """

    name: str = Field(
        ...,
        description="The name of the file. Name should be a path from the root of the codebase.",
    )
    changes: str = Field(
        ...,
        description="A detailed and robust natural language description of the correct changes to be made. Do not write code here.",
    )

    def save(self) -> None:
        file_path = os.path.join(ROOT, self.name)
        with open(file_path, "r") as f:
            current_contents = f.read()
            current_contents = "\n".join(
                f"{i+1}: {line}" for i, line in enumerate(current_contents.split("\n"))
            )
            print(file_path)
            print(current_contents[0:100])

        prompt = f"""
        Line numbers have been added to the Current File section to aid in your response. They are not part of the actual file.
        File Name: {self.name}
        Current File:
        {current_contents}
        Changes Requested:
        {self.changes}
        Diff:
        """

        messages = [
            {
                "role": "system",
                "content": """
                You are an AI programmer. You will be given a file and a set of changes that need to me made. Please respond
                with the correct diff of the file after the changes have been made. Do not make any changes that haven't been requested.
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
        path = os.path.join(ROOT, self.name)
        new_contents = completion["choices"][0]["message"]["content"]
        with open(path, "w") as f:
            f.write(new_contents)


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

    @validator("file_change", always=True)
    def check_file_change(cls, v, values):
        if (
            "command_type" in values
            and values["command_type"] == CommandType.FILE_CHANGE
            and v is None
        ):
            raise ValueError("file_change is required when command_type is FILE_CHANGE")
        return v

    @validator("new_file", always=True)
    def check_new_file(cls, v, values):
        if (
            "command_type" in values
            and values["command_type"] == CommandType.NEW_FILE
            and v is None
        ):
            raise ValueError("new_file is required when command_type is FILE_CHANGE")
        return v

    @validator("command_line", always=True)
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
