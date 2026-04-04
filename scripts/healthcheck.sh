#!/usr/bin/env bash
# STEP 1 scaffold — curl local health endpoint when app is running.
set -euo pipefail
curl -sf "http://127.0.0.1:8000/health" >/dev/null && echo "ok" || echo "fail"
