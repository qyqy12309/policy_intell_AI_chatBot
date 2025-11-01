"""
Conversation Engine Module
=========================
Stage 0-2: Entry Point, Intent Detection, and Conversational Magic
Handles human-like chat interactions, intent detection, and dynamic conversation flows.
"""

from typing import Dict, List, Optional, Tuple
import ollama
from datetime import datetime
import json


class ConversationEngine:
    """
    Main conversation engine that handles:
    - User onboarding and greeting
    - Intent detection
    - Dynamic question sequencing
    - Context-aware responses
    - Persona switching
    """
    
    def __init__(self, vector_store=None, qa_system=None, llm_model: str = "llama3"):
        """
        Initialize the conversation engine.
        
        Args:
            vector_store: VectorStore instance for policy queries
            qa_system: PolicyQASystem instance for answering policy questions
            llm_model: Ollama model to use
        """
        self.vector_store = vector_store
        self.qa_system = qa_system
        self.llm_model = llm_model
        
        # Conversation personas (different chat styles)
        self.personas = {
            'travel_guru': {
                'name': 'Travel Guru',
                'tone': 'fun, friendly, travel-savvy',
                'emoji': '🧳✈️',
                'greeting': 'Hey there! Ready to explore the world? 🌍'
            },
            'advisor': {
                'name': 'Insurance Advisor',
                'tone': 'formal, professional, compliance-aware',
                'emoji': '🛡️',
                'greeting': 'Hello, I\'m here to help you find the perfect travel insurance. How can I assist you today?'
            },
            'companion': {
                'name': 'Travel Companion',
                'tone': 'casual, helpful, empathetic',
                'emoji': '👋',
                'greeting': 'Hi! Planning a trip? I\'d love to help you get protected! 😊'
            }
        }
        
        # Active conversation sessions (in production, use Redis/database)
        self.sessions = {}
    
    def start_conversation(self, user_id: str, persona: str = 'travel_guru') -> Dict:
        """
        Stage 0: Entry Point - Start a new conversation session.
        
        Creates initial greeting and context for the user.
        
        Args:
            user_id: Unique identifier for the user
            persona: Which persona to use ('travel_guru', 'advisor', 'companion')
            
        Returns:
            Dictionary with greeting message and session info
        """
        # Initialize session
        self.sessions[user_id] = {
            'user_id': user_id,
            'persona': persona,
            'stage': 'greeting',
            'context': {},
            'intent': None,
            'entities': {},  # Extracted information (destination, dates, etc.)
            'conversation_history': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Get greeting based on persona
        persona_info = self.personas.get(persona, self.personas['travel_guru'])
        greeting = persona_info['greeting']
        
        # Add contextual awareness if possible
        # (In production, check user history, time of day, etc.)
        hour = datetime.now().hour
        if 6 <= hour < 12:
            greeting += " Good morning!"
        elif 12 <= hour < 18:
            greeting += " Good afternoon!"
        else:
            greeting += " Good evening!"
        
        return {
            'message': greeting,
            'persona': persona_info['name'],
            'session_id': user_id,
            'suggestions': [
                "Get a quote",
                "Compare policies",
                "Ask about coverage",
                "Check country eligibility"
            ]
        }
    
    def detect_intent(self, user_message: str, user_id: str) -> Dict:
        """
        Detect user intent from their message.
        
        Intents include:
        - get_quote: User wants to get insurance quote
        - compare_policies: User wants to compare different policies
        - ask_question: User has a question about insurance
        - check_eligibility: Check if policy covers a country
        - make_claim: User wants to make a claim
        - learn_coverage: User wants to learn about coverage
        
        Args:
            user_message: User's input message
            user_id: User identifier
            
        Returns:
            Dictionary with detected intent and confidence
        """
        # Use LLM to detect intent
        prompt = f"""Analyze this user message and identify their intent. Choose ONE intent:

User message: "{user_message}"

Possible intents:
1. get_quote - User wants an insurance quote (keywords: quote, price, cost, buy, purchase)
2. compare_policies - User wants to compare different insurance plans
3. ask_question - User has a question about insurance coverage (keywords: does it cover, what about, can i)
4. check_eligibility - Check if insurance covers a specific country (keywords: eligible, covers, available in)
5. make_claim - User wants to make a claim (keywords: claim, file claim, reimbursement)
6. learn_coverage - User wants to learn about what's covered (keywords: what covers, explain, tell me about)

Respond with ONLY the intent name (e.g., "get_quote"):"""
        
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={'temperature': 0.1, 'num_predict': 20}
            )
            intent = response['response'].strip().lower()
            
            # Validate intent
            valid_intents = ['get_quote', 'compare_policies', 'ask_question', 
                           'check_eligibility', 'make_claim', 'learn_coverage']
            if intent not in valid_intents:
                # Fallback: simple keyword matching
                message_lower = user_message.lower()
                if any(kw in message_lower for kw in ['quote', 'price', 'cost', 'buy']):
                    intent = 'get_quote'
                elif any(kw in message_lower for kw in ['compare', 'difference']):
                    intent = 'compare_policies'
                elif any(kw in message_lower for kw in ['claim', 'file']):
                    intent = 'make_claim'
                else:
                    intent = 'ask_question'
            
            # Update session
            if user_id in self.sessions:
                self.sessions[user_id]['intent'] = intent
                self.sessions[user_id]['updated_at'] = datetime.now().isoformat()
            
            return {
                'intent': intent,
                'confidence': 'high',
                'message': user_message
            }
        except Exception as e:
            # Fallback intent detection
            message_lower = user_message.lower()
            if any(kw in message_lower for kw in ['quote', 'price', 'buy']):
                intent = 'get_quote'
            else:
                intent = 'ask_question'
            
            return {
                'intent': intent,
                'confidence': 'medium',
                'message': user_message
            }
    
    def extract_entities(self, user_message: str, user_id: str) -> Dict:
        """
        Extract entities from user message (destination, dates, travelers, etc.).
        
        Entities extracted:
        - destination: Country or city name
        - travel_date: Departure date
        - return_date: Return date
        - duration: Trip duration in days
        - travelers: Number of travelers
        - activities: Activities mentioned (adventure sports, etc.)
        
        Args:
            user_message: User's input message
            user_id: User identifier
            
        Returns:
            Dictionary with extracted entities
        """
        prompt = f"""Extract travel information from this message. Return as JSON:

User message: "{user_message}"

Extract:
- destination: Country or city (if mentioned)
- travel_date: Departure date (if mentioned)
- return_date: Return date (if mentioned)
- duration: Trip duration in days (if mentioned or can be calculated)
- travelers: Number of travelers (if mentioned)
- activities: Activities mentioned (e.g., "skiing", "scuba diving")

Return ONLY valid JSON, use null for missing values:
{{"destination": "...", "travel_date": "...", "return_date": "...", "duration": ..., "travelers": ..., "activities": [...]}}"""
        
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={'temperature': 0.1, 'num_predict': 200}
            )
            
            # Parse JSON response
            response_text = response['response'].strip()
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            entities = json.loads(response_text)
            
            # Update session with extracted entities
            if user_id in self.sessions:
                self.sessions[user_id]['entities'].update(entities)
                self.sessions[user_id]['updated_at'] = datetime.now().isoformat()
            
            return entities
        except Exception as e:
            # Return empty entities if extraction fails
            return {
                'destination': None,
                'travel_date': None,
                'return_date': None,
                'duration': None,
                'travelers': None,
                'activities': []
            }
    
    def generate_response(
        self, 
        user_message: str, 
        user_id: str,
        use_qa_system: bool = True
    ) -> Dict:
        """
        Generate a conversational response based on user message and context.
        
        Stage 2: Conversational Magic - Creates human-like responses.
        
        Args:
            user_message: User's input message
            user_id: User identifier
            use_qa_system: Whether to use Q&A system for policy questions
            
        Returns:
            Dictionary with bot response, suggestions, and metadata
        """
        # Get or create session
        if user_id not in self.sessions:
            self.start_conversation(user_id)
        
        session = self.sessions[user_id]
        
        # Detect intent
        intent_result = self.detect_intent(user_message, user_id)
        intent = intent_result['intent']
        
        # Extract entities
        entities = self.extract_entities(user_message, user_id)
        
        # Get persona info
        persona = self.personas.get(session['persona'], self.personas['travel_guru'])
        
        # Handle different intents
        if intent == 'ask_question' and use_qa_system and self.qa_system:
            # Use Q&A system for policy questions
            qa_result = self.qa_system.answer_question(user_message)
            response = qa_result['answer']
            
            # Make it more conversational
            response = self._make_conversational(response, persona)
            
        elif intent == 'get_quote':
            # Guide user through quote process
            missing_info = self._check_missing_quote_info(session['entities'])
            
            if missing_info:
                response = self._generate_quote_question(missing_info[0], persona)
            else:
                response = "Great! I have all the info I need. Let me find the best policies for you..."
                # (In production, call quote generation service)
        
        elif intent == 'compare_policies':
            response = "I'd be happy to help you compare policies! What would you like to compare? For example, coverage limits, prices, or specific benefits?"
        
        else:
            # Generate general conversational response
            context = self._build_context(session, user_message)
            prompt = f"""You are a {persona['tone']} travel insurance assistant. {persona['name']} {persona['emoji']}

Conversation context:
{context}

User message: "{user_message}"

Respond in a {persona['tone']} way. Be helpful, concise, and friendly. Ask follow-up questions if needed to help the user.

Response:"""
            
            try:
                llm_response = ollama.generate(
                    model=self.llm_model,
                    prompt=prompt,
                    options={'temperature': 0.7, 'num_predict': 300}
                )
                response = llm_response['response'].strip()
            except:
                response = "I'm here to help! Could you tell me more about what you need?"
        
        # Update conversation history
        session['conversation_history'].append({
            'user': user_message,
            'bot': response,
            'intent': intent,
            'timestamp': datetime.now().isoformat()
        })
        session['updated_at'] = datetime.now().isoformat()
        
        # Generate suggestions based on intent
        suggestions = self._generate_suggestions(intent, session)
        
        return {
            'message': response,
            'intent': intent,
            'entities': entities,
            'suggestions': suggestions,
            'persona': persona['name']
        }
    
    def _make_conversational(self, response: str, persona: Dict) -> str:
        """
        Make a technical response more conversational.
        
        Args:
            response: Technical response from Q&A system
            persona: Persona information
            
        Returns:
            More conversational version
        """
        # Add friendly prefix/suffix based on persona
        if persona['name'] == 'Travel Guru':
            if not response.startswith('Yes') and not response.startswith('No'):
                response = f"Great question! {response}"
        elif persona['name'] == 'Advisor':
            response = f"According to the policy: {response}"
        
        return response
    
    def _check_missing_quote_info(self, entities: Dict) -> List[str]:
        """
        Check what information is missing for a quote.
        
        Args:
            entities: Extracted entities dictionary
            
        Returns:
            List of missing information fields
        """
        missing = []
        if not entities.get('destination'):
            missing.append('destination')
        if not entities.get('travel_date'):
            missing.append('travel_date')
        if not entities.get('return_date') and not entities.get('duration'):
            missing.append('duration')
        if not entities.get('travelers'):
            missing.append('travelers')
        
        return missing
    
    def _generate_quote_question(self, missing_field: str, persona: Dict) -> str:
        """
        Generate a natural question to get missing quote information.
        
        Args:
            missing_field: Field that's missing
            persona: Persona information
            
        Returns:
            Natural question string
        """
        questions = {
            'destination': {
                'travel_guru': "Where are you planning to go? 🌍",
                'advisor': "Which country or region will you be traveling to?",
                'companion': "Tell me your destination and I'll find the perfect coverage!"
            },
            'travel_date': {
                'travel_guru': "When does your adventure begin? 📅",
                'advisor': "What is your departure date?",
                'companion': "When are you planning to leave?"
            },
            'duration': {
                'travel_guru': "How long will you be away? 🗓️",
                'advisor': "What is the duration of your trip?",
                'companion': "How many days will you be traveling?"
            },
            'travelers': {
                'travel_guru': "How many travelers? (Including yourself!) 👥",
                'advisor': "How many people will be covered under this policy?",
                'companion': "Just yourself or traveling with others?"
            }
        }
        
        field_questions = questions.get(missing_field, {})
        return field_questions.get(persona['name'].lower().replace(' ', '_'), 
                                  field_questions.get('travel_guru', 
                                  f"Could you provide your {missing_field}?"))
    
    def _build_context(self, session: Dict, current_message: str) -> str:
        """
        Build conversation context for LLM.
        
        Args:
            session: User session dictionary
            current_message: Current user message
            
        Returns:
            Context string
        """
        context_parts = []
        
        # Add extracted entities
        entities = session.get('entities', {})
        if entities:
            context_parts.append("Information gathered so far:")
            if entities.get('destination'):
                context_parts.append(f"- Destination: {entities['destination']}")
            if entities.get('travel_date'):
                context_parts.append(f"- Travel date: {entities['travel_date']}")
            if entities.get('travelers'):
                context_parts.append(f"- Travelers: {entities['travelers']}")
        
        # Add recent conversation history
        history = session.get('conversation_history', [])
        if history:
            context_parts.append("\nRecent conversation:")
            for entry in history[-3:]:  # Last 3 exchanges
                context_parts.append(f"User: {entry['user']}")
                context_parts.append(f"Bot: {entry['bot']}")
        
        return "\n".join(context_parts) if context_parts else "New conversation"
    
    def _generate_suggestions(self, intent: str, session: Dict) -> List[str]:
        """
        Generate contextual suggestions for user.
        
        Args:
            intent: Detected intent
            session: User session
            
        Returns:
            List of suggestion strings
        """
        suggestions_map = {
            'get_quote': ["Tell me more about coverage", "Compare with other plans"],
            'compare_policies': ["Show me prices", "What's the difference?"],
            'ask_question': ["Get a quote", "Compare policies"],
            'check_eligibility': ["Ask another question", "Get a quote"],
            'make_claim': ["File a claim", "Check claim status"],
            'learn_coverage': ["Get a quote", "Compare policies"]
        }
        
        return suggestions_map.get(intent, ["How can I help?"])
    
    def get_session(self, user_id: str) -> Optional[Dict]:
        """
        Get user session information.
        
        Args:
            user_id: User identifier
            
        Returns:
            Session dictionary or None
        """
        return self.sessions.get(user_id)
    
    def update_persona(self, user_id: str, persona: str) -> bool:
        """
        Switch conversation persona.
        
        Args:
            user_id: User identifier
            persona: New persona name
            
        Returns:
            True if successful
        """
        if user_id in self.sessions and persona in self.personas:
            self.sessions[user_id]['persona'] = persona
            return True
        return False


# Example usage
if __name__ == "__main__":
    # This would be used with VectorStore and PolicyQASystem
    # from vector_store import VectorStore
    # from rag_qa import PolicyQASystem
    # 
    # store = VectorStore()
    # qa = PolicyQASystem(store)
    # engine = ConversationEngine(store, qa)
    # 
    # # Start conversation
    # result = engine.start_conversation("user123", persona="travel_guru")
    # print(result['message'])
    # 
    # # Get response
    # response = engine.generate_response("I'm going to Japan next week", "user123")
    # print(response['message'])
    pass
