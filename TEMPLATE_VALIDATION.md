# Django Template Validation Command

The `check_templates` management command provides comprehensive validation for Django templates in the Tarbiyat internship platform. It focuses exclusively on project templates in the `app/templates` folder, excluding third-party packages and virtual environment templates.

## Features

- **Project-Focused**: Only validates templates in your project's `app/templates` folder
- **Excludes Third-Party**: Automatically skips templates from virtual environment and packages
- **Syntax Error Detection**: Identifies Django template syntax errors
- **Block Matching**: Detects unclosed template blocks (`{% if %}`, `{% for %}`, etc.)
- **CSRF Token Validation**: Ensures POST forms have CSRF protection
- **Security Warnings**: Flags potential XSS issues with `|safe` filter
- **URL Analysis**: Identifies hardcoded URLs that should use `{% url %}` tags
- **Missing Load Tags**: Warns about missing `{% load %}` statements
- **Auto-Fix Common Issues**: Can automatically fix some problems
- **Flexible Targeting**: Check all templates, specific apps, or individual files

## Installation

The command is automatically available when the Django app is installed. No additional setup required.

## Usage

### Basic Usage

```bash
# Check all templates in the project
env\Scripts\python manage.py check_templates

# Check with detailed output
env\Scripts\python manage.py check_templates --verbose

# Check templates for a specific app only
env\Scripts\python manage.py check_templates --app app

# Check a specific template file
env\Scripts\python manage.py check_templates --template base.html

# Attempt to auto-fix common issues
env\Scripts\python manage.py check_templates --fix-common
```

### Using the Convenience Script

A wrapper script `validate_templates.py` is also provided for easier usage:

```bash
# Check all templates
python validate_templates.py

# Check with options
python validate_templates.py --verbose --fix-common
python validate_templates.py --app app
python validate_templates.py --template home.html
```

## Command Options

| Option | Description |
|--------|-------------|
| `--app APP` | Check templates for a specific Django app only |
| `--template TEMPLATE` | Check a specific template file |
| `--verbose` | Show detailed output including successful templates |
| `--fix-common` | Attempt to automatically fix common template issues |

## What It Checks

### 1. Syntax Errors
- Invalid Django template syntax
- Malformed template tags
- Missing closing tags

### 2. Block Structure
- Unclosed `{% if %}`, `{% for %}`, `{% with %}` blocks
- Mismatched `{% block %}` and `{% endblock %}` pairs
- Incorrect nesting of template blocks

### 3. Security Issues
- Missing CSRF tokens in POST forms
- Usage of `|safe` filter (potential XSS)
- Hardcoded URLs that should use `{% url %}` tags

### 4. Best Practices
- Missing `{% load %}` statements for template tags
- Template inheritance issues
- Context variable availability

## Output Format

The command provides color-coded output:

- ✓ **Green**: Valid templates with no issues
- ⚠ **Yellow**: Templates with warnings (non-critical issues)
- ✗ **Red**: Templates with errors (syntax errors, critical issues)
- 🔧 **Blue**: Templates that were automatically fixed

## Auto-Fix Capabilities

The `--fix-common` option can automatically fix:

- **Missing CSRF tokens**: Adds `{% csrf_token %}` to POST forms
- **Basic formatting issues**: Corrects common whitespace problems

More auto-fix capabilities will be added in future versions.

## Example Output

```
🔍 Starting Django template validation (project templates only)...

Found 74 template files to check.

✓ app/templates/app/home.html: OK
⚠ app/templates/app/form.html:
    WARNING: Found |safe filter - ensure content is properly sanitized
✗ app/templates/app/broken.html:
    ERROR: Syntax error: Invalid block tag on line 15: 'endif', expected 'endblock'
    ERROR: POST form missing CSRF token

==================================================
📊 TEMPLATE VALIDATION SUMMARY
==================================================
Total templates checked: 74
✓ Valid templates: 27
⚠ Templates with warnings: 42
✗ Templates with errors: 5

❌ Found issues in 5 templates.
Run with --fix-common to attempt automatic fixes.
```

## Integration with CI/CD

You can integrate this command into your CI/CD pipeline to catch template issues early:

```bash
# In your CI script
env\Scripts\python manage.py check_templates
if [ $? -ne 0 ]; then
    echo "Template validation failed!"
    exit 1
fi
```

## Common Issues Found

### 1. Missing CSRF Tokens
```html
<!-- Bad -->
<form method="post">
    <input type="submit" value="Submit">
</form>

<!-- Good -->
<form method="post">
    {% csrf_token %}
    <input type="submit" value="Submit">
</form>
```

### 2. Unclosed Template Blocks
```html
<!-- Bad -->
{% if user.is_authenticated %}
    <p>Welcome!</p>
<!-- Missing {% endif %} -->

<!-- Good -->
{% if user.is_authenticated %}
    <p>Welcome!</p>
{% endif %}
```

### 3. Hardcoded URLs
```html
<!-- Bad -->
<a href="/positions/123/">View Position</a>

<!-- Good -->
<a href="{% url 'position_detail' position.nanoid %}">View Position</a>
```

### 4. Missing Load Tags
```html
<!-- Bad -->
{{ form.as_p }}  <!-- Might need {% load widget_tweaks %} -->

<!-- Good -->
{% load widget_tweaks %}
{{ form.as_p }}
```

## Performance

The command is optimized for performance:
- Templates are parsed once and cached
- Only checks files with `.html` extension
- Skips binary files and non-template directories
- Provides progress feedback for large projects

## Limitations

- Cannot detect runtime context issues
- Some complex template logic may not be fully analyzed
- Third-party template tags may cause false positives
- Auto-fix is limited to common, safe operations

## Troubleshooting

### Command Not Found
Make sure you're in the Django project directory and using the correct Python path:
```bash
cd /path/to/your/django/project
env\Scripts\python manage.py check_templates
```

### Permission Errors
Ensure the script has read access to template files and write access for auto-fix:
```bash
# On Unix-like systems
chmod +r app/templates/**/*.html
```

### False Positives
Some warnings may be false positives for advanced template usage. Use `--verbose` to get detailed information about each issue.

## Contributing

To extend the template checker:

1. Add new validation patterns in `check_template_patterns()` method
2. Implement auto-fix logic in `attempt_fixes()` method  
3. Add test cases in `app/tests/test_check_templates.py`
4. Update this documentation

## Related Commands

- `env\Scripts\python manage.py check` - Django's built-in system check
- `env\Scripts\python manage.py validate` - Deprecated Django validation
- `env\Scripts\python manage.py collectstatic` - Static file collection
