# Copilot Instructions for Tarbiyat Internship Platform

## Project Overview
Tarbiyat is a Django-based government internship management platform supporting four user roles: **Students**, **Mentors**, **Teachers**, and **Officials**. The platform uses role-based access control through Django Groups and implements organization domain verification for institutional integrity.

## Architecture & Key Patterns

### Role-Based Architecture
- **User Types**: Defined via Django Groups (`student`, `mentor`, `teacher`, `official`)
- **Profile Models**: Each role has a dedicated profile model linked to User via OneToOneField
- **Access Control**: Views use `get_user_type()` helper function to determine user role
- **Middleware**: `ProfileCompletionMiddleware` enforces profile completion before access

```python
# Common pattern for role-based views
user_type = get_user_type(request.user)
if user_type != 'expected_role':
    messages.error(request, 'Access denied. Required role account needed.')
    return redirect('home')
```

### Organization Domain Verification
- **Companies** and **Institutes** have `email_domain` fields for domain verification
- Users can only join verified organizations if their email matches the organization's domain
- Registration requires approval workflow: `pending` → `approved` by Officials
- Use `validate_user_organization_membership()` utility for email domain validation

### Nanoid-Based IDs
- All major models use nanoid primary keys instead of auto-incrementing integers
- Different nanoid sizes for different models (e.g., 12 chars for positions, 10 for companies)
- Import from `nanoid` package, not UUID

### Template & Styling Approach
- **Tailwind CSS**: Loaded via CDN with custom config in `base.html`
- **Unicode Icons**: Uses Unicode characters (🤝, ✓, ⚠) instead of icon libraries
- **Responsive Design**: Mobile-first approach with Tailwind utilities
- **Template Tags**: Custom `user_tags.py` provides `get_user_type` and `has_user_type` filters

## Development Workflows

### Essential Django Commands
```bash
# Initial setup (always use env\Scripts\python in activated environment)
env\Scripts\python manage.py setup_groups    # Creates role-based groups
env\Scripts\python manage.py seed            # Generates test data
env\Scripts\python manage.py check_env       # Validates environment configuration

# Standard Django commands
env\Scripts\python manage.py makemigrations
env\Scripts\python manage.py migrate
env\Scripts\python manage.py runserver
```

### Command Execution Guidelines
- **Python Path**: Always use `env\Scripts\python` for Python commands
- **Terminal Mode**: Always use foreground terminals for all command execution (never background)
- **Virtual Environment**: Commands assume activated virtual environment
- **Foreground Execution**: Set `isBackground=false` for all `run_in_terminal` calls to ensure proper output visibility and interaction
- **Windows CMD**: Use simple single commands or create temporary files for complex scripts - avoid multi-line scripts in quotes
- **Git Commits**: Always use separate `-m` flags for multi-line commit messages instead of newlines in quotes

### Database & Models
- **SQLite**: Used for both development and production (no PostgreSQL setup needed)
- **File Uploads**: Student resumes stored in `media/resumes/` with file type validation
- **Approval Workflows**: Most models have `registration_status` and approval tracking fields

### View Patterns
- All role-specific views use `@login_required` decorator
- Profile existence checking with try/except blocks for missing profiles
- Consistent redirect patterns: incomplete profiles → `complete_profile`
- Message framework used extensively for user feedback

### URL Structure
- Role-based URL prefixes: `/student/`, `/mentor/`, `/teacher/`, `/official/`
- Nanoid-based detail URLs: `/position/<str:position_nanoid>/`
- Generic patterns like `/profile/edit/` with role-specific implementations

## Testing & Quality

### Current State
- Minimal test coverage in `app/tests.py` (placeholder only)
- Manual testing workflows documented in README
- Use `env\Scripts\python manage.py seed --clear` for fresh test data

### Code Style
- Django best practices and PEP 8 compliance
- Consistent naming: nanoid fields named `nanoid`, not `id`
- Model methods follow Django conventions (`__str__`, `is_approved()`, etc.)

## Integration Points

### Authentication
- **Django Allauth**: Handles user registration/login with social auth support
- Custom account adapters in `app/account_adapters.py`
- Profile completion flow integrated with registration

### File Management
- **Whitenoise**: Static file serving in production
- **Media Files**: Resume uploads with file type validation
- **Static Assets**: Tailwind CSS via CDN, custom CSS/JS in `app/static/`

### Dependencies
- **Core**: Django 5.2.4, django-allauth, python-decouple
- **Deployment**: gunicorn, whitenoise for Heroku/cloud deployment
- **Utilities**: nanoid for ID generation

## Common Gotchas

1. **Profile Completion**: New users must complete role selection and profile creation before accessing main features
2. **Organization Membership**: Email domain validation is enforced for verified organizations
3. **Role Switching**: Users cannot change roles after initial selection (handled via Groups)
4. **Nanoid Fields**: Use string-based lookups, not integer IDs
5. **Static Files**: Custom CSS/JS files may not exist yet - Tailwind handles most styling

## Key Files to Reference
- `app/models.py`: Core data models and relationships
- `app/views.py`: Role-based view logic and patterns
- `app/utils.py`: Organization validation utilities
- `app/middleware.py`: Profile completion enforcement
- `project/settings.py`: Django configuration with Allauth integration
- `app/management/commands/`: Custom Django commands for setup
