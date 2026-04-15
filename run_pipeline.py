"""Top-level orchestrator for the behavioral bias pipeline v3.

Ethnicity × SES × Job Application — Paris Tech — Mid-level.

For each model: starts vLLM, runs all requested eval steps, then stops vLLM
before moving to the next model. Steps 1-2 (profile generation/injection) run
once before the per-model loop.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.llm_client import get_enabled_models, _get_client
from utils.vllm_launcher import start_vllm, stop_vllm, is_server_running

ALL_MODELS = get_enabled_models()


def _reset_client():
    """Force the OpenAI client to reconnect (new model on same port)."""
    import utils.llm_client as lc
    lc._client = None


def main():
    parser = argparse.ArgumentParser(
        description="Behavioral Bias Pipeline v3 — Ethnicity × SES × Job Application"
    )
    parser.add_argument(
        "--step",
        choices=["1", "2", "3a", "3b", "3c", "all"],
        default="all",
        help="Pipeline step: 1=generate profiles, 2=inject identities, "
             "3a=single eval, 3b=comparative eval, 3c=IAT, all=full pipeline",
    )
    parser.add_argument(
        "--models",
        type=str,
        default=",".join(ALL_MODELS),
        help="Comma-separated model list (default: enabled models from config.yml)",
    )
    parser.add_argument("--n", type=int, default=50, help="Number of base profiles")
    parser.add_argument(
        "--gen-model",
        type=str,
        default=None,
        help="Model for profile generation (step 1). Default: from config.",
    )
    parser.add_argument(
        "--no-auto-vllm",
        action="store_true",
        help="Disable automatic vLLM start/stop (assume server is already running)",
    )
    parser.add_argument(
        "--vllm-timeout",
        type=int,
        default=300,
        help="Timeout in seconds for vLLM server startup (default: 300)",
    )
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    auto_vllm = not args.no_auto_vllm

    needs_llm = args.step in ("1", "3a", "3b", "3c", "all")

    # ── Steps 1-2: profile generation (no per-model loop) ──

    if args.step in ("1", "all"):
        gen_model = args.gen_model or models[0]
        proc = None
        if auto_vllm:
            proc = start_vllm(gen_model, timeout=args.vllm_timeout)
            _reset_client()

        try:
            from src.generation.generate_profiles import generate_base_profiles
            print("=" * 60)
            print("STEP 1: Generating base profiles")
            print("=" * 60)
            generate_base_profiles(n=args.n, model=gen_model)
        finally:
            if proc:
                stop_vllm(proc)

    if args.step in ("2", "all"):
        from src.generation.generate_profiles import inject_identities
        print("=" * 60)
        print("STEP 2: Injecting identities (3 ethnicity × 2 address)")
        print("=" * 60)
        inject_identities(n=args.n)

    # ── Steps 3a-3c: evaluation (per-model loop) ──

    eval_steps = []
    if args.step in ("3a", "all"):
        eval_steps.append("3a")
    if args.step in ("3b", "all"):
        eval_steps.append("3b")
    if args.step in ("3c", "all"):
        eval_steps.append("3c")

    if eval_steps:
        for model in models:
            proc = None
            if auto_vllm:
                proc = start_vllm(model, timeout=args.vllm_timeout)
                _reset_client()

            try:
                print(f"\n{'#' * 60}")
                print(f"# MODEL: {model}")
                print(f"{'#' * 60}")

                if "3a" in eval_steps:
                    from src.evaluation.run_single import run_single_evaluation
                    print("=" * 60)
                    print(f"STEP 3A: Single evaluation — {model}")
                    print("=" * 60)
                    run_single_evaluation([model])

                if "3b" in eval_steps:
                    from src.evaluation.run_comparative import run_comparative_evaluation
                    print("=" * 60)
                    print(f"STEP 3B: Comparative evaluation — {model}")
                    print("=" * 60)
                    run_comparative_evaluation([model])

                if "3c" in eval_steps:
                    from src.evaluation.run_iat import run_iat
                    print("=" * 60)
                    print(f"STEP 3C: IAT (ethnicity) — {model}")
                    print("=" * 60)
                    run_iat([model], n_iterations=args.n)

            finally:
                if proc:
                    stop_vllm(proc)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
