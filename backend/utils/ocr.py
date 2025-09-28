import pytesseract
from PIL import Image
import io
import os
from typing import Optional

class OCRProcessor:
    def __init__(self):
        # Configure Tesseract path if needed (Windows)
        if os.name == 'nt':  # Windows
            # Common Tesseract installation paths on Windows
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', ''))
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    
    def extract_text_from_image(self, image_data: bytes) -> Optional[str]:
        """Extract text from image using OCR"""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang='eng')
            
            # Clean up the text
            cleaned_text = self._clean_text(text)
            
            return cleaned_text if cleaned_text.strip() else None
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and format extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Join lines with proper spacing
        cleaned = '\n'.join(lines)
        
        # Remove multiple consecutive spaces
        import re
        cleaned = re.sub(r' +', ' ', cleaned)
        
        return cleaned
    
    def validate_medical_report(self, text: str) -> bool:
        """Basic validation to check if text looks like a medical report"""
        if not text or len(text.strip()) < 50:
            return False
        
        # Common medical report keywords
        medical_keywords = [
            'patient', 'diagnosis', 'test', 'result', 'normal', 'abnormal',
            'blood', 'urine', 'x-ray', 'scan', 'report', 'doctor', 'hospital',
            'clinic', 'medical', 'health', 'examination', 'lab', 'laboratory'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in medical_keywords if keyword in text_lower)
        
        # If at least 2 medical keywords found, consider it a medical report
        return keyword_count >= 2

# Global OCR processor instance
ocr_processor = OCRProcessor()