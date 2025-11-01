"""
Batch Policy Processor
======================
Processes multiple policy PDFs in batch, extracts information,
and checks country eligibility for each policy.
"""

import os
from typing import List, Dict, Optional
from pathlib import Path
from .pipeline import PolicyPipeline
from .vector_store import VectorStore
from .rag_qa import PolicyQASystem
from .country_eligibility import CountryEligibilityChecker
import json


class BatchPolicyProcessor:
    """
    Processes multiple policy documents in batch.
    
    Workflow:
    1. Load all PDFs from a directory
    2. Process each PDF (extract, chunk, embed, store)
    3. Analyze each policy for country eligibility
    4. Generate comprehensive report
    """
    
    def __init__(self, db_path: str = "./chroma_db", llm_model: str = "llama3"):
        """
        Initialize the batch processor.
        
        Args:
            db_path: Path to ChromaDB database
            llm_model: Ollama model to use
        """
        # Initialize components
        self.vector_store = VectorStore(db_path=db_path)
        self.pipeline = PolicyPipeline(self.vector_store)
        self.qa_system = PolicyQASystem(self.vector_store, llm_model=llm_model)
        self.country_checker = CountryEligibilityChecker(self.vector_store, self.qa_system)
        self.llm_model = llm_model
        
        print(f"✓ Batch processor initialized with model: {llm_model}")
    
    def process_batch(
        self, 
        pdf_directory: str,
        countries_to_check: Optional[List[str]] = None,
        policy_name_prefix: Optional[str] = None
    ) -> Dict:
        """
        Process all PDFs in a directory.
        
        Args:
            pdf_directory: Directory containing PDF files
            countries_to_check: Optional list of countries to check eligibility for
            policy_name_prefix: Optional prefix for policy names (uses filename if not provided)
            
        Returns:
            Dictionary with processing results and analysis
        """
        # Find all PDF files
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        
        if not pdf_files:
            return {
                'success': False,
                'error': f"No PDF files found in {pdf_directory}",
                'files_found': 0
            }
        
        print(f"\n{'='*60}")
        print(f"Batch Processing: {len(pdf_files)} PDFs found")
        print(f"{'='*60}\n")
        
        results = {
            'total_files': len(pdf_files),
            'processed_files': [],
            'failed_files': [],
            'policies': {},
            'country_eligibility': {}
        }
        
        # Process each PDF
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            
            # Generate policy name from filename
            policy_name = policy_name_prefix + "_" + Path(pdf_file).stem if policy_name_prefix else Path(pdf_file).stem
            policy_name = policy_name.replace("_", " ").title()  # Clean up name
            
            try:
                # Step 1: Process document (extract, chunk, embed, store)
                process_result = self.pipeline.process_document(str(pdf_file), policy_name)
                
                print(f"  ✓ Processed: {process_result['chunks_count']} chunks created")
                
                results['processed_files'].append({
                    'file': pdf_file.name,
                    'policy_name': policy_name,
                    'chunks': process_result['chunks_count'],
                    'pages': process_result.get('pages', 'N/A')
                })
                
                # Step 2: Extract key information about the policy
                policy_info = self._extract_policy_summary(policy_name)
                
                # Step 3: Check country eligibility if countries provided
                country_eligibility = None
                if countries_to_check:
                    print(f"  Checking country eligibility...")
                    country_eligibility = self.country_checker.check_multiple_countries(
                        policy_name, 
                        countries_to_check
                    )
                
                # Store results
                results['policies'][policy_name] = {
                    'file_name': pdf_file.name,
                    'summary': policy_info,
                    'country_eligibility': country_eligibility
                }
                
                if country_eligibility:
                    results['country_eligibility'][policy_name] = country_eligibility
                
                print(f"  ✓ Completed\n")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}\n")
                results['failed_files'].append({
                    'file': pdf_file.name,
                    'error': str(e)
                })
        
        # Generate summary report
        results['summary'] = self._generate_summary_report(results)
        
        return results
    
    def _extract_policy_summary(self, policy_name: str) -> Dict:
        """
        Extract key information about a policy.
        
        Args:
            policy_name: Name of the policy
            
        Returns:
            Dictionary with policy summary information
        """
        # Ask key questions about the policy
        questions = {
            "coverage_type": "What type of insurance does this policy provide? (travel, health, etc.)",
            "coverage_area": "What countries or regions does this policy cover?",
            "main_benefits": "What are the main benefits and coverage amounts?",
            "exclusions": "What are the main exclusions or limitations?",
            "duration": "What is the policy duration or validity period?"
        }
        
        summary = {}
        for key, question in questions.items():
            try:
                result = self.qa_system.answer_question(
                    question=question,
                    policy_filter=policy_name,
                    include_citations=False
                )
                summary[key] = result['answer']
            except:
                summary[key] = "Information not available"
        
        return summary
    
    def _generate_summary_report(self, results: Dict) -> str:
        """
        Generate a human-readable summary report.
        
        Args:
            results: Processing results dictionary
            
        Returns:
            Summary report string
        """
        report = f"""
{'='*60}
BATCH PROCESSING SUMMARY REPORT
{'='*60}

Total Files: {results['total_files']}
Successfully Processed: {len(results['processed_files'])}
Failed: {len(results['failed_files'])}

Processed Policies:
"""
        for policy_info in results['processed_files']:
            report += f"  • {policy_info['policy_name']} ({policy_info['file']})\n"
            report += f"    - Chunks: {policy_info['chunks']}, Pages: {policy_info['pages']}\n"
        
        if results['failed_files']:
            report += f"\nFailed Files:\n"
            for failed in results['failed_files']:
                report += f"  • {failed['file']}: {failed['error']}\n"
        
        if results['country_eligibility']:
            report += f"\n{'='*60}\nCOUNTRY ELIGIBILITY SUMMARY\n{'='*60}\n"
            for policy_name, eligibility in results['country_eligibility'].items():
                report += f"\n{policy_name}:\n"
                report += eligibility.get('summary', 'No summary available') + "\n"
        
        return report
    
    def export_results(self, results: Dict, output_file: str = "batch_processing_results.json"):
        """
        Export processing results to JSON file.
        
        Args:
            results: Processing results dictionary
            output_file: Output file path
        """
        # Convert to JSON-serializable format
        exportable_results = {
            'total_files': results['total_files'],
            'processed_files': results['processed_files'],
            'failed_files': results['failed_files'],
            'summary': results['summary']
        }
        
        # Export policy summaries (without full chunks to save space)
        exportable_results['policies'] = {}
        for policy_name, policy_data in results['policies'].items():
            exportable_results['policies'][policy_name] = {
                'file_name': policy_data['file_name'],
                'summary': policy_data['summary']
            }
            if policy_data.get('country_eligibility'):
                exportable_results['policies'][policy_name]['country_eligibility'] = policy_data['country_eligibility']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(exportable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Results exported to: {output_file}")


# Command-line usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python batch_processor.py <pdf_directory> [countries...]")
        print("\nExample:")
        print("  python batch_processor.py ./policies Singapore Malaysia Thailand")
        print("\nThis will:")
        print("  1. Process all PDFs in ./policies directory")
        print("  2. Check eligibility for Singapore, Malaysia, Thailand")
        sys.exit(1)
    
    pdf_dir = sys.argv[1]
    countries = sys.argv[2:] if len(sys.argv) > 2 else None
    
    # Initialize processor
    processor = BatchPolicyProcessor()
    
    # Process batch
    results = processor.process_batch(pdf_dir, countries_to_check=countries)
    
    # Print summary
    print(results['summary'])
    
    # Export results
    processor.export_results(results)
    pass
