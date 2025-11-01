"""
Country Eligibility Checker
===========================
This module analyzes policies to determine which countries they are eligible for.
Extracts country information, restrictions, and coverage areas from policy documents.
"""

from typing import List, Dict, Optional
from .rag_qa import PolicyQASystem
import ollama
import re


class CountryEligibilityChecker:
    """
    Checks policy eligibility for different countries.
    
    Extracts information about:
    - Covered countries/regions
    - Excluded countries
    - Geographic restrictions
    - Regional coverage (e.g., "Worldwide except USA")
    """
    
    def __init__(self, vector_store, qa_system: Optional[PolicyQASystem] = None):
        """
        Initialize the country eligibility checker.
        
        Args:
            vector_store: VectorStore instance for searching policy documents
            qa_system: Optional Q&A system (will create one if not provided)
        """
        self.vector_store = vector_store
        self.qa_system = qa_system or PolicyQASystem(vector_store)
        
        # Common country names and variations for better matching
        self.country_aliases = {
            'usa': ['united states', 'united states of america', 'us', 'u.s.a.', 'u.s.'],
            'uk': ['united kingdom', 'great britain', 'britain', 'england', 'scotland', 'wales'],
            'uae': ['united arab emirates', 'emirates'],
            'sg': ['singapore'],
            'my': ['malaysia'],
            'th': ['thailand'],
            'id': ['indonesia'],
            'ph': ['philippines'],
            'vn': ['vietnam'],
            'hk': ['hong kong'],
            'jp': ['japan'],
            'kr': ['south korea', 'korea'],
            'cn': ['china', 'people\'s republic of china', 'prc'],
            'in': ['india'],
            'au': ['australia'],
            'nz': ['new zealand'],
            'fr': ['france'],
            'de': ['germany'],
            'it': ['italy'],
            'es': ['spain'],
            'nl': ['netherlands'],
            'be': ['belgium'],
            'ch': ['switzerland'],
            'at': ['austria'],
            'se': ['sweden'],
            'no': ['norway'],
            'dk': ['denmark'],
            'fi': ['finland'],
            'pl': ['poland'],
            'cz': ['czech republic', 'czechia'],
            'pt': ['portugal'],
            'gr': ['greece'],
            'ie': ['ireland'],
            'br': ['brazil'],
            'mx': ['mexico'],
            'ca': ['canada'],
            'ar': ['argentina'],
            'cl': ['chile'],
            'co': ['colombia'],
            'pe': ['peru'],
            'za': ['south africa'],
            'eg': ['egypt'],
            'sa': ['saudi arabia'],
            'tr': ['turkey'],
            'il': ['israel'],
            'ae': ['united arab emirates'],
        }
    
    def check_country_eligibility(self, policy_name: str, country: str) -> Dict[str, any]:
        """
        Check if a specific policy is eligible for a given country.
        
        Args:
            policy_name: Name of the policy to check
            country: Country name to check eligibility for
            
        Returns:
            Dictionary with eligibility status, details, and citations
        """
        # Normalize country name
        country_normalized = self._normalize_country_name(country)
        
        # Ask questions about country coverage
        questions = [
            f"Does this policy provide coverage for {country_normalized}?",
            f"Can this policy be used in {country_normalized}?",
            f"Is {country_normalized} included in the coverage area?",
            f"Are there any restrictions for {country_normalized}?"
        ]
        
        results = []
        for question in questions:
            result = self.qa_system.answer_question(
                question=question,
                policy_filter=policy_name,
                include_citations=True
            )
            results.append(result)
        
        # Extract eligibility information from answers
        eligibility_info = self._extract_eligibility_from_answers(results, country_normalized)
        
        # Get explicit country lists if available
        country_lists = self._extract_country_lists(policy_name)
        
        return {
            'policy_name': policy_name,
            'country': country,
            'country_normalized': country_normalized,
            'eligibility_status': eligibility_info['status'],  # 'eligible', 'not_eligible', 'unknown'
            'details': eligibility_info['details'],
            'citations': results[0]['citations'] if results else [],
            'covered_countries': country_lists.get('covered', []),
            'excluded_countries': country_lists.get('excluded', []),
            'raw_answers': [r['answer'] for r in results[:2]]  # First 2 answers
        }
    
    def check_multiple_countries(self, policy_name: str, countries: List[str]) -> Dict[str, any]:
        """
        Check eligibility for multiple countries at once.
        
        Args:
            policy_name: Name of the policy to check
            countries: List of country names
            
        Returns:
            Dictionary mapping each country to its eligibility status
        """
        results = {}
        
        for country in countries:
            result = self.check_country_eligibility(policy_name, country)
            results[country] = {
                'eligible': result['eligibility_status'] == 'eligible',
                'status': result['eligibility_status'],
                'details': result['details']
            }
        
        return {
            'policy_name': policy_name,
            'countries_checked': countries,
            'results': results,
            'summary': self._generate_country_summary(results)
        }
    
    def get_all_covered_countries(self, policy_name: str) -> Dict[str, any]:
        """
        Extract list of all countries covered by a policy.
        
        Args:
            policy_name: Name of the policy
            
        Returns:
            Dictionary with covered and excluded countries
        """
        # Ask specific questions about coverage areas
        question = "List all countries, regions, or geographic areas where this policy provides coverage. Also list any excluded countries or regions."
        
        result = self.qa_system.answer_question(
            question=question,
            policy_filter=policy_name,
            include_citations=True
        )
        
        # Extract country lists from answer
        country_lists = self._extract_country_lists(policy_name)
        
        # Also parse the LLM answer for additional countries
        parsed_countries = self._parse_countries_from_text(result['answer'])
        
        return {
            'policy_name': policy_name,
            'covered_countries': list(set(country_lists.get('covered', []) + parsed_countries.get('covered', []))),
            'excluded_countries': list(set(country_lists.get('excluded', []) + parsed_countries.get('excluded', []))),
            'coverage_description': result['answer'],
            'citations': result['citations']
        }
    
    def _normalize_country_name(self, country: str) -> str:
        """
        Normalize country name to handle variations.
        
        Args:
            country: Country name (may be in various formats)
            
        Returns:
            Normalized country name
        """
        country_lower = country.lower().strip()
        
        # Check if country matches any aliases
        for canonical, aliases in self.country_aliases.items():
            if country_lower == canonical.lower() or country_lower in [a.lower() for a in aliases]:
                # Return full country name for better matching
                return aliases[0].title() if aliases else canonical.title()
        
        # Return title-cased version
        return country.title()
    
    def _extract_eligibility_from_answers(self, results: List[Dict], country: str) -> Dict:
        """
        Extract eligibility status from LLM answers.
        
        Args:
            results: List of Q&A results
            country: Country being checked
            
        Returns:
            Dictionary with status and details
        """
        # Combine all answers
        combined_text = " ".join([r['answer'].lower() for r in results])
        
        # Keywords indicating eligibility
        eligible_keywords = ['yes', 'covered', 'included', 'eligible', 'provides coverage', 'covers', 'applicable']
        not_eligible_keywords = ['no', 'not covered', 'excluded', 'not eligible', 'restricted', 'does not cover', 'not applicable']
        
        eligible_count = sum(1 for keyword in eligible_keywords if keyword in combined_text)
        not_eligible_count = sum(1 for keyword in not_eligible_keywords if keyword in combined_text)
        
        # Determine status
        if eligible_count > not_eligible_count:
            status = 'eligible'
        elif not_eligible_count > eligible_count:
            status = 'not_eligible'
        else:
            status = 'unknown'
        
        # Extract details from first answer
        details = results[0]['answer'] if results else "No information available"
        
        return {
            'status': status,
            'details': details
        }
    
    def _extract_country_lists(self, policy_name: str) -> Dict[str, List[str]]:
        """
        Extract explicit lists of covered/excluded countries from policy.
        
        Args:
            policy_name: Name of policy
            
        Returns:
            Dictionary with 'covered' and 'excluded' country lists
        """
        # Search for coverage area information
        search_results = self.vector_store.search(
            query="covered countries regions geographic coverage area eligible countries",
            top_k=10,
            policy_filter=policy_name
        )
        
        covered = []
        excluded = []
        
        for result in search_results:
            text = result['text'].lower()
            
            # Look for patterns like "covered countries: X, Y, Z"
            # This is a simple extraction - could be enhanced with LLM
            # Common patterns
            if 'covered countries' in text or 'countries covered' in text:
                # Try to extract country names (simplified)
                # In production, use LLM or NER to extract proper country names
                pass
        
        return {
            'covered': covered,
            'excluded': excluded
        }
    
    def _parse_countries_from_text(self, text: str) -> Dict[str, List[str]]:
        """
        Parse country names from text using simple pattern matching.
        
        Args:
            text: Text containing country information
            
        Returns:
            Dictionary with 'covered' and 'excluded' countries
        """
        covered = []
        excluded = []
        
        # Simple keyword-based extraction
        # In production, use NER or LLM to extract country names properly
        text_lower = text.lower()
        
        # Check for common patterns
        if 'worldwide' in text_lower or 'global' in text_lower:
            covered.append('Worldwide')
        
        if 'except' in text_lower:
            # Countries after "except" are likely excluded
            pass
        
        return {
            'covered': covered,
            'excluded': excluded
        }
    
    def _generate_country_summary(self, results: Dict) -> str:
        """
        Generate a summary of country eligibility results.
        
        Args:
            results: Dictionary mapping countries to eligibility results
            
        Returns:
            Summary string
        """
        eligible = [country for country, data in results.items() if data['eligible']]
        not_eligible = [country for country, data in results.items() if not data['eligible']]
        unknown = [country for country, data in results.items() if data['status'] == 'unknown']
        
        summary = f"Eligibility Summary:\n"
        summary += f"  ✓ Eligible: {len(eligible)} countries - {', '.join(eligible[:5])}"
        if len(eligible) > 5:
            summary += f" and {len(eligible) - 5} more"
        summary += f"\n  ✗ Not Eligible: {len(not_eligible)} countries"
        if not_eligible:
            summary += f" - {', '.join(not_eligible[:5])}"
        if len(not_eligible) > 5:
            summary += f" and {len(not_eligible) - 5} more"
        if unknown:
            summary += f"\n  ? Unknown: {len(unknown)} countries - {', '.join(unknown)}"
        
        return summary


# Example usage (for testing)
if __name__ == "__main__":
    # from vector_store import VectorStore
    # store = VectorStore()
    # checker = CountryEligibilityChecker(store)
    # 
    # # Check single country
    # result = checker.check_country_eligibility("Travel Insurance Gold", "Singapore")
    # print(result)
    # 
    # # Check multiple countries
    # results = checker.check_multiple_countries("Travel Insurance Gold", ["Singapore", "Malaysia", "Thailand"])
    # print(results)
    pass
