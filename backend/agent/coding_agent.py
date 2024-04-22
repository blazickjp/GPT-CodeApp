# import os
"""
This Python module defines the classes and functions used by the coding agent in the backend of an application. The coding agent is responsible for interacting with various components such as the database, memory management system, and external APIs to facilitate code generation, manipulation, and management tasks. It utilizes models for code generation, applies AST (Abstract Syntax Tree) operations to modify code, and manages the working context and system prompts for the user. Additionally, it handles the execution of generated code operations and integrates with external services like OpenAI and AWS for enhanced functionality.
"""

import re
import json
import boto3
import difflib
import ast

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from types import SimpleNamespace
from pathlib import Path

from agent.agent_functions.ast_ops import ASTChangeApplicator

from database.my_codebase import MyCodebase
from agent.agent_prompts import (  # noqa
    CHANGES_SYSTEM_PROMPT,
    DEFAULT_SYSTEM_PROMPT,
    PROFESSOR_SYNAPSE,
)


class Message(BaseModel):
    role: str
    content: str

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
        }


class NestedNamespace(SimpleNamespace):
    """
    A class to convert a dictionary into a nested namespace.
    """

    def __init__(self, dictionary, **kwargs):
        if not isinstance(dictionary, dict):
            raise ValueError("Input must be a dictionary")
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            elif isinstance(value, list) and all(isinstance(i, dict) for i in value):
                self.__setattr__(key, [NestedNamespace(i) for i in value])
            else:
                self.__setattr__(key, value)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return None


class CodingAgent:
    """
    A class to represent a coding agent that uses OpenAI's GPT-3 model to generate code.

    Attributes:
        memory_manager (MemoryManager): Manages the memory of the agent.
        functions (Optional[List[dict]]): A list of functions that the agent can call.
        callables (Optional[List[Callable]]): A list of callable functions.
        GPT_MODEL (str): The GPT-3 model used by the agent.
        function_map (dict): A dictionary mapping function names to their callable objects.
    """

    def __init__(
        self,
        memory_manager,
        function_map: Optional[dict] = None,
        codebase: Optional[MyCodebase] = None,
    ):
        """
        Constructs all the necessary attributes for the CodingAgent object.

        Args:
            memory_manager (MemoryManager): Manages the memory of the agent.
            functions (Optional[List[dict]]): A list of functions that the agent can call.
            callables (Optional[List[Callable]]): A list of callable functions.
        """

        self.memory_manager = memory_manager
        self.function_map = function_map
        self.GPT_MODEL = "gpt-4-turbo"
        self.codebase = codebase
        self.max_tokens = 4000
        self.temperature = 0.2
        self.tool_choice = "auto"
        self.function_to_call = None
        self.ops_to_execute = []
        self.client = instructor.patch(OpenAI())
        if function_map:
            self.tools = [
                {"type": "function", "function": op.openai_schema}
                for op in self.function_map[0].values()
            ]
        else:
            self.tools = None

    def query(self, input: str, command: Optional[str] = None) -> List[str]:
        """
        Queries the GPT-3 model with the given input and command.

        Args:
            input (str): The input text to be processed by the GPT-3 model.
            command (Optional[str]): The command to be executed by the agent.

        Returns:
            List[str]: The output generated by the GPT-3 model.
        """
        print(f"Input Text: {input}\nCommand: {command}")
        self.memory_manager.add_message("user", input)

        message_history = [
            {"role": i["role"], "content": i["content"]}
            for i in self.memory_manager.get_messages()
        ]

        keyword_args = {
            "model": self.GPT_MODEL,
            "messages": message_history,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,
        }

        print("Message Count: ", len(keyword_args["messages"]))

        # Override normal function calling when function_name is providednd}")
        if command and command.lower() == "changes":
            function_name = None
            json_accumulator = ""
            idx = None
            keyword_args["tools"] = self.tools
            keyword_args["tool_choice"] = "auto"
            print(keyword_args["tools"])

            self.memory_manager.prompt_handler.identity = CHANGES_SYSTEM_PROMPT
            self.memory_manager.prompt_handler.set_system()
            temp_system = self.memory_manager.prompt_handler.system

            self.memory_manager.prompt_handler.identity = DEFAULT_SYSTEM_PROMPT
            self.memory_manager.prompt_handler.set_system()

            assert keyword_args["messages"][0]["role"] == "system"
            keyword_args["messages"][0]["content"] = temp_system

        # Call the model
        print(f"Calling model: {self.GPT_MODEL}")
        for i, chunk in enumerate(self.call_model_streaming(command, **keyword_args)):
            if isinstance(chunk, dict):
                chunk = NestedNamespace(chunk)

            delta = chunk.choices[0].delta
            if delta.tool_calls:
                # Initialize json_accumulator and idx outside the loop
                for call in delta.tool_calls:
                    # Check if we have started a new function call
                    if call.index != idx:
                        # Process the previous function call if any
                        if function_name and json_accumulator:
                            try:
                                data = json.loads(json_accumulator)
                                completed_op = self.function_map[0][function_name](
                                    **data
                                )
                                self.ops_to_execute.append(completed_op)
                                return_string = completed_op.to_json()
                                yield return_string
                            except json.JSONDecodeError as e:
                                pass
                        # Now reset for the new call
                        idx = call.index
                        json_accumulator = call.function.arguments
                        function_name = call.function.name  # Set the new function name
                        print(f"Function Name: {function_name}")
                    else:
                        # Continue accumulating JSON string for the current function call
                        yield call.function.arguments
                        json_accumulator += call.function.arguments
                        # print(f"JSON Accumulator (continued): {json_accumulator}")

                # After the loop, process the final function call if any
                if function_name and json_accumulator:
                    try:
                        data = json.loads(json_accumulator)
                        completed_op = self.function_map[0][function_name](**data)
                        self.ops_to_execute.append(completed_op)
                        return_string = completed_op.to_json()

                        yield return_string
                    except json.JSONDecodeError as e:
                        pass
            else:
                # Process normal text response
                yield chunk.choices[0].delta.content

    def execute_ops(self, ops: List[dict]):
        """
        Executes the operations stored in the `ops_to_execute` list.

        This method iterates over each operation in `ops_to_execute`, applying the necessary changes to the
        corresponding file. It handles file path normalization, reads the original code, applies the AST changes,
        computes the diff between the original and transformed code, and finally writes the transformed code back to the file.
        It accumulates and returns a list of diffs for each operation.

        Args:
            ops (List[dict]): A list of operations to be executed.

        Returns:
            List[str]: A list of unified diff strings representing the changes made to each file.
        """
        diffs = []  # List to store the diffs for each operation

        for op in self.ops_to_execute:
            print(f"Executing operation: {op.id}")
            if "backend" in op.file_name:
                op.file_name = Path(self.codebase.directory).join(
                    op.file_name.replace("backend/", "")
                )

            op.file_name = self.normalize_path(op.file_name)

            # Read the existing code from the file
            try:
                with open(op.file_name, "r") as file:
                    original_code = file.read()
            except FileNotFoundError:
                print(f"File not found: {op.file_name}")
                continue

            # Parse the original code into an AST
            ast_tree = ast.parse(original_code)

            # Create an ASTChangeApplicator to apply the changes
            applicator = ASTChangeApplicator(ast_tree)

            # Apply the operation to the AST tree
            transformed_code = applicator.apply_changes([op])

            # Compute the diff
            diff = difflib.unified_diff(
                original_code.splitlines(keepends=True),
                transformed_code.splitlines(keepends=True),
                fromfile="before.py",
                tofile="after.py",
            )
            diff_string = "".join(diff)
            diffs.append(diff_string)
            print(f"Diff: {diff_string}")

            # Write the transformed code back to the file
            with open(op.file_name, "w") as file:
                file.write(transformed_code)

            # self.ops_to_execute = [op for op in self.ops_to_execute if op != op]

        return diffs

    def process_json(self, args: str) -> str:
        """
        Process a JSON string, handling any triple-quoted strings within it.

        Args:
            args (str): The JSON string to process.

        Returns:
            str: The processed JSON string.
        """
        try:
            # Attempt to load the JSON string
            response = json.loads(args)
            return response
        except json.decoder.JSONDecodeError:
            # If there's a JSONDecodeError, it may be due to triple-quoted strings
            # Find all occurrences of triple-quoted strings
            triple_quoted_strings = re.findall(r"\"\"\"(.*?)\"\"\"", args, re.DOTALL)

            # For each occurrence, replace newlines and triple quotes
            for tqs in triple_quoted_strings:
                # Replace newlines and double quotes within the triple-quoted string
                fixed_string = tqs.replace("\n", "\\n").replace('"', '\\"')
                # Replace the original triple-quoted string with the fixed string
                response_str = args.replace(tqs, fixed_string)

            # Now replace the triple quotes with single quotes
            response_str = args.replace('"""', '"')

            return json.loads(response_str)

    def call_model_streaming(self, command: Optional[str] | None = None, **kwargs):
        if command:
            kwargs["prompt"] = command

        kwargs["stream"] = True
        kwargs["max_tokens"] = kwargs.get("max_tokens", 256)
        kwargs["temperature"] = kwargs.get("temperature", 0.5)

        if "model" not in kwargs:
            raise ValueError("Model not specified in kwargs")

        if self.GPT_MODEL.startswith("gpt") or self.GPT_MODEL is None:
            print("Calling OpenAI")
            for chunk in self.client.chat.completions.create(**kwargs):
                yield chunk

        elif self.GPT_MODEL == "anthropic":
            print("Calling anthropic")
            try:
                print(self.generate_anthropic_prompt())
                sm_client = boto3.client("bedrock-runtime", region_name="us-west-2")
                resp = sm_client.invoke_model_with_response_stream(
                    accept="*/*",
                    contentType="application/json",
                    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                    body=json.dumps(
                        {
                            "messages": kwargs["messages"][1:],
                            "system": self.generate_anthropic_prompt(),
                            "max_tokens": max(kwargs["max_tokens"], 2000),
                            "temperature": kwargs["temperature"],
                            "anthropic_version": "bedrock-2023-05-31",
                        }
                    ),
                )
            except Exception as e:
                print(f"Error calling Anthropic Models: {e}")
                yield {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "delta": {"content": "Error: " + str(e)},
                        }
                    ]
                }

            while True:
                try:
                    chunk = next(iter((resp["body"])))
                    bytes_to_send = chunk["chunk"]["bytes"]
                    decoded_str = json.loads(bytes_to_send.decode("utf-8"))
                    event_type = decoded_str["type"]
                    if event_type == "message_stop":
                        yield {
                            "choices": [
                                {"finish_reason": "stop", "delta": {"content": ""}}
                            ]
                        }
                        break
                    elif event_type == "content_block_delta":
                        content = decoded_str["delta"]["text"]
                        yield {
                            "choices": [
                                {"finish_reason": None, "delta": {"content": content}}
                            ]
                        }

                except StopIteration:
                    break

                except UnboundLocalError:
                    print("UnboundLocalError")
                    break

        else:
            print("Invalid model specified")

    def generate_anthropic_prompt(self) -> str:
        """
        Generates a prompt for the Gaive model.

        Args:
            input (str): The input text to be processed by the GPT-3 model.

        Returns:
            str: The generated prompt.
        """

        self.memory_manager.prompt_handler.set_files_in_prompt(anth=True)

        if self.memory_manager.prompt_handler.system_file_contents:
            file_context = (
                "The human as loadedd the following files into context to help give you background related to the most recent request. They are contained in the <file-contents> XML Tags.\n<file-contents>\n"
                + self.memory_manager.prompt_handler.system_file_contents
                + "\n</file-contents>\n\n"
            )
        else:
            file_context = ""
        if self.memory_manager.prompt_handler.tree:
            tree = (
                "The working directory of the human is always loaded into context. This information is good background when the human is working on the project, but this may not always be the case. Sometimes the human may ask questions not related to the current project <directory-tree> XML Tags\n<directory-tree>\n"
                + self.memory_manager.prompt_handler.tree
                + "\n</directory-tree>\n\n"
            )
        else:
            tree = ""

        sys_prompt = tree + file_context + self.memory_manager.identity

        return sys_prompt
        # return sys_prompt + "\n\n" + last_user_message + "\n\nAssistant: "

    @staticmethod
    def normalize_path(input_path):
        """
        Normalizes a path to be relative to the current working directory.

        Args:
            input_path (str): The path to normalize.

        Returns:
            str: The normalized path.
        """
        # Get the current working directory as a Path object
        working_directory = Path.cwd()

        # Create a Path object from the input path
        input_path_obj = Path(input_path)

        # Resolve the input path (make it absolute and resolve any symlinks)
        resolved_input_path = input_path_obj.resolve()

        # Make the path relative to the working directory, if possible
        try:
            relative_path = resolved_input_path.relative_to(working_directory)
            return str(relative_path)
        except ValueError:
            # The input path is not a subpath of the working directory
            return str(resolved_input_path)
