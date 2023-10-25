import memgpt.autogen.memgpt_agent as memgpt_autogen
import memgpt.autogen.interface as autogen_interface
import memgpt.agent as agent
import memgpt.system as system
import memgpt.utils as utils
import memgpt.presets as presets
import memgpt.constants as constants
import memgpt.personas.personas as personas
import memgpt.humans.humans as humans
from memgpt.persistence_manager import (
    InMemoryStateManager,
    InMemoryStateManagerWithPreloadedArchivalMemory,
    InMemoryStateManagerWithFaiss,
)

import os
import autogen
import asyncio
from absl import app, flags

config_list = [
    {
        "model": "gpt-4",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
]
llm_config = {"config_list": config_list, "seed": 42}
user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message="A human admin.",
    code_execution_config={"last_n_messages": 2, "work_dir": "groupchat"},
)

interface = autogen_interface.AutoGenInterface()
persistence_manager = InMemoryStateManager()
memgpt_agent = presets.use_preset(
    presets.DEFAULT,
    "gpt-4",
    personas.get_persona_text(personas.DEFAULT),
    humans.get_human_text(humans.DEFAULT),
    interface,
    persistence_manager,
)

# MemGPT coder
coder = memgpt_autogen.MemGPTAgent(
    name="MemGPT_coder",
    agent=memgpt_agent,
)

# non-MemGPT PM
pm = autogen.AssistantAgent(
    name="Product_manager",
    system_message="Creative in software product ideas.",
    llm_config=llm_config,
)

groupchat = autogen.GroupChat(agents=[user_proxy, coder, pm], messages=[], max_round=12)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

user_proxy.initiate_chat(manager, message="Build a simple yet elegant saas product.")
