import os
import json
import time
import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI

load_dotenv()

# ── Load config ──
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config.yml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

LOG_PATH = ROOT_DIR / config.get("pipeline", {}).get("log_file", "logs/raw_responses.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Lazy-initialized clients
_anthropic_client = None
_local_client = None

# Build model name mapping: display_name -> HF name (for local models only)
LOCAL_MODEL_MAP = {}
for m in config.get("models", []):
    if m.get("type") != "api" and m.get("enabled", False):
        LOCAL_MODEL_MAP[m["display_name"]] = m["name"]

# Budget guard
_claude_call_count = 0
CLAUDE_CALL_LIMIT = config.get("claude", {}).get("call_limit", 500)


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        key_env = config.get("claude", {}).get("api_key_env", "ANTHROPIC_API_KEY")
        _anthropic_client = Anthropic(api_key=os.environ[key_env])
    return _anthropic_client


def _get_local_client():
    global _local_client
    if _local_client is None:
        vllm_cfg = config.get("vllm", {})
        base_url = vllm_cfg.get("base_url", "http://localhost:8000/v1")
        api_key = vllm_cfg.get("api_key", "not-needed")
        _local_client = OpenAI(base_url=base_url, api_key=api_key)
    return _local_client


def _resolve_local_model(model: str) -> str:
    return LOCAL_MODEL_MAP.get(model, model)


def get_enabled_models() -> list[str]:
    """Return display_name list for all enabled models."""
    return [m["display_name"] for m in config.get("models", []) if m.get("enabled", False)]


def log_raw_response(model: str, system_prompt: str, user_prompt: str,
                     response: str, latency_s: float, error: str = None):
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": model,
        "system_prompt_first_100": system_prompt[:100],
        "user_prompt_first_100": user_prompt[:100],
        "response_length": len(response) if response else 0,
        "response": response,
        "latency_s": round(latency_s, 2),
        "error": error,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def call_llm(model: str, system: str, user: str,
             temperature: float = 0.0, max_tokens: int = 800,
             max_retries: int = 3) -> str:
    global _claude_call_count

    for attempt in range(max_retries):
        t0 = time.time()
        try:
            if "claude" in model.lower():
                _claude_call_count += 1
                if _claude_call_count > CLAUDE_CALL_LIMIT:
                    print(f"[WARNING] Claude API call count reached {_claude_call_count} "
                          f"(limit: {CLAUDE_CALL_LIMIT})")
                client = _get_anthropic_client()
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                text = response.content[0].text
            else:
                local_model = _resolve_local_model(model)
                client = _get_local_client()
                response = client.chat.completions.create(
                    model=local_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = response.choices[0].message.content

            latency = time.time() - t0
            log_raw_response(model, system, user, text, latency)
            return text

        except Exception as e:
            latency = time.time() - t0
            log_raw_response(model, system, user, None, latency, error=str(e))
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

    return ""
