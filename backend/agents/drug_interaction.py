from crewai import Agent, Task, Crew
from utils.llama_api import llama_api
from utils.drug_interaction_tool import drug_interaction_checker, drug_rxcui_finder, multi_drug_interaction_checker
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
            },
            'paracetamol': {
                'interactions': ['warfarin', 'alcohol', 'phenytoin'],
                'severity': 'medium',
                'warning': 'Same as acetaminophen - monitor liver function with high doses'
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
                    goal='Analyze drug interactions between new medications and existing patient medications, providing comprehensive safety assessments using RxNorm API data',
                    backstory="""You are a highly experienced clinical pharmacist with 15+ years of experience in 
                    hospital and community pharmacy settings. You specialize in identifying drug interactions, 
                    contraindications, and medication safety. You have access to the patient's current medication 
                    list from their reminder system and can cross-reference new medications against their existing 
                    regimen using the NIH RxNorm database. You prioritize patient safety and provide clear, actionable recommendations.""",
                    verbose=True,
                    allow_delegation=False,
                    llm=groq_llm,
                    tools=[drug_interaction_checker, drug_rxcui_finder, multi_drug_interaction_checker]
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
    
    def _create_rxnorm_tool(self):
        """Create RxNorm API tool for CrewAI agent"""
        
        # Simple tool function that can be called by the agent
        def check_drug_interactions_rxnorm(drug_names: List[str], current_medications: List[str] = None) -> str:
            """Check drug interactions using NIH RxNorm API"""
            try:
                results = drug_interaction_tool.check_drug_interactions(drug_names, current_medications or [])
                return drug_interaction_tool.format_interaction_results(results)
            except Exception as e:
                return f"Error checking drug interactions: {e}"
        
        return check_drug_interactions_rxnorm
    

    
    def _summarize_rxnorm_results(self, rxnorm_results: Dict) -> str:
        """Summarize RxNorm API results for CrewAI context"""
        
        if not rxnorm_results['api_available']:
            return "RxNorm API unavailable"
        
        summary_parts = []
        
        # Drugs found/not found
        new_drugs_found = [d for d in rxnorm_results['new_drugs'] if d['found']]
        new_drugs_not_found = [d for d in rxnorm_results['new_drugs'] if not d['found']]
        
        if new_drugs_found:
            summary_parts.append(f"New drugs found in RxNorm: {', '.join([d['name'] for d in new_drugs_found])}")
        if new_drugs_not_found:
            summary_parts.append(f"New drugs NOT found in RxNorm: {', '.join([d['name'] for d in new_drugs_not_found])}")
        
        # Current medications
        current_drugs_found = [d for d in rxnorm_results['current_drugs'] if d['found']]
        if current_drugs_found:
            summary_parts.append(f"Current medications found in RxNorm: {', '.join([d['name'] for d in current_drugs_found])}")
        
        # Interactions
        if rxnorm_results['interactions_found']:
            summary_parts.append("INTERACTIONS DETECTED:")
            for interaction in rxnorm_results['interactions_found']:
                summary_parts.append(f"- {interaction['drug1']} + {interaction['drug2']}: {interaction['severity']} severity")
                if interaction['description']:
                    summary_parts.append(f"  Description: {interaction['description'][:100]}...")
        else:
            summary_parts.append("No interactions detected in RxNorm database")
        
        # Warnings
        if rxnorm_results['warnings']:
            summary_parts.append("GENERAL WARNINGS:")
            for warning in rxnorm_results['warnings']:
                summary_parts.append(f"- {warning['drug']}: {warning['interaction_count']} known interactions")
        
        return "\n".join(summary_parts)
    
    def check_interactions(self, message: str, user_id: int = None) -> Optional[str]:
        """Check for drug interactions using RxNorm API and CrewAI agent, or handle reminder requests"""
        
        try:
            # First, check if this is a confirmation request
            confirm_response = self._handle_confirmation_request(message, user_id)
            if confirm_response:
                return confirm_response
            
            # Then, check if this is a delete reminder request
            delete_response = self._handle_delete_reminder_request(message, user_id)
            if delete_response:
                return delete_response
            
            # Then, check if this is an edit reminder request
            edit_response = self._handle_edit_reminder_request(message, user_id)
            if edit_response:
                return edit_response
            
            # Then, check if this is a reminder request
            reminder_response = self._handle_reminder_request(message, user_id)
            if reminder_response:
                return reminder_response
            
            # Check if this is a request to show reminders
            if self._is_show_reminders_request(message):
                return self._show_user_reminders(user_id)
            
            # Get user's current medications from reminders
            current_medications = []
            reminder_count = 0
            
            if user_id:
                try:
                    reminders = db.get_user_reminders(user_id)
                    current_medications = [reminder['medicine_name'].lower() for reminder in reminders]
                    reminder_count = len(reminders)
                    print(f"Found {reminder_count} active reminders for user {user_id}")
                except Exception as e:
                    print(f"Error getting user reminders: {e}")
                    current_medications = []
            else:
                print("No user_id provided - checking without personal medication history")
            
            # Extract new drug names from message
            new_drugs = self._extract_drug_names(message)
            
            # Handle special case: acetaminophen and paracetamol are the same drug
            if 'acetaminophen' in new_drugs and 'paracetamol' in new_drugs:
                return """💊 **Drug Check**

Acetaminophen and paracetamol are the same medication. You should not take both together as this would be a double dose. Choose one or the other, and follow the recommended dosage on the package."""
            
            # If no drugs found, provide general guidance
            if not new_drugs:
                return self._general_drug_response(message)
            
            # Use RxNorm API tool for drug interaction checking
            return self._check_with_rxnorm_api(message, new_drugs, current_medications, user_id)
            
        except Exception as e:
            print(f"Error in drug interaction check: {e}")
            return self._general_drug_response(message)
    
    def _check_with_rxnorm_api(self, message: str, new_drugs: List[str], current_medications: List[str], user_id: int) -> str:
        """Check drug interactions using the comprehensive function"""
        
        try:
            # Use the single comprehensive function that handles everything
            from utils.drug_interaction_tool import check_all_drug_interactions
            
            return check_all_drug_interactions(new_drugs, current_medications)
            
        except Exception as e:
            print(f"Drug interaction check failed: {e}")
            return self._general_drug_response(message)
    
    def _enhance_with_ai_analysis(self, message: str, rxnorm_results: Dict, new_drugs: List[str], current_medications: List[str]) -> Optional[str]:
        """Enhance RxNorm results with AI analysis"""
        
        try:
            # Prepare context for AI
            interactions_summary = []
            for interaction in rxnorm_results['interactions_found']:
                interactions_summary.append(
                    f"{interaction['drug1']} + {interaction['drug2']} ({interaction['severity']}): {interaction['description']}"
                )
            
            warnings_summary = []
            for warning in rxnorm_results['warnings']:
                warnings_summary.append(f"{warning['drug']}: {warning['warning']}")
            
            prompt = f"""
            Based on RxNorm API results, provide additional clinical guidance for this patient query: "{message}"
            
            NEW MEDICATIONS: {', '.join(new_drugs)}
            CURRENT MEDICATIONS: {', '.join(current_medications) if current_medications else 'None'}
            
            RXNORM INTERACTIONS FOUND:
            {chr(10).join(interactions_summary) if interactions_summary else 'None detected'}
            
            RXNORM WARNINGS:
            {chr(10).join(warnings_summary) if warnings_summary else 'None'}
            
            Please provide:
            1. Clinical significance of these interactions
            2. Practical recommendations for the patient
            3. Monitoring suggestions
            4. When to contact healthcare providers
            
            Keep response concise (2-3 sentences max).
            """
            
            system_message = """You are a clinical pharmacist providing additional context to RxNorm API results. 
            Focus on practical, actionable advice for patients while emphasizing professional consultation."""
            
            ai_response = llama_api.generate_response(prompt, system_message, max_tokens=800)
            
            if ai_response:
                truncated_response = self._truncate_at_sentence(ai_response, 300)
                return f"**🩺 Clinical Guidance:**\n{truncated_response}"
            
            return None
            
        except Exception as e:
            print(f"AI enhancement failed: {e}")
            return None
    
    def _analyze_with_crewai(self, message: str, new_drugs: List[str], current_medications: List[str], user_id: int) -> str:
        """Analyze drug interactions using CrewAI agent"""
        
        # Check if CrewAI agent is available
        if not self.crew_agent:
            print("⚠️  CrewAI agent not available, using enhanced local analysis")
            return self._enhanced_local_analysis(message, new_drugs, current_medications)
        
        # Prepare context for the agent
        if current_medications:
            current_meds_text = ", ".join(current_medications)
        elif user_id:
            current_meds_text = "No current medications found in reminder system"
        else:
            current_meds_text = "User not logged in - no personal medication history available"
        
        new_drugs_text = ", ".join(new_drugs) if new_drugs else "No specific drugs identified"
        
        # Get RxNorm API results first
        rxnorm_results = None
        try:
            rxnorm_results = drug_interaction_tool.check_drug_interactions(new_drugs, current_medications)
            rxnorm_summary = self._summarize_rxnorm_results(rxnorm_results)
        except Exception as e:
            print(f"RxNorm API failed: {e}")
            rxnorm_summary = "RxNorm API unavailable - using clinical knowledge only"
        
        # Create detailed task for the agent
        task = Task(
            description=f"""
            DRUG INTERACTION ANALYSIS REQUEST
            
            Patient Query: "{message}"
            
            CURRENT MEDICATIONS (from reminder system):
            {current_meds_text}
            
            NEW MEDICATIONS MENTIONED:
            {new_drugs_text}
            
            INSTRUCTIONS:
            1. Use the drug_rxcui_finder tool to find RxCUI codes for each drug mentioned
            2. Use the drug_interaction_checker tool to check interactions between each pair of drugs
            3. Use the multi_drug_interaction_checker tool if checking multiple drugs at once
            4. Analyze the clinical significance of any interactions found
            5. Provide specific recommendations based on the interaction data
            6. Include monitoring parameters and timing adjustments if needed
            7. Suggest when to consult healthcare providers
            
            WORKFLOW:
            - First, find RxCUI codes for all drugs using drug_rxcui_finder
            - Then check interactions between new drugs and current medications using drug_interaction_checker
            - Also check interactions among new drugs themselves
            - Interpret the results and provide clinical guidance
            
            SAFETY PRIORITIES:
            - Patient safety is paramount
            - Provide clear, actionable advice
            - Include appropriate medical disclaimers
            - Emphasize professional consultation for complex cases
            
            FORMAT: Provide a concise, well-structured response with clear findings and recommendations.
            """,
            expected_output="A comprehensive drug interaction analysis using RxNorm API tools with clinical recommendations and safety warnings formatted for patient understanding.",
            agent=self.crew_agent
        )
        
        # Create and execute crew
        try:
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[task],
                verbose=True
            )
            
            print("Executing CrewAI task...")
            result = crew.kickoff()
            print(f"CrewAI result received: {type(result)}")
            return self._format_crewai_response(str(result), current_medications, new_drugs)
            
        except Exception as e:
            print(f"CrewAI execution failed: {e}")
            print(f"Error type: {type(e).__name__}")
            print("Using direct Groq API analysis...")
            
            # Use our direct Groq API as fallback
            return self._direct_groq_analysis(message, new_drugs, current_medications)
    
    def _format_crewai_response(self, ai_response: str, current_meds: List[str], new_drugs: List[str]) -> str:
        """Format CrewAI response with additional context"""
        
        # Keep analysis short - truncate at sentence boundary
        short_analysis = self._truncate_at_sentence(ai_response, 200)
        quick_ref = self._get_quick_reference(new_drugs, current_meds)
        
        return f"""💊 **Drug Check**

{short_analysis}

{quick_ref}"""
    
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
        
        # Format response based on available data
        current_meds_section = self._format_medication_list(current_medications) if current_medications else "- No medications currently tracked in your reminders"
        new_drugs_section = self._format_medication_list(new_drugs) if new_drugs else "- No specific medications identified"
        
        interaction_section = chr(10).join(interactions_found) if interactions_found else '✅ No major interactions detected in our database'
        warnings_section = chr(10).join(warnings) if warnings else 'No specific warnings in our database'
        
        # Add note about medication reminders if no current medications
        reminder_note = ""
        if not current_medications:
            reminder_note = "\n**💡 Tip:** Add your medications to the reminder system for personalized interaction checking!"
        
        return f"""💊 **Drug Interaction Analysis**

**Your Current Medications:**
{current_meds_section}

**New Medication Being Considered:**
{new_drugs_section}

**Interaction Analysis:**
{interaction_section}

**Medication Warnings:**
{warnings_section}

**Recommendations:**
- Consult your pharmacist or doctor before starting new medications
- Inform them about ALL medications you're taking
- Monitor for any unusual side effects
- Keep your medication list updated{reminder_note}

**Note:** This is a basic analysis. Professional consultation is recommended for comprehensive interaction checking."""
    
    def _extract_drug_names(self, text: str) -> List[str]:
        """Extract drug names from text using enhanced pattern matching"""
        
        # Expanded drug names database
        drug_names = [
            # Pain relievers
            'aspirin', 'ibuprofen', 'acetaminophen', 'paracetamol', 'tylenol', 'advil', 'motrin', 'naproxen', 'aleve',
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
        
        # Try to get AI response first
        try:
            ai_response = llama_api.answer_healthcare_question(message)
            if ai_response:
                # Use the truncation method to keep it short
                short_response = self._truncate_at_sentence(ai_response, 300)
                return f"""💊 **Medication Info**

{short_response}"""
        except Exception as e:
            print(f"Error getting AI response: {e}")
        
        # Fallback response
        return """💊 **Medication Safety**

I can help with drug interactions, side effects, and medication questions. 

**General Safety:**
- Follow prescribed dosages
- Don't mix medications without consulting healthcare providers
- Keep an updated medication list
- Report unusual side effects

Ask me specific questions about medications or drug interactions!"""
    
    def _check_drug_pair(self, drug1: str, drug2: str) -> Optional[str]:
        """Check if two drugs have known interactions"""
        
        if drug1 in self.interaction_database:
            if drug2 in self.interaction_database[drug1]['interactions']:
                return f"⚠️ **{drug1.title()} + {drug2.title()}**: Potential interaction detected"
        
        if drug2 in self.interaction_database:
            if drug1 in self.interaction_database[drug2]['interactions']:
                return f"⚠️ **{drug2.title()} + {drug1.title()}**: Potential interaction detected"
        
        return None
    
    def _handle_delete_reminder_request(self, message: str, user_id: int = None) -> Optional[str]:
        """Handle delete reminder requests"""
        
        try:
            from utils.reminder_parser import ReminderParser
            
            parser = ReminderParser()
            medicine_name = parser.parse_delete_request(message)
            
            print(f"DEBUG: Delete request parsing result: {medicine_name}")
            
            if not medicine_name:
                return None  # Not a delete request
            
            if not user_id:
                return """❌ **Login Required**

To delete medication reminders, please log in to your account first."""
            
            print(f"DEBUG: Processing delete request for {medicine_name} (user {user_id})")
            
            # Get user's current reminders
            try:
                reminders = db.get_user_reminders(user_id)
                print(f"DEBUG: Found {len(reminders)} total reminders")
                
                # Find reminders matching the medicine name (case-insensitive)
                matching_reminders = []
                for reminder in reminders:
                    if reminder['medicine_name'].lower() == medicine_name.lower():
                        matching_reminders.append(reminder)
                
                print(f"DEBUG: Found {len(matching_reminders)} matching reminders for {medicine_name}")
                
                if not matching_reminders:
                    return parser.format_delete_confirmation(medicine_name, False, 0)
                
                # Delete all matching reminders
                deleted_count = 0
                for reminder in matching_reminders:
                    success = db.delete_reminder(reminder['id'], user_id)
                    if success:
                        deleted_count += 1
                        print(f"DEBUG: Deleted reminder {reminder['id']}")
                    else:
                        print(f"DEBUG: Failed to delete reminder {reminder['id']}")
                
                # Return confirmation
                if deleted_count > 0:
                    return parser.format_delete_confirmation(medicine_name, True, deleted_count)
                else:
                    return parser.format_delete_confirmation(medicine_name, False, len(matching_reminders))
                    
            except Exception as e:
                print(f"DEBUG: Error accessing reminders: {e}")
                return parser.format_delete_confirmation(medicine_name, False, 0)
                
        except Exception as e:
            print(f"ERROR: Exception in delete handler: {e}")
            import traceback
            traceback.print_exc()
            return f"""❌ **System Error**

There was an error processing your delete request: {str(e)}

Please try again or contact support."""
    
    def _handle_edit_reminder_request(self, message: str, user_id: int = None) -> Optional[str]:
        """Handle edit reminder requests"""
        
        try:
            from utils.reminder_parser import ReminderParser
            
            parser = ReminderParser()
            edit_data = parser.parse_edit_request(message)
            
            print(f"DEBUG: Edit request parsing result: {edit_data}")
            
            if not edit_data:
                return None  # Not an edit request
            
            if not user_id:
                return """❌ **Login Required**

To edit medication reminders, please log in to your account first."""
            
            medicine_name = edit_data['medicine_name']
            field = edit_data['field']
            new_value = edit_data['new_value']
            
            print(f"DEBUG: Processing edit request for {medicine_name} - {field} to {new_value} (user {user_id})")
            
            # Get user's current reminders
            try:
                reminders = db.get_user_reminders(user_id)
                print(f"DEBUG: Found {len(reminders)} total reminders")
                
                # Find reminders matching the medicine name (case-insensitive)
                matching_reminders = []
                for reminder in reminders:
                    if reminder['medicine_name'].lower() == medicine_name.lower():
                        matching_reminders.append(reminder)
                
                print(f"DEBUG: Found {len(matching_reminders)} matching reminders for {medicine_name}")
                
                if not matching_reminders:
                    return parser.format_edit_confirmation(medicine_name, field, "", new_value, False, 0)
                
                # Update all matching reminders
                updated_count = 0
                old_value = ""
                
                for reminder in matching_reminders:
                    # Get the old value for confirmation
                    if not old_value:
                        old_value = reminder.get(field, "Unknown")
                    
                    success = db.update_reminder(reminder['id'], user_id, field, new_value)
                    if success:
                        updated_count += 1
                        print(f"DEBUG: Updated reminder {reminder['id']}")
                    else:
                        print(f"DEBUG: Failed to update reminder {reminder['id']}")
                
                # Return confirmation
                if updated_count > 0:
                    return parser.format_edit_confirmation(medicine_name, field, old_value, new_value, True, updated_count)
                else:
                    return parser.format_edit_confirmation(medicine_name, field, old_value, new_value, False, len(matching_reminders))
                    
            except Exception as e:
                print(f"DEBUG: Error accessing reminders: {e}")
                return parser.format_edit_confirmation(medicine_name, field, "", new_value, False, 0)
                
        except Exception as e:
            print(f"ERROR: Exception in edit handler: {e}")
            import traceback
            traceback.print_exc()
            return f"""❌ **System Error**

There was an error processing your edit request: {str(e)}

Please try again or contact support."""
    
    def _handle_confirmation_request(self, message: str, user_id: int = None) -> Optional[str]:
        """Handle confirmation requests for adding medications despite interactions"""
        
        try:
            message_lower = message.lower()
            
            # Check for confirmation patterns
            confirm_patterns = [
                r'confirm\s+add\s+(\w+)',
                r'add\s+anyway\s+(\w+)',
                r'proceed\s+with\s+(\w+)',
                r'yes\s+add\s+(\w+)',
                r'force\s+add\s+(\w+)',
            ]
            
            medicine_name = None
            for pattern in confirm_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    medicine_name = match.group(1)
                    break
            
            if not medicine_name:
                return None  # Not a confirmation request
            
            if not user_id:
                return """❌ **Login Required**

To add medication reminders, please log in to your account first."""
            
            # Re-parse the original reminder request with force flag
            # For now, we'll use default values and let user specify if needed
            from utils.reminder_parser import ReminderParser
            parser = ReminderParser()
            
            # Create a forced reminder request
            forced_request = f"force add {medicine_name}, {parser.default_dosage}, {parser.default_frequency}, {parser.default_time}"
            
            return self._handle_reminder_request(forced_request, user_id)
            
        except Exception as e:
            print(f"Error handling confirmation request: {e}")
            return None
    
    def _handle_reminder_request(self, message: str, user_id: int = None) -> Optional[str]:
        """Handle medication reminder requests with pre-save interaction checking"""
        
        try:
            from utils.reminder_parser import ReminderParser
            
            parser = ReminderParser()
            reminder_data = parser.parse_reminder_request(message)
            
            print(f"DEBUG: Parsing result: {reminder_data}")
            
            if not reminder_data:
                return None  # Not a reminder request
            
            if not user_id:
                return """❌ **Login Required**

To set medication reminders, please log in to your account first. This helps us keep your medication information secure and personalized."""
            
            print(f"DEBUG: Processing reminder for user {user_id}")
            
            # Check for "force" or "confirm" keywords to bypass interaction warnings
            force_add = any(keyword in message.lower() for keyword in ['force', 'confirm', 'yes add', 'add anyway', 'proceed'])
            
            # Get current medications BEFORE adding new one
            current_medications = []
            try:
                reminders = db.get_user_reminders(user_id)
                current_medications = [r['medicine_name'].lower() for r in reminders]
                print(f"DEBUG: Current medications: {current_medications}")
            except Exception as e:
                print(f"DEBUG: Error getting current medications: {e}")
            
            # SIMPLIFIED: Only check interactions if there are current medications AND it's not a force add
            should_check_interactions = len(current_medications) > 0 and not force_add
            print(f"DEBUG: Should check interactions: {should_check_interactions}")
            
            if should_check_interactions:
                try:
                    from utils.drug_interaction_tool import check_all_drug_interactions
                    
                    interaction_result = check_all_drug_interactions(
                        [reminder_data['medicine_name']], 
                        current_medications
                    )
                    
                    print(f"DEBUG: Interaction result: {interaction_result[:100]}...")
                    
                    if "⚠️ Interactions Detected" in interaction_result:
                        # Don't add to database yet - warn user first
                        return f"""⚠️ **Drug Interaction Warning**

**New Medication:** {reminder_data['medicine_name'].title()}
**Dosage:** {reminder_data['dosage']}
**Frequency:** {reminder_data['frequency']}
**Time:** {reminder_data['time']}

🚨 **INTERACTION ALERT:**
{interaction_result}

**⚠️ This medication may interact with your current medications.**

**Options:**
• Type "**confirm add {reminder_data['medicine_name']}**" to add it anyway
• Consult your doctor or pharmacist first (recommended)
• Choose a different medication

**Your safety is important - please consult a healthcare professional before proceeding.**"""
                        
                except Exception as e:
                    print(f"DEBUG: Error in interaction checking: {e}")
                    # Continue with adding the reminder if interaction check fails
            
            # No interactions found OR user confirmed OR first medication - proceed with adding
            print(f"DEBUG: Attempting to add reminder to database")
            success = db.add_reminder(
                user_id=user_id,
                medicine_name=reminder_data['medicine_name'],
                dosage=reminder_data['dosage'],
                frequency=reminder_data['frequency'],
                time=reminder_data['time']
            )
            
            print(f"DEBUG: Database add result: {success}")
            
            if success:
                confirmation = parser.format_reminder_confirmation(reminder_data)
                
                # Add safety note if this was a forced add
                if force_add:
                    confirmation += f"\n\n⚠️ **Added Despite Interaction Warning**\nPlease monitor for side effects and consult your healthcare provider."
                elif current_medications:
                    confirmation += f"\n\n✅ **Safety Check Complete**\nNo major interactions detected with your current medications."
                else:
                    confirmation += f"\n\n✅ **First Medication Added**\nYour medication tracking has started!"
                
                return confirmation
            else:
                return """❌ **Error Adding Reminder**

Sorry, there was an error saving your medication reminder. Please try again or contact support if the problem persists."""
                
        except Exception as e:
            print(f"ERROR: Exception in reminder handler: {e}")
            import traceback
            traceback.print_exc()
            return f"""❌ **System Error**

There was an error processing your reminder request: {str(e)}

Please try again or contact support."""
            return None
    
    def _is_show_reminders_request(self, message: str) -> bool:
        """Check if user is asking to see their reminders"""
        
        show_patterns = [
            r'\bshow\s+(?:my\s+)?reminders?\b',
            r'\blist\s+(?:my\s+)?reminders?\b',
            r'\bview\s+(?:my\s+)?reminders?\b',
            r'\bget\s+(?:my\s+)?reminders?\b',
            r'\bmy\s+reminders?\b',
            r'\bwhat\s+reminders?\s+do\s+i\s+have\b',
            r'\breminders?\s+list\b',
        ]
        
        message_lower = message.lower()
        for pattern in show_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _show_user_reminders(self, user_id: int = None) -> str:
        """Show user's current medication reminders"""
        
        if not user_id:
            return """❌ **Login Required**

To view your medication reminders, please log in to your account first."""
        
        try:
            reminders = db.get_user_reminders(user_id)
            
            if not reminders:
                return """📋 **Your Medication Reminders**

You don't have any active medication reminders yet.

💡 **Add a reminder by saying:**
- "Add paracetamol, 1 tablet, 2 times daily, 8:00"
- "Create reminder for aspirin 100mg twice daily at 9:00 am"
- "Set reminder for vitamin D once daily"

I'll help you track your medications and check for interactions!"""
            
            # Format reminders list
            reminder_list = []
            for i, reminder in enumerate(reminders, 1):
                reminder_list.append(
                    f"{i}. **{reminder['medicine_name'].title()}**\n"
                    f"   • Dosage: {reminder['dosage']}\n"
                    f"   • Frequency: {reminder['frequency']}\n"
                    f"   • Time: {reminder['time']}"
                )
            
            response = f"""📋 **Your Medication Reminders** ({len(reminders)} active)

{chr(10).join(reminder_list)}

💡 **Tips:**
- Add new reminders by saying "Add [medicine name]..."
- I automatically check for interactions between your medications
- Keep your reminder list updated for the best safety checks

Need help with any of these medications? Just ask!"""
            
            return response
            
        except Exception as e:
            print(f"Error showing reminders: {e}")
            return """❌ **Error Loading Reminders**

Sorry, there was an error loading your medication reminders. Please try again later."""

# Global instance
drug_interaction_checker = DrugInteractionChecker()