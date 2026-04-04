#!/bin/bash
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/stats || echo "000")
LOG=/var/log/asset-health.log
if [ "$CODE" != "200" ]; then
  echo "[$(date)] UNHEALTHY HTTP $CODE restarting" >> "$LOG"
  sudo systemctl restart asset-register
  sleep 5
  CODE2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/stats || echo "000")
  echo "[$(date)] After restart HTTP $CODE2" >> "$LOG"
else
  echo "[$(date)] Healthy HTTP $CODE" >> "$LOG"
fi
