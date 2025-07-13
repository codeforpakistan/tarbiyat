# Tarbiyat - Government Internship Management Platform

A comprehensive Django-based internship management system designed for government agencies to streamline the internship process for students, mentors, teachers, and administrative officials.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/django-5.2.4-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Features

### Multi-Role Support
- **Students**: Browse positions, submit applications, track progress
- **Mentors**: Manage internship positions, review applications, monitor progress
- **Teachers**: Oversee student internships, academic supervision
- **Officials**: Administrative oversight and reporting

### Core Functionality
- 🎯 **Position Management**: Create, edit, and manage internship positions
- 📝 **Application System**: Streamlined application process with cover letters
- 📊 **Progress Tracking**: Comprehensive progress reports and monitoring
- 🔔 **Notifications**: Real-time updates for all stakeholders
- 👥 **Profile Management**: Detailed profiles for all user types
- 🏛️ **Government Focus**: Tailored for government internship programs

### Modern Technology Stack
- **Backend**: Django 5.2.4 with PostgreSQL/SQLite support
- **Frontend**: Tailwind CSS for modern, responsive design
- **Icons**: Unicode characters for dependency-free icons
- **Security**: Built-in Django security features with custom middleware
- **Authentication**: Django Allauth integration

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/codeforpakistan/tarbiyat.git
   cd tarbiyat
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   
   # On Windows
   env\Scripts\activate
   
   # On macOS/Linux
   source env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create sample data (optional)**
   ```bash
   python manage.py setup_groups
   python manage.py seed
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000` to access the application.

## 📁 Project Structure

```
tarbiyat/
├── app/                          # Main application
│   ├── management/commands/      # Custom Django commands
│   ├── migrations/               # Database migrations
│   ├── templates/               # HTML templates
│   ├── templatetags/            # Custom template tags
│   ├── models.py               # Database models
│   ├── views.py                # View logic
│   ├── urls.py                 # URL routing
│   └── forms.py                # Django forms
├── project/                     # Project settings
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL configuration
│   └── wsgi.py                 # WSGI configuration
├── requirements.txt            # Python dependencies
├── manage.py                   # Django management script
└── README.md                   # This file
```

## 🎨 Design Philosophy

### Modern & Accessible
- **Tailwind CSS**: Utility-first CSS framework for rapid development
- **Responsive Design**: Mobile-first approach for all devices
- **Unicode Icons**: Dependency-free icons using Unicode characters
- **Clean UI**: Modern, government-appropriate interface design

### Government-Ready
- **Security First**: Built with Django's security best practices
- **Scalable Architecture**: Designed to handle multiple institutions
- **Comprehensive Tracking**: Full audit trail for all activities
- **Multi-level Access**: Role-based permissions and workflows

## 🔧 Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database Configuration
The project supports both SQLite (development) and PostgreSQL (production).

For PostgreSQL:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/tarbiyat
```

## 👥 User Roles

### Student
- Browse available internship positions
- Submit applications with cover letters
- Track application status
- Submit progress reports
- Manage personal profile

### Mentor
- Create and manage internship positions
- Review and process applications
- Monitor intern progress
- Provide feedback and evaluations

### Teacher
- Academic supervision of students
- Monitor student progress
- Coordinate with mentors
- Administrative oversight

### Official
- System administration
- Generate reports and analytics
- Manage users and permissions
- Oversee all internship programs

## 🛠️ Development

### Management Commands

```bash
# Check environment configuration
python manage.py check_env

# Set up user groups and permissions
python manage.py setup_groups

# Generate sample data for testing
python manage.py seed
```

### Testing
```bash
python manage.py test
```

### Code Style
This project follows Django best practices and PEP 8 guidelines.

## 🚀 Deployment

### Production Setup

1. **Set environment variables**
   ```bash
   export DEBUG=False
   export SECRET_KEY=your-production-secret-key
   export DATABASE_URL=your-production-database-url
   ```

2. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

### Docker Support (Coming Soon)
Docker configuration for easy deployment will be added in future releases.

## 📖 Documentation

- [Environment Setup Guide](ENVIRONMENT_SETUP.md)
- [Authentication Templates](AUTHENTICATION_TEMPLATES.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏛️ About Code for Pakistan

This project is developed by [Code for Pakistan](https://codeforpakistan.org), a non-profit organization working to improve government services through technology.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/codeforpakistan/tarbiyat/issues) page
2. Create a new issue if your problem isn't already reported
3. Contact us at [support@codeforpakistan.org](mailto:support@codeforpakistan.org)

## 🙏 Acknowledgments

- Django team for the excellent web framework
- Tailwind CSS for the utility-first CSS framework
- All contributors who help improve this project

---

Made with ❤️ by [Code for Pakistan](https://codeforpakistan.org)
