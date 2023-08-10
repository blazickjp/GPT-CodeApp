import os
import openai
import pexpect

from dotenv import load_dotenv
from enum import Enum
from typing import Optional, List, Generator
from pydantic import Field, field_validator
from openai_function_call import OpenAISchema
from agent.agent_functions.changes import Changes
from agent.agent_functions.new_file import NewFile

load_dotenv()
DIRECTORY = os.getenv("PROJECT_DIRECTORY")


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
    file_change: Optional[Changes] = Field(
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
