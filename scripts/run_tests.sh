#!/bin/bash
set -e
venv/Scripts/python.exe -m pytest tests/ --cov=src --cov-fail-under=80 --tb=short -q
