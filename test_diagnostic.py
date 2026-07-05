import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.agents.diagnostic import DiagnosticAgent
from app.services.memory_service import MemoryService

import unittest.mock

def run_test():
    print("Initializing Diagnostic Agent...")
    
    with unittest.mock.patch('cognee.add') as mock_add, \
         unittest.mock.patch('cognee.cognify') as mock_cognify, \
         unittest.mock.patch('cognee.search') as mock_search:
        
        # Mock search to return dummy objects that have a .text attribute
        class MockResult:
            text = "User has basic knowledge of variables and loops."
        mock_search.return_value = [MockResult()]
        
        mock_add.side_effect = lambda data, dataset_name, *args, **kwargs: print(f"[Cognee Mock] Saving to '{dataset_name}':\n{data}")
        mock_cognify.return_value = None
        
        agent = DiagnosticAgent()
        user_id = "test_user_123"
        goal = "Learn Python for data analysis"
    
    print("\n--- PHASE 1: Broad Mapping ---")
    res1 = agent.run_diagnostic(user_id, goal, "phase_1_broad_mapping")
    print(f"Response:\n{res1}")
    
    print("\n--- PHASE 2: Drill Down ---")
    # Simulate user answering the broad questions with some 'somewhat' answers
    prior_answers = [
        {"topic": "Pandas DataFrames", "level": "somewhat"},
        {"topic": "Object Oriented Programming", "level": "no"},
        {"topic": "Basic Syntax", "level": "yes"}
    ]
    res2 = agent.run_diagnostic(user_id, goal, "phase_2_drill_down", prior_answers=prior_answers)
    print(f"Response:\n{res2}")
    
    print("\n--- PHASE 2: Score ---")
    # Simulate user answering the open ended questions
    open_ended_answers = [
        {"topic": "Pandas DataFrames", "answer": "A dataframe is like a dictionary of lists. You can filter it."},
    ]
    res3 = agent.run_diagnostic(user_id, goal, "phase_2_score", prior_answers=open_ended_answers)
    print(f"Response:\n{res3}")
    
    print("\n--- PHASE 3: Learning Profile ---")
    profile_answers = [
        {"question": "How do you prefer to learn?", "answer": "I like watching videos and coding along."},
        {"question": "How much time do you have?", "answer": "About 1 hour every evening."},
        {"question": "When do you need to know this?", "answer": "I have an interview in 3 weeks."}
    ]
    res4 = agent.run_diagnostic(user_id, goal, "phase_3_learning_profile", prior_answers=profile_answers)
    print(f"Response:\n{res4}")
    
    print("\nDone!")

if __name__ == "__main__":
    run_test()
