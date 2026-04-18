#!/bin/bash
# Run all tests

cd "$(dirname "$0")/.."

python -m pytest tests/ -v --tb=short
