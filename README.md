# Naira Expense Tracker (Web)

A web frontend + Flask API for the expense tracker. It reads and writes the
same `expenses.csv` (`date,time,description,amount`) as the command-line
`expenses.py`, so both can be used on the same file.

## Project layout

```
expense-web/
├── app.py            # Flask API + serves the frontend
├── static/index.html # the frontend (single page, no build step)
├── expenses.py       # the command-line version (same CSV)
├── requirements.txt
├── Procfile          # start command for Railway / Render / Heroku
└── .gitignore
```

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

The CLI still works on the same file:

```bash
python expenses.py daily
python expenses.py weekly
```

## Deploy on Railway

1. Push this folder to a GitHub repo.
2. In Railway: **New Project → Deploy from GitHub repo**. Railway detects
   Python and uses the `Procfile`.
3. **Important – keep your data:** Railway's disk is wiped on every redeploy.
   Add a **Volume** to the service, mount it at `/data`, and set the variable:
   `EXPENSES_FILE=/data/expenses.csv`
4. Optional: `APP_TIMEZONE=Africa/Lagos` (this is already the default), so
   expenses are stamped in Lagos time even though the server runs in UTC.
5. Generate a domain under **Settings → Networking**.

The same steps work on Render (add a persistent disk) or any VPS:
`gunicorn app:app --bind 0.0.0.0:8000`.

## API

| Method | Path                    | Purpose                               |
|--------|-------------------------|---------------------------------------|
| GET    | `/api/expenses`         | All expenses as JSON                  |
| POST   | `/api/expenses`         | `{ "description": "...", "amount": 2500 }` – stamps date/time on the server |
| DELETE | `/api/expenses/<id>`    | Delete one expense                    |
| GET    | `/api/export`           | Download the CSV                      |
| GET    | `/api/health`           | Health check                          |

## Note

There is no login. Anyone with the link can add or delete expenses, so keep
the URL private or put it behind authentication before sharing it.
Run with one gunicorn worker (as in the Procfile) because the data is a single CSV file.
