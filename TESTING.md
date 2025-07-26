# Test Documentation for Tarbiyat Internship Platform

## Overview

This document describes the comprehensive test suite for the Tarbiyat internship management platform. The tests are organized into multiple modules within the `app/tests/` directory to provide thorough coverage of all application components.

## Test Structure

### Test Directory Organization

The tests are now organized in the `app/tests/` directory with the following structure:

```
app/tests/
├── __init__.py                 # Test package initialization
├── test_models.py             # Model tests
├── test_views.py              # View and authentication tests  
├── test_forms.py              # Form validation tests
├── test_utils.py              # Utility function tests
└── test_integration.py        # Integration and workflow tests
```

### Test Files

1. **`app/tests/test_models.py`** - Comprehensive model tests
2. **`app/tests/test_views.py`** - View functionality and authentication tests
3. **`app/tests/test_forms.py`** - Form validation and processing tests
4. **`app/tests/test_utils.py`** - Utility function tests
5. **`app/tests/test_integration.py`** - Integration and end-to-end workflow tests
6. **`app/tests.py`** - Legacy test file (still contains some integration tests)
7. **`run_tests.py`** - Test runner script

### Test Categories

#### Model Tests (`test_models.py`)
- **ModelCreationTest**: Tests basic model creation and field validation
- **NanoidGenerationTest**: Tests nanoid generation and uniqueness across all models
- **OrganizationModelTest**: Tests Institute and Company models with domain verification
- **ProfileModelTest**: Tests all profile models (Student, Mentor, Teacher, Official)
- **InternshipWorkflowModelTest**: Tests internship position, application, and internship models
- **ModelRelationshipTest**: Tests foreign key relationships and related object access
- **ModelValidationTest**: Tests model field validation and constraints
- **ModelStringRepresentationTest**: Tests `__str__` methods of all models

#### View Tests (`test_views.py`)
- **UtilityFunctionTest**: Tests the `get_user_type` utility function
- **HomeViewTest**: Tests home page functionality for different user types
- **AuthenticationTest**: Tests login requirements and role-based access
- **ProfileCompletionMiddlewareTest**: Tests profile completion middleware
- **MessageFrameworkTest**: Tests Django messages framework integration
- **ResponseContentTest**: Tests response content and templates
- **URLResolutionTest**: Tests URL routing and resolution
- **SessionHandlingTest**: Tests session persistence and logout
- **ErrorHandlingTest**: Tests error handling (404, 403, 405)

#### Form Tests (`test_forms.py`)
- **CustomSignupFormTest**: Tests the custom signup form validation and processing
- **FormFieldValidationTest**: Tests individual form field validations
- **FormUserTypeTest**: Tests user type choice validation
- **FormErrorHandlingTest**: Tests form error conditions and edge cases

#### Utility Tests (`test_utils.py`)
- **UtilityFunctionTest**: Tests all utility functions in `utils.py`
- **DomainExtractionTest**: Tests email domain extraction functions
- **OrganizationMembershipTest**: Tests organization membership validation
- **UserTypeUtilityTest**: Tests user type detection utilities
- **UtilityErrorHandlingTest**: Tests edge cases and error conditions

#### Integration Tests (`test_integration.py`)
- **IntegrationTest**: End-to-end workflow tests
- **OrganizationApprovalWorkflowTest**: Tests complete organization registration and approval
- **InternshipLifecycleTest**: Tests complete internship lifecycle from posting to completion
- **StudentApplicationWorkflowTest**: Tests student application process
- **MentorPositionManagementTest**: Tests mentor position creation and management
- **NotificationSystemTest**: Tests notification system workflows
- **MultiRoleUserTest**: Tests users with multiple roles
- **OfficialProfileModelTest**: Official profile tests
- **InternshipWorkflowTest**: End-to-end internship workflow tests
- **SecurityTestCase**: Security and authorization tests
- **EdgeCaseTest**: Edge cases and error handling
- **IntegrationTest**: Complete workflow integration tests

## Running Tests

### Run All Tests
```bash
# Using Django's test runner (all tests)
env\Scripts\python manage.py test

# Run all tests in the organized test package
env\Scripts\python manage.py test app.tests

# Using the test runner script
env\Scripts\python run_tests.py
```

### Run Specific Test Modules
```bash
# Model tests
env\Scripts\python manage.py test app.tests.test_models

# View tests  
env\Scripts\python manage.py test app.tests.test_views

# Form tests
env\Scripts\python manage.py test app.tests.test_forms

# Utility function tests
env\Scripts\python manage.py test app.tests.test_utils

# Integration workflow tests
env\Scripts\python manage.py test app.tests.test_integration

# Legacy tests (if still needed)
env\Scripts\python manage.py test app.tests
```

### Run Specific Test Classes
```bash
env\Scripts\python manage.py test app.test_models.NanoidGenerationTest
env\Scripts\python manage.py test app.test_views.HomeViewTest
env\Scripts\python manage.py test app.test_utils.CustomSignupFormTest
```

### Run with Verbose Output
```bash
env\Scripts\python manage.py test -v 2
```

## Test Coverage

### Models Covered
- ✅ Institute (creation, domain validation, approval status)
- ✅ Company (creation, domain validation, approval status)
- ✅ StudentProfile (creation, completion calculation, validation)
- ✅ MentorProfile (creation, company membership, permissions)
- ✅ TeacherProfile (creation, institute membership, permissions)
- ✅ OfficialProfile (creation, basic functionality)
- ✅ InternshipPosition (creation, properties, relationships)
- ✅ InternshipApplication (creation, unique constraints)
- ✅ Internship (creation, progress calculation)

### Views Covered
- ✅ Home view (anonymous and authenticated users)
- ✅ Authentication and authorization
- ✅ Role-based access control
- ✅ Profile completion middleware
- ✅ Error handling (404, 403, 405)
- ✅ Session handling
- ✅ URL resolution

### Utilities Covered
- ✅ `validate_user_organization_membership`
- ✅ `get_available_institutes_for_user`
- ✅ `get_available_companies_for_user`
- ✅ `extract_domain_from_email`
- ✅ `get_user_type`

### Forms Covered
- ✅ CustomSignupForm (validation, user creation, group assignment)

### Security Tests Covered
- ✅ Unauthenticated access prevention
- ✅ Cross-role access prevention
- ✅ Email domain validation
- ✅ Organization membership validation
- ✅ CSRF protection (infrastructure)

## Test Data Setup

### Common Test Data
- **Users**: Student, Mentor, Teacher, Official users with appropriate groups
- **Organizations**: Verified and unverified institutes and companies
- **Profiles**: Complete and minimal profiles for testing completion calculations
- **Groups**: All four user type groups (student, mentor, teacher, official)

### Test Database
- Uses SQLite in-memory database for fast test execution
- Automatically created and destroyed for each test run
- Migrations applied automatically during test setup

## Test Best Practices

### Followed Practices
1. **Isolation**: Each test is independent and doesn't depend on others
2. **Descriptive Names**: Test methods have clear, descriptive names
3. **Setup/Teardown**: Proper setup and cleanup in `setUp()` methods
4. **Edge Cases**: Testing edge cases and error conditions
5. **Documentation**: Each test class and method is documented
6. **Assertions**: Using appropriate Django test assertions
7. **Data Validation**: Testing model validation and constraints

### Test Categories
- **Unit Tests**: Testing individual components in isolation
- **Integration Tests**: Testing component interactions
- **Functional Tests**: Testing complete user workflows
- **Security Tests**: Testing authentication and authorization
- **Edge Case Tests**: Testing error conditions and boundary cases

## Known Issues and Limitations

### Current Limitations
1. **View Tests**: Some view tests may need adjustment based on actual URL patterns
2. **File Upload Tests**: Resume upload functionality needs dedicated tests
3. **Email Tests**: Email sending functionality not yet tested
4. **Admin Tests**: Django admin customizations not tested
5. **API Tests**: No API endpoints to test currently

### Future Improvements
1. Add tests for file uploads (resume functionality)
2. Add tests for email notifications
3. Add performance tests for large datasets
4. Add browser automation tests (Selenium)
5. Add API tests when APIs are implemented
6. Add database migration tests
7. Add deployment configuration tests

## Continuous Integration

### Recommended CI Pipeline
1. **Linting**: Run code linting (flake8, black)
2. **Type Checking**: Run type checking (mypy) if enabled
3. **Security**: Run security checks (bandit)
4. **Tests**: Run full test suite
5. **Coverage**: Generate test coverage report
6. **Documentation**: Validate documentation

### Test Commands for CI
```bash
# Run all tests with coverage
env\Scripts\python -m coverage run manage.py test
env\Scripts\python -m coverage report
env\Scripts\python -m coverage html

# Run linting
flake8 app/
black --check app/

# Run security checks
bandit -r app/
```

## Contributing to Tests

### Adding New Tests
1. Place model tests in `test_models.py`
2. Place view tests in `test_views.py`
3. Place utility/form tests in `test_utils.py`
4. Follow existing naming conventions
5. Include docstrings for test methods
6. Test both success and failure cases
7. Use appropriate assertion methods

### Test Naming Convention
- Test classes: `[Component]Test` (e.g., `StudentProfileModelTest`)
- Test methods: `test_[functionality]_[scenario]` (e.g., `test_profile_completion_with_all_fields`)

This comprehensive test suite ensures the reliability and maintainability of the Tarbiyat internship platform.
