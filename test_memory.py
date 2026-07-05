import os
import asyncio
from dotenv import load_dotenv

# Ensure we actually test the DB (no mock)
os.environ["TEST_MODE"] = "false"
# Skip the internal cognee LLM test that fails with Groq
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"

load_dotenv()

from app.services.memory_service import MemoryService

def test_cognee_memory():
    print("\n=============================================")
    print("   Testing Cognee Graph Memory Backend       ")
    print("=============================================\n")

    dataset = "memory_test_db"
    test_fact = "The user's favorite programming language is Python and they love building AI agents."

    print(f"1. Remembering fact into '{dataset}':")
    print(f"   => '{test_fact}'")
    
    try:
        MemoryService.remember(test_fact, dataset_name=dataset)
        print("   [SUCCESS] Remember successful (data added and cognified).")
    except Exception as e:
        print(f"   [ERROR] Failed to remember. Error: {e}")
        return

    print("\n2. Recalling context...")
    query = "What does the user like to build?"
    print(f"   Query: '{query}'")
    
    try:
        context = MemoryService.get_context(query)
        if context:
            print(f"   [SUCCESS] Recall successful! Context retrieved:\n      {context}")
        else:
            print("   [WARNING] Recall returned no results.")
    except Exception as e:
        print(f"   [ERROR] Failed to recall. Error: {e}")

    print("\n3. Cleaning up local database...")
    try:
        MemoryService.forget(everything=True)
        print("   [SUCCESS] Database pruned successfully.")
    except Exception as e:
        print(f"   [ERROR] Failed to prune database. Error: {e}")

    print("\nMemory Test Complete!")

if __name__ == "__main__":
    test_cognee_memory()
