import logging
import datetime
import json
from app.agents.base_agent import BaseAgent
from app.services.memory_service import MemoryService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class CoachAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            "coach",
            """
            You are an AI learning coach.
            Encourage students.
            Explain difficult concepts.
            Give hints.
            Don't generate quizzes.
            Don't create roadmaps.
            """
        )

    def coach_reply(self, user_id, message):
        """
        The Coach Agent handles general chat. It pulls full history context to provide personalized mentoring.
        """
        full_context = MemoryService.get_context(
            f"user:{user_id} full conversation history, quiz scores, weak areas, roadmap position, original goal, recent activity logs, learning style"
        )

        system_prompt = (
            self.system_prompt +
            "\nYou are a mentor who remembers this learner's entire journey. Reference past context naturally. Never repeat advice already given."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {full_context}\n\nUser Message: {message}"}
        ]

        reply = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Save conversation turn to memory
        MemoryService.remember(
            text=f"Coach conversation on {today} — user said: '{message}' — coach replied: '{reply}'",
            dataset_name=f"chat_history_{user_id}"
        )

        return reply

    def deliver_goal_drift_alert(self, user_id, drift_info):
        """
        Called by the Insight Agent during the weekly review to gently deliver a goal drift alert to the user.
        """
        system_prompt = (
            self.system_prompt +
            "\nDeliver this goal drift finding to the user gently. Offer to redirect them back on track or update their original goal."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Drift info: {json.dumps(drift_info)}"}
        ]

        reply = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        return reply
