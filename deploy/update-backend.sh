#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/leetcode}"

cd "${APP_DIR}"
git pull --ff-only origin master

venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m unittest discover -v
./docker/build-judge.sh
venv/bin/python -m backend.docker_smoke_test
venv/bin/python -m backend.seed

sudo systemctl restart leetcode-api leetcode-worker
sudo systemctl is-active --quiet leetcode-api
sudo systemctl is-active --quiet leetcode-worker

echo "Backend updated to $(git rev-parse --short HEAD)."
