from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
import atexit
from database import db
from utils.email_service import email_service

class ReminderScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Schedule reminder checks every minute
        self.scheduler.add_job(
            func=self.check_and_send_reminders,
            trigger=CronTrigger(second=0),  # Run every minute at 0 seconds
            id='reminder_checker',
            name='Check and send medication reminders',
            replace_existing=True
        )
        
        # Ensure scheduler shuts down when app exits
        atexit.register(lambda: self.scheduler.shutdown())
    
    def check_and_send_reminders(self):
        """Check for due reminders and send emails"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            current_day = datetime.now().strftime("%A").lower()
            
            # Get all active reminders
            reminders = db.get_all_active_reminders()
            
            for reminder in reminders:
                if self.should_send_reminder(reminder, current_time, current_day):
                    self.send_reminder_email(reminder)
                    
        except Exception as e:
            print(f"Error in reminder scheduler: {e}")
    
    def should_send_reminder(self, reminder, current_time, current_day):
        """Determine if a reminder should be sent now"""
        reminder_time = reminder['time']
        frequency = reminder['frequency'].lower()
        
        # Check if current time matches reminder time (within 1 minute)
        if reminder_time != current_time:
            return False
        
        # For simplicity, we'll send daily reminders
        # In a production system, you'd want more sophisticated frequency handling
        if frequency in ['once daily', 'twice daily', 'three times daily', 'four times daily']:
            return True
        
        return False
    
    def send_reminder_email(self, reminder):
        """Send reminder email to user"""
        try:
            if not reminder['email']:
                print(f"No email address for user {reminder['username']}")
                return
            
            success = email_service.send_reminder_email(
                to_email=reminder['email'],
                username=reminder['username'],
                medicine_name=reminder['medicine_name'],
                dosage=reminder['dosage'],
                time=reminder['time']
            )
            
            if success:
                print(f"Reminder sent to {reminder['username']} for {reminder['medicine_name']}")
            else:
                print(f"Failed to send reminder to {reminder['username']}")
                
        except Exception as e:
            print(f"Error sending reminder email: {e}")
    
    def add_custom_reminder(self, user_id, medicine_name, dosage, frequency, time_str):
        """Add a custom scheduled reminder (for future enhancement)"""
        # This could be used for more complex scheduling in the future
        pass
    
    def remove_reminder_job(self, reminder_id):
        """Remove a specific reminder job (for future enhancement)"""
        job_id = f"reminder_{reminder_id}"
        try:
            self.scheduler.remove_job(job_id)
        except:
            pass  # Job might not exist
    
    def get_scheduler_status(self):
        """Get scheduler status for debugging"""
        return {
            'running': self.scheduler.running,
            'jobs': len(self.scheduler.get_jobs()),
            'next_run': str(self.scheduler.get_jobs()[0].next_run_time) if self.scheduler.get_jobs() else None
        }

# Global scheduler instance
reminder_scheduler = ReminderScheduler()