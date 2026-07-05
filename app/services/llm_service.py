import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMService:
    """Direct inference calls using the OpenAI SDK with custom base_url.
    No LiteLLM — each provider is hit directly via its OpenAI-compatible endpoint."""

    # Cache clients per base_url so we reuse TCP connections
    _clients = {}

    @classmethod
    def _get_client(cls, base_url, api_key):
        cache_key = f"{base_url}|{api_key}"
        if cache_key not in cls._clients:
            cls._clients[cache_key] = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
        return cls._clients[cache_key]

    @staticmethod
    def generate(
        model,
        base_url,
        api_key,
        messages,
        temperature=0.7,
        max_tokens=8192
    ):
        client = LLMService._get_client(base_url, api_key)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Direct call failed for '{model}' at {base_url}: {e}")

            # ── Ollama auto-fallback on failure ─────────────────────
            from app.config.agent_config import USE_OLLAMA_FALLBACK, OLLAMA_BASE_URL, OLLAMA_MODEL

            if not USE_OLLAMA_FALLBACK and "localhost" not in base_url:
                logger.warning(f"Attempting Ollama fallback with '{OLLAMA_MODEL}'...")
                try:
                    fallback_client = LLMService._get_client(OLLAMA_BASE_URL, "ollama")
                    response = fallback_client.chat.completions.create(
                        model=OLLAMA_MODEL,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content
                except Exception as fallback_err:
                    logger.error(f"Ollama fallback also failed: {fallback_err}")

            raise

    @staticmethod
    def transcribe_audio(
        file_path: str,
        base_url: str,
        api_key: str,
        model: str = "whisper-large-v3-turbo"
    ):
        """
        Transcribes an audio file using OpenAI-compatible audio endpoint (e.g., Groq Whisper).
        Returns the verbose JSON containing segments and timestamps.
        """
        client = LLMService._get_client(base_url, api_key)
        try:
            with open(file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    file=audio_file,
                    model=model,
                    response_format="verbose_json"
                )
            
            # The python SDK returns a TranscriptionVerbose object. 
            # Convert it to dict for easier processing.
            return response.model_dump()

        except Exception as e:
            logger.error(f"Audio transcription failed for '{model}' at {base_url}: {e}")
            raise
