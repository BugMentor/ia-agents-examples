#!/bin/bash
# Run tests for Memory Agent

cd "$(dirname "$0")/.."

python -m pytest tests/test_agent_memory.py -v --tb=short
