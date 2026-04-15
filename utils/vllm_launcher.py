"""vLLM server launcher — start/stop one model at a time."""

import subprocess
import sys
import time
import signal
from pathlib import Path

import yaml
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config.yml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Build full model config lookup: display_name -> model dict
_MODEL_CONFIGS = {}
for m in config.get("models", []):
    _MODEL_CONFIGS[m["display_name"]] = m

VLLM_CFG = config.get("vllm", {})
BASE_URL = VLLM_CFG.get("base_url", "http://localhost:8000/v1")
# Extract host:port from base_url for health check
_base = BASE_URL.rstrip("/v1").rstrip("/")
HEALTH_URL = f"{_base}/health"

# Defaults from config
GPU_MEM_UTIL = VLLM_CFG.get("gpu_memory_utilization", 0.90)
MAX_MODEL_LEN = VLLM_CFG.get("max_model_len", 4096)


def _parse_host_port():
    """Extract host and port from base_url."""
    from urllib.parse import urlparse
    parsed = urlparse(BASE_URL.replace("/v1", ""))
    host = parsed.hostname or "0.0.0.0"
    port = parsed.port or 8000
    return host, port


def start_vllm(model_display_name: str, timeout: int = 300) -> subprocess.Popen:
    """Start a vLLM server for the given model. Returns the Popen handle."""
    mcfg = _MODEL_CONFIGS.get(model_display_name)
    if mcfg is None:
        raise ValueError(f"Unknown model: {model_display_name}. "
                         f"Available: {list(_MODEL_CONFIGS.keys())}")

    hf_name = mcfg["name"]
    tp = mcfg.get("tensor_parallel_size", 1)
    gpu_mem = mcfg.get("gpu_memory_utilization", GPU_MEM_UTIL)
    host, port = _parse_host_port()

    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", hf_name,
        "--tensor-parallel-size", str(tp),
        "--gpu-memory-utilization", str(gpu_mem),
        "--max-model-len", str(MAX_MODEL_LEN),
        "--host", host,
        "--port", str(port),
        "--dtype", "auto",
    ]

    print(f"[vLLM] Starting: {hf_name} (tp={tp}, port={port})")
    print(f"[vLLM] Command: {' '.join(cmd)}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for the server to become healthy
    if not _wait_healthy(proc, timeout):
        stop_vllm(proc)
        raise RuntimeError(
            f"vLLM server for {model_display_name} did not start within {timeout}s"
        )

    print(f"[vLLM] Server ready for {model_display_name}")
    return proc


def _wait_healthy(proc: subprocess.Popen, timeout: int) -> bool:
    """Poll the health endpoint until the server is ready or timeout."""
    deadline = time.time() + timeout
    interval = 5

    while time.time() < deadline:
        # Check if process died
        if proc.poll() is not None:
            # Read remaining output for debugging
            out = proc.stdout.read() if proc.stdout else ""
            print(f"[vLLM] Process exited with code {proc.returncode}")
            if out:
                # Print last 30 lines
                lines = out.strip().split("\n")
                for line in lines[-30:]:
                    print(f"[vLLM]   {line}")
            return False

        try:
            resp = requests.get(HEALTH_URL, timeout=5)
            if resp.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        except requests.Timeout:
            pass

        time.sleep(interval)

    return False


def stop_vllm(proc: subprocess.Popen):
    """Gracefully stop the vLLM server."""
    if proc.poll() is not None:
        print(f"[vLLM] Process already exited (code={proc.returncode})")
        return

    print("[vLLM] Sending SIGTERM...")
    proc.send_signal(signal.SIGTERM)

    try:
        proc.wait(timeout=30)
        print(f"[vLLM] Server stopped (code={proc.returncode})")
    except subprocess.TimeoutExpired:
        print("[vLLM] SIGTERM timeout, sending SIGKILL...")
        proc.kill()
        proc.wait()
        print("[vLLM] Server killed")


def is_server_running() -> bool:
    """Check if a vLLM server is already running on the configured port."""
    try:
        resp = requests.get(HEALTH_URL, timeout=3)
        return resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False
