# Manual deployment guide

This project is best deployed manually on a VPS with Docker Compose. The frontend container serves the React build through nginx and proxies `/api/*` to the FastAPI backend container.

## 1. Buy domain and VPS

Use any domain registrar and any VPS provider. For this stack, choose at least:

- 2 vCPU
- 4 GB RAM minimum, 8 GB recommended because Kafka, PostgreSQL, Redis, worker, Grafana and Prometheus run together
- Ubuntu 22.04 or 24.04
- Public IPv4 address

Example domain used below: `example.com`.

## 2. Point DNS to the server

Create DNS records at the domain registrar:

```text
A      @      SERVER_IP
A      www    SERVER_IP
```

Wait until DNS resolves:

```bash
nslookup example.com
```

## 3. Prepare the server

Install Docker, Docker Compose plugin, nginx, and Certbot:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git nginx certbot python3-certbot-nginx
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and back in after adding the user to the `docker` group.

## 4. Upload the project

Clone the repository on the server:

```bash
git clone REPOSITORY_URL /opt/portofino
cd /opt/portofino
```

Or upload the project folder manually to `/opt/portofino`.

## 5. Configure environment

Create the secret file:

```bash
cp .env_secret.example .env_secret
nano .env_secret
```

Edit `.env` for production:

```text
APP_ENV=prod
API_BASE_URL=https://example.com/api
FRONTEND_URL=https://example.com
POSTGRES_PASSWORD=the-same-password-from-env-secret
```

Keep internal service hosts as they are:

```text
POSTGRES_HOST=postgres
REDIS_URL=redis://redis:6379/0
KAFKA_BROKER=kafka:9092
```

If Google OAuth is enabled, register this redirect URI in Google Cloud:

```text
https://example.com/api/auth/google/callback
```

## 6. Start the app

Build and run the containers:

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
docker compose logs -f backend
```

At this point the frontend container is available on server port `5173`.

## 7. Put nginx in front

Create `/etc/nginx/sites-available/portofino`:

```nginx
server {
    listen 80;
    server_name example.com www.example.com;

    client_max_body_size 25m;

    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/portofino /etc/nginx/sites-enabled/portofino
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Enable HTTPS

Issue a free Let's Encrypt certificate:

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

Check renewal:

```bash
sudo certbot renew --dry-run
```

## 9. Firewall

Open only SSH and web traffic publicly:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

For a stricter setup, bind Docker service ports to localhost or remove public ports for PostgreSQL, Redis, Kafka, Grafana, Prometheus, Flower and Kafka UI before production launch.

## 10. Smoke checks

Run:

```bash
curl -I https://example.com
curl https://example.com/api/health
```

Then open:

```text
https://example.com
```

## Production notes

- Do not commit `.env_secret`.
- Change Grafana default password before exposing it.
- Do not expose PostgreSQL, Redis or Kafka to the internet.
- Back up the `postgres_data` Docker volume.
- Use `docker compose pull && docker compose up -d --build` for updates.
