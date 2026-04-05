#!/usr/bin/env bash
# Run on the EC2 instance (as ubuntu) after SSH:  bash deploy.sh
# Pulls latest code, refreshes systemd + nginx + app.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "==> git pull"
git pull origin main

echo "==> systemd unit"
sudo cp "$ROOT/asset-register.service" /etc/systemd/system/asset-register.service
sudo systemctl daemon-reload
sudo systemctl enable asset-register

echo "==> nginx + FastAPI (drops default nginx page, proxies to :8000)"
sudo bash "$ROOT/scripts/ensure-nginx-proxy.sh"

echo "==> Done. Open http://<this-server-public-ip>/ in your browser."
