"""
Integration test cases for the Tarbiyat internship platform.
Tests complete workflows and end-to-end functionality.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from ..models import (
    StudentProfile, MentorProfile, TeacherProfile, OfficialProfile,
    Institute, Company, InternshipPosition, InternshipApplication,
    Internship, Notification
)


class IntegrationTest(TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        """Set up test data"""
        self.setup_groups()
        self.setup_users()
        self.setup_organizations()
        
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
            first_name='Dr. Alice',
            last_name='Teacher'
        )
        self.teacher_user.groups.add(self.teacher_group)
        
        self.official_user = User.objects.create_user(
            username='official@gov.pk',
            email='official@gov.pk',
            password='testpass123',
            first_name='Bob',
            last_name='Official'
        )
        self.official_user.groups.add(self.official_group)
        
    def setup_organizations(self):
        """Create test organizations"""
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
        
    def test_student_application_workflow(self):
        """Test complete student application workflow"""
        # 1. Create internship position
        position = InternshipPosition.objects.create(
            company=self.company,
            mentor=self.mentor_profile,
            title='Backend Developer Intern',
            description='Work on API development',
            requirements='Python, REST APIs',
            duration='3',
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=104),
            stipend=Decimal('1200.00'),
            max_students=2
        )
        
        # 2. Student creates application
        application = InternshipApplication.objects.create(
            position=position,
            student=self.student_profile,
            cover_letter='I have experience in Python and Django...',
            status='pending'
        )
        
        # 3. Verify application was created correctly
        self.assertEqual(application.position, position)
        self.assertEqual(application.student, self.student_profile)
        self.assertEqual(application.status, 'pending')
        
        # 4. Mentor reviews and approves
        application.status = 'approved'
        application.reviewed_at = timezone.now()
        application.save()
        
        # 5. Verify application status
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        self.assertIsNotNone(application.reviewed_at)
        
    def test_mentor_position_management_workflow(self):
        """Test mentor creating and managing internship positions"""
        # 1. Mentor creates position
        position = InternshipPosition.objects.create(
            company=self.company,
            mentor=self.mentor_profile,
            title='Frontend Developer Intern',
            description='Work on React applications',
            requirements='JavaScript, React, HTML/CSS',
            duration='6',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=210),
            stipend=Decimal('1800.00'),
            max_students=3
        )
        
        # 2. Verify position creation
        self.assertEqual(position.mentor, self.mentor_profile)
        self.assertEqual(position.company, self.company)
        # Check if position has start date in the future
        self.assertIsNotNone(position.start_date)
        if position.start_date:
            self.assertTrue(position.start_date >= date.today())
        
        # 3. Multiple students apply
        student2 = User.objects.create_user(
            username='student2@university.edu',
            email='student2@university.edu',
            password='testpass123'
        )
        student2.groups.add(self.student_group)
        
        student2_profile = StudentProfile.objects.create(
            user=student2,
            institute=self.institute,
            student_id='STU002',
            year_of_study='2',
            major='Computer Science',
            gpa=Decimal('3.8'),
            expected_graduation=date.today() + timedelta(days=730)
        )
        
        # Applications from both students
        app1 = InternshipApplication.objects.create(
            position=position,
            student=self.student_profile,
            cover_letter='Application 1',
            status='pending'
        )
        
        app2 = InternshipApplication.objects.create(
            position=position,
            student=student2_profile,
            cover_letter='Application 2',
            status='pending'
        )
        
        # 4. Mentor can see all applications
        applications = InternshipApplication.objects.filter(position=position)
        self.assertEqual(applications.count(), 2)
        
        # 5. Mentor approves one, rejects another
        app1.status = 'approved'
        app1.save()
        
        app2.status = 'rejected'
        app2.save()
        
        # Verify status changes
        self.assertEqual(
            InternshipApplication.objects.filter(
                position=position, status='approved'
            ).count(), 
            1
        )
        self.assertEqual(
            InternshipApplication.objects.filter(
                position=position, status='rejected'
            ).count(), 
            1
        )
        
    def test_organization_domain_verification_workflow(self):
        """Test organization domain verification workflow"""
        # 1. Create user with company domain email
        company_user = User.objects.create_user(
            username='employee@company.com',
            email='employee@company.com',
            password='testpass123'
        )
        company_user.groups.add(self.mentor_group)
        
        # 2. User should be able to join approved company
        # This would normally be tested through the view, but we can test the logic
        from ..utils import validate_user_organization_membership
        
        # Should return True for matching domain
        self.assertTrue(
            validate_user_organization_membership(
                company_user, 
                'company',
                self.company.nanoid
            )
        )
        
        # 3. User with different domain should not be able to join
        other_user = User.objects.create_user(
            username='outsider@otherdomain.com',
            email='outsider@otherdomain.com',
            password='testpass123'
        )
        
        # Should return False for non-matching domain
        self.assertFalse(
            validate_user_organization_membership(
                other_user, 
                'company',
                self.company.nanoid
            )
        )
        
    def test_notification_system_workflow(self):
        """Test notification system workflow"""
        # 1. Create internship position
        position = InternshipPosition.objects.create(
            company=self.company,
            mentor=self.mentor_profile,
            title='DevOps Intern',
            description='Work on deployment pipelines',
            requirements='Docker, CI/CD',
            duration='4',
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=127),
            stipend=Decimal('1600.00'),
            max_students=1
        )
        
        # 2. Student applies
        application = InternshipApplication.objects.create(
            position=position,
            student=self.student_profile,
            cover_letter='I have Docker experience...',
            status='pending'
        )
        
        # 3. Create notification for mentor about new application
        notification = Notification.objects.create(
            recipient=self.mentor_user,
            title='New Internship Application',
            message=f'Student {self.student_profile.user.get_full_name()} applied for {position.title}',
            is_read=False
        )
        
        # 4. Verify notification
        self.assertEqual(notification.recipient, self.mentor_user)
        self.assertFalse(notification.is_read)
        
        # 5. Mark notification as read
        notification.is_read = True
        notification.save()
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        
    def test_multi_role_user_workflow(self):
        """Test workflow where user might have multiple roles"""
        # Create a user who is both teacher and official
        multi_role_user = User.objects.create_user(
            username='multirole@university.edu',
            email='multirole@university.edu',
            password='testpass123'
        )
        multi_role_user.groups.add(self.teacher_group)
        multi_role_user.groups.add(self.official_group)
        
        # Create profiles for both roles
        teacher_profile = TeacherProfile.objects.create(
            user=multi_role_user,
            institute=self.institute,
            department='Computer Science',
            position='Professor'
        )
        
        official_profile = OfficialProfile.objects.create(
            user=multi_role_user,
            department='Education Ministry',
            position='Academic Director'
        )
        
        # Test that user has both profiles
        self.assertTrue(hasattr(multi_role_user, 'teacherprofile'))
        self.assertTrue(hasattr(multi_role_user, 'officialprofile'))
        
        # Test role-based functionality
        self.assertTrue(multi_role_user.groups.filter(name='teacher').exists())
        self.assertTrue(multi_role_user.groups.filter(name='official').exists())
