#!/bin/bash
# Run L3 tests only (End-to-End Tests)

cd "$(dirname "$0")/.."

python -m pytest tests/ -v --tb=short -k "test_L3"
