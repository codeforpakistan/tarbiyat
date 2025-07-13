from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

def get_user_type(user):
    """Helper function to get user type from groups"""
    if not user.is_authenticated:
        return None
    user_groups = user.groups.values_list('name', flat=True)
    for group_name in ['student', 'mentor', 'teacher', 'official']:
        if group_name in user_groups:
            return group_name
    return None

class ProfileCompletionMiddleware:
    """
    Middleware to redirect users with incomplete profiles to complete their profile
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that should be accessible even with incomplete profile
        allowed_paths = [
            '/complete-profile/',
            '/accounts/',
            '/admin/',
            '/',  # Allow access to home page
        ]
        
        # Check if user is authenticated and has incomplete profile
        if (request.user.is_authenticated and 
            not get_user_type(request.user) and 
            not any(request.path.startswith(path) for path in allowed_paths)):
            
            return redirect('complete_profile')
        
        response = self.get_response(request)
        return response
