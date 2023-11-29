from instructor import OpenAISchema
from pydantic import Field
import json
import uuid


class AddMethod(OpenAISchema):
    """
    Represents a method to be added to a class.
    """

    file_name: str = Field(
        ...,
        description="The name of the file containing the class to add the method to.",
    )
    class_name: str = Field(
        ..., description="The name of the class to add the method to."
    )
    method_name: str = Field(..., description="The name of the method.")
    args: str = Field(..., description="The arguments of the method.")
    body: str = Field(..., description="The body of the method.")
    decorator_list: list[str] = Field(
        [], description="The list of decorators to be applied to the method."
    )
    returns: str | None = Field(None, description="The return type of the method.")
    id: str = str(uuid.uuid4())

    def to_json(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            class_name=self.class_name,
            method_name=self.method_name,
            args=self.args,
            body=self.body,
            decorator_list=self.decorator_list,
            returns=self.returns,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class DeleteMethod(OpenAISchema):
    """Represents a method to be deleted from a class."""

    file_name: str = Field(
        ...,
        description="The name of the file containing the class to delete the method from.",
    )

    class_name: str = Field(
        ..., description="The name of the class to delete the method from."
    )
    method_name: str = Field(..., description="The name of the method to delete.")
    id: str = str(uuid.uuid4())

    def to_string(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            class_name=self.class_name,
            method_name=self.method_name,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class ModifyMethod(OpenAISchema):
    """
    Represents a method modification operation. Modifications will override the existing method, do not provide Partial values.
    """

    file_name: str = Field(
        ...,
        description="The name of the file containing the class to modify the method in.",
    )
    class_name: str = Field(
        ..., description="The name of the class to modify the method in."
    )
    method_name: str = Field(..., description="The name of the method to modify.")
    new_args: str | None = Field(None, description="The new arguments for the method.")
    new_body: str | None = Field(
        None,
        description="The new body of the method as a string. This will replace the entire existing body of the method.",
    )
    new_decorator_list: list[str] | None = Field(
        None, description="The new list of decorators for the method."
    )
    new_method_name: str | None = Field(
        None, description="The new name for the method."
    )
    new_returns: str | None = Field(
        None, description="The new return type for the method."
    )
    new_docstring: str | None = Field(
        None, description="The new docstring for the function."
    )
    id: str = str(uuid.uuid4())

    def to_json(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            class_name=self.class_name,
            method_name=self.method_name,
            new_args=self.new_args,
            new_body=self.new_body,
            new_decorator_list=self.new_decorator_list,
            new_method_name=self.new_method_name,
            new_returns=self.new_returns,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"
