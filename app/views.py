from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse, Http404, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import os
from django.conf import settings
from .models import (
    Student, Mentor, Teacher, Official,
    Position, Application, Internship, Company, Institute, 
    Notification, Evaluation, Report, Log, Entry, Assessment
)
from .forms import (
    LogForm, EntryFormSet, EntryForm, ProfileCompletionForm,
    InstituteForm, CompanyForm, StudentForm, MentorForm,
    TeacherForm, OfficialForm, PositionForm,
    ApplicationForm, ReportForm,
    AssessmentForm, InternshipForm, EvaluationForm,
    PositionSearchForm, CompanyAdminForm, InstituteAdminForm
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
        'total_students': Student.objects.count(),
        'active_internships': Internship.objects.filter(status='active').count(),
        'total_positions': Position.objects.filter(is_active=True).count(),
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
        student_profile = request.user.student
    except Student.DoesNotExist:
        messages.warning(request, 'Please complete your student profile first.')
        return redirect('create_profile')
    
    # Get student's applications
    applications = Application.objects.filter(student=student_profile).order_by('-applied_at')
    
    # Get available positions
    available_positions = Position.objects.filter(
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get mentor's positions and applications
    positions = Position.objects.filter(mentor=mentor_profile)
    pending_applications = Application.objects.filter(
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
        teacher_profile = request.user.teacher
    except Teacher.DoesNotExist:
        messages.warning(request, 'Please complete your teacher profile first.')
        return redirect('create_profile')
    
    # Get students from same institute
    institute_students = Student.objects.filter(
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
        'total_students': Student.objects.count(),
        'total_mentors': Mentor.objects.count(),
        'total_companies': Company.objects.count(),
        'verified_companies': Company.objects.filter(is_verified=True).count(),
        'total_positions': Position.objects.count(),
        'active_positions': Position.objects.filter(is_active=True).count(),
        'total_applications': Application.objects.count(),
        'pending_applications': Application.objects.filter(status='pending').count(),
        'active_internships': Internship.objects.filter(status='active').count(),
        'completed_internships': Internship.objects.filter(status='completed').count(),
    }
    
    # Recent activity
    recent_applications = Application.objects.order_by('-applied_at')[:10]
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
        teacher_profile = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Please create your teacher profile first.')
        return redirect('create_profile')
    
    # Get students from the same institute
    students = Student.objects.filter(
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
        'year_choices': Student.SEMESTER_CHOICES,
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
        teacher_profile = request.user.teacher
    except Teacher.DoesNotExist:
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
        teacher_profile = request.user.teacher
    except Teacher.DoesNotExist:
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
    activity_logs = internship.activity_logs.all().order_by('-week_starting')
    
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
        teacher_profile = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Please complete your teacher profile first.')
        return redirect('complete_profile')
    
    # Get all reports for students from teacher's institute
    reports = Report.objects.filter(
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
    students = Student.objects.filter(
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
        teacher_profile = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Please complete your teacher profile first.')
        return redirect('complete_profile')
    
    try:
        report = Report.objects.select_related(
            'internship__student__user', 'teacher__user', 'internship__mentor__user', 'internship__mentor__company'
        ).get(nanoid=report_nanoid)
        
        # Ensure the report belongs to a student from teacher's institute
        if report.internship.student.institute != teacher_profile.institute:
            messages.error(request, 'This report does not belong to a student from your institute.')
            return redirect('teacher_reports')
            
    except Report.DoesNotExist:
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
        teacher_profile = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, 'Please create your teacher profile first.')
        return redirect('create_profile')
    
    if not (teacher_profile.can_edit_institute() or teacher_profile.can_manage_institute()):
        messages.error(request, 'You can only edit institutes that you registered or manage as an administrative contact.')
        return redirect_to_role_dashboard(request.user)
    
    institute = teacher_profile.institute
    
    if request.method == 'POST':
        form = InstituteForm(request.POST, instance=institute)
        if form.is_valid():
            form.save()
            messages.success(request, f'Institute "{institute.name}" updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InstituteForm(instance=institute)
    
    context = {
        'form': form,
        'institute': institute,
        'teacher_profile': teacher_profile,
    }
    return render(request, 'app/edit_institute.html', context)

@login_required
def manage_companies(request):
    """Official view to manage companies with search and filtering"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    # Get all companies with filtering
    companies = Company.objects.all().order_by('-created_at')
    
    # Process admin filter form
    form = CompanyAdminForm(request.GET or None)
    if form.is_valid():
        # Search functionality
        search_query = form.cleaned_data.get('search')
        if search_query:
            companies = companies.filter(
                Q(name__icontains=search_query) |
                Q(industry__icontains=search_query) |
                Q(contact_email__icontains=search_query)
            )
        
        # Filter by registration status
        status_filter = form.cleaned_data.get('status')
        if status_filter:
            companies = companies.filter(registration_status=status_filter)
        
        # Filter by domain verification
        domain_verified = form.cleaned_data.get('domain_verified')
        if domain_verified is not None:
            companies = companies.filter(domain_verified=domain_verified)
        
        # Filter by industry
        industry_filter = form.cleaned_data.get('industry')
        if industry_filter:
            companies = companies.filter(industry__icontains=industry_filter)
        
        # Filter by creation date
        created_after = form.cleaned_data.get('created_after')
        if created_after:
            companies = companies.filter(created_at__date__gte=created_after)
    
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
        'form': form,
        'page_obj': page_obj,
        'stats': stats,
        'filtered_count': companies.count(),
    }
    return render(request, 'app/manage_companies.html', context)

@login_required
def mass_verify_companies(request):
    """Official view to mass verify companies"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    # Get the official profile
    try:
        official_profile = request.user.official
    except Official.DoesNotExist:
        messages.error(request, 'Official profile not found.')
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
                approved_by=official_profile
            )
            messages.success(request, f'Successfully approved {updated_count} companies.')
            
        elif action == 'reject':
            # Reject selected companies
            updated_count = companies.update(
                registration_status='rejected',
                approved_at=timezone.now(),
                approved_by=official_profile
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
    """Official view to manage institutes with search and filtering"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    # Get all institutes with filtering
    institutes = Institute.objects.all().order_by('-created_at')
    
    # Process admin filter form
    form = InstituteAdminForm(request.GET or None)
    if form.is_valid():
        # Search functionality
        search_query = form.cleaned_data.get('search')
        if search_query:
            institutes = institutes.filter(
                Q(name__icontains=search_query) |
                Q(contact_email__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        
        # Filter by registration status
        status_filter = form.cleaned_data.get('status')
        if status_filter:
            institutes = institutes.filter(registration_status=status_filter)
        
        # Filter by domain verification
        domain_verified = form.cleaned_data.get('domain_verified')
        if domain_verified is not None:
            institutes = institutes.filter(domain_verified=domain_verified)
        
        # Filter by institute type
        institute_type_filter = form.cleaned_data.get('institute_type')
        if institute_type_filter:
            institutes = institutes.filter(institute_type__icontains=institute_type_filter)
        
        # Filter by city
        city_filter = form.cleaned_data.get('city')
        if city_filter:
            institutes = institutes.filter(
                Q(city__icontains=city_filter) |
                Q(address__icontains=city_filter)
            )
    
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
        'form': form,
        'page_obj': page_obj,
        'stats': stats,
        'filtered_count': institutes.count(),
    }
    return render(request, 'app/manage_institutes.html', context)

@login_required
def mass_verify_institutes(request):
    """Official view to mass verify institutes"""
    user_type = get_user_type(request.user)
    if user_type != 'official':
        messages.error(request, 'Access denied. Official account required.')
        return redirect('home')
    
    # Get the official profile
    try:
        official_profile = request.user.official
    except Official.DoesNotExist:
        messages.error(request, 'Official profile not found.')
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
                approved_by=official_profile
            )
            messages.success(request, f'Successfully approved {updated_count} institutes.')
            
        elif action == 'reject':
            # Reject selected institutes
            updated_count = institutes.update(
                registration_status='rejected',
                approved_at=timezone.now(),
                approved_by=official_profile
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
        'total_positions': Position.objects.count(),
        'active_positions': Position.objects.filter(is_active=True).count(),
        'total_applications': Application.objects.count(),
        'pending_applications': Application.objects.filter(status='pending').count(),
        'accepted_applications': Application.objects.filter(status='accepted').count(),
        'rejected_applications': Application.objects.filter(status='rejected').count(),
        
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
        'new_applications': Application.objects.filter(applied_at__gte=thirty_days_ago).count(),
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
            'applications': Application.objects.filter(applied_at__range=[month_start, month_end]).count(),
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
    total_apps = Application.objects.count()
    if total_apps > 0:
        accepted_apps = Application.objects.filter(status='accepted').count()
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
            company.approved_by = request.user.official
            company.approved_at = timezone.now()
            company.registration_notes = notes
            company.save()
            messages.success(request, f'Company "{company.name}" has been approved.')
            
        elif action == 'reject':
            company.registration_status = 'rejected'
            company.approved_by = request.user.official
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
    mentors = Mentor.objects.filter(company=company)
    positions = Position.objects.filter(company=company).order_by('-created_at')
    
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
            institute.approved_by = request.user.official
            institute.approved_at = timezone.now()
            institute.registration_notes = notes
            institute.save()
            messages.success(request, f'Institute "{institute.name}" has been approved.')
            
        elif action == 'reject':
            institute.registration_status = 'rejected'
            institute.approved_by = request.user.official
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
    teachers = Teacher.objects.filter(institute=institute)
    students = Student.objects.filter(institute=institute)
    
    context = {
        'institute': institute,
        'teachers': teachers,
        'students': students,
    }
    return render(request, 'app/institute_detail_official.html', context)

def browse_positions(request):
    """Browse available internship positions with search and filtering"""
    positions = Position.objects.filter(is_active=True).order_by('-created_at')
    
    # Process search form
    form = PositionSearchForm(request.GET or None)
    if form.is_valid():
        # Search functionality
        search_query = form.cleaned_data.get('search')
        if search_query:
            positions = positions.filter(
                Q(title__icontains=search_query) |
                Q(company__name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by company
        company_filter = form.cleaned_data.get('company')
        if company_filter:
            positions = positions.filter(company=company_filter)
        
        # Filter by duration
        duration_filter = form.cleaned_data.get('duration')
        if duration_filter:
            positions = positions.filter(duration=duration_filter)
        
        # Filter by location
        location_filter = form.cleaned_data.get('location')
        if location_filter:
            positions = positions.filter(
                Q(location__icontains=location_filter) |
                Q(company__city__icontains=location_filter)
            )
        
        # Filter by remote allowed
        if form.cleaned_data.get('remote_allowed'):
            positions = positions.filter(remote_allowed=True)
        
        # Filter by minimum stipend
        min_stipend = form.cleaned_data.get('min_stipend')
        if min_stipend:
            positions = positions.filter(stipend__gte=min_stipend)
    
    # Pagination
    paginator = Paginator(positions, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_positions': positions.count(),
    }
    return render(request, 'app/browse_positions.html', context)

def position_detail(request, position_nanoid):
    """View detailed information about a specific internship position"""
    position = get_object_or_404(Position, nanoid=position_nanoid, is_active=True)
    
    # Check if current user (if student) has already applied
    user_application = None
    if request.user.is_authenticated and get_user_type(request.user) == 'student':
        try:
            student_profile = request.user.student
            user_application = Application.objects.get(
                student=student_profile, position=position
            )
        except (Student.DoesNotExist, Application.DoesNotExist):
            pass
    
    # Calculate number of applications
    total_applications = position.applications.count()
    
    # Get other positions from the same company (max 3)
    related_positions = Position.objects.filter(
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

@login_required
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
        student_profile = request.user.student
    except Student.DoesNotExist:
        messages.warning(request, 'Please complete your student profile first.')
        return redirect('create_profile')
    
    # For now, redirect to edit profile - we can create a view template later
    return redirect('edit_profile')

def mentor_profile_view(request):
    """Mentor profile display view"""
    try:
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # For now, redirect to edit profile - we can create a view template later
    return redirect('edit_profile')

def teacher_profile_view(request):
    """Teacher profile display view"""
    try:
        teacher_profile = request.user.teacher
    except Teacher.DoesNotExist:
        messages.warning(request, 'Please complete your teacher profile first.')
        return redirect('create_profile')
    
    # For now, redirect to edit profile - we can create a view template later
    return redirect('edit_profile')

def official_profile_view(request):
    """Official profile display view"""
    try:
        official_profile = request.user.official
    except Official.DoesNotExist:
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
            student_profile = Student.objects.create(
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
            mentor_profile = Mentor.objects.create(
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
            teacher_profile = Teacher.objects.create(
                user=request.user,
                # Set defaults for optional fields
                department='',
                title='',
                employee_id=''
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
        profile = request.user.student
    except Student.DoesNotExist:
        messages.warning(request, 'Please create your student profile first.')
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # Validate institute membership before saving
            new_institute = form.cleaned_data.get('institute')
            if new_institute and new_institute != profile.institute:
                is_valid, error_message = validate_user_organization_membership(
                    request.user, 'institute', new_institute.pk
                )
                if not is_valid:
                    messages.error(request, error_message or "Invalid organization selection.")
                    available_institutes = get_available_institutes_for_user(request.user)
                    return render(request, 'app/edit_student_profile.html', {
                        'form': form,
                        'profile': profile,
                        'institutes': available_institutes,
                        'domain_error': True,
                    })
            
            # Handle resume deletion
            if 'delete_resume' in request.POST and profile.resume:
                print(f"DEBUG: Deleting resume for user {request.user.username}")
                profile.resume.delete(save=False)
                profile.resume = None
                profile.save()
                print(f"DEBUG: Resume deleted successfully")
            
            # Save the profile and user data
            form.save(user=request.user)
            messages.success(request, 'Profile updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Create form with initial user data
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = StudentForm(instance=profile, initial=initial_data, user=request.user)
    
    available_institutes = get_available_institutes_for_user(request.user)
    context = {
        'form': form,
        'profile': profile,
        'institutes': available_institutes,
    }
    return render(request, 'app/edit_student_profile.html', context)

def edit_mentor_profile_view(request):
    """Mentor profile editing view"""
    try:
        profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please create your mentor profile first.')
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = MentorForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            # Validate company membership before saving
            new_company = form.cleaned_data.get('company')
            if new_company and new_company != profile.company:
                is_valid, error_message = validate_user_organization_membership(
                    request.user, 'company', new_company.pk
                )
                if not is_valid:
                    messages.error(request, error_message or "Invalid organization selection.")
                    available_companies = get_available_companies_for_user(request.user)
                    return render(request, 'app/edit_mentor_profile.html', {
                        'form': form,
                        'profile': profile,
                        'companies': available_companies,
                        'domain_error': True,
                    })
            
            # Save the profile using the form
            form.save()
            
            # Update user fields from request.POST
            user_fields = ['first_name', 'last_name', 'email']
            for field in user_fields:
                if field in request.POST:
                    setattr(request.user, field, request.POST[field])
            request.user.save()
            
            # Handle additional fields that might be in the template but not in the model
            # (linkedin_profile, bio, max_interns, preferred_duration are not in Mentor model)
            # These will be ignored for now until model is updated
            
            messages.success(request, 'Profile updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MentorForm(instance=profile, user=request.user)
    
    available_companies = get_available_companies_for_user(request.user)
    context = {
        'form': form,
        'profile': profile,
        'companies': available_companies,
    }
    return render(request, 'app/edit_mentor_profile.html', context)

def edit_teacher_profile_view(request):
    """Teacher profile editing view"""
    try:
        profile = request.user.teacher
    except Teacher.DoesNotExist:
        messages.warning(request, 'Please create your teacher profile first.')
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            # Validate institute membership before saving
            new_institute = form.cleaned_data.get('institute')
            if new_institute and new_institute != profile.institute:
                is_valid, error_message = validate_user_organization_membership(
                    request.user, 'institute', new_institute.pk
                )
                if not is_valid:
                    messages.error(request, error_message or "Invalid organization selection.")
                    available_institutes = get_available_institutes_for_user(request.user)
                    return render(request, 'app/edit_teacher_profile.html', {
                        'form': form,
                        'profile': profile,
                        'institutes': available_institutes,
                        'domain_error': True,
                    })
            
            # Save the profile using the form
            form.save()
            
            # Update user fields from POST data (not from form since they're not in the form)
            user_fields = ['first_name', 'last_name', 'email']
            user_updated = False
            for field in user_fields:
                if field in request.POST:
                    new_value = request.POST.get(field, '').strip()
                    if new_value and getattr(request.user, field) != new_value:
                        setattr(request.user, field, new_value)
                        user_updated = True
            
            if user_updated:
                request.user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherForm(instance=profile, user=request.user)
    
    available_institutes = get_available_institutes_for_user(request.user)
    context = {
        'form': form,
        'profile': profile,
        'institutes': available_institutes,
    }
    return render(request, 'app/edit_teacher_profile.html', context)

def edit_official_profile_view(request):
    """Official profile editing view"""
    try:
        profile = request.user.official
    except Official.DoesNotExist:
        # Create a basic official profile if it doesn't exist
        profile = Official.objects.create(
            user=request.user,
            department="Not specified"
        )
        messages.success(request, 'Official profile created successfully.')
    
    if request.method == 'POST':
        form = OfficialForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            # Save the profile using the form
            form.save()
            
            # Update user fields if provided in form
            user_fields = ['first_name', 'last_name', 'email']
            for field in user_fields:
                if field in form.cleaned_data:
                    setattr(request.user, field, form.cleaned_data[field])
            request.user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = OfficialForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
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
        profile = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Please create your student profile first.')
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # Validate institute membership before updating
            new_institute = form.cleaned_data.get('institute')
            if new_institute and new_institute != profile.institute:
                is_valid, error_message = validate_user_organization_membership(
                    request.user, 'institute', new_institute.pk
                )
                if not is_valid:
                    messages.error(request, error_message or "Invalid organization selection.")
                    available_institutes = get_available_institutes_for_user(request.user)
                    return render(request, 'app/edit_student_profile.html', {
                        'form': form,
                        'profile': profile,
                        'institutes': available_institutes,
                        'domain_error': True,
                    })
            
            # Handle resume deletion
            if 'delete_resume' in request.POST and profile.resume:
                profile.resume.delete(save=False)
                profile.resume = None
                profile.save()
            
            # Save form with user data
            form.save(user=request.user)
            messages.success(request, 'Profile updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Create form with initial user data
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = StudentForm(instance=profile, initial=initial_data, user=request.user)
    
    available_institutes = get_available_institutes_for_user(request.user)
    context = {
        'form': form,
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
        profile = request.user.mentor
    except Mentor.DoesNotExist:
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
        profile.job_title = request.POST.get('position')
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.error(request, 'Please create your mentor profile first.')
        return redirect('create_profile')
    
    if not mentor_profile.can_edit_company():
        messages.error(request, 'You can only edit companies that you registered.')
        return redirect_to_role_dashboard(request.user)
    
    company = mentor_profile.company
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f'Company "{company.name}" updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CompanyForm(instance=company)
    
    context = {
        'form': form,
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
        profile = request.user.teacher
    except Teacher.DoesNotExist:
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
        profile = request.user.official
    except Official.DoesNotExist:
        messages.error(request, 'Please create your official profile first.')
        return redirect('home')  # No create view for officials yet
    
    if request.method == 'POST':
        # Update profile fields
        profile.department = request.POST.get('department')
        profile.job_title = request.POST.get('position')
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.error(request, 'Please create your mentor profile first.')
        return redirect('create_profile')
    
    if not mentor_profile.is_verified:
        messages.error(request, 'Your mentor profile must be verified before creating positions.')
        return redirect_to_role_dashboard(request.user)
    
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            # Create new position with automatic company and mentor assignment
            position = form.save(commit=False)
            position.company = mentor_profile.company
            position.mentor = mentor_profile
            position.save()
            
            messages.success(request, f'Position "{position.title}" created successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PositionForm()
    
    context = {
        'form': form,
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
        mentor_profile = request.user.mentor
        position = Position.objects.get(nanoid=position_nanoid, mentor=mentor_profile)
    except (Mentor.DoesNotExist, Position.DoesNotExist):
        messages.error(request, 'Position not found or access denied.')
        return redirect_to_role_dashboard(request.user)
    
    # Check if position has applications - prevent editing if it does
    has_applications = position.applications.exists()
    if has_applications and request.method == 'POST':
        messages.error(request, 'Cannot edit position that already has applications. Please create a new position instead.')
        return redirect_to_role_dashboard(request.user)
    
    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(request, f'Position "{position.title}" updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PositionForm(instance=position)
    
    context = {
        'form': form,
        'position': position,
        'mentor_profile': mentor_profile,
        'has_applications': has_applications,
    }
    return render(request, 'app/edit_position.html', context)


@login_required
def apply_position(request, position_nanoid):
    """Handle student applications for internship positions"""
    # Get the position
    position = get_object_or_404(Position, nanoid=position_nanoid)
    
    # Check if user is a student
    if not request.user.groups.filter(name='student').exists():
        messages.error(request, 'Only students can apply for positions.')
        return redirect('position_detail', position_nanoid=position_nanoid)
    
    # Get student profile
    try:
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You must complete your student profile before applying.')
        return redirect('create_profile')
    
    # Check HEC eligibility: Only 4th-8th semester students can apply for internships
    if not student_profile.semester_of_study or student_profile.semester_of_study not in ['4', '5', '6', '7', '8']:
        messages.error(request, 'Only students from 4th to 8th semester are eligible for internships as per HEC policy.')
        return redirect('position_detail', position_nanoid=position_nanoid)
    
    # Check if student has an active application (pending, under_review, interview_scheduled, approved)
    active_application = Application.objects.filter(
        student=student_profile,
        position=position,
        status__in=['pending', 'under_review', 'interview_scheduled', 'approved']
    ).first()
    
    if active_application:
        messages.info(request, f'You have an active application for this position with status: {active_application.get_status_display()}.')
        return redirect('position_detail', position_nanoid=position_nanoid)
    
    # Check for previous applications to show appropriate messaging
    previous_applications = Application.objects.filter(
        student=student_profile,
        position=position,
        status__in=['rejected', 'withdrawn']
    ).order_by('-applied_at')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            # Create the application
            application = form.save(commit=False)
            application.student = student_profile
            application.position = position
            application.status = 'pending'
            application.save()
            
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
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ApplicationForm()
    
    # Get all previous applications for this position
    all_previous_applications = Application.objects.filter(
        student=student_profile,
        position=position
    ).order_by('-applied_at')
    
    context = {
        'form': form,
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
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_profile')
    
    # Get all applications for this student
    applications = Application.objects.filter(
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
        student_profile = Student.objects.get(user=request.user)
        
        # Get the application (ensuring it belongs to the current student)
        application = Application.objects.get(
            nanoid=application_id,
            student=student_profile
        )
        
        # Check if application can be withdrawn (not already approved, rejected, or withdrawn)
        if application.status in ['approved', 'rejected', 'withdrawn']:
            status_display = dict(Application.STATUS_CHOICES).get(application.status, application.status)
            messages.error(request, f'Cannot withdraw application that is already {status_display.lower()}.')
            return redirect('student_applications')
        
        # Withdraw the application
        application.status = 'withdrawn'
        application.reviewed_at = timezone.now()
        application.reviewer_notes = "Application withdrawn by student"
        application.save()
        
        position_title = application.position.title if application.position else "Unknown Position"
        messages.success(request, f'Your application for "{position_title}" has been withdrawn successfully.')
        
    except Student.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_profile')
    except Application.DoesNotExist:
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
        student_profile = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Please create your student profile first.')
        return redirect('create_profile')
    
    # Get current internship
    current_internship = Internship.objects.filter(
        student=student_profile,
        status='active'
    ).select_related(
        'application__position__company',
        'mentor__user',
        'mentor__company', 
        'teacher__user'
    ).first()
    
    # Initialize context variables
    recent_activities = []
    progress_reports = []
    
    # If there's an active internship, get related data
    if current_internship:
        # Get recent activity logs for this internship
        recent_activities = Log.objects.filter(
            internship=current_internship,
            submitted_at__gte=current_internship.created_at
        ).order_by('-week_starting')[:5]
        
        # Get any evaluations or progress reports
        progress_reports = Report.objects.filter(
            internship=current_internship
        ).order_by('-submitted_at')
    
    # Get student's applications to show internship opportunities
    student_applications = Application.objects.filter(
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
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
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
    activity_logs = Log.objects.filter(
        internship=current_internship
    ).prefetch_related('entries').order_by('-week_starting')
    
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
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
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
        log_form = LogForm(request.POST)
        entry_formset = EntryFormSet(request.POST)
        
        if log_form.is_valid() and entry_formset.is_valid():
            # Check if a log already exists for this period
            week_starting = log_form.cleaned_data['week_starting']
            existing_log = Log.objects.filter(
                internship=current_internship,
                week_starting=week_starting
            ).first()
            
            if existing_log:
                messages.error(request, f'An activity log already exists for the week starting {week_starting.strftime("%Y-%m-%d")}.')
                return redirect('student_activities')
            
            # Create the activity log
            activity_log = log_form.save(commit=False)
            activity_log.internship = current_internship
            activity_log.save()
            
            # Create the activities
            activities_created = 0
            for entry_form in entry_formset:
                if entry_form.cleaned_data and not entry_form.cleaned_data.get('DELETE', False):
                    entry = entry_form.save(commit=False)
                    entry.log = activity_log
                    entry.save()
                    activities_created += 1
            
            messages.success(request, f'Activity log created successfully with {activities_created} entries.')
            return redirect('student_activities')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        log_form = LogForm()
        entry_formset = EntryFormSet()
    
    context = {
        'log_form': log_form,
        'entry_formset': entry_formset,
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
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_profile')
    
    # Get the activity log (ensuring it belongs to the current student)
    try:
        activity_log = Log.objects.get(
            nanoid=log_nanoid,
            internship__student=student_profile
        )
    except Log.DoesNotExist:
        messages.error(request, 'Activity log not found or access denied.')
        return redirect('student_activities')
    
    if request.method == 'POST':
        log_form = LogForm(request.POST, instance=activity_log)
        
        # Get existing activities and create formset with instances
        existing_activities = Entry.objects.filter(log=activity_log).order_by('date')
        
        activity_formset = EntryFormSet(
            request.POST,
            queryset=existing_activities
        )
        
        if log_form.is_valid() and activity_formset.is_valid():
            # Save the activity log
            log_form.save()
            
            # Save the formset which will handle create/update/delete automatically
            activity_formset.save()
            
            messages.success(request, 'Activity log updated successfully.')
            return redirect('student_activities')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        log_form = LogForm(instance=activity_log)
        existing_activities = Entry.objects.filter(log=activity_log).order_by('date')
        
        activity_formset = EntryFormSet(queryset=existing_activities)
    
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
        student_profile = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You must complete your student profile first.')
        return redirect('create_profile')
    
    # Get the activity log (ensuring it belongs to the current student)
    try:
        activity_log = Log.objects.get(
            nanoid=log_nanoid,
            internship__student=student_profile
        )
    except Log.DoesNotExist:
        messages.error(request, 'Activity log not found or access denied.')
        return redirect('student_activities')
    
    # Get all activities for this log
    activities = Entry.objects.filter(
        log=activity_log
    ).order_by('date')
    
    # Calculate total entries (no hours in current model)
    total_entries = activities.count()
    
    context = {
        'activity_log': activity_log,
        'activities': activities,
        'total_entries': total_entries,
        'student_profile': student_profile,
        'current_internship': activity_log.internship,
    }
    return render(request, 'app/view_activity_log.html', context)

@login_required
def add_entry_form(request):
    """HTMX endpoint to add a new entry form"""
    if not request.user.groups.filter(name='student').exists():
        return HttpResponse("Unauthorized", status=403)
    
    # Get the form index from the request
    form_index = request.GET.get('form_index', 0)
    try:
        form_index = int(form_index)
    except (ValueError, TypeError):
        form_index = 0
    
    # Create a single entry form with the specified index
    form = EntryForm(prefix=f'form-{form_index}')
    
    context = {
        'form': form,
        'form_index': form_index,
        'show_delete': form_index > 0,  # Show delete for all forms except the first one
    }
    return render(request, 'app/partials/entry_form.html', context)

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
            profile = request.user.mentor
            if not profile.can_register_organization:
                messages.error(request, 'You do not have permission to register new organizations.')
                return redirect_to_role_dashboard(request.user)
        except Mentor.DoesNotExist:
            messages.error(request, 'Please complete your mentor profile first.')
            return redirect('create_profile')
    else:  # teacher
        try:
            profile = request.user.teacher
            # Teachers can always register organizations (no restriction)
        except Teacher.DoesNotExist:
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
            profile = request.user.mentor
            requests = OrganizationRegistrationRequest.objects.filter(requested_by_mentor=profile)
        except Mentor.DoesNotExist:
            messages.error(request, 'Mentor profile not found.')
            return redirect('create_profile')
    elif user_type == 'teacher':
        try:
            profile = request.user.teacher
            requests = OrganizationRegistrationRequest.objects.filter(requested_by_teacher=profile)
        except Teacher.DoesNotExist:
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
        official_profile = request.user.official
        if not official_profile.can_approve_organizations:
            messages.error(request, 'You do not have permission to approve organizations.')
            return redirect_to_role_dashboard(request.user)
    except Official.DoesNotExist:
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
                
                # Associate teacher with institute
                if org_request.requested_by_teacher:
                    org_request.requested_by_teacher.institute = institute
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get all positions with related data
    positions = Position.objects.filter(mentor=mentor_profile).annotate(
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get all applications for mentor's positions
    applications = Application.objects.filter(
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
            filtered_position = Position.objects.get(
                nanoid=position_filter, 
                mentor=mentor_profile
            )
            applications = applications.filter(position=filtered_position)
            position_filter_name = filtered_position.title
        except Position.DoesNotExist:
            # If position doesn't exist or doesn't belong to mentor, ignore filter
            position_filter = ''
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get mentor's positions for filter dropdown
    mentor_positions = Position.objects.filter(mentor=mentor_profile)
    
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    try:
        application = Application.objects.select_related(
            'student__user', 'position__company'
        ).get(
            nanoid=application_nanoid,
            position__mentor=mentor_profile
        )
    except Application.DoesNotExist:
        messages.error(request, 'Application not found or access denied.')
        return redirect('mentor_applications')
    
    # Check if application can be accepted
    if application.status not in ['pending', 'under_review']:
        status_display = dict(Application.STATUS_CHOICES).get(application.status or 'unknown', 'Unknown')
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
            
            # Use InternshipForm for structured creation
            internship_data = {
                'start_date': start_date,
                'end_date': end_date,
                'status': 'active',
                'final_grade': ''  # Will be filled later
            }
            
            form = InternshipForm(internship_data)
            if form.is_valid():
                internship = form.save(commit=False)
                internship.application = application
                internship.student = application.student
                internship.mentor = mentor
                internship.teacher = None  # Teacher assignment can be done separately
                internship.save()
            else:
                # Fallback to manual creation if form validation fails
                internship = Internship.objects.create(
                    application=application,
                    student=application.student,
                    mentor=mentor,
                    teacher=None,
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    try:
        application = Application.objects.select_related(
            'student__user', 'position__company'
        ).get(
            nanoid=application_nanoid,
            position__mentor=mentor_profile
        )
    except Application.DoesNotExist:
        messages.error(request, 'Application not found or access denied.')
        return redirect('mentor_applications')
    
    # Check if application can be rejected
    if application.status not in ['pending', 'under_review']:
        status_display = dict(Application.STATUS_CHOICES).get(application.status or 'unknown', 'Unknown')
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    try:
        application = Application.objects.select_related(
            'student__user', 'position__company'
        ).get(
            nanoid=application_nanoid,
            position__mentor=mentor_profile
        )
    except Application.DoesNotExist:
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get the student profile and verify mentor has access
    try:
        student_profile = Student.objects.select_related(
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
            
    except Student.DoesNotExist:
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
    """Create a mentor assessment for an intern"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get the internship
    internship = get_object_or_404(Internship, nanoid=internship_nanoid, mentor=mentor_profile)
    
    # Check if assessment already exists (OneToOne relationship)
    existing_assessment = Assessment.objects.filter(internship=internship).first()
    
    if request.method == 'POST':
        if existing_assessment:
            form = AssessmentForm(request.POST, instance=existing_assessment)
            action = 'updated'
        else:
            form = AssessmentForm(request.POST)
            action = 'created'
            
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.internship = internship
            assessment.mentor = mentor_profile
            assessment.save()
            
            messages.success(request, f'Assessment {action} successfully.')
            return redirect('mentor_progress_reports', internship_nanoid=internship_nanoid)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssessmentForm(instance=existing_assessment) if existing_assessment else AssessmentForm()
    
    context = {
        'form': form,
        'mentor_profile': mentor_profile,
        'internship': internship,
        'existing_assessment': existing_assessment,
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get the internship
    internship = get_object_or_404(Internship, nanoid=internship_nanoid, mentor=mentor_profile)
    
    # Get all submissions for this internship
    # Student reports (monthly progress reports)
    student_reports = Report.objects.filter(
        internship=internship
    ).order_by('-report_month')
    
    # Mentor assessment (one per internship)
    mentor_assessment = Assessment.objects.filter(internship=internship).first()
    
    # Teacher evaluations
    teacher_evaluations = Evaluation.objects.filter(
        internship=internship
    ).order_by('-evaluation_date')
    
    context = {
        'mentor_profile': mentor_profile,
        'internship': internship,
        'student_reports': student_reports,
        'mentor_assessment': mentor_assessment,
        'teacher_evaluations': teacher_evaluations,
        'total_submissions': student_reports.count() + (1 if mentor_assessment else 0) + teacher_evaluations.count(),
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
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.warning(request, 'Please complete your mentor profile first.')
        return redirect('create_profile')
    
    # Get the progress report
    report = get_object_or_404(
        Report, 
        nanoid=report_nanoid, 
        report_type='mentor',
        internship__mentor=mentor_profile
    )
    
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            report_date_str = report.report_date.strftime("%B %d, %Y") if report.report_date else "Unknown Date"
            messages.success(request, f'Progress report for {report_date_str} updated successfully.')
            return redirect('mentor_progress_reports', internship_nanoid=report.internship.nanoid)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReportForm(instance=report)
    
    context = {
        'form': form,
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

@login_required
def submit_student_report(request, internship_nanoid):
    """Student submits monthly internship report"""
    user_type = get_user_type(request.user)
    if user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('home')
    
    try:
        student_profile = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Please create your student profile first.')
        return redirect('create_profile')
    
    # Get the internship
    try:
        internship = Internship.objects.get(
            nanoid=internship_nanoid, 
            student=student_profile,
            status='active'
        )
    except Internship.DoesNotExist:
        messages.error(request, 'Active internship not found.')
        return redirect('student_internship')
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            # Check if report for this month already exists
            report_month = form.cleaned_data['report_month']
            existing_report = Report.objects.filter(
                internship=internship,
                report_month=report_month
            ).first()
            
            if existing_report:
                messages.error(request, f'Report for {report_month.strftime("%B %Y")} already exists.')
            else:
                # Create new report
                report = form.save(commit=False)
                report.internship = internship
                report.student = student_profile
                report.save()
                
                messages.success(request, f'Report for {report_month.strftime("%B %Y")} submitted successfully!')
                return redirect('student_internship')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ReportForm()
    
    # Get existing reports for context
    existing_reports = Report.objects.filter(
        internship=internship
    ).order_by('-report_month')
    
    context = {
        'form': form,
        'internship': internship,
        'student_profile': student_profile,
        'existing_reports': existing_reports,
    }
    return render(request, 'app/submit_student_report.html', context)

@login_required
def create_supervisor_evaluation(request, internship_nanoid):
    """Mentor creates evaluation for student intern"""
    user_type = get_user_type(request.user)
    if user_type != 'mentor':
        messages.error(request, 'Access denied. Mentor account required.')
        return redirect('home')
    
    try:
        mentor_profile = request.user.mentor
    except Mentor.DoesNotExist:
        messages.error(request, 'Please create your mentor profile first.')
        return redirect('create_profile')
    
    # Get the internship
    try:
        internship = Internship.objects.get(
            nanoid=internship_nanoid, 
            mentor=mentor_profile
        )
    except Internship.DoesNotExist:
        messages.error(request, 'Internship not found or access denied.')
        return redirect('mentor_dashboard')
    
    # Check if evaluation already exists
    existing_evaluation = InternshipSupervisorEvaluation.objects.filter(
        internship=internship
    ).first()
    
    if existing_evaluation:
        messages.info(request, 'Evaluation already exists for this internship.')
        return redirect('mentor_dashboard')
    
    if request.method == 'POST':
        form = InternshipSupervisorEvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.internship = internship
            evaluation.supervisor = mentor_profile
            evaluation.save()
            
            messages.success(request, 'Supervisor evaluation submitted successfully!')
            return redirect('mentor_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InternshipSupervisorEvaluationForm()
    
    context = {
        'form': form,
        'internship': internship,
        'mentor_profile': mentor_profile,
        'student_name': internship.student.user.get_full_name() if internship.student and internship.student.user else 'Student',
    }
    return render(request, 'app/create_supervisor_evaluation.html', context)

@login_required
def edit_internship_status(request, internship_nanoid):
    """Edit internship status and details (mentor or teacher access)"""
    user_type = get_user_type(request.user)
    if user_type not in ['mentor', 'teacher']:
        messages.error(request, 'Access denied. Mentor or Teacher account required.')
        return redirect('home')
    
    try:
        if user_type == 'mentor':
            profile = request.user.mentor
            internship = Internship.objects.get(nanoid=internship_nanoid, mentor=profile)
        else:  # teacher
            profile = request.user.teacher
            internship = Internship.objects.get(nanoid=internship_nanoid, teacher=profile)
    except (Mentor.DoesNotExist, Teacher.DoesNotExist, Internship.DoesNotExist):
        messages.error(request, 'Internship not found or access denied.')
        return redirect_to_role_dashboard(request.user)
    
    if request.method == 'POST':
        form = InternshipForm(request.POST, instance=internship)
        if form.is_valid():
            form.save()
            messages.success(request, 'Internship details updated successfully!')
            return redirect_to_role_dashboard(request.user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InternshipForm(instance=internship)
    
    context = {
        'form': form,
        'internship': internship,
        'profile': profile,
        'user_type': user_type,
    }
    return render(request, 'app/edit_internship_status.html', context)

def dashboard_redirect(request):
    """Generic dashboard redirect"""
    if request.user.is_authenticated:
        return redirect_to_role_dashboard(request.user)
    else:
        return redirect('account_login')
