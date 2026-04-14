# Telegram Stock Query Assistant

A cloud-deployed Telegram chatbot for natural-language stock queries and personal watchlist management.

This project was built for `COMP7940 Cloud Computing` and focuses on:

- Telegram bot integration
- cloud database usage
- LLM-powered response generation
- containerization and deployment readiness
- observability and operational design

## Features

### 1. Natural-language stock query

- Query stocks in plain English
- Compare up to two stocks in one request
- Generate concise LLM summaries
- Log requests and responses in the database

Examples:

```text
AAPL today
Compare AAPL and MSFT
How is Nvidia stock doing?
```

### 2. Personal watchlist management

- Add stocks with `/add AAPL`
- Remove stocks with `/remove AAPL`
- View current watchlist with `/watchlist`
- Summarize tracked stocks with `/summary`

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- MySQL
- Telegram Bot API
- MiMo OpenAI-compatible API
- Twelve Data
- Docker / Docker Compose
- GitHub Actions
- Prometheus-compatible metrics endpoint

## Project Structure

```text
.
├── app/
├── docs/
├── k8s/
├── monitoring/
├── tests/
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Create environment file

```bash
cp .env.example .env
```

Fill at least:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
LLM_API_KEY=your_mimo_api_key
LLM_MODEL=MiMo-V2-Pro
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
TWELVE_DATA_API_KEY=your_twelve_data_api_key
DATABASE_URL=mysql+pymysql://user:password@host:3306/stock_bot?charset=utf8mb4
```

### 2. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run tests

```bash
python -m unittest discover -s tests -v
```

### 4. Run locally

Start the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Start the Telegram polling worker in a second terminal:

```bash
python -m app.dev_polling
```

## Deployment Notes

- The final deployed version uses a cloud VM and a cloud MySQL database.
- The backend is stateless and suitable for horizontal scaling.
- Multi-container orchestration and Kubernetes manifests are included for deployment design and nice-to-have demonstration.

## Nice-to-Have Coverage

- DevOps workflow: GitHub Actions CI
- Scalability: stateless backend + Kubernetes deployment/HPA manifests
- Load balancing: service and ingress manifests
- Multi-container orchestration: Docker Compose design
- Security: environment-based secret management and cloud DB access control
- Practical considerations: health checks, metrics, logging, fallback stock data source

## Included Submission Aids

- [Report outline](./docs/report-outline.md)
- [Presentation outline](./docs/presentation-outline.md)

## Important Note

This bot is for educational use only and does not provide financial advice.
