"""
Minerva's Library - Assignment Chat Application
A simple chatbot with 3 services: Jokes API, Father Brown Search, Calculator
"""

import os
import re
import math
import requests
import gradio as gr
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

try:
    from prompts import get_system_prompt
    from init import chroma_client, get_embedding_function, get_collection, build_graph
except ImportError:
    from assignment_2.prompts import get_system_prompt
    from assignment_2.init import chroma_client, get_embedding_function, get_collection, build_graph

# SERVICE 1: API CALLS - Jokes API

@tool
def get_joke() -> str:
    """Fetches a random joke to share with the user."""
    try:
        response = requests.get(
            "https://v2.jokeapi.dev/joke/Any",
            params={"blacklistFlags": "nsfw,religious,political,racist,sexist,explicit", "type": "twopart"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("type") == "twopart":
                return f"Setup: {data.get('setup', '')}\nPunchline: {data.get('delivery', '')}"
            return data.get("joke", "No joke found")
    except:
        pass
    # Fallback joke
    return "Setup: Why did the librarian get kicked off the plane?\nPunchline: It was overbooked!"

# SERVICE 2: SEMANTIC SEARCH - Father Brown Stories

@tool
def search_father_brown(query: str) -> str:
    """
    Search through Father Brown mystery stories by G.K. Chesterton.
    Use this to find passages or answer questions about the stories.
    """
    collection = get_collection()

    if collection.count() == 0:
        return "Database not set up. Please run: python3 app.py --setup"

    results = collection.query(query_texts=[query], n_results=3)

    if not results['documents'] or not results['documents'][0]:
        return "No relevant passages found."

    passages = []
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
        story = meta.get('story', 'Unknown')
        passages.append(f"From '{story}':\n{doc[:500]}...")

    return "\n\n---\n\n".join(passages)

# SERVICE 3: FUNCTION CALLING - Calculator

@tool
def calculate(expression: str) -> str:
    """
    Perform mathematical calculations.
    Examples: "2 + 2", "sqrt(16)", "3 ** 2", "sin(pi/2)"
    """
    allowed = {
        'sqrt': math.sqrt, 'abs': abs, 'round': round, 'pow': pow,
        'min': min, 'max': max, 'sin': math.sin, 'cos': math.cos,
        'tan': math.tan, 'log': math.log, 'pi': math.pi, 'e': math.e,
        'floor': math.floor, 'ceil': math.ceil
    }

    try:
        # Only allow safe characters and functions
        words = re.findall(r'[a-zA-Z_]+', expression)
        for word in words:
            if word.lower() not in allowed:
                return f"Error: '{word}' not allowed"

        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(round(result, 10) if isinstance(result, float) else result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {e}"

# LANGGRAPH AGENT SETUP

tools = [get_joke, search_father_brown, calculate]
system_prompt = get_system_prompt()
graph = build_graph(tools, system_prompt)

# GRADIO CHAT INTERFACE

def chat(message: str, history: list[dict]) -> str:
    """Process user message and return response."""
    # Convert history to LangChain format
    messages = []
    for msg in history:
        if msg['role'] == 'user':
            messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            messages.append(AIMessage(content=msg['content']))
    messages.append(HumanMessage(content=message))

    # Get response from graph
    result = graph.invoke({"messages": messages})
    return result['messages'][-1].content

# DATABASE SETUP FUNCTION

def setup_database():
    """Create embeddings for Father Brown stories. Run once before using the app."""
    print("Setting up Father Brown database...")

    # Read the text file
    doc_path = os.path.join(os.path.dirname(__file__), "..", "documents", "chesterton.txt")
    with open(doc_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Story titles to split by
    stories = [
        "The Blue Cross", "The Secret Garden", "The Queer Feet", "The Flying Stars",
        "The Invisible Man", "The Honour of Israel Gow", "The Wrong Shape",
        "The Sins of Prince Saradine", "The Hammer of God", "The Eye of Apollo",
        "The Sign of the Broken Sword", "The Three Tools of Death"
    ]

    # Delete existing and create new collection
    try:
        chroma_client.delete_collection("father_brown")
    except:
        pass

    collection = chroma_client.create_collection(
        name="father_brown",
        embedding_function=get_embedding_function()
    )

    # Process each story
    all_chunks, all_ids, all_metas = [], [], []

    for i, title in enumerate(stories):
        # Find story boundaries
        start = text.find(f"\n{title}\n")
        if start == -1:
            continue

        end = text.find(f"\n{stories[i+1]}\n") if i < len(stories)-1 else text.find("*** END OF")
        story_text = text[start:end] if end != -1 else text[start:]

        # Chunk the story (simple 1000 char chunks with overlap)
        chunk_size, overlap = 1000, 200
        for j in range(0, len(story_text), chunk_size - overlap):
            chunk = story_text[j:j + chunk_size].strip()
            if len(chunk) > 100:  # Skip tiny chunks
                all_chunks.append(chunk)
                all_ids.append(f"{title.lower().replace(' ', '_')}_{j}")
                all_metas.append({"story": title})

    # Add to collection in batches
    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        end = min(i + batch_size, len(all_chunks))
        collection.add(
            ids=all_ids[i:end],
            documents=all_chunks[i:end],
            metadatas=all_metas[i:end]
        )
        print(f"Added {end}/{len(all_chunks)} chunks...")

    print(f"Done! Created {collection.count()} embeddings.")

# MAIN

if __name__ == "__main__":
    import sys

    if "--setup" in sys.argv:
        setup_database()
    else:
        print("Starting Ahmet's Library...")
        gr.ChatInterface(
            fn=chat,
            title="Minerva's Library",
            description="Hello! I'm Minerva, your friendly librarian. I can help you explore Father Brown mysteries, share jokes, or do calculations!",
            examples=["Tell me about Father Brown", "Tell me a joke", "Calculate sqrt(144) + 10"]
        ).launch()
