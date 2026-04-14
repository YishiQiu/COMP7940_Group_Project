# Report Outline

## 1. Basic information

- Project title: Telegram Stock Query Assistant
- Bot ID: fill in your Telegram bot username
- Student name: fill in
- Student ID: fill in

## 2. Summary of the app

Telegram Stock Query Assistant is a cloud-ready chatbot that allows users to query stock information in natural language and manage a personalized watchlist. The system integrates Telegram, an LLM API, a database, containerization, and monitoring to demonstrate cloud computing and DevOps practices.

## 3. Main features

### Feature 1: Natural-language stock query

- User asks for stock information through Telegram
- The app extracts stock symbols
- The app fetches market data from an external stock API
- The app uses an LLM API to generate a concise summary
- The app logs the request and response in the database

### Feature 2: Personalized watchlist management

- Users can add and remove stocks from a watchlist
- Users can view their watchlist
- Users can ask the bot to summarize the current status of the watchlist
- All watchlist operations are stored in the database

## 4. System architecture

Telegram User -> Telegram Bot -> FastAPI App -> Stock API + OpenAI API + Database

The FastAPI app is containerized with Docker and monitored with Prometheus and Grafana.

## 5. Technical requirements mapping

### Must-have

- Telegram chatbot: yes
- Database system from a cloud provider: yes, Alibaba Cloud RDS MySQL 8.0
- Hosted on a cloud platform: yes after deployment
- LLM API: yes
- Git-managed project: yes
- Container technologies: yes
- Monitoring and cost control: yes

### Nice-to-have

- DevOps workflow: GitHub Actions CI
- Scalability: Kubernetes deployment with multiple replicas
- Load balancing: Kubernetes service and ingress
- Orchestration of multiple containers: Docker Compose stack
- Security measurements: webhook secret token, env vars, readiness probes
- Practical consideration: logging, health checks, cost-aware design

## 6. Database design

### users

- store Telegram user information

### watchlist

- store user-specific tracked stock symbols

### query_logs

- store user input, detected symbols, market data, and generated replies

## 7. Cloud and DevOps design

- Dockerfile for containerized app
- Docker Compose for local multi-container stack
- GitHub Actions for continuous integration
- Kubernetes manifests for scaling and load balancing demonstration
- Prometheus and Grafana for observability

## 8. Cost control

- keep the service stateless and lightweight
- use low replica counts by default
- use short LLM outputs
- only call the stock API once per query
- use Alibaba Cloud RDS as the main project database and keep the instance size small

## 9. Evidence to include

- Telegram conversation screenshots
- database screenshots
- Docker or cloud deployment screenshots
- Prometheus or Grafana screenshots
- GitHub repository screenshot
- GitHub Actions passing screenshot
- cloud billing screenshot

## 10. Conclusion

This project demonstrates a practical cloud-native chatbot with Telegram integration, database persistence, LLM support, observability, and deployment readiness. It is suitable for a single developer and aligns well with the course project requirements.
