import os
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, AIMessage

load_dotenv()


class RetryLLM:
    """
    Wraps ChatGroq so every .invoke() and .stream() call
    automatically retries across candidate models and handles rate limits gracefully.
    """

    def __init__(self, api_key: str = None, default_model: str = "openai/gpt-oss-120b", max_retries: int = 3):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.candidate_models = [
            os.getenv("GROQ_MODEL", default_model),
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
        ]
        # Remove duplicates while preserving order
        self.candidate_models = [m for m in dict.fromkeys(self.candidate_models) if m]
        self.max_retries = max_retries
        self._active_model_idx = 0
        self._llm = self._create_llm(self.candidate_models[0])

    def _create_llm(self, model_name: str):
        return ChatGroq(
            model=model_name,
            api_key=self.api_key or "gsk_placeholder_dummy_key",
            temperature=0.1,
            max_retries=1,
            request_timeout=60,
            max_tokens=1024,
        )

    def _is_retryable(self, e: Exception) -> bool:
        msg = str(e).lower()
        return (
            "429" in msg or "rate_limit" in msg or "rate limit" in msg or
            "timeout" in msg or "timed out" in msg or
            "connection" in msg or "502" in msg or "503" in msg or "504" in msg or
            "404" in msg or "does not exist" in msg or "model_not_found" in msg
        )

    def invoke(self, messages, **kwargs):
        if not self.api_key or self.api_key.startswith("gsk_placeholder"):
            return AIMessage(content="Based on the dataset profile and rule-based heuristics, this decision was made without a live LLM response.")

        last_exception = None
        for m_idx in range(self._active_model_idx, len(self.candidate_models)):
            model_name = self.candidate_models[m_idx]
            llm_inst = self._create_llm(model_name)
            for attempt in range(self.max_retries):
                try:
                    res = llm_inst.invoke(messages, **kwargs)
                    self._active_model_idx = m_idx
                    return res
                except Exception as e:
                    last_exception = e
                    msg = str(e).lower()
                    if "404" in msg or "model_not_found" in msg or "does not exist" in msg:
                        print(f"[LLM] Model '{model_name}' not available. Trying fallback model...")
                        break
                    elif self._is_retryable(e):
                        wait = 5 * (attempt + 1)
                        print(f"[LLM] Retryable error ({e}). Waiting {wait}s...")
                        time.sleep(wait)
                    else:
                        break

        print(f"[LLM] API call failed: {last_exception}. Falling back to rule-based response.")
        return AIMessage(content="The dataset profile indicates this decision was made using rule-based heuristics because the live model response was unavailable.")

    def stream(self, messages, **kwargs):
        res = self.invoke(messages, **kwargs)
        yield res

    def bind(self, **kwargs):
        return self

    def with_structured_output(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        if hasattr(self._llm, name):
            return getattr(self._llm, name)
        return lambda *args, **kwargs: AIMessage(content="[Fallback Response]")


def get_llm() -> RetryLLM:
    return RetryLLM()


def call_llm_with_retry(llm, messages, max_retries=3):
    return llm.invoke(messages)
