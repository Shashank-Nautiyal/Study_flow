import json
import re
import uuid
import logging
from app.agents.base_agent import BaseAgent
from app.services.memory_service import MemoryService
from app.services.llm_service import LLMService
from app.agents.roadmap import RoadmapAgent

logger = logging.getLogger(__name__)

class ResourceAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            "resource",
            """
            You are a Resource Agent for a learning platform. Your goal is to analyze learning materials like PDFs, Websites, and Videos.
            You classify them and extract structured summaries.
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

    def handle_resource_add(self, user_id, raw_content, source_type):
        """
        Analyzes a newly added resource and checks for overlap with existing resources.
        Returns a confirmation card to be shown to the user.
        """
        # Skip memory overlap check for now to prevent Ollama connection timeout delays
        # existing = MemoryService.get_context(f"user:{user_id} resources covering similar topics")
        existing = None

        system_prompt = (
            self.system_prompt +
            "\nClassify the following resource content as one of: roadmap, learning_material, reference, project, or mixed. "
            "Extract topics and estimate the study time in hours. Extract a short title. "
            "Return JSON in the format: {'title': '...', 'classification': '...', 'topics': ['...', '...'], 'study_time': 2}"
        )

        if source_type == "youtube_playlist" and isinstance(raw_content, dict):
            # Bypass LLM classification for playlists — metadata is perfectly structured
            total_duration_sec = sum(v.get("duration", 0) for v in raw_content.get("videos", []))
            return {
                "title": f"Playlist: {raw_content.get('title')}",
                "type": "learning_material",
                "topics": [v.get("title") for v in raw_content.get("videos", [])[:5]], # first 5 video titles as topics
                "estimated_time": round(total_duration_sec / 3600, 1),
                "conflict_warning": None,
                "is_playlist": True,
                "playlist_metadata": raw_content
            }

        # Truncate raw content if it's too large for a single LLM prompt
        content_snippet = str(raw_content)[:4000]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Source Type: {source_type}\n\nContent:\n{content_snippet}"}
        ]

        response = LLMService.generate(base_url=self.base_url, model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )

        parsed = self._extract_json(response)
        conflict = None

        if existing:
            conflict_sys_prompt = (
                "You are an AI assistant. Analyze the new resource against existing resources to check for significant overlap. "
                "If there is significant overlap, describe it briefly. If not, return null for overlap. "
                "Return JSON in the format: {'has_overlap': true, 'overlap_description': '...'}"
            )
            conflict_msg = [
                {"role": "system", "content": conflict_sys_prompt},
                {"role": "user", "content": f"New Resource: {json.dumps(parsed)}\n\nExisting Resources: {existing}"}
            ]
            conflict_resp = LLMService.generate(base_url=self.base_url, model=self.model,
                api_key=self.api_key,
                messages=conflict_msg,
                temperature=self.temperature
            )
            conflict_parsed = self._extract_json(conflict_resp)
            if conflict_parsed.get("has_overlap"):
                conflict = conflict_parsed.get("overlap_description")

        return {
            "title": parsed.get("title", "Unknown Resource"),
            "type": parsed.get("classification", "mixed"),
            "topics": parsed.get("topics", []),
            "estimated_time": parsed.get("study_time", 0),
            "conflict_warning": conflict
        }

    def confirm_resource(self, user_id, card, full_content):
        """
        Called after the user clicks 'Confirm' on the resource card.
        Stores the resource and updates the roadmap if applicable.
        """
        resource_id = str(uuid.uuid4())
        card["resource_id"] = resource_id
        
        # ---------------------------------------------------------
        # PRE-PROCESSING FILTER: Condense the resource before Cognee
        # ---------------------------------------------------------
        if card.get("is_playlist"):
            # Extract just the titles
            video_titles = [v.get("title") for v in card.get("playlist_metadata", {}).get("videos", [])]
            # Take the first 50 titles max to fit in context window
            topics_list = ", ".join(video_titles[:50])
            
            clean_sys_prompt = (
                "You are an AI curriculum extractor. Given this list of video titles from a course, "
                "write a highly condensed, strictly 200-word summary of the core concepts taught. "
                "List the top 5 most important entities. Be extremely brief so this can be cleanly saved into a Knowledge Graph."
            )
            raw_input = f"Topics: {topics_list}"
            
        else:
            # For PDFs or Web Scrapes, take the first 4000 characters
            content_snippet = str(full_content)[:4000]
            clean_sys_prompt = (
                "You are an AI document extractor. Given this text snippet from a larger document, "
                "write a highly condensed, strictly 200-word summary of the core concepts. "
                "List the top 5 most important entities. Be extremely brief so this can be cleanly saved into a Knowledge Graph."
            )
            raw_input = f"Content Snippet:\n{content_snippet}"
            
        # Generate the ultra-condensed summary (1 API call)
        condensed_summary = LLMService.generate(
            base_url=self.base_url,
            model=self.model,
            api_key=self.api_key,
            messages=[
                {"role": "system", "content": clean_sys_prompt},
                {"role": "user", "content": raw_input}
            ],
            temperature=0.3
        )

        # ---------------------------------------------------------
        # COGNEE INGESTION: Feed only the condensed summary
        # ---------------------------------------------------------
        # Because this is < 300 words, Cognee will process it as a SINGLE chunk (2-3 API calls instead of 110)
        MemoryService.remember(
            text=f"Resource Title: {card['title']}\nCondensed Concepts:\n{condensed_summary}",
            dataset_name=f"resource_{resource_id}"
        )
        
        MemoryService.remember(
            text=f"Added Resource for {user_id}: {json.dumps(card)}",
            dataset_name=f"user_{user_id}_resources"
        )

        if card.get("is_playlist"):
            # If it's a playlist, we can generate a complete roadmap instantly from the video titles
            roadmap_agent = RoadmapAgent()
            # We mock the payload to build the roadmap dynamically
            goal_string = f"Master playlist: {card['title']} covering topics: {', '.join(video_titles[:25])}"
            roadmap = roadmap_agent.build_roadmap(user_id, goal_string, is_demo=False)
            return {"status": "confirmed", "resource_id": resource_id, "roadmap": roadmap}
            
        if card["type"] in ("learning_material", "mixed"):
            roadmap_agent = RoadmapAgent()
            roadmap_agent.adjust_roadmap_for_new_resource(user_id, card)

        return {"status": "confirmed", "resource_id": resource_id}
