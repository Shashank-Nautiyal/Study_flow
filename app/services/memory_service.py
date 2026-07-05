import os
import asyncio
import logging
from datetime import datetime

import cognee
from cognee import SearchType, config as cognee_config

from app.config.memory_config import MEMORY_CONFIG

logger = logging.getLogger(__name__)


class MemoryService:
    """Wraps all Cognee operations. The rest of the codebase only talks to this service."""

    _initialized = False

    @classmethod
    def _ensure_initialized(cls):
        """Configure Cognee once on first use."""
        if cls._initialized:
            return

        #  LLM config (for entity extraction inside Cognee) 
        cognee_config.set_llm_config({
            "llm_provider": MEMORY_CONFIG["llm_provider"],
            "llm_model": MEMORY_CONFIG["llm_model"],
            "llm_api_key": MEMORY_CONFIG["llm_api_key"],
            "llm_endpoint": MEMORY_CONFIG["llm_endpoint"]
        })

        # Embedding config (Ollama — free, local) 
        cognee_config.set_embedding_config({
            "embedding_provider": MEMORY_CONFIG["embedding_provider"],
            "embedding_model": MEMORY_CONFIG["embedding_model"],
            "embedding_dimensions": MEMORY_CONFIG.get("embedding_dimensions", 1536),
            "embedding_endpoint": MEMORY_CONFIG["embedding_endpoint"],
            "embedding_api_key": "ollama"
        })

        cls._initialized = True
        os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"
        logger.info("Cognee memory service initialized.")

    #  Core operations

    @classmethod
    async def _remember(cls, text, dataset_name="main"):
        """Store data and build knowledge graph."""
        if os.getenv("TEST_MODE") == "true":
            print(f"[TEST MODE] Skipping cognee.add and cognify for '{dataset_name}'")
            return
        cls._ensure_initialized()
        await cognee.add(data=text, dataset_name=dataset_name)
        await cognee.cognify()

    @classmethod
    async def _recall(cls, query, search_type=SearchType.GRAPH_COMPLETION):
        """Query the knowledge graph."""
        if os.getenv("TEST_MODE") == "true":
            return []
        cls._ensure_initialized()
        results = await cognee.search(
            query_text=query,
            query_type=search_type
        )
        return results

    @classmethod
    async def _forget(cls, everything=False):
        """Reset memory."""
        if os.getenv("TEST_MODE") == "true":
            return
        cls._ensure_initialized()
        if everything:
            await cognee.prune.prune_data()
            await cognee.prune.prune_system(metadata=True)
            logger.info("All memory cleared.")
        else:
            await cognee.prune.prune_system(
                graph=True, vector=True, metadata=False, cache=True
            )
            logger.info("Graph and vector stores cleared.")

    @classmethod
    async def _store_interaction(cls, agent_name, user_input, response):
        """Store a formatted agent interaction into Cognee."""
        if os.getenv("TEST_MODE") == "true":
            return
        timestamp = datetime.now().isoformat()
        interaction = (
            f"[{timestamp}] Agent: {agent_name}\n"
            f"User: {user_input}\n"
            f"Response: {response}"
        )
        await cls._remember(
            text=interaction,
            dataset_name=f"agent_{agent_name}"
        )

    @classmethod
    async def _get_context(cls, query, search_type=SearchType.CHUNKS):
        """Recall relevant context for an agent's system prompt injection."""
        if os.getenv("TEST_MODE") == "true":
            print(f"[TEST MODE] Returning mock context for: {query}")
            return "User has basic knowledge of variables and loops."
        cls._ensure_initialized()
        try:
            results = await cognee.search(
                query_text=query,
                query_type=search_type
            )
            if not results:
                return ""

            # Combine top results into a context string
            context_parts = []
            for result in results[:5]:
                text = getattr(result, "text", str(result))
                context_parts.append(text)

            return "\n---\n".join(context_parts)

        except Exception as e:
            logger.warning(f"Memory recall failed: {e}")
            return ""

    # Sync wrappers (for non-async callers) 

    @classmethod
    def remember(cls, text, dataset_name="main"):
        """Sync wrapper for _remember."""
        return asyncio.run(cls._remember(text, dataset_name))

    @classmethod
    def recall(cls, query, search_type=SearchType.GRAPH_COMPLETION):
        """Sync wrapper for _recall."""
        return asyncio.run(cls._recall(query, search_type))

    @classmethod
    def forget(cls, everything=False):
        """Sync wrapper for _forget."""
        return asyncio.run(cls._forget(everything))

    @classmethod
    def store_interaction(cls, agent_name, user_input, response):
        """Sync wrapper for _store_interaction."""
        return asyncio.run(cls._store_interaction(agent_name, user_input, response))

    @classmethod
    def get_context(cls, query, search_type=SearchType.CHUNKS):
        """Sync wrapper for _get_context."""
        return asyncio.run(cls._get_context(query, search_type))
