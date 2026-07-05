import os
from dotenv import load_dotenv

load_dotenv()

# Ollama fallback (offline)
USE_OLLAMA_FALLBACK = os.getenv("USE_OLLAMA", "false").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

#  Cloudflare config 
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "2a29379681489a5ef67e45521a23bc5f")

#  Provider Base URLs 
PROVIDER_URLS = {
    "groq":       "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "fireworks":  "https://api.fireworks.ai/inference/v1",
    "cerebras":   "https://api.cerebras.ai/v1",
    "mistral":    "https://api.mistral.ai/v1",
    "deepseek":   "https://api.deepseek.com",
    "cloudflare": f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1",
    "ollama":     OLLAMA_BASE_URL
}

AGENT_CONFIG = {

    #  Coach Agent 
    # GLM 4.7 on Cerebras
    "coach": {
        "provider": "cerebras",
        "model": "gemma-4-31b",
        "base_url": PROVIDER_URLS["cerebras"],
        "api_key": os.getenv("CEREBRAS_API_KEY"),
        "temperature": 0.8
    },

    # Diagnostic Agent 
    # Gemma 4 31B on Cerebras (Larger context window, excellent structured output)
    "diagnostic": {
        "provider": "cerebras",
        "model": "gemma-4-31b",
        "base_url": PROVIDER_URLS["cerebras"],
        "api_key": os.getenv("CEREBRAS_API_KEY"),
        "temperature": 0.2
    },

    # Roadmap Agent
    # Qwen 3.7 Plus on Fireworks AI (Heavy planning task, utilizing free tier credits)
    "roadmap": {
        "provider": "fireworks",
        "model": "accounts/fireworks/models/qwen3p7-plus",
        "base_url": PROVIDER_URLS["fireworks"],
        "api_key": os.getenv("FIREWORKS_API_KEY"),
        "temperature": 0.3
    },

    # Quiz Agent 
    # Llama 4 Scout 17B on Cloudflare (Light formatting task)
    "quiz": {
        "provider": "cloudflare",
        "model": "@cf/meta/llama-4-scout-17b-16e-instruct",
        "base_url": PROVIDER_URLS["cloudflare"],
        "api_key": os.getenv("CLOUDFLARE_API_KEY"),
        "temperature": 0.2
    },

    #  Resource Agent 
    # Gemma 4 26B on Cloudflare (Light extraction task)
    "resource": {
        "provider": "cloudflare",
        "model": "@cf/google/gemma-4-26b-a4b-it",
        "base_url": PROVIDER_URLS["cloudflare"],
        "api_key": os.getenv("CLOUDFLARE_API_KEY"),
        "temperature": 0.4
    },

    # Insight Agent 
    # Small fast Llama 8B on Fireworks (Cost efficient, supports structured output)
    "insight": {
        "provider": "fireworks",
        "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "base_url": PROVIDER_URLS["fireworks"],
        "api_key": os.getenv("FIREWORKS_API_KEY"),
        "temperature": 0.5
    },

    #  Portfolio Agent 
    # Small fast Llama 8B on Fireworks (Cost efficient formatting)
    "portfolio": {
        "provider": "fireworks",
        "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "base_url": PROVIDER_URLS["fireworks"],
        "api_key": os.getenv("FIREWORKS_API_KEY"),
        "temperature": 0.4
    },

    #  Memory Manager Agent 
    # Qwen 2.5 7B on Fireworks (Extremely fast, excellent at strict JSON structured output)
    "memory_manager": {
        "provider": "fireworks",
        "model": "accounts/fireworks/models/qwen2p5-7b-instruct",
        "base_url": PROVIDER_URLS["fireworks"],
        "api_key": os.getenv("FIREWORKS_API_KEY"),
        "temperature": 0.2
    }

}

# Apply Ollama fallback if enabled 
if USE_OLLAMA_FALLBACK:
    for agent_name in AGENT_CONFIG:
        AGENT_CONFIG[agent_name]["model"] = OLLAMA_MODEL
        AGENT_CONFIG[agent_name]["base_url"] = PROVIDER_URLS["ollama"]
        AGENT_CONFIG[agent_name]["api_key"] = "ollama"
