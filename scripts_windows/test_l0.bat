@echo off
REM Run L0 tests only (Unit Tests)

python -m pytest tests\ -v --tb=short -k "test_L0"