import os
from token import OP
from dotenv import load_dotenv
import openai
import pexpect
import subprocess

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


class File(OpenAISchema):
    """
    Correctly named file with contents
    """

    name: str = Field(
        ...,
        description="The name of the file. Name should be a path from the root of the codebase.",
    )
    contents: str = Field(
        ...,
        description="The entire contents of the file. Ensure to include all file contents.",
    )

    def save(self) -> None:
        """
        Save the file to the codebase
        """
        path = os.path.join(ROOT, self.name)
        with open(path, "w") as f:
            f.write(self.contents)


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
        description="A VERY detailed and robust description of the correct changes to be made. Please be as verbose as possible",
    )

    def save(self) -> None:
        with open(os.path.join(ROOT, self.name), "r") as f:
            current_contents = f.read()

        prompt = f"""
        File: {self.name}
        Current contents:
        {current_contents}
        Changes Requested:
        {self.changes}
        Response:
        """

        messages = [
            {
                "role": "system",
                "content": """
                You are an AI Pair Programmer and a world class python developer helping the Human work on a project.
                You will be given a current file and a description of the changes that need to be made. You will then
                make the changes and response with ONLY the contents of the new and COMPLETE file. Make sure you always include
                the complete file contents, not just the changes. Also stick to using the same style and packages from the original file
                unless specifically told not to.
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


class Program(OpenAISchema):
    """
    Set of files that represent a complete and correct program
    """

    files: List[File] = Field(..., description="List of files")


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
    file_change: Optional[FileChange] = Field(None, description="File changes to make")

    @validator("file_change", always=True)
    def check_program(cls, v, values):
        if (
            "command_type" in values
            and values["command_type"] == CommandType.FILE_CHANGE
            and v is None
        ):
            raise ValueError("Program is required when command_type is FILE_CHANGE")
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


# @openai_function
def command_planner(instruction: str) -> CommandPlan:
    """
    Generates a CommandPlan for a given question using the OpenAI API.

    This function sends a chat message to the OpenAI API, asking it to generate a CommandPlan
    for the given question. The CommandPlan is a sequence of command line operations that can be executed
    in a specific order. Each command in the CommandPlan is represented by a Command object,
    which includes the command line to execute and a list of IDs of commands that it depends on.

    Args:
        question (str): The question to generate a CommandPlan for.

    Returns:
        CommandPlan: The generated CommandPlan.

    Raises:
        openai.OpenAIError: If there was a problem with the OpenAI API request.
    """
    messages = [
        {
            "role": "system",
            "content": """
            You are a world class bash command planning algorithm capable of breaking apart tasks into dependant
            subtasks, such that the results of one command can be used to enable the system completing the main task.
            Do not complete the user task, simply provide a correct compute graph with good specific
            commands and relevant subcommands. Before completing the list of tasks, think step by
            step to get a better understanding the problem.""",
        },
        {
            "role": "user",
            "content": f"{instruction}",
        },
    ]

    completion = openai.ChatCompletion.create(
        model="gpt-4-0613",
        temperature=0,
        functions=[CommandPlan.openai_schema],
        function_call={"name": CommandPlan.openai_schema["name"]},
        messages=messages,
        max_tokens=2000,
    )
    root = CommandPlan.from_response(completion)

    return root
