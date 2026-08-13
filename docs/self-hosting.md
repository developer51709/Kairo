# Self-Hosting

This guide covers running Kairo on your own hardware or server.

---

## Requirements

- Python 3.11 or higher
- 512MB RAM minimum (1GB recommended)
- Linux, macOS, or Windows
- A Discord application with bot token, client ID, and client secret

---

## Local Installation

The simplest way to run Kairo — suitable for development and small servers.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/kairo.git
cd kairo

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
python src/setup.py

# 5. Run
python src/run.py
```

---

## Linux (VPS or Dedicated Server)

### Systemd Service

Create a service file so Kairo starts automatically and restarts on failure:

```ini
# /etc/systemd/system/kairo.service

[Unit]
Description=Kairo Discord Bot
After=network.target

[Service]
Type=simple
User=kairo
WorkingDirectory=/opt/kairo
Environment=PATH=/opt/kairo/.venv/bin
ExecStart=/opt/kairo/.venv/bin/python src/run.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kairo
sudo systemctl start kairo
sudo journalctl -u kairo -f   # View logs
```

### Running with the API Server

```ini
ExecStart=/opt/kairo/.venv/bin/python src/run.py --with-api
```

---

## Reverse Proxy (Nginx)

If you want to expose the API or dashboard behind a domain:

```nginx
# /etc/nginx/sites-available/kairo

server {
    listen 443 ssl;
    server_name kairo.example.com;

    ssl_certificate     /etc/letsencrypt/live/kairo.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kairo.example.com/privkey.pem;

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8080;
    }

    # Dashboard (once implemented)
    location / {
        proxy_pass http://127.0.0.1:5173;
    }
}
```

---

## Docker

> 🚧 Docker support is planned for Phase 5.

A `Dockerfile` and `docker-compose.yml` will be provided. Planned usage:

```bash
# Copy and configure
cp .env.example .env
# Edit .env

# Build and run
docker compose up -d

# View logs
docker compose logs -f kairo
```

---

## Cloudflare Tunnel

Cloudflare Tunnel lets you expose your local Kairo installation without
opening any firewall ports.

```bash
# Install cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/install-and-setup/installation/

# Authenticate
cloudflared tunnel login

# Create a tunnel
cloudflared tunnel create kairo

# Configure
cat > ~/.cloudflared/config.yml <<EOF
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: kairo.example.com
    service: http://127.0.0.1:8080
  - service: http_status:404
EOF

# Start
cloudflared tunnel run kairo
```

Set `DASHBOARD_URL=https://kairo.example.com` in your `.env`.

---

## ngrok

```bash
# Install ngrok from https://ngrok.com

# Start a tunnel to the API
ngrok http 8080
```

Copy the generated HTTPS URL and set:
```
DASHBOARD_URL=https://your-ngrok-url.ngrok.io
```

> Note: Free ngrok URLs change on every restart. Use a paid plan or a
> different tunnel provider for stable URLs.

---

## Backups

Back up the database file regularly:

```bash
# Simple copy
cp data/kairo.db data/kairo.db.backup.$(date +%Y%m%d)

# Or use SQLite's built-in backup
sqlite3 data/kairo.db ".backup data/kairo.db.backup"
```

Consider setting up a cron job:

```cron
# Back up the database daily at 3 AM
0 3 * * * sqlite3 /opt/kairo/data/kairo.db ".backup /opt/kairo/backups/kairo.$(date +\%Y\%m\%d).db"
```

---

## Updates

```bash
cd /opt/kairo

# Pull latest changes
git pull

# Update dependencies
.venv/bin/pip install -r requirements.txt

# Restart
sudo systemctl restart kairo
```

Migrations run automatically on startup — the database schema will be
updated to match the new version.

---

## Troubleshooting

**Bot not starting:**
```bash
python src/run.py 2>&1 | head -50
```
Look for configuration errors (missing env vars, invalid token).

**Database errors:**
Ensure the `data/` directory exists and is writable:
```bash
mkdir -p data
chmod 755 data
```

**Slash commands not appearing:**
In development, set `DEV_GUILD_ID` for instant sync.
In production, global sync takes up to 1 hour after startup.

**Permission errors:**
Ensure the bot has been invited with the correct permissions and that
"Server Members Intent" and "Message Content Intent" are enabled in the
Discord Developer Portal.
