from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Mentor management URLs
    path('mentors/positions/', views.mentor_positions, name='mentor_positions'),
    path('mentors/applications/', views.mentor_applications, name='mentor_applications'),
    path('mentors/applications/<str:application_nanoid>/accept/', views.accept_application, name='accept_application'),
    path('mentors/applications/<str:application_nanoid>/reject/', views.reject_application, name='reject_application'),
    path('mentors/applications/<str:application_nanoid>/detail/', views.application_detail, name='application_detail'),
    path('mentors/interns/', views.mentor_interns, name='mentor_interns'),
    
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    
    # Unified profile management URLs
    path('profile/', views.profile, name='profile'),
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Company editing URL (for mentors who registered the company)
    path('companies/edit/', views.edit_company, name='edit_company'),
    
    # Institute editing URL (for teachers who registered the institute)
    path('institutes/edit/', views.edit_institute, name='edit_institute'),
    
    # Teacher management URLs
    path('teachers/students/', views.teacher_students, name='teacher_students'),
    
    # Official management URLs
    path('officials/manage-companies/', views.manage_companies, name='manage_companies'),
    path('officials/manage-institutes/', views.manage_institutes, name='manage_institutes'),
    path('officials/company/<str:company_nanoid>/', views.company_detail_official, name='company_detail_official'),
    path('officials/institute/<str:institute_nanoid>/', views.institute_detail_official, name='institute_detail_official'),
    
    # Student application management
    path('applications/', views.student_applications, name='student_applications'),
    path('applications/<str:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    
    # Student weekly activity log management
    path('activities/', views.student_weekly_activities, name='student_weekly_activities'),
    path('activities/create/', views.create_weekly_activity_log, name='create_weekly_activity_log'),
    path('activities/<str:log_nanoid>/edit/', views.edit_weekly_activity_log, name='edit_weekly_activity_log'),
    path('activities/<str:log_nanoid>/', views.view_weekly_activity_log, name='view_weekly_activity_log'),
    
    # Position management URLs (specific patterns first)
    path('positions/', views.browse_positions, name='browse_positions'),
    path('positions/create/', views.create_position, name='create_position'),
    path('positions/<str:position_nanoid>/apply/', views.apply_position, name='apply_position'),
    path('positions/<str:position_nanoid>/edit/', views.edit_position, name='edit_position'),
    path('positions/<str:position_nanoid>/', views.position_detail, name='position_detail'),
    
    # Progress report management URLs
    path('internships/<str:internship_nanoid>/progress-reports/', views.mentor_progress_reports, name='mentor_progress_reports'),
    path('internships/<str:internship_nanoid>/progress-reports/create/', views.create_progress_report, name='create_progress_report'),
    path('progress-reports/<str:report_nanoid>/edit/', views.edit_progress_report, name='edit_progress_report'),
    
    # Demo and Documentation URLs
    path('docs/', views.documentation_index, name='documentation_index'),
    path('docs/<str:user_type>/<str:topic>/', views.documentation_guide, name='documentation_guide'),
]
