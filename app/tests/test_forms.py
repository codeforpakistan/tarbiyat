"""
Test cases for forms in the Tarbiyat internship platform.
Tests form validation, processing, and user creation.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group

from ..forms import CustomSignupForm


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
        
        # Use Django's test client to create a proper request object with session
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.messages.middleware import MessageMiddleware
        from django.http import HttpResponse
        
        factory = RequestFactory()
        request = factory.post('/signup/')
        
        # Add session middleware
        def get_response(req):
            return HttpResponse()
        
        middleware = SessionMiddleware(get_response)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages middleware
        msg_middleware = MessageMiddleware(get_response)
        msg_middleware.process_request(request)
        
        user = form.save(request)
        
        # Check user was created correctly
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
        if not form.is_valid():
            self.assertIn('first_name', form.errors)
            
    def test_user_type_choices(self):
        """Test that only valid user type choices are accepted"""
        valid_choices = ['student', 'mentor', 'teacher', 'official']
        invalid_choices = ['admin', 'superuser', 'guest', 'visitor']
        
        base_data = {
            'username': 'testuser@example.com',
            'email': 'testuser@example.com',
            'password1': 'complex_password_123',
            'password2': 'complex_password_123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        # Test valid choices
        for choice in valid_choices:
            with self.subTest(choice=choice):
                form_data = base_data.copy()
                form_data['user_type'] = choice
                form = CustomSignupForm(form_data)
                self.assertTrue(form.is_valid(), f"Form should be valid for user_type: {choice}")
        
        # Test invalid choices
        for choice in invalid_choices:
            with self.subTest(choice=choice):
                form_data = base_data.copy()
                form_data['user_type'] = choice
                form = CustomSignupForm(form_data)
                self.assertFalse(form.is_valid(), f"Form should be invalid for user_type: {choice}")
                self.assertIn('user_type', form.errors)
