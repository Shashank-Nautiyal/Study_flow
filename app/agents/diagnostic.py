import json
import re
import logging
from app.agents.base_agent import BaseAgent
from app.services.memory_service import MemoryService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class DiagnosticAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            "diagnostic",
            """You are a Diagnostic Agent for a learning platform. Your goal is to accurately assess a user's knowledge state and extract structured learning profiles.
Always return your output in valid, raw JSON format without markdown blocks if requested."""
        )

    def _extract_json(self, text):
        """Helper to safely extract JSON from LLM outputs that might include markdown wrappers."""
        try:
            # Try parsing directly first
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # Try finding JSON within markdown code blocks or curly braces
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        logger.error(f"Failed to extract JSON from response: {text}")
        return {}
        
    def run_diagnostic(self, user_id, goal, phase, prior_answers=None):
        """
        Executes a phase of the diagnostic flow.
        
        Args:
            user_id: string ID for the user
            goal: string describing the user's learning goal
            phase: string indicating which phase to execute
            prior_answers: list or dict of answers from the previous phase
        """
        # 1. Recall prior knowledge history from memory
        context = MemoryService.get_context(f"user:{user_id} prior knowledge history for {goal}")
        
        if phase == "phase_1_broad_mapping":
            system_prompt = (
                self.system_prompt + 
                "\n\nGenerate 8-10 broad yes/no/somewhat questions mapping surface knowledge of the given goal. "
                "Output exactly in this JSON format:\n"
                '{"questions": [{"id": "q1", "text": "Question text here?"}]}'
            )
            user_prompt = f"Goal: {goal}\nContext: {context}"
            
            response = LLMService.generate(base_url=self.base_url, model=self.model,
                api_key=self.api_key,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=self.temperature
            )
            
            parsed = self._extract_json(response)
            return {"phase": "phase_1", "questions": parsed.get("questions", [])}
            
        if phase == "phase_2_drill_down":
            # Find topics they answered 'somewhat' on
            uncertain_topics = [ans['topic'] for ans in prior_answers if ans.get('level') == 'somewhat']
            
            system_prompt = (
                self.system_prompt +
                "\n\nFor each uncertain topic provided, generate one open-ended question that tests real understanding, not just recall. "
                "Output exactly in this JSON format:\n"
                '{"questions": [{"topic": "Topic Name", "text": "Open ended question?"}]}'
            )
            user_prompt = f"Topics: {uncertain_topics}"
            
            response = LLMService.generate(base_url=self.base_url, model=self.model,
                api_key=self.api_key,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=self.temperature
            )
            
            parsed = self._extract_json(response)
            return {"phase": "phase_2", "questions": parsed.get("questions", [])}
            
        if phase == "phase_2_score":
            system_prompt = (
                self.system_prompt + 
                "\n\nScore each open-ended answer from 0-100 and flag specific misconceptions. "
                "Output exactly in this JSON format:\n"
                '{"scores": [{"topic": "Topic Name", "score": 85, "misconceptions": ["mistake 1"]}]}'
            )
            user_prompt = f"Answers: {prior_answers}"
            
            response = LLMService.generate(base_url=self.base_url, model=self.model,
                api_key=self.api_key,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=self.temperature
            )
            
            parsed = self._extract_json(response)
            scores = parsed.get("scores", [])
            
            # Remember verified state
            MemoryService.remember(
                text=f"Verified knowledge state for {goal}: {json.dumps(scores)}",
                dataset_name=f"diagnostic_{user_id}"
            )
            
            return {"phase": "phase_2_complete", "verified_scores": scores}
            
        if phase == "phase_3_learning_profile":
            system_prompt = (
                self.system_prompt + 
                "\n\nExtract a structured learning profile based on the user's answers. "
                "Determine their format preference, daily hours available, deadline style, and goal specificity. "
                "Output exactly in this JSON format:\n"
                '{"profile": {"format_preference": "video/text", "daily_hours": 2, "deadline_style": "strict/flexible", "goal_specificity": "broad/specific"}}'
            )
            user_prompt = f"Answers: {prior_answers}"
            
            response = LLMService.generate(base_url=self.base_url, model=self.model,
                api_key=self.api_key,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=self.temperature
            )
            
            parsed = self._extract_json(response)
            profile = parsed.get("profile", {})
            
            # Remember learning profile
            MemoryService.remember(
                text=f"Learning profile for {user_id}: {json.dumps(profile)}",
                dataset_name=f"diagnostic_{user_id}"
            )
            
            return {"phase": "complete", "profile": profile}

        return {"error": "Invalid phase"}
