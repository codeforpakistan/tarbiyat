# 🚀 Tarbiyat Platform Deployment Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Infrastructure Specifications](#infrastructure-specifications)
3. [Database Configuration](#database-configuration)
4. [Environment Setup](#environment-setup)
5. [Deployment Options](#deployment-options)
6. [Security Configuration](#security-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Hardware Specifications

| Component | Development | Production (Small) | Production (Medium) | Production (Large) |
|-----------|------------|-------------------|--------------------|--------------------|
| **CPU** | 2 vCPUs | 2 vCPUs | 4 vCPUs | 8+ vCPUs |
| **RAM** | 2 GB | 4 GB | 8 GB | 16+ GB |
| **Storage** | 20 GB SSD | 50 GB SSD | 100 GB SSD | 200+ GB SSD |
| **Network** | Basic | 1 Gbps | 1 Gbps | 10+ Gbps |
| **Users** | 1-10 | 50-200 | 500-2000 | 5000+ |

### Software Requirements

- **Operating System:** Ubuntu 22.04 LTS (recommended) or CentOS 8+
- **Python:** 3.12+ (as specified in `runtime.txt`)
- **Web Server:** Nginx 1.18+
- **Process Manager:** Gunicorn or uWSGI
- **Database:** SQLite (development) / PostgreSQL 14+ (production)
- **Reverse Proxy:** Nginx
- **SSL/TLS:** Let's Encrypt or commercial certificate
- **Process Supervisor:** systemd or supervisor

---

## Infrastructure Specifications

### Cloud Provider Recommendations

#### AWS EC2 Instances
| Size | Instance Type | vCPUs | Memory | Storage | Use Case |
|------|---------------|-------|---------|---------|----------|
| Small | t3.small | 2 | 2 GB | 20 GB GP3 | Development/Testing |
| Medium | t3.medium | 2 | 4 GB | 50 GB GP3 | Small Production |
| Large | t3.large | 2 | 8 GB | 100 GB GP3 | Medium Production |
| XLarge | t3.xlarge | 4 | 16 GB | 200 GB GP3 | Large Production |

#### Digital Ocean Droplets
| Size | Droplet Type | vCPUs | Memory | Storage | Use Case |
|------|--------------|-------|---------|---------|----------|
| Small | Regular $12/mo | 1 | 2 GB | 50 GB SSD | Development |
| Medium | Regular $24/mo | 2 | 4 GB | 80 GB SSD | Small Production |
| Large | Regular $48/mo | 4 | 8 GB | 160 GB SSD | Medium Production |
| XLarge | Regular $96/mo | 8 | 16 GB | 320 GB SSD | Large Production |

#### Google Cloud Compute Engine
| Size | Machine Type | vCPUs | Memory | Storage | Use Case |
|------|--------------|-------|---------|---------|----------|
| Small | e2-small | 2 | 2 GB | 20 GB SSD | Development |
| Medium | e2-medium | 2 | 4 GB | 50 GB SSD | Small Production |
| Large | e2-standard-4 | 4 | 16 GB | 100 GB SSD | Medium Production |
| XLarge | e2-standard-8 | 8 | 32 GB | 200 GB SSD | Large Production |

### Network Configuration

#### Firewall Rules
```bash
# HTTP/HTTPS Traffic
Port 80 (HTTP) - Open to 0.0.0.0/0
Port 443 (HTTPS) - Open to 0.0.0.0/0

# SSH Access (restrict to admin IPs)
Port 22 (SSH) - Open to admin IP ranges only

# Database (if separate server)
Port 5432 (PostgreSQL) - Open to application server only

# Application Server (internal)
Port 8000 (Gunicorn) - Open to reverse proxy only
```

#### Domain Configuration
- **Primary Domain:** `tarbiyat.pk`
- **Subdomain Options:** 
  - `www.tarbiyat.pk` (redirect to primary)
  - `api.tarbiyat.pk` (if API is separated)
  - `admin.tarbiyat.pk` (admin interface)

---

## Database Configuration

### Development Database (SQLite)
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Production Database (PostgreSQL)

#### PostgreSQL Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE tarbiyat_db;
CREATE USER tarbiyat_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE tarbiyat_db TO tarbiyat_user;
ALTER USER tarbiyat_user CREATEDB;
\q
```

#### Django Configuration
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='tarbiyat_db'),
        'USER': config('DB_USER', default='tarbiyat_user'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': config('DB_SSLMODE', default='prefer'),
        },
    }
}
```

#### Database Optimization
```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '2GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
```

---

## Environment Setup

### System Dependencies
```bash
# Ubuntu 22.04 LTS
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip nginx postgresql postgresql-contrib
sudo apt install -y git curl wget unzip supervisor redis-server
sudo apt install -y build-essential libpq-dev python3.12-dev
```

### Application Deployment

#### 1. Create Application User
```bash
sudo adduser --system --group tarbiyat
sudo mkdir -p /var/www/tarbiyat
sudo chown tarbiyat:tarbiyat /var/www/tarbiyat
```

#### 2. Clone Repository
```bash
sudo -u tarbiyat git clone https://github.com/codeforpakistan/tarbiyat.git /var/www/tarbiyat
cd /var/www/tarbiyat
```

#### 3. Create Virtual Environment
```bash
sudo -u tarbiyat python3.12 -m venv venv
sudo -u tarbiyat ./venv/bin/pip install --upgrade pip
sudo -u tarbiyat ./venv/bin/pip install -r requirements.txt
sudo -u tarbiyat ./venv/bin/pip install gunicorn psycopg2-binary
```

#### 4. Environment Configuration
```bash
# Create production environment file
sudo -u tarbiyat cp .env.example .env
sudo -u tarbiyat nano .env
```

### Production Environment Variables
```bash
# .env file for production
# Django Settings
SECRET_KEY=your-very-long-and-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=tarbiyat.pk,www.tarbiyat.pk,your-server-ip

# Database Settings (PostgreSQL)
DB_NAME=tarbiyat_db
DB_USER=tarbiyat_user
DB_PASSWORD=your-secure-database-password
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=prefer

# Email Settings (SendGrid)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@tarbiyat.pk
SENDGRID_API_KEY=your-sendgrid-api-key

# Site Settings
SITE_ID=1

# Security Settings (Production)
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Google OAuth2 Settings
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
```

#### 5. Database Migration
```bash
---

## Deployment Options

### Option 1: Traditional VM Deployment

#### Gunicorn Configuration
```bash
# /var/www/tarbiyat/gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

#### Systemd Service
```ini
# /etc/systemd/system/tarbiyat.service
[Unit]
Description=Tarbiyat Django Application
After=network.target

[Service]
Type=notify
User=tarbiyat
Group=tarbiyat
WorkingDirectory=/var/www/tarbiyat
Environment=DJANGO_SETTINGS_MODULE=project.settings
ExecStart=/var/www/tarbiyat/venv/bin/gunicorn project.wsgi:application -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/tarbiyat
server {
    listen 80;
    server_name tarbiyat.pk www.tarbiyat.pk;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tarbiyat.pk www.tarbiyat.pk;

    ssl_certificate /etc/letsencrypt/live/tarbiyat.pk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tarbiyat.pk/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    client_max_body_size 100M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/tarbiyat/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/tarbiyat/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

#### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable tarbiyat
sudo systemctl start tarbiyat
sudo systemctl enable nginx
sudo systemctl restart nginx

# Enable site
sudo ln -s /etc/nginx/sites-available/tarbiyat /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Option 2: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "project.wsgi:application"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: tarbiyat_db
      POSTGRES_USER: tarbiyat_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DB_HOST=db
    depends_on:
      - db
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_volume:/var/www/static
      - media_volume:/var/www/media
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Option 3: DigitalOcean App Platform

#### Quick Setup
1. Fork the repository to your GitHub
2. Create new app in DigitalOcean App Platform
3. Connect your GitHub repository
4. Configure environment variables:
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=.ondigitalocean.app
```
5. Deploy and run migrations via console

#### Cost: $5-12/month for basic setup

### Option 4: Heroku Deployment
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login and create app
heroku login
heroku create tarbiyat-platform

# Configure environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py setup_groups
```

---

## Security Configuration

### SSL/TLS Setup with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d tarbiyat.pk -d www.tarbiyat.pk

# Auto-renewal setup
sudo crontab -e
# Add line: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration
```bash
# UFW (Ubuntu Firewall)
sudo ufw enable
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny 8000/tcp     # Block direct access to Django
```

### Security Hardening
```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## Monitoring & Maintenance

### Health Monitoring Script
```bash
#!/bin/bash
# /usr/local/bin/health-check.sh

# Check if Tarbiyat service is running
if ! systemctl is-active --quiet tarbiyat; then
    echo "Tarbiyat service is down, restarting..."
    systemctl restart tarbiyat
fi

# Check disk usage
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Warning: Disk usage is $DISK_USAGE%"
fi
```

### Log Management
```bash
# Application logs
sudo mkdir -p /var/log/tarbiyat
sudo chown tarbiyat:tarbiyat /var/log/tarbiyat

# Logrotate configuration
# /etc/logrotate.d/tarbiyat
/var/log/tarbiyat/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 tarbiyat tarbiyat
}
```

---

## Backup & Recovery

### Database Backup Script
```bash
#!/bin/bash
# /usr/local/bin/backup-database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/tarbiyat"
DB_NAME="tarbiyat_db"

mkdir -p $BACKUP_DIR

# Create database backup
sudo -u postgres pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Create media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C /var/www/tarbiyat media/

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Automated Backup Cron Jobs
```bash
# Add to crontab (sudo crontab -e)
# Daily database backup at 2 AM
0 2 * * * /usr/local/bin/backup-database.sh >> /var/log/backup.log 2>&1
```

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check service status
sudo systemctl status tarbiyat

# Check logs
sudo journalctl -u tarbiyat -f

# Restart service
sudo systemctl restart tarbiyat
```

#### 2. Database Connection Issues
```bash
# Test database connection
sudo -u tarbiyat ./venv/bin/python manage.py dbshell

# Check PostgreSQL status
sudo systemctl status postgresql
```

#### 3. Static Files Not Loading
```bash
# Recollect static files
sudo -u tarbiyat ./venv/bin/python manage.py collectstatic --clear --noinput

# Check nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. Email Issues
```bash
# Test email configuration
sudo -u tarbiyat ./venv/bin/python manage.py test_email test@example.com
```

### Emergency Procedures

#### Service Recovery
```bash
# Emergency restart sequence
sudo systemctl stop tarbiyat
sudo systemctl stop nginx
sudo systemctl restart postgresql
sudo systemctl start tarbiyat
sudo systemctl start nginx
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Server provisioned with required specifications
- [ ] Domain name configured and DNS pointing to server
- [ ] SSL certificate obtained
- [ ] Database setup and configured
- [ ] Environment variables configured

### Deployment
- [ ] Application code deployed
- [ ] Dependencies installed
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Services configured and started

### Post-Deployment
- [ ] Functionality testing completed
- [ ] Performance testing completed
- [ ] Security scan performed
- [ ] Monitoring tools configured
- [ ] Backup procedures tested

---

## Cost Estimation

### Development Environment
- **Digital Ocean Droplet (2GB):** $12/month
- **Domain:** $10-15/year
- **SSL Certificate:** Free (Let's Encrypt)
- **Total:** ~$15/month

### Small Production (50-200 users)
- **Digital Ocean Droplet (4GB):** $24/month
- **Domain:** $10-15/year
- **SSL Certificate:** Free (Let's Encrypt)
- **Backups:** $2.40/month (10% of droplet cost)
- **Total:** ~$27/month

### Medium Production (500-2000 users)
- **Digital Ocean Droplet (8GB):** $48/month
- **Database (PostgreSQL):** $15/month
- **Load Balancer:** $10/month
- **Domain:** $10-15/year
- **Total:** ~$75/month

### Large Production (5000+ users)
- **Digital Ocean Droplet (16GB):** $96/month
- **Database (PostgreSQL Pro):** $50/month
- **Load Balancer:** $10/month
- **CDN:** $5/month
- **Monitoring:** $20/month
- **Total:** ~$180/month

---

*This comprehensive deployment guide covers VM specifications, database configuration, security, monitoring, and maintenance for the Tarbiyat platform. Choose the deployment option that best fits your requirements and budget.*
