from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from allauth.account.utils import user_username
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def pre_social_login(self, request, sociallogin):
        """
        This is called after a user successfully authenticates via a social provider,
        but before the login is actually processed.
        """
        # If user is already authenticated, skip
        if request.user.is_authenticated:
            return
            
        # If this is a new user (no user attached to social login yet)
        if not sociallogin.is_existing:
            # Set a temporary username from email
            email = sociallogin.account.extra_data.get('email')
            if email:
                username = email.split('@')[0]
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                sociallogin.user.username = username
                
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and check if user_type needs to be set
        """
        user = super().save_user(request, sociallogin, form)
        
        # Check if user is in any group, if not, store info for profile completion
        user_groups = user.groups.values_list('name', flat=True)
        has_user_type = any(group in ['student', 'mentor', 'teacher', 'official'] for group in user_groups)
        
        if not has_user_type:
            # Store the user ID in session for profile completion
            request.session['incomplete_profile_user_id'] = user.id
            
        return user
        
    def get_signup_form_data(self, request, sociallogin):
        """
        Extract data from social login to pre-populate signup form
        """
        data = {}
        user_data = sociallogin.account.extra_data
        
        if 'given_name' in user_data:
            data['first_name'] = user_data['given_name']
        if 'family_name' in user_data:
            data['last_name'] = user_data['family_name']
        if 'email' in user_data:
            data['email'] = user_data['email']
            
        return data
