from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth.models import User, Group
from django.forms import modelformset_factory
from typing import TYPE_CHECKING
from .models import (
    Log, Entry, Student, Mentor,
    Teacher, Official, Institute, Company, Position,
    Application, Internship, Report,
    Assessment, Notification, Evaluation
)

if TYPE_CHECKING:
    from django.http import HttpRequest

# Base widget classes for consistent styling
class TailwindTextInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({
            'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
        super().__init__(*args, **kwargs)

class TailwindTextarea(forms.Textarea):
    def __init__(self, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({
            'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 4
        })
        super().__init__(*args, **kwargs)

class TailwindSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({
            'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
        super().__init__(*args, **kwargs)

class TailwindNumberInput(forms.NumberInput):
    def __init__(self, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({
            'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
        super().__init__(*args, **kwargs)

class TailwindDateInput(forms.DateInput):
    def __init__(self, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({
            'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        })
        kwargs['format'] = '%Y-%m-%d'  # Set the correct format for HTML5 date input
        super().__init__(*args, **kwargs)

class TailwindEmailInput(forms.EmailInput):
    def __init__(self, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({
            'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
        super().__init__(*args, **kwargs)

class TailwindFileInput(forms.FileInput):
    def __init__(self, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({
            'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
        super().__init__(*args, **kwargs)

# Authentication Forms
class CustomSignupForm(SignupForm):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('teacher', 'Teacher'),
        ('official', 'Official'),
    ]
    
    first_name = forms.CharField(max_length=30, label='First Name', widget=TailwindTextInput())
    last_name = forms.CharField(max_length=30, label='Last Name', widget=TailwindTextInput())
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label='I am a', widget=TailwindSelect())
    
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

class ProfileCompletionForm(forms.Form):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('mentor', 'Mentor'), 
        ('teacher', 'Teacher'),
        ('official', 'Official'),
    ]
    
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label='I am a', widget=TailwindSelect())

# Profile Forms
class StudentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='First Name', widget=TailwindTextInput())
    last_name = forms.CharField(max_length=30, label='Last Name', widget=TailwindTextInput())
    email = forms.EmailField(label='Email Address', widget=TailwindEmailInput())
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'major', 'semester_of_study', 'gpa', 'skills',
            'phone', 'portfolio_url', 'resume', 'institute', 'expected_graduation'
        ]
        widgets = {
            'student_id': TailwindTextInput(),
            'major': TailwindTextInput(),
            'semester_of_study': TailwindSelect(),
            'gpa': TailwindNumberInput(attrs={'step': '0.01', 'min': '0', 'max': '4'}),
            'skills': TailwindTextarea(attrs={'rows': 3, 'placeholder': 'List your skills, separated by commas'}),
            'phone': TailwindTextInput(attrs={'placeholder': '+92-300-1234567'}),
            'portfolio_url': TailwindTextInput(attrs={'placeholder': 'https://yourportfolio.com'}),
            'resume': TailwindFileInput(),
            'institute': TailwindSelect(),
            'expected_graduation': TailwindDateInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Set initial values for user fields
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            
            # Also set the value attribute on the widget for immediate display
            self.fields['first_name'].widget.attrs['value'] = self.user.first_name or ''
            self.fields['last_name'].widget.attrs['value'] = self.user.last_name or ''
            self.fields['email'].widget.attrs['value'] = self.user.email or ''

    def save(self, commit=True, user=None):
        student = super().save(commit=False)
        # Use the user passed to save method, or fall back to the one from __init__
        user_to_update = user or self.user
        if user_to_update:
            user_to_update.first_name = self.cleaned_data['first_name']
            user_to_update.last_name = self.cleaned_data['last_name']
            user_to_update.email = self.cleaned_data['email']
            if commit:
                user_to_update.save()
        if commit:
            student.save()
        return student

class MentorForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='First Name', widget=TailwindTextInput())
    last_name = forms.CharField(max_length=30, label='Last Name', widget=TailwindTextInput())
    email = forms.EmailField(label='Email Address', widget=TailwindEmailInput())
    
    class Meta:
        model = Mentor
        fields = [
            'job_title', 'department', 'experience_years', 'specialization',
            'phone', 'company'
        ]
        widgets = {
            'job_title': TailwindTextInput(),
            'department': TailwindTextInput(),
            'experience_years': TailwindNumberInput(attrs={'min': '0'}),
            'specialization': TailwindTextarea(attrs={'rows': 3, 'placeholder': 'Your areas of specialization'}),
            'phone': TailwindTextInput(attrs={'placeholder': '+92-300-1234567'}),
            'company': TailwindSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Set initial values for user fields
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            
            # Also set the value attribute on the widget for immediate display
            self.fields['first_name'].widget.attrs['value'] = self.user.first_name or ''
            self.fields['last_name'].widget.attrs['value'] = self.user.last_name or ''
            self.fields['email'].widget.attrs['value'] = self.user.email or ''

    def save(self, commit=True, user=None):
        mentor = super().save(commit=False)
        # Use the user passed to save method, or fall back to the one from __init__
        user_to_update = user or self.user
        if user_to_update:
            user_to_update.first_name = self.cleaned_data['first_name']
            user_to_update.last_name = self.cleaned_data['last_name']
            user_to_update.email = self.cleaned_data['email']
            if commit:
                user_to_update.save()
        if commit:
            mentor.save()
        return mentor

class TeacherForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='First Name', widget=TailwindTextInput())
    last_name = forms.CharField(max_length=30, label='Last Name', widget=TailwindTextInput())
    email = forms.EmailField(label='Email Address', widget=TailwindEmailInput())
    
    class Meta:
        model = Teacher
        fields = [
            'title', 'department', 'employee_id', 'phone', 'institute'
        ]
        widgets = {
            'title': TailwindTextInput(attrs={'placeholder': 'Professor, Assistant Professor, etc.'}),
            'department': TailwindTextInput(),
            'employee_id': TailwindTextInput(attrs={'placeholder': 'Employee ID'}),
            'phone': TailwindTextInput(attrs={'placeholder': '+92-300-1234567'}),
            'institute': TailwindSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Set initial values for user fields
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            
            # Also set the value attribute on the widget for immediate display
            self.fields['first_name'].widget.attrs['value'] = self.user.first_name or ''
            self.fields['last_name'].widget.attrs['value'] = self.user.last_name or ''
            self.fields['email'].widget.attrs['value'] = self.user.email or ''

    def save(self, commit=True, user=None):
        teacher = super().save(commit=False)
        # Use the user passed to save method, or fall back to the one from __init__
        user_to_update = user or self.user
        if user_to_update:
            user_to_update.first_name = self.cleaned_data['first_name']
            user_to_update.last_name = self.cleaned_data['last_name']
            user_to_update.email = self.cleaned_data['email']
            if commit:
                user_to_update.save()
        if commit:
            teacher.save()
        return teacher

class OfficialForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='First Name', widget=TailwindTextInput())
    last_name = forms.CharField(max_length=30, label='Last Name', widget=TailwindTextInput())
    email = forms.EmailField(label='Email Address', widget=TailwindEmailInput())
    
    class Meta:
        model = Official
        fields = [
            'department', 'job_title', 'employee_id', 'phone',
            'approval_authority_level'
        ]
        widgets = {
            'department': TailwindTextInput(),
            'job_title': TailwindTextInput(),
            'employee_id': TailwindTextInput(),
            'phone': TailwindTextInput(attrs={'placeholder': '+92-300-1234567'}),
            'approval_authority_level': TailwindSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Set initial values for user fields
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            
            # Also set the value attribute on the widget for immediate display
            self.fields['first_name'].widget.attrs['value'] = self.user.first_name or ''
            self.fields['last_name'].widget.attrs['value'] = self.user.last_name or ''
            self.fields['email'].widget.attrs['value'] = self.user.email or ''

    def save(self, commit=True, user=None):
        official = super().save(commit=False)
        # Use the user passed to save method, or fall back to the one from __init__
        user_to_update = user or self.user
        if user_to_update:
            user_to_update.first_name = self.cleaned_data['first_name']
            user_to_update.last_name = self.cleaned_data['last_name']
            user_to_update.email = self.cleaned_data['email']
            if commit:
                user_to_update.save()
        if commit:
            official.save()
        return official

# Organization Forms
class InstituteForm(forms.ModelForm):
    class Meta:
        model = Institute
        fields = [
            'name', 'address', 'district', 'website', 'contact_email', 
            'phone', 'email_domain', 'male_students_count', 'female_students_count',
            'degree_programs', 'postgraduate_programs', 'management_programs',
            'primary_education_level'
        ]
        widgets = {
            'name': TailwindTextInput(),
            'address': TailwindTextarea(attrs={'rows': 3}),
            'district': TailwindSelect(),
            'website': TailwindTextInput(attrs={'placeholder': 'https://institute.edu.pk'}),
            'contact_email': TailwindEmailInput(),
            'phone': TailwindTextInput(attrs={'placeholder': '+92-42-1234567'}),
            'email_domain': TailwindTextInput(attrs={'placeholder': 'institute.edu.pk'}),
            'male_students_count': TailwindNumberInput(attrs={'min': '0'}),
            'female_students_count': TailwindNumberInput(attrs={'min': '0'}),
            'degree_programs': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'postgraduate_programs': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'management_programs': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'primary_education_level': TailwindSelect(),
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'description', 'industry', 'address',
            'website', 'contact_email', 'phone', 'email_domain'
        ]
        widgets = {
            'name': TailwindTextInput(),
            'description': TailwindTextarea(attrs={'rows': 4}),
            'industry': TailwindTextInput(),
            'address': TailwindTextarea(attrs={'rows': 3}),
            'website': TailwindTextInput(attrs={'placeholder': 'https://company.com'}),
            'contact_email': TailwindEmailInput(),
            'phone': TailwindTextInput(attrs={'placeholder': '+92-21-1234567'}),
            'email_domain': TailwindTextInput(attrs={'placeholder': 'company.com'}),
        }

# Internship-Related Forms
class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = [
            'title', 'description', 'requirements', 'duration',
            'stipend', 'skills_required', 'start_date', 'end_date',
            'max_students', 'is_active'
        ]
        widgets = {
            'title': TailwindTextInput(),
            'description': TailwindTextarea(attrs={'rows': 5}),
            'requirements': TailwindTextarea(attrs={'rows': 4}),
            'duration': TailwindSelect(),
            'stipend': TailwindNumberInput(attrs={'min': '0', 'step': '0.01'}),
            'skills_required': TailwindTextarea(attrs={'rows': 3, 'placeholder': 'Required skills, separated by commas'}),
            'start_date': TailwindDateInput(),
            'end_date': TailwindDateInput(),
            'max_students': TailwindNumberInput(attrs={'min': '1', 'value': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter']
        widgets = {
            'cover_letter': TailwindTextarea(attrs={
                'rows': 6, 
                'placeholder': 'Write a compelling cover letter explaining why you are interested in this position...'
            }),
        }

class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = [
            'start_date', 'end_date', 'status', 'final_grade'
        ]
        widgets = {
            'start_date': TailwindDateInput(),
            'end_date': TailwindDateInput(),
            'status': TailwindSelect(),
            'final_grade': TailwindTextInput(attrs={'placeholder': 'A, B, C, etc.'}),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            'report_month', 'tasks_performed', 'tasks_performed_score',
            'learning_experience', 'learning_experience_score', 'challenges', 
            'challenges_score', 'additional_comments'
        ]
        widgets = {
            'report_month': TailwindDateInput(),
            'tasks_performed': TailwindTextarea(attrs={'rows': 4, 'placeholder': 'Describe the tasks completed this month'}),
            'tasks_performed_score': TailwindNumberInput(attrs={'min': '0', 'max': '10'}),
            'learning_experience': TailwindTextarea(attrs={'rows': 3, 'placeholder': 'Skills and knowledge gained'}),
            'learning_experience_score': TailwindNumberInput(attrs={'min': '0', 'max': '10'}),
            'challenges': TailwindTextarea(attrs={'rows': 3, 'placeholder': 'Challenges faced and how tackled'}),
            'challenges_score': TailwindNumberInput(attrs={'min': '0', 'max': '10'}),
            'additional_comments': TailwindTextarea(attrs={'rows': 3, 'placeholder': 'Any additional comments'}),
        }

class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = [
            'technical_skills', 'work_quality', 'problem_solving', 'teamwork',
            'professionalism', 'performance_benefits', 'observed_development',
            'intern_strengths', 'areas_for_improvement', 'intern_rating',
            'program_rating', 'program_improvement_suggestions'
        ]
        widgets = {
            'technical_skills': TailwindSelect(),
            'work_quality': TailwindSelect(),
            'problem_solving': TailwindSelect(),
            'teamwork': TailwindSelect(),
            'professionalism': TailwindSelect(),
            'performance_benefits': TailwindTextarea(attrs={'rows': 4}),
            'observed_development': TailwindTextarea(attrs={'rows': 4}),
            'intern_strengths': TailwindTextarea(attrs={'rows': 4}),
            'areas_for_improvement': TailwindTextarea(attrs={'rows': 4}),
            'intern_rating': TailwindSelect(),
            'program_rating': TailwindSelect(),
            'program_improvement_suggestions': TailwindTextarea(attrs={'rows': 4}),
        }

# Evaluation Forms
class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = [
            'evaluation_date', 'discussion_notes', 'academic_alignment', 
            'recommendations', 'overall_rating'
        ]
        widgets = {
            'evaluation_date': TailwindDateInput(),
            'discussion_notes': TailwindTextarea(attrs={'rows': 4, 'placeholder': 'Notes from discussions with student and mentor'}),
            'academic_alignment': TailwindTextarea(attrs={'rows': 3, 'placeholder': 'How well does the internship align with academic objectives?'}),
            'recommendations': TailwindTextarea(attrs={'rows': 3, 'placeholder': 'Recommendations for future internships or improvements'}),
            'overall_rating': TailwindSelect(),
        }

# Activity Logging Forms (Already existed, keeping them)
class EntryForm(forms.ModelForm):
    """Form for simple daily activity entries"""
    class Meta:
        model = Entry
        fields = ['date', 'description']
        widgets = {
            'date': TailwindDateInput(),
            'description': TailwindTextarea(attrs={
                'rows': 3,
                'placeholder': 'What did you do on this day? (e.g., "Worked on database design", "Attended team meeting", "Fixed login bugs")'
            }),
        }
        labels = {
            'date': 'Date',
            'description': 'What did you do?',
        }

class LogForm(forms.ModelForm):
    """Form for weekly activity log"""
    class Meta:
        model = Log
        fields = ['week_starting']
        widgets = {
            'week_starting': TailwindDateInput(),
        }
        labels = {
            'week_starting': 'Week Starting (Monday)',
        }
        help_texts = {
            'week_starting': 'Select the Monday of the week you want to report',
        }

# Notification Form
class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type']
        widgets = {
            'title': TailwindTextInput(),
            'message': TailwindTextarea(attrs={'rows': 4}),
            'notification_type': TailwindSelect(),
        }

EntryFormSet = modelformset_factory(
    Entry,
    form=EntryForm,
    extra=1,  # Start with just one entry
    min_num=1,  # At least 1 activity required
    validate_min=True,
    can_delete=True,
    max_num=7  # Maximum 7 days per week
)

# Search and Filter Forms
class PositionSearchForm(forms.Form):
    """Form for searching and filtering internship positions"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': 'Search by title, company, or description...'}),
        label="Search Positions"
    )
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(registration_status='approved').order_by('name'),
        required=False,
        empty_label="All Companies",
        widget=TailwindSelect(),
        label="Filter by Company"
    )
    duration = forms.ChoiceField(
        choices=[('', 'All Durations'), ('1', '1 month'), ('3', '3 months'), ('6', '6 months'), ('12', '12 months')],
        required=False,
        widget=TailwindSelect(),
        label="Filter by Duration"
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': 'Enter city or region...'}),
        label="Location"
    )
    remote_allowed = forms.BooleanField(
        required=False,
        label="Remote Allowed"
    )
    min_stipend = forms.IntegerField(
        required=False,
        widget=TailwindNumberInput(attrs={'placeholder': 'Min stipend'}),
        label="Minimum Stipend"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update company queryset to only include approved companies
        try:
            self.fields['company'].queryset = Company.objects.filter(
                registration_status='approved'
            ).order_by('name')
        except Exception:
            pass

class StudentSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': 'Search students...'})
    )
    institute = forms.ModelChoiceField(
        queryset=Institute.objects.all(),
        required=False,
        widget=TailwindSelect()
    )
    major = forms.CharField(
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': 'Major'})
    )
    year = forms.ChoiceField(
        choices=[('', 'All Semesters')] + list(Student.SEMESTER_CHOICES),
        required=False,
        widget=TailwindSelect()
    )

# Bulk Action Forms
class BulkActionForm(forms.Form):
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('delete', 'Delete'),
    ]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=TailwindSelect())
    selected_items = forms.CharField(widget=forms.HiddenInput())

class CompanyBulkActionForm(BulkActionForm):
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('suspend', 'Suspend'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=TailwindSelect())

class InstituteBulkActionForm(BulkActionForm):
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('verify_domain', 'Verify Domain'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=TailwindSelect())

# =============================================================================
# SEARCH AND ADMIN FORMS
# =============================================================================

class CompanyAdminForm(forms.Form):
    """Form for searching and filtering companies in admin panel"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': "Search by name, industry, or email..."}),
        label="Search Companies"
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('suspended', 'Suspended'),
        ],
        required=False,
        widget=TailwindSelect(),
        label="Registration Status"
    )
    domain_verified = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Domain Verified'),
            ('false', 'Domain Not Verified')
        ],
        required=False,
        widget=TailwindSelect(),
        label="Domain Verification"
    )
    industry = forms.CharField(
        max_length=100,
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': "Filter by industry..."}),
        label="Industry"
    )
    created_after = forms.DateField(
        required=False,
        widget=TailwindDateInput(),
        label="Registered After"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        # Convert string boolean values to actual booleans for filtering
        domain_verified = cleaned_data.get('domain_verified')
        if domain_verified == 'true':
            cleaned_data['domain_verified'] = True
        elif domain_verified == 'false':
            cleaned_data['domain_verified'] = False
        else:
            cleaned_data['domain_verified'] = None
        return cleaned_data

class InstituteAdminForm(forms.Form):
    """Form for searching and filtering institutes in admin panel"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': "Search by name, email, or address..."}),
        label="Search Institutes"
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('suspended', 'Suspended'),
        ],
        required=False,
        widget=TailwindSelect(),
        label="Registration Status"
    )
    domain_verified = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Domain Verified'),
            ('false', 'Domain Not Verified')
        ],
        required=False,
        widget=TailwindSelect(),
        label="Domain Verification"
    )
    institute_type = forms.CharField(
        max_length=100,
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': "Filter by institute type..."}),
        label="Institute Type"
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=TailwindTextInput(attrs={'placeholder': "Filter by city..."}),
        label="City"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        # Convert string boolean values to actual booleans for filtering
        domain_verified = cleaned_data.get('domain_verified')
        if domain_verified == 'true':
            cleaned_data['domain_verified'] = True
        elif domain_verified == 'false':
            cleaned_data['domain_verified'] = False
        else:
            cleaned_data['domain_verified'] = None
        return cleaned_data
