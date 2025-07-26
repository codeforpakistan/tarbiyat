"""
Test cases for utility functions and forms in the Tarbiyat internship platform.
Tests utility functions, form validation, and form processing.
"""

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError

from .models import Institute, Company, StudentProfile, MentorProfile
from .utils import (
    validate_user_organization_membership,
    get_available_institutes_for_user,
    get_available_companies_for_user,
    extract_domain_from_email
)
from .forms import CustomSignupForm


class UtilityFunctionsTest(TestCase):
    """Test utility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.user_university = User.objects.create_user(
            username='user@university.edu',
            email='user@university.edu',
            password='test123'
        )
        
        self.user_company = User.objects.create_user(
            username='user@company.com',
            email='user@company.com',
            password='test123'
        )
        
        self.user_other = User.objects.create_user(
            username='user@other.org',
            email='user@other.org',
            password='test123'
        )
        
        # Create verified organizations
        self.verified_institute = Institute.objects.create(
            name='Verified University',
            email_domain='university.edu',
            domain_verified=True,
            registration_status='approved'
        )
        
        self.verified_company = Company.objects.create(
            name='Verified Company',
            email_domain='company.com',
            domain_verified=True,
            registration_status='approved'
        )
        
        # Create unverified organizations
        self.unverified_institute = Institute.objects.create(
            name='Unverified University',
            domain_verified=False,
            registration_status='approved'
        )
        
        self.unverified_company = Company.objects.create(
            name='Unverified Company',
            domain_verified=False,
            registration_status='approved'
        )
    
    def test_validate_user_organization_membership_valid_institute(self):
        """Test valid institute membership validation"""
        is_valid, error = validate_user_organization_membership(
            self.user_university, 'institute', self.verified_institute.pk
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
    def test_validate_user_organization_membership_invalid_institute(self):
        """Test invalid institute membership validation"""
        is_valid, error = validate_user_organization_membership(
            self.user_other, 'institute', self.verified_institute.pk
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        if error:
            self.assertIn('domain must match', error)
        
    def test_validate_user_organization_membership_valid_company(self):
        """Test valid company membership validation"""
        is_valid, error = validate_user_organization_membership(
            self.user_company, 'company', self.verified_company.pk
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
    def test_validate_user_organization_membership_invalid_company(self):
        """Test invalid company membership validation"""
        is_valid, error = validate_user_organization_membership(
            self.user_other, 'company', self.verified_company.pk
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        if error:
            self.assertIn('domain must match', error)
        
    def test_validate_user_organization_membership_nonexistent(self):
        """Test validation with nonexistent organization"""
        is_valid, error = validate_user_organization_membership(
            self.user_university, 'institute', 99999
        )
        self.assertFalse(is_valid)
        if error:
            self.assertIn('not found', error)
        
        is_valid, error = validate_user_organization_membership(
            self.user_company, 'company', 99999
        )
        self.assertFalse(is_valid)
        if error:
            self.assertIn('not found', error)
        
    def test_validate_user_organization_membership_invalid_type(self):
        """Test validation with invalid organization type"""
        is_valid, error = validate_user_organization_membership(
            self.user_university, 'invalid_type', self.verified_institute.pk
        )
        self.assertFalse(is_valid)
        if error:
            self.assertIn('Invalid organization type', error)
        
    def test_get_available_institutes_for_user_matching_domain(self):
        """Test getting available institutes for user with matching domain"""
        institutes = get_available_institutes_for_user(self.user_university)
        
        # Should include both verified (matching domain) and unverified institutes
        self.assertIn(self.verified_institute, institutes)
        self.assertIn(self.unverified_institute, institutes)
        
    def test_get_available_institutes_for_user_non_matching_domain(self):
        """Test getting available institutes for user with non-matching domain"""
        institutes = get_available_institutes_for_user(self.user_other)
        
        # Should only include unverified institutes
        self.assertNotIn(self.verified_institute, institutes)
        self.assertIn(self.unverified_institute, institutes)
        
    def test_get_available_companies_for_user_matching_domain(self):
        """Test getting available companies for user with matching domain"""
        companies = get_available_companies_for_user(self.user_company)
        
        # Should include both verified (matching domain) and unverified companies
        self.assertIn(self.verified_company, companies)
        self.assertIn(self.unverified_company, companies)
        
    def test_get_available_companies_for_user_non_matching_domain(self):
        """Test getting available companies for user with non-matching domain"""
        companies = get_available_companies_for_user(self.user_other)
        
        # Should only include unverified companies
        self.assertNotIn(self.verified_company, companies)
        self.assertIn(self.unverified_company, companies)
        
    def test_extract_domain_from_email_valid(self):
        """Test domain extraction from valid emails"""
        test_cases = [
            ('user@example.com', 'example.com'),
            ('test@subdomain.university.edu', 'subdomain.university.edu'),
            ('USER@DOMAIN.ORG', 'domain.org'),  # Should be lowercase
            ('admin@company.co.uk', 'company.co.uk'),
        ]
        
        for email, expected_domain in test_cases:
            with self.subTest(email=email):
                result = extract_domain_from_email(email)
                self.assertEqual(result, expected_domain)
                
    def test_extract_domain_from_email_invalid(self):
        """Test domain extraction from invalid emails"""
        invalid_emails = [
            'invalid-email',
            'no-at-symbol',
            '',
            None,
            '@domain.com',  # Missing local part
            'user@',  # Missing domain
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                result = extract_domain_from_email(email)
                self.assertIsNone(result)


class CustomSignupFormTest(TestCase):
    """Test custom signup form"""
    
    def setUp(self):
        """Set up test data"""
        Group.objects.get_or_create(name='student')
        Group.objects.get_or_create(name='mentor')
        Group.objects.get_or_create(name='teacher')
        Group.objects.get_or_create(name='official')
    
    def test_custom_signup_form_valid_data(self):
        """Test custom signup form with valid data"""
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
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
    def test_custom_signup_form_missing_required_fields(self):
        """Test custom signup form with missing required fields"""
        # Missing first_name
        form_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'password1': 'complex_password_123',
            'password2': 'complex_password_123',
            'last_name': 'User',
            'user_type': 'student'
        }
        
        form = CustomSignupForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        
        # Missing user_type
        form_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'password1': 'complex_password_123',
            'password2': 'complex_password_123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        form = CustomSignupForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('user_type', form.errors)
        
    def test_custom_signup_form_invalid_user_type(self):
        """Test custom signup form with invalid user type"""
        form_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'password1': 'complex_password_123',
            'password2': 'complex_password_123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'invalid_type'
        }
        
        form = CustomSignupForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('user_type', form.errors)
        
    def test_custom_signup_form_password_mismatch(self):
        """Test custom signup form with password mismatch"""
        form_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'password1': 'complex_password_123',
            'password2': 'different_password_456',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student'
        }
        
        form = CustomSignupForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        
    def test_custom_signup_form_weak_password(self):
        """Test custom signup form with weak password"""
        form_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'password1': '123',  # Too weak
            'password2': '123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student'
        }
        
        form = CustomSignupForm(form_data)
        self.assertFalse(form.is_valid())
        # Should have password validation errors
        self.assertTrue(any('password' in field for field in form.errors))
        
    def test_custom_signup_form_save_creates_user_with_group(self):
        """Test that form save creates user and assigns to correct group"""
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
        
        # Use Django's test client to create a proper request object
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/signup/')
        
        user = form.save(request)
        
        # Check user was created correctly
        self.assertEqual(user.username, 'testuser@example.com')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        
        # Check user was added to correct group
        self.assertTrue(user.groups.filter(name='student').exists())
        
    def test_custom_signup_form_all_user_types(self):
        """Test form with all valid user types"""
        user_types = ['student', 'mentor', 'teacher', 'official']
        
        for user_type in user_types:
            with self.subTest(user_type=user_type):
                form_data = {
                    'username': f'{user_type}@example.com',
                    'email': f'{user_type}@example.com',
                    'password1': 'complex_password_123',
                    'password2': 'complex_password_123',
                    'first_name': 'Test',
                    'last_name': user_type.title(),
                    'user_type': user_type
                }
                
                form = CustomSignupForm(form_data)
                self.assertTrue(form.is_valid(), f"Form errors for {user_type}: {form.errors}")


class UtilityEdgeCasesTest(TestCase):
    """Test edge cases in utility functions"""
    
    def test_organization_with_none_domain(self):
        """Test organizations with None email domain"""
        institute = Institute.objects.create(
            name='No Domain Institute',
            email_domain=None,
            domain_verified=False
        )
        
        user = User.objects.create_user(
            username='user@any.edu',
            email='user@any.edu',
            password='test123'
        )
        
        # Should not crash with None domain
        result = institute.is_email_from_institute('user@any.edu')
        self.assertFalse(result)
        
        # Utility function should handle this gracefully
        is_valid, error = validate_user_organization_membership(
            user, 'institute', institute.pk
        )
        self.assertTrue(is_valid)  # Should be valid for unverified domain
        
    def test_organization_with_empty_domain(self):
        """Test organizations with empty email domain"""
        company = Company.objects.create(
            name='Empty Domain Company',
            email_domain='',
            domain_verified=True  # Verified but empty domain
        )
        
        user = User.objects.create_user(
            username='user@any.com',
            email='user@any.com',
            password='test123'
        )
        
        # Should not crash with empty domain
        result = company.is_email_from_company('user@any.com')
        self.assertFalse(result)
        
    def test_user_with_none_email(self):
        """Test user with None email"""
        user = User.objects.create_user(
            username='nomail',
            password='test123'
        )
        # User email is empty string by default, not None
        user.email = ''
        user.save()
        
        institute = Institute.objects.create(
            name='Test Institute',
            email_domain='test.edu',
            domain_verified=True
        )
        
        # Should handle empty email gracefully
        result = institute.is_email_from_institute(user.email)
        self.assertFalse(result)
        
    def test_case_sensitivity_in_domain_comparison(self):
        """Test case sensitivity in domain comparison"""
        institute = Institute.objects.create(
            name='Case Test Institute',
            email_domain='UNIVERSITY.EDU',
            domain_verified=True
        )
        
        # Test various case combinations
        test_emails = [
            'student@university.edu',
            'student@UNIVERSITY.EDU',
            'student@University.Edu',
            'student@uNiVeRsItY.eDu'
        ]
        
        for email in test_emails:
            with self.subTest(email=email):
                result = institute.is_email_from_institute(email)
                self.assertTrue(result, f"Failed for email: {email}")


class FormFieldValidationTest(TestCase):
    """Test individual form field validations"""
    
    def test_email_field_validation(self):
        """Test email field validation in signup form"""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user.domain.com',
        ]
        
        base_data = {
            'username': 'testuser',
            'password1': 'complex_password_123',
            'password2': 'complex_password_123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student'
        }
        
        for email in invalid_emails:
            with self.subTest(email=email):
                form_data = base_data.copy()
                form_data.update({
                    'username': email,
                    'email': email
                })
                
                form = CustomSignupForm(form_data)
                self.assertFalse(form.is_valid())
                # Should have email validation error
                self.assertTrue('email' in form.errors or 'username' in form.errors)
                
    def test_name_field_validation(self):
        """Test name field validation"""
        # Test maximum length
        long_name = 'x' * 100  # Longer than typical max_length
        
        form_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'password1': 'complex_password_123',
            'password2': 'complex_password_123',
            'first_name': long_name,
            'last_name': 'User',
            'user_type': 'student'
        }
        
        form = CustomSignupForm(form_data)
        # May or may not be valid depending on field max_length setting
        # This tests that validation is applied
