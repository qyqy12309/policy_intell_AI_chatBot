"""
Example Usage Script
===================
This script demonstrates how to use the Policy Intelligence Engine
programmatically (without the API server).
"""

from pipeline import PolicyPipeline
from vector_store import VectorStore
from rag_qa import PolicyQASystem
from policy_comparison import PolicyComparator


def example_full_workflow():
    """
    Complete example: Upload, process, and query a policy document.
    """
    print("=" * 60)
    print("Policy Intelligence Engine - Example Usage")
    print("=" * 60)
    
    # Step 1: Initialize components
    print("\n[1] Initializing components...")
    vector_store = VectorStore(db_path="./chroma_db")
    pipeline = PolicyPipeline(vector_store)
    qa_system = PolicyQASystem(vector_store)
    
    # Step 2: Process a policy document
    print("\n[2] Processing policy document...")
    # Replace with your actual policy file path
    policy_file = "sample_policy.pdf"  # Change this to your PDF
    
    try:
        result = pipeline.process_document(policy_file, policy_name="Travel Insurance Gold")
        print(f"✓ Successfully processed: {result['chunks_count']} chunks created")
    except FileNotFoundError:
        print(f"⚠ File not found: {policy_file}")
        print("   Please update 'policy_file' variable with your policy PDF path")
        return
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return
    
    # Step 3: Ask questions about the policy
    print("\n[3] Asking questions about the policy...")
    
    questions = [
        "What is the medical expense coverage limit?",
        "Does this policy cover food poisoning?",
        "What are the main exclusions?",
        "What is the baggage loss coverage?"
    ]
    
    for question in questions:
        print(f"\nQ: {question}")
        result = qa_system.answer_question(question, policy_filter="Travel Insurance Gold")
        print(f"A: {result['answer']}")
        if result['citations']:
            print(f"   Sources: {', '.join(result['citations'][:2])}")  # Show first 2 citations
    
    # Step 4: List all policies
    print("\n[4] Listing all policies in database...")
    policies = vector_store.list_policies()
    print(f"✓ Found {len(policies)} policies: {', '.join(policies)}")


def example_comparison():
    """
    Example: Compare multiple policies.
    """
    print("\n" + "=" * 60)
    print("Policy Comparison Example")
    print("=" * 60)
    
    # Initialize
    vector_store = VectorStore(db_path="./chroma_db")
    comparator = PolicyComparator(vector_store)
    
    # Compare policies (replace with your actual policy names)
    policy_names = ["Travel Insurance Gold", "Travel Insurance Silver", "Travel Insurance Bronze"]
    
    # Filter to only existing policies
    existing_policies = vector_store.list_policies()
    policy_names = [p for p in policy_names if p in existing_policies]
    
    if len(policy_names) < 2:
        print(f"⚠ Need at least 2 policies for comparison. Found: {existing_policies}")
        return
    
    print(f"\nComparing policies: {', '.join(policy_names)}")
    result = comparator.compare_policies(policy_names)
    
    print("\nComparison Summary:")
    print(result['summary'])
    
    print("\nComparison Table:")
    for row in result['comparison_table']:
        print(f"\n{row['Category']}:")
        for policy in policy_names:
            if policy in row:
                print(f"  • {policy}: {row[policy][:100]}...")  # First 100 chars


def example_single_question():
    """
    Simple example: Just ask a question (assuming documents are already processed).
    """
    print("\n" + "=" * 60)
    print("Simple Q&A Example")
    print("=" * 60)
    
    # Initialize Q&A system
    vector_store = VectorStore(db_path="./chroma_db")
    qa_system = PolicyQASystem(vector_store)
    
    # Check if any policies exist
    policies = vector_store.list_policies()
    if not policies:
        print("⚠ No policies found. Please process a document first using:")
        print("   pipeline.process_document('your_policy.pdf', 'Policy Name')")
        return
    
    print(f"\nAvailable policies: {', '.join(policies)}")
    
    # Ask a question
    question = "What is the maximum coverage amount for medical expenses?"
    print(f"\nQ: {question}")
    
    result = qa_system.answer_question(question)
    print(f"\nA: {result['answer']}")
    
    if result['citations']:
        print(f"\nSources: {result['citations'][0]}")


if __name__ == "__main__":
    """
    Run examples. Uncomment the example you want to try.
    """
    
    # Run full workflow (process document + ask questions)
    # example_full_workflow()
    
    # Run comparison example
    # example_comparison()
    
    # Run simple Q&A (requires existing processed documents)
    example_single_question()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

