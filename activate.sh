#!/bin/bash
# Activate the Council of Elders environment
# Usage: source activate.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"

echo "Council of Elders activated!"
echo "Run 'council --help' to see available commands."
echo "Run 'council elders' to see the council members."
