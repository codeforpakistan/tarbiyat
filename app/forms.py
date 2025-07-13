from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth.models import User, Group
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest

class CustomSignupForm(SignupForm):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('teacher', 'Teacher'),
        ('official', 'Official'),
    ]
    
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label='I am a')
    
    def save(self, request: 'HttpRequest') -> 'User':
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # Add user to the appropriate group
        user_type = self.cleaned_data['user_type']
        group, created = Group.objects.get_or_create(name=user_type)
        user.groups.add(group)
        
        user.save()
        return user  # type: ignore
