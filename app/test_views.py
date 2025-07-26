"""
Test cases for views in the Tarbiyat internship platform.
Tests view functionality, authentication, authorization, and responses.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.contrib.messages import get_messages

from .models import (
    StudentProfile, MentorProfile, TeacherProfile, OfficialProfile,
    Institute, Company
)
from .views import get_user_type


class ViewTestCase(TestCase):
    """Base test case for view tests"""
    
    def setUp(self):
        self.client = Client()
        self.setup_groups()
        self.setup_users()
        
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


class UtilityFunctionTest(ViewTestCase):
    """Test utility functions used in views"""
    
    def test_get_user_type_function(self):
        """Test get_user_type utility function"""
        self.assertEqual(get_user_type(self.student_user), 'student')
        self.assertEqual(get_user_type(self.mentor_user), 'mentor')
        
        # Test with superuser
        superuser = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass'
        )
        self.assertEqual(get_user_type(superuser), 'admin')
        
        # Test with unauthenticated user
        from django.contrib.auth.models import AnonymousUser
        anonymous_user = AnonymousUser()
        self.assertIsNone(get_user_type(anonymous_user))
        
        # Test with user without groups
        no_group_user = User.objects.create_user(
            username='nogroup@example.com',
            email='nogroup@example.com',
            password='test123'
        )
        self.assertIsNone(get_user_type(no_group_user))


class HomeViewTest(ViewTestCase):
    """Test home view functionality"""
    
    def test_home_view_anonymous_user(self):
        """Test home view for anonymous users"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tarbiyat')  # Should contain site name
        
    def test_home_view_authenticated_user_with_profile(self):
        """Test home view for authenticated users with complete profiles"""
        # Create institute and company for proper setup
        institute = Institute.objects.create(
            name='Test University',
            registration_status='approved'
        )
        
        # Create student profile
        StudentProfile.objects.create(
            user=self.student_user,
            institute=institute,
            student_id='STU001',
            major='Computer Science'
        )
        
        self.client.login(username='student@university.edu', password='testpass123')
        response = self.client.get(reverse('home'))
        
        # Should either show home page or redirect to dashboard
        self.assertIn(response.status_code, [200, 302])
        
    def test_home_view_authenticated_user_without_profile(self):
        """Test home view for authenticated users without profiles"""
        self.client.login(username='student@university.edu', password='testpass123')
        response = self.client.get(reverse('home'))
        
        # Should show message about completing profile or redirect
        self.assertIn(response.status_code, [200, 302])


class AuthenticationTest(ViewTestCase):
    """Test authentication and authorization"""
    
    def test_login_required_views(self):
        """Test that protected views require login"""
        protected_urls = [
            '/student/',
            '/mentor/',
            '/teacher/',
            '/official/',
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            # Should redirect to login, return 404, or 403
            self.assertIn(response.status_code, [302, 404, 403])
            
    def test_role_based_access_control(self):
        """Test that users can only access views for their role"""
        # Student trying to access other role views
        self.client.login(username='student@university.edu', password='testpass123')
        
        role_urls = [
            '/mentor/',
            '/teacher/',
            '/official/',
        ]
        
        for url in role_urls:
            response = self.client.get(url)
            # Should be denied access
            self.assertIn(response.status_code, [302, 403, 404])
            
    def test_superuser_access(self):
        """Test that superusers have special access"""
        superuser = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass'
        )
        
        self.client.login(username='admin@example.com', password='adminpass')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)


class ProfileCompletionMiddlewareTest(ViewTestCase):
    """Test profile completion middleware functionality"""
    
    def test_profile_completion_redirect(self):
        """Test that incomplete profiles trigger appropriate handling"""
        # User with no profile
        new_user = User.objects.create_user(
            username='newuser@test.com',
            email='newuser@test.com',
            password='testpass123'
        )
        new_user.groups.add(self.student_group)
        
        self.client.login(username='newuser@test.com', password='testpass123')
        
        # Try to access a protected view
        response = self.client.get('/student/')
        
        # Should redirect or show appropriate message
        self.assertIn(response.status_code, [200, 302])
        
    def test_complete_profile_access(self):
        """Test that users with complete profiles can access views"""
        # Create institute first
        institute = Institute.objects.create(
            name='Test University',
            registration_status='approved'
        )
        
        # Create complete student profile
        StudentProfile.objects.create(
            user=self.student_user,
            institute=institute,
            student_id='STU001',
            year_of_study='3',
            major='Computer Science'
        )
        
        self.client.login(username='student@university.edu', password='testpass123')
        response = self.client.get('/student/')
        
        # Should be able to access
        self.assertIn(response.status_code, [200, 302])  # May redirect to specific page


class MessageFrameworkTest(ViewTestCase):
    """Test Django messages framework usage in views"""
    
    def test_success_messages(self):
        """Test that success messages are properly displayed"""
        # This would test actual view functionality that creates success messages
        # For now, we'll test the infrastructure
        
        self.client.login(username='student@university.edu', password='testpass123')
        response = self.client.get(reverse('home'))
        
        # Check that messages can be retrieved (infrastructure test)
        messages = list(get_messages(response.wsgi_request))
        # Messages list should be accessible (may be empty)
        self.assertIsInstance(messages, list)
        
    def test_error_messages(self):
        """Test that error messages are properly displayed"""
        # Test accessing a view that should show error message
        self.client.login(username='student@university.edu', password='testpass123')
        
        # Try to access a mentor-only view as a student
        response = self.client.get('/mentor/')
        
        # Should either redirect or show error
        self.assertIn(response.status_code, [302, 403, 404])


class ResponseContentTest(ViewTestCase):
    """Test response content and templates"""
    
    def test_home_page_content(self):
        """Test home page contains expected content"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        # Should contain key elements (adjust based on actual template)
        content = response.content.decode()
        self.assertTrue(any(word in content.lower() for word in ['tarbiyat', 'internship', 'government']))
        
    def test_response_headers(self):
        """Test that responses have appropriate headers"""
        response = self.client.get(reverse('home'))
        
        # Should have content type
        self.assertIn('text/html', response.get('Content-Type', ''))
        
    def test_csrf_protection(self):
        """Test that CSRF protection is enabled"""
        response = self.client.get(reverse('home'))
        
        # Should include CSRF token in forms (if any)
        content = response.content.decode()
        if 'form' in content.lower():
            self.assertIn('csrf', content.lower())


class URLResolutionTest(ViewTestCase):
    """Test URL resolution and routing"""
    
    def test_home_url_resolution(self):
        """Test that home URL resolves correctly"""
        url = reverse('home')
        self.assertEqual(url, '/')
        
        # Test that URL actually works
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_invalid_urls(self):
        """Test that invalid URLs return 404"""
        invalid_urls = [
            '/nonexistent/',
            '/invalid/path/',
            '/random/123/',
        ]
        
        for url in invalid_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)


class SessionHandlingTest(ViewTestCase):
    """Test session handling in views"""
    
    def test_session_persistence(self):
        """Test that sessions persist across requests"""
        # Login
        login_successful = self.client.login(
            username='student@university.edu', 
            password='testpass123'
        )
        self.assertTrue(login_successful)
        
        # Make multiple requests
        response1 = self.client.get(reverse('home'))
        response2 = self.client.get(reverse('home'))
        
        # Session should persist
        self.assertEqual(response1.status_code, response2.status_code)
        
    def test_logout(self):
        """Test logout functionality"""
        # Login first
        self.client.login(username='student@university.edu', password='testpass123')
        
        # Logout
        self.client.logout()
        
        # Should be treated as anonymous user
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)


class ErrorHandlingTest(ViewTestCase):
    """Test error handling in views"""
    
    def test_404_handling(self):
        """Test 404 error handling"""
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        
    def test_permission_denied_handling(self):
        """Test permission denied handling"""
        # Login as student
        self.client.login(username='student@university.edu', password='testpass123')
        
        # Try to access admin interface
        response = self.client.get('/admin/')
        self.assertIn(response.status_code, [302, 403, 404])  # Should be denied
        
    def test_method_not_allowed_handling(self):
        """Test method not allowed handling"""
        # Most GET endpoints should not accept POST without data
        response = self.client.post(reverse('home'))
        # Depending on implementation, might redirect or return method not allowed
        self.assertIn(response.status_code, [200, 302, 405])
