# app_setup.py
import os
import sqlite3
from psycopg2.extensions import connection
from agent.coding_agent import CodingAgent
from agent.agent_prompts import PROFESSOR_SYNAPSE, DEFAULT_SYSTEM_PROMPT
from agent.agent_functions.file_ops import _OP_LIST
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Callable
from pydantic import BaseModel

# from agent.agent_functions.changes import Changes

IGNORE_DIRS = ["node_modules", ".next", ".venv", "__pycache__", ".git"]
FILE_EXTENSIONS = [".js", ".py", ".md", "Dockerfile", '.txt']


def create_database_connection() -> connection:
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        print("Successfully connected to database")
        return conn
    except Exception as e:
        print(e)
        raise e


DB_CONNECTION = create_database_connection()
DIRECTORY = os.getenv("PROJECT_DIRECTORY", ".")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FunctionCall(BaseModel):
    callable: Callable
    name: str = ""
    arguments: str = ""

    def __call__(self) -> Any:
        return self.callable(self.arguments)


def setup_memory_manager(**kwargs) -> MemoryManager:
    memory_manager = MemoryManager(db_connection=DB_CONNECTION, **kwargs)
    return memory_manager


def setup_codebase() -> MyCodebase:
    my_codebase = MyCodebase(
        directory=DIRECTORY,
        db_connection=DB_CONNECTION,
        file_extensions=FILE_EXTENSIONS,
        ignore_dirs=IGNORE_DIRS,
    )

    my_codebase.ignore_dirs = IGNORE_DIRS
    return my_codebase


def setup_app() -> CodingAgent:
    print("Setting up app")
    codebase = setup_codebase()
    memory = setup_memory_manager(tree=codebase.tree(), identity=DEFAULT_SYSTEM_PROMPT)
    agent = CodingAgent(
        memory_manager=memory, function_map=[_OP_LIST], codebase=codebase
    )
    return agent, codebase
