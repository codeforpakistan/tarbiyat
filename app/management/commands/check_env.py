from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config

class Command(BaseCommand):
    help = 'Check environment variables configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Environment Variables Check:'))
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'SECRET_KEY set: {"Yes" if settings.SECRET_KEY else "No"}')
        self.stdout.write(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
        self.stdout.write(f'DATABASE: {settings.DATABASES["default"]["ENGINE"]}')
        
        # Check email settings
        self.stdout.write(f'Email Backend: {settings.EMAIL_BACKEND}')
        
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('Running in DEBUG mode'))
        else:
            self.stdout.write(self.style.SUCCESS('Running in PRODUCTION mode'))
            
        self.stdout.write(self.style.SUCCESS('Environment configuration check complete!'))
