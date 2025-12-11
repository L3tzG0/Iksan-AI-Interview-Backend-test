#!/bin/bash

# This script is the entrypoint for the Railway Worker Service.
# It prevents Railway's auto-detection from overriding the custom start command.

echo "Starting Interview Generation Worker..."
# Execute the main worker script
python scripts/worker.py