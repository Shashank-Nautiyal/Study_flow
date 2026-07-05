import json
import re
import datetime
import logging
from app.agents.base_agent import BaseAgent
from app.services.memory_service import MemoryService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class QuizAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            "quiz",
            """
            You are a Quiz Agent for a learning platform. Your goal is to generate and grade quizzes to test user knowledge.
            Generate conceptual and applied questions. Explain every answer.
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

    def generate_quiz(self, user_id, source_id):
        """
        Generates a quiz based on a specific resource content and the user's past weak areas.
        """
        content = MemoryService.get_context(f"resource:{source_id} content", dataset_name=f"resource_{source_id}")
        past_scores = MemoryService.get_context(f"user:{user_id} past scores on topics in {source_id}")

        system_prompt = (
            self.system_prompt + 
            "\nGenerate 5 questions from this content: 3 conceptual MCQ, and 2 open-ended applied questions. "
            "Return JSON in the format: {'questions': [{'id': 1, 'type': 'mcq', 'text': '...', 'options': [...]}, {'id': 2, 'type': 'open_ended', 'text': '...'}]}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Content: {content}\nPast weak areas: {past_scores}"}
        ]

        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        return self._extract_json(response)

    def score_quiz(self, user_id, source_id, questions, answers):
        """
        Scores a quiz and identifies specific knowledge gaps for wrong answers.
        """
        system_prompt = (
            self.system_prompt +
            "\nScore each answer 0-100. For wrong answers, identify the specific missing concept. "
            "Return JSON in the format: {'overall_score': 80, 'results': [{'q_id': 1, 'score': 100}, ...], 'wrong_answers': [{'q_id': 2, 'concept': 'Backpropagation', 'reason': '...'}...]}"
        )

        qa_pairs = [{"question": q, "answer": a} for q, a in zip(questions, answers)]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Q&A pairs: {json.dumps(qa_pairs)}"}
        ]

        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        results = self._extract_json(response)
        
        # Add hints by recalling where the concept was explained in the resource
        if "wrong_answers" in results:
            for wrong in results["wrong_answers"]:
                concept = wrong.get("concept")
                if concept:
                    source_hint = MemoryService.get_context(f"where is '{concept}' explained", dataset_name=f"resource_{source_id}")
                    if source_hint:
                        wrong["hint"] = f"Review: {source_hint[:200]}..."

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        MemoryService.remember(
            text=f"Quiz result for {source_id}: {json.dumps(results)}",
            dataset_name=f"quiz_results_{user_id}"
        )

        self._update_spaced_repetition_schedule(user_id, source_id, results)
        
        return results

    def _update_spaced_repetition_schedule(self, user_id, source_id, results):
        """
        Updates the next review date for the given source based on quiz results.
        """
        # A simple spaced repetition update logic
        overall_score = results.get("overall_score", 0)
        days_until_next = 1 if overall_score < 70 else 7
        next_review_date = (datetime.datetime.now() + datetime.timedelta(days=days_until_next)).strftime("%Y-%m-%d")
        
        MemoryService.remember(
            text=f"Source {source_id} spaced repetition update: Next review on {next_review_date}. Score was {overall_score}.",
            dataset_name=f"spaced_repetition_{user_id}"
        )

    def check_spaced_repetition_due(self, user_id):
        """
        Retrieves all resources/topics that are due for spaced repetition review today.
        """
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        schedule_context = MemoryService.get_context(f"What resources are scheduled for spaced repetition review on or before {today} for user:{user_id}?", dataset_name=f"spaced_repetition_{user_id}")
        
        system_prompt = "Extract a JSON list of source IDs that are due for review based on the context. Format: {'due_sources': ['id1', 'id2']}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {schedule_context}\nToday: {today}"}
        ]

        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )
        
        return self._extract_json(response)
