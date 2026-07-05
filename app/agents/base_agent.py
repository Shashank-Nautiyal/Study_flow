import logging

from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.config.agent_config import AGENT_CONFIG
from app.config.memory_config import MEMORY_CONFIG

logger = logging.getLogger(__name__)


class BaseAgent:

    def __init__(self, agent_name, system_prompt):
        config = AGENT_CONFIG[agent_name]

        self.agent_name = agent_name
        self.model = config["model"]
        self.base_url = config["base_url"]
        self.api_key = config["api_key"]
        self.temperature = config["temperature"]

        self.system_prompt = system_prompt
        self.auto_store = MEMORY_CONFIG.get("auto_store", False)

    def run(self, user_input="", context=None, memory=None, attachments=None, metadata=None):
        if context is None:
            context = {}
        if memory is None:
            memory = []
        if attachments is None:
            attachments = []
        if metadata is None:
            metadata = {}

        #  Recall relevant memory from Cognee 
        memory_context = ""
        try:
            memory_context = MemoryService.get_context(query=user_input)
        except Exception as e:
            logger.warning(f"[{self.agent_name}] Memory recall skipped: {e}")

        #  Build messages with memory injection 
        system_content = self.system_prompt
        if memory_context:
            system_content += (
                "\n\n--- Relevant Memory ---\n"
                f"{memory_context}\n"
                "--- End Memory ---"
            )

        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        #  Generate response 
        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        # Auto-store interaction into Cognee 
        if self.auto_store:
            try:
                MemoryService.store_interaction(
                    agent_name=self.agent_name,
                    user_input=user_input,
                    response=response
                )
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Memory store skipped: {e}")

        return response
