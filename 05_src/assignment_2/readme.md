# Minerva's Library - Assignment Chat

A simple chatbot with a librarian personality, built for Assignment 2.

## Quick Start

```bash
# 1. Go to app folder
cd 05_src/assignment_2

# 2. Set API gateway key (or place in .secrets)
export API_GATEWAY_KEY="your-gateway-key"

# 3. Create embeddings (run once)
python3 app.py --setup

# 4. Launch the app
python3 app.py
```

The app will open at `http://localhost:7860`

`assignment_2/init.py` automatically loads `05_src/.env` and `05_src/.secrets` (same pattern used in `01_materials/labs/01_1_introduction.ipynb`).

## Three Services

### Service 1: API Calls - Jokes
- **Tool**: `get_joke`
- **API**: [JokeAPI](https://jokeapi.dev/) (free, no auth)
- **Transformation**: LLM presents jokes in Minerva's personality

### Service 2: Semantic Search - Father Brown Stories
- **Tool**: `search_father_brown`
- **Dataset**: `documents/chesterton.txt` (~458KB)
- **Database**: ChromaDB with persistent file storage
- **Embeddings**: OpenAI `text-embedding-3-small`

#### Embedding Process
1. Read text from `documents/chesterton.txt`
2. Split into 12 stories by title
3. Chunk into ~1000 char segments with 200 char overlap
4. Generate embeddings via OpenAI
5. Store in `chroma_db/` folder

### Service 3: Function Calling - Calculator
- **Tool**: `calculate`
- **Features**: Basic math (+, -, *, /, **) and functions (sqrt, sin, cos, log, pi, e)

## Personality

**Minerva** - A friendly librarian who loves mystery stories. Uses bookish expressions like "Ah, what a delightful inquiry!"

## Guardrails

### Restricted Topics (will not discuss)
- Cats and Dogs
- Horoscopes and Zodiac Signs
- Taylor Swift

### System Prompt Protection
- Cannot be revealed or modified

## Dependencies

Standard course libraries: langchain, langgraph, chromadb, gradio, requests
