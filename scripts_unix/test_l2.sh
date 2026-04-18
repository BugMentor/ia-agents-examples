#!/bin/bash
# Run L2 tests only (Service Tests)

cd "$(dirname "$0")/.."

python -m pytest tests/ -v --tb=short -k "test_L2"
