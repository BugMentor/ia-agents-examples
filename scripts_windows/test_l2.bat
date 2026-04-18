@echo off
REM Run L2 tests only (Service Tests)

python -m pytest tests\ -v --tb=short -k "test_L2"