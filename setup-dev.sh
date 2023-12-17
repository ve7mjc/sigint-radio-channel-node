#!/bin/bash

# Get the Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MIN_VERSION="3.10"

# Compare the Python version
if [[ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]]; then
    echo "Error: Python version must be $MIN_VERSION or greater. You have Python $PYTHON_VERSION."
    exit 1
fi

echo "Python version is ${PYTHON_VERSION}"

python3 -m venv venv
venv/bin/pip install -r requirements.txt
