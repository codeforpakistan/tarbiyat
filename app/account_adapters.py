from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for django-allauth to handle custom business logic
    """
    
    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.
        """
        return getattr(settings, 'ACCOUNT_ALLOW_REGISTRATION', True)
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.
        """
        # Check if user is superuser (admin) first
        if request.user.is_superuser:
            # Admins get redirected to Django admin interface
            return '/admin/'
        # Check if user has a profile and redirect accordingly
        elif hasattr(request.user, 'studentprofile'):
            return reverse('dashboard')
        elif hasattr(request.user, 'mentorprofile'):
            return reverse('dashboard')  
        elif hasattr(request.user, 'teacherprofile'):
            return reverse('dashboard')
        elif hasattr(request.user, 'officialprofile'):
            return reverse('dashboard')
        else:
            # Default redirect for users without profiles
            return reverse('home')
    
    def get_signup_redirect_url(self, request):
        """
        Returns the default URL to redirect to after signing up.
        """
        # After signup, redirect to home page or login
        return reverse('account_login')
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Customize email confirmation sending if needed
        """
        # Use the default behavior for now
        super().send_confirmation_mail(request, emailconfirmation, signup)