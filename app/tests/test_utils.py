"""
Test cases for utility functions in the Tarbiyat internship platform.
Tests domain validation, user organization membership, and helper functions.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group
from django.utils import timezone
from unittest.mock import Mock

from ..models import Institute, Company, MentorProfile, OfficialProfile
from ..utils import (
    validate_user_organization_membership,
    get_available_institutes_for_user,
    get_available_companies_for_user,
    extract_domain_from_email
)
from ..views import get_user_type


class UtilityFunctionTest(TestCase):
    """Test utility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.setup_groups()
        self.setup_test_data()
        
    def setup_groups(self):
        """Create user groups"""
        Group.objects.get_or_create(name='student')
        Group.objects.get_or_create(name='mentor')
        Group.objects.get_or_create(name='teacher')
        Group.objects.get_or_create(name='official')
        
    def setup_test_data(self):
        """Set up test organizations and users"""
        # Create institute
        self.institute = Institute.objects.create(
            name='Test University',
            email_domain='university.edu',
            contact_email='admin@university.edu',
            registration_status='approved',
            approved_at=timezone.now()
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            email_domain='company.com',
            contact_email='hr@company.com',
            registration_status='approved',
            approved_at=timezone.now()
        )
        
        # Create user for testing
        self.test_user = User.objects.create_user(
            username='testuser@university.edu',
            email='testuser@university.edu',
            password='testpass123'
        )
        
    def test_extract_domain_from_email(self):
        """Test domain extraction from email addresses"""
        test_cases = [
            ('user@example.com', 'example.com'),
            ('test.user@university.edu', 'university.edu'),
            ('admin@subdomain.company.org', 'subdomain.company.org'),
            ('simple@domain.co.uk', 'domain.co.uk'),
        ]
        
        for email, expected_domain in test_cases:
            with self.subTest(email=email):
                result = extract_domain_from_email(email)
                self.assertEqual(result, expected_domain)
                
    def test_extract_domain_from_invalid_email(self):
        """Test domain extraction from invalid email addresses"""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user.domain.com',
            '',
            None
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                result = extract_domain_from_email(email)
                # Should return None or empty string for invalid emails
                self.assertIn(result, [None, '', email])
                
    def test_validate_user_organization_membership_company(self):
        """Test user organization membership validation for companies"""
        # Create user with matching domain
        company_user = User.objects.create_user(
            username='employee@company.com',
            email='employee@company.com',
            password='testpass123'
        )
        
        # Should return True for matching domain
        result = validate_user_organization_membership(
            company_user, 
            'company', 
            self.company.nanoid
        )
        self.assertTrue(result)
        
        # Create user with non-matching domain
        other_user = User.objects.create_user(
            username='outsider@otherdomain.com',
            email='outsider@otherdomain.com',
            password='testpass123'
        )
        
        # Should return False for non-matching domain
        result = validate_user_organization_membership(
            other_user, 
            'company', 
            self.company.nanoid
        )
        self.assertFalse(result)
        
    def test_validate_user_organization_membership_institute(self):
        """Test user organization membership validation for institutes"""
        # Create user with matching domain
        student_user = User.objects.create_user(
            username='student@university.edu',
            email='student@university.edu',
            password='testpass123'
        )
        
        # Should return True for matching domain
        result = validate_user_organization_membership(
            student_user, 
            'institute', 
            self.institute.nanoid
        )
        self.assertTrue(result)
        
        # Create user with non-matching domain
        other_user = User.objects.create_user(
            username='outsider@otherdomain.com',
            email='outsider@otherdomain.com',
            password='testpass123'
        )
        
        # Should return False for non-matching domain
        result = validate_user_organization_membership(
            other_user, 
            'institute', 
            self.institute.nanoid
        )
        self.assertFalse(result)
        
    def test_validate_user_organization_membership_invalid_type(self):
        """Test user organization membership validation with invalid type"""
        result = validate_user_organization_membership(
            self.test_user, 
            'invalid_type', 
            'some_id'
        )
        self.assertFalse(result)
        
    def test_get_available_institutes_for_user(self):
        """Test getting available institutes for user"""
        # Create multiple institutes
        institute2 = Institute.objects.create(
            name='Another University',
            email_domain='another.edu',
            contact_email='admin@another.edu',
            registration_status='approved',
            approved_at=timezone.now()
        )
        
        # Create pending institute (should not be available)
        Institute.objects.create(
            name='Pending University',
            email_domain='pending.edu',
            contact_email='admin@pending.edu',
            registration_status='pending'
        )
        
        # Get available institutes
        available_institutes = get_available_institutes_for_user(self.test_user)
        
        # Should only return approved institutes
        self.assertEqual(len(available_institutes), 2)
        institute_names = {inst.name for inst in available_institutes}
        self.assertIn('Test University', institute_names)
        self.assertIn('Another University', institute_names)
        self.assertNotIn('Pending University', institute_names)
        
    def test_get_available_companies_for_user(self):
        """Test getting available companies for user"""
        # Create multiple companies
        company2 = Company.objects.create(
            name='Another Company',
            email_domain='another.com',
            contact_email='hr@another.com',
            registration_status='approved',
            approved_at=timezone.now()
        )
        
        # Create pending company (should not be available)
        Company.objects.create(
            name='Pending Company',
            email_domain='pending.com',
            contact_email='hr@pending.com',
            registration_status='pending'
        )
        
        # Get available companies
        available_companies = get_available_companies_for_user(self.test_user)
        
        # Should only return approved companies
        self.assertEqual(len(available_companies), 2)
        company_names = {comp.name for comp in available_companies}
        self.assertIn('Test Company', company_names)
        self.assertIn('Another Company', company_names)
        self.assertNotIn('Pending Company', company_names)
        
    def test_get_user_type_with_groups(self):
        """Test get_user_type utility function with different user groups"""
        # Test student user
        student_user = User.objects.create_user(
            username='student@test.com',
            email='student@test.com',
            password='testpass123'
        )
        student_group = Group.objects.get(name='student')
        student_user.groups.add(student_group)
        
        user_type = get_user_type(student_user)
        self.assertEqual(user_type, 'student')
        
        # Test mentor user
        mentor_user = User.objects.create_user(
            username='mentor@test.com',
            email='mentor@test.com',
            password='testpass123'
        )
        mentor_group = Group.objects.get(name='mentor')
        mentor_user.groups.add(mentor_group)
        
        user_type = get_user_type(mentor_user)
        self.assertEqual(user_type, 'mentor')
        
    def test_get_user_type_no_groups(self):
        """Test get_user_type with user having no groups"""
        user_no_groups = User.objects.create_user(
            username='nogroups@test.com',
            email='nogroups@test.com',
            password='testpass123'
        )
        
        user_type = get_user_type(user_no_groups)
        self.assertIsNone(user_type)
        
    def test_get_user_type_multiple_groups(self):
        """Test get_user_type with user in multiple groups"""
        multi_group_user = User.objects.create_user(
            username='multigroup@test.com',
            email='multigroup@test.com',
            password='testpass123'
        )
        
        # Add user to multiple groups
        student_group = Group.objects.get(name='student')
        mentor_group = Group.objects.get(name='mentor')
        multi_group_user.groups.add(student_group)
        multi_group_user.groups.add(mentor_group)
        
        user_type = get_user_type(multi_group_user)
        # Should return one of the types (implementation dependent)
        self.assertIn(user_type, ['student', 'mentor'])
        
    def test_get_user_type_with_none_user(self):
        """Test get_user_type with None user"""
        user_type = get_user_type(None)
        self.assertIsNone(user_type)


class UtilityErrorHandlingTest(TestCase):
    """Test error handling in utility functions"""
    
    def test_validate_organization_membership_nonexistent_org(self):
        """Test validation with non-existent organization"""
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test with non-existent organization ID
        result = validate_user_organization_membership(
            user, 
            'company', 
            'nonexistent_id'
        )
        self.assertFalse(result)
        
    def test_utility_functions_with_edge_cases(self):
        """Test utility functions with edge cases"""
        # Test with empty strings
        result = extract_domain_from_email('')
        self.assertIn(result, [None, ''])
        
        # Test with whitespace
        result = extract_domain_from_email('  ')
        self.assertIn(result, [None, '', '  '])
        
        # Test organization functions with None user
        result_institutes = get_available_institutes_for_user(None)
        result_companies = get_available_companies_for_user(None)
        
        # Should handle None gracefully (implementation dependent)
        self.assertIsNotNone(result_institutes)
        self.assertIsNotNone(result_companies)
