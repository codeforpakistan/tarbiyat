from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from decouple import config
from app.models import (
    Institute, Company, StudentProfile, MentorProfile, 
    TeacherProfile, OfficialProfile, InternshipPosition,
    InternshipApplication, Internship, ProgressReport, Notification
)
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with initial data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))
        
        with transaction.atomic():
            # Create admin user
            self.create_admin_user()
            
            # Create Google social app
            self.create_google_social_app()
            
            # Create institutes
            institutes = self.create_institutes()
            
            # Create companies
            companies = self.create_companies()
            
            # Create users and profiles
            students = self.create_students(institutes)
            mentors = self.create_mentors(companies)
            teachers = self.create_teachers(institutes)
            officials = self.create_officials()
            
            # Create internship positions
            positions = self.create_internship_positions(companies, mentors)
            
            # Create sample applications and internships
            self.create_sample_applications_and_internships(students, positions, mentors, teachers)

        self.stdout.write(
            self.style.SUCCESS('Database seeding completed successfully!')
        )

    def clear_data(self):
        """Clear existing data"""
        models_to_clear = [
            ProgressReport, Internship, InternshipApplication, 
            InternshipPosition, StudentProfile, MentorProfile, 
            TeacherProfile, OfficialProfile, Company, Institute,
            Notification
        ]
        
        for model in models_to_clear:
            model.objects.all().delete()
        
        # Clear users except superusers
        User.objects.filter(is_superuser=False).delete()
        
        # Clear social apps
        SocialApp.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS('Existing data cleared')
        )

    def create_admin_user(self):
        """Create admin user if it doesn't exist"""
        from allauth.account.models import EmailAddress
        
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@tarbiyat.gov',
                password='admin123',
                first_name='System',
                last_name='Administrator'
            )
            
            # Mark admin email as verified
            EmailAddress.objects.create(
                user=admin,
                email='admin@tarbiyat.gov',
                verified=True,
                primary=True
            )
            
            # Don't add admin to any group - admins are superusers, not officials
            
            # Create OfficialProfile for admin is not needed - admins use Django admin
            
            self.stdout.write(
                self.style.SUCCESS('Admin user created: admin/admin123')
            )
        else:
            # Ensure existing admin user's email is verified
            admin = User.objects.get(username='admin')
            email_address, created = EmailAddress.objects.get_or_create(
                user=admin,
                email=admin.email,
                defaults={'verified': True, 'primary': True}
            )
            if not email_address.verified:
                email_address.verified = True
                email_address.save()
                self.stdout.write(
                    self.style.SUCCESS('Admin email marked as verified')
                )

    def create_google_social_app(self):
        """Create Google OAuth2 social app if it doesn't exist"""
        google_client_id = config('GOOGLE_OAUTH2_CLIENT_ID', default='')
        google_client_secret = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='')
        
        if not google_client_id or not google_client_secret:
            self.stdout.write(
                self.style.WARNING('Google OAuth2 credentials not found in .env file. Skipping social app creation.')
            )
            return
            
        # Check if Google social app already exists
        if SocialApp.objects.filter(provider='google').exists():
            self.stdout.write(
                self.style.WARNING('Google social app already exists')
            )
            return
            
        # Get or create the default site
        site = Site.objects.get_current()
        
        # Create Google social app
        google_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id=google_client_id,
            secret=google_client_secret,
        )
        
        # Add the site to the social app
        google_app.sites.add(site)
        
        self.stdout.write(
            self.style.SUCCESS('Google OAuth2 social app created successfully')
        )

    def create_institutes(self):
        """Create sample institutes"""
        institutes_data = [
            {
                'name': 'Institute of Technology',
                'address': '123 Tech Street, Capital City',
                'website': 'https://itech.edu',
                'contact_email': 'info@itech.edu'
            },
            {
                'name': 'State Institute',
                'address': '456 Academic Ave, Institute Town',
                'website': 'https://stateinst.edu',
                'contact_email': 'contact@stateuni.edu'
            },
            {
                'name': 'Metropolitan College',
                'address': '789 College Blvd, Metro City',
                'website': 'https://metrocollege.edu',
                'contact_email': 'admin@metrocollege.edu'
            }
        ]
        
        institutes = []
        for inst_data in institutes_data:
            institute, created = Institute.objects.get_or_create(
                name=inst_data['name'],
                defaults=inst_data
            )
            institutes.append(institute)
            if created:
                self.stdout.write(f'Created institute: {institute.name}')
        
        return institutes

    def create_companies(self):
        """Create sample companies"""
        companies_data = [
            {
                'name': 'TechCorp Solutions',
                'description': 'Leading software development company specializing in web and mobile applications.',
                'industry': 'Information Technology',
                'address': '100 Silicon Valley, Tech District',
                'website': 'https://techcorp.com',
                'contact_email': 'hr@techcorp.com',
                'phone': '+1-555-0101',
                'is_verified': True
            },
            {
                'name': 'Digital Marketing Agency',
                'description': 'Full-service digital marketing and advertising agency.',
                'industry': 'Marketing',
                'address': '200 Marketing Street, Business District',
                'website': 'https://digitalmarketing.com',
                'contact_email': 'careers@digitalmarketing.com',
                'phone': '+1-555-0102',
                'is_verified': True
            },
            {
                'name': 'Green Energy Systems',
                'description': 'Renewable energy solutions and sustainable technology.',
                'industry': 'Energy',
                'address': '300 Green Avenue, Eco City',
                'website': 'https://greenenergy.com',
                'contact_email': 'jobs@greenenergy.com',
                'phone': '+1-555-0103',
                'is_verified': True
            },
            {
                'name': 'Financial Services Group',
                'description': 'Comprehensive financial planning and investment services.',
                'industry': 'Finance',
                'address': '400 Wall Street, Financial District',
                'website': 'https://finservices.com',
                'contact_email': 'internships@finservices.com',
                'phone': '+1-555-0104',
                'is_verified': True
            },
            {
                'name': 'Healthcare Innovation Lab',
                'description': 'Medical research and healthcare technology development.',
                'industry': 'Healthcare',
                'address': '500 Medical Center Drive, Health City',
                'website': 'https://healthinnovation.com',
                'contact_email': 'research@healthinnovation.com',
                'phone': '+1-555-0105',
                'is_verified': True
            }
        ]
        
        companies = []
        for comp_data in companies_data:
            company, created = Company.objects.get_or_create(
                name=comp_data['name'],
                defaults=comp_data
            )
            companies.append(company)
            if created:
                self.stdout.write(f'Created company: {company.name}')
        
        return companies

    def create_students(self, institutes):
        """Create sample students"""
        students_data = [
            ('john_doe', 'John', 'Doe', 'john.doe@student.edu', 'Computer Science'),
            ('jane_smith', 'Jane', 'Smith', 'jane.smith@student.edu', 'Information Technology'),
            ('mike_johnson', 'Mike', 'Johnson', 'mike.johnson@student.edu', 'Business Administration'),
            ('sarah_wilson', 'Sarah', 'Wilson', 'sarah.wilson@student.edu', 'Marketing'),
            ('david_brown', 'David', 'Brown', 'david.brown@student.edu', 'Engineering'),
            ('emily_davis', 'Emily', 'Davis', 'emily.davis@student.edu', 'Psychology'),
            ('chris_taylor', 'Chris', 'Taylor', 'chris.taylor@student.edu', 'Finance'),
            ('lisa_anderson', 'Lisa', 'Anderson', 'lisa.anderson@student.edu', 'Graphic Design'),
            ('tom_martinez', 'Tom', 'Martinez', 'tom.martinez@student.edu', 'Environmental Science'),
            ('anna_garcia', 'Anna', 'Garcia', 'anna.garcia@student.edu', 'Data Science')
        ]
        
        students = []
        student_group, created = Group.objects.get_or_create(name='student')
        
        for i, (username, first_name, last_name, email, major) in enumerate(students_data):
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='student123',
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Add user to student group
                user.groups.add(student_group)
                
                student_profile = StudentProfile.objects.create(
                    user=user,
                    institute=random.choice(institutes),
                    student_id=f'STU{2024000 + i + 1}',
                    year_of_study=random.choice(['3', '4']),
                    major=major,
                    gpa=round(random.uniform(2.5, 4.0), 2),
                    skills=f'Python, JavaScript, Problem Solving, Communication, {major}-related skills',
                    expected_graduation=date(2025, random.randint(5, 12), random.randint(1, 28)),
                )
                students.append(student_profile)
                self.stdout.write(f'Created student: {user.username}')
        
        return students

    def create_mentors(self, companies):
        """Create sample mentors"""
        mentors_data = [
            ('alex_mentor', 'Alex', 'Thompson', 'alex.thompson@techcorp.com', 'Senior Developer', 'Development'),
            ('susan_lead', 'Susan', 'Rodriguez', 'susan.rodriguez@digitalmarketing.com', 'Marketing Manager', 'Marketing'),
            ('robert_senior', 'Robert', 'Chen', 'robert.chen@greenenergy.com', 'Engineering Lead', 'Engineering'),
            ('maria_director', 'Maria', 'Lopez', 'maria.lopez@finservices.com', 'Finance Director', 'Finance'),
            ('james_head', 'James', 'Kim', 'james.kim@healthinnovation.com', 'Research Head', 'Research')
        ]
        
        mentors = []
        mentor_group, created = Group.objects.get_or_create(name='mentor')
        
        for i, (username, first_name, last_name, email, position, department) in enumerate(mentors_data):
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='mentor123',
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Add user to mentor group
                user.groups.add(mentor_group)
                
                mentor_profile = MentorProfile.objects.create(
                    user=user,
                    company=companies[i % len(companies)],
                    position=position,
                    department=department,
                    experience_years=random.randint(5, 15),
                    specialization=f'{department} and Team Leadership',
                    is_verified=True
                )
                mentors.append(mentor_profile)
                self.stdout.write(f'Created mentor: {user.username}')
        
        return mentors

    def create_teachers(self, institutes):
        """Create sample teachers"""
        teachers_data = [
            ('prof_anderson', 'Dr. Michael', 'Anderson', 'michael.anderson@utech.edu', 'Professor', 'Computer Science'),
            ('prof_clark', 'Dr. Jennifer', 'Clark', 'jennifer.clark@stateuni.edu', 'Associate Professor', 'Business'),
            ('prof_white', 'Dr. Steven', 'White', 'steven.white@metrocollege.edu', 'Professor', 'Engineering')
        ]
        
        teachers = []
        teacher_group, created = Group.objects.get_or_create(name='teacher')
        
        for i, (username, first_name, last_name, email, title, department) in enumerate(teachers_data):
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='teacher123',
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Add user to teacher group
                user.groups.add(teacher_group)
                
                teacher_profile = TeacherProfile.objects.create(
                    user=user,
                    institute=institutes[i % len(institutes)],
                    department=department,
                    title=title,
                    employee_id=f'TEACH{1000 + i + 1}'
                )
                teachers.append(teacher_profile)
                self.stdout.write(f'Created teacher: {user.username}')
        
        return teachers

    def create_officials(self):
        """Create sample officials"""
        officials_data = [
            ('official_john', 'John', 'Official', 'john.official@gov.edu', 'Education Department', 'Program Coordinator'),
            ('official_mary', 'Mary', 'Supervisor', 'mary.supervisor@gov.edu', 'Labor Department', 'Internship Supervisor')
        ]
        
        officials = []
        official_group, created = Group.objects.get_or_create(name='official')
        
        for i, (username, first_name, last_name, email, department, position) in enumerate(officials_data):
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='official123',
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Add user to official group
                user.groups.add(official_group)
                
                official_profile = OfficialProfile.objects.create(
                    user=user,
                    department=department,
                    position=position,
                    employee_id=f'OFF{2000 + i + 1}'
                )
                officials.append(official_profile)
                self.stdout.write(f'Created official: {user.username}')
        
        return officials

    def create_internship_positions(self, companies, mentors):
        """Create sample internship positions"""
        positions_data = [
            {
                'title': 'Software Development Intern',
                'description': 'Join our development team to work on exciting web applications using modern technologies.',
                'requirements': 'Currently enrolled in Computer Science or related field. Basic knowledge of programming.',
                'skills_required': 'Python, JavaScript, HTML/CSS, Git, Problem-solving skills',
                'duration': '3',
                'max_students': 2,
                'stipend': 1500.00
            },
            {
                'title': 'Digital Marketing Intern',
                'description': 'Learn digital marketing strategies, social media management, and campaign optimization.',
                'requirements': 'Marketing, Business, or Communications major. Creative thinking and analytical skills.',
                'skills_required': 'Social Media, Content Creation, Analytics, Communication, Creativity',
                'duration': '2',
                'max_students': 1,
                'stipend': 1200.00
            },
            {
                'title': 'Engineering Research Intern',
                'description': 'Participate in renewable energy research projects and sustainable technology development.',
                'requirements': 'Engineering student with interest in sustainable technology.',
                'skills_required': 'CAD Software, Research Methods, Data Analysis, Technical Writing',
                'duration': '4',
                'max_students': 1,
                'stipend': 1800.00
            },
            {
                'title': 'Finance Analyst Intern',
                'description': 'Support financial analysis, reporting, and investment research activities.',
                'requirements': 'Finance, Economics, or Accounting major. Strong analytical skills.',
                'skills_required': 'Excel, Financial Modeling, Data Analysis, Attention to Detail',
                'duration': '3',
                'max_students': 1,
                'stipend': 1600.00
            },
            {
                'title': 'Healthcare Technology Intern',
                'description': 'Work on healthcare innovation projects and medical technology development.',
                'requirements': 'Computer Science, Biomedical Engineering, or related field.',
                'skills_required': 'Programming, Data Analysis, Healthcare Knowledge, Research Skills',
                'duration': '6',
                'max_students': 1,
                'stipend': 2000.00
            }
        ]
        
        positions = []
        for i, pos_data in enumerate(positions_data):
            if i < len(mentors):
                start_date = date.today() + timedelta(days=random.randint(30, 90))
                end_date = start_date + timedelta(days=int(pos_data['duration']) * 30)
                
                position = InternshipPosition.objects.create(
                    company=mentors[i].company,
                    mentor=mentors[i],
                    title=pos_data['title'],
                    description=pos_data['description'],
                    requirements=pos_data['requirements'],
                    skills_required=pos_data['skills_required'],
                    duration=pos_data['duration'],
                    start_date=start_date,
                    end_date=end_date,
                    stipend=pos_data['stipend'],
                    max_students=pos_data['max_students'],
                    is_active=True
                )
                positions.append(position)
                self.stdout.write(f'Created position: {position.title}')
        
        return positions
        
    def create_sample_applications_and_internships(self, students, positions, mentors, teachers):
        """Create sample applications and internships for demonstration"""
        # Create some applications
        for i, student in enumerate(students[:8]):  # First 8 students apply
            if i < len(positions):
                position = positions[i % len(positions)]
                
                # Create application
                application = InternshipApplication.objects.create(
                    student=student,
                    position=position,
                    cover_letter=f"Dear Hiring Manager,\n\nI am very interested in the {position.title} position at {position.company.name}. As a {student.major} student with a GPA of {student.gpa}, I believe I would be a great fit for this role.\n\nMy skills in {student.skills[:50]}... align well with your requirements. I am eager to contribute to your team and learn from experienced professionals.\n\nThank you for considering my application.\n\nBest regards,\n{student.user.get_full_name()}",
                    status=random.choice(['pending', 'under_review', 'approved', 'rejected'])
                )
                self.stdout.write(f'Created application: {student.user.username} -> {position.title}')
                
                # Create internship for approved applications
                if application.status == 'approved' and i < 3:  # First 3 approved become internships
                    internship = Internship.objects.create(
                        application=application,
                        student=student,
                        mentor=position.mentor,
                        teacher=random.choice(teachers) if teachers else None,
                        start_date=position.start_date,
                        end_date=position.end_date,
                        status=random.choice(['active', 'completed']),
                        final_grade=random.choice(['A', 'B+', 'B', 'C+']) if random.choice([True, False]) else '',
                        certificate_issued=random.choice([True, False])
                    )
                    self.stdout.write(f'Created internship: {student.user.username} at {position.company.name}')
                    
                    # Create progress reports for active/completed internships
                    self.create_sample_progress_reports(internship)
                    
                    # Create notifications
                    Notification.objects.create(
                        recipient=student.user,
                        notification_type='application_status',
                        title=f'Application Approved - {position.title}',
                        message=f'Congratulations! Your application for {position.title} at {position.company.name} has been approved. Your internship starts on {position.start_date}.'
                    )
                    
                elif application.status == 'rejected':
                    Notification.objects.create(
                        recipient=student.user,
                        notification_type='application_status',
                        title=f'Application Update - {position.title}',
                        message=f'Thank you for your interest in {position.title} at {position.company.name}. Unfortunately, we have decided to move forward with other candidates.'
                    )

    def create_sample_progress_reports(self, internship):
        """Create sample progress reports for an internship"""
        if internship.status in ['active', 'completed']:
            weeks_to_create = 3 if internship.status == 'active' else 6
            
            for week in range(1, weeks_to_create + 1):
                # Student report
                ProgressReport.objects.create(
                    internship=internship,
                    report_type='student',
                    reporter=internship.student.user,
                    week_number=week,
                    tasks_completed=f"Week {week}: Completed assigned tasks including research, documentation, and hands-on work. Participated in team meetings and training sessions.",
                    learning_outcomes=f"Gained experience in {internship.student.major}-related skills. Improved communication and teamwork abilities.",
                    challenges_faced="Initial learning curve with new technologies and processes. Time management across multiple tasks.",
                    satisfaction_rating=random.randint(4, 5)
                )
                
                # Mentor report
                ProgressReport.objects.create(
                    internship=internship,
                    report_type='mentor',
                    reporter=internship.mentor.user,
                    week_number=week,
                    student_performance=f"Student showed good progress in week {week}. Demonstrates strong work ethic and willingness to learn.",
                    skills_demonstrated=f"Technical skills, problem-solving, communication, teamwork",
                    areas_for_improvement="Could improve time management and ask more questions when unclear.",
                    attendance_rating=random.randint(4, 5)
                )
                
                # Teacher report (if teacher assigned)
                if internship.teacher:
                    ProgressReport.objects.create(
                        internship=internship,
                        report_type='teacher',
                        reporter=internship.teacher.user,
                        week_number=week,
                        discussion_notes=f"Met with student to discuss week {week} progress. Student is adapting well to professional environment.",
                        academic_alignment="Internship tasks align well with academic curriculum and learning objectives.",
                        recommendations="Continue current trajectory. Encourage student to document learning experiences."
                    )
            
            self.stdout.write(f'Created {weeks_to_create} weeks of progress reports for {internship.student.user.username}')
