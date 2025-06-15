# Infrastructure Deployment Instructions

## Step 1: Deploy Infrastructure

```bash
chmod +x deploy-infrastructure.sh
./deploy-infrastructure.sh
```

## Step 2: Set Up Database

```bash
psql -h your-postgresql-server.postgres.database.azure.com -U pgadmin -d customer_matching -f sql/01-setup-pgvector.sql
```

## Step 3: Configure & Start Application

```bash
cd app
pip install -r requirements.txt
# Edit .env with your OpenAI API key
python main.py
```
