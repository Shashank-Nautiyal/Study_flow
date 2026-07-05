import os
from dotenv import load_dotenv

load_dotenv()

MEMORY_CONFIG = {

    # Using Cerebras to bypass OpenRouter's 8 RPM limit on the free tier
    "llm_provider": "openai",
    "llm_model": "openai/zai-glm-4.7",
    "llm_api_key": os.getenv("CEREBRAS_API_KEY"),
    "llm_endpoint": "https://api.cerebras.ai/v1",

    # Embedding model (Ollama — free, local) 
    "embedding_provider": "litellm",
    "embedding_model": "ollama/nomic-embed-text",
    "embedding_dimensions": 768,
    "embedding_endpoint": os.getenv("OLLAMA_EMBEDDING_ENDPOINT", "http://localhost:11434"),

    #  Storage backends (lightweight defaults for hackathon) 
    "db_provider": "sqlite",
    "graph_db_provider": "kuzu",

    #  Auto-memory: store every agent interaction automatically 
    "auto_store": True

}
