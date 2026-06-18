#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/leetcode}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

for required_path in \
  "${APP_DIR}/.env" \
  "${APP_DIR}/venv/bin/uvicorn" \
  "${APP_DIR}/venv/bin/python" \
  "${APP_DIR}/deploy/nginx/leetcode.conf"; do
  if [[ ! -e "${required_path}" ]]; then
    echo "Missing required path: ${required_path}" >&2
    exit 1
  fi
done

if ! getent group docker >/dev/null; then
  echo "The docker group does not exist." >&2
  exit 1
fi

if ! id -nG ubuntu | tr ' ' '\n' | grep -qx docker; then
  echo "The ubuntu user is not in the docker group." >&2
  exit 1
fi

apt-get update
apt-get install -y nginx

install -d -o ubuntu -g ubuntu -m 0750 "${APP_DIR}/data"
chown ubuntu:ubuntu "${APP_DIR}/.env"
chmod 0600 "${APP_DIR}/.env"

install -o root -g root -m 0644 \
  "${APP_DIR}/deploy/leetcode-api.service" \
  /etc/systemd/system/leetcode-api.service
install -o root -g root -m 0644 \
  "${APP_DIR}/deploy/leetcode-worker.service" \
  /etc/systemd/system/leetcode-worker.service

install -o root -g root -m 0644 \
  "${APP_DIR}/deploy/nginx/leetcode.conf" \
  /etc/nginx/sites-available/leetcode
ln -sfn /etc/nginx/sites-available/leetcode /etc/nginx/sites-enabled/leetcode
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl daemon-reload
systemctl enable --now redis-server docker nginx
systemctl enable --now leetcode-api leetcode-worker
systemctl restart nginx

systemctl --no-pager --full status nginx leetcode-api leetcode-worker
