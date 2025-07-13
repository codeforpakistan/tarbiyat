# DigitalOcean App Platform Deployment Guide

This guide will help you deploy the Tarbiyat application to DigitalOcean App Platform.

## Prerequisites

1. **DigitalOcean Account**: Sign up at [DigitalOcean](https://www.digitalocean.com/)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **Domain (Optional)**: Custom domain for your application

## Deployment Methods

### Method 1: Using DigitalOcean Control Panel (Recommended)

#### Step 1: Create New App

1. Log into your DigitalOcean dashboard
2. Click **"Apps"** in the left sidebar
3. Click **"Create App"**
4. Choose **"GitHub"** as your source
5. Authorize DigitalOcean to access your GitHub account
6. Select the **`codeforpakistan/tarbiyat`** repository
7. Choose the **`master`** branch
8. Click **"Next"**

#### Step 2: Configure Resources

1. **Web Service Configuration**:
   - Name: `tarbiyat-web`
   - Environment Variables (set these in the Environment tab):
     ```
     SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
     DEBUG=False
     ALLOWED_HOSTS=.ondigitalocean.app,.your-domain.com
     ```
   - Build Command: (leave empty, uses requirements.txt automatically)
   - Run Command: `gunicorn --worker-tmp-dir /dev/shm project.wsgi`
   - Instance Size: Basic ($5/month) or higher

2. **Database**: SQLite is used by default (no separate database service needed)

#### Step 3: Environment Variables

Add these environment variables in the App Platform dashboard:

| Key | Value | Type |
|-----|-------|------|
| `SECRET_KEY` | Generate a secure key | Secret |
| `DEBUG` | `False` | Plain Text |
| `ALLOWED_HOSTS` | `.ondigitalocean.app` | Plain Text |

#### Step 4: Deploy

1. Review your configuration
2. Click **"Create Resources"**
3. Wait for the initial deployment (5-10 minutes)

### Method 2: Using App Spec (app.yaml)

1. Fork/clone the repository
2. The `app.yaml` file is already configured
3. Update environment variables in the file
4. Deploy using the DigitalOcean CLI or import the spec

## Post-Deployment Configuration

### Step 1: Run Database Migrations

Access your app's console:

1. Go to your app in the DigitalOcean dashboard
2. Click on **"Console"** tab
3. Select your web service
4. Run the following commands:

```bash
# Run migrations
python manage.py migrate

# Create user groups
python manage.py setup_groups

# Create a superuser
python manage.py createsuperuser

# Optional: Load sample data
python manage.py seed
```

### Step 2: Configure Django Admin

1. Navigate to `https://your-app-url.ondigitalocean.app/admin/`
2. Login with your superuser credentials
3. Add a **Site** object:
   - Domain: `your-app-url.ondigitalocean.app`
   - Display name: `Tarbiyat`

### Step 3: Test the Application

1. Visit your application URL
2. Test user registration and login
3. Create test profiles for different user types
4. Verify all functionality works correctly

## Environment Variables Reference

### Required Variables

```bash
# Security (REQUIRED)
SECRET_KEY=your-secret-key-minimum-50-characters-long

# Environment (REQUIRED)
DEBUG=False
ALLOWED_HOSTS=.ondigitalocean.app,your-custom-domain.com

# Database: SQLite is used by default (no configuration needed)
```

### Optional Variables

```bash
# Email Configuration (for password reset, notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security Headers (automatically set for production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Database Configuration

### SQLite (Default)
The application uses SQLite by default, which is suitable for:
- Small to medium-sized deployments
- Development and testing
- Quick deployment without database setup
- Cost-effective hosting

### When to Consider PostgreSQL
Consider upgrading to PostgreSQL if you need:
- High concurrent users (500+ simultaneous)
- Advanced database features
- Better performance for complex queries
- Database replication and backup features

To switch to PostgreSQL:
1. Add a PostgreSQL database in DigitalOcean App Platform
2. Update your environment variables with `DATABASE_URL`
3. Install `psycopg2-binary` and `dj-database-url` in requirements.txt

### Add Custom Domain

1. In your DigitalOcean App dashboard
2. Go to **"Settings"** → **"Domains"**
3. Click **"Add Domain"**
4. Enter your domain name
5. Update your DNS records as instructed

### Update Environment Variables

Add your custom domain to `ALLOWED_HOSTS`:
```
ALLOWED_HOSTS=.ondigitalocean.app,yourdomain.com,www.yourdomain.com
```

## Scaling and Performance

### Vertical Scaling
- Upgrade your dyno size for more CPU/memory
- Basic ($5) → Professional ($12) → Professional XL ($25)

### Horizontal Scaling
- Increase instance count in the app settings
- Add load balancer for high traffic

### Database Scaling
- Dev Database ($7) → Basic ($15) → Production plans
- Enable connection pooling for better performance

## Monitoring and Logs

### View Application Logs
1. Go to your app dashboard
2. Click **"Runtime Logs"**
3. Monitor for errors and performance issues

### Set Up Alerts
1. Configure alerts for high CPU, memory usage
2. Set up uptime monitoring
3. Monitor database performance

## Troubleshooting

### Common Issues

#### 1. Static Files Not Loading
```bash
# Collect static files during build
python manage.py collectstatic --noinput
```

#### 2. Database Connection Issues
- SQLite database is created automatically
- Ensure migrations have been run
- Check file permissions if database errors occur

#### 3. Secret Key Errors
- Generate a new secret key (50+ characters)
- Update environment variable
- Restart the application

#### 4. ALLOWED_HOSTS Error
- Add your domain to ALLOWED_HOSTS
- Include both with and without 'www'
- Include the DigitalOcean app URL

### Generate Secret Key
```python
# Run this in Python to generate a secret key
import secrets
import string

alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
secret_key = ''.join(secrets.choice(alphabet) for i in range(50))
print(secret_key)
```

## Cost Estimation

### Minimum Setup
- Web Service (Basic): $5/month
- **Total: $5/month** (SQLite included)

### Production Setup
- Web Service (Professional): $12/month
- **Total: $12/month** (SQLite included)

## Security Best Practices

1. **Environment Variables**: Never commit secrets to GitHub
2. **HTTPS**: Always enabled on DigitalOcean App Platform
3. **Regular Updates**: Keep dependencies updated
4. **Monitoring**: Set up error tracking and monitoring
5. **Backups**: Enable automatic database backups

## Support and Resources

- [DigitalOcean App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Tarbiyat GitHub Repository](https://github.com/codeforpakistan/tarbiyat)

## Next Steps

After successful deployment:

1. **Configure Email**: Set up SMTP for password reset functionality
2. **Add Monitoring**: Implement error tracking (Sentry, etc.)
3. **Backup Strategy**: Set up regular database backups
4. **Performance Optimization**: Monitor and optimize slow queries
5. **Security Audit**: Regular security reviews and updates

---

For additional support, please create an issue in the [GitHub repository](https://github.com/codeforpakistan/tarbiyat/issues) or contact Code for Pakistan.
