import os
import tempfile
from agent.agent_functions import FileChange
from diff_match_patch import diff_match_patch


def test_FileChange():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write("Hello\n")

    # Create a FileChange instance
    file_change = FileChange(name=temp_file.name, changes="Change 'Hello' to 'Hi'")

    # # Save the changes
    file_change.save()

    # # Check that the file was updated correctly
    with open(temp_file.name, "r") as f:
        assert f.read() == "Hi\n"

    # Clean up the temporary file
    os.remove(temp_file.name)


def test_FileChange_multiple_changes():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write("Hello\nWorld\n")

    # Create a FileChange instance
    file_change = FileChange(
        name=temp_file.name, changes="Change 'Hello' to 'Hi' and 'World' to 'Everyone'"
    )

    # Save the changes
    new_text = file_change.save()

    # Check that the file was updated correctly
    with open(temp_file.name, "r") as f:
        assert f.read() == "Hi\nEveryone\n"

    # Clean up the temporary file
    os.remove(temp_file.name)


def test_FileChange_real_world_example():
    # Create a temporary file
    TEST_FILE = "tests/test_files/app_setup_test.py"

    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(open(TEST_FILE).read())

    # Create a FileChange instance
    file_change = FileChange(
        name=temp_file.name,
        changes="Change 'Successfully connected to database' to 'Database connection established', add a comment '# This is a new comment' at the end of the 'create_database_connection' function, and delete the duplicate 'DB_CONNECTION = create_database_connection()' line",
    )

    # Save the changes
    new_text = file_change.save()
    new_text_lines = new_text.split("\n")

    assert new_text_lines[31] == '        print("Database connection established")'

    # Check that the file was updated correctly
    with open(temp_file.name, "r") as f:
        assert f.read() == new_text
