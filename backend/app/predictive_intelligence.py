"""
Predictive Intelligence Module
==============================
Stage 5: Predictive Intelligence - Claims Prediction and Smart Nudges
Analyzes patterns to predict risks and provide proactive recommendations.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import ollama


class PredictiveIntelligence:
    """
    Predictive analytics for insurance:
    - Predict high-risk travelers
    - Predict claim likelihood
    - Generate smart nudges
    - Analyze claims patterns
    """
    
    def __init__(self, llm_model: str = "llama3"):
        """
        Initialize predictive intelligence module.
        
        Args:
            llm_model: Ollama model to use
        """
        self.llm_model = llm_model
        
        # Mock historical claims data (in production, use real database)
        self.claims_patterns = {
            'high_risk_destinations': ['Japan (winter)', 'Nepal', 'India', 'Thailand (monsoon)'],
            'high_risk_activities': ['skiing', 'scuba diving', 'mountain climbing'],
            'common_claims': {
                'medical': 45,  # 45% of claims
                'baggage_loss': 25,
                'trip_delay': 20,
                'trip_cancellation': 10
            }
        }
    
    def assess_risk_profile(self, trip_info: Dict, user_info: Optional[Dict] = None) -> Dict:
        """
        Assess risk profile for a traveler/trip.
        
        Factors considered:
        - Destination risk level
        - Activities risk level
        - Traveler age/health (if available)
        - Trip duration
        - Historical patterns
        
        Args:
            trip_info: Trip information dictionary
            user_info: Optional user information (age, health, etc.)
            
        Returns:
            Risk profile dictionary with risk level and factors
        """
        risk_score = 0
        risk_factors = []
        
        # Destination risk
        destination = trip_info.get('destination', '').lower()
        if any(dest in destination for dest in ['japan', 'winter', 'snow']):
            risk_score += 2
            risk_factors.append('Winter destination - higher medical claim risk')
        
        if any(dest in destination for dest in ['india', 'nepal', 'thailand']):
            risk_score += 1
            risk_factors.append('Destination with higher health risks')
        
        # Activity risk
        activities = trip_info.get('activities', [])
        adventure_keywords = ['ski', 'dive', 'climb', 'parachute', 'bungee']
        if any(any(kw in act.lower() for kw in adventure_keywords) for act in activities):
            risk_score += 3
            risk_factors.append('Adventure activities - significantly higher risk')
        
        # Duration risk
        duration = trip_info.get('duration_days', 7)
        if duration > 30:
            risk_score += 1
            risk_factors.append('Extended trip - more opportunities for claims')
        
        # Age risk (if available)
        if user_info and user_info.get('age'):
            age = user_info['age']
            if age > 65:
                risk_score += 2
                risk_factors.append('Senior traveler - higher medical risk')
            elif age < 25:
                risk_score += 1
                risk_factors.append('Young traveler - higher activity risk')
        
        # Determine risk level
        if risk_score >= 5:
            risk_level = 'high'
        elif risk_score >= 3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': self._get_risk_recommendations(risk_level, risk_factors)
        }
    
    def predict_claim_likelihood(self, trip_info: Dict, policy_info: Dict, 
                                user_info: Optional[Dict] = None) -> Dict:
        """
        Predict likelihood of making a claim.
        
        Args:
            trip_info: Trip information
            policy_info: Policy details
            user_info: Optional user information
            
        Returns:
            Prediction dictionary with likelihood percentages
        """
        # Calculate base likelihood
        base_likelihood = 15  # 15% base claim rate
        
        # Adjust based on risk factors
        risk_profile = self.assess_risk_profile(trip_info, user_info)
        
        if risk_profile['risk_level'] == 'high':
            base_likelihood += 20
        elif risk_profile['risk_level'] == 'medium':
            base_likelihood += 10
        
        # Adjust based on coverage type
        coverage = policy_info.get('coverage', {})
        if coverage.get('adventure_sports'):
            base_likelihood += 5  # Adventure sports increase claim risk
        
        # Cap at 70% max
        claim_likelihood = min(base_likelihood, 70)
        
        # Predict claim types
        claim_type_predictions = {
            'medical': claim_likelihood * 0.45,  # Based on historical patterns
            'baggage_loss': claim_likelihood * 0.25,
            'trip_delay': claim_likelihood * 0.20,
            'trip_cancellation': claim_likelihood * 0.10
        }
        
        return {
            'overall_likelihood': round(claim_likelihood, 1),
            'claim_type_predictions': {k: round(v, 1) for k, v in claim_type_predictions.items()},
            'risk_level': risk_profile['risk_level'],
            'recommendation': self._get_claim_prevention_tips(claim_likelihood, trip_info)
        }
    
    def generate_smart_nudges(self, user_id: str, trip_info: Dict, 
                              policy: Optional[Dict] = None) -> List[Dict]:
        """
        Generate proactive smart nudges for users.
        
        Examples:
        - "Trip starts tomorrow - need emergency info?"
        - "Flight delay detected - might be covered!"
        - "Japan in winter - consider ski coverage"
        
        Args:
            user_id: User identifier
            trip_info: Trip information
            policy: Optional policy information
            
        Returns:
            List of nudge dictionaries
        """
        nudges = []
        
        # Check trip start date
        departure_date = trip_info.get('departure_date')
        if departure_date:
            try:
                dep = datetime.fromisoformat(departure_date.replace('Z', '+00:00'))
                days_until_trip = (dep - datetime.now()).days
                
                if days_until_trip == 1:
                    nudges.append({
                        'type': 'trip_reminder',
                        'priority': 'high',
                        'message': 'Your trip starts tomorrow! 📅 Would you like emergency assistance information?',
                        'action': 'get_emergency_info',
                        'icon': '✈️'
                    })
                elif days_until_trip == 0:
                    nudges.append({
                        'type': 'trip_start',
                        'priority': 'high',
                        'message': 'Have a safe trip! 🛫 Keep your policy number handy: {policy_number}',
                        'action': 'show_policy',
                        'icon': '🎒'
                    })
            except:
                pass
        
        # Destination-based nudges
        destination = trip_info.get('destination', '').lower()
        if 'japan' in destination or 'winter' in destination:
            nudges.append({
                'type': 'coverage_suggestion',
                'priority': 'medium',
                'message': 'Traveling to Japan in winter? ❄️ Consider adding ski coverage if you plan to hit the slopes!',
                'action': 'upgrade_coverage',
                'icon': '⛷️'
            })
        
        # Activity-based nudges
        activities = trip_info.get('activities', [])
        if any('dive' in act.lower() or 'scuba' in act.lower() for act in activities):
            nudges.append({
                'type': 'coverage_suggestion',
                'priority': 'medium',
                'message': 'Scuba diving detected! 🏊 Make sure your policy covers water sports.',
                'action': 'check_coverage',
                'icon': '🤿'
            })
        
        # Policy expiration reminder
        if policy:
            return_date = trip_info.get('return_date')
            if return_date:
                try:
                    ret = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
                    days_until_return = (ret - datetime.now()).days
                    
                    if days_until_return <= 7:
                        nudges.append({
                            'type': 'policy_expiry',
                            'priority': 'medium',
                            'message': f'Your policy expires in {days_until_return} days. Consider extending if needed!',
                            'action': 'extend_policy',
                            'icon': '⏰'
                        })
                except:
                    pass
        
        return nudges
    
    def detect_flight_delay(self, flight_info: Dict, policy: Dict) -> Optional[Dict]:
        """
        Detect flight delays and notify about potential coverage.
        
        Args:
            flight_info: Flight information (flight number, status, etc.)
            policy: Policy information
            
        Returns:
            Nudge dictionary if delay detected, None otherwise
        """
        # In production, integrate with flight tracking API
        # For now, mock detection
        
        if flight_info.get('status') == 'delayed' and flight_info.get('delay_minutes', 0) > 180:
            return {
                'type': 'flight_delay',
                'priority': 'high',
                'message': f'Flight delay detected ({flight_info["delay_minutes"]} minutes)! Your policy might cover this. Want to file a claim?',
                'action': 'file_claim',
                'icon': '✈️',
                'delay_minutes': flight_info['delay_minutes']
            }
        
        return None
    
    def _get_risk_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """
        Get recommendations based on risk level.
        
        Args:
            risk_level: Risk level ('low', 'medium', 'high')
            risk_factors: List of risk factors
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if risk_level == 'high':
            recommendations.append('Consider Premium plan for maximum coverage')
            recommendations.append('Ensure adventure sports coverage if applicable')
            recommendations.append('Purchase travel insurance well in advance')
        elif risk_level == 'medium':
            recommendations.append('Standard plan should provide adequate coverage')
            recommendations.append('Review exclusions carefully')
        else:
            recommendations.append('Basic or Standard plan should suffice')
        
        return recommendations
    
    def _get_claim_prevention_tips(self, likelihood: float, trip_info: Dict) -> str:
        """
        Get claim prevention tips based on predicted likelihood.
        
        Args:
            likelihood: Predicted claim likelihood percentage
            trip_info: Trip information
            
        Returns:
            Recommendation string
        """
        if likelihood > 40:
            return 'High claim risk detected. Ensure you have comprehensive coverage and keep all receipts.'
        elif likelihood > 25:
            return 'Moderate claim risk. Make sure to understand your policy coverage before traveling.'
        else:
            return 'Low claim risk expected. Standard coverage should be sufficient.'


# Example usage
if __name__ == "__main__":
    # predictor = PredictiveIntelligence()
    # 
    # trip_info = {
    #     'destination': 'Japan',
    #     'departure_date': '2024-12-15',
    #     'duration_days': 7,
    #     'activities': ['skiing']
    # }
    # 
    # risk = predictor.assess_risk_profile(trip_info)
    # print(risk)
    # 
    # nudges = predictor.generate_smart_nudges("user123", trip_info)
    # print(nudges)
    pass
