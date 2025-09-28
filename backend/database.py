import sqlite3
import bcrypt
from datetime import datetime
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self, db_path: str = "healthcare.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Reminders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                medicine_name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT NOT NULL,
                time TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, username: str, password: str, email: str = None) -> bool:
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                (username, password_hash, email)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, password_hash, email FROM users WHERE username = ?",
            (username,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
            return {
                "id": user[0],
                "username": user[1],
                "email": user[3]
            }
        return None
    
    def add_reminder(self, user_id: int, medicine_name: str, dosage: str, 
                    frequency: str, time: str) -> bool:
        """Add a new reminder for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO reminders (user_id, medicine_name, dosage, frequency, time) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, medicine_name, dosage, frequency, time)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding reminder: {e}")
            return False
    
    def get_user_reminders(self, user_id: int) -> List[Dict]:
        """Get all active reminders for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, medicine_name, dosage, frequency, time, created_at 
               FROM reminders WHERE user_id = ? AND is_active = TRUE
               ORDER BY time""",
            (user_id,)
        )
        
        reminders = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "medicine_name": r[1],
                "dosage": r[2],
                "frequency": r[3],
                "time": r[4],
                "created_at": r[5]
            }
            for r in reminders
        ]
    
    def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        """Delete a reminder"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE reminders SET is_active = FALSE WHERE id = ? AND user_id = ?",
                (reminder_id, user_id)
            )
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting reminder: {e}")
            return False
    
    def get_all_active_reminders(self) -> List[Dict]:
        """Get all active reminders for email scheduling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT r.id, r.medicine_name, r.dosage, r.frequency, r.time,
                      u.username, u.email
               FROM reminders r
               JOIN users u ON r.user_id = u.id
               WHERE r.is_active = TRUE AND u.email IS NOT NULL"""
        )
        
        reminders = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "medicine_name": r[1],
                "dosage": r[2],
                "frequency": r[3],
                "time": r[4],
                "username": r[5],
                "email": r[6]
            }
            for r in reminders
        ]

# Global database instance
db = Database()