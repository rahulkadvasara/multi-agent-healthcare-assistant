from crewai import Agent, Task, Crew
from utils.llama_api import llama_api
from database import db
from typing import Optional, List, Dict
import re

class DrugInteractionChecker:
    """CrewAI-powered drug interaction agent with database access"""
    
    def __init__(self):
        self.agent_name = "Pharmacology Expert"
        self.setup_crewai_agent()
        
        # Enhanced drug interaction database
        self.interaction_database = {
            'warfarin': {
                'interactions': ['aspirin', 'ibuprofen', 'acetaminophen', 'antibiotics', 'vitamin k'],
                'severity': 'high',
                'warning': 'Blood thinner - many interactions possible, monitor INR levels'
            },
            'aspirin': {
                'interactions': ['warfarin', 'ibuprofen', 'alcohol', 'methotrexate'],
                'severity': 'medium',
                'warning': 'Increases bleeding risk, avoid with other NSAIDs'
            },
            'ibuprofen': {
                'interactions': ['warfarin', 'aspirin', 'lisinopril', 'metformin', 'lithium'],
                'severity': 'medium',
                'warning': 'Can affect kidney function and blood pressure medications'
            },
            'metformin': {
                'interactions': ['alcohol', 'contrast dye', 'furosemide'],
                'severity': 'medium',
                'warning': 'Diabetes medication - monitor blood sugar, avoid alcohol'
            },
            'lisinopril': {
                'interactions': ['ibuprofen', 'potassium supplements', 'spironolactone'],
                'severity': 'medium',
                'warning': 'ACE inhibitor - monitor potassium levels'
            },
            'simvastatin': {
                'interactions': ['grapefruit juice', 'erythromycin', 'ketoconazole'],
                'severity': 'high',
                'warning': 'Statin - risk of muscle damage with certain combinations'
            },
            'digoxin': {
                'interactions': ['furosemide', 'quinidine', 'verapamil'],
                'severity': 'high',
                'warning': 'Narrow therapeutic window - monitor levels closely'
            }
        }
    
    def setup_crewai_agent(self):
        """Setup CrewAI agent for drug interaction analysis"""
        try:
            # Try multiple approaches to get CrewAI working
            import os
            groq_api_key = os.getenv("GROQ_API_KEY")
            
            if not groq_api_key or groq_api_key.startswith("gsk_your_"):
                print("⚠️  GROQ_API_KEY not configured. Using enhanced local analysis.")
                self.crew_agent = None
                return
            
            # Approach 1: Try langchain-groq
            try:
                from langchain_groq import ChatGroq
                groq_llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name="llama3-8b-8192",
                    temperature=0.1
                )
                
                self.crew_agent = Agent(
                    role='Clinical Pharmacist and Drug Interaction Specialist',
                    goal='Analyze drug interactions between new medications and existing patient medications, providing comprehensive safety assessments',
                    backstory="""You are a highly experienced clinical pharmacist with 15+ years of experience in 
                    hospital and community pharmacy settings. You specialize in identifying drug interactions, 
                    contraindications, and medication safety. You have access to the patient's current medication 
                    list from their reminder system and can cross-reference new medications against their existing 
                    regimen. You prioritize patient safety and provide clear, actionable recommendations.""",
                    verbose=True,
                    allow_delegation=False,
                    llm=groq_llm
                )
                print("✅ CrewAI agent configured with Groq LLM")
                return
                
            except Exception as e:
                print(f"⚠️  langchain-groq approach failed: {e}")
            
            # Approach 2: Try with OpenAI-compatible setup (using Groq endpoint)
            try:
                from langchain.llms import OpenAI
                from langchain.chat_models import ChatOpenAI
                
                # Create a custom LLM that uses our Groq API
                custom_llm = self._create_custom_groq_llm(groq_api_key)
                
                self.crew_agent = Agent(
                    role='Clinical Pharmacist and Drug Interaction Specialist',
                    goal='Analyze drug interactions between new medications and existing patient medications, providing comprehensive safety assessments',
                    backstory="""You are a highly experienced clinical pharmacist with 15+ years of experience in 
                    hospital and community pharmacy settings. You specialize in identifying drug interactions, 
                    contraindications, and medication safety. You have access to the patient's current medication 
                    list from their reminder system and can cross-reference new medications against their existing 
                    regimen. You prioritize patient safety and provide clear, actionable recommendations.""",
                    verbose=True,
                    allow_delegation=False,
                    llm=custom_llm
                )
                print("✅ CrewAI agent configured with custom Groq LLM")
                return
                
            except Exception as e:
                print(f"⚠️  Custom LLM approach failed: {e}")
            
            # Approach 3: Use CrewAI without custom LLM (will use default but we'll override the execution)
            try:
                # Set a dummy OpenAI key to satisfy CrewAI initialization
                os.environ['OPENAI_API_KEY'] = 'dummy-key-for-crewai-init'
                
                self.crew_agent = Agent(
                    role='Clinical Pharmacist and Drug Interaction Specialist',
                    goal='Analyze drug interactions between new medications and existing patient medications, providing comprehensive safety assessments',
                    backstory="""You are a highly experienced clinical pharmacist with 15+ years of experience in 
                    hospital and community pharmacy settings. You specialize in identifying drug interactions, 
                    contraindications, and medication safety. You have access to the patient's current medication 
                    list from their reminder system and can cross-reference new medications against their existing 
                    regimen. You prioritize patient safety and provide clear, actionable recommendations.""",
                    verbose=False,  # Reduce verbosity to avoid OpenAI calls
                    allow_delegation=False
                )
                print("✅ CrewAI agent configured (will use custom execution)")
                return
                
            except Exception as e:
                print(f"⚠️  Default CrewAI approach failed: {e}")
            
            # If all approaches fail, use None
            self.crew_agent = None
            print("⚠️  All CrewAI approaches failed. Using enhanced local analysis.")
            
        except Exception as e:
            print(f"⚠️  CrewAI agent setup failed: {e}")
            print("   Using enhanced local analysis mode.")
            self.crew_agent = None
    
    def _create_custom_groq_llm(self, api_key: str):
        """Create a custom LLM wrapper for Groq"""
        from utils.llama_api import llama_api
        
        class CustomGroqLLM:
            def __init__(self, api_key):
                self.api_key = api_key
            
            def __call__(self, prompt: str) -> str:
                return llama_api.generate_response(prompt)
            
            def predict(self, text: str) -> str:
                return llama_api.generate_response(text)
        
        return CustomGroqLLM(api_key)
    
    def check_interactions(self, message: str, user_id: int = None) -> Optional[str]:
        """Check for drug interactions using CrewAI agent with database access"""
        
        # Get user's current medications from reminders
        current_medications = []
        if user_id:
            reminders = db.get_user_reminders(user_id)
            current_medications = [reminder['medicine_name'].lower() for reminder in reminders]
        
        # Extract new drug names from message
        new_drugs = self._extract_drug_names(message)
        
        # Create comprehensive analysis task
        return self._analyze_with_crewai(message, new_drugs, current_medications, user_id)
    
    def _analyze_with_crewai(self, message: str, new_drugs: List[str], current_medications: List[str], user_id: int) -> str:
        """Analyze drug interactions using CrewAI agent"""
        
        # Check if CrewAI agent is available
        if not self.crew_agent:
            print("⚠️  CrewAI agent not available, using enhanced local analysis")
            return self._enhanced_local_analysis(message, new_drugs, current_medications)
        
        # Prepare context for the agent
        current_meds_text = ", ".join(current_medications) if current_medications else "No current medications in reminder system"
        new_drugs_text = ", ".join(new_drugs) if new_drugs else "No specific drugs identified"
        
        # Create detailed task for the agent
        task = Task(
            description=f"""
            DRUG INTERACTION ANALYSIS REQUEST
            
            Patient Query: "{message}"
            
            CURRENT MEDICATIONS (from reminder system):
            {current_meds_text}
            
            NEW MEDICATIONS MENTIONED:
            {new_drugs_text}
            
            ANALYSIS REQUIRED:
            1. Identify all potential drug-drug interactions between new and existing medications
            2. Assess interaction severity levels (High/Medium/Low)
            3. Provide specific clinical recommendations
            4. Suggest monitoring parameters if applicable
            5. Recommend timing adjustments if needed
            6. Identify any contraindications
            7. Suggest when to consult healthcare providers
            
            SAFETY PRIORITIES:
            - Patient safety is paramount
            - Provide clear, actionable advice
            - Include appropriate medical disclaimers
            - Emphasize professional consultation for complex cases
            
            FORMAT: Provide a comprehensive, well-structured response with clear sections for findings, recommendations, and safety warnings.
            """,
            agent=self.crew_agent
        )
        
        # Create and execute crew
        try:
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            return self._format_crewai_response(str(result), current_medications, new_drugs)
            
        except Exception as e:
            print(f"CrewAI execution failed: {e}")
            print("Using direct Groq API analysis...")
            
            # Use our direct Groq API as fallback
            return self._direct_groq_analysis(message, new_drugs, current_medications)
    
    def _format_crewai_response(self, ai_response: str, current_meds: List[str], new_drugs: List[str]) -> str:
        """Format CrewAI response with additional context"""
        
        return f"""
## 💊 Comprehensive Drug Interaction Analysis

### 📋 **Current Medications** (from your reminders):
{self._format_medication_list(current_meds)}

### 🆕 **New Medications** being considered:
{self._format_medication_list(new_drugs)}

### 🔍 **AI Pharmacist Analysis:**
{ai_response}

### 📊 **Quick Reference - Interaction Database:**
{self._get_quick_reference(new_drugs, current_meds)}

---

### ⚠️ **Important Safety Reminders:**
- This analysis is based on your current medication reminders
- Always inform ALL healthcare providers about ALL medications you take
- Keep your medication list updated in the reminder system
- Some interactions may not be immediately apparent
- Over-the-counter medications and supplements can also interact

### 📞 **When to Contact Healthcare Providers:**
- Before starting any new medication
- If you experience unusual side effects
- If you have questions about timing or dosing
- For personalized medical advice

**🏥 Emergency:** If you experience severe side effects, seek immediate medical attention.
"""
    
    def _format_medication_list(self, medications: List[str]) -> str:
        """Format medication list for display"""
        if not medications:
            return "- None currently tracked"
        return "\n".join([f"- {med.title()}" for med in medications])
    
    def _get_quick_reference(self, new_drugs: List[str], current_meds: List[str]) -> str:
        """Get quick reference from local database"""
        interactions_found = []
        
        for new_drug in new_drugs:
            if new_drug.lower() in self.interaction_database:
                drug_info = self.interaction_database[new_drug.lower()]
                for current_med in current_meds:
                    if current_med.lower() in drug_info['interactions']:
                        severity = drug_info.get('severity', 'medium')
                        interactions_found.append(
                            f"⚠️ **{new_drug.title()} + {current_med.title()}**: {severity.upper()} risk - {drug_info['warning']}"
                        )
        
        if interactions_found:
            return "\n".join(interactions_found)
        else:
            return "✅ No major interactions found in quick reference database"
    
    def _enhanced_local_analysis(self, message: str, new_drugs: List[str], current_medications: List[str]) -> str:
        """Enhanced local analysis when CrewAI fails"""
        
        if not new_drugs and not current_medications:
            return self._general_drug_response(message)
        
        interactions_found = []
        warnings = []
        
        # Check interactions between new drugs and current medications
        for new_drug in new_drugs:
            if new_drug in self.interaction_database:
                drug_info = self.interaction_database[new_drug]
                warnings.append(f"**{new_drug.title()}**: {drug_info['warning']}")
                
                for current_med in current_medications:
                    if current_med in drug_info['interactions']:
                        severity = drug_info.get('severity', 'medium')
                        interactions_found.append(
                            f"⚠️ **{new_drug.title()} + {current_med.title()}**: {severity.upper()} risk interaction detected"
                        )
        
        return f"""
## 💊 Drug Interaction Analysis (Enhanced Local Analysis)

### 📋 **Your Current Medications:**
{self._format_medication_list(current_medications)}

### 🆕 **New Medication Being Considered:**
{self._format_medication_list(new_drugs)}

### 🔍 **Interaction Analysis:**
{chr(10).join(interactions_found) if interactions_found else '✅ No major interactions detected in our database'}

### ⚠️ **Medication Warnings:**
{chr(10).join(warnings) if warnings else 'No specific warnings in our database'}

### 📞 **Recommendations:**
- Consult your pharmacist or doctor before starting new medications
- Inform them about ALL medications in your reminder system
- Monitor for any unusual side effects
- Keep your medication reminders updated

**Note:** This is a basic analysis. Professional consultation is recommended for comprehensive interaction checking.
"""
    
    def _extract_drug_names(self, text: str) -> List[str]:
        """Extract drug names from text using enhanced pattern matching"""
        
        # Expanded drug names database
        drug_names = [
            # Pain relievers
            'aspirin', 'ibuprofen', 'acetaminophen', 'tylenol', 'advil', 'motrin', 'naproxen', 'aleve',
            # Blood thinners
            'warfarin', 'coumadin', 'heparin', 'eliquis', 'xarelto', 'pradaxa',
            # Diabetes medications
            'metformin', 'insulin', 'glipizide', 'glyburide', 'januvia', 'victoza',
            # Blood pressure medications
            'lisinopril', 'atenolol', 'amlodipine', 'hydrochlorothiazide', 'losartan', 'metoprolol',
            # Stomach medications
            'omeprazole', 'ranitidine', 'nexium', 'prilosec', 'zantac', 'pepcid',
            # Cholesterol medications
            'simvastatin', 'atorvastatin', 'lipitor', 'crestor', 'zocor',
            # Thyroid medications
            'levothyroxine', 'synthroid', 'armour thyroid',
            # Steroids
            'prednisone', 'prednisolone', 'methylprednisolone',
            # Respiratory
            'albuterol', 'ventolin', 'proair', 'symbicort', 'advair',
            # Antibiotics
            'amoxicillin', 'azithromycin', 'ciprofloxacin', 'doxycycline', 'penicillin',
            # Heart medications
            'digoxin', 'furosemide', 'lasix', 'spironolactone'
        ]
        
        text_lower = text.lower()
        found_drugs = []
        
        for drug in drug_names:
            if drug in text_lower:
                found_drugs.append(drug)
        
        return list(set(found_drugs))  # Remove duplicates
    
    def _direct_groq_analysis(self, message: str, new_drugs: List[str], current_medications: List[str]) -> str:
        """Direct analysis using our Groq API when CrewAI fails"""
        from utils.llama_api import llama_api
        
        current_meds_text = ", ".join(current_medications) if current_medications else "No current medications in reminder system"
        new_drugs_text = ", ".join(new_drugs) if new_drugs else "No specific drugs identified"
        
        prompt = f"""
        You are a Clinical Pharmacist and Drug Interaction Specialist with 15+ years of experience.
        
        PATIENT QUERY: "{message}"
        
        CURRENT MEDICATIONS (from reminder system): {current_meds_text}
        NEW MEDICATIONS MENTIONED: {new_drugs_text}
        
        Please provide a comprehensive drug interaction analysis including:
        1. Identify potential drug-drug interactions between new and existing medications
        2. Assess interaction severity levels (High/Medium/Low)
        3. Provide specific clinical recommendations
        4. Suggest monitoring parameters if applicable
        5. Recommend timing adjustments if needed
        6. Identify any contraindications
        7. Suggest when to consult healthcare providers
        
        Focus on patient safety and provide clear, actionable advice with appropriate medical disclaimers.
        """
        
        system_message = """You are an expert clinical pharmacist specializing in drug interactions and medication safety. 
        Provide comprehensive, evidence-based analysis while emphasizing patient safety and professional consultation."""
        
        ai_response = llama_api.generate_response(prompt, system_message, max_tokens=1500)
        
        if ai_response:
            return self._format_crewai_response(ai_response, current_medications, new_drugs)
        else:
            return self._enhanced_local_analysis(message, new_drugs, current_medications)
    
    def _analyze_multiple_drugs(self, drugs: List[str], original_message: str) -> str:
        """Analyze interactions between multiple drugs"""
        
        interactions_found = []
        warnings = []
        
        for i, drug1 in enumerate(drugs):
            for drug2 in drugs[i+1:]:
                interaction = self._check_drug_pair(drug1, drug2)
                if interaction:
                    interactions_found.append(interaction)
        
        # Get individual drug warnings
        for drug in drugs:
            if drug in self.interaction_database:
                warnings.append(f"**{drug.title()}**: {self.interaction_database[drug]['warning']}")
        
        # Use AI for detailed analysis
        ai_analysis = llama_api.answer_healthcare_question(
            f"Analyze potential drug interactions between: {', '.join(drugs)}. {original_message}"
        )
        
        return f"""
## 💊 Drug Interaction Analysis

**Medications Mentioned:**
{', '.join([drug.title() for drug in drugs])}

**Potential Interactions Found:**
{chr(10).join(interactions_found) if interactions_found else 'No major interactions detected in our basic database.'}

**Individual Drug Warnings:**
{chr(10).join(warnings) if warnings else 'No specific warnings in our database.'}

**AI Analysis:**
{ai_analysis if ai_analysis else 'AI analysis unavailable at this time.'}

---

**⚠️ Important Safety Information:**
- This is a basic interaction check only
- Always consult your pharmacist or doctor before combining medications
- Keep an updated medication list with you
- Inform all healthcare providers about ALL medications you take
- Don't stop medications without medical supervision

**When to Contact Healthcare Providers:**
- Before starting any new medication
- If you experience unusual side effects
- If you have questions about drug interactions
- Before taking over-the-counter medications with prescriptions
"""
    
    def _analyze_single_drug(self, drug: str, original_message: str) -> str:
        """Provide information about a single drug"""
        
        drug_info = self.interaction_database.get(drug, {})
        warning = drug_info.get('warning', 'General medication safety applies')
        interactions = drug_info.get('interactions', [])
        
        # Use AI for detailed information
        ai_response = llama_api.answer_healthcare_question(
            f"Provide information about {drug} medication including uses, side effects, and precautions. {original_message}"
        )
        
        return f"""
## 💊 Medication Information: {drug.title()}

**General Information:**
{ai_response if ai_response else f'Information about {drug} medication.'}

**Known Interactions:**
{', '.join([i.title() for i in interactions]) if interactions else 'No major interactions in our basic database.'}

**Safety Warning:**
{warning}

---

**General Medication Safety:**
- Take as prescribed by your healthcare provider
- Don't share medications with others
- Store medications properly
- Check expiration dates regularly
- Report side effects to your doctor

**⚠️ Always Consult:**
- Your pharmacist for drug interaction questions
- Your doctor before stopping or changing medications
- Healthcare providers before taking new medications
"""
    
    def _general_drug_response(self, message: str) -> str:
        """Provide general drug-related response"""
        
        ai_response = llama_api.answer_healthcare_question(message)
        
        if ai_response:
            return f"""
## 💊 Medication Information

{ai_response}

---

**General Medication Safety Tips:**
- Always follow prescribed dosages
- Don't mix medications without consulting healthcare providers
- Keep an updated medication list
- Store medications safely and properly
- Report any unusual side effects immediately

**Resources:**
- Consult your pharmacist for drug interaction questions
- Use reputable medical websites for drug information
- Keep emergency contact information for your healthcare providers
"""
        else:
            return """
## 💊 Medication Safety Information

I'd be happy to help with medication questions! You can ask me about:

- **Drug Interactions**: "Can I take aspirin with my blood pressure medication?"
- **Side Effects**: "What are the side effects of metformin?"
- **General Safety**: "How should I store my medications?"
- **Timing**: "When is the best time to take my medication?"

**Important Safety Reminders:**
- Always consult your pharmacist or doctor for specific medication advice
- Keep an updated list of all medications you take
- Don't stop medications without medical supervision
- Report unusual side effects to your healthcare provider

**Emergency Situations:**
If you experience severe side effects or suspect a medication overdose, seek immediate medical attention or call poison control.
"""
    
    def _check_drug_pair(self, drug1: str, drug2: str) -> Optional[str]:
        """Check if two drugs have known interactions"""
        
        if drug1 in self.interaction_database:
            if drug2 in self.interaction_database[drug1]['interactions']:
                return f"⚠️ **{drug1.title()} + {drug2.title()}**: Potential interaction detected"
        
        if drug2 in self.interaction_database:
            if drug1 in self.interaction_database[drug2]['interactions']:
                return f"⚠️ **{drug2.title()} + {drug1.title()}**: Potential interaction detected"
        
        return None

# Global instance
drug_interaction_checker = DrugInteractionChecker()