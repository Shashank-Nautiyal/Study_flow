# Platform Architecture & Agents

This document details the inner workings of the personalized learning platform, specifically focusing on the Multi-Agent architecture and the resource extraction pipelines (like the YouTube Playlist Extractor).

---

## The Multi-Agent System

Instead of relying on a single monolithic LLM prompt, this platform uses a **Multi-Agent Architecture**. Different specialized AI "Agents" are assigned to handle specific tasks. This drastically improves speed, lowers API costs, and increases the quality of the output.

### 1. The Roadmap Agent (The Architect)
*   **Role:** Builds the core curriculum and syllabus.
*   **Model:** Qwen 3.7 Plus (via Fireworks AI).
*   **How it works:** When you finish the onboarding diagnostic, this agent takes your learning goal, available time, format preferences, and diagnostic scores. It performs deep reasoning to generate a structured, multi-week JSON curriculum. Because this requires high intelligence, it uses the most powerful (and token-heavy) model in the stack.

### 2. The Coach Agent (The Mentor)
*   **Role:** Provides interactive, contextual chat assistance.
*   **Model:** Gemma 31B (via Cerebras).
*   **How it works:** Whenever you send a message, the Coach first queries the **Cognee Knowledge Graph**. It retrieves your *entire* context—weak areas, current week in the roadmap, past quiz scores, and recent chat history. It injects this into its system prompt so it never repeats itself and always gives highly personalized advice. It runs on Cerebras to guarantee lightning-fast response times.

### 3. The Diagnostic & Quiz Agents (The Evaluators)
*   **Role:** Generates dynamic multiple-choice questions.
*   **Models:** Gemma 31B (Cerebras) and Llama 4 Scout 17B (Cloudflare).
*   **How it works:** These agents take a specific topic (or a newly uploaded resource) and generate JSON-formatted quizzes to test your comprehension. Cloudflare and Cerebras are used because they are free/generous and excellent at fast JSON output.

### 4. The Background Agents (Insight, Portfolio, Memory Manager)
*   **Role:** Handles invisible background tasks.
*   **Models:** Llama 3.1 8B Instruct (via Groq / Fireworks AI).
*   **How it works:** These are tiny, blazing-fast, highly cost-efficient models. When you chat or complete a task, the Memory Manager Agent quietly runs in the background to clean up strings, extract entities, and format data for the Knowledge Graph. By using 8B models here, the platform saves thousands of expensive tokens.

---

## 🧠 Cognee Knowledge Graph (The Memory)

The platform uses **Cognee**, a Graph RAG (Retrieval-Augmented Generation) framework, to replace traditional vector databases.

When you upload a resource or chat with the Coach:
1.  **Extraction:** Cognee breaks the text into chunks.
2.  **Cognify:** It passes these chunks to the LLM (powered by Cerebras `zai-glm-4.7`) to extract "Nodes" (e.g., "Python", "Data Structures") and "Edges" (relationships).
3.  **Graph Storage:** It stores these interconnected nodes in a local graph database.
4.  **Retrieval:** When the Coach needs context, it traverses this graph to find exactly what you know and how it relates to your current goal, rather than just doing a dumb keyword search.

---

## 🎥 YouTube & Playlist Extractor Workflow

The platform features a highly robust YouTube processing engine (`youtube_service.py`) capable of digesting entire playlists or multi-hour lectures.

### 1. Playlist Flat-Fetching
When a YouTube Playlist URL is submitted, the backend uses `yt-dlp` in `extract_flat` mode. This instantly fetches the metadata (titles, durations, IDs) for all videos in the playlist *without* downloading them, returning the list to the UI in milliseconds.

### 2. Audio Extraction & Downsampling
When a specific video is selected for processing:
1.  `yt-dlp` downloads the lowest-quality audio stream to save bandwidth and speed up the process.
2.  The audio is converted to a lightweight `.mp3`.

### 3. Smart Chunking (Bypassing API Limits)
Most transcription APIs (like OpenAI's Whisper) have a strict **25MB file size limit**.
If a lecture is over 45 minutes long, the file will exceed this limit.
*   The `youtube_service.py` uses `pydub.AudioSegment` to automatically detect the length of the audio.
*   If the audio is too large, it seamlessly slices it into exactly 45-minute chunks.

### 4. Parallel Transcription & Summarization
1.  The chunks are sent to the Whisper API for transcription.
2.  The resulting text transcripts are combined.
3.  The combined transcript is sent to the **Resource Agent**, which generates a structured summary, extracts key concepts, and integrates it into your learning roadmap!
