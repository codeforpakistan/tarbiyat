# Contributing to Tarbiyat

Thank you for your interest in contributing to Tarbiyat! This document provides guidelines and information for contributors.

## 🌟 How to Contribute

### Ways to Contribute
- 🐛 **Bug Reports**: Help us identify and fix issues
- 💡 **Feature Requests**: Suggest new features or improvements
- 📝 **Documentation**: Improve or add documentation
- 🔧 **Code Contributions**: Submit bug fixes or new features
- 🎨 **UI/UX Improvements**: Enhance the user interface and experience
- 🧪 **Testing**: Help with testing and quality assurance

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic understanding of Django and web development
- Familiarity with Tailwind CSS (for frontend contributions)

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork the repo on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/tarbiyat.git
   cd tarbiyat
   ```

2. **Set up the development environment**
   ```bash
   # Create virtual environment
   python -m venv env
   
   # Activate it (Windows)
   env\Scripts\activate
   # Or on macOS/Linux
   source env/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure the project**
   ```bash
   # Copy environment file
   cp .env.example .env
   
   # Run migrations
   python manage.py migrate
   
   # Set up groups and sample data
   python manage.py setup_groups
   python manage.py seed
   ```

4. **Create a branch for your work**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/your-bugfix-name
   ```

## 📋 Contribution Guidelines

### Code Style

#### Python/Django
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions small and focused
- Use Django best practices

#### HTML/CSS
- Use semantic HTML5 elements
- Follow Tailwind CSS utility-first approach
- Ensure responsive design (mobile-first)
- Use Unicode characters for icons when possible
- Maintain accessibility standards

#### JavaScript
- Use modern ES6+ syntax
- Follow consistent indentation (2 spaces)
- Add comments for complex logic
- Minimize external dependencies

### Commit Guidelines

Use clear, descriptive commit messages:

```bash
# Good examples
git commit -m "Add student application filtering feature"
git commit -m "Fix notification creation error in mentor dashboard"
git commit -m "Update README with deployment instructions"

# Bad examples
git commit -m "Fix bug"
git commit -m "Update stuff"
git commit -m "WIP"
```

#### Commit Message Format
```
type(scope): brief description

Detailed explanation if needed

- List specific changes
- Reference issues: Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Pull Request Process

1. **Before submitting**
   - Ensure your code follows the style guidelines
   - Run tests and make sure they pass
   - Update documentation if needed
   - Test your changes thoroughly

2. **Submitting a PR**
   - Use a clear, descriptive title
   - Provide a detailed description of changes
   - Reference related issues
   - Include screenshots for UI changes
   - Ensure CI checks pass

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Style/UI improvement
   
   ## Testing
   - [ ] Tests pass locally
   - [ ] Manual testing completed
   
   ## Screenshots (if applicable)
   
   ## Related Issues
   Fixes #(issue number)
   ```

## 🐛 Bug Reports

When reporting bugs, please include:

### Required Information
- **Django version**: Output of `python -c "import django; print(django.get_version())"`
- **Python version**: Output of `python --version`
- **Operating system**: Windows/macOS/Linux
- **Browser** (for UI issues): Chrome/Firefox/Safari/Edge

### Bug Report Template
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Screenshots
If applicable

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

### Before Submitting
- Check if the feature already exists
- Search existing issues and discussions
- Consider if it fits the project's scope

### Feature Request Template
```markdown
## Feature Description
Clear description of the proposed feature

## Problem Statement
What problem does this solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other solutions you've considered

## Additional Context
Any other relevant information
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test app

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Writing Tests
- Write tests for new features
- Update tests when modifying existing features
- Aim for good test coverage
- Use Django's testing framework

## 📖 Documentation

### Areas that need documentation
- Code comments and docstrings
- User guides and tutorials
- API documentation
- Deployment guides

### Documentation Style
- Use clear, simple language
- Include code examples
- Add screenshots for UI features
- Keep documentation up to date

## 🔍 Code Review Process

### For Contributors
- Be open to feedback
- Respond to review comments promptly
- Make requested changes in a timely manner
- Ask questions if something is unclear

### For Reviewers
- Be constructive and respectful
- Focus on code quality and maintainability
- Suggest improvements
- Approve when ready

## 🏛️ Government Standards

Since Tarbiyat is designed for government use, please ensure:

### Security Considerations
- Follow security best practices
- Don't hardcode sensitive information
- Validate all user inputs
- Use Django's built-in security features

### Accessibility
- Follow WCAG guidelines
- Ensure keyboard navigation
- Use proper ARIA labels
- Test with screen readers

### Performance
- Optimize database queries
- Minimize resource usage
- Consider scalability
- Test with realistic data volumes

## 🤝 Community Guidelines

### Be Respectful
- Use inclusive language
- Be patient with newcomers
- Provide constructive feedback
- Help others learn and grow

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: [support@codeforpakistan.org](mailto:support@codeforpakistan.org)

## 📄 License

By contributing to Tarbiyat, you agree that your contributions will be licensed under the same MIT License that covers the project.

## 🙋‍♀️ Need Help?

- Read the documentation
- Check existing issues and discussions
- Ask questions in GitHub Discussions
- Contact the maintainers

## 🏆 Recognition

Contributors will be:
- Listed in the project's contributors
- Mentioned in release notes for significant contributions
- Invited to join the Code for Pakistan community

---

Thank you for contributing to Tarbiyat and helping improve government services through technology! 🇵🇰
