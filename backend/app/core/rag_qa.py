"""
RAG Q&A Module (Retrieval-Augmented Generation)
===============================================
This module combines semantic search with LLM to answer questions
with accurate citations from policy documents.

Uses Ollama for local LLM inference (no API required).
"""

from typing import List, Dict, Optional
import ollama
from dotenv import load_dotenv
import os

load_dotenv()


class PolicyQASystem:
    """
    Question-Answering system that uses RAG (Retrieval-Augmented Generation).
    
    RAG Workflow:
    1. User asks a question
    2. System retrieves relevant policy chunks using semantic search
    3. LLM (Ollama) generates answer based on retrieved chunks + question
    4. Answer includes citations (section, page) for transparency
    """
    
    def __init__(self, vector_store, llm_model: str = "llama3"):
        """
        Initialize the Q&A system with Ollama.
        
        Args:
            vector_store: VectorStore instance for semantic search
            llm_model: Ollama model to use (default: "llama3")
                     Other options: "mistral", "llama2", "codellama", etc.
                     Run: ollama list (to see available models)
        """
        self.llm_model = llm_model
        self.vector_store = vector_store
        
        # Verify Ollama is running and model is available
        try:
            # Test connection to Ollama
            ollama.list()
            print(f"✓ Ollama connected, using model: {llm_model}")
        except Exception as e:
            print(f"⚠ Warning: Could not connect to Ollama: {e}")
            print("  Make sure Ollama is running: ollama serve")
            print(f"  Make sure model is downloaded: ollama pull {llm_model}")
    
    def format_citation(self, metadata: Dict) -> str:
        """
        Format metadata into a readable citation.
        
        Example: "Section 3.2, page 15, Travel Insurance Gold Policy"
        
        Args:
            metadata: Chunk metadata dictionary
            
        Returns:
            Formatted citation string
        """
        citation_parts = []
        
        # Add section if available
        if 'section_title' in metadata:
            citation_parts.append(metadata['section_title'])
        
        # Add page number if available
        if 'page_number' in metadata:
            citation_parts.append(f"page {metadata['page_number']}")
        
        # Add policy name if available
        if 'policy_name' in metadata:
            citation_parts.append(metadata['policy_name'] + " Policy")
        
        return ", ".join(citation_parts) if citation_parts else "Policy Document"
    
    def answer_question(
        self, 
        question: str, 
        top_k: int = 5,
        policy_filter: Optional[str] = None,
        include_citations: bool = True
    ) -> Dict[str, any]:
        """
        Answer a question about policy documents using RAG with Ollama.
        
        Process:
        1. Search vector database for relevant chunks
        2. Format chunks as context
        3. Send question + context to Ollama LLM
        4. Extract answer with citations
        
        Args:
            question: User's question
            top_k: Number of relevant chunks to retrieve
            policy_filter: Optional filter for specific policy
            include_citations: Whether to include citations in answer
            
        Returns:
            Dictionary with answer, citations, and source chunks
        """
        # Step 1: Retrieve relevant chunks from vector database
        relevant_chunks = self.vector_store.search(
            query=question,
            top_k=top_k,
            policy_filter=policy_filter
        )
        
        if not relevant_chunks:
            return {
                'answer': "I couldn't find relevant information in the policy documents to answer this question.",
                'citations': [],
                'source_chunks': [],
                'question': question
            }
        
        # Step 2: Format retrieved chunks as context for LLM
        context_parts = []
        citations = []
        
        for chunk in relevant_chunks:
            # Extract text and metadata
            chunk_text = chunk['text']
            metadata = chunk['metadata']
            
            # Format citation
            citation = self.format_citation(metadata)
            citations.append(citation)
            
            # Add to context with citation
            context_parts.append(
                f"[{citation}]\n{chunk_text}"
            )
        
        # Combine all context
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 3: Create prompt for LLM
        prompt = f"""You are an expert insurance policy assistant. Answer the user's question based ONLY on the provided policy document excerpts.

Policy Document Excerpts:
{context}

User Question: {question}

Instructions:
- Answer the question accurately based on the provided excerpts
- If the information is not in the excerpts, say so clearly
- Include specific details like coverage amounts, limits, and conditions
- If citations are requested, reference the section/page information provided
- Be concise but complete

Answer:"""
        
        # Step 4: Generate answer using Ollama LLM
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.1,  # Low temperature for more consistent, factual answers
                    'top_p': 0.9,
                    'num_predict': 500  # Max tokens to generate
                }
            )
            
            answer = response['response']
        except Exception as e:
            # Fallback if Ollama fails
            answer = f"Error generating answer: {str(e)}\n\nRelevant information found:\n"
            for chunk in relevant_chunks[:2]:
                answer += f"\n{chunk['text'][:200]}...\n"
        
        # Step 5: Format response with citations if requested
        if include_citations and citations:
            # Add citations to the end of the answer
            unique_citations = list(set(citations))  # Remove duplicates
            citation_text = "\n\nSources: " + "; ".join(unique_citations)
            answer = answer + citation_text
        
        return {
            'answer': answer,
            'citations': unique_citations if include_citations else [],
            'source_chunks': relevant_chunks,
            'question': question
        }
    
    def answer_with_explicit_citations(self, question: str, policy_filter: Optional[str] = None) -> Dict[str, any]:
        """
        Answer question with explicit inline citations (e.g., "Section 3.2").
        Useful for more detailed responses.
        
        Args:
            question: User's question
            policy_filter: Optional filter for specific policy
            
        Returns:
            Dictionary with answer and citations
        """
        # Get answer
        result = self.answer_question(question, policy_filter=policy_filter, include_citations=True)
        
        # Enhance answer with inline citations
        answer = result['answer']
        source_chunks = result['source_chunks']
        
        # Add more detailed citations inline
        if source_chunks:
            detailed_answer = answer + "\n\n\nDetailed References:\n"
            for i, chunk in enumerate(source_chunks[:3], 1):  # Top 3 chunks
                metadata = chunk['metadata']
                citation = self.format_citation(metadata)
                similarity = chunk['similarity_score']
                detailed_answer += f"\n{i}. {citation} (Relevance: {similarity:.1f}%)\n"
                detailed_answer += f"   Excerpt: {chunk['text'][:200]}...\n"
        
        result['answer'] = detailed_answer if source_chunks else answer
        return result


# Example usage (for testing)
if __name__ == "__main__":
    # This would be used with VectorStore
    # from vector_store import VectorStore
    # store = VectorStore()
    # qa = PolicyQASystem(store)
    # 
    # result = qa.answer_question("Does this policy cover food poisoning?")
    # print(result['answer'])
    pass
