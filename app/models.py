from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
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
    phone = models.CharField(max_length=15, null=True, blank=True, help_text="Contact phone number")
    # Email domain verification
    email_domain = models.CharField(max_length=100, null=True, blank=True, help_text="Official email domain (e.g., university.edu.pk)")
    domain_verified = models.BooleanField(default=False, help_text="Whether the email domain has been verified")
    # Registration and approval
    registered_by = models.ForeignKey('Teacher', on_delete=models.PROTECT, null=True, blank=True, related_name='registered_institutes')
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
    approved_by = models.ForeignKey('Official', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_institutes')
    approved_at = models.DateTimeField(null=True, blank=True)
    registration_notes = models.TextField(null=True, blank=True, help_text="Notes from government official during review")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Supporting documents for approval
    registration_certificate = models.FileField(
        upload_to='org_documents/',
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'png'])],
        help_text="Upload educational registration certificate"
    )
    authorization_letter = models.FileField(
        upload_to='org_documents/', 
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'png'])],
        help_text="Authorization letter proving you can represent this institute"
    )
    
    # Location and demographics
    district = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        choices=[
            ('Abbottabad', 'Abbottabad'),
            ('Bajaur', 'Bajaur'),
            ('Bannu', 'Bannu'),
            ('Battagram', 'Battagram'),
            ('Bunner', 'Bunner'),
            ('Charsadda', 'Charsadda'),
            ('D.I.Khan', 'D.I.Khan'),
            ('Dir Lower', 'Dir Lower'),
            ('Dir Upper', 'Dir Upper'),
            ('Hangu', 'Hangu'),
            ('Haripur', 'Haripur'),
            ('Karak', 'Karak'),
            ('Khyber', 'Khyber'),
            ('Kohat', 'Kohat'),
            ('Kohistan', 'Kohistan'),
            ('Kurram', 'Kurram'),
            ('Lakki Marwat', 'Lakki Marwat'),
            ('Lower Chitral', 'Lower Chitral'),
            ('Malakand', 'Malakand'),
            ('Mansehra', 'Mansehra'),
            ('Mardan', 'Mardan'),
            ('Mohmand', 'Mohmand'),
            ('North Waziristan', 'North Waziristan'),
            ('Nowshera', 'Nowshera'),
            ('Orakzai', 'Orakzai'),
            ('Peshawar', 'Peshawar'),
            ('Shangla', 'Shangla'),
            ('South Waziristan', 'South Waziristan'),
            ('Swabi', 'Swabi'),
            ('Swat', 'Swat'),
            ('Tank', 'Tank'),
            ('Upper Chitral', 'Upper Chitral'),
        ],
        help_text="District where the institute is located"
    )
    
    # Gender ratio tracking
    male_students_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of male students enrolled"
    )
    female_students_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of female students enrolled"
    )
    
    # Education level offerings
    degree_programs = models.BooleanField(
        default=False,
        help_text="Offers degree-level programs"
    )
    postgraduate_programs = models.BooleanField(
        default=False,
        help_text="Offers postgraduate programs"
    )
    management_programs = models.BooleanField(
        default=False,
        help_text="Offers management programs"
    )
    
    # Additional demographic and program details
    primary_education_level = models.CharField(
        max_length=20,
        choices=[
            ('Degree', 'Degree'),
            ('PostGraduate', 'Post Graduate'),
            ('Management', 'Management'),
        ],
        null=True,
        blank=True,
        help_text="Primary level of education offered"
    )
    
    def is_email_from_institute(self, email):
        """Check if email belongs to this institute's domain"""
        if not self.email_domain or not email:
            return False
        email_domain = email.split('@')[-1].lower()
        return email_domain == self.email_domain.lower()
    
    def is_approved(self):
        """Check if institute is approved for operations"""
        return self.registration_status == 'approved'
    
    def get_total_students(self):
        """Get total number of students"""
        return self.male_students_count + self.female_students_count
    
    def get_gender_ratio(self):
        """Get gender ratio as percentage"""
        total = self.get_total_students()
        if total == 0:
            return {'male': 0, 'female': 0}
        
        male_percentage = (self.male_students_count / total) * 100
        female_percentage = (self.female_students_count / total) * 100
        
        return {
            'male': round(male_percentage, 1),
            'female': round(female_percentage, 1)
        }
    
    def get_offered_programs(self):
        """Get list of offered education programs"""
        programs = []
        if self.degree_programs:
            programs.append('Degree')
        if self.postgraduate_programs:
            programs.append('Post Graduate')
        if self.management_programs:
            programs.append('Management')
        return programs
    
    def get_district_display_name(self):
        """Get display name for district"""
        return self.district if self.district else "Not specified"
    
    def __str__(self):
        status_indicator = "✓" if self.is_approved() else "⚠"
        district_info = f" ({self.district})" if self.district else ""
        return f"{status_indicator} {self.name or 'Unnamed Institute'}{district_info}"

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
    registered_by = models.ForeignKey('Mentor', on_delete=models.PROTECT, null=True, blank=True, related_name='registered_companies')
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
    approved_by = models.ForeignKey('Official', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_companies')
    approved_at = models.DateTimeField(null=True, blank=True)
    registration_notes = models.TextField(null=True, blank=True, help_text="Notes from government official during review")
    is_verified = models.BooleanField(default=False)  # Keep for backward compatibility
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Supporting documents for approval
    registration_certificate = models.FileField(
        upload_to='org_documents/',
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'png'])],
        help_text="Upload business registration certificate"
    )
    authorization_letter = models.FileField(
        upload_to='org_documents/', 
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'png'])],
        help_text="Authorization letter proving you can represent this company"
    )
    
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

class Student(models.Model):
    """Student profile with academic information"""
    SEMESTER_CHOICES = (
        ('4', '4th Semester'),
        ('5', '5th Semester'),
        ('6', '6th Semester'),
        ('7', '7th Semester'),
        ('8', '8th Semester'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    institute = models.ForeignKey(Institute, on_delete=models.SET_NULL, null=True, blank=True)
    student_id = models.CharField(max_length=50, null=True, blank=True)
    semester_of_study = models.CharField(max_length=1, choices=SEMESTER_CHOICES, null=True, blank=True)
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
    # Contact information
    phone = models.CharField(max_length=15, null=True, blank=True, help_text="Contact phone number")
    
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
            self.semester_of_study,
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
            self.phone,
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

class Mentor(models.Model):
    """Mentor profile for company representatives"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    specialization = models.CharField(max_length=200, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    # Contact information
    phone = models.CharField(max_length=15, null=True, blank=True, help_text="Contact phone number")
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

class Teacher(models.Model):
    """Teacher profile for institute staff"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    institute = models.ForeignKey(Institute, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=50, null=True, blank=True)  # Professor, Associate Professor, etc.
    employee_id = models.CharField(max_length=50, null=True, blank=True)
    # Contact information
    phone = models.CharField(max_length=15, null=True, blank=True, help_text="Contact phone number")
    
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
    
    def can_edit_institute(self):
        """Check if teacher can edit institute (if they registered it)"""
        if not self.institute:
            return False
        return self.institute.registered_by == self
    
    def __str__(self):
        institute_name = self.institute.name if self.institute else "No Institute"
        return f"{self.title or 'Teacher'} {self.user.get_full_name()} - {institute_name}"

class Official(models.Model):
    """Government official profile"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='official')
    department = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    employee_id = models.CharField(max_length=50, null=True, blank=True)
    # Contact information
    phone = models.CharField(max_length=15, null=True, blank=True, help_text="Contact phone number")
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

class Position(models.Model):
    """Internship positions offered by companies"""
    DURATION_CHOICES = (
        ('2', '2 Months'),
        ('3', '3 Months'),
        ('4', '4 Months'),
        ('6', '6 Months'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_position_id, unique=True, db_index=True, editable=False)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, blank=True)
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
        applications: 'RelatedManager[Application]'
    
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

class Application(models.Model):
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
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, related_name='applications', null=True, blank=True)
    cover_letter = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        # Allow reapplication after rejection/withdrawal by only preventing duplicate active applications
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'position'],
                condition=models.Q(status__in=['pending', 'under_review', 'interview_scheduled', 'approved']),
                name='unique_active_application'
            )
        ]
    
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
    application = models.OneToOneField(Application, on_delete=models.SET_NULL, null=True, blank=True)
    interviewer = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, blank=True)
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
    application = models.OneToOneField(Application, on_delete=models.SET_NULL, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
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
    
    @property
    def position(self):
        """Get the internship position from application or return None"""
        if self.application and self.application.position:
            return self.application.position
        return None
    
    def get_progress_percentage(self):
        """Calculate progress percentage based on time elapsed"""
        if not self.start_date or not self.end_date:
            return 0
        
        from datetime import date
        today = date.today()
        
        if today < self.start_date:
            return 0
        elif today > self.end_date:
            return 100
        else:
            total_days = (self.end_date - self.start_date).days
            elapsed_days = (today - self.start_date).days
            return min(100, max(0, (elapsed_days / total_days) * 100))

class Evaluation(models.Model):
    """End of internship evaluation submitted by teachers"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    internship = models.ForeignKey(Internship, on_delete=models.SET_NULL, related_name='teacher_evaluations', null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    evaluation_date = models.DateField(default=timezone.now, help_text="Date of the evaluation")
    
    # Teacher evaluation fields
    discussion_notes = models.TextField(
        help_text="Notes from discussions with student and mentor"
    )
    academic_alignment = models.TextField(
        help_text="How well the internship aligns with academic objectives"
    )
    recommendations = models.TextField(
        help_text="Recommendations for future internships or improvements"
    )
    overall_rating = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Overall evaluation rating (1-5)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['internship', 'teacher', 'evaluation_date']
    
    def __str__(self):
        internship_str = str(self.internship) if self.internship else "No Internship"
        date_str = self.evaluation_date.strftime('%b %d, %Y') if self.evaluation_date else 'No Date'
        teacher_str = str(self.teacher) if self.teacher else "No Teacher"
        return f"Teacher Evaluation - {date_str} by {teacher_str} for {internship_str}"

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
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

class Report(models.Model):
    """End of internship report submitted by students"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    internship = models.ForeignKey(Internship, on_delete=models.SET_NULL, related_name='student_reports', null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    report_month = models.DateField(help_text="Month and year for this report")
    
    # Report sections with descriptions and scores
    tasks_performed = models.TextField(
        help_text="Major duties designated and assignments completed by the student"
    )
    tasks_performed_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score for tasks performed (0-10)"
    )
    
    learning_experience = models.TextField(
        help_text="Skills and knowledge gained or refined through the internship"
    )
    learning_experience_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score for learning experience (0-10)"
    )
    
    challenges = models.TextField(
        help_text="Major challenges faced and how they were tackled"
    )
    challenges_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score for handling challenges (0-10)"
    )
    
    additional_comments = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Note: unique_together with nullable fields may allow multiple null combinations
        unique_together = ['internship', 'report_month']
        ordering = ['-report_month']
        
    def get_total_score(self):
        """Calculate total score out of 30"""
        return self.tasks_performed_score + self.learning_experience_score + self.challenges_score
    
    def __str__(self):
        if self.internship and self.internship.student:
            student_name = self.internship.student.user.get_full_name()
        else:
            student_name = "No Student"
        return f"Report for {student_name} - {self.report_month.strftime('%B %Y')}"

class Log(models.Model):
    """Weekly activity log for students during their internship"""
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    internship = models.ForeignKey(Internship, on_delete=models.SET_NULL, related_name='activity_logs', null=True, blank=True)
    week_starting = models.DateField(help_text="Monday of the week you're reporting")
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-week_starting']
        unique_together = ['internship', 'week_starting']
        verbose_name = "Weekly Activity Log"
        verbose_name_plural = "Weekly Activity Logs"

    def __str__(self):
        if self.internship and self.internship.student:
            student_name = self.internship.student.user.get_full_name()
        else:
            student_name = "No Student"
        return f"Activity Log: {student_name} - Week of {self.week_starting.strftime('%Y-%m-%d')}"

class Entry(models.Model):
    """Simple daily activity entry for students"""
    log = models.ForeignKey(Log, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField(help_text="Date of the activity")
    description = models.TextField(help_text="What did you do on this day?")
    
    class Meta:
        ordering = ['date']
        unique_together = ['log', 'date']  # One entry per day per log
        verbose_name = "Daily Activity Entry"
        verbose_name_plural = "Daily Activity Entries"

    def __str__(self):
        return f"{self.date}: {self.description[:50]}..."

class Assessment(models.Model):
    """End of internship assessment filled by mentors"""
    RATING_CHOICES = (
        (1, 'Does not meet expectations'),
        (2, 'Inconsistently meets expectations'),
        (3, 'Consistently meets expectations'),
        (4, 'Above expectations'),
    )
    
    EXPERIENCE_RATING = (
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    )
    
    nanoid = models.CharField(max_length=12, default=generate_nanoid, unique=True, db_index=True, editable=False)
    internship = models.OneToOneField(Internship, on_delete=models.SET_NULL, related_name='supervisor_evaluation', null=True, blank=True)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Performance Indicators (1-4 scale)
    technical_skills = models.IntegerField(
        choices=RATING_CHOICES,
        help_text="Technical competency and ability to learn/apply new skills"
    )
    work_quality = models.IntegerField(
        choices=RATING_CHOICES,
        help_text="Quality and accuracy of work, attention to detail"
    )
    problem_solving = models.IntegerField(
        choices=RATING_CHOICES,
        help_text="Ability to analyze problems and find solutions"
    )
    teamwork = models.IntegerField(
        choices=RATING_CHOICES,
        help_text="Collaboration, communication, and interpersonal skills"
    )
    professionalism = models.IntegerField(
        choices=RATING_CHOICES,
        help_text="Punctuality, reliability, and professional conduct"
    )
    
    # Qualitative Feedback
    performance_benefits = models.TextField(
        help_text="Describe the ways in which the intern's performance benefited your organization"
    )
    observed_development = models.TextField(
        help_text="What development have you observed in the student's skills, knowledge, personal and/or professional performance?"
    )
    intern_strengths = models.TextField(
        help_text="What do you consider to be the intern's strengths?"
    )
    areas_for_improvement = models.TextField(
        help_text="In what areas does the intern need to improve?"
    )
    
    # Overall Experience and Recommendations
    intern_rating = models.CharField(
        max_length=10,
        choices=EXPERIENCE_RATING,
        help_text="Overall, how do you rate your experience with this intern?"
    )
    program_rating = models.CharField(
        max_length=10,
        choices=EXPERIENCE_RATING,
        help_text="Overall, how do you rate your experience with this internship program?"
    )
    program_improvement_suggestions = models.TextField(
        help_text="What are your suggestions for improving the internship program?"
    )
    would_recommend = models.BooleanField(
        help_text="Based on your experience, would you supervise other interns or recommend the internship program to others?"
    )
    additional_comments = models.TextField(
        null=True, blank=True,
        help_text="Do you have any other comments that will help the institute and our students?"
    )
    
    class Meta:
        verbose_name = "Internship Supervisor Evaluation"
        verbose_name_plural = "Internship Supervisor Evaluations"
    
    def get_average_rating(self):
        """Calculate average score across all performance indicators"""
        scores = [
            self.technical_skills,
            self.work_quality,
            self.problem_solving,
            self.teamwork,
            self.professionalism
        ]
        return sum(scores) / len(scores)
    
    def __str__(self):
        if self.internship and self.internship.student:
            student_name = self.internship.student.user.get_full_name()
        else:
            student_name = "No Student"
        return f"Supervisor Evaluation for {student_name} - {self.submitted_at.strftime('%Y-%m-%d')}"

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
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='notifications', null=True, blank=True)
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
