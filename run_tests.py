#!/usr/bin/env python
"""
Test runner script for the Tarbiyat internship platform.
Run all tests with coverage reporting and detailed output.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run all tests in the app
    test_modules = [
        'app.tests',
        'app.test_models', 
        'app.test_views',
        'app.test_utils'
    ]
    
    failures = test_runner.run_tests(test_modules)
    
    if failures:
        sys.exit(bool(failures))
