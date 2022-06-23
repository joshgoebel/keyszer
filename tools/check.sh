#!/usr/bin/env bash
SOURCE="src tests"
ONLY_SOURCE="src"
codespell # see .codespellrc
bandit -q --recursive --skip B101 $SOURCE
flake8 $SOURCE --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src --count --exit-zero --max-complexity=15 --max-line-length=88 \
                      --show-source --statistics
black --check $ONLY_SOURCE
isort --check-only --profile black -w 80 .
pytest
safety check | tail -n +15
