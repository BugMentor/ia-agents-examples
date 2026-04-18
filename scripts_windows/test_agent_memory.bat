@echo off
REM Run tests for Memory Agent

python -m pytest tests\test_agent_memory.py -v --tb=short