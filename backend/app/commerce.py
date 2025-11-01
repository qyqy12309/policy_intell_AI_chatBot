"""
Commerce Module
===============
Stage 4: Seamless Commerce - Quote Generation and Payment Processing
Handles insurance quote generation, policy presentation, and payment flow.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid


class QuoteGenerator:
    """
    Generates insurance quotes based on trip information and policy data.
    """
    
    def __init__(self, vector_store=None, qa_system=None):
        """
        Initialize quote generator.
        
        Args:
            vector_store: VectorStore instance for querying policies
            qa_system: PolicyQASystem for getting coverage details
        """
        self.vector_store = vector_store
        self.qa_system = qa_system
        
        # Mock policy database (in production, use real database)
        # Each policy has: name, base_price_per_day, coverage details, etc.
        self.policies = {
            'basic': {
                'name': 'Basic Plan',
                'description': 'Essential coverage for budget travelers',
                'base_price_per_day': 5,
                'coverage': {
                    'medical': 50000,
                    'baggage': 1000,
                    'trip_cancellation': 2000,
                    'trip_delay': 300
                }
            },
            'standard': {
                'name': 'Standard Plan',
                'description': 'Comprehensive coverage for most travelers',
                'base_price_per_day': 8,
                'coverage': {
                    'medical': 100000,
                    'baggage': 2000,
                    'trip_cancellation': 5000,
                    'trip_delay': 500,
                    'emergency_evacuation': 100000
                }
            },
            'premium': {
                'name': 'Premium Plan',
                'description': 'Maximum protection for peace of mind',
                'base_price_per_day': 12,
                'coverage': {
                    'medical': 200000,
                    'baggage': 5000,
                    'trip_cancellation': 10000,
                    'trip_delay': 1000,
                    'emergency_evacuation': 200000,
                    'adventure_sports': True
                }
            }
        }
    
    def generate_quotes(self, trip_info: Dict) -> List[Dict]:
        """
        Generate insurance quotes for a trip.
        
        Args:
            trip_info: Dictionary with trip details (destination, dates, travelers, etc.)
            
        Returns:
            List of quote dictionaries with policy details and prices
        """
        # Extract trip information
        destination = trip_info.get('destination', 'Unknown')
        duration = trip_info.get('duration_days', 7)  # Default 7 days
        traveler_count = trip_info.get('traveler_count', 1)
        activities = trip_info.get('activities', [])
        
        quotes = []
        
        # Generate quote for each policy tier
        for policy_key, policy_data in self.policies.items():
            # Calculate base price
            base_price = policy_data['base_price_per_day'] * duration * traveler_count
            
            # Add surcharges based on destination/activities
            surcharge = self._calculate_surcharge(destination, activities, policy_key)
            total_price = base_price + surcharge
            
            # Build quote card
            quote = {
                'quote_id': str(uuid.uuid4()),
                'policy_name': policy_data['name'],
                'policy_key': policy_key,
                'description': policy_data['description'],
                'price': round(total_price, 2),
                'currency': 'SGD',
                'duration_days': duration,
                'traveler_count': traveler_count,
                'coverage': policy_data['coverage'],
                'highlights': self._get_highlights(policy_data['coverage']),
                'features': self._get_features(policy_key),
                'created_at': datetime.now().isoformat(),
                'valid_until': (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            quotes.append(quote)
        
        # Sort by price (cheapest first)
        quotes.sort(key=lambda x: x['price'])
        
        return quotes
    
    def _calculate_surcharge(self, destination: str, activities: List, policy_key: str) -> float:
        """
        Calculate additional surcharges based on destination and activities.
        
        Args:
            destination: Travel destination
            activities: List of activities
            policy_key: Policy tier key
            
        Returns:
            Surcharge amount
        """
        surcharge = 0
        
        # Destination-based surcharges (high-risk areas)
        high_risk_destinations = ['africa', 'middle east', 'south america']
        if any(dest in destination.lower() for dest in high_risk_destinations):
            surcharge += 20
        
        # Activity-based surcharges
        adventure_activities = ['ski', 'dive', 'scuba', 'climbing', 'parachute']
        if any(any(act in activity.lower() for act in adventure_activities) 
               for activity in activities):
            # Only charge if not included in premium
            if policy_key != 'premium':
                surcharge += 30
        
        return surcharge
    
    def _get_highlights(self, coverage: Dict) -> List[str]:
        """
        Get key highlights from coverage details.
        
        Args:
            coverage: Coverage dictionary
            
        Returns:
            List of highlight strings
        """
        highlights = []
        
        if coverage.get('medical'):
            highlights.append(f"Medical coverage: ${coverage['medical']:,}")
        
        if coverage.get('baggage'):
            highlights.append(f"Baggage protection: ${coverage['baggage']:,}")
        
        if coverage.get('trip_cancellation'):
            highlights.append(f"Trip cancellation: ${coverage['trip_cancellation']:,}")
        
        if coverage.get('adventure_sports'):
            highlights.append("Adventure sports included")
        
        return highlights
    
    def _get_features(self, policy_key: str) -> List[str]:
        """
        Get feature list for a policy.
        
        Args:
            policy_key: Policy tier key
            
        Returns:
            List of feature strings
        """
        features_map = {
            'basic': [
                '24/7 Emergency Assistance',
                'Medical Expenses Coverage',
                'Baggage Loss Protection',
                'Trip Cancellation Coverage'
            ],
            'standard': [
                'All Basic Features',
                'Higher Coverage Limits',
                'Emergency Evacuation',
                'Trip Delay Coverage',
                'Personal Accident Coverage'
            ],
            'premium': [
                'All Standard Features',
                'Maximum Coverage Limits',
                'Adventure Sports Coverage',
                'Pre-Existing Conditions',
                'Cancel For Any Reason (CFAR)'
            ]
        }
        
        return features_map.get(policy_key, features_map['basic'])


class PaymentProcessor:
    """
    Handles payment processing and policy issuance.
    """
    
    def __init__(self):
        """Initialize payment processor."""
        # In production, integrate with real payment gateway
        # (Stripe, PayPal, etc.)
        pass
    
    def create_payment_link(self, quote: Dict, user_info: Dict) -> Dict:
        """
        Create payment link for a quote.
        
        Args:
            quote: Quote dictionary
            user_info: User information dictionary
            
        Returns:
            Dictionary with payment link and transaction ID
        """
        transaction_id = str(uuid.uuid4())
        
        # In production, call payment gateway API
        # For now, return mock payment link
        payment_link = f"https://payment.example.com/checkout/{transaction_id}"
        
        return {
            'transaction_id': transaction_id,
            'payment_link': payment_link,
            'amount': quote['price'],
            'currency': quote['currency'],
            'quote_id': quote['quote_id'],
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
    
    def process_payment(self, transaction_id: str, payment_data: Dict) -> Dict:
        """
        Process payment (mock implementation).
        
        In production, integrate with payment gateway.
        
        Args:
            transaction_id: Transaction identifier
            payment_data: Payment information (card, etc.)
            
        Returns:
            Payment result dictionary
        """
        # Mock payment processing
        # In production, call payment gateway API
        return {
            'transaction_id': transaction_id,
            'status': 'success',
            'payment_id': str(uuid.uuid4()),
            'processed_at': datetime.now().isoformat(),
            'message': 'Payment processed successfully'
        }
    
    def issue_policy(self, transaction_id: str, quote: Dict, user_info: Dict) -> Dict:
        """
        Issue insurance policy after successful payment.
        
        Args:
            transaction_id: Transaction identifier
            quote: Quote dictionary
            user_info: User information
            
        Returns:
            Policy document dictionary
        """
        policy_number = f"POL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        policy = {
            'policy_number': policy_number,
            'policy_name': quote['policy_name'],
            'policy_key': quote['policy_key'],
            'policy_holder': user_info.get('name', 'Traveler'),
            'email': user_info.get('email'),
            'coverage_details': quote['coverage'],
            'duration_days': quote['duration_days'],
            'traveler_count': quote['traveler_count'],
            'price_paid': quote['price'],
            'currency': quote['currency'],
            'issued_at': datetime.now().isoformat(),
            'valid_from': quote.get('departure_date'),
            'valid_until': quote.get('return_date'),
            'policy_document_url': f"https://policies.example.com/{policy_number}.pdf",
            'download_url': f"https://policies.example.com/download/{policy_number}",
            'transaction_id': transaction_id
        }
        
        return policy
    
    def send_policy_confirmation(self, policy: Dict) -> bool:
        """
        Send policy confirmation email/SMS.
        
        Args:
            policy: Policy dictionary
            
        Returns:
            True if sent successfully
        """
        # In production, integrate with email/SMS service
        # (SendGrid, Twilio, etc.)
        
        email_content = f"""
        Subject: Your Travel Insurance Policy - {policy['policy_number']}
        
        Dear {policy['policy_holder']},
        
        Your travel insurance policy has been issued successfully!
        
        Policy Number: {policy['policy_number']}
        Coverage: {policy['policy_name']}
        Amount Paid: {policy['currency']} {policy['price_paid']}
        
        Download your policy: {policy['download_url']}
        
        Thank you for choosing our insurance!
        """
        
        # Mock: In production, send actual email
        print(f"Email sent to {policy.get('email')}: {email_content}")
        
        return True


class QuoteService:
    """
    Main service that orchestrates quote generation and purchase flow.
    """
    
    def __init__(self, vector_store=None, qa_system=None):
        """
        Initialize quote service.
        
        Args:
            vector_store: VectorStore instance
            qa_system: PolicyQASystem instance
        """
        self.quote_generator = QuoteGenerator(vector_store, qa_system)
        self.payment_processor = PaymentProcessor()
    
    def get_quotes(self, trip_info: Dict) -> Dict:
        """
        Get quotes for a trip.
        
        Args:
            trip_info: Trip information dictionary
            
        Returns:
            Dictionary with quotes and metadata
        """
        quotes = self.quote_generator.generate_quotes(trip_info)
        
        return {
            'quotes': quotes,
            'trip_info': trip_info,
            'generated_at': datetime.now().isoformat(),
            'quote_count': len(quotes)
        }
    
    def initiate_purchase(self, quote_id: str, trip_info: Dict, user_info: Dict) -> Dict:
        """
        Initiate purchase flow for a quote.
        
        Args:
            quote_id: Quote identifier
            trip_info: Trip information
            user_info: User information
            
        Returns:
            Dictionary with payment link and transaction details
        """
        # Get quotes again to find the selected one
        quotes_data = self.get_quotes(trip_info)
        selected_quote = next(
            (q for q in quotes_data['quotes'] if q['quote_id'] == quote_id),
            None
        )
        
        if not selected_quote:
            return {
                'success': False,
                'error': 'Quote not found'
            }
        
        # Create payment link
        payment_info = self.payment_processor.create_payment_link(selected_quote, user_info)
        
        return {
            'success': True,
            'quote': selected_quote,
            'payment': payment_info
        }
    
    def complete_purchase(self, transaction_id: str, payment_data: Dict, 
                          quote_id: str, trip_info: Dict, user_info: Dict) -> Dict:
        """
        Complete purchase after payment.
        
        Args:
            transaction_id: Transaction identifier
            payment_data: Payment information
            quote_id: Quote identifier
            trip_info: Trip information
            user_info: User information
            
        Returns:
            Dictionary with policy details
        """
        # Process payment
        payment_result = self.payment_processor.process_payment(transaction_id, payment_data)
        
        if payment_result['status'] != 'success':
            return {
                'success': False,
                'error': 'Payment failed'
            }
        
        # Get quote
        quotes_data = self.get_quotes(trip_info)
        selected_quote = next(
            (q for q in quotes_data['quotes'] if q['quote_id'] == quote_id),
            None
        )
        
        if not selected_quote:
            return {
                'success': False,
                'error': 'Quote not found'
            }
        
        # Issue policy
        policy = self.payment_processor.issue_policy(transaction_id, selected_quote, user_info)
        
        # Send confirmation
        self.payment_processor.send_policy_confirmation(policy)
        
        return {
            'success': True,
            'policy': policy,
            'payment': payment_result
        }


# Example usage
if __name__ == "__main__":
    # quote_service = QuoteService()
    # 
    # # Get quotes
    # trip_info = {
    #     'destination': 'Japan',
    #     'duration_days': 7,
    #     'traveler_count': 2,
    #     'activities': ['skiing']
    # }
    # 
    # quotes = quote_service.get_quotes(trip_info)
    # print(quotes)
    pass
