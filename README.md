# Telegram Stock Query Assistant

This project is a cloud-ready Telegram chatbot for stock lookup and watchlist management.
It is designed to fit a cloud computing course project with:

- Telegram bot interface
- LLM API integration
- database logging
- containerization
- cloud deployment
- monitoring
- DevOps workflow

## 1. What this bot can do

Feature 1: Natural-language stock query

- Ask for a stock in normal language
- Compare up to two stocks
- Get a short LLM-generated summary
- Log every request and response in the database

Feature 2: Personalized watchlist

- Add stocks with `/add AAPL`
- Remove stocks with `/remove AAPL`
- View watchlist with `/watchlist`
- Summarize watchlist with `/summary`

## 2. Tech stack

- Python 3.12
- FastAPI
- SQLAlchemy
- OpenAI API
- Yahoo Finance quote endpoint
- PostgreSQL or SQLite
- Docker and Docker Compose
- Prometheus and Grafana
- GitHub Actions
- Kubernetes manifests for scaling and load balancing demonstration

## 3. Project structure

```text
.
├── app
│   ├── config.py
│   ├── database.py
│   ├── dev_polling.py
│   ├── main.py
│   ├── metrics.py
│   ├── models.py
│   └── services
├── monitoring
├── k8s
├── tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .github/workflows/ci.yml
```

## 4. Accounts you need

Create these before running the project:

1. Telegram bot token from BotFather
2. MiMo Coding Plane API key and model name, or another OpenAI-compatible API
3. A database connection string

You already have an Alibaba Cloud RDS instance, so you should use that as the main project database.
That fits the course requirement better than a local SQLite database.

## 5. Local quick start

### Step 1: create `.env`

Run:

```bash
cp .env.example .env
```

Open `.env` and fill at least:

```env
TELEGRAM_BOT_TOKEN=your_real_bot_token
LLM_API_KEY=your_real_mimo_api_key
LLM_MODEL=MiMo-V2-Pro
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
TWELVE_DATA_API_KEY=your_twelve_data_api_key
DATABASE_URL=mysql+pymysql://db_user:db_password@rm-7xvu52u1yf7qo4vfn.mysql.rds.aliyuncs.com:3306/stockbot?charset=utf8mb4
```

This project is already wired for your MiMo setup because your dedicated endpoint is OpenAI-compatible.
You only need to put your real MiMo API key into `LLM_API_KEY`.

If you want to use OpenAI directly instead, you can leave `LLM_*` empty and fill:

```env
OPENAI_API_KEY=your_real_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
```

If you want webhook mode later, also set:

```env
TELEGRAM_WEBHOOK_SECRET_TOKEN=your_secret_string
PUBLIC_BASE_URL=https://your-domain.example.com
SET_TELEGRAM_WEBHOOK_ON_STARTUP=true
```

Important for your Alibaba Cloud RDS:

1. Your CSV shows the engine is `MySQL 8.0`
2. The private endpoint is `rm-7xvu52u1yf7qo4vfn.mysql.rds.aliyuncs.com`
3. The port is `3306`
4. `PublicString` is empty, so this RDS currently has no public endpoint

This means:

- your final ECS deployment should connect through the private endpoint
- the ECS instance should ideally be in the same VPC as the RDS
- local laptop testing may fail unless you later enable a public endpoint
- before running the app, create a database such as `stockbot` and a DB user with permission

For stock quotes, the app now works best with Twelve Data.
Set `TWELVE_DATA_API_KEY` in `.env` to avoid Yahoo Finance rate limits during your demo.

### Step 2: create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: run tests

```bash
python -m unittest discover -s tests -v
```

### Step 4: run the API service

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/healthz
- http://127.0.0.1:8000/metrics

### Step 5: run Telegram locally with polling mode

For local development, polling is easier than webhook:

```bash
python -m app.dev_polling
```

Now go to Telegram and send messages to your bot:

```text
/start
AAPL today
Compare AAPL and MSFT
/add NVDA
/watchlist
/summary
```

## 6. Docker run

### Option A: use Alibaba Cloud RDS directly, plus local monitoring containers

Update `.env` first.

If you want the app container to use your Alibaba Cloud RDS, set:

```env
DATABASE_URL=mysql+pymysql://db_user:db_password@rm-7xvu52u1yf7qo4vfn.mysql.rds.aliyuncs.com:3306/stockbot?charset=utf8mb4
```

Then run:

```bash
docker compose up --build
```

This now starts:

- `app` for FastAPI
- `poller` for Telegram polling
- `prometheus`
- `grafana`

If you also want a local PostgreSQL container for testing instead of Alibaba Cloud RDS, run:

```bash
docker compose --profile local-db up --build
```

Services:

- App: http://127.0.0.1:8000
- Prometheus: http://127.0.0.1:9090
- Grafana: http://127.0.0.1:3000

Grafana login:

- username: `admin`
- password: `admin`

## 7. Cloud deployment path

### Easiest path for today

Use one of these:

1. Cloud Run for hosting and Supabase or Neon for database
2. Railway for hosting and PostgreSQL
3. Render for hosting and PostgreSQL

### Final target for your project

If you want to deploy to Alibaba Cloud ECS, follow:

- [docs/deploy-to-aliyun-ecs.md](/Users/magic/Desktop/Cloud_Computing/docs/deploy-to-aliyun-ecs.md:1)

Exact prices and free-tier rules can change, so check the provider dashboard before deploying.

### Production environment variables

Set these in your cloud platform:

```env
APP_ENV=production
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET_TOKEN=...
PUBLIC_BASE_URL=https://your-real-domain.example.com
SET_TELEGRAM_WEBHOOK_ON_STARTUP=true
LLM_API_KEY=your_real_mimo_api_key
LLM_MODEL=MiMo-V2-Pro
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
DATABASE_URL=mysql+pymysql://db_user:db_password@rm-7xvu52u1yf7qo4vfn.mysql.rds.aliyuncs.com:3306/stockbot?charset=utf8mb4
```

### Build and push image

```bash
docker build -t telegram-stock-bot .
```

If you use GitHub Container Registry:

```bash
docker tag telegram-stock-bot ghcr.io/YOUR_GITHUB_USERNAME/telegram-stock-bot:latest
docker push ghcr.io/YOUR_GITHUB_USERNAME/telegram-stock-bot:latest
```

## 8. Telegram webhook setup

If your app is deployed at:

```text
https://your-domain.example.com
```

Then the bot webhook endpoint will be:

```text
https://your-domain.example.com/webhook/telegram
```

The app can call Telegram `setWebhook` automatically at startup when:

- `PUBLIC_BASE_URL` is set
- `SET_TELEGRAM_WEBHOOK_ON_STARTUP=true`

## 9. Database tables

The app auto-creates these tables:

- `users`
- `watchlist`
- `query_logs`

These tables are enough to demonstrate:

- persistence
- request logging
- user-specific data
- cloud database integration

## 10. Monitoring and cost-awareness

This project includes:

- `/healthz` for health checks
- `/readyz` for readiness checks
- `/metrics` for Prometheus
- Prometheus scrape config
- Grafana container

For cost control in the report, mention:

1. small container size
2. SQLite for local testing and PostgreSQL only for final cloud usage
3. low replica count by default
4. short response format to reduce LLM token usage
5. only one external data request per stock query

## 11. Nice-to-have mapping

This repository helps you demonstrate the extra items:

- DevOps workflow: GitHub Actions CI
- Scalability: Kubernetes deployment with replicas
- Load balancing: Kubernetes service and ingress
- Multiple containers: app, postgres, prometheus, grafana
- Security: env vars, webhook secret token, health probes
- Practical consideration: logging, monitoring, cost control

## 12. Recommended demo flow

Use this order in your presentation:

1. Show architecture diagram
2. Show GitHub repository
3. Show CI workflow file
4. Run the bot on Telegram
5. Query `AAPL today`
6. Add a stock to watchlist
7. Show `/watchlist`
8. Show `/summary`
9. Show database entries
10. Show `/metrics`
11. Show Docker or cloud dashboard

## 13. Good report sentences you can reuse

### Project summary

This project is a cloud-deployed Telegram chatbot that supports natural-language stock queries and personalized watchlist management. The bot integrates stock market data, an LLM API, database persistence, containerization, and monitoring to demonstrate practical cloud computing and DevOps concepts.

### Why this topic

The topic is practical, easy to demonstrate, and suitable for a single developer. It also naturally supports database usage, cloud hosting, LLM integration, observability, and scalable deployment design.

## 14. Important note

This bot is for educational use only.
It does not provide financial advice.
