# WSL Ubuntu PostgreSQL Setup

Use this when FastAPI runs on Windows and PostgreSQL runs inside WSL Ubuntu.

## 1. Start PostgreSQL In WSL

Open Ubuntu/WSL and run:

```bash
sudo service postgresql start
sudo service postgresql status
```

## 2. Create App User And Database

In Ubuntu/WSL:

```bash
sudo -u postgres psql
```

Then run:

```sql
CREATE USER analyzer WITH PASSWORD 'analyzer';
CREATE DATABASE analyzer OWNER analyzer;
GRANT ALL PRIVILEGES ON DATABASE analyzer TO analyzer;
\q
```

If the user/database already exists, use:

```sql
ALTER USER analyzer WITH PASSWORD 'analyzer';
```

## 3. Confirm Windows Can Reach WSL PostgreSQL

Most WSL2 installs forward `localhost` automatically. From Windows PowerShell:

```powershell
Test-NetConnection localhost -Port 5432
```

If `TcpTestSucceeded` is `True`, keep this in `.env`:

```text
DATABASE_URL=postgresql+psycopg://analyzer:analyzer@localhost:5432/analyzer?sslmode=disable
```

## 4. If Localhost Does Not Work

Find the WSL IP from Ubuntu:

```bash
hostname -I
```

Use the first IP address in `.env`, for example:

```text
DATABASE_URL=postgresql+psycopg://analyzer:analyzer@172.25.144.1:5432/analyzer?sslmode=disable
```

Then make PostgreSQL listen beyond WSL localhost. In Ubuntu:

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Set:

```text
listen_addresses = '*'
```

Edit client access:

```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Add a line, replacing `172.25.144.1/32` with your Windows/WSL network range if needed:

```text
host    analyzer    analyzer    0.0.0.0/0    scram-sha-256
```

Restart PostgreSQL:

```bash
sudo service postgresql restart
```

## 5. Run The App From Windows

In PowerShell:

```powershell
cd C:\Users\Lenovo\Documents\Codex\2026-05-17\files-mentioned-by-the-user-ai\ai-document-analyzer
.\.venv-py312\Scripts\Activate.ps1
python -c "from backend.db.session import init_db; init_db(); print('database connected and tables created')"
python run_dev.py
```

Open:

```text
http://127.0.0.1:8000
```
