# app_setup.py
import os
import sqlite3
import sys
from agent.coding_agent import CodingAgent
from agent.agent_prompts import (
    PROFESSOR_SYNAPSE,
    DEFAULT_SYSTEM_PROMPT,
    LSA,
    DEFAULT_SYSTEM_PROMPT_V2,
)
from agent.agent_functions.file_ops import _OP_LIST
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Callable
from pydantic import BaseModel
import logging

logger = logging.getLogger("logger")
logger.setLevel(logging.WARNING)  # Adjust to the appropriate log level

# Create a file handler which logs even debug messages
if not os.path.exists("logs"):
    os.makedirs("logs")

formatter = logging.Formatter(
    "%(asctime)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s"
)

# Create a file handler which logs even debug messages
fh = logging.FileHandler("logs/backend.log")
fh.setLevel(logging.INFO)  # File handler level to capture all messages
fh.setFormatter(formatter)
logger.addHandler(fh)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)  # Console handler level
ch.setFormatter(formatter)
logger.addHandler(ch)

# Add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


# Stream handler for stdout/stderr
stream_handler = logging.StreamHandler(stream=sys.stdout)  # Redirects stdout
stream_handler.setLevel(
    logging.INFO
)  # Set the level if you want to filter out messages
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level):
        self.logger = logger
        self.log_level = log_level
        self._is_logging = False

    def write(self, message):
        if not self._is_logging:
            self._is_logging = True
            self.logger.log(self.log_level, message.rstrip())
            self._is_logging = False

    def flush(self):
        pass


sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)


# from agent.agent_functions.changes import Changes

IGNORE_DIRS = ["node_modules", ".next", ".venv", "__pycache__", ".git"]
FILE_EXTENSIONS = [".js", ".py", ".md", "Dockerfile", ".txt", ".ts", ".yaml"]


def create_database_connection() -> sqlite3.Connection:
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        logger.info("Successfully connected to database")
        return conn
    except Exception as e:
        logger.info(e)
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
    memory = setup_memory_manager(
        tree=codebase.tree(),
        identity=DEFAULT_SYSTEM_PROMPT_V2,
    )
    agent = CodingAgent(
        memory_manager=memory, function_map=[_OP_LIST], codebase=codebase
    )
    return agent, codebase
