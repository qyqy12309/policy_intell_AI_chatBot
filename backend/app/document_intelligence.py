"""
Document Intelligence Module
============================
Stage 3: Smart Data Extraction from User Uploads
Extracts travel information from itineraries, invoices, and other documents.
"""

from typing import Dict, List, Optional
import ollama
import json
import re
from datetime import datetime

# Import DocumentIngester if available (from core modules)
try:
    from core.document_ingestion import DocumentIngester
except ImportError:
    # Fallback: create minimal ingester if module not found
    class DocumentIngester:
        def extract_from_pdf(self, path):
            with open(path, 'rb') as f:
                return {'text': f.read().decode('utf-8', errors='ignore'), 'file_name': path}
        def extract_from_docx(self, path):
            return self.extract_from_pdf(path)


class DocumentIntelligence:
    """
    Extracts structured travel data from user-uploaded documents.
    
    Supported documents:
    - Travel itineraries (PDF, email, text)
    - Flight confirmations
    - Hotel bookings
    - Invoices
    - Screenshots (with OCR)
    """
    
    def __init__(self, llm_model: str = "llama3"):
        """
        Initialize document intelligence module.
        
        Args:
            llm_model: Ollama model to use for extraction
        """
        self.llm_model = llm_model
        self.ingester = DocumentIngester(use_ocr=True)
    
    def extract_travel_info(self, document_path: str) -> Dict:
        """
        Extract travel information from a document.
        
        Extracts:
        - Destination (country/city)
        - Departure date
        - Return date
        - Flight numbers
        - Traveler names
        - Trip duration
        - Accommodation details
        
        Args:
            document_path: Path to document file
            
        Returns:
            Dictionary with extracted travel information
        """
        # Step 1: Extract text from document
        try:
            if document_path.endswith('.pdf'):
                extracted = self.ingester.extract_from_pdf(document_path)
            elif document_path.endswith('.docx'):
                extracted = self.ingester.extract_from_docx(document_path)
            else:
                # Try as text file
                with open(document_path, 'r', encoding='utf-8') as f:
                    extracted = {'text': f.read(), 'file_name': document_path}
            
            document_text = extracted['text']
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to extract text: {str(e)}"
            }
        
        # Step 2: Use LLM to extract structured information
        prompt = f"""Extract travel information from this document. Return as JSON:

Document text:
{document_text[:3000]}  # Limit to first 3000 chars

Extract the following information (use null if not found):
- destination: Country or city (primary destination)
- departure_date: Departure date (format: YYYY-MM-DD)
- return_date: Return date (format: YYYY-MM-DD)
- duration_days: Trip duration in days (calculate if dates available)
- travelers: Array of traveler names
- traveler_count: Number of travelers
- flight_numbers: Array of flight numbers (e.g., ["SQ123", "SQ456"])
- airlines: Array of airline names
- accommodation: Hotel or accommodation name
- activities: Array of activities mentioned (e.g., ["skiing", "scuba diving"])
- trip_type: Type of trip (e.g., "business", "leisure", "adventure")

Return ONLY valid JSON, no markdown:
{{"destination": "...", "departure_date": "...", ...}}"""
        
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={'temperature': 0.1, 'num_predict': 500}
            )
            
            # Parse JSON response
            response_text = response['response'].strip()
            
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Clean up response
            response_text = response_text.strip()
            if response_text.startswith('{'):
                extracted_info = json.loads(response_text)
            else:
                # Try to find JSON object in response
                match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if match:
                    extracted_info = json.loads(match.group())
                else:
                    raise ValueError("No JSON found in response")
            
            # Calculate duration if dates available
            if extracted_info.get('departure_date') and extracted_info.get('return_date'):
                try:
                    dep = datetime.strptime(extracted_info['departure_date'], '%Y-%m-%d')
                    ret = datetime.strptime(extracted_info['return_date'], '%Y-%m-%d')
                    duration = (ret - dep).days
                    extracted_info['duration_days'] = duration
                except:
                    pass
            
            # Set traveler_count from travelers array if not set
            if extracted_info.get('travelers') and not extracted_info.get('traveler_count'):
                extracted_info['traveler_count'] = len(extracted_info['travelers'])
            
            return {
                'success': True,
                'extracted_info': extracted_info,
                'source_file': extracted.get('file_name', document_path)
            }
            
        except Exception as e:
            # Fallback: try simple pattern matching
            return self._extract_with_patterns(document_text)
    
    def _extract_with_patterns(self, text: str) -> Dict:
        """
        Fallback extraction using pattern matching.
        
        Args:
            text: Document text
            
        Returns:
            Extracted information dictionary
        """
        extracted = {
            'destination': None,
            'departure_date': None,
            'return_date': None,
            'duration_days': None,
            'traveler_count': 1,
            'flight_numbers': [],
            'activities': []
        }
        
        # Find dates (simple patterns)
        date_pattern = r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'
        dates = re.findall(date_pattern, text)
        if dates:
            extracted['departure_date'] = dates[0]
            if len(dates) > 1:
                extracted['return_date'] = dates[1]
        
        # Find flight numbers (e.g., SQ123, AA456)
        flight_pattern = r'\b([A-Z]{2}\d{3,4})\b'
        flights = re.findall(flight_pattern, text)
        if flights:
            extracted['flight_numbers'] = flights[:5]  # Limit to 5
        
        # Find country names (simple list - in production use NER)
        countries = ['Japan', 'Singapore', 'Malaysia', 'Thailand', 'USA', 'UK', 'France']
        for country in countries:
            if country.lower() in text.lower():
                extracted['destination'] = country
                break
        
        return {
            'success': True,
            'extracted_info': extracted,
            'note': 'Used pattern matching (some info may be missing)'
        }
    
    def suggest_coverage_from_trip(self, trip_info: Dict) -> Dict:
        """
        Suggest insurance coverage based on extracted trip information.
        
        Uses trip details to recommend appropriate coverage.
        
        Args:
            trip_info: Extracted trip information dictionary
            
        Returns:
            Dictionary with coverage suggestions
        """
        suggestions = {
            'recommended_coverage': [],
            'optional_coverage': [],
            'notes': []
        }
        
        destination = trip_info.get('destination', '').lower()
        activities = trip_info.get('activities', [])
        duration = trip_info.get('duration_days', 0)
        
        # Destination-based suggestions
        if any(c in destination for c in ['japan', 'snow', 'ski']):
            suggestions['recommended_coverage'].append('Winter sports coverage')
            suggestions['notes'].append('Your destination may require special coverage')
        
        if any(c in destination for c in ['island', 'beach', 'dive', 'snorkel']):
            suggestions['recommended_coverage'].append('Water sports coverage')
        
        # Activity-based suggestions
        adventure_keywords = ['ski', 'dive', 'scuba', 'hiking', 'climbing', 'parachute']
        if any(any(kw in act.lower() for kw in adventure_keywords) for act in activities):
            suggestions['recommended_coverage'].append('Adventure sports coverage')
            suggestions['notes'].append('Adventure activities detected - special coverage recommended')
        
        # Duration-based suggestions
        if duration > 30:
            suggestions['recommended_coverage'].append('Extended trip coverage')
            suggestions['notes'].append('Long trip - ensure coverage duration matches')
        
        # Default recommendations
        if not suggestions['recommended_coverage']:
            suggestions['recommended_coverage'] = [
                'Medical expenses coverage',
                'Trip cancellation coverage',
                'Baggage loss coverage'
            ]
        
        suggestions['optional_coverage'] = [
            'Travel delay coverage',
            'Emergency evacuation',
            'Personal accident coverage'
        ]
        
        return suggestions
    
    def auto_fill_quote_form(self, trip_info: Dict) -> Dict:
        """
        Auto-fill insurance quote form fields from trip information.
        
        Args:
            trip_info: Extracted trip information
            
        Returns:
            Dictionary with form field values
        """
        form_data = {
            'destination': trip_info.get('destination'),
            'departure_date': trip_info.get('departure_date'),
            'return_date': trip_info.get('return_date'),
            'duration_days': trip_info.get('duration_days'),
            'traveler_count': trip_info.get('traveler_count', 1),
            'travelers': trip_info.get('travelers', []),
            'activities': trip_info.get('activities', []),
            'trip_type': trip_info.get('trip_type', 'leisure')
        }
        
        # Add coverage suggestions
        coverage_suggestions = self.suggest_coverage_from_trip(trip_info)
        form_data['suggested_coverage'] = coverage_suggestions['recommended_coverage']
        form_data['optional_coverage'] = coverage_suggestions['optional_coverage']
        
        return form_data


# Example usage
if __name__ == "__main__":
    # doc_intel = DocumentIntelligence()
    # 
    # # Extract from itinerary
    # result = doc_intel.extract_travel_info("itinerary.pdf")
    # print(result)
    # 
    # # Auto-fill form
    # if result['success']:
    #     form_data = doc_intel.auto_fill_quote_form(result['extracted_info'])
    #     print(form_data)
    pass
