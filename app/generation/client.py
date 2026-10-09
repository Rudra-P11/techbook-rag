import time
import logging
from typing import Optional, Tuple
from openai import OpenAI
from app.config import settings
from app.generation.prompts import SYSTEM_PROMPT, format_user_prompt

logger = logging.getLogger(__name__)


class GenerationClient:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured in .env or environment.")
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                timeout=settings.OPENAI_TIMEOUT_SECONDS,
                max_retries=settings.OPENAI_MAX_RETRIES
            )
        return self._client

    def generate_answer(self, query: str, context: str, model: Optional[str] = None) -> Tuple[str, int]:
        """
        Sends the grounded query and retrieved evidence context to OpenAI.
        Returns:
            (raw_answer_text, latency_ms)
        """
        start_time = time.perf_counter()
        client = self._get_client()

        user_content = format_user_prompt(query, context)
        selected_model = model or self.model

        try:
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=settings.OPENAI_MAX_OUTPUT_TOKENS,
                temperature=0.1
            )
            raw_text = response.choices[0].message.content or ""
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return raw_text, latency_ms

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}", exc_info=True)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            raise RuntimeError(f"Error during LLM answer generation: {str(e)}") from e


generation_client = GenerationClient()
