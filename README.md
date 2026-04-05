# Employee Asset Management Register

## See the dashboard you asked for (UI)

The layout is in **`templates/index.html`**: left sidebar (Employee Assets, Internal / External Applications, Admin Assets), top bar with **ISO 27001 ✓**, **+ Add Asset**, **↓ Export All**.

### Option A — On your PC (fastest)

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -c "from app.database import init_db; init_db()"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **`http://127.0.0.1:8000/`** in your browser — you should see that UI (not the nginx welcome page). API docs: **`http://127.0.0.1:8000/docs`**.

### Option B — On EC2 (if you only see “Welcome to nginx”)

1. SSH in: `ssh -i YOUR_KEY.pem ubuntu@YOUR_PUBLIC_IP`
2. Run **one** script (pulls latest + fixes nginx + restarts app):

```bash
cd /home/ubuntu/Employee_Asset_Management_Register
git pull origin main
bash scripts/apply-dashboard-on-server.sh
```

3. In the browser open **`http://YOUR_PUBLIC_IP/`** (hard refresh or incognito if it looked cached).

If the script errors, check: `sudo journalctl -u asset-register -n 50 --no-pager`

### GitHub Actions auto-deploy

Set repo secrets **`DEPLOY_HOST`** and **`SSH_PRIVATE_KEY`** — each push to **`main`** runs deploy (see `.github/workflows/deploy-ec2.yml`).
