import logging

from app.agents.base_agent import BaseAgent
from app.services.memory_service import MemoryService
from cognee import SearchType

logger = logging.getLogger(__name__)


class MemoryManagerAgent(BaseAgent):
    """Specialized agent that combines LLM summarization with Cognee memory.

    Unlike other agents that auto-store raw interactions, the Memory Manager
    can compress, summarize, and intelligently manage the knowledge graph.
    """

    def __init__(self):
        super().__init__(
            "memory_manager",
            """
            You are a memory management agent.

            Summarize and compress conversation history.

            Extract key facts, preferences, and progress.

            Return structured memory objects with:
            - Key facts learned
            - Student preferences
            - Progress milestones
            - Topics discussed
            - Action items

            Keep summaries concise for fast retrieval.
            """
        )

    def summarize_and_store(self, conversation_history):
        """Use the LLM to summarize a conversation, then store the summary in Cognee."""

        summary = self.run(
            user_input=(
                "Summarize the following conversation into key facts, "
                "student progress, and action items. Be concise.\n\n"
                f"{conversation_history}"
            )
        )

        # Store the compressed summary (not the raw conversation)
        MemoryService.remember(
            text=summary,
            dataset_name="conversation_summaries"
        )

        logger.info("Conversation summary stored in Cognee.")
        return summary

    def recall_student_profile(self, student_query):
        """Recall everything known about a student from the knowledge graph."""
        return MemoryService.recall(
            query=student_query,
            search_type=SearchType.GRAPH_COMPLETION
        )

    def recall_progress(self, topic):
        """Recall learning progress for a specific topic."""
        return MemoryService.recall(
            query=f"What progress has been made on {topic}?",
            search_type=SearchType.INSIGHTS
        )

    def get_learning_insights(self, student_query):
        """Get structured entity relationships about learning patterns."""
        return MemoryService.recall(
            query=student_query,
            search_type=SearchType.INSIGHTS
        )

    def clear_memory(self, everything=False):
        """Reset the memory store."""
        MemoryService.forget(everything=everything)
        logger.info(f"Memory cleared (everything={everything}).")
