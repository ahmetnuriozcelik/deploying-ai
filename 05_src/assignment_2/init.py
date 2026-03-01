import os
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_openai import ChatOpenAI


def load_assignment_env() -> None:
    """
    Load environment files using the same convention as 01_1_introduction.ipynb:
    ../../05_src/.env and ../../05_src/.secrets (from notebook location).
    """
    here = Path(__file__).resolve()
    src_dir = here.parents[1]  # .../05_src

    env_files = [
        src_dir / ".env",
        src_dir / ".secrets",
        Path(".env"),
        Path(".secrets"),
    ]

    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=False)


load_assignment_env()


CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
OPENAI_GATEWAY_BASE_URL = "https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1"
OPENAI_DUMMY_API_KEY = "any value"


def get_gateway_headers() -> dict[str, str]:
    gateway_key = os.getenv("API_GATEWAY_KEY")
    if not gateway_key:
        raise ValueError("Missing API_GATEWAY_KEY environment variable.")
    return {"x-api-key": gateway_key}


def get_embedding_function():
    return OpenAIEmbeddingFunction(
        api_key=OPENAI_DUMMY_API_KEY,
        api_base=OPENAI_GATEWAY_BASE_URL,
        default_headers=get_gateway_headers(),
        model_name="text-embedding-3-small",
    )


def get_collection():
    """Get or create the Father Brown collection."""
    return chroma_client.get_or_create_collection(
        name="father_brown",
        embedding_function=get_embedding_function(),
    )


def build_graph(tools: list, system_prompt: str):
    """Build and compile the LangGraph agent."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        base_url=OPENAI_GATEWAY_BASE_URL,
        api_key=OPENAI_DUMMY_API_KEY,
        default_headers=get_gateway_headers(),
    )

    def call_model(state: MessagesState):
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.bind_tools(tools).invoke(messages)
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder.compile()
