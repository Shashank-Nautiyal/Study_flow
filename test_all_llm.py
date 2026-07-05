"""
Test script to verify all LLM calls are working.
Tests each provider/model one by one and reports results.

Usage:
    python test_all_llm.py
"""

import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── All agents and their configs ───────────────────────────────────

AGENTS_TO_TEST = {
    "Coach (Cerebras / GLM 4.7)": {
        "base_url": "https://api.cerebras.ai/v1",
        "model": "zai-glm-4.7",
        "api_key": os.getenv("CEREBRAS_API_KEY"),
    },
    "Diagnostic (OpenRouter / DeepSeek V4 Pro)": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "deepseek/deepseek-v4-pro",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
    },
    "Roadmap (Mistral / mistral-large)": {
        "base_url": "https://api.mistral.ai/v1",
        "model": "mistral-large-latest",
        "api_key": os.getenv("MISTRAL_API_KEY"),
    },
    "Quiz (Cloudflare / Llama 4 Scout)": {
        "base_url": f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID', '2a29379681489a5ef67e45521a23bc5f')}/ai/v1",
        "model": "@cf/meta/llama-4-scout-17b-16e-instruct",
        "api_key": os.getenv("CLOUDFLARE_API_KEY"),
    },
    "Resource (Cloudflare / Gemma 4 26B)": {
        "base_url": f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID', '2a29379681489a5ef67e45521a23bc5f')}/ai/v1",
        "model": "@cf/google/gemma-4-26b-a4b-it",
        "api_key": os.getenv("CLOUDFLARE_API_KEY"),
    },
    "Insight (Fireworks / GLM 5.1)": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "model": "accounts/fireworks/models/glm-5p1",
        "api_key": os.getenv("FIREWORKS_API_KEY"),
    },
    "Portfolio (Fireworks / GLM 5.2)": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "model": "accounts/fireworks/models/glm-5p2",
        "api_key": os.getenv("FIREWORKS_API_KEY"),
    },
    "Memory Manager (Groq / Llama 3.1 8B)": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.1-8b-instant",
        "api_key": os.getenv("GROQ_API_KEY"),
    },
}

TEST_PROMPT = "Say 'Hello, I am working!' in one short sentence. Nothing else."


def test_agent(name, config):
    """Test a single agent's LLM call."""

    api_key = config["api_key"]

    # ── Check API key exists ───────────────────────────────────
    if not api_key:
        return "SKIPPED", "No API key set", 0

    # ── Make the call ──────────────────────────────────────────
    try:
        client = OpenAI(
            base_url=config["base_url"],
            api_key=api_key,
            timeout=120.0
        )

        start = time.time()

        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "user", "content": TEST_PROMPT}
            ],
            temperature=0.1,
            max_tokens=256
        )

        elapsed = time.time() - start
        content = response.choices[0].message.content

        if content is None:
            return "FAIL", "Response content is None (reasoning model may need more tokens)", 0

        return "PASS", content.strip(), round(elapsed, 2)

    except Exception as e:
        return "FAIL", str(e)[:120], 0


def main():
    print()
    print("=" * 70)
    print("  LLM Connection Test — All Agents")
    print("=" * 70)
    print()

    results = []
    pass_count = 0
    fail_count = 0
    skip_count = 0

    for name, config in AGENTS_TO_TEST.items():
        print(f"  Testing: {name}")
        print(f"    Model:    {config['model']}")
        print(f"    Endpoint: {config['base_url']}")

        status, message, elapsed = test_agent(name, config)

        if status == "PASS":
            print(f"    Status:   [PASS] ({elapsed}s)")
            print(f"    Response: \"{message}\"")
            pass_count += 1
        elif status == "SKIPPED":
            print(f"    Status:   [SKIP] -- {message}")
            skip_count += 1
        else:
            print(f"    Status:   [FAIL]")
            print(f"    Error:    {message}")
            fail_count += 1

        results.append((name, status, message))
        print()

    # ── Summary ────────────────────────────────────────────────
    print("=" * 70)
    print(f"  RESULTS:  {pass_count} passed  |  {fail_count} failed  |  {skip_count} skipped")
    print("=" * 70)
    print()

    if fail_count > 0:
        print("  Failed agents:")
        for name, status, message in results:
            if status == "FAIL":
                print(f"    • {name}: {message}")
        print()

    if skip_count > 0:
        print("  Skipped agents (missing API keys in .env):")
        for name, status, message in results:
            if status == "SKIPPED":
                print(f"    • {name}")
        print()

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
