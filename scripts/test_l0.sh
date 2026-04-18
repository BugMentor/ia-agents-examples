#!/bin/bash
# Run L0 tests only (Unit Tests)

cd "$(dirname "$0")/.."

python -m pytest tests/ -v --tb=short -k "test_L0"
