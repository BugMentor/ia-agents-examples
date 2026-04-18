@echo off
REM Run tests for Simple Agent

python -m pytest tests\test_agent_example.py -v --tb=short