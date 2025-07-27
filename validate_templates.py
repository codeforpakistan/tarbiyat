#!/usr/bin/env python
"""
Template validation script for the Tarbiyat internship platform.
This script demonstrates how to use the check_templates management command.
Only validates project templates in app/templates, excluding third-party packages.

Usage examples:
    python validate_templates.py                    # Check all project templates
    python validate_templates.py --app app          # Check specific app templates  
    python validate_templates.py --verbose          # Show detailed output
    python validate_templates.py --fix-common       # Auto-fix common issues
"""

import os
import sys
import subprocess
from pathlib import Path

def run_template_check(args=None):
    """Run the Django template check command for project templates only."""
    if args is None:
        args = []
    
    # Ensure we're in the Django project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Build the command
    cmd = ["env\\Scripts\\python", "manage.py", "check_templates"] + args
    
    print("🔍 Running Django template validation (project templates only)...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        # Run the command and capture output
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ Error: Python executable not found. Make sure virtual environment is set up.")
        print("Run: python -m venv env && env\\Scripts\\activate")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate Django templates for the Tarbiyat platform (project templates only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_templates.py                     # Check all project templates
  python validate_templates.py --app app           # Check app templates only
  python validate_templates.py --verbose           # Detailed output
  python validate_templates.py --fix-common        # Auto-fix issues
  python validate_templates.py --template base.html # Check specific template
        """
    )
    
    parser.add_argument(
        '--app',
        help='Check templates for a specific app only'
    )
    parser.add_argument(
        '--template',
        help='Check a specific template file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output including successful templates'
    )
    parser.add_argument(
        '--fix-common',
        action='store_true',
        help='Attempt to fix common template issues automatically'
    )
    
    args = parser.parse_args()
    
    # Convert arguments to command line format
    cmd_args = []
    if args.app:
        cmd_args.extend(['--app', args.app])
    if args.template:
        cmd_args.extend(['--template', args.template])
    if args.verbose:
        cmd_args.append('--verbose')
    if args.fix_common:
        cmd_args.append('--fix-common')
    
    # Run the template check
    success = run_template_check(cmd_args)
    
    if success:
        print("\n✅ Template validation completed successfully!")
    else:
        print("\n❌ Template validation completed with issues.")
        sys.exit(1)


if __name__ == '__main__':
    main()
