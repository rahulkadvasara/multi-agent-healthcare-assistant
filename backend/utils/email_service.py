import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_pass = os.getenv("EMAIL_PASS")
    
    def send_reminder_email(self, to_email: str, username: str, 
                           medicine_name: str, dosage: str, time: str) -> bool:
        """Send medication reminder email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = f"Medication Reminder: {medicine_name}"
            
            # Email body
            body = f"""
            Hello {username},
            
            This is a friendly reminder to take your medication:
            
            💊 Medicine: {medicine_name}
            📏 Dosage: {dosage}
            ⏰ Time: {time}
            
            Please take your medication as prescribed by your healthcare provider.
            
            Stay healthy!
            
            ---
            Healthcare Support System
            This is an automated reminder. Please do not reply to this email.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            print(f"Reminder email sent to {to_email} for {medicine_name}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """Send test email to verify configuration"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = "Healthcare System - Email Configuration Test"
            
            body = """
            Hello!
            
            This is a test email to verify your email configuration is working correctly.
            
            If you received this email, your healthcare reminder system is ready to send notifications.
            
            Best regards,
            Healthcare Support System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send test email: {e}")
            return False

# Global email service instance
email_service = EmailService()