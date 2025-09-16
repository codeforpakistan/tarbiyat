from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from decouple import config
from app.models import (
    Institute, Company, Student, Mentor, 
    Teacher, Official, Position,
    Application, Internship, Report, Notification
)
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = '''Seed the database with initial data for testing in stages:
    Stage 1: Admin user and basic setup
    Stage 2: Organizations and users (includes Stage 1)
    Stage 3: Internships and applications (includes Stages 1 & 2)'''

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--stage',
            type=int,
            choices=[1, 2, 3],
            help='Seeding stage: 1=admin only, 2=users and organizations, 3=internships and applications',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all stages (equivalent to --stage 3)',
        )
        parser.add_argument(
            '--only',
            action='store_true',
            help='Run only the specified stage (requires prerequisites to exist)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        stage = options.get('stage')
        run_all = options.get('all')
        only_stage = options.get('only')
        
        # If no stage specified and --all not used, show help
        if stage is None and not run_all:
            self.stdout.write(
                self.style.WARNING('No stage specified. Use --stage 1|2|3 or --all. Run with --help for details.')
            )
            self.stdout.write('')
            self.stdout.write('Seeding stages:')
            self.stdout.write('  Stage 1: Admin user and basic setup')
            self.stdout.write('  Stage 2: Organizations and users (includes Stage 1)')
            self.stdout.write('  Stage 3: Internships and applications (includes Stages 1 & 2)')
            self.stdout.write('')
            self.stdout.write('Examples:')
            self.stdout.write('  env\\Scripts\\python manage.py seed --stage 1')
            self.stdout.write('  env\\Scripts\\python manage.py seed --stage 2')
            self.stdout.write('  env\\Scripts\\python manage.py seed --stage 3 --only  # Only stage 3')
            self.stdout.write('  env\\Scripts\\python manage.py seed --all')
            return
            
        # If --all is used, run all stages
        if run_all:
            stage = 3
            only_stage = False
            
        # At this point, stage should always be a valid integer
        assert stage is not None, "Stage should not be None at this point"

        if only_stage:
            self.stdout.write(self.style.SUCCESS(f'Starting database seeding - Stage {stage} only...'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Starting database seeding - Stage {stage}...'))
        
        with transaction.atomic():
            # Stage 1: Admin user and basic setup
            if not only_stage or stage == 1:
                self.stdout.write(self.style.SUCCESS('=== Stage 1: Creating admin user and basic setup ==='))
                self.create_admin_user()
                self.create_google_social_app()
            
            # Stage 2: Organizations and users
            if (stage >= 2 and not only_stage) or (only_stage and stage == 2):
                self.stdout.write(self.style.SUCCESS('=== Stage 2: Creating organizations and users ==='))
                # Create institutes
                institutes = self.create_institutes()
                
                # Create companies
                companies = self.create_companies()
                
                # Create users and profiles
                students = self.create_students(institutes)
                mentors = self.create_mentors(companies)
                teachers = self.create_teachers(institutes)
                officials = self.create_officials()
            
            # Stage 3: Internships and applications
            if (stage >= 3 and not only_stage) or (only_stage and stage == 3):
                self.stdout.write(self.style.SUCCESS('=== Stage 3: Creating internships and applications ==='))
                # Get existing data if we're only running stage 3
                if only_stage and stage == 3:
                    institutes = list(Institute.objects.all())
                    companies = list(Company.objects.all())
                    students = list(Student.objects.all())
                    mentors = list(Mentor.objects.all())
                    teachers = list(Teacher.objects.all())
                    
                    if not institutes or not companies or not students or not mentors:
                        self.stdout.write(
                            self.style.ERROR('Stage 3 requires existing organizations and users. Run stages 1 and 2 first.')
                        )
                        return
                
                # Create internship positions
                positions = self.create_internship_positions(companies, mentors)
                
                # Create sample applications and internships
                self.create_sample_applications_and_internships(students, positions, mentors, teachers)

        if only_stage:
            self.stdout.write(
                self.style.SUCCESS(f'Database seeding Stage {stage} only completed successfully!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Database seeding Stage {stage} completed successfully!')
            )

    def clear_data(self):
        """Clear existing data"""
        # Clear in the correct order to handle foreign key constraints
        
        # First, clear related data that references main models
        Report.objects.all().delete()
        Notification.objects.all().delete()
        Internship.objects.all().delete()
        Application.objects.all().delete()
        Position.objects.all().delete()
        
        # Remove foreign key references before deleting profiles
        Company.objects.all().update(registered_by=None)
        
        # Clear profile models (which reference companies/institutes)
        Student.objects.all().delete()
        Mentor.objects.all().delete()
        Teacher.objects.all().delete()
        Official.objects.all().delete()
        
        # Clear organization models
        Company.objects.all().delete()
        Institute.objects.all().delete()
        
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
            
            # Create Official for admin is not needed - admins use Django admin
            
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
                
                student_profile = Student.objects.create(
                    user=user,
                    institute=random.choice(institutes),
                    student_id=f'STU{2024000 + i + 1}',
                    semester_of_study=random.choice(['4', '5', '6', '7', '8']),
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
                
                mentor_profile = Mentor.objects.create(
                    user=user,
                    company=companies[i % len(companies)],
                    job_title=position,
                    department=department,
                    experience_years=random.randint(5, 15),
                    specialization=f'{department} and Team Leadership',
                    is_verified=True
                )
                mentors.append(mentor_profile)
                
                # Set the mentor as the one who registered the company (for the first mentor of each company)
                company = companies[i % len(companies)]
                if not company.registered_by:
                    company.registered_by = mentor_profile
                    company.registration_status = 'approved'  # Set to approved so mentors can create positions
                    company.save()
                    self.stdout.write(f'Set {mentor_profile.user.username} as registrant for company {company.name}')
                
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
                
                teacher_profile = Teacher.objects.create(
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
                
                official_profile = Official.objects.create(
                    user=user,
                    department=department,
                    job_title=position,
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
                
                position = Position.objects.create(
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
                company_name = position.company.name if position.company else "Unknown Company"
                application = Application.objects.create(
                    student=student,
                    position=position,
                    cover_letter=f"Dear Hiring Manager,\n\nI am very interested in the {position.title} position at {company_name}. As a {student.major} student with a GPA of {student.gpa}, I believe I would be a great fit for this role.\n\nMy skills in {student.skills[:50]}... align well with your requirements. I am eager to contribute to your team and learn from experienced professionals.\n\nThank you for considering my application.\n\nBest regards,\n{student.user.get_full_name()}",
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
                    company_name = position.company.name if position.company else "Unknown Company"
                    self.stdout.write(f'Created internship: {student.user.username} at {company_name}')
                    
                    # Create progress reports for active/completed internships
                    self.create_sample_progress_reports(internship)
                    
                    # Create notifications
                    company_name = position.company.name if position.company else "Unknown Company"
                    Notification.objects.create(
                        recipient=student.user,
                        notification_type='application_status',
                        title=f'Application Approved - {position.title}',
                        message=f'Congratulations! Your application for {position.title} at {company_name} has been approved. Your internship starts on {position.start_date}.'
                    )
                    
                elif application.status == 'rejected':
                    company_name = position.company.name if position.company else "Unknown Company"
                    Notification.objects.create(
                        recipient=student.user,
                        notification_type='application_status',
                        title=f'Application Update - {position.title}',
                        message=f'Thank you for your interest in {position.title} at {company_name}. Unfortunately, we have decided to move forward with other candidates.'
                    )

    def create_sample_progress_reports(self, internship):
        """Create sample reports, assessments, and evaluations for an internship"""
        if internship.status in ['active', 'completed']:
            reports_to_create = 3 if internship.status == 'active' else 6
            
            from datetime import date, timedelta
            from app.models import Report, Assessment, Evaluation
            start_date = internship.start_date or date.today() - timedelta(days=30)
            
            # Create student reports
            for i in range(reports_to_create):
                report_month = start_date + timedelta(weeks=i)
                
                Report.objects.create(
                    internship=internship,
                    teacher=internship.teacher,
                    report_month=report_month,
                    tasks_performed=f"Period {i+1}: Completed assigned tasks including research, documentation, and hands-on work. Participated in team meetings and training sessions.",
                    tasks_performed_score=random.randint(7, 10),
                    learning_experience=f"Gained experience in {internship.student.major}-related skills. Improved communication and teamwork abilities.",
                    learning_experience_score=random.randint(7, 10),
                    challenges="Initial learning curve with new technologies and processes. Time management across multiple tasks.",
                    challenges_score=random.randint(6, 9),
                    additional_comments="Overall positive experience with good learning opportunities."
                )
            
            # Create mentor assessment (one per internship)
            if internship.status == 'completed':
                Assessment.objects.create(
                    internship=internship,
                    mentor=internship.mentor,
                    technical_skills=random.randint(2, 4),
                    work_quality=random.randint(2, 4),
                    problem_solving=random.randint(2, 4),
                    teamwork=random.randint(3, 4),
                    professionalism=random.randint(3, 4),
                    performance_benefits="Student contributed positively to team projects and brought fresh perspectives.",
                    observed_development="Significant improvement in technical skills and professional communication throughout the internship.",
                    intern_strengths="Quick learner, good communication skills, reliable attendance, positive attitude.",
                    areas_for_improvement="Could benefit from more experience with advanced project management techniques.",
                    intern_rating='good',
                    program_rating='excellent',
                    program_improvement_suggestions="More structured initial training program would be beneficial.",
                    would_recommend=True,
                    additional_comments="We would definitely consider hiring this intern full-time."
                )
            
            # Create teacher evaluation (for completed internships)
            if internship.status == 'completed' and internship.teacher:
                Evaluation.objects.create(
                    internship=internship,
                    teacher=internship.teacher,
                    evaluation_date=start_date + timedelta(days=reports_to_create * 7),
                    discussion_notes="Regular check-ins with student and mentor. Student demonstrated good progress and professional growth.",
                    academic_alignment="Internship aligns well with academic objectives and provides practical experience in the field.",
                    recommendations="Student should consider pursuing advanced coursework in areas where they showed particular strength.",
                    overall_rating=random.randint(4, 5)
                )
            
            self.stdout.write(f'Created sample reports/assessments/evaluations for {internship.student.user.username}')
