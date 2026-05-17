import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending emails via SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM
    
    def send_email(self, to_email: str, subject: str, body: str, html: bool = False):
        """Send email to a recipient"""
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.from_email
            message['To'] = to_email
            
            # Attach body
            if html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_otp_email(self, to_email: str, otp: str):
        """Send OTP verification email"""
        subject = "Verify Your Email - Homeezy"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <h2 style="color: #2563eb; margin-bottom: 20px;">Email Verification</h2>
              <p style="color: #374151; font-size: 16px;">Thank you for registering with Homeezy!</p>
              <p style="color: #374151; font-size: 16px;">Your verification code is:</p>
              <div style="background-color: #eff6ff; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <h1 style="color: #2563eb; font-size: 36px; margin: 0; letter-spacing: 8px;">{otp}</h1>
              </div>
              <p style="color: #6b7280; font-size: 14px;">This code will expire in 10 minutes.</p>
              <p style="color: #6b7280; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                © 2025 Homeezy. All rights reserved.
              </p>
            </div>
          </body>
        </html>
        """
        return self.send_email(to_email, subject, body, html=True)
    
    def send_welcome_email(self, to_email: str, name: str, role: str):
        """Send welcome email after successful registration"""
        subject = "Welcome to Homeezy!"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <h2 style="color: #2563eb; margin-bottom: 20px;">Welcome to Homeezy, {name}! 🎉</h2>
              <p style="color: #374151; font-size: 16px;">
                Thank you for joining Homeezy as a <strong>{role.capitalize()}</strong>.
              </p>
              <p style="color: #374151; font-size: 16px;">
                You're now part of India's most trusted home services platform!
              </p>
              <div style="margin: 30px 0;">
                <a href="https://homeezy.com/login" style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                  Get Started
                </a>
              </div>
              <p style="color: #6b7280; font-size: 14px;">
                If you have any questions, feel free to reach out to our support team at support@homeezy.com
              </p>
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                © 2025 Homeezy. All rights reserved.
              </p>
            </div>
          </body>
        </html>
        """
        return self.send_email(to_email, subject, body, html=True)
    
    def send_booking_notification(self, to_email: str, booking_id: str, service: str):
        """Send booking confirmation email"""
        subject = f"Booking Confirmed - {service}"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <h2 style="color: #10b981; margin-bottom: 20px;">Booking Confirmed ✓</h2>
              <p style="color: #374151; font-size: 16px;">
                Your booking for <strong>{service}</strong> has been confirmed!
              </p>
              <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Booking ID:</strong> {booking_id}</p>
                <p style="margin: 5px 0;"><strong>Service:</strong> {service}</p>
              </div>
              <p style="color: #374151; font-size: 16px;">
                We're matching you with the best professionals. You'll receive an update shortly!
              </p>
              <div style="margin: 30px 0;">
                <a href="https://homeezy.com/booking/{booking_id}" style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                  View Booking
                </a>
              </div>
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                © 2025 Homeezy. All rights reserved.
              </p>
            </div>
          </body>
        </html>
        """
        return self.send_email(to_email, subject, body, html=True)
    
    def send_worker_approved_email(self, to_email: str, name: str):
        """Send email when worker is approved by admin"""
        subject = "Your Homeezy Application is Approved! 🎉"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <h2 style="color: #10b981; margin-bottom: 20px;">Congratulations, {name}! 🎉</h2>
              <p style="color: #374151; font-size: 16px;">
                Your application to become a Homeezy professional has been <strong>APPROVED</strong>!
              </p>
              <p style="color: #374151; font-size: 16px;">
                You can now start receiving booking requests and earning with Homeezy.
              </p>
              <div style="background-color: #d1fae5; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
                <p style="color: #065f46; margin: 0;">
                  <strong>Next Steps:</strong><br>
                  1. Log in to your dashboard<br>
                  2. Set your availability<br>
                  3. Start accepting bookings!
                </p>
              </div>
              <div style="margin: 30px 0;">
                <a href="https://homeezy.com/worker/dashboard" style="background-color: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                  Go to Dashboard
                </a>
              </div>
              <p style="color: #6b7280; font-size: 14px;">
                Welcome to the Homeezy family! 🏠
              </p>
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                © 2025 Homeezy. All rights reserved.
              </p>
            </div>
          </body>
        </html>
        """
        return self.send_email(to_email, subject, body, html=True)
    
    def send_payment_receipt(self, to_email: str, booking_id: str, amount: float):
        """Send payment receipt email"""
        subject = f"Payment Receipt - Booking #{booking_id}"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <h2 style="color: #2563eb; margin-bottom: 20px;">Payment Receipt</h2>
              <p style="color: #374151; font-size: 16px;">
                Thank you for your payment!
              </p>
              <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Booking ID:</strong> {booking_id}</p>
                <p style="margin: 5px 0;"><strong>Amount Paid:</strong> ₹{amount:.2f}</p>
                <p style="margin: 5px 0;"><strong>Payment Status:</strong> <span style="color: #10b981;">Success</span></p>
              </div>
              <p style="color: #374151; font-size: 16px;">
                This is your payment receipt for the above booking. Keep it for your records.
              </p>
              <p style="color: #6b7280; font-size: 14px;">
                For any queries regarding this payment, please contact us at payments@homeezy.com
              </p>
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                © 2025 Homeezy. All rights reserved.
              </p>
            </div>
          </body>
        </html>
        """
        return self.send_email(to_email, subject, body, html=True)
    
    def send_password_reset_email(self, to_email: str, reset_token: str):
        """Send password reset email"""
        reset_link = f"https://homeezy.com/reset-password?token={reset_token}"
        subject = "Reset Your Password - Homeezy"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
              <h2 style="color: #2563eb; margin-bottom: 20px;">Reset Your Password</h2>
              <p style="color: #374151; font-size: 16px;">
                We received a request to reset your password. Click the button below to reset it:
              </p>
              <div style="margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                  Reset Password
                </a>
              </div>
              <p style="color: #6b7280; font-size: 14px;">
                This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.
              </p>
              <p style="color: #9ca3af; font-size: 12px; margin-top: 20px;">
                Or copy and paste this URL into your browser:<br>
                {reset_link}
              </p>
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                © 2025 Homeezy. All rights reserved.
              </p>
            </div>
          </body>
        </html>
        """
        return self.send_email(to_email, subject, body, html=True)