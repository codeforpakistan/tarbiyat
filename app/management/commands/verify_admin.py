from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()


class Command(BaseCommand):
    help = 'Verify admin user email address'

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(username='admin')
            
            # Get or create email address for admin
            email_address, created = EmailAddress.objects.get_or_create(
                user=admin,
                email=admin.email,
                defaults={
                    'verified': True,
                    'primary': True
                }
            )
            
            if not created and not email_address.verified:
                email_address.verified = True
                email_address.primary = True
                email_address.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Admin email {admin.email} has been verified')
                )
            elif created:
                self.stdout.write(
                    self.style.SUCCESS(f'Admin email {admin.email} created and verified')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Admin email {admin.email} was already verified')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user not found. Please run seed command first.')
            )
