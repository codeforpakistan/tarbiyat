from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from decimal import Decimal
from typing import TYPE_CHECKING
from nanoid import generate

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


def generate_nanoid():
    """Generate a standard nanoid"""
    return generate(size=12)

def generate_position_id():
    """Generate a unique nanoid for position IDs"""
    return generate(size=12)

def generate_institute_id():
    """Generate a unique nanoid for institute IDs"""
    return generate(size=10)

def generate_company_id():
    """Generate a unique nanoid for company IDs"""
    return generate(size=10)

def generate_application_id():
    """Generate a unique nanoid for application IDs"""
    return generate(size=14)

class Institute(models.Model):
    """Institute model for universities and colleges"""

    class Meta:
        verbose_name_plural = "Institutes"

    nanoid = models.CharField(max_length=10, default=generate_institute_id, unique=True, db_index=True, editable=False)
    name = models.CharField(max_length=200, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    # Email domain verification
    email_domain = models.CharField(max_length=100, null=True, blank=True, help_text="Official email domain (e.g., university.edu.pk)")
    domain_verified = models.BooleanField(default=False, help_text="Whether the email domain has been verified")
    # Registration and approval
    registered_by = models.ForeignKey('TeacherProfile', on_delete=models.PROTECT, null=True, blank=True, related_name='registered_institutes')
    registration_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('suspended', 'Suspended'),
        ],
        default='pending'
    )
    approved_by = models.ForeignKey('OfficialProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_institutes')
    approved_at = models.DateTimeField(null=True, blank=True)
    registration_notes = models.TextField(null=True, blank=True, help_text="Notes from government official during review")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_email_from_institute(self, email):
        """Check if email belongs to this institute's domain"""
        if not self.email_domain or not email:
            return False
        email_domain = email.split('@')[-1].lower()
        return email_domain == self.email_domain.lower()
    
    def is_approved(self):
        """Check if institute is approved for operations"""
        return self.registration_status == 'approved'
    
    def __str__(self):
        status_indicator = "✓" if self.is_approved() else "⚠"
        return f"{status_indicator} {self.name or 'Unnamed Institute'}"

class Company(models.Model):
    """Company model for organizations offering internships"""
    nanoid = models.CharField(max_length=10, default=generate_company_id, unique=True, db_index=True, editable=False)
    name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    # Email domain verification
    email_domain = models.CharField(max_length=100, null=True, blank=True, help_text="Official email domain (e.g., company.com)")
    domain_verified = models.BooleanField(default=False, help_text="Whether the email domain has been verified")
    # Registration and approval
    registered_by = models.ForeignKey('MentorProfile', on_delete=models.PROTECT, null=True, blank=True, related_name='registered_companies')
    registration_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('suspended', 'Suspended'),
        ],
        default='pending'
    )
    approved_by = models.ForeignKey('OfficialProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_companies')
    approved_at = models.DateTimeField(null=True, blank=True)
    registration_notes = models.TextField(null=True, blank=True, help_text="Notes from government official during review")
    is_verified = models.BooleanField(default=False)  # Keep for backward compatibility
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Companies"
    
    def is_email_from_company(self, email):
        """Check if email belongs to this company's domain"""
        if not self.email_domain or not email:
            return False
        email_domain = email.split('@')[-1].lower()
        return email_domain == self.email_domain.lower()
    
    def is_approved(self):
        """Check if company is approved for operations"""
        return self.registration_status == 'approved'
    
    def __str__(self):
        status_indicator = "✓" if self.is_approved() else "⚠"
        return f"{status_indicator} {self.name or 'Unnamed Company'}"

class StudentProfile(models.Model):
    """Student profile with academic information"""
    YEAR_CHOICES = (
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, null=True, blank=True)
    student_id = models.CharField(max_length=50, null=True, blank=True)
    year_of_study = models.CharField(max_length=1, choices=YEAR_CHOICES, null=True, blank=True)
    major = models.CharField(max_length=100, null=True, blank=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(4)], null=True, blank=True)
    skills = models.TextField(help_text="List your technical and soft skills", null=True, blank=True)
    resume = models.FileField(
        upload_to='resumes/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        help_text="Upload your resume in PDF, DOC, or DOCX format"
    )
    portfolio_url = models.URLField(null=True, blank=True)
    expected_graduation = models.DateField(null=True, blank=True)
    is_available_for_internship = models.BooleanField(default=True)
    
    def get_profile_completion(self):
        """Calculate profile completion percentage"""
        # Required fields for a complete profile
        required_fields = [
            # User fields (always considered required)
            self.user.first_name,
            self.user.last_name,
            self.user.email,
            # Profile fields
            self.institute,
            self.year_of_study,
            self.major,
            self.gpa,
            self.skills,
            self.expected_graduation,
        ]
        
        # Optional but recommended fields
        optional_fields = [
            self.student_id,
            self.portfolio_url,
            self.resume,
        ]
        
        # Count filled required fields (weight: 80%)
        filled_required = sum(1 for field in required_fields if field)
        required_score = (filled_required / len(required_fields)) * 80
        
        # Count filled optional fields (weight: 20%)
        filled_optional = sum(1 for field in optional_fields if field)
        optional_score = (filled_optional / len(optional_fields)) * 20
        
        total_completion = required_score + optional_score
        return round(total_completion)
    
    def get_completion_status(self):
        """Get human-readable completion status"""
        completion = self.get_profile_completion()
        if completion >= 90:
            return "Your profile is complete! You're ready for internship opportunities."
        elif completion >= 70:
            return f"Your profile is {completion}% complete. Consider adding a resume and portfolio to increase your chances."
        else:
            return f"Your profile is {completion}% complete. Please fill in the missing information to improve your visibility to employers."
    
    def get_resume_filename(self):
        """Get just the filename from the resume path"""
        if self.resume:
            return self.resume.name.split('/')[-1]
        return None
    
    def can_join_institute(self, institute):
        """Check if student can join this institute based on email domain"""
        if not institute or not institute.domain_verified:
            return True  # Allow if institute doesn't have domain verification
        return institute.is_email_from_institute(self.user.email)
    
    def validate_institute_membership(self):
        """Validate that student's email matches institute domain"""
        if self.institute and self.institute.domain_verified:
            if not self.institute.is_email_from_institute(self.user.email):
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Your email domain must match {self.institute.name}'s official domain ({self.institute.email_domain}) to join this institute."
                )
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id or 'No ID'}"

class MentorProfile(models.Model):
    """Mentor profile for company representatives"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    specialization = models.CharField(max_length=200, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    # Administrative contact status
    is_admin_contact = models.BooleanField(default=False, help_text="Whether this mentor is an administrative contact for their company")
    can_register_organization = models.BooleanField(default=True, help_text="Whether this mentor can register a new company")
    
    def can_join_company(self, company):
        """Check if mentor can join this company based on email domain"""
        if not company or not company.domain_verified:
            return True  # Allow if company doesn't have domain verification
        return company.is_email_from_company(self.user.email)
    
    def validate_company_membership(self):
        """Validate that mentor's email matches company domain"""
        if self.company and self.company.domain_verified:
            if not self.company.is_email_from_company(self.user.email):
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Your email domain must match {self.company.name}'s official domain ({self.company.email_domain}) to join this company."
                )
    
    def can_manage_company(self):
        """Check if mentor can manage company settings"""
        return self.is_admin_contact and self.company and self.company.is_approved()
    
    def can_edit_company(self):
        """Check if mentor can edit company information (if they registered it)"""
        return (
            self.company and 
            self.company.registered_by == self and
            self.company.registration_status in ['pending', 'approved']
        )
    
    def __str__(self):
        company_name = self.company.name if self.company else "No Company"
        admin_indicator = " (Admin)" if self.is_admin_contact else ""
        return f"{self.user.get_full_name()} - {company_name}{admin_indicator}"

class TeacherProfile(models.Model):
    """Teacher profile for institute staff"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=50, null=True, blank=True)  # Professor, Associate Professor, etc.
    employee_id = models.CharField(max_length=50, null=True, blank=True)
    # Administrative contact status
    is_admin_contact = models.BooleanField(default=False, help_text="Whether this teacher is an administrative contact for their institute")
    can_register_organization = models.BooleanField(default=True, help_text="Whether this teacher can register a new institute")
    
    def can_join_institute(self, institute):
        """Check if teacher can join this institute based on email domain"""
        if not institute or not institute.domain_verified:
            return True  # Allow if institute doesn't have domain verification
        return institute.is_email_from_institute(self.user.email)
    
    def validate_institute_membership(self):
        """Validate that teacher's email matches institute domain"""
        if self.institute and self.institute.domain_verified:
            if not self.institute.is_email_from_institute(self.user.email):
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Your email domain must match {self.institute.name}'s official domain ({self.institute.email_domain}) to join this institute."
                )
    
    def can_manage_institute(self):
        """Check if teacher can manage institute settings"""
        return self.is_admin_contact and self.institute and self.institute.is_approved()
    
    def can_edit_institute(self):
        """Check if teacher can edit institute (if they registered it)"""
        if not self.institute:
            return False
        return self.institute.registered_by == self
    
    def __str__(self):
        institute_name = self.institute.name if self.institute else "No Institute"
        admin_indicator = " (Admin)" if self.is_admin_contact else ""
        return f"{self.title or 'Teacher'} {self.user.get_full_name()} - {institute_name}{admin_indicator}"

class OfficialProfile(models.Model):
    """Government official profile"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='official_profile')
    department = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    employee_id = models.CharField(max_length=50, null=True, blank=True)
    # Approval permissions
    can_approve_organizations = models.BooleanField(default=True, help_text="Whether this official can approve organization registrations")
    approval_authority_level = models.CharField(
        max_length=20,
        choices=[
            ('local', 'Local Authority'),
            ('provincial', 'Provincial Authority'),
            ('federal', 'Federal Authority'),
        ],
        default='local'
    )
    
    def get_pending_approvals_count(self):
        """Get count of organizations pending approval"""
        pending_companies = Company.objects.filter(registration_status='pending').count()
        pending_institutes = Institute.objects.filter(registration_status='pending').count()
        return pending_companies + pending_institutes
    
    def can_approve_organization(self, organization):
        """Check if official can approve this organization"""
        return self.can_approve_organizations
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department or 'No Department'}"

class OrganizationRegistrationRequest(models.Model):
    """Organization registration requests from mentors/teachers"""
    ORGANIZATION_TYPES = (
        ('company', 'Company'),
        ('institute', 'Institute'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    organization_type = models.CharField(max_length=10, choices=ORGANIZATION_TYPES)
    
    # Organization details
    organization_name = models.CharField(max_length=200)
    organization_description = models.TextField()
    industry = models.CharField(max_length=100, null=True, blank=True)  # For companies
    address = models.TextField()
    website = models.URLField(null=True, blank=True)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=15, null=True, blank=True)
    email_domain = models.CharField(max_length=100, help_text="Official email domain to verify")
    
    # Supporting documents
    registration_certificate = models.FileField(
        upload_to='org_documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'png'])],
        help_text="Upload business/educational registration certificate"
    )
    authorization_letter = models.FileField(
        upload_to='org_documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'png'])],
        help_text="Authorization letter proving you can represent this organization"
    )
    
    # Request details
    requested_by_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_requests')
    requested_by_mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, null=True, blank=True)
    requested_by_teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, null=True, blank=True)
    
    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(OfficialProfile, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(null=True, blank=True)
    
    # Created organization (set when approved)
    approved_company = models.OneToOneField(Company, on_delete=models.CASCADE, null=True, blank=True)
    approved_institute = models.OneToOneField(Institute, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        org_type = "Company" if self.organization_type == 'company' else "Institute"
        status_display = self.status.title()
        return f"{self.organization_name} ({org_type}) - {status_display}"

class InternshipPosition(models.Model):
    """Internship positions offered by companies"""
    DURATION_CHOICES = (
        ('2', '2 Months'),
        ('3', '3 Months'),
        ('4', '4 Months'),
        ('6', '6 Months'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_position_id, unique=True, db_index=True, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)
    skills_required = models.TextField(null=True, blank=True)
    duration = models.CharField(max_length=1, choices=DURATION_CHOICES, default='2', null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Stipend amount in PKR")
    max_students = models.IntegerField(default=1, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    if TYPE_CHECKING:
        applications: 'RelatedManager[InternshipApplication]'
    
    def __str__(self):
        company_name = self.company.name if self.company else "No Company"
        return f"{self.title or 'Untitled Position'} at {company_name}"
    
    @property
    def available_spots(self):
        # Django creates the 'applications' reverse relation automatically
        approved_applications = self.applications.filter(status='approved').count()  # type: ignore
        max_students = self.max_students or 1
        return max_students - approved_applications

    @property
    def approved_applications_count(self):
        return self.applications.filter(status='approved').count()  # type: ignore
    
    @property
    def pending_applications_count(self):
        return self.applications.filter(status='pending').count()  # type: ignore
    
    @property
    def total_applications_count(self):
        return self.applications.count()  # type: ignore

class InternshipApplication(models.Model):
    """Student applications for internship positions"""
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    nanoid = models.CharField(max_length=14, default=generate_application_id, unique=True, db_index=True, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, null=True, blank=True)
    position = models.ForeignKey(InternshipPosition, on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    cover_letter = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'position']
    
    def __str__(self):
        student_name = self.student.user.get_full_name() if self.student else "No Student"
        position_title = self.position.title if self.position else "No Position"
        return f"{student_name} -> {position_title}"

class Interview(models.Model):
    """Interview scheduling and management"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    application = models.OneToOneField(InternshipApplication, on_delete=models.CASCADE, null=True, blank=True)
    interviewer = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, null=True, blank=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)  # or online link
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled', null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        student_name = "No Student"
        if self.application and self.application.student:
            student_name = self.application.student.user.get_full_name()
        return f"Interview: {student_name} - {self.scheduled_date or 'Not Scheduled'}"

class Internship(models.Model):
    """Active internship instances"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
        ('on_hold', 'On Hold'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    application = models.OneToOneField(InternshipApplication, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, null=True, blank=True)
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active', null=True, blank=True)
    final_grade = models.CharField(max_length=2, null=True, blank=True)  # A, B, C, D, F
    certificate_issued = models.BooleanField(default=False)
    certificate_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        student_name = self.student.user.get_full_name() if self.student else "No Student"
        company_name = "No Company"
        if self.mentor and self.mentor.company:
            company_name = self.mentor.company.name
        return f"{student_name} at {company_name}"

class ProgressReport(models.Model):
    """Progress reports during internship"""
    REPORT_TYPE_CHOICES = (
        ('student', 'Student Report'),
        ('mentor', 'Mentor Report'),
        ('teacher', 'Teacher Report'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='progress_reports', null=True, blank=True)
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES, null=True, blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    week_number = models.IntegerField(null=True, blank=True)
    
    # Student-specific fields
    tasks_completed = models.TextField(null=True, blank=True)
    learning_outcomes = models.TextField(null=True, blank=True)
    challenges_faced = models.TextField(null=True, blank=True)
    satisfaction_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Mentor-specific fields
    student_performance = models.TextField(null=True, blank=True)
    skills_demonstrated = models.TextField(null=True, blank=True)
    areas_for_improvement = models.TextField(null=True, blank=True)
    attendance_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Teacher-specific fields
    discussion_notes = models.TextField(null=True, blank=True)
    academic_alignment = models.TextField(null=True, blank=True)
    recommendations = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['internship', 'report_type', 'week_number']
    
    def __str__(self):
        # Django automatically creates get_<field>_display() methods for choice fields
        report_type_display = self.get_report_type_display() if self.report_type else "Unknown Type"  # type: ignore
        internship_str = str(self.internship) if self.internship else "No Internship"
        return f"Week {self.week_number or 'N/A'} - {report_type_display} for {internship_str}"

class Payment(models.Model):
    """Payment tracking for platform fees"""
    PAYMENT_TYPE_CHOICES = (
        ('student_fee', 'Student Registration Fee'),
        ('mentor_fee', 'Mentor/Company Fee'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPE_CHOICES, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in PKR", null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', null=True, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        # Django automatically creates get_<field>_display() methods for choice fields
        username = self.user.username if self.user else "No User"
        payment_type_display = self.get_payment_type_display() if self.payment_type else "Unknown Type"  # type: ignore
        amount = self.amount or 0
        return f"{username} - {payment_type_display} - PKR {amount}"

class Notification(models.Model):
    """System notifications for users"""
    NOTIFICATION_TYPES = (
        ('application_status', 'Application Status Update'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('progress_reminder', 'Progress Report Reminder'),
        ('internship_completed', 'Internship Completed'),
        ('general', 'General Notification'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        title = self.title or "No Title"
        username = self.recipient.username if self.recipient else "No Recipient"
        return f"{title} - {username}"
