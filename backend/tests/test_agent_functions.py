import shutil
import re
import json
import os
import openai
from app_setup import DIRECTORY
from agent.agent_functions.changes import Changes

temp_file = "backend/tests/test_files/agent_function_test1.py"
TEST_FILE = "backend/tests/test_files/app_setup_test.py"
FULL_PATH = os.path.join(DIRECTORY, TEST_FILE)
temp_file_full = os.path.join(DIRECTORY, temp_file)
with open(FULL_PATH, "r") as f:
    CONTENT = f.read()

system_prompt = f""""
You are an AI Pair Programmer and a world class python developer helping the Human work on a project.

The project directory is setup as follows:
+--GPT-CodeApp
    +--frontend
        +--tailwind.config.js
        +--next.config.js
        +--postcss.config.js
        +--store
            +--sidebar
                +--sidebarSlice.js
            +--index.js
            +--messages
                +--messagesSlice.js
            +--modal_bar_modals
                +--messageHistorySlice.js
                +--systemPromptSlice.js
                +--functionsSlice.js
        +--styles
            +--globals.css
        +--components
            +--ModelSelector.js
            +--RightSidebar.js
            +--ChatInput.js
            +--EditFilesModal.js
            +--LeftSidebar.js
            +--SearchBar.js
            +--modal_bar_modals
                +--MessageHistoryModal.js
                +--SystemPromptModal.js
                +--FunctionsModal.js
            +--ChatBox.js
            +--ModalBar.js
        +--pages
            +--index.js
    +--README.md
    +--CONTRIBUTING.md
    +--backend
        +--agent
            +--openai_function_call.py
            +--agent_functions
                +--changes.py
                +--shell_commands.py
                +--new_file.py
            +--agent_functions.py
            +--memory_manager.py
            +--agent.py
        +--database
            +--my_codebase.py
            +--UpdateHandler.py
        +--tests
            +--test_codebase.py
            +--test_files
                +--app_setup_test.py
                +--agent_function_test1.py
            +--conftest.py
            +--test_agent_functions.py
            +--test_memory_manager.py
        +--main.py
        +--app_setup.py
    +--CODE_OF_CONDUCT.md
    +--.pytest_cache
        +--README.md

Related File Contents:
File: backend/tests/test_files/agent_function_test1.py
Content:
{CONTENT}
"""


def preprocess_response(response_str):
    # Find all occurrences of triple-quoted strings
    triple_quoted_strings = re.findall(r"\"\"\"(.*?)\"\"\"", response_str, re.DOTALL)

    # For each occurrence, replace newlines and triple quotes
    for tqs in triple_quoted_strings:
        fixed_string = tqs.replace("\n", "\\n").replace('"', '\\"')
        response_str = response_str.replace(tqs, fixed_string)

    # Now replace the triple quotes with single quotes
    response_str = response_str.replace('"""', '"')

    return response_str


def test_FileChange_real_world_example2():
    # Create a temporary file
    message_history = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"For file the file {temp_file}, re-write the Exception message to be informative. Respond with proper json",
        },
    ]

    keyword_args = {
        "model": "gpt-4-0613",
        "messages": message_history,
        "max_tokens": 1000,
        "temperature": 0.1,
        "functions": [Changes.openai_schema],
        "function_call": {"name": Changes.openai_schema["name"]},
    }

    # Create a FileChange instance
    response = openai.ChatCompletion.create(**keyword_args)
    processed_response = preprocess_response(
        response["choices"][0].message.function_call.arguments
    )
    print(repr(processed_response))

    args = json.loads(processed_response)
    print("File Name: ", temp_file)
    print("File Name: ", args.get("file_name"))
    print(f"Args: {args}")
    assert args.get("file_name") == temp_file


def test_FileChange_real_world_example3():
    TEST_FILE = "backend/tests/test_files/app_setup_test.py"
    FULL_PATH = os.path.join(DIRECTORY, TEST_FILE)
    if os.path.exists(temp_file_full):
        os.remove(temp_file_full)
        shutil.copy2(FULL_PATH, temp_file_full)
    else:
        shutil.copy2(FULL_PATH, temp_file_full)

    args = json.loads(
        '{\n  "file_name": "backend/tests/test_files/agent_function_test1.py",\n  "thought": "The current exception message is not very informative. It should be updated to provide more details about the error and how to fix it.",\n  "changes": [\n    {\n      "original": "\\"\\"\\"\\nFailed to connect to database.\\nCredentials not set or changed in .env file or .env file is missing.\\nPlease set the following environment variables in the .env file in the root directory:\\nCODEAPP_DB_NAME, CODEAPP_DB_USER, CODEAPP_DB_PW, CODEAPP_DB_HOST\\n\\"\\"\\"",\n      "updated": "\\"\\"\\"\\nFailed to connect to the database. This could be due to one of the following reasons:\\n1. The credentials are not set in the .env file.\\n2. The credentials in the .env file have been changed.\\n3. The .env file is missing.\\n\\nTo fix this issue, please ensure that the .env file in the root directory contains the following environment variables with the correct values:\\n- CODEAPP_DB_NAME: The name of your database.\\n- CODEAPP_DB_USER: The username for your database.\\n- CODEAPP_DB_PW: The password for your database.\\n- CODEAPP_DB_HOST: The host of your database.\\n\\"\\"\\""\n    }\n  ]\n}'
    )
    changes = Changes(**args)
    resp = changes.execute()
    print(resp)
    with open(temp_file_full, "r") as f:
        new_text = f.read()

    assert (
        "Credentials not set or changed in .env file or .env file is missing."
        not in new_text
    )
    assert "CODEAPP_DB_NAME: The name of your database." in new_text
    assert "CODEAPP_DB_USER: The username for your database." in new_text
    os.remove(temp_file_full)


def test_FileChange_real_world_example4():
    TEST_FILE = "backend/tests/test_files/app_setup_test.py"
    FULL_PATH = os.path.join(DIRECTORY, TEST_FILE)
    if os.path.exists(temp_file_full):
        os.remove(temp_file_full)
        shutil.copy2(FULL_PATH, temp_file_full)
    else:
        shutil.copy2(FULL_PATH, temp_file_full)

    changes = Changes(
        file_name=temp_file,
        thought="none needed for test",
        changes=[
            {
                "original": "Queries the GPT-3 model with the given input and command.\n\nParameters:\ninput (str) : The input text to be processed by the GPT-3 model.\ncommand (Optional[str]) : The command to be executed by the agent.\n\nReturns:\nList[str] : The output generated by the GPT-3 model.",
                "updated": "Queries the GPT-3 model with the given input and command.\n\nArgs:\n    input (str): The input text to be processed by the GPT-3 model.\n    command (Optional[str]): The command to be executed by the agent.\n\nReturns:\n    List[str]: The output generated by the GPT-3 model.",
            }
        ],
    )
    resp = changes.execute()
    print(resp)
    with open(temp_file_full, "r") as f:
        new_text = f.read()
    assert "Args:" in new_text


def test_match_partial():
    changes = Changes(file_name="test.py", thought="testing", changes=[])
    print(changes.match_partial(["    a", "    b"], ["  a", "  b"]))

    assert changes.match_partial(["    a", "    b"], ["a", "b"]) == (0, 2, 4)
    assert changes.match_partial(["    a", "    b"], [" a", " b"]) == (0, 2, 3)
    assert changes.match_partial(["    a", "    b"], ["  a", "  b"]) == (0, 2, 2)
    assert changes.match_partial(["    a", "    b"], ["   a", "   b"]) == (0, 2, 1)
    assert changes.match_partial(["    a", "    b"], ["    a", "    b"]) == (0, 2, 0)
    assert changes.match_partial(["    x", "    a", "    b"], ["a", "b"]) == (1, 3, 4)


def test_replace_part_with_missing_leading_whitespace():
    changes = Changes(file_name="test.py", thought="testing", changes=[])

    assert (
        changes.replace_part_with_missing_leading_whitespace(
            ["    a", "    b"], ["a", "b"], ["c", "d"]
        )
        == "    c\n    d"
    )
    assert (
        changes.replace_part_with_missing_leading_whitespace(
            ["    a", "    b"], [" a", " b"], [" c", " d"]
        )
        == "    c\n    d"
    )
    assert (
        changes.replace_part_with_missing_leading_whitespace(
            ["    a", "    b"], ["  a", "  b"], ["  c", "  d"]
        )
        == "    c\n    d"
    )
    assert (
        changes.replace_part_with_missing_leading_whitespace(
            ["    a", "    b"], ["   a", "   b"], ["   c", "   d"]
        )
        == "    c\n    d"
    )
    assert (
        changes.replace_part_with_missing_leading_whitespace(
            ["    a", "    b"], ["    a", "    b"], ["    c", "    d"]
        )
        == "    c\n    d"
    )
    assert (
        changes.replace_part_with_missing_leading_whitespace(
            ["    a", "    b"], ["a", " c"], ["c", "d"]
        )
        == "    a\n    b"
    )
