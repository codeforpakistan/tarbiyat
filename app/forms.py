from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth.models import User, Group
from django.forms import formset_factory
from typing import TYPE_CHECKING
from .models import StudentWeeklyActivityLog, StudentWeeklyActivity

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

class StudentWeeklyActivityForm(forms.ModelForm):
    """Form for individual weekly activities"""
    class Meta:
        model = StudentWeeklyActivity
        fields = ['task_description', 'hours_spent', 'date_performed']
        widgets = {
            'task_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Describe the task or activity you performed...'
            }),
            'hours_spent': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'step': '0.1',
                'min': '0',
                'max': '60',
                'placeholder': '0.0'
            }),
            'date_performed': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
        }

class StudentWeeklyActivityLogForm(forms.ModelForm):
    """Form for weekly activity log header"""
    class Meta:
        model = StudentWeeklyActivityLog
        fields = ['week_starting']
        widgets = {
            'week_starting': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
        }

# Create a formset for multiple activities
StudentWeeklyActivityFormSet = formset_factory(
    StudentWeeklyActivityForm,
    extra=3,  # Start with 3 empty forms
    min_num=1,  # At least 1 activity required
    validate_min=True,
    can_delete=True
)
