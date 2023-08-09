# Base
import json
import os
from uuid import uuid4
import tiktoken
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from database.my_codebase import get_git_root
from app_setup import setup_app, app


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
                yield json.dumps({"id": id, "content": content}) + "\n"

        AGENT.memory_manager.add_message("assistant", accumulated_messages[id])

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/system_prompt")
async def get_system_prompt():
    return {"system_prompt": AGENT.memory_manager.system}


@app.post("/update_system")
async def update_system_prompt(input: dict):
    AGENT.memory_manager.set_system(input.get("system_prompt"))
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
    if len(AGENT.memory_manager.messages) == 1:
        return {"messages": []}
    else:
        return {"messages": AGENT.memory_manager.get_messages(chat_box=chatbox)[1:]}


@app.get("/get_summaries")
async def get_summaries(reset: bool | None = None):
    if reset:
        print("Refreshing Data")
        CODEBASE._update_files_and_embeddings()

    cur = CODEBASE.conn.cursor()
    cur.execute("SELECT DISTINCT file_path, summary, token_count FROM files")
    results = cur.fetchall()
    root_path = get_git_root(CODEBASE.directory)
    result = [
        {
            "file_path": os.path.relpath(file_path, root_path),
            "file_token_count": token_count,
            "summary": summary,
            "summary_token_count": len(ENCODER.encode(summary)),
        }
        for file_path, summary, token_count in results
        if file_path.startswith(root_path)
    ]
    result = sorted(result, key=lambda x: x["file_path"])
    return result


@app.get("/generate_readme")
async def generate_readme():
    return {"readme": "Deprecated"}


@app.post("/set_summary_files_in_prompt")
async def set_summary_files_in_prompt(input: dict):
    if "files" not in input:
        return JSONResponse(status_code=400, content={"error": "missing files"})

    files = [
        os.path.join(get_git_root(CODEBASE.directory), file)
        for file in input.get("files")
    ]
    summaries = CODEBASE.get_summaries()
    summaries = [f"{k}:\n{v}" for k, v in summaries.items() if k in files]
    additional_system_prompt_summaries = "\n\n".join(summaries)
    AGENT.memory_manager.system_file_summaries = additional_system_prompt_summaries
    AGENT.memory_manager.set_system()
    return JSONResponse(status_code=200, content={})


@app.post("/set_files_in_prompt")
async def set_files_in_prompt(input: dict):
    files = [
        os.path.join(get_git_root(CODEBASE.directory), file)
        for file in input.get("files")
    ]
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files provided."})
    content = CODEBASE.get_file_contents()
    content = [f"{k}:\n{v}" for k, v in content.items() if k in files]
    if not content:
        return JSONResponse(status_code=400, content={"error": "No files found."})
    additional_system_prompt_files = "\n\n".join(content)
    AGENT.memory_manager.system_file_contents = additional_system_prompt_files
    AGENT.memory_manager.set_system()
    return JSONResponse(status_code=200, content={})


@app.post("/set_model")
async def set_model(input: dict):
    model = input.get("model")
    AGENT.GPT_MODEL = model
    return JSONResponse(status_code=200, content={})
