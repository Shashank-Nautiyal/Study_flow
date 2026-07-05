import logging
import datetime
import json
import re
from app.agents.base_agent import BaseAgent
from app.services.memory_service import MemoryService
from app.services.llm_service import LLMService
from app.agents.coach import CoachAgent

logger = logging.getLogger(__name__)

class InsightAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            "insight",
            """
            You are an Insight Agent for a learning platform. Your goal is to analyze learning history, find patterns, and suggest improvements.
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

    def morning_briefing(self, user_id):
        """
        Generates a concise 'Today's Mission' based on recent activity and spaced repetition schedules.
        """
        context = MemoryService.get_context(
            f"user:{user_id} yesterday's incomplete tasks, recent quiz scores, spaced repetition schedule",
            dataset_name=f"user_{user_id}_context"
        )

        system_prompt = (
            self.system_prompt +
            "\nGenerate a short 'Today's Mission' with exactly 3 focused tasks. "
            "Return JSON in the format: {'mission_statement': '...', 'tasks': ['...', '...', '...']}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}"}
        ]

        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        briefing = self._extract_json(response)
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        MemoryService.remember(
            text=f"Morning briefing sent on {today}: {json.dumps(briefing)}",
            dataset_name=f"insights_{user_id}"
        )
        
        return briefing

    def weekly_review(self, user_id):
        """
        Conducts a deep analysis of the past week's activity to find goal drift, decaying topics, and source conflicts.
        """
        context = MemoryService.get_context(
            f"user:{user_id} last 7 days activity logs, quiz scores, original goal, current roadmap position, all resources",
            dataset_name=f"user_{user_id}_context"
        )

        # Prompt 1: Goal Drift
        drift_msg = [
            {"role": "system", "content": self.system_prompt + "\nCompare the user's original goal to their actual activity. Is there a mismatch/drift? Be specific. Return JSON: {'has_drift': true, 'drift_analysis': '...'}"},
            {"role": "user", "content": f"Context: {context}"}
        ]
        drift_resp = LLMService.generate(base_url=self.base_url, model=self.model, api_key=self.api_key, messages=drift_msg, temperature=self.temperature)
        goal_drift = self._extract_json(drift_resp)

        # Prompt 2: Decaying Topics
        decay_msg = [
            {"role": "system", "content": self.system_prompt + "\nBased on the logs, which topics haven't been touched in 14+ days? Return JSON: {'decaying_topics': ['...', '...']}"},
            {"role": "user", "content": f"Context: {context}"}
        ]
        decay_resp = LLMService.generate(base_url=self.base_url, model=self.model, api_key=self.api_key, messages=decay_msg, temperature=self.temperature)
        decaying_topics = self._extract_json(decay_resp).get("decaying_topics", [])

        # Prompt 3: Source Conflicts
        conflict_msg = [
            {"role": "system", "content": self.system_prompt + "\nDo any two resources explain the same concept differently? Reconcile if so. Return JSON: {'conflicts': [{'concept': '...', 'conflict': '...', 'reconciliation': '...'}]}"},
            {"role": "user", "content": f"Context: {context}"}
        ]
        conflict_resp = LLMService.generate(base_url=self.base_url, model=self.model, api_key=self.api_key, messages=conflict_msg, temperature=self.temperature)
        source_conflicts = self._extract_json(conflict_resp).get("conflicts", [])

        summary = {
            "goal_drift": goal_drift,
            "decaying_topics": decaying_topics,
            "source_conflicts": source_conflicts
        }

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        MemoryService.remember(
            text=f"Weekly review for {today}: {json.dumps(summary)}",
            dataset_name=f"insights_{user_id}"
        )

        # If significant goal drift is detected, proactively dispatch the CoachAgent to handle it
        if goal_drift.get("has_drift"):
            coach = CoachAgent()
            coach_alert = coach.deliver_goal_drift_alert(user_id, goal_drift.get("drift_analysis"))
            summary["coach_alert_dispatched"] = coach_alert

        return summary
