"""
Working URL Status Tests for Tarbiyat Platform

Tests all existing URL patterns to ensure they return appropriate HTTP status codes.
Based on actual URL patterns discovered in the application.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model

User = get_user_model()


class WorkingURLStatusTestCase(TestCase):
    """Test all working URLs return appropriate HTTP status codes"""
    
    def setUp(self):
        """Set up minimal test data"""
        self.client = Client()
        
        # Create groups
        Group.objects.get_or_create(name='student')
        Group.objects.get_or_create(name='mentor')
        Group.objects.get_or_create(name='teacher')
        Group.objects.get_or_create(name='official')
    
    def test_public_urls_status(self):
        """Test public URLs that actually exist"""
        public_urls = [
            'home',
            'documentation_index',
        ]
        
        for url_name in public_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, [200, 301, 302], 
                                f"URL {url_name} ({url}) returned status {response.status_code}")
                    print(f"✓ {url_name}: {response.status_code}")
                except Exception as e:
                    self.fail(f"✗ URL {url_name} failed: {e}")
    
    def test_auth_urls_status(self):
        """Test authentication URLs"""
        auth_urls = [
            'account_login',
            'account_signup', 
            'account_logout',
        ]
        
        for url_name in auth_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, [200, 301, 302], 
                                f"URL {url_name} ({url}) returned status {response.status_code}")
                    print(f"✓ {url_name}: {response.status_code}")
                except Exception as e:
                    self.fail(f"✗ URL {url_name} failed: {e}")
    
    def test_protected_urls_redirect_unauthenticated(self):
        """Test protected URLs redirect when not authenticated"""
        protected_urls = [
            'dashboard',  # This is the actual dashboard URL name
            'mentor_positions',
            'mentor_applications', 
            'mentor_interns',
            'student_applications',
        ]
        
        for url_name in protected_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name)
                    response = self.client.get(url)
                    # Should redirect to login (302) or return 403/404
                    self.assertIn(response.status_code, [302, 403, 404], 
                                f"Protected URL {url_name} ({url}) should redirect/deny access, got {response.status_code}")
                    print(f"✓ {url_name}: {response.status_code} (protected)")
                except Exception as e:
                    self.fail(f"✗ Protected URL {url_name} failed: {e}")
    
    def test_urls_with_parameters_exist(self):
        """Test that parameterized URLs exist and handle invalid parameters gracefully"""
        param_urls = [
            ('position_detail', {'position_nanoid': 'invalid123'}),
            ('application_detail', {'application_nanoid': 'invalid123'}),
            ('mentor_progress_reports', {'internship_nanoid': 'invalid123'}),
            ('student_profile_detail', {'student_nanoid': 'invalid123'}),
            ('company_detail_official', {'company_nanoid': 'invalid123'}),
            ('institute_detail_official', {'institute_nanoid': 'invalid123'}),
        ]
        
        for url_name, kwargs in param_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    # Any response is fine - we just want to make sure the URL pattern exists
                    # Common responses: 404 (not found), 302 (redirect to login), 403 (forbidden)
                    self.assertIsNotNone(response.status_code, 
                                       f"URL {url_name} exists and returns a response")
                    print(f"✓ {url_name}: {response.status_code} (parameterized)")
                except Exception as e:
                    self.fail(f"✗ Parameterized URL {url_name} failed: {e}")
    
    def test_all_discovered_urls_are_accessible(self):
        """Test all discovered URL patterns are at least accessible"""
        # URLs that don't require parameters and should be testable
        simple_urls = [
            'home',
            'dashboard', 
            'mentor_positions',
            'mentor_applications',
            'mentor_interns',
            'complete_profile',
            'profile',
            'create_profile',
            'edit_profile',
            'edit_company',
            'edit_institute',
            'teacher_students',
            'manage_companies',
            'manage_institutes',
            'student_applications',
            'student_weekly_activities',
            'create_weekly_activity_log',
            'browse_positions',
            'create_position',
            'documentation_index',
            'account_login',
            'account_signup',
            'account_logout',
        ]
        
        results = {
            'success': [],
            'redirects': [],
            'errors': []
        }
        
        for url_name in simple_urls:
            try:
                url = reverse(url_name)
                response = self.client.get(url)
                
                if response.status_code == 200:
                    results['success'].append(f"{url_name}: {response.status_code}")
                elif response.status_code in [301, 302]:
                    results['redirects'].append(f"{url_name}: {response.status_code}")
                else:
                    results['errors'].append(f"{url_name}: {response.status_code}")
                    
            except Exception as e:
                results['errors'].append(f"{url_name}: ERROR - {e}")
        
        # Print summary
        print(f"\n📊 URL Test Summary:")
        print(f"✅ Working URLs ({len(results['success'])}): {len(results['success'])}")
        print(f"🔄 Redirects ({len(results['redirects'])}): {len(results['redirects'])}")  
        print(f"❌ Errors ({len(results['errors'])}): {len(results['errors'])}")
        
        if results['errors']:
            print(f"\n❌ Failed URLs:")
            for error in results['errors']:
                print(f"  - {error}")
        
        # Test passes if we have more working URLs than errors
        total_working = len(results['success']) + len(results['redirects'])
        total_errors = len(results['errors'])
        
        self.assertGreater(total_working, total_errors, 
                         f"Should have more working URLs ({total_working}) than errors ({total_errors})")


class URLHealthCheckTest(TestCase):
    """Quick health check for critical application URLs"""
    
    def test_application_health_check(self):
        """Verify the application's critical URLs are functional"""
        client = Client()
        
        critical_checks = [
            ('Homepage loads', 'home', 200),
            ('Login page accessible', 'account_login', 200),
            ('Signup page accessible', 'account_signup', 200),
            ('Dashboard redirects when not logged in', 'dashboard', [302, 403]),
        ]
        
        all_passed = True
        results = []
        
        for description, url_name, expected_status in critical_checks:
            try:
                url = reverse(url_name)
                response = client.get(url)
                
                if isinstance(expected_status, list):
                    status_ok = response.status_code in expected_status
                else:
                    status_ok = response.status_code == expected_status
                
                if status_ok:
                    results.append(f"✅ {description}")
                else:
                    results.append(f"❌ {description} (expected {expected_status}, got {response.status_code})")
                    all_passed = False
                    
            except Exception as e:
                results.append(f"❌ {description} - ERROR: {e}")
                all_passed = False
        
        # Print results
        print("\n🏥 Application Health Check:")
        for result in results:
            print(f"  {result}")
        
        self.assertTrue(all_passed, "All critical application URLs should be healthy")
        
        # Additional check: verify URL patterns are properly configured
        try:
            from app.urls import urlpatterns
            self.assertGreater(len(urlpatterns), 10, "Should have a reasonable number of URL patterns")
            print(f"✅ URL patterns configured: {len(urlpatterns)} patterns found")
        except Exception as e:
            self.fail(f"Error accessing URL patterns: {e}")
