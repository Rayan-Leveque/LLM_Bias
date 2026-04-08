"""Top-level orchestrator for the behavioral bias pipeline."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.llm_client import get_enabled_models

ALL_MODELS = get_enabled_models()


def main():
    parser = argparse.ArgumentParser(
        description="Behavioral Bias Pipeline v2 — Sexuality × Job Application"
    )
    parser.add_argument(
        "--step",
        choices=["1", "2", "3a", "3b", "3c", "all"],
        default="all",
        help="Pipeline step: 1=generate profiles, 2=inject signals, "
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
        default="claude-sonnet-4-6",
        help="Model for profile generation (step 1+2)",
    )
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]

    if args.step in ("1", "all"):
        from src.generation.generate_profiles import generate_base_profiles
        print("=" * 60)
        print("STEP 1: Generating base profiles")
        print("=" * 60)
        generate_base_profiles(n=args.n, model=args.gen_model)

    if args.step in ("2", "all"):
        from src.generation.generate_profiles import inject_signals
        print("=" * 60)
        print("STEP 2: Injecting signals")
        print("=" * 60)
        inject_signals(n=args.n, model=args.gen_model)

    if args.step in ("3a", "all"):
        from src.evaluation.run_single import run_single_evaluation
        print("=" * 60)
        print("STEP 3A: Single evaluation")
        print("=" * 60)
        run_single_evaluation(models)

    if args.step in ("3b", "all"):
        from src.evaluation.run_comparative import run_comparative_evaluation
        print("=" * 60)
        print("STEP 3B: Comparative evaluation")
        print("=" * 60)
        run_comparative_evaluation(models)

    if args.step in ("3c", "all"):
        from src.evaluation.run_iat import run_iat
        print("=" * 60)
        print("STEP 3C: IAT")
        print("=" * 60)
        run_iat(models, n_iterations=args.n)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
