#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/leetcode}"

cd "${APP_DIR}"

if [[ ! -f .env ]]; then
  echo "${APP_DIR}/.env is missing." >&2
  exit 1
fi

mkdir -p data
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt

venv/bin/alembic upgrade head
venv/bin/python -m unittest discover -v
./docker/build-judge.sh
venv/bin/python -m backend.docker_smoke_test
venv/bin/python -m backend.seed

sudo "${APP_DIR}/deploy/install-services.sh"

echo "Backend bootstrap completed."
