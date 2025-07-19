from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Institute, Company, StudentProfile, MentorProfile, 
    TeacherProfile, OfficialProfile, InternshipPosition, 
    InternshipApplication, Interview, Internship, ProgressReport,
    Payment, Notification, OrganizationRegistrationRequest
)

@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ('name', 'email_domain', 'registration_status', 'domain_verification_status', 'registered_by', 'approved_by', 'created_at')
    list_filter = ('registration_status', 'domain_verified', 'created_at')
    search_fields = ('name', 'contact_email', 'email_domain', 'registered_by__user__username')
    actions = ['approve_institutes', 'reject_institutes', 'verify_domain', 'unverify_domain']
    readonly_fields = ('nanoid', 'created_at', 'approved_at')
    
    def domain_verification_status(self, obj):
        if obj.domain_verified:
            return format_html('<span style="color: green;">✓ Domain Verified</span>')
        elif obj.email_domain:
            return format_html('<span style="color: orange;">⚠ Domain Set, Not Verified</span>')
        else:
            return format_html('<span style="color: gray;">No Domain Set</span>')
    domain_verification_status.short_description = 'Domain Status'
    
    def approve_institutes(self, request, queryset):
        updated = queryset.update(registration_status='approved')
        self.message_user(request, f"{updated} institutes approved successfully.")
    approve_institutes.short_description = "✓ Approve selected institutes"
    
    def reject_institutes(self, request, queryset):
        updated = queryset.update(registration_status='rejected')
        self.message_user(request, f"{updated} institutes rejected successfully.")
    reject_institutes.short_description = "✗ Reject selected institutes"
    
    def verify_domain(self, request, queryset):
        updated = queryset.filter(email_domain__isnull=False).exclude(email_domain='').update(domain_verified=True)
        self.message_user(request, f"{updated} institute domains verified successfully.")
    verify_domain.short_description = "✓ Verify domain for selected institutes"
    
    def unverify_domain(self, request, queryset):
        updated = queryset.update(domain_verified=False)
        self.message_user(request, f"{updated} institute domains unverified successfully.")
    unverify_domain.short_description = "✗ Unverify domain for selected institutes"

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'email_domain', 'registration_status', 'domain_verification_status', 'registered_by', 'approved_by', 'created_at')
    list_filter = ('industry', 'registration_status', 'domain_verified', 'created_at')
    search_fields = ('name', 'industry', 'contact_email', 'email_domain', 'registered_by__user__username')
    actions = ['approve_companies', 'reject_companies', 'verify_domain', 'unverify_domain']
    readonly_fields = ('nanoid', 'created_at', 'approved_at')
    
    def domain_verification_status(self, obj):
        if obj.domain_verified:
            return format_html('<span style="color: green;">✓ Domain Verified</span>')
        elif obj.email_domain:
            return format_html('<span style="color: orange;">⚠ Domain Set, Not Verified</span>')
        else:
            return format_html('<span style="color: gray;">No Domain Set</span>')
    domain_verification_status.short_description = 'Domain Status'
    
    def approve_companies(self, request, queryset):
        updated = queryset.update(registration_status='approved')
        self.message_user(request, f"{updated} companies approved successfully.")
    approve_companies.short_description = "✓ Approve selected companies"
    
    def reject_companies(self, request, queryset):
        updated = queryset.update(registration_status='rejected')
        self.message_user(request, f"{updated} companies rejected successfully.")
    reject_companies.short_description = "✗ Reject selected companies"
    
    def verify_domain(self, request, queryset):
        updated = queryset.filter(email_domain__isnull=False).exclude(email_domain='').update(domain_verified=True)
        self.message_user(request, f"{updated} company domains verified successfully.")
    verify_domain.short_description = "✓ Verify domain for selected companies"
    
    def unverify_domain(self, request, queryset):
        updated = queryset.update(domain_verified=False)
        self.message_user(request, f"{updated} company domains unverified successfully.")
    unverify_domain.short_description = "✗ Unverify domain for selected companies"

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'institute', 'year_of_study', 'major', 'gpa', 'availability_status')
    list_filter = ('institute', 'year_of_study', 'is_available_for_internship', 'major')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'student_id', 'major')
    actions = ['mark_available', 'mark_unavailable', 'send_welcome_notification']
    
    def availability_status(self, obj):
        if obj.is_available_for_internship:
            return format_html('<span style="color: green;">✓ Available</span>')
        else:
            return format_html('<span style="color: orange;">● Unavailable</span>')
    availability_status.short_description = 'Availability'
    
    def mark_available(self, request, queryset):
        updated = queryset.update(is_available_for_internship=True)
        self.message_user(request, f"{updated} students marked as available for internships.")
    mark_available.short_description = "✓ Mark as available for internships"
    
    def mark_unavailable(self, request, queryset):
        updated = queryset.update(is_available_for_internship=False)
        self.message_user(request, f"{updated} students marked as unavailable for internships.")
    mark_unavailable.short_description = "● Mark as unavailable for internships"
    
    def send_welcome_notification(self, request, queryset):
        from .models import Notification
        count = 0
        for student in queryset:
            Notification.objects.create(
                recipient=student.user,
                notification_type='general',
                title='Welcome to Tarbiyat!',
                message=f'Welcome {student.user.get_full_name()}! Your student profile has been reviewed. You can now browse and apply for internship positions.'
            )
            count += 1
        self.message_user(request, f"Welcome notifications sent to {count} students.")
    send_welcome_notification.short_description = "📧 Send welcome notifications"

@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'position', 'department', 'verification_status', 'experience_years')
    list_filter = ('company', 'is_verified', 'experience_years')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'position', 'department')
    actions = ['verify_mentors', 'unverify_mentors', 'verify_mentor_and_company']
    
    def verification_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        else:
            return format_html('<span style="color: red;">✗ Not Verified</span>')
    verification_status.short_description = 'Verification Status'
    
    def verify_mentors(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} mentor profiles verified successfully.")
    verify_mentors.short_description = "✓ Verify selected mentors"
    
    def unverify_mentors(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"{updated} mentor profiles unverified successfully.")
    unverify_mentors.short_description = "✗ Unverify selected mentors"
    
    def verify_mentor_and_company(self, request, queryset):
        mentor_count = 0
        company_count = 0
        companies_verified = set()
        
        for mentor in queryset:
            # Verify mentor
            if not mentor.is_verified:
                mentor.is_verified = True
                mentor.save()
                mentor_count += 1
            
            # Verify associated company if not already verified
            if not mentor.company.is_verified and mentor.company.id not in companies_verified:
                mentor.company.is_verified = True
                mentor.company.save()
                companies_verified.add(mentor.company.id)
                company_count += 1
        
        self.message_user(request, 
            f"Verified {mentor_count} mentors and {company_count} companies successfully.")
    verify_mentor_and_company.short_description = "✓ Verify mentors and their companies"

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institute', 'department', 'title', 'employee_id')
    list_filter = ('institute', 'department')
    search_fields = ('user__username', 'user__email', 'employee_id')

@admin.register(OfficialProfile)
class OfficialProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'position', 'employee_id')
    list_filter = ('department',)
    search_fields = ('user__username', 'user__email', 'employee_id')

@admin.register(InternshipPosition)
class InternshipPositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'mentor', 'duration', 'start_date', 'end_date', 'max_students', 'available_spots', 'position_status')
    list_filter = ('company', 'duration', 'is_active', 'start_date', 'mentor__is_verified')
    search_fields = ('title', 'company__name', 'mentor__user__username', 'mentor__user__first_name', 'mentor__user__last_name')
    date_hierarchy = 'start_date'
    actions = ['activate_positions', 'deactivate_positions', 'extend_deadline']
    
    def position_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactive</span>')
    position_status.short_description = 'Status'
    
    def activate_positions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} positions activated successfully.")
    activate_positions.short_description = "✓ Activate positions"
    
    def deactivate_positions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} positions deactivated successfully.")
    deactivate_positions.short_description = "✗ Deactivate positions"
    
    def extend_deadline(self, request, queryset):
        from datetime import timedelta
        count = 0
        for position in queryset:
            if position.is_active:
                position.end_date = position.end_date + timedelta(days=30)
                position.save()
                count += 1
        self.message_user(request, f"Extended deadline by 30 days for {count} active positions.")
    extend_deadline.short_description = "📅 Extend deadline by 30 days"

@admin.register(InternshipApplication)
class InternshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'position', 'application_status', 'applied_at', 'reviewed_at')
    list_filter = ('status', 'applied_at', 'position__company', 'position__mentor')
    search_fields = ('student__user__username', 'student__user__email', 'student__user__first_name', 'student__user__last_name', 'position__title')
    date_hierarchy = 'applied_at'
    actions = ['approve_applications', 'reject_applications', 'mark_under_review', 'schedule_interviews']
    
    def application_status(self, obj):
        status_colors = {
            'pending': '#ffa500',  # orange
            'under_review': '#007bff',  # blue
            'interview_scheduled': '#6f42c1',  # purple
            'approved': '#28a745',  # green
            'rejected': '#dc3545',  # red
            'withdrawn': '#6c757d',  # gray
        }
        color = status_colors.get(obj.status, '#000000')
        return format_html('<span style="color: {};">● {}</span>', color, obj.get_status_display())
    application_status.short_description = 'Status'
    
    def approve_applications(self, request, queryset):
        updated = queryset.update(status='approved')
        # Create notifications
        from .models import Notification
        for app in queryset:
            Notification.objects.create(
                recipient=app.student.user,
                notification_type='application_status',
                title='Application Approved!',
                message=f'Congratulations! Your application for {app.position.title} at {app.position.company.name} has been approved.'
            )
        self.message_user(request, f"{updated} applications approved and notifications sent.")
    approve_applications.short_description = "✓ Approve applications"
    
    def reject_applications(self, request, queryset):
        updated = queryset.update(status='rejected')
        # Create notifications
        from .models import Notification
        for app in queryset:
            Notification.objects.create(
                recipient=app.student.user,
                notification_type='application_status',
                title='Application Status Update',
                message=f'Thank you for your interest in {app.position.title} at {app.position.company.name}. Unfortunately, your application was not selected at this time.'
            )
        self.message_user(request, f"{updated} applications rejected and notifications sent.")
    reject_applications.short_description = "✗ Reject applications"
    
    def mark_under_review(self, request, queryset):
        updated = queryset.update(status='under_review')
        self.message_user(request, f"{updated} applications marked as under review.")
    mark_under_review.short_description = "👁 Mark as under review"
    
    def schedule_interviews(self, request, queryset):
        updated = queryset.update(status='interview_scheduled')
        self.message_user(request, f"{updated} applications marked for interview scheduling.")
    schedule_interviews.short_description = "📅 Schedule interviews"

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'interviewer', 'scheduled_date', 'status')
    list_filter = ('status', 'scheduled_date', 'interviewer__company')
    search_fields = ('application__student__user__username', 'interviewer__user__username')
    date_hierarchy = 'scheduled_date'

@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ('student', 'mentor', 'start_date', 'end_date', 'status', 'final_grade', 'certificate_issued')
    list_filter = ('status', 'certificate_issued', 'start_date', 'mentor__company')
    search_fields = ('student__user__username', 'mentor__user__username', 'mentor__company__name')
    date_hierarchy = 'start_date'

@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = ('internship', 'report_type', 'reporter', 'week_number', 'created_at')
    list_filter = ('report_type', 'week_number', 'created_at')
    search_fields = ('internship__student__user__username', 'reporter__username')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_type', 'amount', 'status', 'transaction_id', 'payment_date')
    list_filter = ('payment_type', 'status', 'payment_date')
    search_fields = ('user__username', 'transaction_id')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'read_status', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'recipient__first_name', 'recipient__last_name', 'title')
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread', 'send_general_notification']
    
    def read_status(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        else:
            return format_html('<span style="color: blue;">● Unread</span>')
    read_status.short_description = 'Read Status'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notifications marked as read.")
    mark_as_read.short_description = "✓ Mark as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notifications marked as unread.")
    mark_as_unread.short_description = "● Mark as unread"
