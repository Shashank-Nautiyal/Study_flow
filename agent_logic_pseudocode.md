<USER_REQUEST>
# AI Growth Tracker — Agent Pseudocode Reference

## How to use this file

This is planning-level pseudocode, not runnable code. Helper functions like
`parse_questions()`, `filter_answers()`, `web_search()`, `zip_qa()` are
placeholders — you write their real logic during implementation. The real
`recall()`, `remember()`, `improve()`, `forget()`, and `call_llm()` functions
live in `memory.py` and `llm.py` and wrap the actual Cognee SDK and LiteLLM
calls — their exact internal syntax will differ from this pseudocode, that's
expected and fine.

**All 8 agents below belong inside one `agents.py` file for now.** Do not
split into separate files per agent yet — that only happens after each one
is proven working end to end, per our earlier file-structure discussion.

---

## Shared Interfaces (from `memory.py` and `llm.py`)

```python
def recall(query: str, dataset: str = None) -> str:
    """Ask Cognee's memory graph a question, get relevant context back as text."""
    ...

def recall_with_reference(query: str, dataset: str = None) -> dict:
    """Like recall(), but also returns the source location (timestamp/page)
    the answer came from — uses Cognee's native reference-point flag."""
    ...

def remember(content: str, metadata: dict = None) -> None:
    """Store a fact/event/outcome into Cognee's memory graph."""
    ...

def improve() -> None:
    """Trigger Cognee's self-improvement pass — reweights graph connections."""
    ...

def forget(query: str) -> None:
    """Remove outdated or mastered content from Cognee's memory graph."""
    ...

def call_llm(model: str, system: str, user: str) -> str:
    """LiteLLM wrapper — same signature no matter which provider."""
    ...
```

## The Pattern Every Agent Follows

```python
def agent_template(input_data):
    context = recall(query=...)                    # 1. recall
    response = call_llm(model=..., system=..., user=...)  # 2. think
    result = parse_structured_output(response)      # 3. act
    remember(content=..., metadata=...)              # 4. remember
    return result
```

---

## 1. Diagnostic Agent
**Model:** Gemini 2.5 Pro | **Triggered by:** onboarding + periodic re-assessment

```python
MODEL = "gemini/gemini-2.5-pro"

def run_diagnostic(user_id, goal, phase, prior_answers=None):

    context = recall(f"user:{user_id} prior knowledge history for {goal}")

    if phase == "phase_1_broad_mapping":
        questions = call_llm(
            model=MODEL,
            system="Generate 8-10 broad yes/no/somewhat questions mapping surface knowledge of {goal}",
            user=f"Goal: {goal}\nContext: {context}"
        )
        return {"phase": "phase_1", "questions": parse_questions(questions)}

    if phase == "phase_2_drill_down":
        uncertain_topics = filter_answers(prior_answers, level="somewhat")
        deep_questions = call_llm(
            model=MODEL,
            system="For each uncertain topic, generate one open-ended question that tests real understanding, not recall",
            user=f"Topics: {uncertain_topics}"
        )
        return {"phase": "phase_2", "questions": parse_questions(deep_questions)}

    if phase == "phase_2_score":
        # never trust self-report — this is where claimed knowledge gets verified
        scored = call_llm(
            model=MODEL,
            system="Score each open-ended answer 0-100 and flag specific misconceptions",
            user=f"Answers: {prior_answers}"
        )
        scores = parse_scores(scored)

        remember(
            content=f"Verified knowledge state for {goal}: {scores}",
            metadata={"user_id": user_id, "type": "diagnostic_result", "goal": goal}
        )
        return {"phase": "phase_2_complete", "verified_scores": scores}

    if phase == "phase_3_learning_profile":
        profile = call_llm(
            model=MODEL,
            system="Extract structured learning profile: format preference, daily hours, deadline style, goal specificity",
            user=f"Answers: {prior_answers}"
        )
        parsed_profile = parse_profile(profile)

        remember(
            content=f"Learning profile: {parsed_profile}",
            metadata={"user_id": user_id, "type": "learning_profile"}
        )
        return {"phase": "complete", "profile": parsed_profile}
```

---

## 2. Roadmap Agent
**Model:** Claude Opus | **Triggered by:** after Diagnostic completes, or a resource is added

```python
MODEL = "claude-opus"

def build_roadmap(user_id, goal):

    verified_state = recall(f"user:{user_id} verified knowledge state for {goal}")
    learning_profile = recall(f"user:{user_id} learning profile")
    resources = recall(f"user:{user_id} resources added for {goal}")

    if resources:
        structure = call_llm(
            model=MODEL,
            system="Build a roadmap using ONLY these resources, ordered chronologically, skip verified topics",
            user=f"Resources: {resources}\nVerified: {verified_state}\nProfile: {learning_profile}"
        )
    else:
        structure = call_llm(
            model=MODEL,
            system="Generate a demo roadmap for this goal from general knowledge, mark as DEMO",
            user=f"Goal: {goal}\nVerified: {verified_state}\nProfile: {learning_profile}"
        )

    roadmap = parse_roadmap(structure)

    remember(
        content=f"Roadmap generated: {roadmap}",
        metadata={"user_id": user_id, "type": "roadmap", "goal": goal,
                   "source": "resources" if resources else "demo"}
    )
    return roadmap


def adjust_roadmap_for_new_resource(user_id, resource):
    # called by Resource Agent after a new resource is confirmed
    current_roadmap = recall(f"user:{user_id} current roadmap")

    position = call_llm(
        model=MODEL,
        system="Find the best position for this resource in the existing roadmap",
        user=f"Roadmap: {current_roadmap}\nNew resource: {resource}"
    )

    remember(
        content=f"Resource {resource['id']} slotted at position {position}",
        metadata={"user_id": user_id, "type": "roadmap_update"}
    )
    return position
```

---

## 3. Resource Agent
**Model:** GPT-4o + web search | **Triggered by:** resource added, or recommendation requested

```python
MODEL = "gpt-4o"  # web_search tool enabled

def handle_resource_add(user_id, raw_content, source_type):
    # source_type: youtube | pdf | website | video | audio | epub

    existing = recall(f"user:{user_id} resources covering similar topics")

    classification = call_llm(
        model=MODEL,
        system="Classify as: roadmap | learning_material | reference | project | mixed. Extract topics and estimate study time.",
        user=f"Content: {raw_content[:2000]}"
    )
    parsed = parse_classification(classification)

    conflict = None
    if existing:
        conflict_check = call_llm(
            model=MODEL,
            system="Does this new resource significantly overlap with existing resources? Describe overlap if yes.",
            user=f"New: {parsed}\nExisting: {existing}"
        )
        conflict = parse_conflict(conflict_check)

    # returned to user as a confirmation card — NOT remembered yet
    return {
        "title": parsed["title"],
        "type": parsed["classification"],
        "topics": parsed["topics"],
        "estimated_time": parsed["study_time"],
        "conflict_warning": conflict
    }


def confirm_resource(user_id, card, full_content):
    # only called after the user clicks "Confirm" on the card
    remember(
        content=full_content,
        metadata={
            "user_id": user_id, "type": "resource",
            "classification": card["type"], "topics": card["topics"],
            "resource_id": generate_id()
        }
    )

    if card["type"] in ("learning_material", "mixed"):
        adjust_roadmap_for_new_resource(user_id, card)

    return {"status": "confirmed", "resource_id": card["resource_id"]}


def recommend_resources(user_id, topic):
    profile = recall(f"user:{user_id} learning profile, past resource ratings")
    search_results = web_search(f"best {topic} resources {profile['format_preference']} {profile['level']}")

    ranked = call_llm(
        model=MODEL,
        system="Rank these resources by fit for this learner. Return top 5 with reasons.",
        user=f"Results: {search_results}\nProfile: {profile}"
    )
    return parse_ranked_list(ranked)
```

---

## 4. Quiz Agent
**Model:** Mistral / Qwen | **Triggered by:** source marked complete, or spaced repetition due

```python
MODEL = "mistral-large"

def generate_quiz(user_id, source_id):
    content = recall(f"resource:{source_id} content", dataset=source_id)
    past_scores = recall(f"user:{user_id} past scores on topics in {source_id}")

    questions = call_llm(
        model=MODEL,
        system="Generate 5 questions from this content: 3 conceptual MCQ, 2 open-ended applied",
        user=f"Content: {content}\nPast weak areas: {past_scores}"
    )
    return parse_questions(questions)


def score_quiz(user_id, source_id, questions, answers):
    scored = call_llm(
        model=MODEL,
        system="Score each answer 0-100. For wrong answers, identify the specific gap.",
        user=f"Q&A pairs: {zip_qa(questions, answers)}"
    )
    results = parse_scores(scored)

    for wrong in results["wrong_answers"]:
        source_location = recall_with_reference(f"where is '{wrong['concept']}' explained", dataset=source_id)
        wrong["hint"] = f"Review: {source_location['timestamp_or_page']}"

    remember(
        content=f"Quiz result for {source_id}: {results}",
        metadata={"user_id": user_id, "type": "quiz_result", "source_id": source_id, "date": today()}
    )

    update_spaced_repetition_schedule(user_id, source_id, results)
    return results


def check_spaced_repetition_due(user_id):
    schedule = recall(f"user:{user_id} spaced repetition schedule")
    return [t for t in schedule if t["next_review"] <= today()]
```

---

## 5. Coach Agent
**Model:** GPT-4o | **Triggered by:** chat message, or proactive nudge

```python
MODEL = "gpt-4o"

def coach_reply(user_id, message):
    # the ONLY agent that recalls full history — needs complete context
    full_context = recall(f"""
        user:{user_id} full conversation history, quiz scores, weak areas,
        roadmap position, original goal, recent activity logs, learning style
    """)

    reply = call_llm(
        model=MODEL,
        system="You are a mentor who remembers this learner's entire journey. Reference past context naturally. Never repeat advice already given.",
        user=f"Context: {full_context}\nMessage: {message}"
    )

    remember(
        content=f"Coach conversation — user said: {message} — coach replied: {reply}",
        metadata={"user_id": user_id, "type": "conversation", "date": today()}
    )
    return reply


def deliver_goal_drift_alert(user_id, drift_info):
    # called by Insight Agent, delivered conversationally by Coach
    return call_llm(
        model=MODEL,
        system="Deliver this goal drift finding gently, offer to redirect or update the goal",
        user=f"Drift info: {drift_info}"
    )
```

---

## 6. Insight Agent
**Model:** Gemini Flash | **Triggered by:** every morning (scheduled) + weekly

```python
MODEL = "gemini-flash"

def morning_briefing(user_id):
    context = recall(f"""
        user:{user_id} yesterday's incomplete tasks, recent quiz scores,
        spaced repetition schedule
    """)

    briefing = call_llm(
        model=MODEL,
        system="Generate a short 'Today's Mission' with exactly 3 focused tasks",
        user=f"Context: {context}"
    )

    remember(content=f"Morning briefing sent: {briefing}",
             metadata={"user_id": user_id, "type": "briefing", "date": today()})
    return briefing


def weekly_review(user_id):
    context = recall(f"""
        user:{user_id} last 7 days activity logs, quiz scores,
        original goal, current roadmap position, all resources
    """)

    goal_drift = call_llm(model=MODEL,
        system="Compare original goal to actual activity. Is there a mismatch? Be specific.",
        user=f"Context: {context}")

    decay = call_llm(model=MODEL,
        system="Which topics haven't been touched in 14+ days?",
        user=f"Context: {context}")

    conflicts = call_llm(model=MODEL,
        system="Do any two resources explain the same concept differently? Reconcile if so.",
        user=f"Context: {context}")

    summary = {
        "goal_drift": parse_drift(goal_drift),
        "decaying_topics": parse_decay(decay),
        "source_conflicts": parse_conflicts(conflicts)
    }

    remember(content=f"Weekly review: {summary}",
             metadata={"user_id": user_id, "type": "weekly_review", "week": current_week()})

    if summary["goal_drift"]["detected"]:
        deliver_goal_drift_alert(user_id, summary["goal_drift"])  # hands off to Coach Agent

    return summary
```

---

## 7. Portfolio Agent
**Model:** Claude Sonnet | **Triggered by:** milestone completed, or user opens portfolio view

```python
MODEL = "claude-sonnet"

def generate_portfolio(user_id):
    achievements = recall(f"""
        user:{user_id} all achievements, completed resources,
        quiz scores above 90%, projects finished, skills mastered
    """)

    bullets = call_llm(
        model=MODEL,
        system="Turn these verified achievements into resume bullet points. Only use what's provided — never fabricate.",
        user=f"Achievements: {achievements}"
    )

    portfolio = organize_by_category(parse_bullets(bullets))
    # categories: Skills, Projects, Courses Completed, Measurable Outcomes

    remember(content=f"Portfolio generated, version {next_version(user_id)}",
             metadata={"user_id": user_id, "type": "portfolio_snapshot"})
    return portfolio
```

---

## 8. Memory Manager Agent
**Model:** Groq small model (llama3-8b) | **Triggered by:** weekly, always after Insight Agent

```python
MODEL = "groq/llama3-8b"

def weekly_cleanup(user_id):
    all_memory_state = recall(f"user:{user_id} all stored memories, last interaction dates, mastery scores")

    improve()  # Cognee's native self-improvement pass — reweights the graph

    to_forget = call_llm(
        model=MODEL,
        system="List memory items to forget: mastery > 90% AND not a prerequisite for anything upcoming, OR outdated/replaced resources",
        user=f"State: {all_memory_state}"
    )

    forgotten = []
    for item in parse_forget_list(to_forget):
        forget(item["query"])
        forgotten.append(item)

    report = {"improved": True, "forgotten": forgotten, "date": today()}
    remember(content=f"Weekly cleanup: {report}", metadata={"user_id": user_id, "type": "memory_cleanup"})
    return report
```

---

## Orchestration — Agent Router (LangGraph, added later)

```python
def route_action(user_id, action_type, payload):

    if action_type == "onboarding_start":
        return run_diagnostic(user_id, payload["goal"], phase="phase_1_broad_mapping")

    if action_type == "onboarding_answers":
        # sequential — Diagnostic MUST finish before Roadmap runs
        diagnostic_result = run_diagnostic(user_id, payload["goal"], phase=payload["phase"], prior_answers=payload["answers"])
        if diagnostic_result["phase"] == "complete":
            return build_roadmap(user_id, payload["goal"])
        return diagnostic_result

    if action_type == "add_resource":
        return handle_resource_add(user_id, payload["content"], payload["source_type"])

    if action_type == "confirm_resource":
        return confirm_resource(user_id, payload["card"], payload["full_content"])

    if action_type == "mark_source_complete":
        return generate_quiz(user_id, payload["source_id"])

    if action_type == "submit_quiz":
        return score_quiz(user_id, payload["source_id"], payload["questions"], payload["answers"])

    if action_type == "chat_message":
        return coach_reply(user_id, payload["message"])

    # scheduled jobs — not user-triggered
    if action_type == "scheduled_morning":
        return morning_briefing(user_id)

    if action_type == "scheduled_weekly":
        # order matters — Memory Manager always runs AFTER Insight
        insight_result = weekly_review(user_id)
        cleanup_result = weekly_cleanup(user_id)
        return {"insight": insight_result, "cleanup": cleanup_result}
```

---

## Build Order Reminder

```
1. Diagnostic Agent   ← implement for real first, proves recall/llm/remember pattern
2. Roadmap Agent + Resource Agent
3. Quiz Agent + Coach Agent
4. Insight Agent + Memory Manager + Portfolio Agent
5. Only then: wrap all of this in the LangGraph router above
```

*Reference version 1.0*

the name of model are incorrect but the code for agent is correct can you implement for me 
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-07-02T08:59:57+05:30.
</ADDITIONAL_METADATA>