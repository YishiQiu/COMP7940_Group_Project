# Deploy to Alibaba Cloud ECS

Current deployment target used in this project:

- region: `China (Hong Kong)`
- public IPv4: `101.32.219.172`
- private IPv4: `172.17.13.26`
- instance ID: `lhins-rndux1j5`
- key pair: `lhkp-lld2masr`

This guide assumes:

- Ubuntu 24.04 LTS
- one ECS instance
- one domain name already pointing to the ECS public IP
- Docker-based deployment

This ECS uses key-based SSH login, so use your private key instead of password login.

## 1. Recommended architecture

- Alibaba Cloud ECS: run Docker, Nginx, and the FastAPI app
- Alibaba Cloud RDS MySQL 8.0: the cloud database for logs and watchlist data
- Telegram webhook: `https://your-domain/webhook/telegram`
- Optional monitoring: Prometheus and Grafana in Docker

## 2. Prepare the ECS instance

In the Alibaba Cloud console:

1. Create an ECS instance in a VPC
2. Use Ubuntu 22.04
3. Choose a low-cost instance type
4. Make sure the instance has public Internet access
5. Configure the security group inbound rules:
   - TCP 22 for SSH
   - TCP 80 for HTTP
   - TCP 443 for HTTPS

For your current RDS instance:

- Engine: `MySQL 8.0`
- Private endpoint: `rm-7xvu52u1yf7qo4vfn.mysql.rds.aliyuncs.com`
- Private port: `3306`
- Public endpoint: must be enabled if this Hong Kong ECS will connect to the Guangzhou RDS

Because this ECS is in Hong Kong and your RDS is in Guangzhou, you should:

1. enable the RDS public endpoint
2. add `101.32.219.172` to the RDS whitelist
3. use the RDS public endpoint in `DATABASE_URL`

If your instance does not have a public IP yet, Alibaba Cloud documents that you can either allocate a public IP or bind an EIP to the ECS instance:

- [ECS supports EIP/public network integration](https://help.aliyun.com/zh/ecs/services-that-work-with-ecs)
- [EIP quick start](https://help.aliyun.com/zh/eip/getting-started)

## 3. Connect to ECS

From your local terminal:

```bash
chmod 600 /path/to/your-private-key.pem
ssh -i /path/to/your-private-key.pem root@101.32.219.172
```

If `root` is not allowed, try:

```bash
ssh -i /path/to/your-private-key.pem ubuntu@101.32.219.172
```

## 4. Install Docker and Docker Compose plugin

Run on ECS:

```bash
apt update
apt install -y docker.io docker-compose-v2 nginx
systemctl enable docker
systemctl start docker
systemctl enable nginx
systemctl start nginx
```

Then configure the Alibaba Cloud registry mirror:

```bash
mkdir -p /etc/docker
cat >/etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": ["https://u93vpt35.mirror.aliyuncs.com/"]
}
EOF
systemctl daemon-reload
systemctl restart docker
docker info | grep -A 5 "Registry Mirrors"
```

## 5. Upload the project

On your local machine:

```bash
cd /Users/magic/Desktop/Cloud_Computing
scp -i /path/to/your-private-key.pem -r . root@101.32.219.172:/opt/telegram-stock-bot
```

If you must use `ubuntu`:

```bash
scp -i /path/to/your-private-key.pem -r . ubuntu@101.32.219.172:/tmp/telegram-stock-bot
ssh -i /path/to/your-private-key.pem ubuntu@101.32.219.172
sudo mv /tmp/telegram-stock-bot /opt/telegram-stock-bot
```

On ECS:

```bash
cd /opt/telegram-stock-bot
cp .env.example .env
```

Edit `.env`:

```bash
nano .env
```

Use values like:

```env
APP_ENV=production
APP_PORT=8000
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET_TOKEN=dev-secret
PUBLIC_BASE_URL=
SET_TELEGRAM_WEBHOOK_ON_STARTUP=false

LLM_API_KEY=your_mimo_api_key
LLM_MODEL=MiMo-V2-Pro
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
LLM_PROVIDER_NAME=MiMo Coding Plane

TWELVE_DATA_API_KEY=your_twelve_data_key
TWELVE_DATA_BASE_URL=https://api.twelvedata.com

DATABASE_URL=mysql+pymysql://dms_user_cbe1532:YOUR_PASSWORD_ENCODED@YOUR_RDS_PUBLIC_HOST:3306/stock_bot?charset=utf8mb4
```

Before starting the app, finish these RDS steps in the Alibaba Cloud console:

1. Create a database named `stock_bot`
2. Make sure the account `dms_user_cbe1532` has permission on `stock_bot`
3. Enable the RDS public endpoint
4. Add `101.32.219.172` to the RDS whitelist
5. Replace `YOUR_PASSWORD_ENCODED` with your URL-encoded password
6. Replace `YOUR_RDS_PUBLIC_HOST` with the real RDS public address

## 6. Build and start the app

On ECS:

```bash
cd /opt/telegram-stock-bot
docker compose up -d --build
docker compose ps
```

Check logs:

```bash
docker compose logs -f app
```

If database connection fails, check these first:

1. the RDS username and password
2. whether the `stock_bot` database exists
3. whether the RDS public endpoint is enabled
4. whether `101.32.219.172` is in the RDS whitelist

## 7. Configure Nginx reverse proxy

Create the Nginx site file:

```bash
cat >/etc/nginx/sites-available/telegram-stock-bot <<'EOF'
server {
    listen 80;
    server_name your-domain.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
ln -sf /etc/nginx/sites-available/telegram-stock-bot /etc/nginx/sites-enabled/telegram-stock-bot
nginx -t
systemctl reload nginx
```

## 8. Add HTTPS with Let's Encrypt

Run:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.example.com
```

After HTTPS is ready, Telegram webhook can call your server securely.

## 9. Test the service

Open these URLs in your browser:

- `https://your-domain.example.com/`
- `https://your-domain.example.com/healthz`
- `https://your-domain.example.com/metrics`

Then test the bot in Telegram:

```text
/start
AAPL today
/add NVDA
/watchlist
/summary
```

## 10. Useful operations

Restart:

```bash
cd /opt/telegram-stock-bot
docker compose restart
```

Rebuild after code changes:

```bash
cd /opt/telegram-stock-bot
docker compose up -d --build
```

View all logs:

```bash
cd /opt/telegram-stock-bot
docker compose logs -f
```

## 11. What to screenshot for your report

Take screenshots of:

1. ECS instance details page
2. Security group rules for ports 22, 80, 443
3. Your domain opening `/healthz`
4. Telegram conversation with the bot
5. `docker compose ps`
6. Prometheus or Grafana if enabled

## 12. Why this satisfies the database requirement

Your CSV shows you are already using a real cloud database service:

- provider: Alibaba Cloud
- product: RDS
- engine: MySQL 8.0
- region: `cn-guangzhou`

So yes, this database is valid for the course requirement.
