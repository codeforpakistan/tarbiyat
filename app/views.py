from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import (
    StudentProfile, MentorProfile, TeacherProfile, OfficialProfile,
    InternshipPosition, InternshipApplication, Internship, Company, Institute, 
    Notification, OrganizationRegistrationRequest
)
from django import forms
from .utils import (
    validate_user_organization_membership, 
    get_available_institutes_for_user, 
    get_available_companies_for_user
)

def get_user_type(user):
    """Helper function to get user type from groups"""
    if not user.is_authenticated:
        return None
    
    # Check if user is superuser (admin) first
    if user.is_superuser:
        return 'admin'
        
    user_groups = user.groups.values_list('name', flat=True)
    for group_name in ['student', 'mentor', 'teacher', 'official']:
        if group_name in user_groups:
            return group_name
    return None

def home(request):
    """Homepage with different views for different user types"""
    if request.user.is_authenticated:
        user_type = get_user_type(request.user)
        # Check if user needs to complete profile - show a message instead of redirect
        if not user_type:
            # Don't redirect here, let them see the homepage with a completion prompt
            pass
        elif user_type == 'admin':
            return redirect('/admin/')
        elif user_type == 'student':
            return redirect('student_dashboard')
        elif user_type == 'mentor':
            return redirect('mentor_dashboard')
        elif user_type == 'teacher':
            return redirect('teacher_dashboard')
        elif user_type == 'official':
            return redirect('official_dashboard')
    
    context = {
        'total_companies': Company.objects.filter(is_verified=True).count(),
        'total_students': StudentProfile.objects.count(),
        'active_internships': Internship.objects.filter(status='active').count(),
        'total_positions': InternshipPosition.objects.filter(is_active=True).count(),
    }
    return render(request, 'app/home.html', context)

@login_required
def student_dashboard(request):
    """Student dashboard with internship opportunities and applications"""
    user_type = get_user_type(request.user)
    # Check if user has incomplete profile
    if not user_type:
        return redirect('complete_profile')
        
    if user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('home')
    
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.warning(request, 'Please complete your student profile first.')
        return redirect('create_student_profile')
    
    # Get student's applications
    applications = InternshipApplication.objects.filter(student=student_profile).order_by('-applied_at')
    
    # Get available positions
    available_positions = InternshipPosition.objects.filter(
        is_active=True,
        start_date__gte=date.today()
    ).exclude(
        applications__student=student_profile
    ).order_by('start_date')[:5]
    
    # Get current internship if any
    current_internship = Internship.objects.filter(
        student=student_profile,
        status='active'
    ).first()
    
    context = {
        'student_profile': student_profile,
        'applications': applications[:5],
        'available_positions': available_positions,
        'current_internship': current_internship,
        'total_applications': applications.count(),
        'profile_completion': student_profile.get_profile_completion(),
        'completion_status': student_profile.get_completion_status(),
    }
    return render(request, 'app/student_dashboard.html', context)

@login_required
def mentor_dashboard(request):
    """Mentor dashboard for managing applications and internships"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_mentor_profile')
    
    # Get mentor's positions and applications
    positions = InternshipPosition.objects.filter(mentor=mentor_profile)
    pending_applications = InternshipApplication.objects.filter(
        position__mentor=mentor_profile,
        status__in=['pending', 'under_review']
    ).order_by('-applied_at')
    
    # Get active internships
    active_internships = Internship.objects.filter(
        mentor=mentor_profile,
        status='active'
    )
    
    context = {
        'mentor_profile': mentor_profile,
        'positions': positions,
        'pending_applications': pending_applications[:10],
        'active_internships': active_internships,
        'total_positions': positions.count(),
        'total_applications': pending_applications.count(),
    }
    return render(request, 'app/mentor_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Teacher dashboard for monitoring student internships"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.warning(request, 'Please complete your teacher profile first.')
        return redirect('create_teacher_profile')
    
    # Get students from same institute
    institute_students = StudentProfile.objects.filter(
        institute=teacher_profile.institute
    )
    
    # Get active internships for institute students
    active_internships = Internship.objects.filter(
        student__institute=teacher_profile.institute,
        status='active'
    )
    
    context = {
        'teacher_profile': teacher_profile,
        'institute_students': institute_students.count(),
        'active_internships': active_internships,
        'students_with_internships': active_internships.count(),
    }
    return render(request, 'app/teacher_dashboard.html', context)

@login_required
def official_dashboard(request):
    """Official dashboard with system overview and statistics"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    # System statistics
    stats = {
        'total_students': StudentProfile.objects.count(),
        'total_mentors': MentorProfile.objects.count(),
        'total_companies': Company.objects.count(),
        'verified_companies': Company.objects.filter(is_verified=True).count(),
        'total_positions': InternshipPosition.objects.count(),
        'active_positions': InternshipPosition.objects.filter(is_active=True).count(),
        'total_applications': InternshipApplication.objects.count(),
        'pending_applications': InternshipApplication.objects.filter(status='pending').count(),
        'active_internships': Internship.objects.filter(status='active').count(),
        'completed_internships': Internship.objects.filter(status='completed').count(),
    }
    
    # Recent activity
    recent_applications = InternshipApplication.objects.order_by('-applied_at')[:10]
    recent_internships = Internship.objects.order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'recent_applications': recent_applications,
        'recent_internships': recent_internships,
    }
    return render(request, 'app/official_dashboard.html', context)

@login_required
def manage_companies(request):
    """Official view to manage companies"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    # Get all companies with filtering options
    companies = Company.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(industry__icontains=search_query) |
            Q(contact_email__icontains=search_query)
        )
    
    # Filter by registration status
    status_filter = request.GET.get('status')
    if status_filter:
        companies = companies.filter(registration_status=status_filter)
    
    # Filter by domain verification
    domain_filter = request.GET.get('domain_verified')
    if domain_filter == 'true':
        companies = companies.filter(domain_verified=True)
    elif domain_filter == 'false':
        companies = companies.filter(domain_verified=False)
    
    # Pagination
    paginator = Paginator(companies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    stats = {
        'total': Company.objects.count(),
        'pending': Company.objects.filter(registration_status='pending').count(),
        'approved': Company.objects.filter(registration_status='approved').count(),
        'rejected': Company.objects.filter(registration_status='rejected').count(),
        'domain_verified': Company.objects.filter(domain_verified=True).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'domain_filter': domain_filter,
        'stats': stats,
        'status_choices': Company._meta.get_field('registration_status').choices,
    }
    return render(request, 'app/manage_companies.html', context)

@login_required
def manage_institutes(request):
    """Official view to manage institutes"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    # Get all institutes with filtering options
    institutes = Institute.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        institutes = institutes.filter(
            Q(name__icontains=search_query) |
            Q(contact_email__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    # Filter by registration status
    status_filter = request.GET.get('status')
    if status_filter:
        institutes = institutes.filter(registration_status=status_filter)
    
    # Filter by domain verification
    domain_filter = request.GET.get('domain_verified')
    if domain_filter == 'true':
        institutes = institutes.filter(domain_verified=True)
    elif domain_filter == 'false':
        institutes = institutes.filter(domain_verified=False)
    
    # Pagination
    paginator = Paginator(institutes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    stats = {
        'total': Institute.objects.count(),
        'pending': Institute.objects.filter(registration_status='pending').count(),
        'approved': Institute.objects.filter(registration_status='approved').count(),
        'rejected': Institute.objects.filter(registration_status='rejected').count(),
        'domain_verified': Institute.objects.filter(domain_verified=True).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'domain_filter': domain_filter,
        'stats': stats,
        'status_choices': Institute._meta.get_field('registration_status').choices,
    }
    return render(request, 'app/manage_institutes.html', context)

@login_required
def company_detail_official(request, company_nanoid):
    """Official view to manage a specific company"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    company = get_object_or_404(Company, nanoid=company_nanoid)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '').strip()
        
        if action == 'approve':
            company.registration_status = 'approved'
            company.approved_by = request.user.official_profile
            company.approved_at = timezone.now()
            company.registration_notes = notes
            company.save()
            messages.success(request, f'Company "{company.name}" has been approved.')
            
        elif action == 'reject':
            company.registration_status = 'rejected'
            company.approved_by = request.user.official_profile
            company.approved_at = timezone.now()
            company.registration_notes = notes
            company.save()
            messages.success(request, f'Company "{company.name}" has been rejected.')
            
        elif action == 'suspend':
            company.registration_status = 'suspended'
            company.registration_notes = notes
            company.save()
            messages.success(request, f'Company "{company.name}" has been suspended.')
            
        elif action == 'verify_domain':
            company.domain_verified = True
            company.save()
            messages.success(request, f'Domain verification completed for "{company.name}".')
            
        elif action == 'unverify_domain':
            company.domain_verified = False
            company.save()
            messages.success(request, f'Domain verification removed for "{company.name}".')
        
        return redirect('company_detail_official', company_nanoid=company_nanoid)
    
    # Get related data
    mentors = MentorProfile.objects.filter(company=company)
    positions = InternshipPosition.objects.filter(company=company).order_by('-created_at')
    
    context = {
        'company': company,
        'mentors': mentors,
        'positions': positions,
    }
    return render(request, 'app/company_detail_official.html', context)

@login_required
def institute_detail_official(request, institute_nanoid):
    """Official view to manage a specific institute"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    institute = get_object_or_404(Institute, nanoid=institute_nanoid)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '').strip()
        
        if action == 'approve':
            institute.registration_status = 'approved'
            institute.approved_by = request.user.official_profile
            institute.approved_at = timezone.now()
            institute.registration_notes = notes
            institute.save()
            messages.success(request, f'Institute "{institute.name}" has been approved.')
            
        elif action == 'reject':
            institute.registration_status = 'rejected'
            institute.approved_by = request.user.official_profile
            institute.approved_at = timezone.now()
            institute.registration_notes = notes
            institute.save()
            messages.success(request, f'Institute "{institute.name}" has been rejected.')
            
        elif action == 'suspend':
            institute.registration_status = 'suspended'
            institute.registration_notes = notes
            institute.save()
            messages.success(request, f'Institute "{institute.name}" has been suspended.')
            
        elif action == 'verify_domain':
            institute.domain_verified = True
            institute.save()
            messages.success(request, f'Domain verification completed for "{institute.name}".')
            
        elif action == 'unverify_domain':
            institute.domain_verified = False
            institute.save()
            messages.success(request, f'Domain verification removed for "{institute.name}".')
        
        return redirect('institute_detail_official', institute_nanoid=institute_nanoid)
    
    # Get related data
    teachers = TeacherProfile.objects.filter(institute=institute)
    students = StudentProfile.objects.filter(institute=institute)
    
    context = {
        'institute': institute,
        'teachers': teachers,
        'students': students,
    }
    return render(request, 'app/institute_detail_official.html', context)

def browse_positions(request):
    """Browse available internship positions"""
    positions = InternshipPosition.objects.filter(is_active=True).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        positions = positions.filter(
            Q(title__icontains=search_query) |
            Q(company__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by company
    company_filter = request.GET.get('company')
    if company_filter:
        positions = positions.filter(company_id=company_filter)
    
    # Filter by duration
    duration_filter = request.GET.get('duration')
    if duration_filter:
        positions = positions.filter(duration=duration_filter)
    
    # Pagination
    paginator = Paginator(positions, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    companies = Company.objects.filter(is_verified=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'companies': companies,
        'search_query': search_query,
        'company_filter': company_filter,
        'duration_filter': duration_filter,
    }
    return render(request, 'app/browse_positions.html', context)

def position_detail(request, position_nanoid):
    """View detailed information about a specific internship position"""
    position = get_object_or_404(InternshipPosition, nanoid=position_nanoid, is_active=True)
    
    # Check if current user (if student) has already applied
    user_application = None
    if request.user.is_authenticated and get_user_type(request.user) == 'student':
        try:
            student_profile = request.user.student_profile
            user_application = InternshipApplication.objects.get(
                student=student_profile, position=position
            )
        except (StudentProfile.DoesNotExist, InternshipApplication.DoesNotExist):
            pass
    
    # Calculate number of applications
    total_applications = position.applications.count()
    
    # Get other positions from the same company (max 3)
    related_positions = InternshipPosition.objects.filter(
        company=position.company, 
        is_active=True
    ).exclude(pk=position.pk)[:3]
    
    context = {
        'position': position,
        'user_application': user_application,
        'related_positions': related_positions,
        'total_applications': total_applications,
    }
    return render(request, 'app/position_detail.html', context)

class ProfileCompletionForm(forms.Form):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('teacher', 'Teacher'),
        ('official', 'Official'),
    ]
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label='I am a')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })

def complete_profile(request):
    """Handle profile completion for social auth users"""
    user_id = request.session.get('incomplete_profile_user_id')
    
    if not user_id:
        return redirect('home')
        
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data['user_type']
            # Add user to the appropriate group
            group, created = Group.objects.get_or_create(name=user_type)
            user.groups.add(group)
            
            # Clear the session
            del request.session['incomplete_profile_user_id']
            messages.success(request, 'Profile completed successfully!')
            
            # Redirect based on user type
            if user_type == 'student':
                return redirect('student_dashboard')
            elif user_type == 'mentor':
                return redirect('mentor_dashboard')
            elif user_type == 'teacher':
                return redirect('teacher_dashboard')
            elif user_type == 'official':
                return redirect('official_dashboard')
            else:
                return redirect('home')
    else:
        form = ProfileCompletionForm()
    
    return render(request, 'app/complete_profile.html', {'form': form, 'user': user})

@login_required
def create_student_profile(request):
    """Create student profile"""
    user_type = get_user_type(request.user)
    if user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('home')
    
    # Check if profile already exists
    if hasattr(request.user, 'student_profile'):
        messages.info(request, 'Student profile already exists.')
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        # Simple profile creation - you can enhance this with a proper form
        institute = Institute.objects.first()  # For now, assign first institute
        
        # Set default expected graduation to 2 years from now
        default_graduation = date.today() + timedelta(days=730)  # Approximately 2 years
        
        StudentProfile.objects.create(
            user=request.user,
            institute=institute,
            student_id=f'STU{request.user.id:06d}',
            year_of_study='3',
            major='Computer Science',  # Default major
            gpa=3.0,
            skills='Programming, Problem Solving',  # Default skills
            expected_graduation=default_graduation
        )
        messages.success(request, 'Student profile created successfully!')
        return redirect('student_dashboard')
    
    institutes = Institute.objects.all()
    return render(request, 'app/create_student_profile.html', {'institutes': institutes})

@login_required
def create_mentor_profile(request):
    """Create mentor profile"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    # Check if profile already exists
    if hasattr(request.user, 'mentor_profile'):
        messages.info(request, 'Mentor profile already exists.')
        return redirect('mentor_dashboard')
    
    if request.method == 'POST':
        # Simple profile creation - you can enhance this with a proper form
        company = Company.objects.first()  # For now, assign first company
        MentorProfile.objects.create(
            user=request.user,
            company=company,
            position='Software Engineer',  # Default position
            department='Engineering',
            experience_years=5,
            specialization='Software Development'  # Default specialization
        )
        messages.success(request, 'Mentor profile created successfully!')
        return redirect('mentor_dashboard')
    
    companies = Company.objects.filter(is_verified=True)
    return render(request, 'app/create_mentor_profile.html', {'companies': companies})

@login_required
def create_teacher_profile(request):
    """Create teacher profile"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    # Check if profile already exists
    if hasattr(request.user, 'teacher_profile'):
        messages.info(request, 'Teacher profile already exists.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        # Simple profile creation - you can enhance this with a proper form
        institute = Institute.objects.first()  # For now, assign first institute
        TeacherProfile.objects.create(
            user=request.user,
            institute=institute,
            department='Computer Science',  # Default department
            title='Professor',
            employee_id=f'TEACH{request.user.id:06d}'
        )
        messages.success(request, 'Teacher profile created successfully!')
        return redirect('teacher_dashboard')
    
    institutes = Institute.objects.all()
    return render(request, 'app/create_teacher_profile.html', {'institutes': institutes})

@login_required
def edit_profile(request):
    """Edit user profile based on their type"""
    user_type = get_user_type(request.user)
    
    if user_type == 'student':
        return redirect('edit_student_profile')
    elif user_type == 'mentor':
        return redirect('edit_mentor_profile')
    elif user_type == 'teacher':
        return redirect('edit_teacher_profile')
    elif user_type == 'official':
        return redirect('edit_official_profile')
    else:
        messages.error(request, 'Please complete your profile first.')
        return redirect('complete_profile')

@login_required
def edit_student_profile(request):
    """Edit student profile"""
    user_type = get_user_type(request.user)
    if user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('home')
    
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please create your student profile first.')
        return redirect('create_student_profile')
    
    if request.method == 'POST':
        # Validate institute membership before updating
        new_institute_id = request.POST.get('institute')
        if new_institute_id and new_institute_id != str(profile.institute.pk if profile.institute else ''):
            is_valid, error_message = validate_user_organization_membership(
                request.user, 'institute', int(new_institute_id)
            )
            if not is_valid:
                messages.error(request, error_message or "Invalid organization selection.")
                available_institutes = get_available_institutes_for_user(request.user)
                return render(request, 'app/edit_student_profile.html', {
                    'profile': profile,
                    'institutes': available_institutes,
                    'domain_error': True,
                })
        
        # Update profile fields
        profile.institute_id = new_institute_id
        profile.year_of_study = request.POST.get('year_of_study')
        profile.major = request.POST.get('major')
        profile.gpa = float(request.POST.get('gpa', 0))
        profile.skills = request.POST.get('skills')
        profile.portfolio_url = request.POST.get('portfolio_url', '')
        profile.expected_graduation = request.POST.get('expected_graduation')
        profile.is_available_for_internship = 'available' in request.POST
        
        # Handle resume upload and deletion
        if 'delete_resume' in request.POST and profile.resume:
            # Delete the old resume file
            profile.resume.delete(save=False)
            profile.resume = None
        elif 'resume' in request.FILES:
            resume_file = request.FILES['resume']
            # Check file size (5MB limit)
            if resume_file.size > 5 * 1024 * 1024:  # 5MB in bytes
                messages.error(request, 'Resume file size must be less than 5MB.')
                return render(request, 'app/edit_student_profile.html', {
                    'profile': profile,
                    'institutes': Institute.objects.all(),
                })
            # Delete old resume if exists
            if profile.resume:
                profile.resume.delete(save=False)
            profile.resume = resume_file
        
        # Update user fields
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        
        profile.save()
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('student_dashboard')
    
    available_institutes = get_available_institutes_for_user(request.user)
    context = {
        'profile': profile,
        'institutes': available_institutes,
    }
    return render(request, 'app/edit_student_profile.html', context)

@login_required
def edit_mentor_profile(request):
    """Edit mentor profile"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.error(request, 'Please create your mentor profile first.')
        return redirect('create_mentor_profile')
    
    if request.method == 'POST':
        # Validate company membership before updating
        new_company_id = request.POST.get('company')
        if new_company_id and new_company_id != str(profile.company.pk if profile.company else ''):
            is_valid, error_message = validate_user_organization_membership(
                request.user, 'company', int(new_company_id)
            )
            if not is_valid:
                messages.error(request, error_message or "Invalid organization selection.")
                available_companies = get_available_companies_for_user(request.user)
                return render(request, 'app/edit_mentor_profile.html', {
                    'profile': profile,
                    'companies': available_companies,
                    'domain_error': True,
                })
        
        # Update profile fields
        profile.company_id = new_company_id
        profile.position = request.POST.get('position')
        profile.department = request.POST.get('department')
        profile.experience_years = int(request.POST.get('experience_years', 0))
        profile.specialization = request.POST.get('specialization')
        
        # Update user fields
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        
        profile.save()
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('mentor_dashboard')
    
    available_companies = get_available_companies_for_user(request.user)
    context = {
        'profile': profile,
        'companies': available_companies,
    }
    return render(request, 'app/edit_mentor_profile.html', context)

@login_required
def edit_company(request):
    """Edit company information (for mentors who registered the company)"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.error(request, 'Please create your mentor profile first.')
        return redirect('create_mentor_profile')
    
    if not mentor_profile.can_edit_company():
        messages.error(request, 'You can only edit companies that you registered.')
        return redirect('mentor_dashboard')
    
    company = mentor_profile.company
    
    if request.method == 'POST':
        # Validate required fields
        name = request.POST.get('name', '').strip()
        industry = request.POST.get('industry', '').strip()
        
        if not name or not industry:
            messages.error(request, 'Company name and industry are required fields.')
            context = {
                'company': company,
                'mentor_profile': mentor_profile,
            }
            return render(request, 'app/edit_company.html', context)
        
        # Update company fields
        company.name = name
        company.description = request.POST.get('description', '').strip()
        company.industry = industry
        company.address = request.POST.get('address', '').strip()
        company.website = request.POST.get('website', '').strip() or None
        company.contact_email = request.POST.get('contact_email', '').strip() or None
        company.phone = request.POST.get('phone', '').strip() or None
        company.email_domain = request.POST.get('email_domain', '').strip() or None
        
        # Validate email domain format if provided
        email_domain = company.email_domain
        if email_domain:
            # Remove any @ symbols and convert to lowercase
            email_domain = email_domain.replace('@', '').lower()
            company.email_domain = email_domain
            
            # Basic domain validation
            if not email_domain.replace('-', '').replace('_', '').replace('.', '').isalnum():
                messages.error(request, 'Please enter a valid email domain (e.g., company.com)')
                context = {
                    'company': company,
                    'mentor_profile': mentor_profile,
                }
                return render(request, 'app/edit_company.html', context)
        
        company.save()
        
        messages.success(request, f'Company "{company.name}" updated successfully!')
        return redirect('mentor_dashboard')
    
    context = {
        'company': company,
        'mentor_profile': mentor_profile,
    }
    return render(request, 'app/edit_company.html', context)

@login_required
def edit_teacher_profile(request):
    """Edit teacher profile"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please create your teacher profile first.')
        return redirect('create_teacher_profile')
    
    if request.method == 'POST':
        # Update profile fields
        profile.institute_id = request.POST.get('institute')
        profile.department = request.POST.get('department')
        profile.title = request.POST.get('title')
        profile.employee_id = request.POST.get('employee_id')
        
        # Update user fields
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        
        profile.save()
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('teacher_dashboard')
    
    institutes = Institute.objects.all()
    context = {
        'profile': profile,
        'institutes': institutes,
    }
    return render(request, 'app/edit_teacher_profile.html', context)

@login_required
def edit_official_profile(request):
    """Edit official profile"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    try:
        profile = request.user.official_profile
    except OfficialProfile.DoesNotExist:
        messages.error(request, 'Please create your official profile first.')
        return redirect('home')  # No create view for officials yet
    
    if request.method == 'POST':
        # Update profile fields
        profile.department = request.POST.get('department')
        profile.position = request.POST.get('position')
        profile.employee_id = request.POST.get('employee_id')
        
        # Update user fields
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        
        profile.save()
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('official_dashboard')
    
    context = {
        'profile': profile,
    }
    return render(request, 'app/edit_official_profile.html', context)

@login_required
def create_position(request):
    """Create new internship position (mentor only)"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.error(request, 'Please create your mentor profile first.')
        return redirect('create_mentor_profile')
    
    if not mentor_profile.is_verified:
        messages.error(request, 'Your mentor profile must be verified before creating positions.')
        return redirect('mentor_dashboard')
    
    if request.method == 'POST':
        # Create new position
        position = InternshipPosition.objects.create(
            company=mentor_profile.company,
            mentor=mentor_profile,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            requirements=request.POST.get('requirements'),
            skills_required=request.POST.get('skills_required'),
            duration=request.POST.get('duration'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            stipend=Decimal(request.POST.get('stipend')) if request.POST.get('stipend') else None,
            max_students=int(request.POST.get('max_students', 1))
        )
        
        messages.success(request, f'Position "{position.title}" created successfully!')
        return redirect('mentor_dashboard')
    
    context = {
        'mentor_profile': mentor_profile,
    }
    return render(request, 'app/create_position.html', context)

@login_required
def edit_position(request, position_nanoid):
    """Edit existing internship position (mentor only)"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
        position = InternshipPosition.objects.get(nanoid=position_nanoid, mentor=mentor_profile)
    except (MentorProfile.DoesNotExist, InternshipPosition.DoesNotExist):
        messages.error(request, 'Position not found or access denied.')
        return redirect('mentor_dashboard')
    
    # Check if position has applications - prevent editing if it does
    has_applications = position.applications.exists()
    if has_applications and request.method == 'POST':
        messages.error(request, 'Cannot edit position that already has applications. Please create a new position instead.')
        return redirect('mentor_dashboard')
    
    if request.method == 'POST':
        # Update position
        position.title = request.POST.get('title')
        position.description = request.POST.get('description')
        position.requirements = request.POST.get('requirements')
        position.skills_required = request.POST.get('skills_required')
        position.duration = request.POST.get('duration')
        position.start_date = request.POST.get('start_date')
        position.end_date = request.POST.get('end_date')
        position.stipend = Decimal(request.POST.get('stipend')) if request.POST.get('stipend') else None
        position.max_students = int(request.POST.get('max_students', 1))
        position.is_active = 'is_active' in request.POST
        
        position.save()
        
        messages.success(request, f'Position "{position.title}" updated successfully!')
        return redirect('mentor_dashboard')
    
    context = {
        'position': position,
        'mentor_profile': mentor_profile,
        'has_applications': has_applications,
    }
    return render(request, 'app/edit_position.html', context)


@login_required
def apply_position(request, position_nanoid):
    """Handle student applications for internship positions"""
    # Get the position
    position = get_object_or_404(InternshipPosition, nanoid=position_nanoid)
    
    # Check if user is a student
    if not request.user.groups.filter(name='student').exists():
        messages.error(request, 'Only students can apply for positions.')
        return redirect('position_detail', position_nanoid=position_nanoid)
    
    # Get student profile
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must complete your student profile before applying.')
        return redirect('create_student_profile')
    
    # Check if student has already applied
    existing_application = InternshipApplication.objects.filter(
        student=student_profile,
        position=position
    ).first()
    
    if existing_application:
        messages.info(request, 'You have already applied for this position.')
        return redirect('position_detail', position_nanoid=position_nanoid)
    
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '').strip()
        
        if not cover_letter:
            messages.error(request, 'Cover letter is required.')
        else:
            # Create the application
            application = InternshipApplication.objects.create(
                student=student_profile,
                position=position,
                cover_letter=cover_letter,
                status='pending'
            )
            
            # Create notification for mentor
            mentor_profile = position.mentor
            if mentor_profile and mentor_profile.user:
                Notification.objects.create(
                    recipient=mentor_profile.user,
                    title="New Application Received",
                    message=f"New application received for {position.title} from {student_profile.user.get_full_name() or student_profile.user.username}",
                    notification_type='general'
                )
            
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('position_detail', position_nanoid=position_nanoid)
    
    context = {
        'position': position,
        'student_profile': student_profile,
    }
    return render(request, 'app/apply_position.html', context)


@login_required
def student_applications(request):
    """Display all applications for the current student"""
    # Check if user is a student
    if not request.user.groups.filter(name='student').exists():
        messages.error(request, 'Only students can view applications.')
        return redirect('home')
    
    # Get student profile
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_student_profile')
    
    # Get all applications for this student
    applications = InternshipApplication.objects.filter(
        student=student_profile
    ).select_related('position', 'position__mentor', 'position__company').order_by('-applied_at')
    
    # Pagination
    paginator = Paginator(applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'applications': page_obj,
        'student_profile': student_profile,
    }
    return render(request, 'app/student_applications.html', context)

@login_required
def withdraw_application(request, application_id):
    """Allow students to withdraw their applications"""
    # Check if user is a student
    if not request.user.groups.filter(name='student').exists():
        messages.error(request, 'Only students can withdraw applications.')
        return redirect('home')
    
    try:
        # Get student profile
        student_profile = StudentProfile.objects.get(user=request.user)
        
        # Get the application (ensuring it belongs to the current student)
        application = InternshipApplication.objects.get(
            nanoid=application_id,
            student=student_profile
        )
        
        # Check if application can be withdrawn (not already approved, rejected, or withdrawn)
        if application.status in ['approved', 'rejected', 'withdrawn']:
            status_display = dict(InternshipApplication.STATUS_CHOICES).get(application.status, application.status)
            messages.error(request, f'Cannot withdraw application that is already {status_display.lower()}.')
            return redirect('student_applications')
        
        # Withdraw the application
        application.status = 'withdrawn'
        application.reviewed_at = timezone.now()
        application.reviewer_notes = "Application withdrawn by student"
        application.save()
        
        position_title = application.position.title if application.position else "Unknown Position"
        messages.success(request, f'Your application for "{position_title}" has been withdrawn successfully.')
        
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_student_profile')
    except InternshipApplication.DoesNotExist:
        messages.error(request, 'Application not found or you do not have permission to withdraw it.')
    
    return redirect('student_applications')

@login_required
def register_organization(request):
    """Register a new organization (company or institute)"""
    user_type = get_user_type(request.user)
    
    if user_type not in ['mentor', 'teacher']:
        messages.error(request, 'Only mentors and teachers can register organizations.')
        return redirect('home')
    
    # Check if user can register organizations
    if user_type == 'mentor':
        try:
            profile = request.user.mentor_profile
            if not profile.can_register_organization:
                messages.error(request, 'You do not have permission to register new organizations.')
                return redirect('mentor_dashboard')
        except MentorProfile.DoesNotExist:
            messages.error(request, 'Please complete your mentor profile first.')
            return redirect('create_mentor_profile')
    else:  # teacher
        try:
            profile = request.user.teacher_profile
            if not profile.can_register_organization:
                messages.error(request, 'You do not have permission to register new organizations.')
                return redirect('teacher_dashboard')
        except TeacherProfile.DoesNotExist:
            messages.error(request, 'Please complete your teacher profile first.')
            return redirect('create_teacher_profile')
    
    if request.method == 'POST':
        # Create organization registration request
        org_request = OrganizationRegistrationRequest(
            organization_type=request.POST.get('organization_type'),
            organization_name=request.POST.get('organization_name'),
            organization_description=request.POST.get('organization_description'),
            industry=request.POST.get('industry') if request.POST.get('organization_type') == 'company' else None,
            address=request.POST.get('address'),
            website=request.POST.get('website'),
            contact_email=request.POST.get('contact_email'),
            phone=request.POST.get('phone'),
            email_domain=request.POST.get('email_domain'),
            requested_by_user=request.user,
        )
        
        # Set the requesting profile
        if user_type == 'mentor':
            org_request.requested_by_mentor = profile
        else:
            org_request.requested_by_teacher = profile
        
        # Handle file uploads
        if 'registration_certificate' in request.FILES:
            org_request.registration_certificate = request.FILES['registration_certificate']
        if 'authorization_letter' in request.FILES:
            org_request.authorization_letter = request.FILES['authorization_letter']
        
        org_request.save()
        
        messages.success(request, f'Your {org_request.organization_name} registration request has been submitted for review.')
        return redirect('view_organization_requests')
    
    return render(request, 'app/register_organization.html', {
        'user_type': user_type,
    })

@login_required
def view_organization_requests(request):
    """View organization registration requests"""
    user_type = get_user_type(request.user)
    
    if user_type == 'mentor':
        try:
            profile = request.user.mentor_profile
            requests = OrganizationRegistrationRequest.objects.filter(requested_by_mentor=profile)
        except MentorProfile.DoesNotExist:
            messages.error(request, 'Mentor profile not found.')
            return redirect('create_mentor_profile')
    elif user_type == 'teacher':
        try:
            profile = request.user.teacher_profile
            requests = OrganizationRegistrationRequest.objects.filter(requested_by_teacher=profile)
        except TeacherProfile.DoesNotExist:
            messages.error(request, 'Teacher profile not found.')
            return redirect('create_teacher_profile')
    elif user_type == 'official':
        # Officials can see all requests
        requests = OrganizationRegistrationRequest.objects.all()
    else:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    return render(request, 'app/view_organization_requests.html', {
        'requests': requests,
        'user_type': user_type,
    })

@login_required
def approve_organization_request(request, request_nanoid):
    """Approve organization registration request (officials only)"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    try:
        official_profile = request.user.official_profile
        if not official_profile.can_approve_organizations:
            messages.error(request, 'You do not have permission to approve organizations.')
            return redirect('official_dashboard')
    except OfficialProfile.DoesNotExist:
        messages.error(request, 'Please complete your official profile first.')
        return redirect('create_official_profile')
    
    try:
        org_request = OrganizationRegistrationRequest.objects.get(nanoid=request_nanoid)
    except OrganizationRegistrationRequest.DoesNotExist:
        messages.error(request, 'Organization request not found.')
        return redirect('view_organization_requests')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('review_notes', '')
        
        if action == 'approve':
            # Create the organization
            if org_request.organization_type == 'company':
                company = Company.objects.create(
                    name=org_request.organization_name,
                    description=org_request.organization_description,
                    industry=org_request.industry,
                    address=org_request.address,
                    website=org_request.website,
                    contact_email=org_request.contact_email,
                    phone=org_request.phone,
                    email_domain=org_request.email_domain,
                    registered_by=org_request.requested_by_mentor,
                    registration_status='approved',
                    approved_by=official_profile,
                    approved_at=timezone.now(),
                    registration_notes=notes,
                    domain_verified=True,  # Assume domain is verified upon approval
                    is_verified=True,
                )
                org_request.approved_company = company
                
                # Set mentor as admin contact
                if org_request.requested_by_mentor:
                    org_request.requested_by_mentor.company = company
                    org_request.requested_by_mentor.is_admin_contact = True
                    org_request.requested_by_mentor.save()
                    
            else:  # institute
                institute = Institute.objects.create(
                    name=org_request.organization_name,
                    address=org_request.address,
                    website=org_request.website,
                    contact_email=org_request.contact_email,
                    email_domain=org_request.email_domain,
                    registered_by=org_request.requested_by_teacher,
                    registration_status='approved',
                    approved_by=official_profile,
                    approved_at=timezone.now(),
                    registration_notes=notes,
                    domain_verified=True,  # Assume domain is verified upon approval
                )
                org_request.approved_institute = institute
                
                # Set teacher as admin contact
                if org_request.requested_by_teacher:
                    org_request.requested_by_teacher.institute = institute
                    org_request.requested_by_teacher.is_admin_contact = True
                    org_request.requested_by_teacher.save()
            
            org_request.status = 'approved'
            org_request.reviewed_by = official_profile
            org_request.reviewed_at = timezone.now()
            org_request.review_notes = notes
            org_request.save()
            
            messages.success(request, f'{org_request.organization_name} has been approved and created successfully.')
            
        elif action == 'reject':
            org_request.status = 'rejected'
            org_request.reviewed_by = official_profile
            org_request.reviewed_at = timezone.now()
            org_request.review_notes = notes
            org_request.save()
            
            messages.success(request, f'{org_request.organization_name} registration request has been rejected.')
        
        return redirect('view_organization_requests')
    
    return render(request, 'app/approve_organization.html', {
        'org_request': org_request,
    })
