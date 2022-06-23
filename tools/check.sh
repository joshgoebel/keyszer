#!/usr/bin/env bash
codespell # see .codespellrc
bandit -q --recursive --skip B101 src tests
flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src --count --exit-zero --max-complexity=15 --max-line-length=88 \
                      --show-source --statistics
black --check src tests
isort --check-only --profile black -w 80 .
