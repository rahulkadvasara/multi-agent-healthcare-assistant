from utils.llama_api import llama_api
from typing import Optional

class HealthcareChatbot:
    """General healthcare information chatbot"""
    
    def __init__(self):
        self.agent_name = "Healthcare Information Specialist"
        
        # Common health topics and responses
        self.health_topics = {
            'nutrition': [
                'diet', 'nutrition', 'vitamins', 'minerals', 'healthy eating',
                'calories', 'protein', 'carbs', 'fat', 'fiber'
            ],
            'exercise': [
                'exercise', 'workout', 'fitness', 'physical activity',
                'cardio', 'strength training', 'yoga', 'walking'
            ],
            'mental_health': [
                'stress', 'anxiety', 'depression', 'mental health',
                'sleep', 'relaxation', 'meditation', 'mood'
            ],
            'prevention': [
                'prevention', 'screening', 'checkup', 'vaccine',
                'immunization', 'health maintenance'
            ],
            'chronic_conditions': [
                'diabetes', 'hypertension', 'heart disease', 'arthritis',
                'asthma', 'copd', 'chronic pain'
            ]
        }
    
    def respond_to_query(self, message: str) -> Optional[str]:
        """Respond to general healthcare queries"""
        
        # Identify topic category
        topic = self._identify_topic(message)
        
        # Use AI for response
        ai_response = llama_api.answer_healthcare_question(message)
        
        if ai_response:
            return self._format_response(ai_response, topic, message)
        else:
            return self._fallback_response(topic, message)
    
    def _identify_topic(self, message: str) -> str:
        """Identify the main health topic in the message"""
        
        message_lower = message.lower()
        
        for topic, keywords in self.health_topics.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic
        
        return 'general'
    
    def _format_response(self, ai_response: str, topic: str, original_message: str) -> str:
        """Format AI response with additional context"""
        
        topic_emojis = {
            'nutrition': '🥗',
            'exercise': '💪',
            'mental_health': '🧠',
            'prevention': '🛡️',
            'chronic_conditions': '🏥',
            'general': '💡'
        }
        
        emoji = topic_emojis.get(topic, '💡')
        
        # Provide comprehensive response - truncate at sentence boundary for readability
        comprehensive_response = self._truncate_at_sentence(ai_response, 700)
        
        formatted_response = f"""{emoji} **Health Information**

{comprehensive_response}

💡 **Note:** This is educational information. Consult healthcare professionals for personalized medical advice."""
        
        return formatted_response
    
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
    
    def _get_topic_resources(self, topic: str) -> str:
        """Get additional resources based on topic"""
        
        resources = {
            'nutrition': """
- Consult a registered dietitian for personalized nutrition plans
- Use reputable sources like the USDA MyPlate guidelines
- Consider keeping a food diary to track eating patterns
- Discuss supplements with your healthcare provider
""",
            'exercise': """
- Start slowly and gradually increase intensity
- Consult your doctor before beginning new exercise programs
- Consider working with a certified fitness trainer
- Listen to your body and rest when needed
""",
            'mental_health': """
- Reach out to mental health professionals when needed
- Practice stress management techniques regularly
- Maintain social connections and support systems
- Don't hesitate to seek help if you're struggling
""",
            'prevention': """
- Follow recommended screening schedules for your age group
- Stay up to date with vaccinations
- Maintain regular checkups with your healthcare provider
- Adopt healthy lifestyle habits for long-term wellness
""",
            'chronic_conditions': """
- Work closely with your healthcare team
- Follow prescribed treatment plans consistently
- Monitor your condition as recommended
- Join support groups or educational programs
""",
            'general': """
- Maintain regular healthcare checkups
- Stay informed about health topics from reliable sources
- Don't hesitate to ask questions during medical appointments
- Keep accurate records of your health information
"""
        }
        
        return resources.get(topic, resources['general'])
    
    def _fallback_response(self, topic: str, message: str) -> str:
        """Provide fallback response when AI is unavailable"""
        
        topic_responses = {
            'nutrition': """🥗 **Nutrition Information**

A balanced diet includes a variety of colorful fruits and vegetables, whole grains like brown rice and quinoa, and lean proteins such as fish, poultry, beans, and nuts. Limit processed foods high in sodium, sugar, and unhealthy fats. Stay hydrated with water throughout the day. Consider portion control and eating regular meals to maintain stable energy levels. Include healthy fats from sources like avocados, olive oil, and fatty fish for optimal nutrition.

💡 **Note:** Individual nutritional needs vary. Consult a registered dietitian for personalized guidance.""",
            'exercise': """💪 **Exercise Guidelines**

Adults should aim for at least 150 minutes of moderate-intensity aerobic activity weekly, plus muscle-strengthening activities twice per week. Start slowly if you're new to exercise and gradually increase intensity and duration. Include both cardiovascular exercises like walking or swimming and strength training with weights or resistance bands. Listen to your body, stay hydrated, and allow rest days for recovery. Regular physical activity improves cardiovascular health, strengthens bones, and enhances mental well-being.

💡 **Note:** Consult your doctor before starting new exercise programs, especially if you have health conditions.""",
            'mental_health': """🧠 **Mental Wellness**

Mental health is as important as physical health. Practice stress management through deep breathing exercises, meditation, or mindfulness techniques. Maintain 7-9 hours of quality sleep nightly and establish consistent sleep routines. Stay socially connected with family and friends, and engage in activities you enjoy. Regular exercise, balanced nutrition, and limiting alcohol can significantly impact mood and mental clarity. Don't hesitate to seek professional help when needed.

💡 **Note:** If you're experiencing persistent mental health concerns, reach out to a mental health professional.""",
            'prevention': """🛡️ **Preventive Health**

Prevention is the foundation of good health. Follow age-appropriate screening guidelines for conditions like cancer, diabetes, and heart disease. Stay current with vaccinations including annual flu shots and recommended boosters. Schedule regular checkups with your healthcare provider even when feeling well. Maintain a healthy lifestyle by not smoking, limiting alcohol consumption, eating nutritiously, exercising regularly, and managing stress effectively. Early detection and prevention are key to long-term health.

💡 **Note:** Discuss your individual risk factors and screening schedule with your healthcare provider.""",
            'chronic_conditions': """🏥 **Chronic Condition Management**

Successfully managing chronic conditions requires a comprehensive approach. Follow your prescribed treatment plan consistently and take medications exactly as directed by your healthcare provider. Monitor your condition regularly using recommended tools like blood pressure cuffs or glucose meters. Maintain healthy lifestyle habits including proper nutrition, regular exercise as approved by your doctor, adequate sleep, and stress management. Keep all medical appointments and communicate openly with your healthcare team about any concerns or changes in your condition.

💡 **Note:** Work closely with your healthcare team to develop a personalized management plan.""",
            'general': """💡 **Healthcare Information**

I'm here to provide general health information on topics like nutrition, exercise, mental wellness, preventive care, and chronic condition management. I can help answer questions about healthy lifestyle choices, general symptoms, and wellness strategies. However, I cannot provide specific medical diagnoses or replace professional medical advice. For personalized medical guidance, diagnostic questions, or treatment decisions, always consult with qualified healthcare professionals who can evaluate your individual situation.

💡 **Note:** This is educational information only. Seek professional medical advice for health concerns."""
        }
        
        return topic_responses.get(topic, topic_responses['general'])

# Global instance
healthcare_chatbot = HealthcareChatbot()