# Employee Asset Management Register

STEP 1 project structure scaffold. Say **proceed** for STEP 2.

## Run locally (dev)

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -c "from app.database import init_db; init_db()"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000` and `http://127.0.0.1:8000/docs`.
