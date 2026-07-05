from app.agents.coach import CoachAgent
from app.agents.quiz import QuizAgent
from app.agents.roadmap import RoadmapAgent
from app.agents.resource import ResourceAgent
from app.agents.diagnostic import DiagnosticAgent
from app.agents.insight import InsightAgent
from app.agents.portfolio import PortfolioAgent
from app.agents.memory_manager import MemoryManagerAgent

class Orchestrator:

    def __init__(self):
        self.agents = {
            "coach": CoachAgent(),
            "quiz": QuizAgent(),
            "roadmap": RoadmapAgent(),
            "resource": ResourceAgent(),
            "diagnostic": DiagnosticAgent(),
            "insight": InsightAgent(),
            "portfolio": PortfolioAgent(),
            "memory_manager": MemoryManagerAgent()
        }

    def route_action(self, user_id, action_type, payload):
        """
        Routes incoming actions to the appropriate specialized agent.
        """
        if action_type == "onboarding_start":
            # Flowchart Step 1 & 2: Check if resources exist. If not, generate Demo Roadmap.
            # If resources DO exist, we rely on the frontend to have already sent "add_resource".
            # The frontend should immediately follow this by prompting the user: "Have you studied this before?"
            if not payload.get("has_resources"):
                return self.agents["roadmap"].build_roadmap(user_id, payload.get("goal"), is_demo=True)
            return {"status": "onboarding_started", "next_step": "ask_prior_knowledge"}

        if action_type == "prior_knowledge_yes":
            # Flowchart: User has studied this before -> "How far along are you?" -> Diagnostic Test
            return self.agents["diagnostic"].run_diagnostic(user_id, payload.get("goal"), phase="phase_1_broad_mapping")

        if action_type == "prior_knowledge_no":
            # Flowchart: User hasn't studied this before -> Skip Diagnostic -> Final Roadmap
            return self.agents["roadmap"].build_roadmap(user_id, payload.get("goal"), is_demo=False)

        if action_type == "onboarding_answers":
            # Sequential diagnostic loop. Once complete -> Final Roadmap
            diagnostic_result = self.agents["diagnostic"].run_diagnostic(
                user_id, 
                payload.get("goal"), 
                phase=payload.get("phase"), 
                prior_answers=payload.get("answers")
            )
            if diagnostic_result.get("phase") == "complete":
                return self.agents["roadmap"].build_roadmap(user_id, payload.get("goal"), is_demo=False)
            return diagnostic_result

        if action_type == "add_resource":
            return self.agents["resource"].handle_resource_add(user_id, payload.get("content"), payload.get("source_type"))

        if action_type == "confirm_resource":
            return self.agents["resource"].confirm_resource(user_id, payload.get("card"), payload.get("full_content"))

        if action_type == "mark_source_complete":
            return self.agents["quiz"].generate_quiz(user_id, payload.get("source_id"))

        if action_type == "submit_quiz":
            return self.agents["quiz"].score_quiz(
                user_id, 
                payload.get("source_id"), 
                payload.get("questions"), 
                payload.get("answers")
            )

        if action_type == "chat_message":
            return self.agents["coach"].coach_reply(user_id, payload.get("message"))
            
        if action_type == "generate_portfolio":
            return self.agents["portfolio"].generate_portfolio(user_id)

        # scheduled jobs — not user-triggered
        if action_type == "scheduled_morning":
            return self.agents["insight"].morning_briefing(user_id)

        if action_type == "scheduled_weekly":
            # order matters — Memory Manager always runs AFTER Insight
            insight_result = self.agents["insight"].weekly_review(user_id)
            return {"insight": insight_result}

        raise ValueError(f"Unknown action_type: {action_type}")
