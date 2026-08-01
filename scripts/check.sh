#!/bin/sh
set -eu
ruff check .
ruff format --check .
mypy
python -m unittest discover -s tests -p 'test_*.py' -v
