"""
Django management command to check if templates are well-formed.

This command validates Django templates for:
- Syntax errors
- Missing template tags
- Unclosed template blocks
- Missing context variables (warnings)
- Template inheritance issues
"""

import os
import re
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template
from django.template.engine import Engine
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = 'Check if Django templates in the project (app/templates) are well-formed and identify potential issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Check templates for a specific app only',
        )
        parser.add_argument(
            '--template',
            type=str,
            help='Check a specific template file',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output including successful templates',
        )
        parser.add_argument(
            '--fix-common',
            action='store_true',
            help='Attempt to fix common template issues automatically',
        )

    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        self.fix_common = options.get('fix_common', False)
        
        self.style.SUCCESS = self.style.SUCCESS
        self.style.ERROR = self.style.ERROR  
        self.style.WARNING = self.style.WARNING
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Starting Django template validation (project templates only)...\n')
        )
        
        template_dirs = self.get_template_directories(options.get('app'))
        template_files = self.find_template_files(template_dirs, options.get('template'))
        
        if not template_files:
            self.stdout.write(
                self.style.WARNING('⚠ No template files found to check.')
            )
            return
            
        self.stdout.write(f'Found {len(template_files)} template files to check.\n')
        
        results = {
            'total': len(template_files),
            'valid': 0,
            'errors': 0,
            'warnings': 0,
            'fixed': 0
        }
        
        for template_file in template_files:
            result = self.check_template(template_file)
            results[result] += 1
            
        self.print_summary(results)

    def get_template_directories(self, specific_app=None):
        """Get template directories to check - only from the app folder."""
        template_dirs = []
        
        # Only look at the main app's templates directory
        if specific_app:
            try:
                app_config = apps.get_app_config(specific_app)
                # Only include if it's our main app, not third-party packages
                if not app_config.path.startswith(os.path.join(os.getcwd(), 'env')):
                    app_template_dir = os.path.join(app_config.path, 'templates')
                    if os.path.exists(app_template_dir):
                        template_dirs.append(app_template_dir)
            except LookupError:
                raise CommandError(f'App "{specific_app}" not found.')
        else:
            # Only include our project apps, exclude third-party packages
            project_root = os.getcwd()
            for app_config in apps.get_app_configs():
                # Skip third-party packages (those in env/ or site-packages)
                if (app_config.path.startswith(os.path.join(project_root, 'env')) or
                    'site-packages' in app_config.path):
                    continue
                    
                app_template_dir = os.path.join(app_config.path, 'templates')
                if os.path.exists(app_template_dir):
                    template_dirs.append(app_template_dir)
        
        return template_dirs

    def find_template_files(self, template_dirs, specific_template=None):
        """Find all template files in the given directories."""
        template_files = []
        
        for template_dir in template_dirs:
            template_path = Path(template_dir)
            if not template_path.exists():
                continue
                
            if specific_template:
                # Look for specific template
                specific_path = template_path / specific_template
                if specific_path.exists() and specific_path.suffix == '.html':
                    template_files.append(specific_path)
            else:
                # Find all HTML templates recursively
                for html_file in template_path.rglob('*.html'):
                    template_files.append(html_file)
        
        return sorted(template_files)

    def check_template(self, template_path):
        """Check a single template file for issues."""
        relative_path = self.get_relative_path(template_path)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except (IOError, UnicodeDecodeError) as e:
            self.stdout.write(
                self.style.ERROR(f'✗ {relative_path}: Cannot read file - {e}')
            )
            return 'errors'
        
        issues = []
        warnings = []
        
        # Check for syntax errors
        try:
            template = Template(template_content)
            # Try to render with empty context to catch more issues
            template.render(Context({}))
        except TemplateSyntaxError as e:
            issues.append(f'Syntax error: {e}')
        except Exception as e:
            # Some errors only show up during rendering
            # Filter out common false positives
            error_msg = str(e).lower()
            if not any(false_positive in error_msg for false_positive in [
                'request', 'csrf_token', 'user', 'messages'
            ]):
                warnings.append(f'Rendering warning: {e}')
        
        # Check for common template issues
        template_issues = self.check_template_patterns(template_content, template_path)
        issues.extend(template_issues['errors'])
        warnings.extend(template_issues['warnings'])
        
        # Attempt fixes if requested
        if self.fix_common and issues:
            fixed_content = self.attempt_fixes(template_content, issues)
            if fixed_content != template_content:
                try:
                    with open(template_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    self.stdout.write(
                        self.style.SUCCESS(f'🔧 {relative_path}: Auto-fixed common issues')
                    )
                    return 'fixed'
                except IOError as e:
                    issues.append(f'Could not write fixes: {e}')
        
        # Report results
        if issues:
            self.stdout.write(self.style.ERROR(f'✗ {relative_path}:'))
            for issue in issues:
                self.stdout.write(f'    ERROR: {issue}')
            for warning in warnings:
                self.stdout.write(f'    WARNING: {warning}')
            return 'errors'
        elif warnings:
            self.stdout.write(self.style.WARNING(f'⚠ {relative_path}:'))
            for warning in warnings:
                self.stdout.write(f'    WARNING: {warning}')
            return 'warnings'
        else:
            if self.verbose:
                self.stdout.write(self.style.SUCCESS(f'✓ {relative_path}: OK'))
            return 'valid'

    def check_template_patterns(self, content, template_path):
        """Check for common template pattern issues."""
        issues = {'errors': [], 'warnings': []}
        
        # Check for unclosed template blocks
        block_pattern = r'{%\s*(block|if|for|with|comment|verbatim|spaceless)\s+([^%]*)%}'
        end_pattern = r'{%\s*end(block|if|for|with|comment|verbatim|spaceless)\s*%}'
        
        blocks = re.findall(block_pattern, content)
        ends = re.findall(end_pattern, content)
        
        block_counts = {}
        for block_type, _ in blocks:
            block_counts[block_type] = block_counts.get(block_type, 0) + 1
            
        end_counts = {}
        for end_type in ends:
            end_counts[end_type] = end_counts.get(end_type, 0) + 1
        
        for block_type, count in block_counts.items():
            end_count = end_counts.get(block_type, 0)
            if count != end_count:
                issues['errors'].append(
                    f'Mismatched {block_type} blocks: {count} opened, {end_count} closed'
                )
        
        # Check for missing load tags for common template tags
        if '{% extends' in content and '{% load' not in content:
            # Check if template uses tags that need loading
            needs_load = []
            if any(tag in content for tag in ['{% csrf_token']):
                needs_load.append('Check if you need {% load %} tags for custom template tags')
            if '|' in content and 'filter' in content:
                needs_load.append('Check if custom filters need {% load %} tags')
            
            if needs_load:
                issues['warnings'].extend(needs_load)
        
        # Check for potential XSS issues
        if '|safe' in content:
            issues['warnings'].append(
                'Found |safe filter - ensure content is properly sanitized'
            )
        
        # Check for hardcoded URLs
        href_pattern = r'href\s*=\s*["\'][^"\']*["\']'
        hardcoded_urls = re.findall(href_pattern, content)
        for url in hardcoded_urls:
            if 'http' in url and '{% url' not in url:
                issues['warnings'].append(
                    f'Potential hardcoded URL: {url}. Consider using {{% url %}} tag'
                )
        
        # Check for missing CSRF tokens in forms
        if '<form' in content and 'method="post"' in content.lower():
            if '{% csrf_token %}' not in content and '{{ csrf_token }}' not in content:
                issues['errors'].append(
                    'POST form missing CSRF token'
                )
        
        return issues

    def attempt_fixes(self, content, issues):
        """Attempt to automatically fix common template issues."""
        fixed_content = content
        
        # Add CSRF token to POST forms
        if any('POST form missing CSRF token' in issue for issue in issues):
            form_pattern = r'(<form[^>]*method\s*=\s*["\']post["\'][^>]*>)'
            def add_csrf(match):
                form_tag = match.group(1)
                return f'{form_tag}\n    {{% csrf_token %}}'
            
            fixed_content = re.sub(form_pattern, add_csrf, fixed_content, flags=re.IGNORECASE)
        
        return fixed_content

    def get_relative_path(self, template_path):
        """Get relative path for display."""
        try:
            return str(template_path.relative_to(Path.cwd()))
        except ValueError:
            return str(template_path)

    def print_summary(self, results):
        """Print summary of template check results."""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 TEMPLATE VALIDATION SUMMARY'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'Total templates checked: {results["total"]}')
        
        if results['valid'] > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Valid templates: {results["valid"]}')
            )
        
        if results['warnings'] > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠ Templates with warnings: {results["warnings"]}')
            )
        
        if results['errors'] > 0:
            self.stdout.write(
                self.style.ERROR(f'✗ Templates with errors: {results["errors"]}')
            )
        
        if results['fixed'] > 0:
            self.stdout.write(
                self.style.SUCCESS(f'🔧 Templates auto-fixed: {results["fixed"]}')
            )
        
        if results['errors'] == 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 All templates are well-formed!')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Found issues in {results["errors"]} templates.')
            )
            self.stdout.write('Run with --fix-common to attempt automatic fixes.')
