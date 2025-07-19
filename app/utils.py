"""
Utility functions for the internship management system
"""
from django.core.exceptions import ValidationError
from django.contrib import messages
from .models import Institute, Company


def validate_user_organization_membership(user, organization_type, organization_id):
    """
    Validate that a user can join an organization based on email domain
    
    Args:
        user: User instance
        organization_type: 'institute' or 'company'
        organization_id: ID of the organization
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if organization_type == 'institute':
        try:
            institute = Institute.objects.get(pk=organization_id)
            if institute.domain_verified and not institute.is_email_from_institute(user.email):
                return False, f"Your email domain must match {institute.name}'s official domain ({institute.email_domain}) to join this institute."
            return True, None
        except Institute.DoesNotExist:
            return False, "Institute not found."
    
    elif organization_type == 'company':
        try:
            company = Company.objects.get(pk=organization_id)
            if company.domain_verified and not company.is_email_from_company(user.email):
                return False, f"Your email domain must match {company.name}'s official domain ({company.email_domain}) to join this company."
            return True, None
        except Company.DoesNotExist:
            return False, "Company not found."
    
    return False, "Invalid organization type."


def get_available_institutes_for_user(user):
    """
    Get institutes that the user can join based on email domain
    
    Args:
        user: User instance
    
    Returns:
        QuerySet: Available institutes
    """
    # Get all institutes without domain verification or with matching domain
    available_institutes = []
    
    for institute in Institute.objects.all():
        if not institute.domain_verified or institute.is_email_from_institute(user.email):
            available_institutes.append(institute.pk)
    
    return Institute.objects.filter(pk__in=available_institutes)


def get_available_companies_for_user(user):
    """
    Get companies that the user can join based on email domain
    
    Args:
        user: User instance
    
    Returns:
        QuerySet: Available companies
    """
    # Get all companies without domain verification or with matching domain
    available_companies = []
    
    for company in Company.objects.all():
        if not company.domain_verified or company.is_email_from_company(user.email):
            available_companies.append(company.pk)
    
    return Company.objects.filter(pk__in=available_companies)


def extract_domain_from_email(email):
    """
    Extract domain from email address
    
    Args:
        email: Email address string
    
    Returns:
        str: Domain part of email
    """
    if email and '@' in email:
        return email.split('@')[-1].lower()
    return None


def suggest_organization_by_domain(user, organization_type):
    """
    Suggest organizations that match the user's email domain
    
    Args:
        user: User instance
        organization_type: 'institute' or 'company'
    
    Returns:
        QuerySet: Matching organizations
    """
    user_domain = extract_domain_from_email(user.email)
    if not user_domain:
        return None
    
    if organization_type == 'institute':
        return Institute.objects.filter(
            email_domain__iexact=user_domain,
            domain_verified=True
        )
    elif organization_type == 'company':
        return Company.objects.filter(
            email_domain__iexact=user_domain,
            domain_verified=True
        )
    
    return None


def check_domain_verification_status(organization, organization_type):
    """
    Check if an organization has domain verification enabled
    
    Args:
        organization: Institute or Company instance
        organization_type: 'institute' or 'company'
    
    Returns:
        dict: Status information
    """
    return {
        'has_domain': bool(organization.email_domain),
        'is_verified': organization.domain_verified,
        'domain': organization.email_domain,
        'requires_verification': organization.domain_verified and bool(organization.email_domain)
    }
