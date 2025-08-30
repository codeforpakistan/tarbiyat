from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # Public pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('harassment/', views.anti_harassment_policy, name='anti_harassment_policy'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # Mentor URLs
    path('mentor/', views.mentor_dashboard_view, name='mentor_dashboard'),
    path('mentor/positions/', views.mentor_positions, name='mentor_positions'),
    path('mentor/applications/', views.mentor_applications, name='mentor_applications'),
    path('mentor/applications/<str:application_nanoid>/', views.application_detail, name='application_detail'),
    path('mentor/applications/<str:application_nanoid>/accept/', views.accept_application, name='accept_application'),
    path('mentor/applications/<str:application_nanoid>/reject/', views.reject_application, name='reject_application'),
    path('mentor/interns/', views.mentor_interns, name='mentor_interns'),
    
    # Student URLs
    path('student/', views.student_dashboard_view, name='student_dashboard'),
    path('student/applications/', views.student_applications, name='student_applications'),
    path('student/applications/<str:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('student/internship/', views.student_internship, name='student_internship'),
    path('student/activities/', views.student_weekly_activities, name='student_weekly_activities'),
    path('student/activities/create/', views.create_weekly_activity_log, name='create_weekly_activity_log'),
    path('student/activities/<str:log_nanoid>/edit/', views.edit_weekly_activity_log, name='edit_weekly_activity_log'),
    path('student/activities/<str:log_nanoid>/', views.view_weekly_activity_log, name='view_weekly_activity_log'),
    
    # Teacher URLs
    path('teacher/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/internships/', views.teacher_internships, name='teacher_internships'),
    path('teacher/internship/<str:internship_nanoid>/', views.teacher_internship_detail, name='teacher_internship_detail'),
    path('teacher/reports/', views.teacher_reports, name='teacher_reports'),
    path('teacher/reports/<str:report_nanoid>/', views.teacher_report_detail, name='teacher_report_detail'),
    
    # Official URLs
    path('official/', views.official_dashboard_view, name='official_dashboard'),
    path('official/companies/', views.manage_companies, name='manage_companies'),
    path('official/companies/mass-verify/', views.mass_verify_companies, name='mass_verify_companies'),
    path('official/companies/<str:company_nanoid>/', views.company_detail_official, name='company_detail_official'),
    path('official/institutes/', views.manage_institutes, name='manage_institutes'),
    path('official/institutes/mass-verify/', views.mass_verify_institutes, name='mass_verify_institutes'),
    path('official/institutes/<str:institute_nanoid>/', views.institute_detail_official, name='institute_detail_official'),
    path('official/reports/', views.official_reports, name='official_reports'),
    
    # Shared URLs
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
