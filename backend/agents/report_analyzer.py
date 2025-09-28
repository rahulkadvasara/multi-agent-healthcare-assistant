from utils.llama_api import llama_api
from typing import Optional

class ReportAnalyzer:
    """Specialized agent for analyzing medical reports"""
    
    def __init__(self):
        self.agent_name = "Medical Report Analyzer"
    
    def analyze_report(self, ocr_text: str) -> Optional[str]:
        """Analyze medical report text and provide insights"""
        
        if not ocr_text or len(ocr_text.strip()) < 20:
            return "The extracted text is too short or unclear to analyze. Please upload a clearer image."
        
        # Use LLaMA API for analysis
        analysis = llama_api.analyze_medical_report(ocr_text)
        
        if analysis:
            return self._format_analysis(analysis, ocr_text)
        else:
            return self._fallback_analysis(ocr_text)
    
    def _format_analysis(self, analysis: str, original_text: str) -> str:
        """Format the analysis with proper structure"""
        
        formatted = f"""
## 📋 Medical Report Analysis

**AI Analysis:**
{analysis}

---

**Original Extracted Text:**
```
{original_text[:500]}{'...' if len(original_text) > 500 else ''}
```

---

**⚠️ Important Disclaimer:**
This analysis is for informational purposes only and should not replace professional medical advice. Please consult with your healthcare provider to discuss these results and their implications for your health.
"""
        return formatted
    
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
        
        return f"""
## 📋 Medical Report Analysis

**Extracted Text:**
{ocr_text}

**Basic Analysis:**
{'- ' + chr(10).join(findings) if findings else 'No specific patterns detected in the text.'}

**⚠️ Important:**
I was unable to provide a detailed AI analysis at this time. Please:
1. Ensure the image is clear and readable
2. Consult with your healthcare provider for proper interpretation
3. Keep the original report for your medical records

**Next Steps:**
- Share this report with your doctor
- Ask about any values that seem concerning
- Follow up as recommended by your healthcare provider
"""

# Global instance
report_analyzer = ReportAnalyzer()