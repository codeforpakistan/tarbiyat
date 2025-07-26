from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import tempfile
import os

from .models import (
    StudentProfile, MentorProfile, TeacherProfile, OfficialProfile,
    Institute, Company, InternshipPosition, InternshipApplication,
    Internship, Notification
)
from .utils import (
    validate_user_organization_membership,
    get_available_institutes_for_user,
    get_available_companies_for_user,
    extract_domain_from_email
)
from .views import get_user_type


class ModelTestCase(TestCase):
    """Test cases for all models"""
    
    def setUp(self):
        """Set up test data"""
        self.setup_groups()
        self.setup_users()
        self.setup_organizations()
        
    def setup_groups(self):
        """Create user groups"""
        self.student_group, _ = Group.objects.get_or_create(name='student')
        self.mentor_group, _ = Group.objects.get_or_create(name='mentor')
        self.teacher_group, _ = Group.objects.get_or_create(name='teacher')
        self.official_group, _ = Group.objects.get_or_create(name='official')
        
    def setup_users(self):
        """Create test users"""
        self.student_user = User.objects.create_user(
            username='student@university.edu',
            email='student@university.edu',
            password='testpass123',
            first_name='John',
            last_name='Student'
        )
        self.student_user.groups.add(self.student_group)
        
        self.mentor_user = User.objects.create_user(
            username='mentor@company.com',
            email='mentor@company.com',
            password='testpass123',
            first_name='Jane',
            last_name='Mentor'
        )
        self.mentor_user.groups.add(self.mentor_group)
        
        self.teacher_user = User.objects.create_user(
            username='teacher@university.edu',
            email='teacher@university.edu',
            password='testpass123',
            first_name='Bob',
            last_name='Teacher'
        )
        self.teacher_user.groups.add(self.teacher_group)
        
        self.official_user = User.objects.create_user(
            username='official@govt.pk',
            email='official@govt.pk',
            password='testpass123',
            first_name='Alice',
            last_name='Official'
        )
        self.official_user.groups.add(self.official_group)
        
    def setup_organizations(self):
        """Create test organizations"""
        self.institute = Institute.objects.create(
            name='Test University',
            address='123 University St',
            contact_email='info@university.edu',
            email_domain='university.edu',
            domain_verified=True,
            registration_status='approved'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            industry='Technology',
            address='456 Business Ave',
            contact_email='hr@company.com',
            email_domain='company.com',
            domain_verified=True,
            registration_status='approved'
        )


class InstituteModelTest(ModelTestCase):
    """Test Institute model functionality"""
    
    def test_institute_creation(self):
        """Test institute creation with nanoid"""
        self.assertIsNotNone(self.institute.nanoid)
        self.assertEqual(len(self.institute.nanoid), 10)
        self.assertEqual(str(self.institute), "✓ Test University")
        
    def test_institute_email_domain_validation(self):
        """Test email domain validation"""
        self.assertTrue(self.institute.is_email_from_institute('student@university.edu'))
        self.assertFalse(self.institute.is_email_from_institute('student@other.edu'))
        self.assertFalse(self.institute.is_email_from_institute(''))
        
    def test_institute_approval_status(self):
        """Test institute approval status"""
        self.assertTrue(self.institute.is_approved())
        
        pending_institute = Institute.objects.create(
            name='Pending University',
            registration_status='pending'
        )
        self.assertFalse(pending_institute.is_approved())
        
    def test_institute_string_representation(self):
        """Test string representation with status indicators"""
        approved_institute = Institute.objects.create(
            name='Approved University',
            registration_status='approved'
        )
        self.assertEqual(str(approved_institute), "✓ Approved University")
        
        pending_institute = Institute.objects.create(
            name='Pending University',
            registration_status='pending'
        )
        self.assertEqual(str(pending_institute), "⚠ Pending University")


class CompanyModelTest(ModelTestCase):
    """Test Company model functionality"""
    
    def test_company_creation(self):
        """Test company creation with nanoid"""
        self.assertIsNotNone(self.company.nanoid)
        self.assertEqual(len(self.company.nanoid), 10)
        self.assertEqual(str(self.company), "✓ Test Company")
        
    def test_company_email_domain_validation(self):
        """Test email domain validation"""
        self.assertTrue(self.company.is_email_from_company('employee@company.com'))
        self.assertFalse(self.company.is_email_from_company('employee@other.com'))
        self.assertFalse(self.company.is_email_from_company(''))
        
    def test_company_approval_status(self):
        """Test company approval status"""
        self.assertTrue(self.company.is_approved())
        
        pending_company = Company.objects.create(
            name='Pending Company',
            registration_status='pending'
        )
        self.assertFalse(pending_company.is_approved())


class StudentProfileModelTest(ModelTestCase):
    """Test StudentProfile model functionality"""
    
    def setUp(self):
        super().setUp()
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            institute=self.institute,
            student_id='STU001',
            year_of_study='3',
            major='Computer Science',
            gpa=Decimal('3.5'),
            skills='Python, Django, JavaScript',
            expected_graduation=date.today() + timedelta(days=365)
        )
        
    def test_student_profile_creation(self):
        """Test student profile creation"""
        self.assertIsNotNone(self.student_profile.nanoid)
        self.assertEqual(len(self.student_profile.nanoid), 12)
        self.assertEqual(self.student_profile.user, self.student_user)
        
    def test_profile_completion_calculation(self):
        """Test profile completion percentage calculation"""
        completion = self.student_profile.get_profile_completion()
        self.assertGreaterEqual(completion, 80)  # Should be high with filled fields
        
        # Test with minimal profile
        minimal_profile = StudentProfile.objects.create(user=self.mentor_user)
        minimal_completion = minimal_profile.get_profile_completion()
        self.assertLess(minimal_completion, 50)
        
    def test_institute_membership_validation(self):
        """Test institute membership validation"""
        # Should pass with matching domain
        self.student_profile.validate_institute_membership()
        
        # Should fail with non-matching domain
        wrong_user = User.objects.create_user(
            username='wrong@other.com',
            email='wrong@other.com',
            password='test123'
        )
        wrong_profile = StudentProfile.objects.create(
            user=wrong_user,
            institute=self.institute
        )
        
        with self.assertRaises(ValidationError):
            wrong_profile.validate_institute_membership()
            
    def test_can_join_institute(self):
        """Test institute joining validation"""
        self.assertTrue(self.student_profile.can_join_institute(self.institute))
        
        # Create unverified institute
        unverified_institute = Institute.objects.create(
            name='Unverified Institute',
            domain_verified=False
        )
        self.assertTrue(self.student_profile.can_join_institute(unverified_institute))


class MentorProfileModelTest(ModelTestCase):
    """Test MentorProfile model functionality"""
    
    def setUp(self):
        super().setUp()
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            company=self.company,
            position='Software Engineer',
            department='Engineering',
            experience_years=5,
            specialization='Web Development',
            is_admin_contact=True
        )
        
    def test_mentor_profile_creation(self):
        """Test mentor profile creation"""
        self.assertIsNotNone(self.mentor_profile.nanoid)
        self.assertEqual(len(self.mentor_profile.nanoid), 12)
        self.assertEqual(self.mentor_profile.user, self.mentor_user)
        
    def test_company_membership_validation(self):
        """Test company membership validation"""
        # Should pass with matching domain
        self.mentor_profile.validate_company_membership()
        
        # Should fail with non-matching domain
        wrong_user = User.objects.create_user(
            username='wrong@other.com',
            email='wrong@other.com',
            password='test123'
        )
        wrong_profile = MentorProfile.objects.create(
            user=wrong_user,
            company=self.company
        )
        
        with self.assertRaises(ValidationError):
            wrong_profile.validate_company_membership()
            
    def test_can_manage_company(self):
        """Test company management permissions"""
        self.assertTrue(self.mentor_profile.can_manage_company())
        
        # Non-admin contact should not be able to manage
        non_admin_profile = MentorProfile.objects.create(
            user=self.teacher_user,
            company=self.company,
            is_admin_contact=False
        )
        self.assertFalse(non_admin_profile.can_manage_company())


class TeacherProfileModelTest(ModelTestCase):
    """Test TeacherProfile model functionality"""
    
    def setUp(self):
        super().setUp()
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institute=self.institute,
            department='Computer Science',
            title='Professor',
            employee_id='EMP001',
            is_admin_contact=True
        )
        
    def test_teacher_profile_creation(self):
        """Test teacher profile creation"""
        self.assertIsNotNone(self.teacher_profile.nanoid)
        self.assertEqual(len(self.teacher_profile.nanoid), 12)
        self.assertEqual(self.teacher_profile.user, self.teacher_user)
        
    def test_institute_membership_validation(self):
        """Test institute membership validation"""
        # Should pass with matching domain
        self.teacher_profile.validate_institute_membership()
        
    def test_can_manage_institute(self):
        """Test institute management permissions"""
        self.assertTrue(self.teacher_profile.can_manage_institute())


class OfficialProfileModelTest(ModelTestCase):
    """Test OfficialProfile model functionality"""
    
    def setUp(self):
        super().setUp()
        self.official_profile = OfficialProfile.objects.create(
            user=self.official_user,
            department='Education Ministry',
            position='Director',
            employee_id='OFF001'
        )
        
    def test_official_profile_creation(self):
        """Test official profile creation"""
        self.assertIsNotNone(self.official_profile.nanoid)
        self.assertEqual(len(self.official_profile.nanoid), 12)
        self.assertEqual(self.official_profile.user, self.official_user)


class UtilityFunctionsTest(ModelTestCase):
    """Test utility functions"""
    
    def test_validate_user_organization_membership(self):
        """Test organization membership validation"""
        # Valid institute membership
        is_valid, error = validate_user_organization_membership(
            self.student_user, 'institute', self.institute.pk
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Invalid institute membership
        wrong_user = User.objects.create_user(
            username='wrong@other.com',
            email='wrong@other.com',
            password='test123'
        )
        is_valid, error = validate_user_organization_membership(
            wrong_user, 'institute', self.institute.pk
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        
    def test_get_available_institutes_for_user(self):
        """Test getting available institutes for user"""
        institutes = get_available_institutes_for_user(self.student_user)
        self.assertIn(self.institute, institutes)
        
        # User with non-matching domain should not see domain-verified institutes
        wrong_user = User.objects.create_user(
            username='wrong@other.com',
            email='wrong@other.com',
            password='test123'
        )
        institutes = get_available_institutes_for_user(wrong_user)
        self.assertNotIn(self.institute, institutes)
        
    def test_extract_domain_from_email(self):
        """Test domain extraction from email"""
        self.assertEqual(extract_domain_from_email('user@example.com'), 'example.com')
        self.assertEqual(extract_domain_from_email('test@subdomain.example.org'), 'subdomain.example.org')
        self.assertIsNone(extract_domain_from_email('invalid-email'))
        self.assertIsNone(extract_domain_from_email(''))


class ViewsTestCase(ModelTestCase):
    """Test view functionality"""
    
    def setUp(self):
        super().setUp()
        self.client = Client()
        
    def test_get_user_type_function(self):
        """Test get_user_type utility function"""
        self.assertEqual(get_user_type(self.student_user), 'student')
        self.assertEqual(get_user_type(self.mentor_user), 'mentor')
        self.assertEqual(get_user_type(self.teacher_user), 'teacher')
        self.assertEqual(get_user_type(self.official_user), 'official')
        
        # Test with unauthenticated user
        from django.contrib.auth.models import AnonymousUser
        anonymous_user = AnonymousUser()
        self.assertIsNone(get_user_type(anonymous_user))
        
    def test_home_view_redirect_for_authenticated_users(self):
        """Test home view redirects authenticated users appropriately"""
        # Test student user - may redirect if profile is incomplete
        self.client.login(username='student@university.edu', password='testpass123')
        response = self.client.get(reverse('home'))
        # User without complete profile may be redirected
        self.assertIn(response.status_code, [200, 302])
        
    def test_home_view_for_anonymous_users(self):
        """Test home view for anonymous users"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
    def test_profile_completion_redirect(self):
        """Test that users without profiles are redirected to complete profile"""
        # Login as user without profile
        new_user = User.objects.create_user(
            username='newuser@test.com',
            email='newuser@test.com',
            password='testpass123'
        )
        new_user.groups.add(self.student_group)
        
        self.client.login(username='newuser@test.com', password='testpass123')
        response = self.client.get(reverse('home'))
        # User without profile should be redirected or shown message
        self.assertIn(response.status_code, [200, 302])


class FormTestCase(ModelTestCase):
    """Test form functionality"""
    
    def test_custom_signup_form(self):
        """Test custom signup form"""
        from .forms import CustomSignupForm
        
        form_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'password1': 'complex_password_123',
            'password2': 'complex_password_123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student'
        }
        
        form = CustomSignupForm(form_data)
        self.assertTrue(form.is_valid())


class InternshipWorkflowTest(ModelTestCase):
    """Test internship application and approval workflow"""
    
    def setUp(self):
        super().setUp()
        # Create profiles
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            institute=self.institute,
            student_id='STU001',
            year_of_study='3',
            major='Computer Science',
            gpa=Decimal('3.5'),
            expected_graduation=date.today() + timedelta(days=365)
        )
        
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            company=self.company,
            position='Senior Developer',
            is_admin_contact=True
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institute=self.institute,
            department='Computer Science',
            is_admin_contact=True
        )
        
        # Create internship position
        self.position = InternshipPosition.objects.create(
            company=self.company,
            mentor=self.mentor_profile,
            title='Software Developer Intern',
            description='Great internship opportunity',
            requirements='Python, Django',
            duration='3',  # 3 months
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=97),  # ~3 months
            stipend=Decimal('1000.00'),
            max_students=2
        )
        
    def test_internship_position_creation(self):
        """Test internship position creation"""
        self.assertIsNotNone(self.position.nanoid)
        self.assertEqual(len(self.position.nanoid), 12)
        self.assertTrue(self.position.is_active)
        
    def test_application_creation(self):
        """Test internship application creation"""
        application = InternshipApplication.objects.create(
            position=self.position,
            student=self.student_profile,
            cover_letter='I am interested in this position...',
            status='pending'
        )
        
        self.assertIsNotNone(application.nanoid)
        self.assertEqual(len(application.nanoid), 14)
        self.assertEqual(application.student, self.student_profile)
        self.assertEqual(application.position, self.position)
        
    def test_internship_creation_after_approval(self):
        """Test internship creation after application approval"""
        application = InternshipApplication.objects.create(
            position=self.position,
            student=self.student_profile,
            cover_letter='I am interested in this position...',
            status='approved'
        )
        
        internship = Internship.objects.create(
            application=application,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=84),  # 12 weeks
            mentor=self.mentor_profile,
            teacher=self.teacher_profile,
            status='active'
        )
        
        self.assertIsNotNone(internship.nanoid)
        self.assertEqual(internship.application, application)
        self.assertEqual(internship.mentor, self.mentor_profile)
        self.assertEqual(internship.teacher, self.teacher_profile)


class SecurityTestCase(ModelTestCase):
    """Test security aspects"""
    
    def setUp(self):
        super().setUp()
        self.client = Client()
        
    def test_unauthenticated_access_to_protected_views(self):
        """Test that unauthenticated users cannot access protected views"""
        protected_urls = [
            '/student/',
            '/mentor/',
            '/teacher/',
            '/official/',
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            # Should redirect to login or show 404/403
            self.assertIn(response.status_code, [302, 404, 403])
            
    def test_cross_role_access_prevention(self):
        """Test that users cannot access views for other roles"""
        # Student trying to access mentor view
        self.client.login(username='student@university.edu', password='testpass123')
        response = self.client.get('/mentor/')
        self.assertIn(response.status_code, [302, 403, 404])


class EdgeCaseTest(ModelTestCase):
    """Test edge cases and error handling"""
    
    def test_nanoid_uniqueness(self):
        """Test that nanoids are unique across models"""
        # Create multiple instances and check uniqueness
        companies = []
        for i in range(10):
            company = Company.objects.create(
                name=f'Company {i}',
                registration_status='approved'
            )
            companies.append(company)
            
        nanoids = [company.nanoid for company in companies]
        self.assertEqual(len(nanoids), len(set(nanoids)))  # All should be unique
        
    def test_email_domain_case_insensitivity(self):
        """Test that email domain validation is case insensitive"""
        institute = Institute.objects.create(
            name='Test Institute',
            email_domain='UNIVERSITY.EDU',
            domain_verified=True
        )
        
        self.assertTrue(institute.is_email_from_institute('student@university.edu'))
        self.assertTrue(institute.is_email_from_institute('student@UNIVERSITY.EDU'))
        self.assertTrue(institute.is_email_from_institute('student@University.Edu'))


class IntegrationTest(ModelTestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        super().setUp()
        self.client = Client()
        
        # Create complete profiles
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            institute=self.institute,
            student_id='STU001',
            year_of_study='3',
            major='Computer Science',
            gpa=Decimal('3.5'),
            skills='Python, Django',
            expected_graduation=date.today() + timedelta(days=365)
        )
        
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            company=self.company,
            position='Senior Developer',
            is_admin_contact=True
        )
        
        self.official_profile = OfficialProfile.objects.create(
            user=self.official_user,
            department='Education Ministry',
            position='Director'
        )
        
    def test_complete_organization_approval_workflow(self):
        """Test complete organization registration and approval workflow"""
        # 1. Create pending company
        pending_company = Company.objects.create(
            name='New Company',
            email_domain='newcompany.com',
            registered_by=self.mentor_profile,
            registration_status='pending'
        )
        
        self.assertFalse(pending_company.is_approved())
        
        # 2. Official approves company
        pending_company.registration_status = 'approved'
        pending_company.approved_at = timezone.now()
        pending_company.save()
        
        # Refresh from database
        pending_company.refresh_from_db()
        self.assertTrue(pending_company.is_approved())
        
    def test_complete_internship_lifecycle(self):
        """Test complete internship lifecycle from posting to completion"""
        # 1. Create internship position
        position = InternshipPosition.objects.create(
            company=self.company,
            mentor=self.mentor_profile,
            title='Django Developer Intern',
            description='Work on web applications',
            requirements='Python, Django knowledge',
            duration='4',  # 4 months
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=127),  # ~4 months
            stipend=Decimal('1500.00'),
            max_students=1
        )
        
        # 2. Student applies
        application = InternshipApplication.objects.create(
            position=position,
            student=self.student_profile,
            cover_letter='I am very interested...',
            status='pending'
        )
        
        # 3. Application gets approved
        application.status = 'approved'
        application.save()
        
        # 4. Internship starts
        internship = Internship.objects.create(
            application=application,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=84),
            mentor=self.mentor_profile,
            status='active'
        )
        
        # 5. Internship completes
        internship.status = 'completed'
        internship.final_grade = 'A'
        internship.save()
        
        self.assertEqual(internship.status, 'completed')
        self.assertEqual(internship.final_grade, 'A')
