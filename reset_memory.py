import os
from dotenv import load_dotenv

load_dotenv()
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"

from app.services.memory_service import MemoryService

def reset():
    print("Pruning system...")
    MemoryService.forget(everything=True)
    print("Done")

if __name__ == "__main__":
    reset()
