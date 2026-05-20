#!/bin/bash
# Run pipeline with BOTH thinking modes and save results separately

cd "$(dirname "$0")"
source .venv/bin/activate

echo "=========================================="
echo "RUN 1: Qwen3 WITH thinking (default)"
echo "=========================================="
python run_pipeline.py --no-auto-vllm --step all

# Move results so they don't get overwritten
if [ -d "data/results" ]; then
    mv data/results data/results_think
    echo "[SAVED] Results moved to data/results_think/"
fi

echo ""
echo "=========================================="
echo "RUN 2: Qwen3 WITHOUT thinking (--no-think)"
echo "=========================================="
python run_pipeline.py --no-auto-vllm --step all --no-think

if [ -d "data/results" ]; then
    mv data/results data/results_nothink
    echo "[SAVED] Results moved to data/results_nothink/"
fi

echo ""
echo "=========================================="
echo "DONE! Both variants completed."
echo "  - With thinking:    data/results_think/"
echo "  - Without thinking: data/results_nothink/"
echo "=========================================="
