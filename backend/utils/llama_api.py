import os
from dotenv import load_dotenv
from typing import Optional

# Try to import Groq, but handle if it fails
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Groq not available: {e}")
    GROQ_AVAILABLE = False
    Groq = None

load_dotenv()

class LlamaAPI:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key.startswith("gsk_your_"):
            print("Warning: GROQ_API_KEY not configured properly")
            self.client = None
            self.model = None
        else:
            try:
                # Try different initialization approaches
                self.client = Groq(api_key=api_key)
                self.model = "llama-3.3-70b-versatile"  # Using available LLaMA model
                print("✅ Groq client initialized successfully")
            except TypeError as e:
                if "proxies" in str(e):
                    print("⚠️  Groq version compatibility issue. Using fallback mode.")
                    self.client = None
                    self.model = None
                else:
                    print(f"Error initializing Groq client: {e}")
                    self.client = None
                    self.model = None
            except Exception as e:
                print(f"Error initializing Groq client: {e}")
                self.client = None
                self.model = None
    
    def generate_response(self, prompt: str, system_message: str = None, 
                         max_tokens: int = 1000) -> Optional[str]:
        """Generate response using LLaMA via GroqCloud"""
        if not self.client:
            return self._fallback_response(prompt, system_message)
            
        try:
            messages = []
            
            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                timeout=30  # 30 second timeout
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                print(f"Request timed out: {e}")
                return self._timeout_fallback_response(prompt, system_message)
            else:
                print(f"Error generating LLaMA response: {e}")
                return self._fallback_response(prompt, system_message)
    
    def analyze_medical_report(self, ocr_text: str) -> Optional[str]:
        """Analyze medical report text"""
        system_message = """You are a medical report analyzer. Analyze the provided medical report text and provide a comprehensive summary in simple, easy-to-understand language. Include:
        1. Key findings and what they mean
        2. Important values and their significance in plain terms
        3. Any abnormalities or areas of concern
        4. What the results suggest about health status
        5. General recommendations
        
        Write 5-6 sentences that explain the report in layman's terms. Be clear and informative without medical jargon."""
        
        prompt = f"Please analyze this medical report and explain it in simple terms:\n\n{ocr_text}"
        
        return self.generate_response(prompt, system_message, max_tokens=1500)
    
    def check_symptoms(self, symptoms: str) -> Optional[str]:
        """Analyze symptoms and suggest possible conditions"""
        system_message = """You are a helpful symptom checker assistant. Provide a clear, comprehensive analysis in 4-5 complete sentences that covers:
        1. Most likely possible conditions or causes
        2. General care recommendations (rest, hydration, etc.)
        3. When to seek medical attention if symptoms worsen
        4. Any important things to monitor
        
        Write in simple, clear language that's easy to understand. Be helpful and informative."""
        
        prompt = f"Please analyze these symptoms and provide guidance: {symptoms}"
        
        return self.generate_response(prompt, system_message, max_tokens=1200)
    
    def answer_healthcare_question(self, question: str) -> Optional[str]:
        """Answer general healthcare questions"""
        system_message = """You are a knowledgeable healthcare assistant. Provide accurate, helpful information about:
        - General health topics
        - Wellness and prevention
        - Basic medical concepts
        - Healthy lifestyle recommendations
        
        Always remind users to consult healthcare professionals for specific medical advice."""
        
        return self.generate_response(question, system_message, max_tokens=1000)
    
    def _timeout_fallback_response(self, prompt: str, system_message: str = None) -> str:
        """Provide fallback response when request times out"""
        if "drug" in prompt.lower() or "medication" in prompt.lower():
            return """The AI service is currently experiencing delays, but I can provide immediate medication safety guidance:

**Medication Safety Checklist:**
- Always inform healthcare providers about ALL medications you're taking
- Check with your pharmacist before starting new medications
- Don't mix medications without professional guidance
- Keep an updated medication list with you
- Report unusual side effects immediately

**For drug interactions:** Contact your pharmacist or doctor directly for immediate assistance.

**⚠️ Important:** For urgent medication questions, contact your healthcare provider or pharmacist directly."""

        elif "symptom" in prompt.lower():
            return """The AI service is currently experiencing delays. For immediate symptom guidance:

**General Care:**
- Monitor symptoms and note changes
- Stay hydrated and rest
- Use appropriate over-the-counter remedies for minor symptoms

**Seek immediate care if you experience:**
- High fever, difficulty breathing, severe pain
- Signs of dehydration or persistent vomiting

**⚠️ For urgent symptoms, contact your healthcare provider or call emergency services.**"""

        else:
            return """The AI service is currently experiencing delays. For immediate healthcare assistance, please contact your healthcare provider directly.

**For urgent medical concerns:** Call your doctor or emergency services.
**For medication questions:** Contact your pharmacist.
**For general health info:** Try again in a few minutes."""

    def _fallback_response(self, prompt: str, system_message: str = None) -> str:
        """Provide fallback response when AI is unavailable"""
        if "symptom" in prompt.lower() or "pain" in prompt.lower() or "hurt" in prompt.lower():
            return """I'm currently unable to connect to the AI service, but I can provide some general guidance:

**For symptoms you're experiencing:**
- Monitor your symptoms and note any changes
- Stay hydrated and get adequate rest
- Consider over-the-counter remedies for minor symptoms
- Contact your healthcare provider if symptoms persist or worsen

**When to seek immediate medical care:**
- High fever (>101.3°F/38.5°C)
- Difficulty breathing
- Severe pain
- Signs of dehydration
- Persistent vomiting

**⚠️ Important:** This is general information only. For proper diagnosis and treatment, please consult with a qualified healthcare professional."""

        elif "drug" in prompt.lower() or "medication" in prompt.lower():
            return """I'm currently unable to connect to the AI service, but here's important medication safety information:

**General Medication Safety:**
- Always follow prescribed dosages
- Don't mix medications without consulting healthcare providers
- Keep an updated medication list
- Store medications safely and properly
- Report any unusual side effects immediately

**Drug Interaction Safety:**
- Inform all healthcare providers about ALL medications you're taking
- Check with your pharmacist before starting new medications
- Be aware of over-the-counter drug interactions
- Don't stop medications without medical supervision

**⚠️ Always consult your pharmacist or doctor for specific medication advice and interaction checking.**"""

        elif "report" in prompt.lower() or "test" in prompt.lower():
            return """I'm currently unable to connect to the AI service for detailed report analysis.

**For medical report interpretation:**
- Schedule an appointment with your healthcare provider
- Bring the original report to your appointment
- Prepare questions about specific values or findings
- Ask for explanations in terms you can understand

**General guidance:**
- Keep copies of all medical reports for your records
- Note any values marked as "abnormal" or "high/low"
- Follow up as recommended by your healthcare provider"""

        else:
            return """I'm currently unable to connect to the AI service, but I'm here to help with healthcare information.

**I can assist with:**
- General health and wellness questions
- Symptom guidance and when to seek care
- Medication safety information
- Medical report guidance
- Health maintenance tips

**Important reminders:**
- This service provides information only, not medical advice
- Always consult healthcare professionals for specific medical concerns
- In emergencies, call 911 or go to the nearest emergency room

Please try your question again, or contact your healthcare provider for immediate assistance."""

# Global LLaMA API instance
llama_api = LlamaAPI()