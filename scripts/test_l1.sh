#!/bin/bash
# Run L1 tests only (Integration Tests)

cd "$(dirname "$0")/.."

python -m pytest tests/ -v --tb=short -k "test_L1"
