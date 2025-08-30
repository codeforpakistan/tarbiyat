from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import os
from django.conf import settings
from .models import (
    StudentProfile, MentorProfile, TeacherProfile, OfficialProfile,
    InternshipPosition, InternshipApplication, Internship, Company, Institute, 
    Notification, OrganizationRegistrationRequest, ProgressReport,
    StudentActivityLog, StudentActivity, StudentInternshipReport
)
from .forms import (
    StudentActivityLogForm, StudentActivityFormSet
)
from django import forms
from .utils import (
    validate_user_organization_membership, 
    get_available_institutes_for_user, 
    get_available_companies_for_user
)

def redirect_to_role_dashboard(user):
    """Helper function to redirect users to their role-specific dashboard"""
    user_type = get_user_type(user)
    
    if user_type == 'student':
        return redirect('student_dashboard')
    elif user_type == 'mentor':
        return redirect('mentor_dashboard')
    elif user_type == 'teacher':
        return redirect('teacher_dashboard')
    elif user_type == 'official':
        return redirect('official_dashboard')
    elif user_type == 'admin':
        return redirect('/admin/')
    else:
        return redirect('home')

def get_user_type(user):
    """Helper function to get user type from groups"""
    if not user or not user.is_authenticated:
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
        elif user_type in ['student', 'mentor', 'teacher', 'official']:
            return redirect_to_role_dashboard(request.user)
    
    context = {
        'total_companies': Company.objects.filter(is_verified=True).count(),
        'total_students': StudentProfile.objects.count(),
        'active_internships': Internship.objects.filter(status='active').count(),
        'total_positions': InternshipPosition.objects.filter(is_active=True).count(),
    }
    return render(request, 'app/home.html', context)

@login_required
def dashboard(request):
    """Unified dashboard that routes to appropriate dashboard based on user role"""
    user_type = get_user_type(request.user)
    
    # Check if user has incomplete profile
    if not user_type:
        return redirect('complete_profile')
    
    # Route to appropriate dashboard based on user type
    if user_type == 'student':
        return student_dashboard_view(request)
    elif user_type == 'mentor':
        return mentor_dashboard_view(request)
    elif user_type == 'teacher':
        return teacher_dashboard_view(request)
    elif user_type == 'official':
        return official_dashboard_view(request)
    elif user_type == 'admin':
        return redirect('/admin/')  # Admins go to Django admin
    else:
        messages.error(request, 'Invalid user type. Please contact support.')
        return redirect('home')

def student_dashboard_view(request):
    """Student dashboard with internship opportunities and applications"""
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.warning(request, 'Please complete your student profile first.')
        return redirect('create_profile')
    
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

def mentor_dashboard_view(request):
    """Mentor dashboard for managing applications and internships"""
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
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
    
    # Calculate stats for the dashboard
    stats = {
        'active_positions': positions.filter(is_active=True).count(),
        'pending_applications': pending_applications.count(),
        'current_interns': active_internships.count(),
        'scheduled_interviews': 0,  # Add interview functionality later if needed
    }
    
    context = {
        'mentor_profile': mentor_profile,
        'positions': positions,
        'recent_applications': pending_applications[:5],  # Recent applications for dashboard
        'current_interns': active_internships,  # Current active internships
        'stats': stats,
    }
    return render(request, 'app/mentor_dashboard.html', context)

def teacher_dashboard_view(request):
    """Teacher dashboard for monitoring student internships"""
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.warning(request, 'Please complete your teacher profile first.')
        return redirect('create_profile')
    
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
        'institute_students': institute_students,
        'active_internships': active_internships,
        'students_with_internships': active_internships.count(),
    }
    return render(request, 'app/teacher_dashboard.html', context)

def official_dashboard_view(request):
    """Official dashboard with system overview and statistics"""
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
def teacher_students(request):
    """View all students from teacher's institute"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please create your teacher profile first.')
        return redirect('create_profile')
    
    # Get students from the same institute
    students = StudentProfile.objects.filter(
        institute=teacher_profile.institute
    ).select_related('user').order_by('user__last_name', 'user__first_name')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(major__icontains=search_query)
        )
    
    # Filter by semester of study
    year_filter = request.GET.get('year')
    if year_filter:
        students = students.filter(semester_of_study=year_filter)
    
    # Filter by internship status
    internship_filter = request.GET.get('internship_status')
    if internship_filter == 'active':
        students = students.filter(
            internship__status='active'
        ).distinct()
    elif internship_filter == 'completed':
        students = students.filter(
            internship__status='completed'
        ).distinct()
    elif internship_filter == 'none':
        students = students.filter(
            internship__isnull=True
        )
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'teacher_profile': teacher_profile,
        'page_obj': page_obj,
        'search_query': search_query,
        'year_filter': year_filter,
        'internship_filter': internship_filter,
        'year_choices': StudentProfile.YEAR_CHOICES,
    }
    return render(request, 'app/teacher_students.html', context)

@login_required
def teacher_internships(request):
    """View all internships for students from teacher's institute"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please complete your teacher profile first.')
        return redirect('complete_profile')
    
    # Get all internships for students from teacher's institute
    internships = Internship.objects.filter(
        student__institute=teacher_profile.institute
    ).select_related(
        'student__user', 'mentor__user', 'mentor__company'
    ).prefetch_related('student_reports', 'activity_logs').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        internships = internships.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        internships = internships.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query) |
            Q(mentor__company__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(internships, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'teacher_profile': teacher_profile,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Internship.STATUS_CHOICES,
    }
    return render(request, 'app/teacher_internships.html', context)

@login_required
def teacher_internship_detail(request, internship_nanoid):
    """View detailed information about a specific internship"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please complete your teacher profile first.')
        return redirect('complete_profile')
    
    try:
        internship = Internship.objects.select_related(
            'student__user', 'mentor__user', 'mentor__company', 'teacher__user'
        ).prefetch_related(
            'student_reports', 'activity_logs'
        ).get(nanoid=internship_nanoid)
        
        # Ensure the internship belongs to a student from teacher's institute
        if internship.student.institute != teacher_profile.institute:
            messages.error(request, 'This internship does not belong to a student from your institute.')
            return redirect('teacher_internships')
            
    except Internship.DoesNotExist:
        messages.error(request, 'Internship not found.')
        return redirect('teacher_internships')
    
    # Get reports and activity logs
    student_reports = internship.student_reports.all().order_by('-report_month')
    activity_logs = internship.activity_logs.all().order_by('-period_starting')
    
    context = {
        'teacher_profile': teacher_profile,
        'internship': internship,
        'student_reports': student_reports,
        'activity_logs': activity_logs,
    }
    return render(request, 'app/teacher_internship_detail.html', context)

@login_required
def teacher_reports(request):
    """View all reports from students in teacher's institute"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please complete your teacher profile first.')
        return redirect('complete_profile')
    
    # Get all reports for students from teacher's institute
    reports = StudentInternshipReport.objects.filter(
        internship__student__institute=teacher_profile.institute
    ).select_related(
        'internship__student__user', 'teacher__user', 'internship__mentor__company'
    ).order_by('-report_month')
    
    # Filter by report type or student
    student_filter = request.GET.get('student', '')
    if student_filter:
        reports = reports.filter(internship__student__nanoid=student_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        reports = reports.filter(
            Q(internship__student__user__first_name__icontains=search_query) |
            Q(internship__student__user__last_name__icontains=search_query) |
            Q(internship__student__student_id__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(reports, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get students for filter dropdown
    students = StudentProfile.objects.filter(
        institute=teacher_profile.institute,
        internship__isnull=False
    ).distinct().order_by('user__first_name')
    
    context = {
        'teacher_profile': teacher_profile,
        'page_obj': page_obj,
        'search_query': search_query,
        'student_filter': student_filter,
        'students': students,
    }
    return render(request, 'app/teacher_reports.html', context)

@login_required
def teacher_report_detail(request, report_nanoid):
    """View detailed information about a specific report"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please complete your teacher profile first.')
        return redirect('complete_profile')
    
    try:
        report = StudentInternshipReport.objects.select_related(
            'internship__student__user', 'teacher__user', 'internship__mentor__user', 'internship__mentor__company'
        ).get(nanoid=report_nanoid)
        
        # Ensure the report belongs to a student from teacher's institute
        if report.internship.student.institute != teacher_profile.institute:
            messages.error(request, 'This report does not belong to a student from your institute.')
            return redirect('teacher_reports')
            
    except StudentInternshipReport.DoesNotExist:
        messages.error(request, 'Report not found.')
        return redirect('teacher_reports')
    
    context = {
        'teacher_profile': teacher_profile,
        'report': report,
    }
    return render(request, 'app/teacher_report_detail.html', context)

@login_required
def edit_institute(request):
    """Edit institute information (for teachers who registered the institute)"""
    user_type = get_user_type(request.user)
    if user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher account required.')
        return redirect('home')
    
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Please create your teacher profile first.')
        return redirect('create_profile')
    
    if not teacher_profile.can_edit_institute():
        messages.error(request, 'You can only edit institutes that you registered.')
        return redirect_to_role_dashboard(request.user)
    
    institute = teacher_profile.institute
    
    if request.method == 'POST':
        # Validate required fields
        name = request.POST.get('name', '').strip()
        
        if not name:
            messages.error(request, 'Institute name is a required field.')
            context = {
                'institute': institute,
                'teacher_profile': teacher_profile,
            }
            return render(request, 'app/edit_institute.html', context)
        
        # Update institute fields
        institute.name = name
        institute.description = request.POST.get('description', '').strip()
        institute.institute_type = request.POST.get('institute_type', '')
        institute.address = request.POST.get('address', '').strip()
        institute.website = request.POST.get('website', '').strip() or None
        institute.contact_email = request.POST.get('contact_email', '').strip() or None
        institute.phone = request.POST.get('phone', '').strip() or None
        institute.email_domain = request.POST.get('email_domain', '').strip() or None
        institute.established_year = request.POST.get('established_year') or None
        
        # Update demographic fields
        institute.district = request.POST.get('district', '') or None
        institute.male_students_count = int(request.POST.get('male_students_count', 0) or 0)
        institute.female_students_count = int(request.POST.get('female_students_count', 0) or 0)
        institute.degree_programs = request.POST.get('degree_programs') == 'on'
        institute.postgraduate_programs = request.POST.get('postgraduate_programs') == 'on'
        institute.management_programs = request.POST.get('management_programs') == 'on'
        institute.primary_education_level = request.POST.get('primary_education_level', '') or None
        
        # Validate email domain format if provided
        email_domain = institute.email_domain
        if email_domain:
            # Remove any @ symbols and convert to lowercase
            email_domain = email_domain.replace('@', '').lower()
            institute.email_domain = email_domain
            
            # Basic domain validation
            if not email_domain.replace('-', '').replace('_', '').replace('.', '').isalnum():
                messages.error(request, 'Please enter a valid email domain (e.g., university.edu.pk)')
                context = {
                    'institute': institute,
                    'teacher_profile': teacher_profile,
                }
                return render(request, 'app/edit_institute.html', context)
        
        institute.save()
        
        messages.success(request, f'Institute "{institute.name}" updated successfully!')
        return redirect_to_role_dashboard(request.user)
    
    context = {
        'institute': institute,
        'teacher_profile': teacher_profile,
    }
    return render(request, 'app/edit_institute.html', context)

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
def mass_verify_companies(request):
    """Official view to mass verify companies"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    if request.method == 'POST':
        # Get selected company IDs from the form
        company_ids = request.POST.getlist('company_ids')
        action = request.POST.get('action')
        
        if not company_ids:
            messages.error(request, 'Please select at least one company.')
            return redirect('manage_companies')
        
        # Get the companies
        companies = Company.objects.filter(nanoid__in=company_ids)
        
        if action == 'approve':
            # Approve selected companies
            updated_count = companies.update(
                registration_status='approved',
                approved_at=timezone.now(),
                approved_by=request.user
            )
            messages.success(request, f'Successfully approved {updated_count} companies.')
            
        elif action == 'reject':
            # Reject selected companies
            updated_count = companies.update(
                registration_status='rejected',
                approved_at=timezone.now(),
                approved_by=request.user
            )
            messages.success(request, f'Successfully rejected {updated_count} companies.')
            
        elif action == 'verify_domain':
            # Verify domain for selected companies
            updated_count = companies.update(domain_verified=True)
            messages.success(request, f'Successfully verified domain for {updated_count} companies.')
            
        elif action == 'unverify_domain':
            # Unverify domain for selected companies
            updated_count = companies.update(domain_verified=False)
            messages.success(request, f'Successfully unverified domain for {updated_count} companies.')
            
        else:
            messages.error(request, 'Invalid action selected.')
        
        return redirect('manage_companies')
    
    # If GET request, redirect to manage companies
    return redirect('manage_companies')

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
def mass_verify_institutes(request):
    """Official view to mass verify institutes"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    if request.method == 'POST':
        # Get selected institute IDs from the form
        institute_ids = request.POST.getlist('institute_ids')
        action = request.POST.get('action')
        
        if not institute_ids:
            messages.error(request, 'Please select at least one institute.')
            return redirect('manage_institutes')
        
        # Get the institutes
        institutes = Institute.objects.filter(nanoid__in=institute_ids)
        
        if action == 'approve':
            # Approve selected institutes
            updated_count = institutes.update(
                registration_status='approved',
                approved_at=timezone.now(),
                approved_by=request.user
            )
            messages.success(request, f'Successfully approved {updated_count} institutes.')
            
        elif action == 'reject':
            # Reject selected institutes
            updated_count = institutes.update(
                registration_status='rejected',
                approved_at=timezone.now(),
                approved_by=request.user
            )
            messages.success(request, f'Successfully rejected {updated_count} institutes.')
            
        elif action == 'verify_domain':
            # Verify domain for selected institutes
            updated_count = institutes.update(domain_verified=True)
            messages.success(request, f'Successfully verified domain for {updated_count} institutes.')
            
        elif action == 'unverify_domain':
            # Unverify domain for selected institutes
            updated_count = institutes.update(domain_verified=False)
            messages.success(request, f'Successfully unverified domain for {updated_count} institutes.')
            
        else:
            messages.error(request, 'Invalid action selected.')
        
        return redirect('manage_institutes')
    
    # If GET request, redirect to manage institutes
    return redirect('manage_institutes')

@login_required
def official_reports(request):
    """Official view to generate and view system reports"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    # Entity Counts
    entity_counts = {
        # User Counts
        'total_users': User.objects.count(),
        'students': User.objects.filter(groups__name='student').count(),
        'mentors': User.objects.filter(groups__name='mentor').count(),
        'teachers': User.objects.filter(groups__name='teacher').count(),
        'officials': User.objects.filter(groups__name='official').count(),
        
        # Organization Counts
        'total_companies': Company.objects.count(),
        'approved_companies': Company.objects.filter(registration_status='approved').count(),
        'pending_companies': Company.objects.filter(registration_status='pending').count(),
        'rejected_companies': Company.objects.filter(registration_status='rejected').count(),
        'verified_companies': Company.objects.filter(domain_verified=True).count(),
        
        'total_institutes': Institute.objects.count(),
        'approved_institutes': Institute.objects.filter(registration_status='approved').count(),
        'pending_institutes': Institute.objects.filter(registration_status='pending').count(),
        'rejected_institutes': Institute.objects.filter(registration_status='rejected').count(),
        'verified_institutes': Institute.objects.filter(domain_verified=True).count(),
        
        # Position and Application Counts
        'total_positions': InternshipPosition.objects.count(),
        'active_positions': InternshipPosition.objects.filter(is_active=True).count(),
        'total_applications': InternshipApplication.objects.count(),
        'pending_applications': InternshipApplication.objects.filter(status='pending').count(),
        'accepted_applications': InternshipApplication.objects.filter(status='accepted').count(),
        'rejected_applications': InternshipApplication.objects.filter(status='rejected').count(),
        
        # Internship Counts
        'total_internships': Internship.objects.count(),
        'active_internships': Internship.objects.filter(status='active').count(),
        'completed_internships': Internship.objects.filter(status='completed').count(),
        'terminated_internships': Internship.objects.filter(status='terminated').count(),
    }
    
    # Recent Activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_activity = {
        'new_users': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
        'new_companies': Company.objects.filter(created_at__gte=thirty_days_ago).count(),
        'new_institutes': Institute.objects.filter(created_at__gte=thirty_days_ago).count(),
        'new_applications': InternshipApplication.objects.filter(applied_at__gte=thirty_days_ago).count(),
        'new_internships': Internship.objects.filter(start_date__gte=thirty_days_ago).count(),
    }
    
    # Monthly Trends (last 6 months)
    monthly_trends = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_trends.append({
            'month': month_start.strftime('%B %Y'),
            'users': User.objects.filter(date_joined__range=[month_start, month_end]).count(),
            'companies': Company.objects.filter(created_at__range=[month_start, month_end]).count(),
            'applications': InternshipApplication.objects.filter(applied_at__range=[month_start, month_end]).count(),
            'internships': Internship.objects.filter(start_date__range=[month_start, month_end]).count(),
        })
    
    monthly_trends.reverse()  # Show oldest first
    
    # Success Metrics
    success_metrics = {
        'application_success_rate': 0,
        'company_approval_rate': 0,
        'institute_approval_rate': 0,
        'internship_completion_rate': 0,
    }
    
    # Calculate success rates
    total_apps = InternshipApplication.objects.count()
    if total_apps > 0:
        accepted_apps = InternshipApplication.objects.filter(status='accepted').count()
        success_metrics['application_success_rate'] = round((accepted_apps / total_apps) * 100, 1)
    
    total_companies = Company.objects.count()
    if total_companies > 0:
        approved_companies = Company.objects.filter(registration_status='approved').count()
        success_metrics['company_approval_rate'] = round((approved_companies / total_companies) * 100, 1)
    
    total_institutes = Institute.objects.count()
    if total_institutes > 0:
        approved_institutes = Institute.objects.filter(registration_status='approved').count()
        success_metrics['institute_approval_rate'] = round((approved_institutes / total_institutes) * 100, 1)
    
    total_internships = Internship.objects.count()
    if total_internships > 0:
        completed_internships = Internship.objects.filter(status='completed').count()
        success_metrics['internship_completion_rate'] = round((completed_internships / total_internships) * 100, 1)
    
    context = {
        'entity_counts': entity_counts,
        'recent_activity': recent_activity,
        'monthly_trends': monthly_trends,
        'success_metrics': success_metrics,
        'report_generated_at': timezone.now(),
    }
    
    return render(request, 'app/official_reports.html', context)

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
    companies = Company.objects.filter(registration_status='approved').order_by('name')
    
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
            'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
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
                return redirect_to_role_dashboard(request.user)
            elif user_type == 'mentor':
                return redirect_to_role_dashboard(request.user)
            elif user_type == 'teacher':
                return redirect_to_role_dashboard(request.user)
            elif user_type == 'official':
                return redirect_to_role_dashboard(request.user)
            else:
                return redirect('home')
    else:
        form = ProfileCompletionForm()
    
    return render(request, 'app/complete_profile.html', {'form': form, 'user': user})

@login_required
def profile(request):
    """Unified profile view that shows appropriate profile based on user role"""
    user_type = get_user_type(request.user)
    
    # Check if user has incomplete profile
    if not user_type:
        return redirect('complete_profile')
    
    # Route to appropriate profile view based on user type
    if user_type == 'student':
        return student_profile_view(request)
    elif user_type == 'mentor':
        return mentor_profile_view(request)
    elif user_type == 'teacher':
        return teacher_profile_view(request)
    elif user_type == 'official':
        return official_profile_view(request)
    elif user_type == 'admin':
        return redirect('/admin/')  # Admins go to Django admin
    else:
        messages.error(request, 'Invalid user type. Please contact support.')
        return redirect('home')

@login_required
def create_profile(request):
    """Unified profile creation that routes to appropriate creation based on user role"""
    user_type = get_user_type(request.user)
    
    # Check if user has incomplete profile setup
    if not user_type:
        return redirect('complete_profile')
    
    # Route to appropriate profile creation based on user type
    if user_type == 'student':
        return create_student_profile_view(request)
    elif user_type == 'mentor':
        return create_mentor_profile_view(request)
    elif user_type == 'teacher':
        return create_teacher_profile_view(request)
    elif user_type == 'official':
        # Officials don't need a separate profile creation, redirect to edit
        return redirect('edit_profile')
    else:
        messages.error(request, 'Invalid user type. Please contact support.')
        return redirect('home')

@login_required
def edit_profile(request):
    """Unified profile editing that routes to appropriate editing based on user role"""
    user_type = get_user_type(request.user)
    
    # Check if user has incomplete profile
    if not user_type:
        return redirect('complete_profile')
    
    # Route to appropriate profile editing based on user type
    if user_type == 'student':
        return edit_student_profile_view(request)
    elif user_type == 'mentor':
        return edit_mentor_profile_view(request)
    elif user_type == 'teacher':
        return edit_teacher_profile_view(request)
    elif user_type == 'official':
        return edit_official_profile_view(request)
    elif user_type == 'admin':
        return redirect('/admin/')  # Admins go to Django admin
    else:
        messages.error(request, 'Invalid user type. Please contact support.')
        return redirect('home')

def student_profile_view(request):
    """Student profile display view"""
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.warning(request, 'Please complete your student profile first.')
        return redirect('create_profile')
    
    # For now, redirect to edit profile - we can create a view template later
    return redirect('edit_profile')

def mentor_profile_view(request):
    """Mentor profile display view"""
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # For now, redirect to edit profile - we can create a view template later
    return redirect('edit_profile')

def teacher_profile_view(request):
    """Teacher profile display view"""
    try:
        teacher_profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.warning(request, 'Please complete your teacher profile first.')
        return redirect('create_profile')
    
    # For now, redirect to edit profile - we can create a view template later
    return redirect('edit_profile')

def official_profile_view(request):
    """Official profile display view"""
    try:
        official_profile = request.user.official_profile
    except OfficialProfile.DoesNotExist:
        # Officials might not have profiles created yet
        messages.info(request, 'Create your official profile to get started.')
        return redirect('create_profile')
    
    # For now, redirect to edit profile - we can create a view template later
    return redirect('edit_profile')

def create_student_profile_view(request):
    """Student profile creation view"""
    # Check if profile already exists
    if hasattr(request.user, 'student_profile'):
        messages.info(request, 'Your profile already exists. You can edit it here.')
        return redirect('edit_profile')
    
    if request.method == 'POST':
        try:
            # Create student profile with basic information
            student_profile = StudentProfile.objects.create(
                user=request.user,
                # Set defaults for optional fields
                student_id='',
                semester_of_study='',
                major='',
                skills=''
            )
            
            messages.success(request, 'Your student profile has been created successfully! You can now update your details.')
            return redirect('edit_profile')
            
        except Exception as e:
            messages.error(request, f'Error creating profile: {str(e)}')
    
    institutes = Institute.objects.filter(registration_status='approved')
    return render(request, 'app/create_student_profile.html', {'institutes': institutes})

def create_mentor_profile_view(request):
    """Mentor profile creation view"""
    # Check if profile already exists
    if hasattr(request.user, 'mentor_profile'):
        messages.info(request, 'Your profile already exists. You can edit it here.')
        return redirect('edit_profile')
    
    if request.method == 'POST':
        try:
            # Create mentor profile with basic information
            mentor_profile = MentorProfile.objects.create(
                user=request.user,
                # Set defaults for optional fields
                position='',
                department='',
                experience_years=0,
                specialization=''
            )
            
            messages.success(request, 'Your mentor profile has been created successfully! You can now update your details.')
            return redirect('edit_profile')
            
        except Exception as e:
            messages.error(request, f'Error creating profile: {str(e)}')
    
    companies = Company.objects.filter(registration_status='approved')
    return render(request, 'app/create_mentor_profile.html', {'companies': companies})

def create_teacher_profile_view(request):
    """Teacher profile creation view"""
    # Check if profile already exists
    if hasattr(request.user, 'teacher_profile'):
        messages.info(request, 'Your profile already exists. You can edit it here.')
        return redirect('edit_profile')
    
    if request.method == 'POST':
        try:
            # Create teacher profile with basic information
            teacher_profile = TeacherProfile.objects.create(
                user=request.user,
                # Set defaults for optional fields
                department='',
                title='',
                employee_id='',
                is_admin_contact=False,
                can_register_organization=True
            )
            
            messages.success(request, 'Your teacher profile has been created successfully! You can now update your details.')
            return redirect('edit_profile')
            
        except Exception as e:
            messages.error(request, f'Error creating profile: {str(e)}')
    
    institutes = Institute.objects.filter(registration_status='approved')
    return render(request, 'app/create_teacher_profile.html', {'institutes': institutes})

def edit_student_profile_view(request):
    """Student profile editing view"""
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.warning(request, 'Please create your student profile first.')
        return redirect('create_profile')
    
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
        profile.semester_of_study = request.POST.get('semester_of_study')
        profile.major = request.POST.get('major')
        profile.gpa = float(request.POST.get('gpa', 0))
        profile.skills = request.POST.get('skills')
        profile.portfolio_url = request.POST.get('portfolio_url', '')
        profile.expected_graduation = request.POST.get('expected_graduation')
        profile.is_available_for_internship = 'available' in request.POST
        profile.phone = request.POST.get('phone', '')
        
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
        return redirect_to_role_dashboard(request.user)
    
    available_institutes = get_available_institutes_for_user(request.user)
    context = {
        'profile': profile,
        'institutes': available_institutes,
    }
    return render(request, 'app/edit_student_profile.html', context)

def edit_mentor_profile_view(request):
    """Mentor profile editing view"""
    try:
        profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please create your mentor profile first.')
        return redirect('create_profile')
    
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
        return redirect_to_role_dashboard(request.user)
    
    available_companies = get_available_companies_for_user(request.user)
    context = {
        'profile': profile,
        'companies': available_companies,
    }
    return render(request, 'app/edit_mentor_profile.html', context)

def edit_teacher_profile_view(request):
    """Teacher profile editing view"""
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.warning(request, 'Please create your teacher profile first.')
        return redirect('create_profile')
    
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
                return render(request, 'app/edit_teacher_profile.html', {
                    'profile': profile,
                    'institutes': available_institutes,
                    'domain_error': True,
                })
        
        # Update profile fields
        profile.institute_id = new_institute_id
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
        return redirect_to_role_dashboard(request.user)
    
    available_institutes = get_available_institutes_for_user(request.user)
    context = {
        'profile': profile,
        'institutes': available_institutes,
    }
    return render(request, 'app/edit_teacher_profile.html', context)

def edit_official_profile_view(request):
    """Official profile editing view"""
    try:
        profile = request.user.official_profile
    except OfficialProfile.DoesNotExist:
        # Create a basic official profile if it doesn't exist
        profile = OfficialProfile.objects.create(
            user=request.user,
            department="Not specified"
        )
        messages.success(request, 'Official profile created successfully.')
    
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
        return redirect_to_role_dashboard(request.user)
    
    context = {
        'profile': profile,
    }
    return render(request, 'app/edit_official_profile.html', context)

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
        return redirect('create_profile')
    
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
        profile.semester_of_study = request.POST.get('semester_of_study')
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
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect('create_profile')
    
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
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect('create_profile')
    
    if not mentor_profile.can_edit_company():
        messages.error(request, 'You can only edit companies that you registered.')
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect('create_profile')
    
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
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect('create_profile')
    
    if not mentor_profile.is_verified:
        messages.error(request, 'Your mentor profile must be verified before creating positions.')
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect_to_role_dashboard(request.user)
    
    # Check if position has applications - prevent editing if it does
    has_applications = position.applications.exists()
    if has_applications and request.method == 'POST':
        messages.error(request, 'Cannot edit position that already has applications. Please create a new position instead.')
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect_to_role_dashboard(request.user)
    
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
        return redirect('create_profile')
    
    # Check HEC eligibility: Only 4th-8th semester students can apply for internships
    if not student_profile.semester_of_study or student_profile.semester_of_study not in ['4', '5', '6', '7', '8']:
        messages.error(request, 'Only students from 4th to 8th semester are eligible for internships as per HEC policy.')
        return redirect('position_detail', position_nanoid=position_nanoid)
    
    # Check if student has an active application (pending, under_review, interview_scheduled, approved)
    active_application = InternshipApplication.objects.filter(
        student=student_profile,
        position=position,
        status__in=['pending', 'under_review', 'interview_scheduled', 'approved']
    ).first()
    
    if active_application:
        messages.info(request, f'You have an active application for this position with status: {active_application.get_status_display()}.')
        return redirect('position_detail', position_nanoid=position_nanoid)
    
    # Check for previous applications to show appropriate messaging
    previous_applications = InternshipApplication.objects.filter(
        student=student_profile,
        position=position,
        status__in=['rejected', 'withdrawn']
    ).order_by('-applied_at')
    
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
    
    # Get all previous applications for this position
    all_previous_applications = InternshipApplication.objects.filter(
        student=student_profile,
        position=position
    ).order_by('-applied_at')
    
    context = {
        'position': position,
        'student_profile': student_profile,
        'previous_applications': all_previous_applications,
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
        return redirect('create_profile')
    
    # Get all applications for this student
    applications = InternshipApplication.objects.filter(
        student=student_profile
    ).select_related('position', 'position__mentor', 'position__company').order_by('-applied_at')
    
    # Get current internship for sidebar
    current_internship = Internship.objects.filter(
        student=student_profile,
        status='active'
    ).first()
    
    # Pagination
    paginator = Paginator(applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'applications': page_obj,
        'student_profile': student_profile,
        'current_internship': current_internship,
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
        return redirect('create_profile')
    except InternshipApplication.DoesNotExist:
        messages.error(request, 'Application not found or you do not have permission to withdraw it.')
    
    return redirect('student_applications')

@login_required
def student_internship(request):
    """Display student's current internship details"""
    user_type = get_user_type(request.user)
    if user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('home')
    
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Please create your student profile first.')
        return redirect('create_profile')
    
    # Get current internship
    current_internship = Internship.objects.filter(
        student=student_profile,
        status='active'
    ).first()
    
    # Initialize context variables
    recent_activities = []
    progress_reports = []
    
    # If there's an active internship, get related data
    if current_internship:
        # Get recent activity logs for this internship
        recent_activities = StudentActivityLog.objects.filter(
            internship=current_internship,
            submitted_at__gte=current_internship.created_at
        ).order_by('-period_starting')[:5]
        
        # Get any evaluations or progress reports
        progress_reports = ProgressReport.objects.filter(
            internship=current_internship
        ).order_by('-created_at')
    
    # Get student's applications to show internship opportunities
    student_applications = InternshipApplication.objects.filter(
        student=student_profile
    ).select_related('position', 'position__company').order_by('-applied_at')[:5]
    
    context = {
        'student_profile': student_profile,
        'current_internship': current_internship,
        'recent_activities': recent_activities,
        'progress_reports': progress_reports,
        'student_applications': student_applications,
    }
    return render(request, 'app/student_internship.html', context)

@login_required
def student_activities(request):
    """Display all activity logs for the current student"""
    # Check if user is a student
    if not request.user.groups.filter(name='student').exists():
        messages.error(request, 'Only students can view activity logs.')
        return redirect('home')
    
    # Get student profile
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_profile')
    
    # Get current active internship
    current_internship = Internship.objects.filter(
        student=student_profile,
        status='active'
    ).first()
    
    if not current_internship:
        messages.info(request, 'You need an active internship to submit activity logs.')
        return redirect_to_role_dashboard(request.user)
    
    # Get all activity logs for this internship
    activity_logs = StudentActivityLog.objects.filter(
        internship=current_internship
    ).prefetch_related('activities').order_by('-period_starting')
    
    context = {
        'activity_logs': activity_logs,
        'current_internship': current_internship,
        'student_profile': student_profile,
    }
    return render(request, 'app/student_activities.html', context)

@login_required
def create_activity_log(request):
    """Create a new activity log"""
    # Check if user is a student
    if not request.user.groups.filter(name='student').exists():
        messages.error(request, 'Only students can create activity logs.')
        return redirect('home')
    
    # Get student profile
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_profile')
    
    # Get current active internship
    current_internship = Internship.objects.filter(
        student=student_profile,
        status='active'
    ).first()
    
    if not current_internship:
        messages.error(request, 'You need an active internship to submit activity logs.')
        return redirect_to_role_dashboard(request.user)
    
    if request.method == 'POST':
        log_form = StudentActivityLogForm(request.POST)
        activity_formset = StudentActivityFormSet(request.POST)
        
        if log_form.is_valid() and activity_formset.is_valid():
            # Check if a log already exists for this week
            period_starting = log_form.cleaned_data['period_starting']
            existing_log = StudentActivityLog.objects.filter(
                internship=current_internship,
                period_starting=period_starting
            ).first()
            
            if existing_log:
                messages.error(request, f'A weekly log already exists for the week starting {period_starting.strftime("%Y-%m-%d")}.')
                return redirect('student_activities')
            
            # Create the weekly log
            activity_log = log_form.save(commit=False)
            activity_log.internship = current_internship
            activity_log.save()
            
            # Create the activities
            activities_created = 0
            for activity_form in activity_formset:
                if activity_form.cleaned_data and not activity_form.cleaned_data.get('DELETE', False):
                    activity = activity_form.save(commit=False)
                    activity.activity_log = activity_log
                    activity.save()
                    activities_created += 1
            
            messages.success(request, f'Activity log created successfully with {activities_created} activities.')
            return redirect('student_activities')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        log_form = StudentActivityLogForm()
        activity_formset = StudentActivityFormSet()
    
    context = {
        'log_form': log_form,
        'activity_formset': activity_formset,
        'current_internship': current_internship,
        'student_profile': student_profile,
    }
    return render(request, 'app/create_activity_log.html', context)

@login_required
def edit_activity_log(request, log_nanoid):
    """Edit an existing activity log"""
    # Check if user is a student
    if not request.user.groups.filter(name='student').exists():
        messages.error(request, 'Only students can edit activity logs.')
        return redirect('home')
    
    # Get student profile
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_profile')
    
    # Get the weekly log (ensuring it belongs to the current student)
    try:
        activity_log = StudentActivityLog.objects.get(
            nanoid=log_nanoid,
            internship__student=student_profile
        )
    except StudentActivityLog.DoesNotExist:
        messages.error(request, 'Activity log not found or access denied.')
        return redirect('student_activities')
    
    if request.method == 'POST':
        log_form = StudentActivityLogForm(request.POST, instance=activity_log)
        
        # Get existing activities
        existing_activities = StudentActivity.objects.filter(activity_log=activity_log)
        
        # Create initial data for formset from existing activities
        initial_data = []
        for activity in existing_activities:
            initial_data.append({
                'task_description': activity.task_description,
                'hours_spent': activity.hours_spent,
                'date_performed': activity.date_performed,
            })
        
        activity_formset = StudentActivityFormSet(
            request.POST,
            initial=initial_data
        )
        
        if log_form.is_valid() and activity_formset.is_valid():
            # Save the weekly log
            log_form.save()
            
            # Handle activities
            activities_updated = 0
            for activity_form in activity_formset:
                if activity_form.cleaned_data:
                    if activity_form.cleaned_data.get('DELETE', False):
                        # Delete the activity if marked for deletion
                        if activity_form.instance.pk:
                            activity_form.instance.delete()
                    else:
                        # Save or update the activity
                        activity = activity_form.save(commit=False)
                        activity.activity_log = activity_log
                        activity.save()
                        activities_updated += 1
            
            messages.success(request, f'Activity log updated successfully with {activities_updated} activities.')
            return redirect('student_activities')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        log_form = StudentActivityLogForm(instance=activity_log)
        existing_activities = StudentActivity.objects.filter(activity_log=activity_log)
        
        # Create initial data for formset from existing activities
        initial_data = []
        for activity in existing_activities:
            initial_data.append({
                'task_description': activity.task_description,
                'hours_spent': activity.hours_spent,
                'date_performed': activity.date_performed,
            })
        
        activity_formset = StudentActivityFormSet(initial=initial_data)
    
    context = {
        'log_form': log_form,
        'activity_formset': activity_formset,
        'activity_log': activity_log,
        'student_profile': student_profile,
        'current_internship': activity_log.internship,
    }
    return render(request, 'app/edit_activity_log.html', context)

@login_required
def view_activity_log(request, log_nanoid):
    """View details of a specific activity log"""
    # Check if user is a student
    if not request.user.groups.filter(name='student').exists():
        messages.error(request, 'Only students can view activity logs.')
        return redirect('home')
    
    # Get student profile
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_profile')
    
    # Get the weekly log (ensuring it belongs to the current student)
    try:
        activity_log = StudentActivityLog.objects.get(
            nanoid=log_nanoid,
            internship__student=student_profile
        )
    except StudentActivityLog.DoesNotExist:
        messages.error(request, 'Activity log not found or access denied.')
        return redirect('student_activities')
    
    # Get all activities for this log
    activities = StudentActivity.objects.filter(
        activity_log=activity_log
    ).order_by('date_performed')
    
    # Calculate total hours
    total_hours = sum(activity.hours_spent for activity in activities)
    
    context = {
        'activity_log': activity_log,
        'activities': activities,
        'total_hours': total_hours,
        'student_profile': student_profile,
        'current_internship': activity_log.internship,
    }
    return render(request, 'app/view_activity_log.html', context)

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
                return redirect_to_role_dashboard(request.user)
        except MentorProfile.DoesNotExist:
            messages.error(request, 'Please complete your mentor profile first.')
            return redirect('create_profile')
    else:  # teacher
        try:
            profile = request.user.teacher_profile
            if not profile.can_register_organization:
                messages.error(request, 'You do not have permission to register new organizations.')
                return redirect_to_role_dashboard(request.user)
        except TeacherProfile.DoesNotExist:
            messages.error(request, 'Please complete your teacher profile first.')
            return redirect('create_profile')
    
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
            return redirect('create_profile')
    elif user_type == 'teacher':
        try:
            profile = request.user.teacher_profile
            requests = OrganizationRegistrationRequest.objects.filter(requested_by_teacher=profile)
        except TeacherProfile.DoesNotExist:
            messages.error(request, 'Teacher profile not found.')
            return redirect('create_profile')
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
            return redirect_to_role_dashboard(request.user)
    except OfficialProfile.DoesNotExist:
        messages.error(request, 'Please complete your official profile first.')
        return redirect('create_profile')
    
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

@login_required
def mentor_positions(request):
    """View all positions created by the mentor"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get all positions with related data
    positions = InternshipPosition.objects.filter(mentor=mentor_profile).annotate(
        application_count=Count('applications')
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        positions = positions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(skills_required__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'active':
            positions = positions.filter(is_active=True, end_date__gte=timezone.now().date())
        elif status_filter == 'inactive':
            positions = positions.filter(is_active=False)
        elif status_filter == 'expired':
            positions = positions.filter(end_date__lt=timezone.now().date())
        elif status_filter == 'draft':
            # Assuming draft means positions without proper dates or inactive
            positions = positions.filter(Q(start_date__isnull=True) | Q(end_date__isnull=True) | Q(is_active=False))
    
    # Pagination
    paginator = Paginator(positions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'mentor_profile': mentor_profile,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_positions': positions.count(),
        'today': timezone.now().date(),
    }
    
    return render(request, 'app/mentor_positions.html', context)

@login_required
def mentor_applications(request):
    """View all applications received by the mentor"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get all applications for mentor's positions
    applications = InternshipApplication.objects.filter(
        position__mentor=mentor_profile
    ).select_related(
        'student__user', 'position'
    ).order_by('-applied_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        applications = applications.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__user__email__icontains=search_query) |
            Q(position__title__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Position filter
    position_filter = request.GET.get('position', '')
    position_filter_name = None
    if position_filter:
        try:
            filtered_position = InternshipPosition.objects.get(
                nanoid=position_filter, 
                mentor=mentor_profile
            )
            applications = applications.filter(position=filtered_position)
            position_filter_name = filtered_position.title
        except InternshipPosition.DoesNotExist:
            # If position doesn't exist or doesn't belong to mentor, ignore filter
            position_filter = ''
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get mentor's positions for filter dropdown
    mentor_positions = InternshipPosition.objects.filter(mentor=mentor_profile)
    
    context = {
        'mentor_profile': mentor_profile,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'position_filter': position_filter,
        'position_filter_name': position_filter_name,
        'mentor_positions': mentor_positions,
        'total_applications': applications.count(),
    }
    
    return render(request, 'app/mentor_applications.html', context)

@login_required
def accept_application(request, application_nanoid):
    """Accept a student application (mentor only)"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    try:
        application = InternshipApplication.objects.select_related(
            'student__user', 'position__company'
        ).get(
            nanoid=application_nanoid,
            position__mentor=mentor_profile
        )
    except InternshipApplication.DoesNotExist:
        messages.error(request, 'Application not found or access denied.')
        return redirect('mentor_applications')
    
    # Check if application can be accepted
    if application.status not in ['pending', 'under_review']:
        status_display = dict(InternshipApplication.STATUS_CHOICES).get(application.status or 'unknown', 'Unknown')
        messages.error(request, f'Cannot accept application with status: {status_display}')
        return redirect('mentor_applications')
    
    if request.method == 'POST':
        # Update application status
        application.status = 'approved'
        application.reviewed_at = timezone.now()
        application.reviewer_notes = request.POST.get('notes', '')
        application.save()
        
        # Create internship record
        try:
            from datetime import datetime
            
            # Calculate start and end dates (start today, duration from position)
            start_date = datetime.now().date()
            duration_months = 3  # Default duration
            if application.position and hasattr(application.position, 'duration') and application.position.duration:
                try:
                    duration_months = int(application.position.duration)
                except (ValueError, TypeError):
                    duration_months = 3
            
            end_date = start_date + timedelta(days=duration_months * 30)  # Approximate months to days
            
            # Get mentor from position
            mentor = application.position.mentor if application.position else None
            
            internship = Internship.objects.create(
                application=application,
                student=application.student,
                mentor=mentor,
                teacher=None,  # Teacher assignment can be done separately
                start_date=start_date,
                end_date=end_date,
                status='active'
            )
            
        except Exception as e:
            # Log error but continue - internship can be created manually later
            pass
        
        # Create notification for student
        try:
            from .models import Notification
            student_name = application.student.user.get_full_name() if application.student and application.student.user else 'Student'
            position_title = application.position.title if application.position else 'Position'
            company_name = application.position.company.name if application.position and application.position.company else 'Company'
            
            Notification.objects.create(
                recipient=application.student.user,
                title="Application Approved!",
                message=f"Congratulations! Your application for {position_title} at {company_name} has been approved. Check your email for next steps.",
                notification_type='application_status'
            )
        except Exception as e:
            # Continue even if notification creation fails
            pass
        
        student_name = application.student.user.get_full_name() if application.student and application.student.user else 'Student'
        messages.success(request, f'Application from {student_name} has been approved!')
        return redirect('mentor_applications')
    
    context = {
        'application': application,
        'mentor_profile': mentor_profile,
    }
    return render(request, 'app/accept_application.html', context)

@login_required
def reject_application(request, application_nanoid):
    """Reject a student application (mentor only)"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    try:
        application = InternshipApplication.objects.select_related(
            'student__user', 'position__company'
        ).get(
            nanoid=application_nanoid,
            position__mentor=mentor_profile
        )
    except InternshipApplication.DoesNotExist:
        messages.error(request, 'Application not found or access denied.')
        return redirect('mentor_applications')
    
    # Check if application can be rejected
    if application.status not in ['pending', 'under_review']:
        status_display = dict(InternshipApplication.STATUS_CHOICES).get(application.status or 'unknown', 'Unknown')
        messages.error(request, f'Cannot reject application with status: {status_display}')
        return redirect('mentor_applications')
    
    if request.method == 'POST':
        # Update application status
        application.status = 'rejected'
        application.reviewed_at = timezone.now()
        application.reviewer_notes = request.POST.get('feedback', '')
        application.save()
        
        # Create notification for student
        try:
            from .models import Notification
            feedback_message = request.POST.get('feedback', '')
            position_title = application.position.title if application.position else 'Position'
            company_name = application.position.company.name if application.position and application.position.company else 'Company'
            
            notification_message = f"Thank you for your interest in {position_title} at {company_name}. Unfortunately, your application was not selected at this time."
            if feedback_message:
                notification_message += f"\n\nFeedback: {feedback_message}"
            
            Notification.objects.create(
                recipient=application.student.user,
                title="Application Status Update",
                message=notification_message,
                notification_type='application_status'
            )
        except Exception as e:
            # Continue even if notification creation fails
            pass
        
        student_name = application.student.user.get_full_name() if application.student and application.student.user else 'Student'
        messages.success(request, f'Application from {student_name} has been rejected.')
        return redirect('mentor_applications')
    
    context = {
        'application': application,
        'mentor_profile': mentor_profile,
    }
    return render(request, 'app/reject_application.html', context)

@login_required
def application_detail(request, application_nanoid):
    """View detailed application information (mentor only)"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    try:
        application = InternshipApplication.objects.select_related(
            'student__user', 'position__company'
        ).get(
            nanoid=application_nanoid,
            position__mentor=mentor_profile
        )
    except InternshipApplication.DoesNotExist:
        messages.error(request, 'Application not found or access denied.')
        return redirect('mentor_applications')
    
    context = {
        'application': application,
        'mentor_profile': mentor_profile,
    }
    return render(request, 'app/application_detail.html', context)

@login_required
def mentor_interns(request):
    """View all active and past interns"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get all internships for this mentor
    internships = Internship.objects.filter(
        mentor=mentor_profile
    ).select_related(
        'student__user', 'application__position'
    ).order_by('-start_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        internships = internships.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__user__email__icontains=search_query) |
            Q(application__position__title__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        internships = internships.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(internships, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    active_interns = internships.filter(status='active').count()
    completed_interns = internships.filter(status='completed').count()
    
    context = {
        'mentor_profile': mentor_profile,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_interns': internships.count(),
        'active_interns': active_interns,
        'completed_interns': completed_interns,
    }
    
    return render(request, 'app/mentor_interns.html', context)

@login_required
def student_profile_detail(request, student_nanoid):
    """View detailed student profile (for mentors to view their interns)"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get the student profile and verify mentor has access
    try:
        student_profile = StudentProfile.objects.select_related(
            'user', 'institute'
        ).get(nanoid=student_nanoid)
        
        # Verify this mentor has an internship with this student
        internship = Internship.objects.filter(
            mentor=mentor_profile,
            student=student_profile
        ).first()
        
        if not internship:
            messages.error(request, 'Access denied. You can only view profiles of your interns.')
            return redirect('mentor_interns')
            
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('mentor_interns')
    
    context = {
        'student_profile': student_profile,
        'mentor_profile': mentor_profile,
        'internship': internship,
    }
    return render(request, 'app/student_profile_detail.html', context)

@login_required
def create_progress_report(request, internship_nanoid):
    """Create a mentor progress report for an intern"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get the internship
    internship = get_object_or_404(Internship, nanoid=internship_nanoid, mentor=mentor_profile)
    
    if request.method == 'POST':
        # Get form data
        week_number = request.POST.get('week_number')
        student_performance = request.POST.get('student_performance')
        skills_demonstrated = request.POST.get('skills_demonstrated')
        areas_for_improvement = request.POST.get('areas_for_improvement')
        attendance_rating = request.POST.get('attendance_rating')
        
        # Validate required fields
        if not week_number or not student_performance:
            messages.error(request, 'Week number and student performance are required.')
        else:
            try:
                # Check if report for this week already exists
                existing_report = ProgressReport.objects.filter(
                    internship=internship,
                    report_type='mentor',
                    week_number=int(week_number)
                ).first()
                
                if existing_report:
                    messages.error(request, f'Progress report for week {week_number} already exists.')
                else:
                    # Create new progress report
                    ProgressReport.objects.create(
                        internship=internship,
                        report_type='mentor',
                        reporter=request.user,
                        week_number=int(week_number),
                        student_performance=student_performance,
                        skills_demonstrated=skills_demonstrated,
                        areas_for_improvement=areas_for_improvement,
                        attendance_rating=int(attendance_rating) if attendance_rating else None
                    )
                    
                    messages.success(request, f'Progress report for week {week_number} created successfully.')
                    return redirect('mentor_progress_reports', internship_nanoid=internship_nanoid)
            
            except ValueError:
                messages.error(request, 'Please enter valid numbers for week and rating.')
            except Exception as e:
                messages.error(request, f'Error creating progress report: {str(e)}')
    
    # Get existing reports for context
    existing_reports = ProgressReport.objects.filter(
        internship=internship,
        report_type='mentor'
    ).order_by('-week_number')
    
    context = {
        'mentor_profile': mentor_profile,
        'internship': internship,
        'existing_reports': existing_reports,
    }
    
    return render(request, 'app/create_progress_report.html', context)

@login_required
def mentor_progress_reports(request, internship_nanoid):
    """View all progress reports for a specific internship"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get the internship
    internship = get_object_or_404(Internship, nanoid=internship_nanoid, mentor=mentor_profile)
    
    # Get all progress reports for this internship
    mentor_reports = ProgressReport.objects.filter(
        internship=internship,
        report_type='mentor'
    ).order_by('-week_number')
    
    student_reports = ProgressReport.objects.filter(
        internship=internship,
        report_type='student'
    ).order_by('-week_number')
    
    teacher_reports = ProgressReport.objects.filter(
        internship=internship,
        report_type='teacher'
    ).order_by('-week_number')
    
    context = {
        'mentor_profile': mentor_profile,
        'internship': internship,
        'mentor_reports': mentor_reports,
        'student_reports': student_reports,
        'teacher_reports': teacher_reports,
        'total_reports': mentor_reports.count() + student_reports.count() + teacher_reports.count(),
    }
    
    return render(request, 'app/mentor_progress_reports.html', context)

@login_required
def edit_progress_report(request, report_nanoid):
    """Edit a mentor progress report"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get the progress report
    report = get_object_or_404(
        ProgressReport, 
        nanoid=report_nanoid, 
        report_type='mentor',
        internship__mentor=mentor_profile
    )
    
    if request.method == 'POST':
        # Get form data
        student_performance = request.POST.get('student_performance')
        skills_demonstrated = request.POST.get('skills_demonstrated')
        areas_for_improvement = request.POST.get('areas_for_improvement')
        attendance_rating = request.POST.get('attendance_rating')
        
        # Validate required fields
        if not student_performance:
            messages.error(request, 'Student performance is required.')
        else:
            try:
                # Update progress report
                report.student_performance = student_performance
                report.skills_demonstrated = skills_demonstrated
                report.areas_for_improvement = areas_for_improvement
                report.attendance_rating = int(attendance_rating) if attendance_rating else None
                report.save()
                
                messages.success(request, f'Progress report for week {report.week_number} updated successfully.')
                return redirect('mentor_progress_reports', internship_nanoid=report.internship.nanoid)
            
            except ValueError:
                messages.error(request, 'Please enter a valid number for rating.')
            except Exception as e:
                messages.error(request, f'Error updating progress report: {str(e)}')
    
    context = {
        'mentor_profile': mentor_profile,
        'report': report,
        'internship': report.internship,
    }
    
    return render(request, 'app/edit_progress_report.html', context)

def component_demo(request):
    """Demo page showing custom CSS components"""
    return render(request, 'app/component_demo.html')

def documentation_index(request):
    """Documentation homepage with available guides"""
    return render(request, 'docs/index.html')

def documentation_guide(request, user_type, topic):
    """Render a specific documentation guide"""
    # Define available guide templates organized by user type
    guide_templates = {
        'getting-started': {
            'overview': 'docs/getting-started/overview.html',
            'account-setup': 'docs/getting-started/account-setup.html',
        },
        'students': {
            'dashboard': 'docs/students/dashboard.html',
            'profile-management': 'docs/students/profile-management.html',
            'finding-internships': 'docs/students/finding-internships.html',
            'applying-positions': 'docs/students/applying-positions.html',
            'managing-applications': 'docs/students/managing-applications.html',
            'application-progress': 'docs/students/application-progress.html',
        },
        'mentors': {
            'dashboard': 'docs/mentors/dashboard.html',
            'creating-positions': 'docs/mentors/creating-positions.html',
            'managing-applications': 'docs/mentors/managing-applications.html',
            'intern-supervision': 'docs/mentors/intern-supervision.html',
            'company-registration': 'docs/mentors/company-registration.html',
        },
        'teachers': {
            'dashboard': 'docs/teachers/dashboard.html',
            'student-supervision': 'docs/teachers/student-supervision.html',
            'progress-monitoring': 'docs/teachers/progress-monitoring.html',
            'institute-registration': 'docs/teachers/institute-registration.html',
        },
        'officials': {
            'dashboard': 'docs/officials/dashboard.html',
            'managing-organizations': 'docs/officials/managing-organizations.html',
            'system-administration': 'docs/officials/system-administration.html',
        },
    }
    
    # Check if the requested guide exists
    if user_type in guide_templates and topic in guide_templates[user_type]:
        template_name = guide_templates[user_type][topic]
        return render(request, template_name)
    else:
        raise Http404("Documentation page not found")

# Public pages
def about(request):
    """About page"""
    return render(request, 'app/about.html')

def contact(request):
    """Contact page"""
    return render(request, 'app/contact.html')

def privacy_policy(request):
    """Privacy policy page"""
    return render(request, 'app/privacy_policy.html')

def terms_of_service(request):
    """Terms of service page"""
    return render(request, 'app/terms_of_service.html')

def anti_harassment_policy(request):
    """Anti-sexual harassment policy page"""
    return render(request, 'app/anti_harassment_policy.html')

def dashboard_redirect(request):
    """Generic dashboard redirect"""
    if request.user.is_authenticated:
        return redirect_to_role_dashboard(request.user)
    else:
        return redirect('account_login')
