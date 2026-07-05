<USER_REQUEST>
Yes. I actually think this is the better design for your project.

Since you haven't decided which model each agent should use, **don't hardcode any provider or model inside the agents**. Make every agent completely provider-agnostic. Then later you can change a model by editing one config file instead of touching the agent code.

I'd structure it like this:

```text
app/
│
├── agents/
│   ├── base_agent.py
│   ├── coach.py
│   ├── diagnostic.py
│   ├── roadmap.py
│   ├── quiz.py
│   ├── resource.py
│   ├── insight.py
│   ├── portfolio.py
│   └── orchestrator.py
│
├── config/
│   └── agent_config.py
│
└── services/
    └── llm_service.py
```

---

# Step 1: agent_config.py

This is the only file you'll edit when changing providers.

```python
import os
from dotenv import load_dotenv

load_dotenv()

AGENT_CONFIG = {

    "coach": {
        "provider": "groq",
        "model": "",
        "api_key": os.getenv("GROQ_API_KEY"),
        "temperature": 0.8
    },

    "diagnostic": {
        "provider": "nvidia",
        "model": "",
        "api_key": os.getenv("NVIDIA_API_KEY"),
        "temperature": 0.2
    },

    "roadmap": {
        "provider": "fireworks",
        "model": "",
        "api_key": os.getenv("FIREWORKS_API_KEY"),
        "temperature": 0.3
    },

    "quiz": {
        "provider": "cerebras",
        "model": "",
        "api_key": os.getenv("CEREBRAS_API_KEY"),
        "temperature": 0.2
    },

    "resource": {
        "provider": "openrouter",
        "model": "",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "temperature": 0.4
    },

    "insight": {
        "provider": "groq",
        "model": "",
        "api_key": os.getenv("GROQ_API_KEY"),
        "temperature": 0.5
    },

    "portfolio": {
        "provider": "fireworks",
        "model": "",
        "api_key": os.getenv("FIREWORKS_API_KEY"),
        "temperature": 0.4
    }

}
```

Notice every model is empty.

Later you'll simply write

```python
"model": "groq/llama-3.3-70b-versatile"
```

or

```python
"model": "openrouter/google/gemini-2.5-pro"
```

without changing anything else.

---

# Step 2: LLM Service

This is the only place LiteLLM exists.

```python
from litellm import completion


class LLMService:

    @staticmethod
    def generate(
        model,
        api_key,
        messages,
        temperature=0.7,
        max_tokens=2048
    ):

        response = completion(
            model=model,
            api_key=api_key,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content
```

---

# Step 3: Base Agent

```python
from services.llm_service import LLMService
from config.agent_config import AGENT_CONFIG


class BaseAgent:

    def __init__(self, agent_name, system_prompt):

        config = AGENT_CONFIG[agent_name]

        self.model = config["model"]
        self.api_key = config["api_key"]
        self.temperature = config["temperature"]

        self.system_prompt = system_prompt

    def run(self, user_input):

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        return LLMService.generate(
            model=self.model,
            api_key=self.api_key,
            messages=messages,
            temperature=self.temperature
        )
```

---

# Coach Agent

```python
from agents.base_agent import BaseAgent


class CoachAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            "coach",
            """
            You are an AI learning coach.

            Encourage students.

            Explain difficult concepts.

            Give hints.

            Don't generate quizzes.

            Don't create roadmaps.
            """
        )
```

---

# Diagnostic Agent

```python
from agents.base_agent import BaseAgent


class DiagnosticAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            "diagnostic",
            """
            Analyze the student's skills.

            Return

            - Skill Level
            - Weak Topics
            - Strong Topics
            - Confidence
            """
        )
```

---

# Roadmap Agent

```python
class RoadmapAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            "roadmap",
            """
            Build personalized learning roadmaps.

            Divide into weeks.

            Suggest projects.

            Suggest milestones.
            """
        )
```

---

# Quiz Agent

```python
class QuizAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            "quiz",
            """
            Generate quizzes.

            Include answers.

            Explain every answer.
            """
        )
```

---

# Resource Agent

```python
class ResourceAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            "resource",
            """
            Analyze

            PDFs

            Websites

            YouTube videos

            Return structured summaries.
            """
        )
```

---

# Insight Agent

```python
class InsightAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            "insight",
            """
            Analyze learning history.

            Find patterns.

            Suggest improvements.
            """
        )
```

---

# Portfolio Agent

```python
class PortfolioAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            "portfolio",
            """
            Convert completed projects into

            Resume bullets

            Portfolio descriptions

            GitHub README sections.
            """
        )
```

---

# Orchestrator

```python
from agents.coach import CoachAgent
from agents.quiz import QuizAgent
from agents.roadmap import RoadmapAgent
from agents.resource import ResourceAgent
from agents.diagnostic import DiagnosticAgent
from agents.insight import InsightAgent
from agents.portfolio import PortfolioAgent


class Orchestrator:

    def __init__(self):

        self.agents = {
            "coach": CoachAgent(),
            "quiz": QuizAgent(),
            "roadmap": RoadmapAgent(),
            "resource": ResourceAgent(),
            "diagnostic": DiagnosticAgent(),
            "insight": InsightAgent(),
            "portfolio": PortfolioAgent()
        }

    def execute(self, task, input_data):

        if task not in self.agents:
            raise ValueError(f"Unknown task: {task}")

        return self.agents[task].run(input_data)
```

---

## 💡 Since you're building a hackathon project, I'd make one additional improvement.

Instead of passing just a string to `run()`, define a common interface like:

```python
agent.run(
    user_input="...",
    context={},
    memory=[],
    attachments=[],
    metadata={}
)
```

Even if some agents ignore `attachments` or `metadata` today, you'll be able to add PDFs, Cognee memory, YouTube transcripts, retrieved documents, or tool outputs later **without changing every agent's method signature**. It keeps the architecture flexible while still staying lightweight enough for a 6-day hackathon.

</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-07-01T22:14:51+05:30.
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from None to Gemini 3.1 Pro (High). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>