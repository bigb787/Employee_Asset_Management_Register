#!/usr/bin/env bash
# Run on the EC2 instance (as ubuntu) after SSH:  bash deploy.sh
# GitHub Actions sets DEPLOY_SKIP_GIT=1 and runs git fetch/reset before this script.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ -z "${DEPLOY_SKIP_GIT:-}" ]]; then
  echo "==> git pull"
  git pull origin main
else
  echo "==> skip git (DEPLOY_SKIP_GIT set — repo already synced)"
fi

if [[ -d "$ROOT/venv" ]]; then
  echo "==> pip install"
  # shellcheck source=/dev/null
  source "$ROOT/venv/bin/activate"
  pip install -r requirements.txt
  echo "==> init_db"
  python -c "from app.database import init_db; init_db()"
else
  echo "WARNING: no venv at $ROOT/venv — run user_data or: python3.11 -m venv venv && pip install -r requirements.txt"
fi

echo "==> systemd unit"
sudo cp "$ROOT/asset-register.service" /etc/systemd/system/asset-register.service
sudo systemctl daemon-reload
sudo systemctl enable asset-register

echo "==> nginx + FastAPI (drops default nginx page, proxies to :8000)"
sudo bash "$ROOT/scripts/ensure-nginx-proxy.sh"

echo "==> Done. Open http://<this-server-public-ip>/ in your browser."
