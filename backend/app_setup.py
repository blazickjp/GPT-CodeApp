# app_setup.py
import os
import sqlite3
from psycopg2.extensions import connection
from agent.agent import CodingAgent
from agent.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Callable
from pydantic import BaseModel
from agent.agent_functions.changes import Changes
from agent.agent_functions.shell_commands import CommandPlan

load_dotenv()
CODEAPP_DB_NAME = os.getenv("CODEAPP_DB_NAME")
CODEAPP_DB_USER = os.getenv("CODEAPP_DB_USER")
CODEAPP_DB_PW = os.getenv("CODEAPP_DB_PW")
CODEAPP_DB_HOST = os.getenv("CODEAPP_DB_HOST")
DIRECTORY = os.getenv("PROJECT_DIRECTORY")
IDENTITY = "You are an AI Pair Programmer and a world class python developer. Your role is to assist the Human in developing, debugging, and optimizing their project. Feel free to ask for more details if something isn't clear."


def create_database_connection() -> connection:
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        print("Successfully connected to database")
        return conn
    except Exception as e:
        if CODEAPP_DB_USER is None or CODEAPP_DB_USER == "USER_FROM_SETUP_STEP4":
            raise Exception(
                """
                Failed to connect to database.
                Credentials not set or changed in .env file or .env file is missing.
                Please set the following environment variables in the .env file in the root directory:
                CODEAPP_DB_NAME, CODEAPP_DB_USER, CODEAPP_DB_PW, CODEAPP_DB_HOST
                """
            )
        else:
            raise e


DB_CONNECTION = create_database_connection()

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
    my_codebase = MyCodebase(directory=DIRECTORY, db_connection=DB_CONNECTION)
    return my_codebase


def setup_app() -> CodingAgent:
    print("Setting up app")
    codebase = setup_codebase()
    memory = setup_memory_manager(tree=codebase.tree(), identity=IDENTITY)
    agent = CodingAgent(
        memory_manager=memory, callables=[CommandPlan, Changes], codebase=codebase
    )
    return agent, codebase
