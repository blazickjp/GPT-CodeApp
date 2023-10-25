# import os
import io
import re
import openai
import json
import os
import boto3

# import time

from typing import List, Optional, Callable
from pydantic import BaseModel
from database.my_codebase import MyCodebase

# from agent.agent_functions import Program, File

# GPT_MODEL = "gpt-3.5-turbo-0613"  # or any other chat model you want to use
GPT_MODEL = "gpt-4"  # or any other chat model you want to use
# GPT_MODEL = "anthropic"  # or any other chat model you want to use
MAX_TOKENS = 2000  # or any other number of tokens you want to use
TEMPERATURE = 0.2  # or any other temperature you want to use


class FunctionCall(BaseModel):
    name: Optional[str] = None
    arguments: str = ""


class Message(BaseModel):
    role: str
    content: str

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
        }


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
        functions: Optional[List[dict]] = None,
        callables: Optional[List[Callable]] = None,
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
        self.functions = functions
        self.callables = callables
        self.GPT_MODEL = GPT_MODEL
        self.codebase = codebase
        self.buff = io.BytesIO()
        self.read_pos = 0
        if callables:
            self.function_map = {
                func.__name__: func for func in callables if func is not None
            }

    def query(self, input: str, command: Optional[str] = None) -> List[str]:
        """
        Queries the GPT-3 model with the given input and command.

        Args:
            input (str): The input text to be processed by the GPT-3 model.
            command (Optional[str]): The command to be executed by the agent.

        Returns:
            List[str]: The output generated by the GPT-3 model.
        """
        print(f"Input Text: {input}")
        self.memory_manager.add_message("user", input)
        message_history = [
            Message(**i).to_dict() for i in self.memory_manager.get_messages()
        ]
        function_to_call = FunctionCall()

        keyword_args = {
            "model": self.GPT_MODEL,
            "messages": message_history,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "stream": True,
        }
        if self.functions:
            keyword_args["functions"] = self.functions
            keyword_args["function_call"] = "auto"

        # Override normal function calling when function_name is provided
        if command:
            if command not in self.function_map:
                raise ValueError(f"Function {command} not registered with Agent")

            keyword_args["functions"] = [self.function_map.get(command).openai_schema]
            keyword_args["function_call"] = {"name": command}

            if command == "Changes":
                # self.memory_manager.identity = (
                #     self.memory_manager.identity
                #     + "\nLine numbers have been added to the Current File to aid in your response. They are not part of the actual file."
                # )
                # self.set_files_in_prompt(include_line_numbers=True)
                keyword_args["model"] = "gpt-4"

        for i, chunk in enumerate(self.call_model_streaming(**keyword_args)):
            delta = chunk["choices"][0].get("delta", {})
            if "function_call" in delta:
                if "name" in delta.function_call:
                    function_to_call.name = delta.function_call["name"]
                if "arguments" in delta.function_call:
                    if function_to_call.name == "Changes" and i == 0:
                        yield "\n```json\n" + delta.function_call["arguments"]
                    else:
                        function_to_call.arguments += delta.function_call["arguments"]
                        yield delta.function_call["arguments"]
            if chunk["choices"][0]["finish_reason"] == "stop" and function_to_call.name:
                if function_to_call.name == "Changes":
                    yield "```\n\n"

                args = self.process_json(function_to_call.arguments)
                function_response = self.function_map[function_to_call.name](**args)
                if function_to_call.name == "Changes":
                    diff = function_response.execute()
                    # Show the diff back to the user
                    yield diff
            else:
                yield delta.get("content")

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

    def generate_llama_prompt(self) -> str:
        """
        Generates a prompt for the Code Llama model.

        Args:
            input (str): The input text to be processed by the GPT-3 model.

        Returns:
            str: The generated prompt.
        """
        prompt = f"### System Prompt\n{self.memory_manager.system}\n\n"
        for message in self.memory_manager.get_messages():
            if message["role"].lower() == "user":
                prompt += f"### User Message\n{message['content']}\n\n"
            if message["role"].lower() == "assistant":
                prompt += f"### Assistant\n{message['content']}\n\n"

        return prompt + "### Assistant"

    def generate_anthropic_prompt(self) -> str:
        """
        Generates a prompt for the Gaive model.

        Args:
            input (str): The input text to be processed by the GPT-3 model.

        Returns:
            str: The generated prompt.
        """
        prompt = f"\n\nHuman: {self.memory_manager.system}\n\n"
        user_messages = 0
        for message in self.memory_manager.get_messages():
            if message["role"].lower() == "user":
                if user_messages == 0:
                    prompt += f"{message['content']}\n\n"
                    user_messages += 1
                else:
                    prompt += f"Human: {message['content']}\n\n"
            if message["role"].lower() == "assistant":
                prompt += f"Assistant: {message['content']}\n\n"

        return prompt + "Assistant:"

    def call_model_streaming(self, **kwargs):
        self.read_pos = 0
        if self.GPT_MODEL == "gpt-4" or self.GPT_MODEL == "gpt-3.5-turbo":
            for chunk in openai.ChatCompletion.create(**kwargs):
                yield chunk
        if self.GPT_MODEL == "code-llama":
            try:
                sm_client = boto3.client("sagemaker-runtime")
                endpoint = os.getenv("CODELLAMA_ENDPOINT")
                if not endpoint:
                    raise ValueError("CODELLAMA_ENDPOINT environment variable not set")
                resp = sm_client.invoke_endpoint_with_response_stream(
                    EndpointName=endpoint,
                    Body=json.dumps(
                        {
                            "inputs": self.generate_llama_prompt(),
                            "parameters": {
                                "max_new_tokens": kwargs["max_tokens"],
                            },
                        }
                    ),
                    ContentType="application/json",
                )
            except Exception as e:
                print(f"Error calling Code Llama: {e}")
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
                    chunk = next(iter((resp["Body"])))
                    bytes_to_send = chunk["PayloadPart"]["Bytes"]
                    decoded_str = bytes_to_send.decode("utf-8")
                    cleaned_str = decoded_str.replace(
                        '{"generated_text": "', ""
                    ).replace('"}', "")
                    cleaned_str = cleaned_str.encode().decode("unicode_escape")

                    yield {
                        "choices": [
                            {"finish_reason": "stop", "delta": {"content": cleaned_str}}
                        ]
                    }
                except StopIteration:
                    break

                except UnboundLocalError:
                    print("UnboundLocalError")
                    break
        if self.GPT_MODEL == "anthropic":
            print("Calling anthropic")
            try:
                sm_client = boto3.client("bedrock-runtime")
                resp = sm_client.invoke_model_with_response_stream(
                    accept="*/*",
                    contentType="application/json",
                    modelId="anthropic.claude-v2",
                    body=json.dumps(
                        {
                            "prompt": self.generate_anthropic_prompt(),
                            "max_tokens_to_sample": max(kwargs["max_tokens"], 2000),
                            "temperature": kwargs["temperature"],
                            # "stop_sequences": ["Human:"]
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
                    content = decoded_str["completion"]
                    stop_reason = decoded_str["stop_reason"]
                    if stop_reason == "stop_sequence":
                        yield {
                            "choices": [
                                {"finish_reason": "stop", "delta": {"content": content}}
                            ]
                        }
                        break
                    else:
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
