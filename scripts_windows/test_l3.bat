@echo off
REM Run L3 tests only (End-to-End Tests)

python -m pytest tests\ -v --tb=short -k "test_L3"