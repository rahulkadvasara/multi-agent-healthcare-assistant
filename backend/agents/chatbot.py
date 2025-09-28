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
        
        formatted_response = f"""
## {emoji} Healthcare Information

{ai_response}

---

**Additional Resources:**
{self._get_topic_resources(topic)}

**⚠️ Important Reminder:**
This information is for educational purposes only and should not replace professional medical advice. Always consult with qualified healthcare providers for personalized medical guidance.
"""
        
        return formatted_response
    
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
            'nutrition': """
## 🥗 Nutrition & Diet Information

I'd be happy to help with nutrition questions! Here are some general guidelines:

**Healthy Eating Basics:**
- Eat a variety of fruits and vegetables
- Choose whole grains over refined grains
- Include lean proteins in your diet
- Limit processed foods and added sugars
- Stay hydrated with plenty of water

**For Personalized Advice:**
- Consult with a registered dietitian
- Discuss dietary changes with your healthcare provider
- Consider your individual health conditions and needs
""",
            'exercise': """
## 💪 Exercise & Fitness Information

Regular physical activity is important for overall health:

**Exercise Guidelines:**
- Aim for at least 150 minutes of moderate activity per week
- Include both cardio and strength training
- Start slowly if you're new to exercise
- Find activities you enjoy to stay motivated

**Safety First:**
- Consult your doctor before starting new exercise programs
- Warm up before and cool down after exercise
- Listen to your body and rest when needed
- Stay hydrated during physical activity
""",
            'mental_health': """
## 🧠 Mental Health & Wellness

Mental health is just as important as physical health:

**Stress Management:**
- Practice relaxation techniques like deep breathing
- Get adequate sleep (7-9 hours for most adults)
- Maintain social connections
- Engage in activities you enjoy

**When to Seek Help:**
- If you're feeling overwhelmed or unable to cope
- If symptoms interfere with daily activities
- If you have thoughts of self-harm
- Don't hesitate to reach out to mental health professionals
""",
            'prevention': """
## 🛡️ Preventive Healthcare

Prevention is key to maintaining good health:

**Regular Screenings:**
- Follow age-appropriate screening guidelines
- Keep up with recommended vaccinations
- Schedule regular checkups with your healthcare provider
- Know your family health history

**Healthy Lifestyle:**
- Don't smoke or use tobacco products
- Limit alcohol consumption
- Maintain a healthy weight
- Practice safe behaviors
""",
            'chronic_conditions': """
## 🏥 Chronic Condition Management

Managing chronic conditions requires ongoing care:

**Key Strategies:**
- Follow your treatment plan consistently
- Take medications as prescribed
- Monitor your condition regularly
- Maintain healthy lifestyle habits

**Healthcare Team:**
- Work closely with your doctors
- Ask questions about your condition
- Keep track of symptoms and changes
- Don't skip appointments
""",
            'general': """
## 💡 General Health Information

I'm here to help with your health questions! I can provide information about:

- **Nutrition & Diet**: Healthy eating tips and guidelines
- **Exercise & Fitness**: Physical activity recommendations
- **Mental Health**: Stress management and wellness
- **Prevention**: Screening and preventive care
- **Chronic Conditions**: Management strategies
- **General Wellness**: Overall health maintenance

**Remember**: This information is educational only. Always consult healthcare professionals for personalized medical advice.

Feel free to ask specific questions about any health topic!
"""
        }
        
        return topic_responses.get(topic, topic_responses['general'])

# Global instance
healthcare_chatbot = HealthcareChatbot()