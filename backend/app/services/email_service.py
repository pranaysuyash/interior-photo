"""
Email Service for Interior AI

Supports multiple providers:
- SendGrid
- Mailgun
- AWS SES
- SMTP

Handles:
- Welcome emails
- Email verification
- Password reset
- Transformation completion notifications
- Subscription updates
"""

import os
from typing import Optional, List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Email service with multiple provider support"""

    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "smtp")  # smtp, sendgrid, mailgun, ses
        self.from_email = os.getenv("FROM_EMAIL", "noreply@interior-ai.com")
        self.from_name = os.getenv("FROM_NAME", "Interior AI")

        # SMTP Configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

        # SendGrid
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")

        # Mailgun
        self.mailgun_api_key = os.getenv("MAILGUN_API_KEY", "")
        self.mailgun_domain = os.getenv("MAILGUN_DOMAIN", "")

        # AWS SES
        self.aws_region = os.getenv("AWS_SES_REGION", "us-east-1")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email using configured provider"""

        try:
            if self.provider == "sendgrid":
                return self._send_via_sendgrid(to_email, subject, html_content, text_content)
            elif self.provider == "mailgun":
                return self._send_via_mailgun(to_email, subject, html_content, text_content)
            elif self.provider == "ses":
                return self._send_via_ses(to_email, subject, html_content, text_content)
            else:
                return self._send_via_smtp(to_email, subject, html_content, text_content, cc, bcc)
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email via SMTP"""

        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = ', '.join(cc)
        if bcc:
            msg['Bcc'] = ', '.join(bcc)

        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            server.sendmail(self.from_email, recipients, msg.as_string())

        logger.info(f"Email sent via SMTP to {to_email}")
        return True

    def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str]
    ) -> bool:
        """Send email via SendGrid"""

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )

            if text_content:
                message.plain_text_content = text_content

            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)

            logger.info(f"Email sent via SendGrid to {to_email}, status: {response.status_code}")
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False

    def _send_via_mailgun(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str]
    ) -> bool:
        """Send email via Mailgun"""

        try:
            import requests

            url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"

            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_content
            }

            if text_content:
                data["text"] = text_content

            response = requests.post(
                url,
                auth=("api", self.mailgun_api_key),
                data=data
            )

            logger.info(f"Email sent via Mailgun to {to_email}, status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Mailgun error: {e}")
            return False

    def _send_via_ses(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str]
    ) -> bool:
        """Send email via AWS SES"""

        try:
            import boto3

            client = boto3.client('ses', region_name=self.aws_region)

            message = {
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': html_content}}
            }

            if text_content:
                message['Body']['Text'] = {'Data': text_content}

            response = client.send_email(
                Source=f"{self.from_name} <{self.from_email}>",
                Destination={'ToAddresses': [to_email]},
                Message=message
            )

            logger.info(f"Email sent via SES to {to_email}, MessageId: {response['MessageId']}")
            return True
        except Exception as e:
            logger.error(f"SES error: {e}")
            return False

    # Templated emails

    def send_welcome_email(self, to_email: str, name: str) -> bool:
        """Send welcome email to new user"""

        subject = "Welcome to Interior AI! 🎨"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Interior AI!</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>

                    <p>Thank you for joining Interior AI! We're excited to help you transform your space with AI-powered interior design.</p>

                    <p><strong>Here's what you can do:</strong></p>
                    <ul>
                        <li>Upload photos of any room</li>
                        <li>Choose from 8 different design vibes</li>
                        <li>Select your preferred color palette</li>
                        <li>Add reference images for inspiration</li>
                        <li>Get AI-generated transformations in minutes</li>
                    </ul>

                    <p>You've been credited with <strong>5 free transformations</strong> to get started!</p>

                    <a href="https://interior-ai.com/dashboard" class="button">Start Transforming</a>

                    <p>Need help? Check out our <a href="https://interior-ai.com/docs">documentation</a> or reply to this email.</p>

                    <p>Happy designing!<br>The Interior AI Team</p>
                </div>
                <div class="footer">
                    <p>Interior AI - Transform Your Space with AI</p>
                    <p>If you didn't sign up for this account, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Interior AI!

        Hi {name},

        Thank you for joining Interior AI! We're excited to help you transform your space with AI-powered interior design.

        You've been credited with 5 free transformations to get started!

        Visit https://interior-ai.com/dashboard to start transforming your space.

        Happy designing!
        The Interior AI Team
        """

        return self.send_email(to_email, subject, html_content, text_content)

    def send_verification_email(self, to_email: str, name: str, verification_token: str) -> bool:
        """Send email verification"""

        verification_url = f"https://interior-ai.com/verify-email?token={verification_token}"

        subject = "Verify your Interior AI email address"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verify Your Email</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>

                    <p>Thanks for signing up! Please verify your email address to activate your Interior AI account.</p>

                    <a href="{verification_url}" class="button">Verify Email Address</a>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="background: #fff; padding: 10px; border-radius: 5px; word-break: break-all;">{verification_url}</p>

                    <p>This link will expire in 24 hours.</p>

                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>Interior AI - Transform Your Space with AI</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_content)

    def send_password_reset_email(self, to_email: str, name: str, reset_token: str) -> bool:
        """Send password reset email"""

        reset_url = f"https://interior-ai.com/reset-password?token={reset_token}"

        subject = "Reset your Interior AI password"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Reset Your Password</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>

                    <p>We received a request to reset your Interior AI password. Click the button below to create a new password:</p>

                    <a href="{reset_url}" class="button">Reset Password</a>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="background: #fff; padding: 10px; border-radius: 5px; word-break: break-all;">{reset_url}</p>

                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong> This link will expire in 1 hour. If you didn't request a password reset, please ignore this email and ensure your account is secure.
                    </div>

                    <p>For security reasons, we cannot tell you your current password. But you can always create a new one!</p>
                </div>
                <div class="footer">
                    <p>Interior AI - Transform Your Space with AI</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_content)

    def send_transformation_complete_email(
        self,
        to_email: str,
        name: str,
        transformation_id: str,
        original_url: str,
        transformed_url: str
    ) -> bool:
        """Send notification when transformation is complete"""

        view_url = f"https://interior-ai.com/transformations/{transformation_id}"

        subject = "Your interior transformation is ready! ✨"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .images {{ display: flex; gap: 10px; margin: 20px 0; }}
                .image-box {{ flex: 1; text-align: center; }}
                .image-box img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Transformation is Ready!</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>

                    <p>Great news! Your interior design transformation is complete. Check out the stunning results:</p>

                    <div class="images">
                        <div class="image-box">
                            <p><strong>Before</strong></p>
                            <img src="{original_url}" alt="Before">
                        </div>
                        <div class="image-box">
                            <p><strong>After</strong></p>
                            <img src="{transformed_url}" alt="After">
                        </div>
                    </div>

                    <a href="{view_url}" class="button">View Full Transformation</a>

                    <p><strong>What's next?</strong></p>
                    <ul>
                        <li>Download your transformed image</li>
                        <li>Share it with friends and family</li>
                        <li>Try different styles on the same room</li>
                        <li>Transform more spaces!</li>
                    </ul>

                    <p>Love the result? Create more transformations and bring your vision to life!</p>

                    <p>Happy designing!<br>The Interior AI Team</p>
                </div>
                <div class="footer">
                    <p>Interior AI - Transform Your Space with AI</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_content)


# Global instance
email_service = EmailService()
