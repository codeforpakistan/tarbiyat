"""
Simple URL Status Tests for Tarbiyat Platform

Tests basic URL patterns to ensure they return appropriate HTTP status codes.
This is a simplified version focusing on essential URL testing.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model

User = get_user_model()


class BasicURLStatusTestCase(TestCase):
    """Test basic URLs return appropriate HTTP status codes"""
    
    def setUp(self):
        """Set up minimal test data"""
        self.client = Client()
        
        # Create groups
        Group.objects.get_or_create(name='student')
        Group.objects.get_or_create(name='mentor')
        Group.objects.get_or_create(name='teacher')
        Group.objects.get_or_create(name='official')
    
    def test_public_urls_status(self):
        """Test public URLs return 200 or appropriate redirect"""
        public_urls = [
            'home',
            'about',
            'documentation_index',
            'contact',
            'privacy_policy',
            'terms_of_service',
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
        """Test authentication URLs return appropriate status"""
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
            'dashboard',  # All roles use the same dashboard URL
        ]
        
        for url_name in protected_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name)
                    response = self.client.get(url)
                    # Should redirect to login (302) or return 403
                    self.assertIn(response.status_code, [302, 403], 
                                f"Protected URL {url_name} ({url}) should redirect/deny access, got {response.status_code}")
                    print(f"✓ {url_name}: {response.status_code} (protected)")
                except Exception as e:
                    self.fail(f"✗ Protected URL {url_name} failed: {e}")
    
    def test_urls_with_parameters_exist(self):
        """Test that parameterized URLs exist (even if they return 404 without valid params)"""
        param_urls = [
            ('position_detail', {'position_nanoid': 'test123'}),
            ('application_detail', {'application_nanoid': 'test123'}),
            ('mentor_progress_reports', {'internship_nanoid': 'test123'}),
        ]
        
        for url_name, kwargs in param_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    # Any response is fine - we just want to make sure the URL pattern exists
                    self.assertIsNotNone(response.status_code, 
                                       f"URL {url_name} exists and returns a response")
                    print(f"✓ {url_name}: {response.status_code} (parameterized)")
                except Exception as e:
                    self.fail(f"✗ Parameterized URL {url_name} failed: {e}")
    
    def test_all_named_urls_reversible(self):
        """Test that all named URL patterns can be reversed"""
        from app.urls import urlpatterns
        
        reversible_urls = []
        failed_urls = []
        
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name:
                try:
                    # Try to reverse without parameters first
                    reverse(pattern.name)
                    reversible_urls.append(pattern.name)
                except Exception as e:
                    # If it fails, it might need parameters
                    if 'arguments' in str(e).lower():
                        # URL needs parameters, but pattern is valid
                        reversible_urls.append(f"{pattern.name} (needs params)")
                    else:
                        failed_urls.append(f"{pattern.name}: {e}")
        
        print(f"\n✓ Reversible URLs ({len(reversible_urls)}):")
        for url in reversible_urls:
            print(f"  - {url}")
        
        if failed_urls:
            print(f"\n✗ Failed URLs ({len(failed_urls)}):")
            for url in failed_urls:
                print(f"  - {url}")
            self.fail(f"{len(failed_urls)} URL patterns failed reverse lookup")
        
        self.assertGreater(len(reversible_urls), 0, "Should have at least some reversible URLs")


class QuickURLSmokeTest(TestCase):
    """Quick smoke test for critical URLs"""
    
    def test_critical_urls_respond(self):
        """Test that critical application URLs respond"""
        client = Client()
        
        critical_urls = {
            'home': 'Homepage',
            'account_login': 'Login page',
            'account_signup': 'Signup page',
            'about': 'About page',
        }
        
        all_passed = True
        results = []
        
        for url_name, description in critical_urls.items():
            try:
                url = reverse(url_name)
                response = client.get(url)
                status = response.status_code
                
                if status in [200, 301, 302]:
                    results.append(f"✓ {description} ({url_name}): {status}")
                else:
                    results.append(f"✗ {description} ({url_name}): {status}")
                    all_passed = False
                    
            except Exception as e:
                results.append(f"✗ {description} ({url_name}): ERROR - {e}")
                all_passed = False
        
        # Print results
        print("\nURL Smoke Test Results:")
        for result in results:
            print(f"  {result}")
        
        self.assertTrue(all_passed, "All critical URLs should respond with appropriate status codes")
