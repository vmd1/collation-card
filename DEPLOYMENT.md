# Deployment Guide

## Quick Start (Development)

1. Clone the repository
2. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

3. Build and run with Docker Compose:
   ```bash
   docker-compose build
   docker-compose up
   ```

4. Access the services:
   - Dashboard: http://localhost:8000
   - Submit: http://localhost:8001
   - Card: http://localhost:8002

## Production Deployment with Traefik + Authentik

### Prerequisites

- External Traefik reverse proxy running
- External Authentik instance configured
- Docker and Docker Compose installed

### Configuration

1. **Update docker-compose.yml labels** for your domain:
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.dashboard.rule=Host(`dashboard.yourdomain.com`)"
     - "traefik.http.routers.dashboard.middlewares=authentik-forward-auth@docker"
   ```

2. **Set environment variables** in `.env`:
   ```bash
   SECRET_KEY=$(openssl rand -hex 32)
   DATABASE_URL=sqlite:////data/virtual_card.db
   MEDIA_PATH=/media
   REDIS_URL=redis://redis:6379/0  # For production rate limiting
   ```

3. **Configure Authentik** to protect Dashboard and Card services
   - Dashboard requires authentication
   - Card requires authentication
   - Submit is public (no auth required)

### Important Security Notes

- The Flask applications DO NOT read or act on auth headers from Traefik/Authentik
- Authentication is enforced at the Traefik layer only
- Applications use ProxyFix for correct URL generation but DO NOT use forwarded identity headers

## Database Migrations

Database tables are automatically created on first run. The schema is defined in `shared/models.py`.

## Scaling

For production:
- Replace SQLite with PostgreSQL
- Use Redis for rate limiting
- Use dedicated media storage (S3, etc.)
- Increase gunicorn workers based on CPU cores

## Monitoring

- Health check endpoint: `/health` (submit service)
- Monitor logs via `docker-compose logs -f`
- Set up Prometheus metrics as needed

## Backups

Backup these volumes:
- `db_data` - SQLite database
- `media_data` - Uploaded images
