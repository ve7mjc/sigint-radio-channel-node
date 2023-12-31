#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR"

source $SCRIPT_DIR/venv/bin/activate

# Check if at least one argument is provided
if [ $# -eq 0 ]; then
    echo "Error: No arguments supplied."
    echo "Usage: $0 <config_file>"
    exit 1
fi

${SCRIPT_DIR}/venv/bin/python3 -m app.main --config $1
