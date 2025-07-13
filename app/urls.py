from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('mentor/dashboard/', views.mentor_dashboard, name='mentor_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('official/dashboard/', views.official_dashboard, name='official_dashboard'),
    path('browse/', views.browse_positions, name='browse_positions'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    
    # Profile creation URLs
    path('student/create-profile/', views.create_student_profile, name='create_student_profile'),
    path('mentor/create-profile/', views.create_mentor_profile, name='create_mentor_profile'),
    path('teacher/create-profile/', views.create_teacher_profile, name='create_teacher_profile'),
    
    # Profile editing URLs
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('student/edit-profile/', views.edit_student_profile, name='edit_student_profile'),
    path('mentor/edit-profile/', views.edit_mentor_profile, name='edit_mentor_profile'),
    path('teacher/edit-profile/', views.edit_teacher_profile, name='edit_teacher_profile'),
    path('official/edit-profile/', views.edit_official_profile, name='edit_official_profile'),
    
    # Student application management
    path('applications/', views.student_applications, name='student_applications'),
    
    # Position management URLs (specific patterns first)
    path('position/create/', views.create_position, name='create_position'),
    path('position/<str:position_nanoid>/apply/', views.apply_position, name='apply_position'),
    path('position/<str:position_nanoid>/edit/', views.edit_position, name='edit_position'),
    path('position/<str:position_nanoid>/', views.position_detail, name='position_detail'),
]
