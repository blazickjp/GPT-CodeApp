import os
import shutil
from app_setup import setup_app_testing, DIRECTORY

AGENT, CODEBASE = setup_app_testing()
temp_file = "backend/tests/test_files/agent_function_test1"
temp_file_full = os.path.join(DIRECTORY, temp_file)


def test_FileChange_real_world_example():
    # Create a temporary file
    TEST_FILE = "backend/tests/test_files/app_setup_test.py"
    FULL_PATH = os.path.join(DIRECTORY, TEST_FILE)
    shutil.copy2(FULL_PATH, temp_file_full)
    AGENT.files_in_prompt = [TEST_FILE]
    AGENT.set_files_in_prompt(include_line_numbers=True)

    # Create a FileChange instance
    accumulated_message = ""
    for content in AGENT.query(
        input=f"""
        For file - {temp_file}, Change 'Successfully connected to database' to 'Database connection established',
        add a comment '# This is a new comment' after the 'create_database_connection' function, and finally
        delete the duplicate 'DB_CONNECTION = create_database_connection()' line
        """,
        command="Changes",
    ):
        if content is not None:
            accumulated_message += content

    # Check that the file was updated correctly
    with open(temp_file_full, "r") as f:
        new_text = f.readlines()

    # Should be 8 spaces for indents and one newline character
    assert len(new_text[32]) - len('print("Database connection established")') == 9
    assert new_text[32].strip() == 'print("Database connection established")'
    assert new_text[46].strip() == "# This is a new comment"
    assert new_text[69].strip() == ""
    os.remove(temp_file_full)
