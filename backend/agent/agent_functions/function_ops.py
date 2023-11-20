from instructor import OpenAISchema
from pydantic import Field
import json


class AddFunction(OpenAISchema):
    """
    Represents a function to be added to a Python file.
    """

    file_name: str = Field(
        ..., description="The name of the file to add the function to."
    )
    function_name: str = Field(..., description="The name of the function.")
    args: str = Field(..., description="The arguments of the function.")
    body: str = Field(..., description="The body of the function.")
    decorator_list: list[str] = Field(
        [], description="The list of decorators to be applied to the function."
    )
    returns: str | None = Field(None, description="The return type of the function.")

    def to_json(self):
        out = dict(
            file_name=self.file_name,
            function_name=self.function_name,
            args=self.args,
            body=self.body,
            decorator_list=self.decorator_list,
            returns=self.returns,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class DeleteFunction(OpenAISchema):
    """
    Represents a request to delete a function from the agent.
    """

    file_name: str = Field(
        ..., description="The name of the file containing the function to delete."
    )
    function_name: str = Field(..., description="The name of the function to delete.")

    def to_json(self):
        out = dict(
            file_name=self.file_name,
            function_name=self.function_name,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class ModifyFunction(OpenAISchema):
    """
    A class representing modifications to a function. Modifications will override the existing function.
    """

    file_name: str = Field(
        ..., description="The name of the file containing the function to modify."
    )
    function_name: str = Field(..., description="The name of the function to modify.")
    new_args: str | None = Field(
        None, description="The new arguments for the function."
    )
    arg_types: list[str] | None = Field(
        None, description="The types of the new arguments for the function."
    )
    new_body: str | None = Field(
        None,
        description="The new body of the function. This will overwrite the old body. Always include a full body.",
    )
    new_decorator_list: list[str] | None = Field(
        None, description="The new list of decorators for the function."
    )
    new_returns: str | None = Field(
        None, description="The new return type for the function."
    )
    new_name: str | None = Field(None, description="The new name for the function.")
    new_docstring: str | None = Field(
        None, description="The new docstring for the function."
    )

    def to_json(self):
        out = dict(
            file_name=self.file_name,
            function_name=self.function_name,
            new_args=self.new_args,
            new_body=self.new_body,
            new_decorator_list=self.new_decorator_list,
            new_returns=self.new_returns,
            new_name=self.new_name,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"
