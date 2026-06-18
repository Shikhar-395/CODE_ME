#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${JUDGE_DOCKER_IMAGE:-leetcode-judge:latest}"

docker build \
  --file "${SCRIPT_DIR}/judge/Dockerfile" \
  --tag "${IMAGE}" \
  "${SCRIPT_DIR}/judge"

echo
echo "Built ${IMAGE}"
