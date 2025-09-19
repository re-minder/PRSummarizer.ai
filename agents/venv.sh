#!/bin/bash
# Virtual environment activation script for PR Summarizer agents

# Get the project root directory (when executed from coral-server, go up two levels from coral-server/../agents/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Activate the main project virtual environment
source "${PROJECT_ROOT}/venv/bin/activate"

# Change to project root to ensure proper imports
cd "${PROJECT_ROOT}"

# Execute the Python script with unbuffered output
python -u "$1"