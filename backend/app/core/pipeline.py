"""
Policy Processing Pipeline
==========================
Orchestrates the entire document processing workflow:
Upload → Extract → Chunk → Embed → Store
"""

from typing import Dict, Optional
from .document_ingestion import DocumentIngester
from .text_chunking import TextChunker
from .vector_store import VectorStore
import os


class PolicyPipeline:
    """
    Main pipeline that orchestrates document processing.
    
    Workflow:
    1. Document Ingestion: Extract text from PDF/Word
    2. Text Chunking: Split into manageable pieces
    3. Embedding & Storage: Convert to vectors and store
    """
    
    def __init__(
        self, 
        vector_store: VectorStore,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        use_ocr: bool = True
    ):
        """
        Initialize the pipeline with all components.
        
        Args:
            vector_store: VectorStore instance for storing embeddings
            chunk_size: Target tokens per chunk
            chunk_overlap: Overlapping tokens between chunks
            use_ocr: Enable OCR for scanned documents
        """
        # Initialize document ingester
        self.ingester = DocumentIngester(use_ocr=use_ocr)
        
        # Initialize text chunker
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Store vector store reference
        self.vector_store = vector_store
    
    def process_document(self, file_path: str, policy_name: str) -> Dict:
        """
        Process a policy document through the entire pipeline.
        
        Complete workflow:
        1. Extract text from document
        2. Chunk the text with metadata
        3. Generate embeddings and store in vector DB
        
        Args:
            file_path: Path to policy document
            policy_name: Name to identify this policy
            
        Returns:
            Dictionary with processing statistics
        """
        # Step 1: Extract text from document
        print(f"Step 1: Extracting text from {file_path}...")
        extracted = self.ingester.ingest_document(file_path)
        
        if 'error' in extracted:
            raise ValueError(f"Document extraction failed: {extracted['error']}")
        
        print(f"  ✓ Extracted {len(extracted['text'])} characters from {extracted['file_name']}")
        
        # Step 2: Chunk the text
        print(f"Step 2: Chunking text...")
        
        # Prepare metadata for chunks
        metadata = {
            'file_name': extracted['file_name'],
            'file_type': extracted['file_type'],
            'policy_name': policy_name
        }
        
        # Add page information if available (for PDFs)
        if 'pages' in extracted:
            metadata['pages'] = extracted['pages']
        
        # Chunk the text
        chunks = self.chunker.chunk_text(extracted['text'], metadata)
        
        print(f"  ✓ Created {len(chunks)} chunks")
        
        # Step 3: Generate embeddings and store
        print(f"Step 3: Generating embeddings and storing in vector database...")
        self.vector_store.store_chunks(chunks, policy_name=policy_name)
        
        print(f"  ✓ Stored {len(chunks)} chunks for policy '{policy_name}'")
        
        # Return processing statistics
        return {
            'policy_name': policy_name,
            'file_name': extracted['file_name'],
            'total_characters': len(extracted['text']),
            'chunks_count': len(chunks),
            'pages': extracted.get('total_pages', 'N/A')
        }
    
    def process_multiple_documents(
        self, 
        file_paths: list, 
        policy_names: Optional[list] = None
    ) -> Dict:
        """
        Process multiple documents at once.
        Useful for bulk uploads.
        
        Args:
            file_paths: List of file paths
            policy_names: Optional list of policy names (uses file names if not provided)
            
        Returns:
            Dictionary with results for each document
        """
        results = []
        
        # Use file names as policy names if not provided
        if policy_names is None:
            policy_names = [os.path.splitext(os.path.basename(f))[0] for f in file_paths]
        
        # Process each document
        for file_path, policy_name in zip(file_paths, policy_names):
            try:
                result = self.process_document(file_path, policy_name)
                results.append(result)
            except Exception as e:
                results.append({
                    'policy_name': policy_name,
                    'file_path': file_path,
                    'error': str(e)
                })
        
        return {
            'total_processed': len(results),
            'successful': len([r for r in results if 'error' not in r]),
            'failed': len([r for r in results if 'error' in r]),
            'results': results
        }


# Example usage (for testing)
if __name__ == "__main__":
    # Initialize components
    # vector_store = VectorStore()
    # pipeline = PolicyPipeline(vector_store)
    # 
    # # Process a document
    # result = pipeline.process_document("sample_policy.pdf", "Travel Insurance Gold")
    # print(f"Processed: {result}")
    pass
