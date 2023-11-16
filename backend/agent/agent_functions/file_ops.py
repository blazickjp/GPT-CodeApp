import json
from instructor import OpenAISchema
from pydantic import Field


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

    def to_string(self):
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

    def to_string(self):
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

    def to_string(self):
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


class AddClass(OpenAISchema):
    """Represents a class to be added to a file."""

    file_name: str = Field(..., description="The name of the file to add the class to.")
    class_name: str = Field(..., description="The name of the class.")
    bases: list[str] = Field([], description="The base classes for the class.")
    body: str = Field(..., description="The body of the class.")
    decorator_list: list[str] = Field(
        [], description="The list of decorators to be applied to the class."
    )

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            class_name=self.class_name,
            bases=self.bases,
            body=self.body,
            decorator_list=self.decorator_list,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


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


class ModifyClass(OpenAISchema):
    """Represents a request to modify a Python class. Modifications will override the existing class."""

    file_name: str = Field(
        ..., description="The name of the file containing the class to modify."
    )
    class_name: str = Field(..., description="The name of the class to modify.")
    new_bases: list[str] | None = Field(
        None, description="The new base classes for the class."
    )
    new_body: list | None = Field(
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

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            class_name=self.class_name,
            new_bases=self.new_bases,
            new_body=self.new_body,
            new_decorator_list=self.new_decorator_list,
            new_name=self.new_name,
            new_args=self.new_args,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


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

    def to_string(self):
        out = dict(
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

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            class_name=self.class_name,
            method_name=self.method_name,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class ModifyMethod(OpenAISchema):
    """
    Represents a method modification operation. Modifications will override the existing method.
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

    def to_string(self):
        out = dict(
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


class VariableNameChange(OpenAISchema):
    """
    Represents a request to change the name of a variable. Changes take place over the entire codebase.
    """

    original_name: str = Field(..., description="The original name of the variable.")
    new_name: str = Field(..., description="The new name of the variable.")

    def to_string(self):
        out = dict(original_name=self.original_name, new_name=self.new_name)
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class AddImport(OpenAISchema):
    """
    Represents an import statement to be added to a Python file.
    """

    file_name: str = Field(
        ..., description="The name of the file to add the import to."
    )
    module: str = Field(..., description="The name of the module to import.")
    names: list | None = Field(
        None, description="The names to import from the module. Defaults to None."
    )
    asnames: list | None = Field(
        None, description="The names to import from the module with an alias."
    )
    objects: list | None = Field(
        None, description="The objects to import from the module."
    )

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            module=self.module,
            names=self.names,
            asnames=self.asnames,
            objects=self.objects,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class DeleteImport(OpenAISchema):
    """
    Represents a request to delete one or more imports from a Python module.
    """

    file_name: str = Field(
        ..., description="The name of the file to delete the import from."
    )
    module: str = Field(
        ..., description="The name of the module to delete imports from."
    )
    names: list | None = Field(
        None, description="The names to delete from the module. Defaults to None."
    )
    asnames: list | None = Field(
        None, description="The names to delete from the module with an alias."
    )
    objects: list | None = Field(
        None, description="The objects to delete from the module."
    )

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            module=self.module,
            names=self.names,
            asnames=self.asnames,
            objects=self.objects,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class ModifyImport(OpenAISchema):
    """
    Represents a modification to an import statement in a Python file."""

    file_name: str = Field(
        ..., description="The name of the file containing the import to modify."
    )
    module: str = Field(..., description="The name of the module to modify.")
    new_names: list | None = Field(
        None, description="The new names to import from the module."
    )
    new_asnames: list | None = Field(
        None, description="The new names to import from the module with an alias."
    )
    objects_to_remove: list | None = Field(
        None, description="The old objects to remove."
    )
    objects_to_add: list | None = Field(None, description="The new objects to add.")

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            module=self.module,
            new_names=self.new_names,
            new_asnames=self.new_asnames,
            new_objects=self.new_objects,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


_OP_LIST = [
    AddImport,
    DeleteImport,
    AddFunction,
    DeleteFunction,
    AddClass,
    DeleteClass,
    AddMethod,
    DeleteMethod,
    ModifyFunction,
    ModifyClass,
    ModifyMethod,
    ModifyImport,
    VariableNameChange,
]

_OP_LIST = {cls.__name__: cls for cls in _OP_LIST}
