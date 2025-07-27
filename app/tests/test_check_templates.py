"""
Tests for the check_templates management command.
"""

import os
import tempfile
from pathlib import Path
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO


class CheckTemplatesCommandTest(TestCase):
    """Test the check_templates management command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.temp_dir) / 'templates'
        self.template_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_template_file(self, name, content):
        """Helper to create a template file."""
        template_path = self.template_dir / name
        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return template_path

    @override_settings(TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }])
    def test_valid_template(self):
        """Test checking a valid template."""
        # Create a valid template
        template_content = """
        {% load user_tags %}
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Template</title>
        </head>
        <body>
            <h1>Hello, {{ user.username }}!</h1>
            {% if user.is_authenticated %}
                <p>Welcome back!</p>
            {% endif %}
            
            <form method="post">
                {% csrf_token %}
                <input type="submit" value="Submit">
            </form>
        </body>
        </html>
        """
        
        self.create_template_file('test_valid.html', template_content)
        
        out = StringIO()
        with self.settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(self.template_dir)],
            'APP_DIRS': False,
            'OPTIONS': {},
        }]):
            call_command('check_templates', '--verbose', stdout=out)
        
        output = out.getvalue()
        self.assertIn('test_valid.html: OK', output)
        self.assertIn('All templates are well-formed!', output)

    def test_template_with_syntax_error(self):
        """Test checking a template with syntax errors."""
        # Create template with syntax error
        template_content = """
        <html>
        <body>
            {% if user.is_authenticated
                <p>Missing endif and closing bracket</p>
        </body>
        </html>
        """
        
        self.create_template_file('test_syntax_error.html', template_content)
        
        out = StringIO()
        with self.settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(self.template_dir)],
            'APP_DIRS': False,
            'OPTIONS': {},
        }]):
            call_command('check_templates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('test_syntax_error.html', output)
        self.assertIn('ERROR: Syntax error', output)

    def test_template_missing_csrf_token(self):
        """Test checking a template missing CSRF token."""
        # Create template with POST form missing CSRF token
        template_content = """
        <html>
        <body>
            <form method="post" action="/submit/">
                <input type="text" name="data">
                <input type="submit" value="Submit">
            </form>
        </body>
        </html>
        """
        
        self.create_template_file('test_missing_csrf.html', template_content)
        
        out = StringIO()
        with self.settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(self.template_dir)],
            'APP_DIRS': False,
            'OPTIONS': {},
        }]):
            call_command('check_templates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('test_missing_csrf.html', output)
        self.assertIn('POST form missing CSRF token', output)

    def test_template_with_warnings(self):
        """Test checking a template with warnings."""
        # Create template with potential issues
        template_content = """
        <html>
        <body>
            <p>{{ content|safe }}</p>
            <a href="http://example.com/hardcoded">Hardcoded link</a>
        </body>
        </html>
        """
        
        self.create_template_file('test_warnings.html', template_content)
        
        out = StringIO()
        with self.settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(self.template_dir)],
            'APP_DIRS': False,
            'OPTIONS': {},
        }]):
            call_command('check_templates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('test_warnings.html', output)
        self.assertIn('WARNING', output)
        self.assertIn('|safe filter', output)

    def test_unclosed_template_blocks(self):
        """Test checking templates with unclosed blocks."""
        # Create template with unclosed blocks
        template_content = """
        <html>
        <body>
            {% if user.is_authenticated %}
                <p>Welcome!</p>
            {% for item in items %}
                <span>{{ item }}</span>
            <!-- Missing {% endfor %} -->
        </body>
        </html>
        """
        
        self.create_template_file('test_unclosed.html', template_content)
        
        out = StringIO()
        with self.settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(self.template_dir)],
            'APP_DIRS': False,
            'OPTIONS': {},
        }]):
            call_command('check_templates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('test_unclosed.html', output)
        self.assertIn('ERROR', output)

    def test_fix_common_issues(self):
        """Test automatic fixing of common issues."""
        # Create template with fixable issues
        template_content = """
        <html>
        <body>
            <form method="post" action="/submit/">
                <input type="text" name="data">
                <input type="submit" value="Submit">
            </form>
        </body>
        </html>
        """
        
        template_path = self.create_template_file('test_fixable.html', template_content)
        
        out = StringIO()
        with self.settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(self.template_dir)],
            'APP_DIRS': False,
            'OPTIONS': {},
        }]):
            call_command('check_templates', '--fix-common', stdout=out)
        
        # Check if CSRF token was added
        with open(template_path, 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        
        self.assertIn('{% csrf_token %}', fixed_content)
        
        output = out.getvalue()
        self.assertIn('Auto-fixed common issues', output)

    def test_specific_template_check(self):
        """Test checking a specific template file."""
        # Create multiple templates
        self.create_template_file('test1.html', '<html><body>Valid</body></html>')
        self.create_template_file('test2.html', '<html><body>{% if %}</body></html>')  # Invalid
        
        out = StringIO()
        with self.settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(self.template_dir)],
            'APP_DIRS': False,
            'OPTIONS': {},
        }]):
            call_command('check_templates', '--template', 'test1.html', stdout=out)
        
        output = out.getvalue()
        self.assertIn('test1.html', output)
        self.assertNotIn('test2.html', output)  # Should not check this one

    def test_no_templates_found(self):
        """Test when no templates are found."""
        out = StringIO()
        with self.settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': ['/non/existent/path'],
            'APP_DIRS': False,
            'OPTIONS': {},
        }]):
            call_command('check_templates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('No template files found to check', output)

    def test_invalid_app_argument(self):
        """Test providing an invalid app name."""
        with self.assertRaises(CommandError):
            call_command('check_templates', '--app', 'nonexistent_app')

    def test_unreadable_template_file(self):
        """Test handling unreadable template files."""
        # Create a template file
        template_path = self.create_template_file('test_unreadable.html', 'content')
        
        # Make it unreadable by changing permissions (if on Unix-like system)
        try:
            os.chmod(template_path, 0o000)
            
            out = StringIO()
            with self.settings(TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [str(self.template_dir)],
                'APP_DIRS': False,
                'OPTIONS': {},
            }]):
                call_command('check_templates', stdout=out)
            
            output = out.getvalue()
            self.assertIn('Cannot read file', output)
            
        except OSError:
            # Skip this test on systems where chmod doesn't work as expected
            pass
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(template_path, 0o644)
            except OSError:
                pass
