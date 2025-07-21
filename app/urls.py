from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('students/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('mentors/dashboard/', views.mentor_dashboard, name='mentor_dashboard'),
    path('mentors/positions/', views.mentor_positions, name='mentor_positions'),
    path('mentors/applications/', views.mentor_applications, name='mentor_applications'),
    path('mentors/interns/', views.mentor_interns, name='mentor_interns'),
    path('teachers/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('officials/dashboard/', views.official_dashboard, name='official_dashboard'),
    
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    
    # Profile creation URLs
    path('students/create-profile/', views.create_student_profile, name='create_student_profile'),
    path('mentors/create-profile/', views.create_mentor_profile, name='create_mentor_profile'),
    path('teachers/create-profile/', views.create_teacher_profile, name='create_teacher_profile'),
    
    # Profile editing URLs
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('students/edit-profile/', views.edit_student_profile, name='edit_student_profile'),
    path('mentors/edit-profile/', views.edit_mentor_profile, name='edit_mentor_profile'),
    path('teachers/edit-profile/', views.edit_teacher_profile, name='edit_teacher_profile'),
    path('officials/edit-profile/', views.edit_official_profile, name='edit_official_profile'),
    
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
    
    # Documentation URLs
    path('docs/', views.documentation_index, name='documentation_index'),
    path('docs/<str:user_type>/<str:topic>/', views.documentation_guide, name='documentation_guide'),
]
