# AI-Powered Personalized Learning Platform

A dynamic, intelligent learning platform designed to generate personalized curriculums, assess knowledge gaps, and provide persistent, context-aware AI coaching.

## 🚀 Features

*   **Intelligent Onboarding & Diagnostics**: Assesses your prior knowledge via a dynamic diagnostic test to tailor your starting point.
*   **AI Curriculum Generation**: Builds highly detailed, week-by-week learning roadmaps customized to your specific goals and format preferences (Video, Text, Hands-on).
*   **Persistent Knowledge Graph Memory**: Powered by [Cognee](https://github.com/topoteretes/cognee), the backend builds a deep knowledge graph of your learning profile, quiz scores, and weak areas. Your AI coach *remembers* your entire journey.
*   **Multi-Agent Architecture**: 
    *   **Roadmap Agent** (Powered by Qwen 3.7 Plus via Fireworks AI) for deep reasoning and curriculum building.
    *   **Coach & Diagnostic Agents** (Powered by Gemma 31B via Cerebras) for lightning-fast, context-aware mentoring.
    *   **Background Agents** (Llama 3.1 8B via Groq/Fireworks) for highly cost-efficient data formatting and memory management.
*   **Interactive Dashboard**: Dynamically syncs with your AI-generated curriculum to show "Today's Plan" and track progress.

## 🛠️ Technology Stack

### Frontend
*   React (Vite)
*   Standard CSS for UI/UX
*   Lucide React for iconography

### Backend
*   **Framework**: FastAPI (Python 3.12)
*   **Memory / RAG**: Cognee (Graph RAG framework)
*   **LLM Orchestration**: LiteLLM and Instructor for strict JSON structured outputs
*   **Inference Providers**: Fireworks AI, Cerebras, Groq, Cloudflare (Optimized for cost and speed)

## ⚙️ Setup & Installation

### Prerequisites
*   Node.js & npm
*   Python 3.12+
*   API keys for the integrated LLM providers (e.g., Fireworks AI, Cerebras)

### Backend Setup
1.  Navigate to the project root and create a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/Scripts/activate  # On Windows
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up your `.env` file in the root directory:
    ```env
    FIREWORKS_API_KEY=your_key
    CEREBRAS_API_KEY=your_key
    GROQ_API_KEY=your_key
    CLOUDFLARE_API_KEY=your_key
    ```
4.  Start the FastAPI backend:
    ```bash
    uvicorn app.main:app --reload
    ```

### Frontend Setup
1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the Vite development server:
    ```bash
    npm run dev
    ```

## 🧠 Architecture Overview

The system aggressively optimizes AI token costs while maximizing reasoning capability:
*   **Heavy planning tasks** (like generating the initial roadmap) are routed to highly capable models like Qwen 3.7 Plus.
*   **Conversational tasks** are routed through incredibly fast inference engines like Cerebras.
*   **Background data structuring** (cleaning memory arrays, formatting strings) is handled by blazing-fast, nearly free 8B parameter models.
*   **Cognee** intercepts all conversational turns and quiz results, injecting them into a local network graph. When you chat with the Coach Agent, it queries this graph to retrieve a highly specific context payload so the AI never repeats itself and always knows exactly where you are in your syllabus.

## 📝 License
MIT License
