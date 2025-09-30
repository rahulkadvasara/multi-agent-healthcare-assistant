from utils.llama_api import llama_api
from typing import Optional
try:
    from crewai import Agent, Task, Crew
    _CREW_AVAILABLE = True
except Exception as _e:
    _CREW_AVAILABLE = False

class ReportAnalyzer:
    """Specialized agent for analyzing medical reports"""
    
    def __init__(self):
        self.agent_name = "Medical Report Analyzer"
        self._crew_agent = None
        if _CREW_AVAILABLE:
            try:
                custom_llm = self._create_custom_groq_llm()
                self._crew_agent = Agent(
                    role='Medical Report Analyzer',
                    goal='Explain medical report text in clear lay language with key findings and guidance.',
                    backstory=(
                        'You review OCR-extracted medical text and summarize key findings, abnormalities, and next steps '
                        'in plain language for patients. You avoid jargon and keep safety first.'
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
    
    def analyze_report(self, ocr_text: str) -> Optional[str]:
        """Analyze medical report text and provide insights"""
        
        if not ocr_text or len(ocr_text.strip()) < 20:
            return "The extracted text is too short or unclear to analyze. Please upload a clearer image."
        
        # Prefer CrewAI; fallback to existing llama path
        analysis = None
        if self._crew_agent is not None:
            try:
                task = Task(
                    description=(
                        'Summarize the following medical report text, listing key findings, simple explanations, any '
                        'abnormalities, and general recommendations. Keep it 5-6 sentences, layperson-friendly. '
                        f'Report text: {ocr_text}'
                    ),
                    expected_output='A single paragraph (5-6 sentences) in plain language with key findings and guidance.',
                    agent=self._crew_agent
                )
                crew = Crew(agents=[self._crew_agent], tasks=[task], verbose=False)
                analysis = str(crew.kickoff())
            except Exception:
                analysis = None
        if analysis is None:
            # Existing llama fallback
            analysis = llama_api.analyze_medical_report(ocr_text)
        
        if analysis:
            return self._format_analysis(analysis, ocr_text)
        else:
            return self._fallback_analysis(ocr_text)
    
    def _format_analysis(self, analysis: str, original_text: str) -> str:
        """Format the analysis with proper structure"""
        
        # Allow longer analysis for reports (5-6 sentences) - truncate at sentence boundary
        short_analysis = self._truncate_at_sentence(analysis, 500)
        
        formatted = f"""📋 **Report Analysis**

{short_analysis}"""
        return formatted
    
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
    
    def _fallback_analysis(self, ocr_text: str) -> str:
        """Provide basic analysis when AI fails"""
        
        # Basic keyword detection
        keywords = {
            'normal': ['normal', 'within normal limits', 'wnl', 'negative'],
            'abnormal': ['abnormal', 'elevated', 'high', 'low', 'positive', 'detected'],
            'urgent': ['critical', 'urgent', 'immediate', 'severe', 'emergency']
        }
        
        text_lower = ocr_text.lower()
        findings = []
        
        for category, terms in keywords.items():
            found_terms = [term for term in terms if term in text_lower]
            if found_terms:
                findings.append(f"{category.title()}: {', '.join(found_terms)}")
        
        return f"""📋 **Report Analysis**

**Findings:** {'; '.join(findings) if findings else 'No specific patterns detected'}"""

# Global instance
report_analyzer = ReportAnalyzer()