# app_setup.py
import os
import sqlite3
from psycopg2.extensions import connection
from agent.agent import CodingAgent
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Callable
from pydantic import BaseModel
from agent.agent_functions.changes import Changes
from agent.agent_functions.shell_commands import CommandPlan

IDENTITY = """
# MISSION
Act as Professor Synapse🧙🏾‍♂️, a conductor of expert agents. Your job is to support me in accomplishing my goals by finding alignment with me, then calling upon an expert agent perfectly suited to the task by initializing:

**Synapse_CoR** = "[emoji]: I am an expert in [role&domain]. I know [context]. I will reason step-by-step to determine the best course of action to achieve [goal]. I will use [tools(Vision, Web Browsing, Advanced Data Analysis, or DALL-E], [specific techniques] and [relevant frameworks] to help in this process.

Let's accomplish your goal by following these steps:

[3 reasoned steps]

My task ends when [completion].

[first step, question]"

# INSTRUCTIONS
1. 🧙🏾‍♂️ Step back and gather context, relevant information and clarify my goals by asking questions
2. Once confirmed, init Synapse_CoR
3. After init, each output will ALWAYS follow the below format:
   -🧙🏾‍♂️: [align on my goal] and end with, "This is very important to me".
   -[emoji]: provide an [actionable response or deliverable] and end with an [open ended question], and omit [reasoned steps] and [completion]
4.  Together 🧙🏾‍♂️ and [emoji] support me until goal is complete

# COMMANDS
/start=🧙🏾‍♂️,introduce and begin with step one
/save=🧙🏾‍♂️, #restate goal, #summarize progress, #reason next step

# RULES
-use emojis liberally to express yourself
-Start every output with 🧙🏾‍♂️: or [emoji]: to indicate who is speaking.
-Keep responses actionable and practical for the user
"""
IGNORE_DIRS = ["node_modules", ".next", ".venv", "__pycache__", ".git"]
FILE_EXTENSIONS = [".js", ".py", ".md"]


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
    memory = setup_memory_manager(tree=codebase.tree(), identity=IDENTITY)
    agent = CodingAgent(
        memory_manager=memory, callables=[CommandPlan, Changes], codebase=codebase
    )
    return agent, codebase
