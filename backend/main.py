import json
import os
from uuid import uuid4
import tiktoken
from fastapi import Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from app_setup import setup_app, app
from agent.agent_functions.file_ops import _OP_LIST
import traceback
import logging

ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")
AGENT, CODEBASE = setup_app()

logger = logging.getLogger("logger")


@app.on_event("startup")
async def startup_event():
    config = AGENT.memory_manager.cur.execute(
        """
        SELECT field, value FROM config
        """
    ).fetchall()
    config = {field: value for field, value in config}
    if config.get("model"):
        AGENT.GPT_MODEL = config["model"]
    if config.get("max_message_tokens"):
        AGENT.memory_manager.max_tokens = int(config["max_message_tokens"])
    if config.get("directory"):
        CODEBASE.set_directory(config["directory"])
        AGENT.memory_manager.prompt_handler.tree = CODEBASE.tree()
        AGENT.memory_manager.prompt_handler.set_system()
        AGENT.memory_manager.set_directory(config["directory"])
    if config.get("files"):
        AGENT.memory_manager.prompt_handler.files_in_prompt = json.loads(
            config["files"]
        )
        AGENT.memory_manager.prompt_handler.set_files_in_prompt()
        AGENT.memory_manager.prompt_handler.set_system()


@app.post("/message_streaming")
async def message_streaming(
    request: Request, background_tasks: BackgroundTasks
) -> StreamingResponse:
    data = await request.json()
    logger.warning(data.keys())

    def stream():
        id = str(uuid4())
        accumulated_messages = {id: ""}
        for content in AGENT.query(**data):
            if content is not None:
                accumulated_messages[id] += content
                yield json.dumps({"id": id, "content": content}) + "@@"
        AGENT.memory_manager.add_message(
            "assistant",
            accumulated_messages[id],
            system_prompt=AGENT.memory_manager.prompt_handler.system,
        )
        # Experimental feature to update the context after each message
        # background_tasks.add_task(AGENT.memory_manager.update_context)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/get_functions")
async def get_functions():
    if AGENT.tools is None:
        agent_functions = {
            "agent_functions": [
                {"name": "None", "description": "The Agent has 0 Functions Loaded"}
            ]
        }
    else:
        agent_functions = {
            "agent_functions": [
                {"name": cls.__name__, "description": cls.__doc__}
                for cls in AGENT.function_map[0].values()
            ]
        }
        on_demand_functions = {
            "on_demand_functions": [
                {"name": cls.__name__, "description": cls.__doc__}
                for cls in AGENT.function_map[0].values()
            ]
        }
    return JSONResponse(content={**agent_functions, **on_demand_functions})


@app.get("/get_messages")
async def get_messages(chatbox: bool | None = None):
    return {"messages": AGENT.memory_manager.get_messages(chat_box=chatbox)[1:]}


@app.get("/get_summaries")
async def get_summaries(reset: bool | None = None):
    if reset:
        CODEBASE._update_files_and_embeddings()
    cur = CODEBASE.conn.cursor()
    cur.execute("SELECT DISTINCT file_path, summary, token_count FROM files")
    results = cur.fetchall()
    if len(results) == 0:
        return JSONResponse(status_code=400, content={"error": "No summaries found"})
    root_path = CODEBASE.directory
    result = [
        {
            "file_path": os.path.relpath(file_path, root_path),
            "file_token_count": token_count,
            "summary": None,
            "summary_token_count": 0,
        }
        for file_path, summary, token_count in results
        if file_path.startswith(root_path)
    ]
    result = sorted(result, key=lambda x: x["file_path"])
    return result


@app.post("/set_files_in_prompt")
async def set_files_in_prompt(input: dict):
    """Sets the files to be included in the prompt.

    This endpoint accepts a JSON input with a key "files", which should contain a list of file names.
    These files are then stored in the database and updated in the agent's memory manager for use in
    generating prompts.

    Args:
        input (dict): A dictionary containing the "files" key with a list of file names as its value.

    Returns:
        JSONResponse: A response with a 200 status code on success, or an error message on failure.
    """
    files = [file for file in input.get("files", None)]
    AGENT.memory_manager.cur.execute(
        """
        INSERT INTO config (field, value, last_updated)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(field)
        DO UPDATE SET value = excluded.value, last_updated = excluded.last_updated
        WHERE field = 'files';
        """,
        ("files", json.dumps(files)),
    )
    AGENT.memory_manager.prompt_handler.files_in_prompt = files
    AGENT.memory_manager.prompt_handler.set_files_in_prompt()
    return JSONResponse(status_code=200, content={})


@app.get("/get_files_in_prompt")
async def get_files_in_prompt():
    return {"files": AGENT.memory_manager.prompt_handler.files_in_prompt}


@app.post("/set_model")
async def set_model(input: dict):
    model = input.get("model")
    if model:
        AGENT.memory_manager.cur.execute(
            """
            INSERT INTO config (field, value, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(field)
            DO UPDATE SET value = excluded.value, last_updated = excluded.last_updated
            WHERE field = 'model';
            """,
            ("model", model),
        )
        AGENT.GPT_MODEL = model
        return JSONResponse(status_code=200, content={})
    else:
        return JSONResponse(status_code=400, content={"error": "No model was provided"})


@app.get("/get_model")
async def get_model():
    return {"model": AGENT.GPT_MODEL}


@app.get("/get_max_message_tokens")
async def get_max_message_tokens():
    max_message_tokens = AGENT.memory_manager.cur.execute(
        """
        SELECT value FROM config
        WHERE field = 'max_message_tokens';
        """
    ).fetchone()
    return {"max_message_tokens": max_message_tokens}


@app.post("/set_directory")
async def set_directory(input: dict):
    directory = input.get("directory")
    try:
        CODEBASE.set_directory(directory)
        AGENT.memory_manager.project_directory = directory
        AGENT.memory_manager.prompt_handler.tree = CODEBASE.tree()
        AGENT.memory_manager.prompt_handler.directory = directory
        AGENT.memory_manager.prompt_handler.set_system()
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        print(f"An error occurred: {e}")
        raise JSONResponse(status_code=400, detail="Could not set directory")


@app.get("/get_directory")
async def get_directory():
    return {"directory": CODEBASE.get_directory()}


@app.get("/get_home")
async def get_home():
    home_directory = os.path.expanduser("~")
    logging.info("home_directory", home_directory)
    return {"home_directory": home_directory}


@app.post("/set_max_message_tokens")
async def set_max_message_tokens(input: dict):
    max_message_tokens = input.get("max_message_tokens")
    try:
        AGENT.memory_manager.cur.execute(
            """
            INSERT INTO config (field, value, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(field)
            DO UPDATE SET value = excluded.value, last_updated = excluded.last_updated
            WHERE field = 'max_message_tokens';
            """,
            ("max_message_tokens", max_message_tokens),
        )
        AGENT.memory_manager.conn.commit()
        AGENT.memory_manager.max_tokens = max_message_tokens
    except Exception as e:
        print(f"An error occurred: {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})
    return JSONResponse(status_code=200, content={})


@app.get("/get_ops")
async def get_ops():
    print("Ops to execute: ", AGENT.ops_to_execute)
    if len(AGENT.ops_to_execute) > 0:
        ops = AGENT.ops_to_execute
        return {"ops": ops}
    else:
        return {"ops": []}


@app.post("/execute_ops")
async def execute_ops(input: dict):
    op_id = input.get("op_id")
    ops_to_execute = [op for op in AGENT.ops_to_execute if op.id in op_id]
    if len(ops_to_execute) > 0:
        try:
            AGENT.execute_ops(ops_to_execute)
            print("Ops to execute: ", AGENT.ops_to_execute[0].to_json())
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            return JSONResponse(status_code=400, content={"error": str(e)})
        return JSONResponse(status_code=200, content={})
    else:
        print("No ops to execute")
        return JSONResponse(status_code=400, content={"error": "No ops to execute"})


@app.get("/get_context")
async def get_context():
    # Your logic to retrieve and return the context goes here
    context = AGENT.memory_manager.working_context.get_context()
    return JSONResponse(status_code=200, content={"context": context})


@app.get("/logs/errors")
def get_error_logs():
    # Security checks to ensure only authorized access

    # Read the log file and return the last N lines of errors
    with open("logs/backend.log", "r") as log_file:
        log_lines = log_file.readlines()
        # Filter or process the log lines to retrieve only errors
        error_logs = [line for line in log_lines if "INFO" in line]

    return JSONResponse(status_code=200, content={"error_logs": error_logs})


@app.post("/set_temperature")
async def set_temperature(input: dict):
    """Sets the temperature value for the system.

    This endpoint accepts a JSON input with a key "temperature", which should contain the temperature value.
    The temperature value is then stored and used by the system as needed.

    Args:
        input (dict): A dictionary containing the "temperature" key with a temperature value as its value.

    Returns:
        JSONResponse: A response with a 200 status code on success, or an error message on failure.
    """
    temperature = input.get("temperature")
    if temperature is not None:
        # Here you would implement the logic to store and use the temperature value as needed.
        # For demonstration, let's just print it.
        AGENT.temperature = temperature
        print(f"Setting system temperature to: {temperature}")
        return JSONResponse(
            status_code=200, content={"message": "Temperature set successfully"}
        )
    else:
        return JSONResponse(
            status_code=400, content={"error": "No temperature was provided"}
        )


@app.post("/save_prompt")
async def save_prompt(input: dict):
    logger.warn(input)
    prompt = input.get("prompt")
    prompt_name = input.get("prompt_name")
    if AGENT.memory_manager.prompt_handler.get_prompt(prompt_name):
        AGENT.memory_manager.prompt_handler.update_prompt(prompt_name, prompt)
    else:
        AGENT.memory_manager.prompt_handler.create_prompt(prompt_name, prompt)
    AGENT.memory_manager.prompt_handler.set_system({"system_prompt": prompt})
    AGENT.memory_manager.prompt_handler.name = prompt_name
    return JSONResponse(status_code=200, content={})


@app.get("/system_prompt")
async def system_prompt():
    if AGENT.GPT_MODEL.startswith("gpt"):
        return {
            "system_prompt": AGENT.memory_manager.prompt_handler.system,
            "name": AGENT.memory_manager.prompt_handler.name,
        }
    elif AGENT.GPT_MODEL == "anthropic":
        return {
            "system_prompt": AGENT.generate_anthropic_prompt(),
            "name": AGENT.memory_manager.prompt_handler.name,
        }


@app.get("/list_prompts")
async def list_prompts():
    prompts = AGENT.memory_manager.prompt_handler.list_prompts()
    return {"prompts": prompts}


@app.post("/delete_prompt")
async def delete_prompt(input: dict):
    logger.warn(input)
    prompt_id = input.get("prompt_id", None)
    prompt_name = input.get("prompt_name", None)
    try:
        AGENT.memory_manager.prompt_handler.delete_prompt(prompt_id)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    return JSONResponse(status_code=200, content={})
