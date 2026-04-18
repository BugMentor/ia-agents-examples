@echo off
REM Run L1 tests only (Integration Tests)

python -m pytest tests\ -v --tb=short -k "test_L1"