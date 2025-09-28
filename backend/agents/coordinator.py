from crewai import Agent, Task, Crew
from typing import Dict, Any
import re
from utils.llama_api import llama_api

class CoordinatorAgent:
    def __init__(self):
        self.setup_agents()
    
    def setup_agents(self):
        """Setup specialized agents for different healthcare tasks"""
        
        # Import specialized agents
        from agents.report_analyzer import report_analyzer
        from agents.symptom_checker import symptom_checker
        from agents.drug_interaction import drug_interaction_checker
        from agents.chatbot import healthcare_chatbot
        
        self.report_analyzer = report_analyzer
        self.symptom_checker = symptom_checker
        self.drug_interaction_checker = drug_interaction_checker
        self.healthcare_chatbot = healthcare_chatbot
    
    def route_request(self, message: str, context: Dict[str, Any] = None) -> str:
        """Route user request to appropriate agent based on content analysis"""
        
        message_lower = message.lower()
        user_id = context.get('user_id') if context else None
        
        # Check for report analysis request
        if any(keyword in message_lower for keyword in [
            'report', 'test result', 'lab result', 'blood test', 'x-ray', 
            'scan', 'mri', 'ct scan', 'analyze', 'interpretation'
        ]):
            return self._handle_report_analysis(message, context)
        
        # Check for symptom checking request
        elif any(keyword in message_lower for keyword in [
            'symptom', 'pain', 'ache', 'fever', 'headache', 'nausea', 
            'dizzy', 'tired', 'cough', 'sore', 'hurt', 'feel', 'sick'
        ]):
            return self._handle_symptom_check(message)
        
        # Check for drug interaction request
        elif any(keyword in message_lower for keyword in [
            'drug', 'medication', 'medicine', 'pill', 'interaction', 
            'taking', 'prescribed', 'pharmacy', 'side effect', 'can i take'
        ]):
            return self._handle_drug_interaction(message, user_id)
        
        # Default to general healthcare chatbot
        else:
            return self._handle_general_question(message)
    
    def _handle_report_analysis(self, message: str, context: Dict[str, Any] = None) -> str:
        """Handle medical report analysis"""
        
        if context and 'ocr_text' in context:
            # Use OCR text from uploaded image
            ocr_text = context['ocr_text']
            return self.report_analyzer.analyze_report(ocr_text)
        
        else:
            # User is asking about report analysis without uploading
            return """I'd be happy to help analyze your medical report! 
            
Please upload an image of your medical report (JPG or PNG format) by:
- Clicking on the file upload area above, or
- Dragging and dropping the image file

I can analyze various types of medical reports including:
- Blood test results
- Urine analysis
- X-ray reports
- MRI/CT scan reports
- Lab reports

Once you upload the image, I'll extract the text and provide a detailed analysis with explanations in simple terms."""
    
    def _handle_symptom_check(self, message: str) -> str:
        """Handle symptom checking requests"""
        return self.symptom_checker.check_symptoms(message)
    
    def _handle_drug_interaction(self, message: str, user_id: int = None) -> str:
        """Handle drug interaction checking with database access"""
        return self.drug_interaction_checker.check_interactions(message, user_id)
    
    def _handle_general_question(self, message: str) -> str:
        """Handle general healthcare questions"""
        return self.healthcare_chatbot.respond_to_query(message)
    
    def _basic_drug_interaction_response(self, message: str) -> str:
        """Basic drug interaction response when CrewAI fails"""
        
        # Extract potential drug names using simple pattern matching
        drug_patterns = [
            r'\b(aspirin|ibuprofen|acetaminophen|tylenol|advil|motrin)\b',
            r'\b(warfarin|coumadin|heparin)\b',
            r'\b(metformin|insulin|glipizide)\b',
            r'\b(lisinopril|atenolol|amlodipine)\b',
            r'\b(omeprazole|ranitidine|tums)\b'
        ]
        
        found_drugs = []
        message_lower = message.lower()
        
        for pattern in drug_patterns:
            matches = re.findall(pattern, message_lower)
            found_drugs.extend(matches)
        
        if found_drugs:
            return f"""I notice you mentioned: {', '.join(set(found_drugs))}

**Important Drug Safety Information:**

🔍 **General Considerations:**
- Always inform all healthcare providers about ALL medications you're taking
- Keep an updated medication list with you
- Check with your pharmacist before starting new medications
- Be aware of over-the-counter drug interactions

⚠️ **Common Interaction Warnings:**
- Blood thinners (warfarin) interact with many medications
- Pain relievers can affect blood pressure medications
- Some medications should not be taken with certain foods

📞 **When to Contact Healthcare Providers:**
- Before starting any new medication
- If you experience unusual side effects
- If you're taking multiple medications

**Disclaimer:** This is general information only. Always consult your pharmacist or doctor for specific medication advice and interaction checking."""
        
        else:
            return llama_api.answer_healthcare_question(message)

# Global coordinator instance
coordinator = CoordinatorAgent()