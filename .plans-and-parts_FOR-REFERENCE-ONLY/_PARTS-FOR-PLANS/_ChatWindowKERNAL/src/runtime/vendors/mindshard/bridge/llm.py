"""
bridge.llm — LLM backend abstraction.

Supports:
  - Ollama (local inference, default)
  - Echo (returns prompt back — for testing without an LLM)

The bridge is a TOOL — it sends a prompt, gets text back.
It does NOT decide what to send. The agent shell decides.

Usage::

    from bridge.llm import OllamaBridge, EchoBridge

    llm = OllamaBridge(model="mistral")
    response = llm.generate("Explain this code:\\n```python\\nprint('hi')\\n```")

    # For testing without a live LLM:
    llm = EchoBridge()
    response = llm.generate("anything")  # returns canned response
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Response type ────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    """What comes back from a generation call."""
    text: str
    model: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error


# ── Abstract bridge ──────────────────────────────────────────────────

class LLMBridge(ABC):
    """Abstract base for LLM backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Send a prompt, get text back."""
        ...

    @abstractmethod
    def name(self) -> str:
        ...


# ── Ollama bridge ────────────────────────────────────────────────────

class OllamaBridge(LLMBridge):
    """
    Local inference via Ollama's HTTP API.

    Requires Ollama running locally (default: http://localhost:11434).
    Works with any model Ollama has pulled: mistral, llama3, codellama,
    deepseek-coder, phi3, etc.

    Features:
      - Queries model's actual context window on first use
      - Estimates prompt tokens and truncates context to fit
      - Streams responses to avoid HTTP timeout on long generations
      - Exposes context_length for callers that need to budget tokens
    """

    # Rough chars-per-token for budget estimation.
    # Most tokenizers average 3–4 chars/token; 3.5 is conservative.
    _CHARS_PER_TOKEN = 3.5

    def __init__(
        self,
        model: str = "mistral",
        base_url: str = "http://localhost:11434",
        timeout: float = 300.0,
        context_reserve: float = 0.25,
    ) -> None:
        """
        Args:
            model:           Ollama model name.
            base_url:        Ollama server URL.
            timeout:         HTTP timeout (seconds). Raised to 300s for streaming.
            context_reserve: Fraction of context window reserved for the response.
                             0.25 = 25% for output, 75% for prompt.
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._context_reserve = context_reserve
        self._context_length: Optional[int] = None  # fetched lazily

    def name(self) -> str:
        return f"ollama/{self._model}"

    # ── Context window discovery ─────────────────────────────────────

    def context_length(self) -> int:
        """
        Return the model's context window in tokens.
        Queries Ollama /api/show on first call, then caches.
        Falls back to 2048 if the API doesn't report it.
        """
        if self._context_length is not None:
            return self._context_length

        import urllib.request
        try:
            url = f"{self._base_url}/api/show"
            payload = json.dumps({"name": self._model}).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            # Ollama returns model info with parameters or model_info
            params = body.get("model_info", {})
            # Try common keys for context length
            ctx = (
                params.get("context_length")
                or params.get("llama.context_length")
                or params.get("num_ctx")
            )
            # Also check the modelfile parameters string
            if not ctx:
                param_str = body.get("parameters", "")
                for line in param_str.split("\n"):
                    if "num_ctx" in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            try:
                                ctx = int(parts[-1])
                            except ValueError:
                                pass

            self._context_length = int(ctx) if ctx else 2048
            logger.info(
                "Model %s context window: %d tokens",
                self._model, self._context_length,
            )
        except Exception as exc:
            logger.warning(
                "Could not query context length for %s: %s (defaulting to 2048)",
                self._model, exc,
            )
            self._context_length = 2048

        return self._context_length

    def max_prompt_tokens(self) -> int:
        """Max tokens available for the prompt (context minus response reserve)."""
        return int(self.context_length() * (1.0 - self._context_reserve))

    def estimate_tokens(self, text: str) -> int:
        """Rough token count from character length."""
        return max(1, int(len(text) / self._CHARS_PER_TOKEN))

    def fits_in_context(self, prompt: str, system: str = "") -> bool:
        """Check whether a prompt fits within the model's context budget."""
        total = self.estimate_tokens(prompt) + self.estimate_tokens(system)
        return total <= self.max_prompt_tokens()

    # ── Generation ───────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """
        Call Ollama /api/generate with streaming.

        Streams the response token-by-token to avoid HTTP timeout,
        then assembles the full text. If the prompt exceeds the model's
        context window, returns an error instead of sending garbage.
        """
        import urllib.request
        import urllib.error

        # ── Context budget check ─────────────────────────────────
        prompt_tokens = self.estimate_tokens(prompt) + self.estimate_tokens(system)
        ctx_limit = self.context_length()
        max_prompt = self.max_prompt_tokens()

        if prompt_tokens > max_prompt:
            return LLMResponse(
                text="",
                model=self._model,
                error=(
                    f"Prompt too large: ~{prompt_tokens} tokens "
                    f"exceeds budget of {max_prompt} "
                    f"(model context: {ctx_limit}). "
                    f"Reduce memory context or shorten the prompt."
                ),
            )

        # Cap response tokens to remaining space
        remaining = ctx_limit - prompt_tokens
        effective_max = min(max_tokens, remaining)

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": effective_max,
            },
        }
        if system:
            payload["system"] = system
        if stop:
            payload["options"]["stop"] = stop

        url = f"{self._base_url}/api/generate"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
        )

        t0 = time.time()
        try:
            # ── Stream response ──────────────────────────────────
            chunks: List[str] = []
            metadata: Dict[str, Any] = {}

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token = obj.get("response", "")
                    if token:
                        chunks.append(token)

                    # Last message carries the full stats
                    if obj.get("done", False):
                        metadata = {
                            "total_duration": obj.get("total_duration"),
                            "load_duration": obj.get("load_duration"),
                            "prompt_eval_count": obj.get("prompt_eval_count"),
                            "eval_count": obj.get("eval_count"),
                            "context_length": ctx_limit,
                            "prompt_tokens_est": prompt_tokens,
                        }

            latency = (time.time() - t0) * 1000
            full_text = "".join(chunks)

            return LLMResponse(
                text=full_text,
                model=self._model,
                tokens_used=metadata.get("eval_count", len(chunks)),
                latency_ms=latency,
                metadata=metadata,
            )

        except urllib.error.URLError as exc:
            latency = (time.time() - t0) * 1000
            return LLMResponse(
                text="",
                model=self._model,
                latency_ms=latency,
                error=f"Ollama connection failed: {exc}",
            )
        except Exception as exc:
            return LLMResponse(
                text="",
                model=self._model,
                error=f"Ollama error: {exc}",
            )

    def list_models(self) -> List[str]:
        """Query Ollama for available models."""
        import urllib.request
        try:
            url = f"{self._base_url}/api/tags"
            with urllib.request.urlopen(url, timeout=5) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return [m["name"] for m in body.get("models", [])]
        except Exception:
            return []

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is pulled."""
        models = self.list_models()
        return any(self._model in m for m in models)


# ── Echo bridge (testing) ────────────────────────────────────────────

class EchoBridge(LLMBridge):
    """
    Returns structured canned responses for testing the agent loop
    without a live LLM. Matches the exact prompt patterns emitted by
    each loop phase (plan, act, observe, reflect, react, refine) and
    returns differentiated, plausible structured output.
    """

    def __init__(self, latency_ms: float = 5.0) -> None:
        self._latency = latency_ms
        self._call_count = 0
        self._eval_count = 0  # tracks iterative refinement evaluations

    def name(self) -> str:
        return "echo/test"

    def _parse_step_number(self, prompt: str) -> int:
        """Extract STEP N/M from an ACT prompt, or 0 if not found."""
        import re
        m = re.search(r"step\s+(\d+)/\d+", prompt, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        self._call_count += 1
        p = prompt.lower()

        # ── PlanActObserve: PLAN phase ──────────────────────────────
        if "decompose" in p and "task" in p:
            text = json.dumps({
                "plan": [
                    {"step": 1, "action": "analyze", "description": "Analyze requirements and edge cases"},
                    {"step": 2, "action": "implement", "description": "Write the core implementation"},
                    {"step": 3, "action": "test", "description": "Write and run tests"},
                ],
                "reasoning": "Decomposed into analysis, implementation, and verification phases.",
            })

        # ── PlanActObserve: ACT phase (step-aware) ──────────────────
        elif "execute this step" in p:
            step_n = self._parse_step_number(p)
            if step_n == 1:
                text = json.dumps({
                    "code": "",
                    "language": "python",
                    "explanation": "Identified key requirements: input validation, "
                                   "error handling, and clean output formatting.",
                    "output": "Requirements analysis complete. Key constraints: "
                              "handle edge cases (empty input, special chars), "
                              "return clear error messages, maintain O(n) complexity.",
                })
            elif step_n == 2:
                text = json.dumps({
                    "code": (
                        "def process(data: str) -> str:\n"
                        "    \"\"\"Core implementation from MindSHARD agent.\"\"\"\n"
                        "    if not data or not data.strip():\n"
                        "        raise ValueError('Input cannot be empty')\n"
                        "    tokens = data.strip().split()\n"
                        "    result = ' '.join(t.capitalize() for t in tokens)\n"
                        "    return result\n"
                    ),
                    "language": "python",
                    "explanation": "Implemented core logic with input validation and edge case handling.",
                    "output": "",
                })
            elif step_n == 3:
                text = json.dumps({
                    "code": (
                        "import pytest\n\n"
                        "def test_basic():\n"
                        "    assert process('hello world') == 'Hello World'\n\n"
                        "def test_empty_raises():\n"
                        "    with pytest.raises(ValueError):\n"
                        "        process('')\n\n"
                        "def test_whitespace():\n"
                        "    assert process('  foo  bar  ') == 'Foo Bar'\n\n"
                        "# All 3 tests passed.\n"
                    ),
                    "language": "python",
                    "explanation": "Test suite covers happy path, empty input, and whitespace edge cases.",
                    "output": "3 tests passed.",
                })
            else:
                text = json.dumps({
                    "code": f"# Step {step_n} implementation\npass",
                    "language": "python",
                    "explanation": f"Executed step {step_n}.",
                    "output": f"Step {step_n} complete.",
                })

        # ── PlanActObserve: OBSERVE phase ───────────────────────────
        elif "evaluate this result" in p:
            text = json.dumps({
                "evaluation": "Step completed successfully. Output meets requirements.",
                "issues": [],
                "suggestions": [],
                "confidence": 0.88,
                "should_continue": True,
            })

        # ── PlanActObserve: REFLECT phase ───────────────────────────
        elif "reflect on the task" in p:
            text = json.dumps({
                "reflection": "Task completed through a clean plan→act→observe cycle. "
                              "The decomposition into analysis, implementation, and testing "
                              "phases kept each step focused.",
                "lessons": [
                    "Breaking tasks into analysis-first helps catch edge cases early",
                    "Writing tests as a separate step ensures coverage",
                ],
                "should_remember": True,
                "memory_text": "Learned: decompose tasks into analyze→implement→test phases "
                               "for cleaner execution.",
            })

        # ── ReactLoop: single-step reason+act ───────────────────────
        elif "what should you do next" in p:
            if self._call_count <= 2:
                text = json.dumps({
                    "thought": "I need to understand the task requirements first.",
                    "action": "Analyze the request and identify constraints.",
                    "result": "Key requirements identified. Ready to implement.",
                    "finished": False,
                })
            elif self._call_count <= 4:
                text = json.dumps({
                    "thought": "Requirements are clear. Time to implement.",
                    "action": "Write the solution.",
                    "result": "def solve(x): return x * 2  # core logic",
                    "finished": False,
                })
            else:
                text = json.dumps({
                    "thought": "Implementation is complete and verified.",
                    "action": "Finalize.",
                    "result": "Task complete. Solution verified and working.",
                    "finished": True,
                })

        # ── IterativeRefinement: initial implementation ─────────────
        elif "implement this task" in p:
            text = json.dumps({
                "code": "def solve(data):\n    return [x for x in data if x]\n",
                "language": "python",
                "explanation": "Initial draft: basic filter implementation.",
            })

        # ── IterativeRefinement: evaluate implementation ────────────
        elif "evaluate this implementation" in p:
            self._eval_count += 1
            if self._eval_count == 1:
                text = json.dumps({
                    "evaluation": "Functional but could be more robust.",
                    "issues": ["No type hints", "Missing docstring"],
                    "suggestions": ["Add type annotations", "Add docstring"],
                    "confidence": 0.65,
                })
            else:
                # After refinement, confidence exceeds threshold → loop exits
                text = json.dumps({
                    "evaluation": "Refined version looks solid. Type hints and docstring added.",
                    "issues": [],
                    "suggestions": [],
                    "confidence": 0.92,
                })

        # ── IterativeRefinement: refine ─────────────────────────────
        elif "refine this implementation" in p:
            text = json.dumps({
                "code": (
                    "from typing import List, Any\n\n"
                    "def solve(data: List[Any]) -> List[Any]:\n"
                    "    \"\"\"Filter falsy values from a list.\"\"\"\n"
                    "    return [x for x in data if x]\n"
                ),
                "changes": "Added type hints and docstring.",
            })

        # ── Chat fallback ───────────────────────────────────────────
        else:
            text = json.dumps({
                "response": f"Processed request (call #{self._call_count})",
                "prompt_length": len(prompt),
            })

        return LLMResponse(
            text=text,
            model="echo/test",
            tokens_used=len(text.split()),
            latency_ms=self._latency,
        )
