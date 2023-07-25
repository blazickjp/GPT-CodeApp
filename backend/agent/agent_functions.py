from openai_function_call import OpenAISchema, openai_function
from pydantic import Field, validator
from typing import Optional, List
import pexpect
import os
from database.my_codebase import get_git_root
import openai

ROOT = get_git_root()


class File(OpenAISchema):
    """
    Correctly named file with contents
    """

    name: str = Field(..., description="The name of the file")
    contents: str = Field(..., description="The contents of the file")

    def save(self) -> None:
        """
        Save the file to the codebase
        """
        path = os.path.join(ROOT, self.name)
        with open(path, "w") as f:
            f.write(self.contents)


class Program(OpenAISchema):
    """
    Set of files that represent a complete and correct program
    """

    files: List[File] = Field(..., description="List of files")


class Shell(OpenAISchema):
    command: str = Field(..., description="The Bash command to run")
    child: pexpect.spawn = Field(
        default_factory=lambda: pexpect.spawn("/bin/bash", echo=False)
    )
    root: str = get_git_root()

    def execute(self):
        self.child.sendline(self.command)
        self.child.expect_exact(self.command)
        self.child.expect_exact("$ ")
        return self.child.before

    class Config:
        arbitrary_types_allowed = True
