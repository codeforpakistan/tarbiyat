"""
Email utilities for Tarbiyat platform using SendGrid
"""

import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, From, Subject, PlainTextContent, HtmlContent

logger = logging.getLogger(__name__)


class EmailService:
    """Email service class for sending various types of emails"""
    
    def __init__(self):
        self.sendgrid_client = None
        if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
            try:
                self.sendgrid_client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize SendGrid client: {e}")
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: Optional[str] = None,
        plain_content: Optional[str] = None,
        from_email: Optional[str] = None,
        template_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send email using SendGrid or Django's email backend as fallback
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML content of the email (optional if using template)
            plain_content: Plain text content (optional, will be generated from HTML if not provided)
            from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL if not provided)
            template_name: Django template name for rendering content (optional)
            context: Context for template rendering (optional)
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        
        try:
            # Use template if provided
            if template_name and context:
                html_content = render_to_string(template_name, context)
            
            # If no HTML content is provided, we can't send the email
            if not html_content:
                logger.error("No HTML content or template provided for email")
                return False
            
            # Generate plain text from HTML if not provided
            if not plain_content:
                plain_content = strip_tags(html_content)
            
            # Set default from email
            if not from_email:
                from_email = settings.DEFAULT_FROM_EMAIL
            
            # Try SendGrid first if available
            if self.sendgrid_client:
                success = self._send_with_sendgrid(to_emails, subject, html_content, plain_content, from_email)
                if success:
                    return True
                else:
                    logger.warning("SendGrid failed, falling back to Django email backend")
                    # Fall through to Django backend
            
            # Use Django's email backend (either as fallback or primary)
            return self._send_with_django(to_emails, subject, html_content, plain_content, from_email)
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _send_with_sendgrid(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        plain_content: str,
        from_email: str
    ) -> bool:
        """Send email using SendGrid API"""
        try:
            message = Mail()
            message.from_email = From(from_email)
            message.subject = Subject(subject)
            
            # Add recipients
            for email in to_emails:
                message.add_to(To(email))
            
            # Add content
            message.add_content(PlainTextContent(plain_content))
            message.add_content(HtmlContent(html_content))
            
            # Send the email
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 202]:
                logger.info(f"Email sent successfully via SendGrid to {to_emails}")
                return True
            else:
                logger.error(f"SendGrid returned status code {response.status_code}: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid email sending failed: {e}")
            # Log more details for debugging
            logger.error(f"From email: {from_email}")
            logger.error(f"To emails: {to_emails}")
            logger.error(f"Subject: {subject}")
            return False
    
    def _send_with_django(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        plain_content: str,
        from_email: str
    ) -> bool:
        """Send email using Django's email backend"""
        try:
            from django.core.mail import EmailMultiAlternatives
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_content,
                from_email=from_email,
                to=to_emails
            )
            msg.attach_alternative(html_content, "text/html")
            
            result = msg.send()
            if result:
                logger.info(f"Email sent successfully via Django backend to {to_emails}")
                return True
            else:
                logger.error("Django email backend failed to send email")
                return False
                
        except Exception as e:
            logger.error(f"Django email sending failed: {e}")
            return False


# Global email service instance
email_service = EmailService()


def send_welcome_email(user_email: str, user_name: str) -> bool:
    """Send welcome email to new users"""
    context = {
        'user_name': user_name,
        'platform_name': 'Tarbiyat',
        'login_url': 'https://tarbiyat.pk/accounts/login/',
    }
    
    return email_service.send_email(
        to_emails=[user_email],
        subject='Welcome to Tarbiyat - Government Internship Platform',
        template_name='emails/welcome_email.html',
        context=context
    )


def send_profile_approval_email(user_email: str, user_name: str, organization_name: str) -> bool:
    """Send email when user's organization membership is approved"""
    context = {
        'user_name': user_name,
        'organization_name': organization_name,
        'platform_name': 'Tarbiyat',
        'dashboard_url': 'https://tarbiyat.pk/',
    }
    
    return email_service.send_email(
        to_emails=[user_email],
        subject=f'Your membership to {organization_name} has been approved',
        template_name='emails/profile_approval_email.html',
        context=context
    )


def send_application_status_email(
    user_email: str,
    user_name: str,
    position_title: str,
    company_name: str,
    status: str
) -> bool:
    """Send email when internship application status changes"""
    status_messages = {
        'approved': 'Congratulations! Your application has been approved',
        'rejected': 'Update on your internship application',
        'interview_scheduled': 'Interview scheduled for your internship application',
        'under_review': 'Your application is now under review',
    }
    
    context = {
        'user_name': user_name,
        'position_title': position_title,
        'company_name': company_name,
        'status': status,
        'status_message': status_messages.get(status, 'Your application status has been updated'),
        'platform_name': 'Tarbiyat',
        'applications_url': 'https://tarbiyat.pk/student/applications/',
    }
    
    return email_service.send_email(
        to_emails=[user_email],
        subject=f'Internship Application Update - {position_title}',
        template_name='emails/application_status_email.html',
        context=context
    )


def send_interview_notification_email(
    user_email: str,
    user_name: str,
    position_title: str,
    company_name: str,
    interview_date: str,
    interview_location: str
) -> bool:
    """Send email when interview is scheduled"""
    context = {
        'user_name': user_name,
        'position_title': position_title,
        'company_name': company_name,
        'interview_date': interview_date,
        'interview_location': interview_location,
        'platform_name': 'Tarbiyat',
        'interviews_url': 'https://tarbiyat.pk/student/interviews/',
    }
    
    return email_service.send_email(
        to_emails=[user_email],
        subject=f'Interview Scheduled - {position_title} at {company_name}',
        template_name='emails/interview_notification_email.html',
        context=context
    )


def send_organization_approval_notification(
    admin_emails: List[str],
    organization_type: str,
    organization_name: str,
    requested_by: str
) -> bool:
    """Send notification to officials when new organization registration is submitted"""
    context = {
        'organization_type': organization_type,
        'organization_name': organization_name,
        'requested_by': requested_by,
        'platform_name': 'Tarbiyat',
        'review_url': 'https://tarbiyat.pk/official/organizations/',
    }
    
    return email_service.send_email(
        to_emails=admin_emails,
        subject=f'New {organization_type.title()} Registration Pending Review',
        template_name='emails/organization_approval_notification.html',
        context=context
    )


def send_report_reminder_email(
    user_email: str,
    user_name: str,
    report_type: str,
    due_date: str
) -> bool:
    """Send reminder email for pending reports"""
    context = {
        'user_name': user_name,
        'report_type': report_type,
        'due_date': due_date,
        'platform_name': 'Tarbiyat',
        'reports_url': 'https://tarbiyat.pk/reports/',
    }
    
    return email_service.send_email(
        to_emails=[user_email],
        subject=f'Reminder: {report_type} Report Due {due_date}',
        template_name='emails/report_reminder_email.html',
        context=context
    )
