from utils.llama_api import llama_api
from typing import Optional, List, Dict
try:
    from crewai import Agent, Task, Crew
    _CREW_AVAILABLE = True
except Exception as _e:
    _CREW_AVAILABLE = False

class SymptomChecker:
    """Specialized agent for symptom analysis and triage"""
    
    def __init__(self):
        self.agent_name = "Symptom Assessment Specialist"
        self._crew_agent = None
        self.emergency_keywords = [
            'chest pain', 'difficulty breathing', 'shortness of breath',
            'severe headache', 'confusion', 'loss of consciousness',
            'severe bleeding', 'severe burns', 'poisoning',
            'severe allergic reaction', 'stroke symptoms',
            'heart attack', 'seizure', 'suicide'
        ]
        if _CREW_AVAILABLE:
            try:
                custom_llm = self._create_custom_groq_llm()
                self._crew_agent = Agent(
                    role='Symptom Assessment Specialist',
                    goal='Analyze symptoms, provide likely causes, home-care advice, and when to seek care.',
                    backstory=(
                        'You triage symptoms conservatively with patient safety first. '
                        'You provide clear, layperson-friendly guidance and highlight red flags.'
                    ),
                    allow_delegation=False,
                    verbose=False,
                    llm=custom_llm
                )
            except Exception:
                self._crew_agent = None

    def _create_custom_groq_llm(self):
        from utils.llama_api import llama_api as _llama
        class _GroqLLM:
            def __call__(self, prompt: str) -> str:
                return _llama.generate_response(prompt)
            def predict(self, text: str) -> str:
                return _llama.generate_response(text)
        return _GroqLLM()
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
        
        # Prefer CrewAI; fallback to existing path
        analysis = None
        if self._crew_agent is not None:
            try:
                task = Task(
                    description=(
                        'Provide a symptom assessment with likely causes, self-care advice, monitoring, '
                        'and when to seek medical attention. Use clear language. '
                        f'Symptoms: {symptoms}'
                    ),
                    expected_output=(
                        'A clear 4-8 sentence assessment with conservative safety guidance and red flags.'
                    ),
                    agent=self._crew_agent
                )
                crew = Crew(agents=[self._crew_agent], tasks=[task], verbose=False)
                analysis = str(crew.kickoff())
            except Exception:
                analysis = None
        if analysis is None:
            # Use existing llama path
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
        return """🚨 **EMERGENCY - Call 911 NOW**

Your symptoms may indicate a medical emergency.

**Do not wait. Seek immediate medical help.**"""
    
    def _format_symptom_analysis(self, analysis: str, original_symptoms: str) -> str:
        """Format symptom analysis with proper structure"""
        
        # Allow comprehensive analysis for symptoms (6-8 sentences) - truncate at sentence boundary
        comprehensive_analysis = self._truncate_at_sentence(analysis, 800)
        
        return f"""🩺 **Symptom Analysis**

{comprehensive_analysis}

💡 **Remember:** This is general guidance only. Consult a healthcare professional for proper diagnosis and treatment."""
    
    def _truncate_at_sentence(self, text: str, max_length: int) -> str:
        """Truncate text at sentence boundary to avoid mid-sentence cuts"""
        if len(text) <= max_length:
            return text
        
        # Find the last sentence ending before max_length
        truncated = text[:max_length]
        
        # Look for sentence endings (., !, ?)
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        # Find the latest sentence ending
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > 0:
            # Include the punctuation mark
            return text[:last_sentence_end + 1]
        else:
            # If no sentence ending found, look for other natural breaks
            last_colon = truncated.rfind(':')
            last_semicolon = truncated.rfind(';')
            
            natural_break = max(last_colon, last_semicolon)
            if natural_break > 0:
                return text[:natural_break + 1]
            
            # As last resort, find last complete word
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return text[:last_space] + "..."
            
            return text[:max_length] + "..."
    
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
        
        # Provide more detailed fallback based on category
        if detected_categories:
            category_guidance = self._get_category_guidance(detected_categories[0])
            return f"""🩺 **Symptom Check**

**Category:** {detected_categories[0].title()} symptoms detected.

{category_guidance}"""
        else:
            return f"""🩺 **Symptom Analysis**

For general symptoms, focus on rest and comprehensive self-care. Stay well-hydrated with water and clear fluids, get adequate sleep (7-9 hours), and monitor how you feel throughout the day. Consider appropriate over-the-counter remedies based on your specific symptoms. Maintain good nutrition with light, easily digestible foods. Contact a healthcare provider if symptoms persist beyond a few days, worsen significantly, or if you develop concerning signs like high fever, difficulty breathing, severe pain, or any symptoms that worry you.

💡 **Remember:** This is general guidance only. Trust your instincts about your health."""
    
    def _get_category_guidance(self, category: str) -> str:
        """Get specific guidance based on symptom category"""
        guidance = {
            'respiratory': "For respiratory symptoms like cough or congestion, stay hydrated, use a humidifier, and get plenty of rest. Warm liquids and throat lozenges may help. Seek medical attention if you develop difficulty breathing, high fever, or symptoms worsen after a few days.",
            'gastrointestinal': "For stomach-related symptoms, try the BRAT diet (bananas, rice, applesauce, toast) and stay hydrated with clear fluids. Avoid dairy and fatty foods. Contact a healthcare provider if you experience severe dehydration, persistent vomiting, or severe abdominal pain.",
            'musculoskeletal': "For muscle or joint pain, try rest, ice or heat therapy, and over-the-counter pain relievers if appropriate. Gentle stretching may help. Seek medical attention if pain is severe, persists for several days, or is accompanied by swelling or limited mobility.",
            'neurological': "For headaches, dizziness, or fatigue, ensure adequate rest, hydration, and regular meals. Consider stress management techniques. Contact a healthcare provider if symptoms are severe, persistent, or accompanied by vision changes, confusion, or weakness.",
            'dermatological': "For skin symptoms like rash or itching, keep the area clean and dry, avoid scratching, and consider cool compresses. Over-the-counter antihistamines may help with itching. Seek medical attention if the rash spreads rapidly, is accompanied by fever, or shows signs of infection."
        }
        return guidance.get(category, "Monitor your symptoms closely and seek medical attention if they worsen or persist.")

# Global instance
symptom_checker = SymptomChecker()