import json
import re
import logging
from app.agents.base_agent import BaseAgent
from app.services.memory_service import MemoryService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class RoadmapAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            "roadmap",
            """
            You are a Roadmap Agent for a learning platform. Your goal is to build personalized, weekly learning roadmaps.
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

    def build_roadmap(self, user_id, goal, is_demo=False):
        """
        Builds a roadmap based on the user's verified state and available resources.
        If is_demo is True, generates a generic preview roadmap.
        If is_demo is False, generates the final personalized roadmap skipping verified topics.
        """
        verified_state = MemoryService.get_context(f"user:{user_id} verified knowledge state for {goal}")
        learning_profile = MemoryService.get_context(f"user:{user_id} learning profile")
        resources = MemoryService.get_context(f"user:{user_id} resources added for {goal}")

        system_prompt = self.system_prompt + "\n"
        
        if is_demo:
            system_prompt += (
                "Generate a demo learning roadmap for this goal from general knowledge. Mark it as DEMO. "
                "Divide into weeks. Suggest projects and milestones. "
                "Return JSON in the format: {'roadmap': [{'week': 1, 'topics': [...], 'milestone': '...'}, ...], 'is_demo': true}"
            )
        else:
            system_prompt += (
                "Build a FINAL personalized learning roadmap. "
                "Skip topics that the user has already verified they know (from Verified State). "
                "If resources are provided, slot them into the correct roadmap positions. "
                "Preserve chronological learning order. "
                "Divide into weeks. Suggest projects and milestones.\n"
                "Return JSON in the format: {'roadmap': [{'week': 1, 'topics': [...], 'resources': [...], 'project': '...'}, ...], 'is_demo': false}"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": f"Goal: {goal}\nVerified State: {verified_state}\nProfile: {learning_profile}\nResources: {resources}"
            }
        ]

        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        roadmap = self._extract_json(response)
        
        MemoryService.remember(
            text=f"Roadmap generated for {goal} (is_demo={is_demo}): {json.dumps(roadmap)}",
            dataset_name=f"roadmap_{user_id}"
        )
        
        return roadmap

    def adjust_roadmap_for_new_resource(self, user_id, resource):
        """
        Called by the Resource Agent after a new resource is confirmed to find the best slot in the roadmap.
        """
        current_roadmap = MemoryService.get_context(f"user:{user_id} current roadmap")
        
        system_prompt = (
            self.system_prompt + 
            "\nFind the best week/position for this new resource in the existing roadmap. "
            "Return JSON in the format: {'recommended_week': 2, 'reason': '...'}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": f"Current Roadmap: {current_roadmap}\nNew Resource: {json.dumps(resource)}"
            }
        ]

        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        position = self._extract_json(response)
        
        MemoryService.remember(
            text=f"Resource {resource.get('title', 'Unknown')} slotted at position {position}",
            dataset_name=f"roadmap_{user_id}"
        )
        
        return position
