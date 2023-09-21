import json
import os
from uuid import uuid4
import tiktoken
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from app_setup import setup_app, app
import openai


ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")
AGENT, CODEBASE = setup_app()


@app.post("/message_streaming")
async def message_streaming(request: Request) -> StreamingResponse:
    data = await request.json()

    def stream():
        id = str(uuid4())
        accumulated_messages = {id: ""}
        for content in AGENT.query(**data):
            if content is not None:
                accumulated_messages[id] += content
                yield json.dumps({"id": id, "content": content}) + "@@"

        AGENT.memory_manager.add_message("assistant", accumulated_messages[id])

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/system_prompt")
async def get_system_prompt():
    return {"system_prompt": AGENT.memory_manager.system}


@app.post("/update_system")
async def update_system_prompt(input: dict):
    AGENT.memory_manager.set_system(input)
    return JSONResponse(status_code=200, content={})


@app.get("/get_functions")
async def get_functions():
    if AGENT.functions is None:
        agent_functions = {
            "agent_functions": [
                {"name": "None", "description": "The Agent has 0 Functions Loaded"}
            ]
        }
    else:
        agent_functions = {
            "agent_functions": [
                {"name": func.__name__, "description": func.__doc__}
                for func in AGENT.functions
            ]
        }
    if AGENT.callables is None:
        on_demand_functions = {
            "on_demand_functions": [
                {
                    "name": "None",
                    "description": "The Agent has 0 Functions for On-Demand-Calling",
                }
            ]
        }
    else:
        on_demand_functions = {
            "on_demand_functions": [
                {"name": func.__name__, "description": func.__doc__}
                for func in AGENT.callables
            ]
        }
    return JSONResponse(content={**agent_functions, **on_demand_functions})


@app.get("/get_messages")
async def get_messages(chatbox: bool | None = None):
    return {"messages": AGENT.memory_manager.get_messages(chat_box=chatbox)[1:]}


@app.get("/get_summaries")
async def get_summaries(reset: bool | None = None):
    if reset:
        print("Refreshing Data")
        CODEBASE._update_files_and_embeddings()

    cur = CODEBASE.conn.cursor()
    cur.execute("SELECT DISTINCT file_path, summary, token_count FROM files")
    results = cur.fetchall()
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


@app.get("/generate_readme")
async def generate_readme():
    return {"readme": "Deprecated"}


@app.post("/set_files_in_prompt")
async def set_files_in_prompt(input: dict):
    files = [file for file in input.get("files", None)]
    AGENT.files_in_prompt = files
    AGENT.set_files_in_prompt()
    return JSONResponse(status_code=200, content={})


@app.post("/set_model")
async def set_model(input: dict):
    model = input.get("model")
    AGENT.GPT_MODEL = model
    return JSONResponse(status_code=200, content={})


@app.post("/save_sytem_prompt")
async def save_prompt(input: dict):
    prompt = input.get("prompt")
    prompt_name = input.get("prompt_name")
    print(prompt_name)
    print(prompt)
    # Create or update prompt
    if AGENT.memory_manager.prompt_handler.read_prompt(prompt_name):
        AGENT.memory_manager.prompt_handler.update_prompt(prompt_name, prompt)
    else:
        AGENT.memory_manager.prompt_handler.create_prompt(prompt_name, prompt)
    return JSONResponse(status_code=200, content={})


@app.get("/list_prompts")
async def list_prompts():
    prompts = AGENT.memory_manager.prompt_handler.list_prompts()
    return {"prompts": prompts}


@app.post("/delete_prompt")
async def delete_prompt(input: dict):
    print(input)
    prompt_id = input.get("prompt_id")
    print(prompt_id)
    try:
        AGENT.memory_manager.prompt_handler.delete_prompt(prompt_id)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    return JSONResponse(status_code=200, content={})

@app.post("/set_prompt")
async def set_prompt(input: dict):
    prompt_id = input.get("prompt_id")
    prompt = input.get("prompt")
    print(prompt_id)
    print(prompt)
    AGENT.memory_manager.prompt_handler.update_prompt(prompt_id, prompt)
    AGENT.memory_manager.set_system({"system_prompt": prompt})
    return JSONResponse(status_code=200, content={})
