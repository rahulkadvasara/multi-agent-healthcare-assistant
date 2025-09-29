"""
Natural language parser for medication reminders
Parses user input like "Add paracetamol, 1 dosage, 1 time, 7:00"
"""

import re
from typing import Dict, Optional, Tuple
from datetime import datetime

class ReminderParser:
    """Parse natural language medication reminder requests"""
    
    def __init__(self):
        # Default values
        self.default_dosage = "1"
        self.default_frequency = "2 times daily"
        self.default_time = "8:00"
        
        # Patterns for parsing
        self.add_patterns = [
            r'add\s+(.+)',
            r'create\s+reminder\s+for\s+(.+)',
            r'set\s+reminder\s+for\s+(.+)',
            r'remind\s+me\s+to\s+take\s+(.+)',
        ]
        
        # Patterns for deleting reminders
        self.delete_patterns = [
            r'delete\s+(.+?)\s+reminder',
            r'remove\s+(.+?)\s+reminder',
            r'cancel\s+(.+?)\s+reminder',
            r'stop\s+(.+?)\s+reminder',
            r'delete\s+reminder\s+for\s+(.+)',
            r'remove\s+reminder\s+for\s+(.+)',
            r'cancel\s+reminder\s+for\s+(.+)',
            r'stop\s+reminder\s+for\s+(.+)',
            r'delete\s+(.+)',
            r'remove\s+(.+)',
        ]
        
        # Patterns for editing reminders
        self.edit_patterns = [
            # Edit specific field patterns
            r'edit\s+(.+?)\s+reminder\s+(time|dosage|frequency)\s+to\s+(.+)',
            r'change\s+(.+?)\s+reminder\s+(time|dosage|frequency)\s+to\s+(.+)',
            r'update\s+(.+?)\s+reminder\s+(time|dosage|frequency)\s+to\s+(.+)',
            r'modify\s+(.+?)\s+reminder\s+(time|dosage|frequency)\s+to\s+(.+)',
            
            # Alternative patterns
            r'edit\s+(.+?)\s+(time|dosage|frequency)\s+to\s+(.+)',
            r'change\s+(.+?)\s+(time|dosage|frequency)\s+to\s+(.+)',
            r'update\s+(.+?)\s+(time|dosage|frequency)\s+to\s+(.+)',
            
            # Set patterns
            r'set\s+(.+?)\s+reminder\s+(time|dosage|frequency)\s+to\s+(.+)',
            r'set\s+(.+?)\s+(time|dosage|frequency)\s+to\s+(.+)',
        ]
        
        # Time patterns
        self.time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',
            r'(\d{1,2})\s*(am|pm)',
            r'at\s+(\d{1,2}):(\d{2})',
            r'at\s+(\d{1,2})\s*(am|pm)',
        ]
        
        # Dosage patterns
        self.dosage_patterns = [
            r'(\d+)\s*(?:tablet|pill|capsule|mg|ml|dose|dosage)s?',
            r'(\d+)\s*(?:x|times?)\s*(?:tablet|pill|capsule|mg|ml|dose|dosage)s?',
            r'(\d+(?:\.\d+)?)\s*(?:mg|ml|g|mcg)',
        ]
        
        # Frequency patterns
        self.frequency_patterns = [
            r'(\d+)\s*(?:time|times)\s*(?:daily|per day|a day)',
            r'(\d+)\s*(?:time|times)',
            r'once\s*(?:daily|per day|a day)',
            r'twice\s*(?:daily|per day|a day)',
            r'three\s*times\s*(?:daily|per day|a day)',
            r'every\s*(\d+)\s*hours?',
        ]
    
    def parse_reminder_request(self, text: str) -> Optional[Dict]:
        """
        Parse a natural language reminder request
        
        Args:
            text: User input like "Add paracetamol, 1 dosage, 1 time, 7:00"
            
        Returns:
            Dictionary with parsed reminder data or None if not a reminder request
        """
        text_lower = text.lower().strip()
        
        # Check if this is a reminder request
        medicine_name = self._extract_medicine_name(text_lower)
        if not medicine_name:
            return None
        
        # Extract components
        dosage = self._extract_dosage(text_lower)
        frequency = self._extract_frequency(text_lower)
        time = self._extract_time(text_lower)
        
        return {
            'medicine_name': medicine_name,
            'dosage': dosage or self.default_dosage,
            'frequency': frequency or self.default_frequency,
            'time': time or self.default_time,
            'raw_input': text
        }
    
    def _extract_medicine_name(self, text: str) -> Optional[str]:
        """Extract medicine name from text"""
        
        # Try different add patterns
        for pattern in self.add_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                remainder = match.group(1).strip()
                
                # Extract medicine name (first word/phrase before comma or dosage info)
                # Split by common separators
                parts = re.split(r'[,;]|\s+(?:\d+|once|twice|three|every|at)', remainder)
                if parts:
                    medicine_name = parts[0].strip()
                    # Clean up common words
                    medicine_name = re.sub(r'\b(?:tablet|pill|capsule|mg|ml|dose|dosage)s?\b', '', medicine_name, flags=re.IGNORECASE)
                    medicine_name = medicine_name.strip()
                    
                    if medicine_name:
                        return medicine_name
        
        return None
    
    def _extract_dosage(self, text: str) -> Optional[str]:
        """Extract dosage information"""
        
        for pattern in self.dosage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dosage_num = match.group(1)
                
                # Try to find the unit in the original match
                full_match = match.group(0)
                if 'mg' in full_match.lower():
                    return f"{dosage_num} mg"
                elif 'ml' in full_match.lower():
                    return f"{dosage_num} ml"
                elif 'mcg' in full_match.lower():
                    return f"{dosage_num} mcg"
                elif 'g' in full_match.lower() and 'mg' not in full_match.lower():
                    return f"{dosage_num} g"
                else:
                    return f"{dosage_num} tablet" if dosage_num == "1" else f"{dosage_num} tablets"
        
        return None
    
    def _extract_frequency(self, text: str) -> Optional[str]:
        """Extract frequency information"""
        
        # Check for specific frequency patterns
        if re.search(r'\bonce\s*(?:daily|per day|a day)', text):
            return "1 time daily"
        elif re.search(r'\btwice\s*(?:daily|per day|a day)', text):
            return "2 times daily"
        elif re.search(r'\bthree\s*times\s*(?:daily|per day|a day)', text):
            return "3 times daily"
        
        # Check for numeric patterns
        for pattern in self.frequency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'every' in pattern:
                    hours = match.group(1)
                    return f"Every {hours} hours"
                else:
                    times = match.group(1)
                    return f"{times} time{'s' if int(times) > 1 else ''} daily"
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time information"""
        
        for pattern in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2 and match.group(2).isdigit():
                    # HH:MM format
                    hour = int(match.group(1))
                    minute = match.group(2)
                    am_pm = match.group(3) if len(match.groups()) >= 3 else None
                    
                    if am_pm:
                        if am_pm.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif am_pm.lower() == 'am' and hour == 12:
                            hour = 0
                    
                    return f"{hour:02d}:{minute}"
                
                elif len(match.groups()) >= 2 and match.group(2):
                    # H AM/PM format
                    hour = int(match.group(1))
                    am_pm = match.group(2).lower()
                    
                    if am_pm == 'pm' and hour != 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                    
                    return f"{hour:02d}:00"
        
        return None
    
    def format_reminder_confirmation(self, reminder_data: Dict) -> str:
        """Format a confirmation message for the parsed reminder"""
        
        return f"""✅ **Medication Reminder Added**

**Medicine:** {reminder_data['medicine_name'].title()}
**Dosage:** {reminder_data['dosage']}
**Frequency:** {reminder_data['frequency']}
**Time:** {reminder_data['time']}

Your reminder has been saved successfully! You'll be notified at the scheduled time.

💡 **Tip:** 
• Check the "⏰ Reminders" tab to see all your medications
• Ask "show my reminders" to view them in chat
• Your reminders are automatically saved to your account"""
    
    def parse_delete_request(self, text: str) -> Optional[str]:
        """
        Parse a delete reminder request
        
        Args:
            text: User input like "delete paracetamol reminder" or "remove aspirin reminder"
            
        Returns:
            Medicine name to delete or None if not a delete request
        """
        text_lower = text.lower().strip()
        
        # Try different delete patterns
        for pattern in self.delete_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                medicine_name = match.group(1).strip()
                
                # Clean up common words
                medicine_name = re.sub(r'\b(?:the|my|reminder|medication|medicine|drug|pill|tablet)s?\b', '', medicine_name, flags=re.IGNORECASE)
                medicine_name = medicine_name.strip()
                
                # Remove extra spaces and clean up
                medicine_name = ' '.join(medicine_name.split())
                
                if medicine_name:
                    return medicine_name
        
        return None
    
    def parse_edit_request(self, text: str) -> Optional[Dict]:
        """
        Parse an edit reminder request
        
        Args:
            text: User input like "edit paracetamol reminder time to 9:00"
            
        Returns:
            Dictionary with medicine_name, field, and new_value or None if not an edit request
        """
        text_lower = text.lower().strip()
        
        # Try different edit patterns
        for pattern in self.edit_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                medicine_name = match.group(1).strip()
                field = match.group(2).strip().lower()
                new_value = match.group(3).strip()
                
                # Clean up medicine name
                medicine_name = re.sub(r'\b(?:the|my|reminder|medication|medicine|drug|pill|tablet)s?\b', '', medicine_name, flags=re.IGNORECASE)
                medicine_name = medicine_name.strip()
                medicine_name = ' '.join(medicine_name.split())
                
                # Validate and normalize field
                if field in ['time', 'dosage', 'frequency']:
                    # Process the new value based on field type
                    if field == 'time':
                        new_value = self._normalize_time(new_value)
                    elif field == 'dosage':
                        new_value = self._normalize_dosage(new_value)
                    elif field == 'frequency':
                        new_value = self._normalize_frequency(new_value)
                    
                    if medicine_name and new_value:
                        return {
                            'medicine_name': medicine_name,
                            'field': field,
                            'new_value': new_value,
                            'raw_input': text
                        }
        
        return None
    
    def _normalize_time(self, time_str: str) -> str:
        """Normalize time input"""
        # Use existing time extraction logic
        normalized = self._extract_time(f"at {time_str}")
        return normalized if normalized else time_str
    
    def _normalize_dosage(self, dosage_str: str) -> str:
        """Normalize dosage input"""
        # Use existing dosage extraction logic
        normalized = self._extract_dosage(dosage_str)
        return normalized if normalized else dosage_str
    
    def _normalize_frequency(self, frequency_str: str) -> str:
        """Normalize frequency input"""
        # Use existing frequency extraction logic
        normalized = self._extract_frequency(frequency_str)
        return normalized if normalized else frequency_str
    
    def format_delete_confirmation(self, medicine_name: str, success: bool, found_reminders: int = 0) -> str:
        """
        Format a confirmation message for deleting a reminder
        
        Args:
            medicine_name: Name of the medicine
            success: Whether the deletion was successful
            found_reminders: Number of reminders found for this medicine
            
        Returns:
            Formatted confirmation message
        """
        
        if success and found_reminders > 0:
            plural = "reminder" if found_reminders == 1 else "reminders"
            return f"""✅ **Reminder Deleted Successfully**

**Medicine:** {medicine_name.title()}
**Deleted:** {found_reminders} {plural}

Your {medicine_name.title()} reminder{'s' if found_reminders > 1 else ''} ha{'ve' if found_reminders > 1 else 's'} been removed from your medication schedule.

💡 **Tip:** 
• Check the "⏰ Reminders" tab to see your updated medication list
• Ask "show my reminders" to view remaining medications
• You can add it back anytime by saying "Add {medicine_name.title()}...\""""
        
        elif found_reminders == 0:
            return f"""❌ **Reminder Not Found**

**Medicine:** {medicine_name.title()}

No reminders found for {medicine_name.title()}. 

💡 **Possible reasons:**
• The medicine name might be spelled differently
• The reminder might already be deleted
• Try asking "show my reminders" to see your current medications

**Tip:** Medicine names are case-insensitive, but spelling must match exactly."""
        
        else:
            return f"""❌ **Error Deleting Reminder**

**Medicine:** {medicine_name.title()}

Sorry, there was an error deleting your reminder. Please try again or contact support if the problem persists.

💡 **You can also:**
• Try deleting from the "⏰ Reminders" tab
• Ask "show my reminders" to verify current medications"""
    
    def format_edit_confirmation(self, medicine_name: str, field: str, old_value: str, new_value: str, success: bool, found_reminders: int = 0) -> str:
        """
        Format a confirmation message for editing a reminder
        
        Args:
            medicine_name: Name of the medicine
            field: Field that was edited (time, dosage, frequency)
            old_value: Previous value
            new_value: New value
            success: Whether the edit was successful
            found_reminders: Number of reminders found for this medicine
            
        Returns:
            Formatted confirmation message
        """
        
        field_display = {
            'time': 'Time',
            'dosage': 'Dosage', 
            'frequency': 'Frequency'
        }
        
        if success and found_reminders > 0:
            plural = "reminder" if found_reminders == 1 else "reminders"
            return f"""✅ **Reminder Updated Successfully**

**Medicine:** {medicine_name.title()}
**Field Changed:** {field_display.get(field, field.title())}
**Previous Value:** {old_value}
**New Value:** {new_value}
**Updated:** {found_reminders} {plural}

Your {medicine_name.title()} reminder{'s' if found_reminders > 1 else ''} ha{'ve' if found_reminders > 1 else 's'} been updated successfully.

💡 **Tip:** 
• Check the "⏰ Reminders" tab to see your updated medication schedule
• Ask "show my reminders" to view all current medications
• You can edit other fields by saying "edit {medicine_name.title()} [field] to [new value]\""""
        
        elif found_reminders == 0:
            return f"""❌ **Reminder Not Found**

**Medicine:** {medicine_name.title()}

No reminders found for {medicine_name.title()}. 

💡 **Possible reasons:**
• The medicine name might be spelled differently
• The reminder might have been deleted
• Try asking "show my reminders" to see your current medications

**Tip:** You can add a new reminder by saying "Add {medicine_name.title()}...\""""
        
        else:
            return f"""❌ **Error Updating Reminder**

**Medicine:** {medicine_name.title()}
**Field:** {field_display.get(field, field.title())}
**New Value:** {new_value}

Sorry, there was an error updating your reminder. Please try again or contact support if the problem persists.

💡 **You can also:**
• Try editing from the "⏰ Reminders" tab
• Delete and re-add the reminder with new values"""

def test_parser():
    """Test the reminder parser with various inputs"""
    
    parser = ReminderParser()
    
    test_cases = [
        "Add paracetamol, 1 dosage, 1 time, 7:00",
        "add aspirin 100mg twice daily at 8:00 am",
        "Create reminder for metformin 500mg, 2 times daily, 9:00",
        "Set reminder for vitamin D once daily",
        "Remind me to take ibuprofen 200mg every 6 hours",
        "add insulin 10 units at 7:30 pm",
        "Not a reminder request",
    ]
    
    print("🧪 Testing Reminder Parser")
    print("=" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Input: \"{test_case}\"")
        result = parser.parse_reminder_request(test_case)
        
        if result:
            print("✅ Parsed successfully:")
            for key, value in result.items():
                if key != 'raw_input':
                    print(f"   {key}: {value}")
        else:
            print("❌ Not recognized as reminder request")

if __name__ == "__main__":
    test_parser()