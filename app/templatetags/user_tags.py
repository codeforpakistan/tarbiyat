from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def get_user_type(user):
    """Template filter to get user type from groups"""
    if not user.is_authenticated:
        return None
    user_groups = user.groups.values_list('name', flat=True)
    for group_name in ['student', 'mentor', 'teacher', 'official']:
        if group_name in user_groups:
            return group_name
    return None

@register.filter
def has_user_type(user):
    """Template filter to check if user has any user type"""
    return get_user_type(user) is not None
