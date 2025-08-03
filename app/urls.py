from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Dashboard URLs (role-specific management)
    path('dashboard/positions/', views.mentor_positions, name='mentor_positions'),
    path('dashboard/applications/', views.mentor_applications, name='mentor_applications'),
    path('dashboard/applications/<str:application_nanoid>/', views.application_detail, name='application_detail'),
    path('dashboard/applications/<str:application_nanoid>/accept/', views.accept_application, name='accept_application'),
    path('dashboard/applications/<str:application_nanoid>/reject/', views.reject_application, name='reject_application'),
    path('dashboard/interns/', views.mentor_interns, name='mentor_interns'),
    path('students/<str:student_nanoid>/', views.student_profile_detail, name='student_profile_detail'),
    
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    
    # Unified profile management URLs
    path('profile/', views.profile, name='profile'),
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Company editing URL
    path('companies/edit/', views.edit_company, name='edit_company'),
    
    # Institute editing URL
    path('institutes/edit/', views.edit_institute, name='edit_institute'),
    
    # Student management URLs
    path('students/', views.teacher_students, name='teacher_students'),
    
    # Management URLs
    path('companies/', views.manage_companies, name='manage_companies'),
    path('companies/<str:company_nanoid>/', views.company_detail_official, name='company_detail_official'),

    path('institutes/', views.manage_institutes, name='manage_institutes'),
    path('institutes/<str:institute_nanoid>/', views.institute_detail_official, name='institute_detail_official'),
    
    # Application management (renamed from student applications to avoid conflict)
    path('my-applications/', views.student_applications, name='student_applications'),
    path('my-applications/<str:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    
    # Activity log management
    path('activities/', views.student_weekly_activities, name='student_weekly_activities'),
    path('activities/create/', views.create_weekly_activity_log, name='create_weekly_activity_log'),
    path('activities/<str:log_nanoid>/edit/', views.edit_weekly_activity_log, name='edit_weekly_activity_log'),
    path('activities/<str:log_nanoid>/', views.view_weekly_activity_log, name='view_weekly_activity_log'),
    
    # Public position browsing URLs (specific patterns first)
    path('positions/', views.browse_positions, name='browse_positions'),
    path('positions/create/', views.create_position, name='create_position'),
    path('positions/<str:position_nanoid>/', views.position_detail, name='position_detail'),
    path('positions/<str:position_nanoid>/apply/', views.apply_position, name='apply_position'),
    path('positions/<str:position_nanoid>/edit/', views.edit_position, name='edit_position'),
    
    # Progress report management URLs
    path('internships/<str:internship_nanoid>/progress-reports/', views.mentor_progress_reports, name='mentor_progress_reports'),
    path('internships/<str:internship_nanoid>/progress-reports/create/', views.create_progress_report, name='create_progress_report'),
    path('progress-reports/<str:report_nanoid>/edit/', views.edit_progress_report, name='edit_progress_report'),
    
    # Demo and Documentation URLs
    path('docs/', views.documentation_index, name='documentation_index'),
    path('docs/<str:user_type>/<str:topic>/', views.documentation_guide, name='documentation_guide'),
]
