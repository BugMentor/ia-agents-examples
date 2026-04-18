#!/bin/bash
# Run tests for Simple Agent

cd "$(dirname "$0")/.."

python -m pytest tests/test_agent_example.py -v --tb=short
