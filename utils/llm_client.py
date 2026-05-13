"""LLM client — supports both local vLLM and Novita AI (OpenAI-compatible APIs)."""

import json
import os
import time
import datetime
from pathlib import Path

import yaml
from openai import OpenAI

# ── Load config ──
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config.yml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

LOG_PATH = ROOT_DIR / config.get("pipeline", {}).get("log_file", "logs/raw_responses.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Lazy-initialized clients
_local_client = None
_novita_client = None

# Build model config lookup: display_name -> {name, provider}
MODEL_CONFIGS = {}
for m in config.get("models", []):
    if m.get("enabled", False):
        MODEL_CONFIGS[m["display_name"]] = {
            "name": m["name"],
            "provider": m.get("provider", "local"),
        }


def _get_local_client():
    global _local_client
    if _local_client is None:
        vllm_cfg = config.get("vllm", {})
        base_url = vllm_cfg.get("base_url", "http://localhost:8000/v1")
        api_key = vllm_cfg.get("api_key", "not-needed")
        _local_client = OpenAI(base_url=base_url, api_key=api_key)
    return _local_client


def _get_novita_client():
    global _novita_client
    if _novita_client is None:
        novita_cfg = config.get("novita", {})
        base_url = novita_cfg.get("base_url", "https://api.novita.ai/v3/openai")
        api_key = novita_cfg.get("api_key") or os.environ.get("NOVITA_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "Novita API key not found. Set NOVITA_API_KEY environment variable "
                "or add api_key to the novita section in config.yml."
            )
        _novita_client = OpenAI(base_url=base_url, api_key=api_key)
    return _novita_client


def _resolve_model(model: str) -> str:
    """Resolve display_name to model identifier."""
    return MODEL_CONFIGS.get(model, {}).get("name", model)


def get_model_provider(model: str) -> str:
    """Return provider ('local' or 'novita') for a given model display_name."""
    return MODEL_CONFIGS.get(model, {}).get("provider", "local")


def get_enabled_models() -> list[str]:
    """Return display_name list for all enabled models."""
    return list(MODEL_CONFIGS.keys())


def get_local_models() -> list[str]:
    """Return display_name list for enabled local models."""
    return [name for name, cfg in MODEL_CONFIGS.items() if cfg["provider"] == "local"]


def get_novita_models() -> list[str]:
    """Return display_name list for enabled Novita models."""
    return [name for name, cfg in MODEL_CONFIGS.items() if cfg["provider"] == "novita"]


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
    provider = get_model_provider(model)
    resolved_model = _resolve_model(model)
    client = _get_local_client() if provider == "local" else _get_novita_client()

    for attempt in range(max_retries):
        t0 = time.time()
        try:
            response = client.chat.completions.create(
                model=resolved_model,
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
