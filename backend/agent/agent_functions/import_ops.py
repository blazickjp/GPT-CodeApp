from instructor import OpenAISchema
from pydantic import Field
import json
import uuid


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
    id: str = str(uuid.uuid4())

    def to_json(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            module=self.module,
            names=self.names,
            asnames=self.asnames,
            objects=self.objects,
        )
        return "\n\n```json\n" + json.dumps(out, indent=4) + "\n```\n"


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
    id: str = str(uuid.uuid4())

    def to_json(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            module=self.module,
            names=self.names,
            asnames=self.asnames,
            objects=self.objects,
        )
        return "\n\n```json\n" + json.dumps(out, indent=4) + "\n```\n"


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
    id: str = str(uuid.uuid4())

    def to_json(self):
        out = dict(
            id=self.id,
            file_name=self.file_name,
            module=self.module,
            new_names=self.new_names,
            new_asnames=self.new_asnames,
            new_objects=self.new_objects,
        )
        return "\n\n```json\n" + json.dumps(out, indent=4) + "\n```\n"
