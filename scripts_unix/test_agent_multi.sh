#!/bin/bash
# Run tests for Multi-Agent System

cd "$(dirname "$0")/.."

python -m pytest tests/test_agent_multi.py -v --tb=short
