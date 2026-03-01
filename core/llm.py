import os
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage

load_dotenv()


class RetryLLM:
    """
    Wraps ChatGroq so every .invoke() and .stream() call
    automatically retries on 429 rate limit errors.
    No changes needed in any agent file.
    """

    def __init__(self, llm, max_retries: int = 4):
        self._llm        = llm
        self.max_retries = max_retries

    def _is_rate_limit(self, e: Exception) -> bool:
        msg = str(e).lower()
        return "429" in msg or "rate_limit" in msg or "rate limit" in msg

    def _is_retryable(self, e: Exception) -> bool:
        msg = str(e).lower()
        return (
            "429" in msg or "rate_limit" in msg or "rate limit" in msg or
            "timeout" in msg or "timed out" in msg or
            "connection" in msg or "502" in msg or "503" in msg or "504" in msg
        )

    def invoke(self, messages, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return self._llm.invoke(messages, **kwargs)
            except Exception as e:
                if self._is_retryable(e):
                    is_rate = self._is_rate_limit(e)
                    wait    = 30 * (attempt + 1) if is_rate else 10 * (attempt + 1)
                    reason  = "Rate limit" if is_rate else "Timeout/connection error"
                    print(f"[LLM] {reason} (attempt {attempt+1}/{self.max_retries}) "
                          f"— waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    raise   # non-retryable errors raised immediately
        raise Exception(
            f"[LLM] Failed after {self.max_retries} retries. "
            "Check your API key and network connection."
        )

    def stream(self, messages, **kwargs):
        for attempt in range(self.max_retries):
            try:
                yield from self._llm.stream(messages, **kwargs)
                return
            except Exception as e:
                if self._is_rate_limit(e):
                    wait = 30 * (attempt + 1)
                    print(f"[LLM] Rate limit hit on stream (attempt {attempt+1}/{self.max_retries}) "
                          f"— waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise
        raise Exception(f"[LLM] Rate limit persists after {self.max_retries} retries.")

    def bind(self, **kwargs):
        """Pass-through for agents that call llm.bind(tools=...)"""
        return RetryLLM(self._llm.bind(**kwargs), self.max_retries)

    def with_structured_output(self, *args, **kwargs):
        """Pass-through for structured output."""
        return RetryLLM(self._llm.with_structured_output(*args, **kwargs), self.max_retries)

    def __getattr__(self, name):
        """Fallback — forward any other attribute to the underlying LLM."""
        return getattr(self._llm, name)


def get_llm() -> RetryLLM:
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1,
        max_retries=1,       # let RetryLLM handle retries, not ChatGroq
        request_timeout=60,
        max_tokens=1024,  # 60s timeout — prevents infinite hang
    )
    return RetryLLM(llm, max_retries=4)


# Keep this for backwards compatibility if anything imports it directly
def call_llm_with_retry(llm, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                wait = 30 * (attempt + 1)
                print(f"[LLM] Rate limit hit, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("LLM rate limit: max retries exceeded")