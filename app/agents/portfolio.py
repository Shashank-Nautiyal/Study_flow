import logging
import datetime
import json
import re
from app.agents.base_agent import BaseAgent
from app.services.memory_service import MemoryService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class PortfolioAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            "portfolio",
            """
            You are a Portfolio Agent for a learning platform. Your goal is to convert completed projects and achievements into resume bullets, portfolio descriptions, and GitHub README sections.
            Always return your output in valid, raw JSON format without markdown blocks if requested.
            """
        )

    def _extract_json(self, text):
        """Helper to safely extract JSON from LLM outputs."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        match = re.search(r'```(?:json)?\s*(\{.*\}|\[.*\])\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        logger.error(f"Failed to extract JSON from response: {text}")
        return {}

    def generate_portfolio(self, user_id):
        """
        Generates structured portfolio items based on verified achievements.
        """
        achievements = MemoryService.get_context(
            f"user:{user_id} all achievements, completed resources, quiz scores above 90%, projects finished, skills mastered",
            dataset_name=f"user_{user_id}_context"
        )

        system_prompt = (
            self.system_prompt +
            "\nTurn these verified achievements into professional resume bullet points. Only use what's provided — never fabricate. "
            "Organize them by category (Skills, Projects, Courses Completed, Measurable Outcomes). "
            "Return JSON in the format: {'categories': [{'name': 'Skills', 'bullets': ['...', '...']}, ...]}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Achievements: {achievements}"}
        ]

        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        portfolio = self._extract_json(response)
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        MemoryService.remember(
            text=f"Portfolio generated on {today}: {json.dumps(portfolio)}",
            dataset_name=f"portfolio_{user_id}"
        )
        
        return portfolio
