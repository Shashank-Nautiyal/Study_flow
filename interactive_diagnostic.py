import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()
os.environ["TEST_MODE"] = "true"  # Bypass DB migrations for quick testing

from app.agents.diagnostic import DiagnosticAgent

def run_interactive_test():
    print("\n=============================================")
    print("   AI Growth Tracker - Diagnostic Agent UI   ")
    print("=============================================\n")
    
    agent = DiagnosticAgent()
    user_id = "manual_tester_01"
    
    goal = input("🎯 What is your learning goal? (e.g., 'Learn Python'): ")
    print("\n[Agent Thinking...] Generating mapping questions...")
    
    # PHASE 1
    res1 = agent.run_diagnostic(user_id, goal, "phase_1_broad_mapping")
    questions = res1.get("questions", [])
    
    print("\n--- PHASE 1: Broad Mapping ---")
    print("Please answer with 'yes', 'no', or 'somewhat':\n")
    
    prior_answers = []
    # Just ask the first 3 questions to keep the test quick
    for q in questions[:3]:
        ans = input(f"Q: {q['text']}\nYour answer: ").strip().lower()
        # Force a 'somewhat' if they didn't provide one, just so we can test Phase 2
        if ans not in ['yes', 'no', 'somewhat']:
            ans = 'somewhat'
        
        prior_answers.append({"topic": q['text'], "level": ans})

    # Ensure there is at least one 'somewhat' answer to trigger Phase 2 properly
    if not any(a['level'] == 'somewhat' for a in prior_answers):
        print("\n(Forcing one answer to 'somewhat' so we can test the Drill Down phase...)")
        prior_answers[0]["level"] = "somewhat"
        
    print("\n[Agent Thinking...] Generating drill-down questions...")
    
    # PHASE 2
    res2 = agent.run_diagnostic(user_id, goal, "phase_2_drill_down", prior_answers=prior_answers)
    deep_questions = res2.get("questions", [])
    
    print("\n--- PHASE 2: Drill Down ---")
    print("Please provide a detailed, open-ended answer:\n")
    
    open_ended_answers = []
    for dq in deep_questions:
        ans = input(f"Q ({dq['topic']}): {dq['text']}\nYour detailed answer: ").strip()
        open_ended_answers.append({"topic": dq['topic'], "answer": ans})
        
    print("\n[Agent Thinking...] Scoring your answers...")
    
    # PHASE 2 SCORE
    res3 = agent.run_diagnostic(user_id, goal, "phase_2_score", prior_answers=open_ended_answers)
    scores = res3.get("verified_scores", [])
    
    print("\n--- YOUR SCORES & FEEDBACK ---")
    for score in scores:
        print(f"Topic: {score.get('topic')}")
        print(f"Score: {score.get('score')}/100")
        if score.get("misconceptions"):
            print(f"Misconception Found: {score.get('misconceptions')[0]}")
    
    print("\n[Agent Thinking...] Extracting your learning profile...")
    
    # PHASE 3 
    profile_answers = [
        {"question": "How do you prefer to learn?", "answer": "I like hands-on coding."},
        {"question": "How much time do you have?", "answer": "1 hour a day."},
        {"question": "When do you need to know this?", "answer": "No strict deadline."}
    ]
    res4 = agent.run_diagnostic(user_id, goal, "phase_3_learning_profile", prior_answers=profile_answers)
    
    print("\n--- EXTRACTED LEARNING PROFILE ---")
    print(json.dumps(res4.get("profile", {}), indent=2))
    
    print("\n✅ Diagnostic Complete!")

if __name__ == "__main__":
    run_interactive_test()
