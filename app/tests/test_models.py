"""
Test cases specifically for Django models in the Tarbiyat internship platform.
Tests model creation, validation, methods, and relationships.
"""

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from ..models import (
    StudentProfile, MentorProfile, TeacherProfile, OfficialProfile,
    Institute, Company, InternshipPosition, InternshipApplication,
    Internship, ProgressReport, Notification
)


class BaseModelTestCase(TestCase):
    """Base test case with common setup for model tests"""
    
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


class NanoidGenerationTest(BaseModelTestCase):
    """Test nanoid generation across different models"""
    
    def test_nanoid_generation_and_uniqueness(self):
        """Test that nanoids are generated and unique"""
        # Test Institute nanoids (10 chars)
        institutes = []
        for i in range(5):
            inst = Institute.objects.create(
                name=f'Institute {i}',
                registration_status='approved'
            )
            institutes.append(inst)
            self.assertEqual(len(inst.nanoid), 10)
            
        # Check uniqueness
        institute_nanoids = [inst.nanoid for inst in institutes]
        self.assertEqual(len(institute_nanoids), len(set(institute_nanoids)))
        
        # Test Company nanoids (10 chars)
        companies = []
        for i in range(5):
            comp = Company.objects.create(
                name=f'Company {i}',
                registration_status='approved'
            )
            companies.append(comp)
            self.assertEqual(len(comp.nanoid), 10)
            
        # Check uniqueness
        company_nanoids = [comp.nanoid for comp in companies]
        self.assertEqual(len(company_nanoids), len(set(company_nanoids)))
        
        # Test Profile nanoids (12 chars)
        student_profile = StudentProfile.objects.create(user=self.student_user)
        mentor_profile = MentorProfile.objects.create(user=self.mentor_user)
        teacher_profile = TeacherProfile.objects.create(user=self.teacher_user)
        official_profile = OfficialProfile.objects.create(user=self.official_user)
        
        for profile in [student_profile, mentor_profile, teacher_profile, official_profile]:
            self.assertEqual(len(profile.nanoid), 12)
            
        # Test InternshipPosition nanoids (12 chars)
        position = InternshipPosition.objects.create(
            company=self.company,
            title='Test Position'
        )
        self.assertEqual(len(position.nanoid), 12)


class OrganizationDomainVerificationTest(BaseModelTestCase):
    """Test email domain verification for organizations"""
    
    def test_institute_domain_verification(self):
        """Test institute email domain verification"""
        # Test with verified domain
        verified_institute = Institute.objects.create(
            name='Verified University',
            email_domain='verified.edu',
            domain_verified=True
        )
        
        self.assertTrue(verified_institute.is_email_from_institute('student@verified.edu'))
        self.assertTrue(verified_institute.is_email_from_institute('STUDENT@VERIFIED.EDU'))  # Case insensitive
        self.assertFalse(verified_institute.is_email_from_institute('student@other.edu'))
        self.assertFalse(verified_institute.is_email_from_institute(''))
        self.assertFalse(verified_institute.is_email_from_institute(None))
        
        # Test without domain verification
        unverified_institute = Institute.objects.create(
            name='Unverified University',
            domain_verified=False
        )
        
        # Without domain verification, method should handle gracefully
        self.assertFalse(unverified_institute.is_email_from_institute('student@any.edu'))
        
    def test_company_domain_verification(self):
        """Test company email domain verification"""
        # Test with verified domain
        verified_company = Company.objects.create(
            name='Verified Company',
            email_domain='verified.com',
            domain_verified=True
        )
        
        self.assertTrue(verified_company.is_email_from_company('employee@verified.com'))
        self.assertTrue(verified_company.is_email_from_company('EMPLOYEE@VERIFIED.COM'))  # Case insensitive
        self.assertFalse(verified_company.is_email_from_company('employee@other.com'))
        self.assertFalse(verified_company.is_email_from_company(''))
        self.assertFalse(verified_company.is_email_from_company(None))


class ProfileCompletionTest(BaseModelTestCase):
    """Test profile completion calculations"""
    
    def test_student_profile_completion_complete(self):
        """Test student profile completion with all fields filled"""
        complete_profile = StudentProfile.objects.create(
            user=self.student_user,
            institute=self.institute,
            student_id='STU001',
            year_of_study='3',
            major='Computer Science',
            gpa=Decimal('3.5'),
            skills='Python, Django, JavaScript',
            expected_graduation=date.today() + timedelta(days=365),
            portfolio_url='https://example.com'
        )
        
        completion = complete_profile.get_profile_completion()
        self.assertGreaterEqual(completion, 90)  # Should be very high
        
    def test_student_profile_completion_minimal(self):
        """Test student profile completion with minimal fields"""
        minimal_profile = StudentProfile.objects.create(
            user=self.mentor_user  # Using different user
        )
        
        completion = minimal_profile.get_profile_completion()
        self.assertLess(completion, 30)  # Should be low
        
    def test_student_profile_completion_status_messages(self):
        """Test profile completion status messages"""
        # Complete profile
        complete_profile = StudentProfile.objects.create(
            user=self.student_user,
            institute=self.institute,
            student_id='STU001',
            year_of_study='3',
            major='Computer Science',
            gpa=Decimal('3.5'),
            skills='Python, Django',
            expected_graduation=date.today() + timedelta(days=365)
        )
        
        status = complete_profile.get_completion_status()
        self.assertIn('complete', status.lower())
        
        # Minimal profile
        minimal_profile = StudentProfile.objects.create(
            user=self.mentor_user
        )
        
        status = minimal_profile.get_completion_status()
        self.assertIn('%', status)  # Should contain percentage


class OrganizationMembershipValidationTest(BaseModelTestCase):
    """Test organization membership validation"""
    
    def test_student_institute_membership_validation(self):
        """Test student institute membership validation"""
        # Create student profile with matching domain
        student_profile = StudentProfile.objects.create(
            user=self.student_user,
            institute=self.institute
        )
        
        # Should pass validation
        try:
            student_profile.validate_institute_membership()
        except ValidationError:
            self.fail("validate_institute_membership() raised ValidationError unexpectedly")
            
        # Create student with non-matching domain
        wrong_user = User.objects.create_user(
            username='wrong@other.edu',
            email='wrong@other.edu',
            password='test123'
        )
        
        wrong_profile = StudentProfile.objects.create(
            user=wrong_user,
            institute=self.institute
        )
        
        # Should fail validation
        with self.assertRaises(ValidationError):
            wrong_profile.validate_institute_membership()
            
    def test_mentor_company_membership_validation(self):
        """Test mentor company membership validation"""
        # Create mentor profile with matching domain
        mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            company=self.company
        )
        
        # Should pass validation
        try:
            mentor_profile.validate_company_membership()
        except ValidationError:
            self.fail("validate_company_membership() raised ValidationError unexpectedly")
            
        # Create mentor with non-matching domain
        wrong_user = User.objects.create_user(
            username='wrong@other.com',
            email='wrong@other.com',
            password='test123'
        )
        
        wrong_profile = MentorProfile.objects.create(
            user=wrong_user,
            company=self.company
        )
        
        # Should fail validation
        with self.assertRaises(ValidationError):
            wrong_profile.validate_company_membership()


class InternshipWorkflowModelTest(BaseModelTestCase):
    """Test internship workflow models"""
    
    def setUp(self):
        super().setUp()
        # Create profiles
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            institute=self.institute,
            student_id='STU001',
            major='Computer Science'
        )
        
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            company=self.company,
            position='Senior Developer'
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institute=self.institute,
            department='Computer Science'
        )
        
    def test_internship_position_properties(self):
        """Test internship position properties and methods"""
        position = InternshipPosition.objects.create(
            company=self.company,
            mentor=self.mentor_profile,
            title='Software Engineer Intern',
            description='Great opportunity',
            max_students=2
        )
        
        # Test string representation
        self.assertIn('Software Engineer Intern', str(position))
        self.assertIn('Test Company', str(position))
        
        # Test available spots (initially should equal max_students)
        self.assertEqual(position.available_spots, 2)
        
        # Create applications and test available spots
        app1 = InternshipApplication.objects.create(
            position=position,
            student=self.student_profile,
            status='pending'
        )
        self.assertEqual(position.available_spots, 2)  # Pending doesn't reduce spots
        
        app1.status = 'approved'
        app1.save()
        position.refresh_from_db()
        self.assertEqual(position.available_spots, 1)  # Approved reduces spots
        
    def test_internship_application_unique_constraint(self):
        """Test that students can't apply to same position twice"""
        position = InternshipPosition.objects.create(
            company=self.company,
            mentor=self.mentor_profile,
            title='Test Position'
        )
        
        # First application should succeed
        app1 = InternshipApplication.objects.create(
            position=position,
            student=self.student_profile,
            cover_letter='First application'
        )
        
        # Second application from same student should fail
        with self.assertRaises(Exception):  # Django will raise IntegrityError
            InternshipApplication.objects.create(
                position=position,
                student=self.student_profile,
                cover_letter='Second application'
            )
            
    def test_internship_progress_calculation(self):
        """Test internship progress calculation"""
        # Create internship
        application = InternshipApplication.objects.create(
            position=InternshipPosition.objects.create(
                company=self.company,
                mentor=self.mentor_profile,
                title='Test Position'
            ),
            student=self.student_profile,
            status='approved'
        )
        
        today = date.today()
        internship = Internship.objects.create(
            application=application,
            student=self.student_profile,
            mentor=self.mentor_profile,
            start_date=today - timedelta(days=30),  # Started 30 days ago
            end_date=today + timedelta(days=60),    # Ends in 60 days
            status='active'
        )
        
        # Should be around 33% complete (30 out of 90 days)
        progress = internship.get_progress_percentage()
        self.assertGreater(progress, 25)
        self.assertLess(progress, 40)
        
        # Test completed internship
        completed_internship = Internship.objects.create(
            application=application,
            student=self.student_profile,
            mentor=self.mentor_profile,
            start_date=today - timedelta(days=90),
            end_date=today - timedelta(days=1),  # Ended yesterday
            status='completed'
        )
        
        progress = completed_internship.get_progress_percentage()
        self.assertEqual(progress, 100)


class ModelStringRepresentationTest(BaseModelTestCase):
    """Test string representations of models"""
    
    def test_model_string_representations(self):
        """Test __str__ methods of all models"""
        # Institute
        institute = Institute.objects.create(
            name='Test Institute',
            registration_status='approved'
        )
        self.assertIn('✓', str(institute))
        self.assertIn('Test Institute', str(institute))
        
        pending_institute = Institute.objects.create(
            name='Pending Institute',
            registration_status='pending'
        )
        self.assertIn('⚠', str(pending_institute))
        
        # Company
        company = Company.objects.create(
            name='Test Company',
            registration_status='approved'
        )
        self.assertIn('✓', str(company))
        self.assertIn('Test Company', str(company))
        
        # Profiles
        student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id='STU001'
        )
        self.assertIn('John Student', str(student_profile))
        self.assertIn('STU001', str(student_profile))
        
        mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            company=company
        )
        self.assertIn('Jane Mentor', str(mentor_profile))
        self.assertIn('Test Company', str(mentor_profile))
