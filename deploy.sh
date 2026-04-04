#!/usr/bin/env bash
# Manual deploy helper (run from Git Bash/WSL/macOS/Linux).
# On the EC2 instance, run: ./deploy.sh local
# From your laptop: ./deploy.sh remote ubuntu@EIP path/to/key.pem
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

usage() {
  echo "Employee Asset Register — deploy helper"
  echo ""
  echo "  $0 local              On EC2: git pull, pip, restart asset-register + nginx"
  echo "  $0 remote <user@host> [identity.pem]   SSH and run the same steps"
  echo ""
  echo "  EC2_SSH_KEY may hold the path to the .pem when the third arg is omitted."
}

run_deploy_on_server() {
  set -euo pipefail
  cd /home/ubuntu/Employee_Asset_Management_Register
  git pull origin main
  source venv/bin/activate
  pip install -r requirements.txt --quiet
  sudo systemctl restart asset-register
  sudo systemctl restart nginx
  sleep 2
  curl -sf "http://127.0.0.1:8000/api/stats" >/dev/null
  echo "Deploy OK ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
}

case "${1:-}" in
  local)
    run_deploy_on_server
    ;;
  remote)
    if [[ -z "${2:-}" ]]; then
      usage
      exit 1
    fi
    HOST="$2"
    KEY="${3:-${EC2_SSH_KEY:-}}"
    SSH=(ssh -o StrictHostKeyChecking=accept-new)
    [[ -n "$KEY" ]] && SSH+=(-i "$KEY")
    "${SSH[@]}" "$HOST" bash -s <<'REMOTE_SCRIPT'
set -euo pipefail
cd /home/ubuntu/Employee_Asset_Management_Register
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
sudo systemctl restart asset-register
sudo systemctl restart nginx
sleep 2
curl -sf "http://127.0.0.1:8000/api/stats" >/dev/null
echo "Deploy OK ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
REMOTE_SCRIPT
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac
