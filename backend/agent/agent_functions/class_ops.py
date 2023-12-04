from instructor import OpenAISchema
from pydantic import Field
import json
import uuid


class AddClass(OpenAISchema):
    """Represents a class to be added to a file."""

    file_name: str = Field(..., description="The name of the file to add the class to.")
    class_name: str = Field(..., description="The name of the class.")
    bases: list[str] = Field([], description="The base classes for the class.")
    body: str = Field(..., description="The body of the class.")
    decorator_list: list[str] = Field(
        [], description="The list of decorators to be applied to the class."
    )
    id: str | None = str(uuid.uuid4())

    def to_json(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            class_name=self.class_name,
            bases=self.bases,
            body=self.body,
            decorator_list=self.decorator_list,
        )
        return "\n\n```json\n" + json.dumps(out, indent=4) + "\n```\n"


class DeleteClass(OpenAISchema):
    """Represents a class to be deleted.

    Attributes:
        file_name (str): The name of the file containing the class to be deleted.
        class_name (str): The name of the class to be deleted.
    """

    file_name: str = Field(
        ..., description="The name of the file containing the class to delete."
    )
    class_name: str = Field(..., description="The name of the class to delete.")
    id: str | None = str(uuid.uuid4())

    def to_json(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            class_name=self.class_name,
        )
        return "\n\n```json\n" + json.dumps(out, indent=4) + "\n```\n"


class ModifyClass(OpenAISchema):
    """Represents a request to modify a Python class. Modifications will override the existing class."""

    file_name: str = Field(
        ..., description="The name of the file containing the class to modify."
    )
    class_name: str = Field(..., description="The name of the class to modify.")
    new_bases: list[str] | None = Field(
        None, description="The new base classes for the class."
    )
    new_body: str | None = Field(
        None,
        description="The new body of the class as a list of statements or a string. This will replace the entire existing body of the class.",
    )
    new_decorator_list: list[str] | None = Field(
        None, description="The new list of decorators for the class."
    )
    new_name: str | None = Field(None, description="The new name for the class.")
    new_args: str | None = Field(None, description="The new arguments for the class.")
    new_docstring: str | None = Field(
        None, description="The new docstring for the function."
    )
    id: str | None = str(uuid.uuid4())

    def to_json(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            class_name=self.class_name,
            new_bases=self.new_bases,
            new_body=self.new_body,
            new_decorator_list=self.new_decorator_list,
            new_name=self.new_name,
            new_args=self.new_args,
        )
        return "\n\n```json\n" + json.dumps(out, indent=4) + "\n```\n"
