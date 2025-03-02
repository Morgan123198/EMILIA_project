#!/bin/bash
# Helper script to set up PYTHONPATH correctly for running the CBT bot

# Get the absolute path of the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Export the PYTHONPATH to include the current directory
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

echo "PYTHONPATH has been set to include: $SCRIPT_DIR"
echo "You can now run the CBT bot with: python test_cbt_bot.py" 