"""
Policy Comparison Engine
=======================
This module compares multiple insurance policies side-by-side,
extracting key coverage details and presenting them clearly.
"""

from typing import List, Dict, Optional
from .rag_qa import PolicyQASystem
import pandas as pd
import ollama
from dotenv import load_dotenv
import os

load_dotenv()


class PolicyComparator:
    """
    Compares multiple insurance policies by extracting and normalizing
    coverage categories, benefits, and limits.
    
    Uses Ollama for local LLM inference.
    """
    
    def __init__(self, vector_store, qa_system: Optional[PolicyQASystem] = None, llm_model: str = "llama3"):
        """
        Initialize the policy comparator.
        
        Args:
            vector_store: VectorStore instance to search across policies
            qa_system: Optional Q&A system for extracting policy details
            llm_model: Ollama model to use (default: "llama3")
        """
        self.vector_store = vector_store
        self.qa_system = qa_system or PolicyQASystem(vector_store, llm_model=llm_model)
        self.llm_model = llm_model
    
    def extract_coverage_details(self, policy_name: str, coverage_categories: List[str]) -> Dict[str, any]:
        """
        Extract coverage details for specific categories from a policy.
        
        Process:
        1. Ask structured questions about each coverage category
        2. Extract limits, conditions, and details
        3. Normalize responses into structured format
        
        Args:
            policy_name: Name of policy to analyze
            coverage_categories: List of categories (e.g., ["Medical", "Baggage", "Trip Delay"])
            
        Returns:
            Dictionary mapping categories to their details
        """
        coverage_data = {}
        
        # Standard questions for each category
        category_questions = {
            "Medical": "What is the medical expense coverage limit and what does it cover?",
            "Baggage": "What is the baggage loss or damage coverage limit?",
            "Trip Delay": "What is the trip delay coverage and conditions?",
            "Trip Cancellation": "What is the trip cancellation coverage limit and conditions?",
            "Emergency Evacuation": "What is the emergency evacuation coverage?",
            "Personal Accident": "What is the personal accident death benefit coverage?",
            "Exclusions": "What are the main exclusions in this policy?"
        }
        
        # Extract details for each category
        for category in coverage_categories:
            # Get question for this category (or use default)
            question = category_questions.get(category, f"What is the {category} coverage in this policy?")
            
            # Ask the question filtered to this policy
            result = self.qa_system.answer_question(
                question=question,
                policy_filter=policy_name,
                include_citations=True
            )
            
            coverage_data[category] = {
                'description': result['answer'],
                'citations': result['citations']
            }
        
        return coverage_data
    
    def compare_policies(
        self, 
        policy_names: List[str],
        coverage_categories: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Compare multiple policies side-by-side.
        
        Process:
        1. Extract coverage details for each policy
        2. Normalize into comparable format
        3. Create comparison table
        
        Args:
            policy_names: List of policy names to compare
            coverage_categories: Optional list of specific categories to compare
            
        Returns:
            Dictionary with comparison table and summary
        """
        # Default categories if none specified
        if coverage_categories is None:
            coverage_categories = [
                "Medical", "Baggage", "Trip Delay", 
                "Trip Cancellation", "Emergency Evacuation", "Personal Accident"
            ]
        
        # Extract details for each policy
        all_policy_data = {}
        for policy_name in policy_names:
            print(f"Extracting details for {policy_name}...")
            policy_data = self.extract_coverage_details(policy_name, coverage_categories)
            all_policy_data[policy_name] = policy_data
        
        # Create comparison DataFrame (table format)
        comparison_rows = []
        
        for category in coverage_categories:
            row = {'Category': category}
            
            # Add data for each policy
            for policy_name in policy_names:
                category_data = all_policy_data[policy_name].get(category, {})
                # Extract key information (limits, amounts) using LLM
                description = category_data.get('description', 'N/A')
                
                # Try to extract structured data (amounts, limits) from description
                structured_info = self._extract_structured_info(description, category)
                row[policy_name] = structured_info
            
            comparison_rows.append(row)
        
        # Create DataFrame
        comparison_df = pd.DataFrame(comparison_rows)
        
        # Generate conversational summary
        summary = self._generate_comparison_summary(all_policy_data, policy_names)
        
        return {
            'comparison_table': comparison_df.to_dict('records'),  # Convert to list of dicts for JSON
            'summary': summary,
            'policies': policy_names,
            'categories': coverage_categories
        }
    
    def _extract_structured_info(self, description: str, category: str) -> str:
        """
        Extract structured information (amounts, limits) from text description.
        Uses Ollama LLM to parse and normalize coverage details.
        
        Args:
            description: Full text description from Q&A
            category: Coverage category name
            
        Returns:
            Concise summary with key numbers and limits
        """
        prompt = f"""Extract the key coverage details from this text. Focus on:
- Coverage amounts/limits (currency and numbers)
- Main conditions or restrictions
- What is covered

Category: {category}
Description: {description}

Provide a concise summary (2-3 sentences max) with specific numbers:"""
        
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.1,
                    'num_predict': 200
                }
            )
            return response['response']
        except:
            # Fallback to first 200 chars if extraction fails
            return description[:200] + "..." if len(description) > 200 else description
    
    def _generate_comparison_summary(self, all_policy_data: Dict, policy_names: List[str]) -> str:
        """
        Generate a conversational summary comparing policies.
        
        Args:
            all_policy_data: Dictionary mapping policy names to their coverage data
            policy_names: List of policy names
            
        Returns:
            Natural language summary of the comparison
        """
        summary_parts = [f"Comparing {len(policy_names)} policies: {', '.join(policy_names)}\n\n"]
        
        # Compare each category
        categories = list(next(iter(all_policy_data.values())).keys())
        
        for category in categories:
            summary_parts.append(f"{category} Coverage:\n")
            
            for policy_name in policy_names:
                category_data = all_policy_data[policy_name].get(category, {})
                description = category_data.get('description', 'N/A')
                # Get first sentence or key info
                key_info = description.split('.')[0] if description != 'N/A' else 'N/A'
                summary_parts.append(f"  • {policy_name}: {key_info}\n")
            
            summary_parts.append("\n")
        
        return "".join(summary_parts)
    
    def compare_specific_category(self, policy_names: List[str], category: str) -> Dict[str, any]:
        """
        Compare a specific coverage category across multiple policies.
        More detailed than full comparison.
        
        Args:
            policy_names: List of policies to compare
            category: Specific category to compare (e.g., "Medical", "Baggage")
            
        Returns:
            Detailed comparison for this category
        """
        category_data = {}
        
        for policy_name in policy_names:
            result = self.qa_system.answer_question(
                question=f"What is the {category} coverage, including limits and conditions?",
                policy_filter=policy_name,
                include_citations=True
            )
            category_data[policy_name] = {
                'answer': result['answer'],
                'citations': result['citations'],
                'source_chunks': result['source_chunks']
            }
        
        # Generate comparison summary
        comparison_text = f"Comparison of {category} Coverage:\n\n"
        for policy_name in policy_names:
            comparison_text += f"{policy_name}:\n{category_data[policy_name]['answer']}\n\n"
        
        return {
            'category': category,
            'policies': policy_names,
            'detailed_comparison': category_data,
            'summary': comparison_text
        }


# Example usage (for testing)
if __name__ == "__main__":
    # This would be used with VectorStore and QASystem
    # from vector_store import VectorStore
    # store = VectorStore()
    # comparator = PolicyComparator(store)
    # 
    # result = comparator.compare_policies(["Gold Plan", "Silver Plan", "Bronze Plan"])
    # print(result['summary'])
    pass
