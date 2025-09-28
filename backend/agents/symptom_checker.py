from utils.llama_api import llama_api
from typing import Optional, List, Dict

class SymptomChecker:
    """Specialized agent for symptom analysis and triage"""
    
    def __init__(self):
        self.agent_name = "Symptom Assessment Specialist"
        self.emergency_keywords = [
            'chest pain', 'difficulty breathing', 'shortness of breath',
            'severe headache', 'confusion', 'loss of consciousness',
            'severe bleeding', 'severe burns', 'poisoning',
            'severe allergic reaction', 'stroke symptoms',
            'heart attack', 'seizure', 'suicide'
        ]
    
    def check_symptoms(self, symptoms: str) -> Optional[str]:
        """Analyze symptoms and provide assessment"""
        
        # Check for emergency symptoms first
        if self._is_emergency(symptoms):
            return self._emergency_response()
        
        # Use LLaMA API for detailed analysis
        analysis = llama_api.check_symptoms(symptoms)
        
        if analysis:
            return self._format_symptom_analysis(analysis, symptoms)
        else:
            return self._fallback_symptom_analysis(symptoms)
    
    def _is_emergency(self, symptoms: str) -> bool:
        """Check if symptoms indicate emergency situation"""
        symptoms_lower = symptoms.lower()
        return any(keyword in symptoms_lower for keyword in self.emergency_keywords)
    
    def _emergency_response(self) -> str:
        """Provide emergency response guidance"""
        return """
## 🚨 EMERGENCY ALERT

**Your symptoms may indicate a medical emergency.**

**IMMEDIATE ACTION REQUIRED:**
- Call emergency services (911) immediately
- Do not drive yourself to the hospital
- If possible, have someone stay with you
- Bring a list of your medications

**Do not wait or try to self-treat these symptoms.**

---

**Emergency Warning Signs Include:**
- Chest pain or pressure
- Difficulty breathing
- Severe headache with confusion
- Loss of consciousness
- Severe bleeding
- Signs of stroke (face drooping, arm weakness, speech difficulty)
- Severe allergic reactions

**This is not a substitute for emergency medical care. Seek immediate professional help.**
"""
    
    def _format_symptom_analysis(self, analysis: str, original_symptoms: str) -> str:
        """Format symptom analysis with proper structure"""
        
        return f"""
## 🩺 Symptom Analysis

**Your Symptoms:**
{original_symptoms}

**AI Assessment:**
{analysis}

---

**General Recommendations:**
- Monitor your symptoms closely
- Keep a symptom diary with dates and severity
- Stay hydrated and get adequate rest
- Contact your healthcare provider if symptoms worsen

**When to Seek Medical Care:**
- Symptoms persist or worsen
- You develop new concerning symptoms
- You have underlying health conditions
- You're unsure about the severity

**⚠️ Important Reminder:**
This assessment is for informational purposes only and cannot replace professional medical evaluation. When in doubt, consult with a healthcare provider.
"""
    
    def _fallback_symptom_analysis(self, symptoms: str) -> str:
        """Provide basic symptom guidance when AI fails"""
        
        # Basic symptom categorization
        common_symptoms = {
            'respiratory': ['cough', 'congestion', 'runny nose', 'sore throat'],
            'gastrointestinal': ['nausea', 'vomiting', 'diarrhea', 'stomach pain'],
            'musculoskeletal': ['muscle pain', 'joint pain', 'back pain', 'stiffness'],
            'neurological': ['headache', 'dizziness', 'fatigue', 'weakness'],
            'dermatological': ['rash', 'itching', 'swelling', 'redness']
        }
        
        symptoms_lower = symptoms.lower()
        detected_categories = []
        
        for category, symptom_list in common_symptoms.items():
            if any(symptom in symptoms_lower for symptom in symptom_list):
                detected_categories.append(category)
        
        return f"""
## 🩺 Symptom Analysis

**Your Symptoms:**
{symptoms}

**Detected Categories:**
{', '.join(detected_categories).title() if detected_categories else 'General symptoms'}

**General Guidance:**
- Rest and stay hydrated
- Monitor symptom progression
- Consider over-the-counter remedies for minor symptoms
- Maintain good hygiene to prevent spread if infectious

**When to Contact Healthcare Provider:**
- Symptoms persist beyond expected timeframe
- Symptoms worsen significantly
- You develop fever or other concerning signs
- You have chronic conditions that may be affected

**Red Flag Symptoms (Seek Immediate Care):**
- High fever (>101.3°F/38.5°C)
- Difficulty breathing
- Severe pain
- Signs of dehydration
- Persistent vomiting

**⚠️ Disclaimer:**
This is general information only. For proper diagnosis and treatment, please consult with a qualified healthcare professional.
"""

# Global instance
symptom_checker = SymptomChecker()