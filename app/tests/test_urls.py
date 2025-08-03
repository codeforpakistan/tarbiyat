"""
URL Status Tests for Tarbiyat Platform

Tests all URL patterns to ensure they return appropriate HTTP status codes.
This helps catch broken URLs, template errors, and missing views.
"""

from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from app.models import (
    StudentProfile, MentorProfile, TeacherProfile, OfficialProfile,
    Company, Institute, InternshipPosition, InternshipApplication, Internship,
    InternshipSupervisorEvaluation, ProgressReport
)
from nanoid import generate
import tempfile
import os

User = get_user_model()


class URLStatusTestCase(TestCase):
    """Test all URLs return appropriate HTTP status codes"""
    
    def setUp(self):
        """Set up test data for URL testing"""
        # Create groups
        self.student_group, _ = Group.objects.get_or_create(name='student')
        self.mentor_group, _ = Group.objects.get_or_create(name='mentor')
        self.teacher_group, _ = Group.objects.get_or_create(name='teacher')
        self.official_group, _ = Group.objects.get_or_create(name='official')
        
        # Create test users
        self.student_user = User.objects.create_user(
            username='teststudent@example.com',
            email='teststudent@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Student'
        )
        self.student_user.groups.add(self.student_group)
        
        self.mentor_user = User.objects.create_user(
            username='testmentor@example.com',
            email='testmentor@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Mentor'
        )
        self.mentor_user.groups.add(self.mentor_group)
        
        self.teacher_user = User.objects.create_user(
            username='testteacher@example.com',
            email='testteacher@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Teacher'
        )
        self.teacher_user.groups.add(self.teacher_group)
        
        self.official_user = User.objects.create_user(
            username='testofficial@example.com',
            email='testofficial@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Official'
        )
        self.official_user.groups.add(self.official_group)
        
        # Create test institute and company
        self.institute = Institute.objects.create(
            name='Test University',
            email_domain='testuni.edu',
            registration_status='approved'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            email_domain='testcompany.com',
            industry='Technology',
            registration_status='approved'
        )
        
        # Create test profiles
        # Create a temporary PDF file for resume
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        self.temp_file.write(b'%PDF-1.4 test content')
        self.temp_file.close()
        
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id='STU001',
            institute=self.institute,
            major='Computer Science',
            gpa=3.8,
            expected_graduation='2024-06-15',
            resume=SimpleUploadedFile('test_resume.pdf', b'test content', content_type='application/pdf')
        )
        
        self.mentor_profile = MentorProfile.objects.create(
            user=self.mentor_user,
            company=self.company,
            position='Senior Developer',
            can_edit_company=True
        )
        
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            institute=self.institute,
            department='Computer Science',
            employee_id='TEACH001'
        )
        
        self.official_profile = OfficialProfile.objects.create(
            user=self.official_user,
            organization_type='government',
            department='Education Ministry',
            employee_id='OFF001'
        )
        
        # Create test position
        self.position = InternshipPosition.objects.create(
            nanoid=generate(size=12),
            title='Software Developer Intern',
            company=self.company,
            mentor=self.mentor_profile,
            description='Test internship position',
            requirements='Python, Django',
            duration='3',
            stipend=25000.00,
            is_active=True
        )
        
        # Create test application
        self.application = InternshipApplication.objects.create(
            nanoid=generate(size=10),
            student=self.student_profile,
            position=self.position,
            status='pending'
        )
        
        # Create test internship
        self.internship = Internship.objects.create(
            nanoid=generate(size=10),
            student=self.student_profile,
            mentor=self.mentor_profile,
            position=self.position,
            start_date='2024-01-15',
            end_date='2024-04-15',
            status='active'
        )
        
        # Create test evaluations
        self.supervisor_eval = InternshipSupervisorEvaluation.objects.create(
            nanoid=generate(size=10),
            internship=self.internship,
            evaluator=self.mentor_profile,
            week_number=1,
            student_performance='Excellent work'
        )
        
        self.progress_report = ProgressReport.objects.create(
            nanoid=generate(size=10),
            internship=self.internship,
            created_by=self.mentor_profile.user,
            week_number=1,
            content='Good progress this week'
        )
        
        self.client = Client()
    
    def tearDown(self):
        """Clean up test files"""
        try:
            os.unlink(self.temp_file.name)
        except OSError:
            pass
    
    def test_public_urls(self):
        """Test public URLs that don't require authentication"""
        public_urls = [
            ('home', {}),
            ('about', {}),
            ('documentation_index', {}),
            ('contact', {}),
            ('privacy_policy', {}),
            ('terms_of_service', {}),
        ]
        
        for url_name, kwargs in public_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, [200, 302], 
                                f"URL {url_name} returned status {response.status_code}")
                except Exception as e:
                    self.fail(f"URL {url_name} failed with error: {e}")
    
    def test_auth_urls(self):
        """Test authentication URLs"""
        auth_urls = [
            ('account_login', {}),
            ('account_signup', {}),
            ('account_logout', {}),
        ]
        
        for url_name, kwargs in auth_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, [200, 302], 
                                f"URL {url_name} returned status {response.status_code}")
                except Exception as e:
                    self.fail(f"URL {url_name} failed with error: {e}")
    
    def test_student_urls(self):
        """Test student-specific URLs"""
        self.client.login(username='teststudent@example.com', password='testpass123')
        
        student_urls = [
            ('student_dashboard', {}),
            ('browse_positions', {}),
            ('position_detail', {'position_nanoid': self.position.nanoid}),
            ('student_applications', {}),
            ('edit_profile', {}),
        ]
        
        for url_name, kwargs in student_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, [200, 302], 
                                f"URL {url_name} returned status {response.status_code}")
                except Exception as e:
                    self.fail(f"URL {url_name} failed with error: {e}")
    
    def test_mentor_urls(self):
        """Test mentor-specific URLs"""
        self.client.login(username='testmentor@example.com', password='testpass123')
        
        mentor_urls = [
            ('mentor_dashboard', {}),
            ('mentor_positions', {}),
            ('create_position', {}),
            ('mentor_applications', {}),
            ('mentor_interns', {}),
            ('application_detail', {'application_nanoid': self.application.nanoid}),
            ('edit_mentor_profile', {}),
            ('edit_company', {}),
            ('mentor_progress_reports', {'internship_nanoid': self.internship.nanoid}),
            ('create_progress_report', {'internship_nanoid': self.internship.nanoid}),
            ('edit_progress_report', {'report_nanoid': self.progress_report.nanoid}),
        ]
        
        for url_name, kwargs in mentor_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, [200, 302], 
                                f"URL {url_name} returned status {response.status_code}")
                except Exception as e:
                    self.fail(f"URL {url_name} failed with error: {e}")
    
    def test_teacher_urls(self):
        """Test teacher-specific URLs"""
        self.client.login(username='testteacher@example.com', password='testpass123')
        
        teacher_urls = [
            ('teacher_dashboard', {}),
            ('edit_teacher_profile', {}),
        ]
        
        for url_name, kwargs in teacher_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, [200, 302], 
                                f"URL {url_name} returned status {response.status_code}")
                except Exception as e:
                    self.fail(f"URL {url_name} failed with error: {e}")
    
    def test_official_urls(self):
        """Test official-specific URLs"""
        self.client.login(username='testofficial@example.com', password='testpass123')
        
        official_urls = [
            ('official_dashboard', {}),
            ('edit_official_profile', {}),
        ]
        
        for url_name, kwargs in official_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, [200, 302], 
                                f"URL {url_name} returned status {response.status_code}")
                except Exception as e:
                    self.fail(f"URL {url_name} failed with error: {e}")
    
    def test_protected_urls_redirect_when_not_authenticated(self):
        """Test that protected URLs redirect to login when not authenticated"""
        # Ensure client is not logged in
        self.client.logout()
        
        protected_urls = [
            ('student_dashboard', {}),
            ('mentor_dashboard', {}),
            ('teacher_dashboard', {}),
            ('official_dashboard', {}),
            ('edit_profile', {}),
        ]
        
        for url_name, kwargs in protected_urls:
            with self.subTest(url_name=url_name):
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    response = self.client.get(url)
                    # Should redirect to login
                    self.assertEqual(response.status_code, 302,
                                   f"Protected URL {url_name} should redirect when not authenticated")
                except Exception as e:
                    self.fail(f"URL {url_name} failed with error: {e}")
    
    def test_role_based_access_control(self):
        """Test that users can only access URLs for their role"""
        # Test student trying to access mentor URLs
        self.client.login(username='teststudent@example.com', password='testpass123')
        
        response = self.client.get(reverse('mentor_dashboard'))
        self.assertIn(response.status_code, [302, 403], 
                     "Student should not be able to access mentor dashboard")
        
        # Test mentor trying to access official URLs
        self.client.login(username='testmentor@example.com', password='testpass123')
        
        response = self.client.get(reverse('official_dashboard'))
        self.assertIn(response.status_code, [302, 403], 
                     "Mentor should not be able to access official dashboard")
    
    def test_all_url_patterns_have_names(self):
        """Test that all URL patterns have names for reverse lookup"""
        from app.urls import urlpatterns
        
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name:
                with self.subTest(url_name=pattern.name):
                    try:
                        # Try to reverse the URL to ensure it's properly configured
                        reverse(pattern.name)
                    except Exception as e:
                        # Some URLs might need parameters, that's okay
                        if 'arguments' not in str(e).lower():
                            self.fail(f"URL pattern {pattern.name} failed reverse lookup: {e}")


class URLPerformanceTestCase(TestCase):
    """Test URL response times for performance monitoring"""
    
    def setUp(self):
        """Set up minimal test data for performance testing"""
        self.client = Client()
        
    def test_public_url_performance(self):
        """Test that public URLs respond within reasonable time"""
        import time
        
        public_urls = [
            reverse('home'),
            reverse('about'),
            reverse('contact'),
        ]
        
        for url in public_urls:
            with self.subTest(url=url):
                start_time = time.time()
                response = self.client.get(url)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Response should be successful
                self.assertIn(response.status_code, [200, 302])
                
                # Response should be under 2 seconds (adjust as needed)
                self.assertLess(response_time, 2.0, 
                              f"URL {url} took {response_time:.2f} seconds to respond")
