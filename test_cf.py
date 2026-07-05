import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ACCOUNT_ID = "2a29379681489a5ef67e45521a23bc5f"
api_key = os.getenv("CLOUDFLARE_API_KEY")
base_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/v1"

client = OpenAI(base_url=base_url, api_key=api_key, timeout=120.0)

# Test a few models
models_to_test = [
    "@cf/meta/llama-4-scout-17b-16e-instruct",
    "@cf/qwen/qwq-32b",
    "@cf/google/gemma-4-26b-a4b-it",
    "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
]

for model in models_to_test:
    print(f"Testing: {model}")
    try:
        start = time.time()
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in one sentence"}],
            max_tokens=256,
            temperature=0.1
        )
        content = r.choices[0].message.content
        if content:
            print(f"  [PASS] ({round(time.time()-start,2)}s): {content.strip()[:80]}")
        else:
            print(f"  [FAIL] Content is None")
    except Exception as e:
        print(f"  [FAIL] {str(e)[:100]}")
    print()
