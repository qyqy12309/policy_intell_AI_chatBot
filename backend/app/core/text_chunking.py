"""
Text Chunking and Preprocessing Module
======================================
This module splits long policy documents into smaller, manageable chunks.
Each chunk is labeled with metadata (section, page, policy name) for better retrieval.
"""

import re
from typing import List, Dict, Optional
import tiktoken


class TextChunker:
    """
    Splits policy documents into semantic chunks for better embedding and retrieval.
    
    Why chunking?
    - Policy documents are too long for LLMs to process at once
    - Chunks allow precise retrieval of relevant sections
    - Metadata helps provide context and citations
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target number of tokens per chunk (default 500)
            chunk_overlap: Number of overlapping tokens between chunks (prevents context loss)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize tokenizer for counting tokens (GPT-style)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        Uses OpenAI's tokenizer (same as GPT models).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))
    
    def split_by_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Split text by section headers (e.g., "Section 1.1:", "CHAPTER 2").
        This preserves document structure and improves semantic search.
        
        Args:
            text: Full document text
            
        Returns:
            List of dictionaries, each with 'text' and detected 'section_title'
        """
        # Pattern to detect section headers (e.g., "Section 3.2", "CHAPTER 1", "Article 5")
        section_pattern = r'(?i)(?:Section|Chapter|Article|Part)\s+\d+(?:\.\d+)*[:\-]?\s*(.*?)(?=\n)'
        
        sections = []
        matches = list(re.finditer(section_pattern, text))
        
        # If no sections found, treat entire document as one section
        if not matches:
            return [{'text': text, 'section_title': 'Document'}]
        
        # Split text based on section markers
        for i, match in enumerate(matches):
            # Find the start position of this section
            start_pos = match.start()
            
            # Find the end position (start of next section or end of text)
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)
            
            # Extract section text
            section_text = text[start_pos:end_pos].strip()
            section_title = match.group(0).strip()
            
            if section_text:
                sections.append({
                    'text': section_text,
                    'section_title': section_title
                })
        
        return sections
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict[str, any]]:
        """
        Main method to chunk text into smaller pieces.
        
        Process:
        1. First split by sections (if detectable)
        2. Then split large sections into smaller chunks
        3. Add metadata to each chunk
        
        Args:
            text: Text to chunk
            metadata: Dictionary with document metadata (file_name, policy_name, etc.)
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Default metadata if none provided
        if metadata is None:
            metadata = {}
        
        # First, try to split by sections for better structure
        sections = self.split_by_sections(text)
        
        all_chunks = []
        
        # Process each section
        for section in sections:
            section_text = section['text']
            section_title = section['section_title']
            
            # Count tokens in this section
            token_count = self.count_tokens(section_text)
            
            # If section is small enough, keep it as one chunk
            if token_count <= self.chunk_size:
                chunk = {
                    'text': section_text,
                    'chunk_index': len(all_chunks),
                    'section_title': section_title,
                    **metadata  # Spread metadata (file_name, policy_name, etc.)
                }
                all_chunks.append(chunk)
            
            # Otherwise, split section into smaller chunks
            else:
                # Split by paragraphs first (natural breakpoints)
                paragraphs = section_text.split('\n\n')
                
                current_chunk = ""
                current_tokens = 0
                chunk_index = len(all_chunks)
                
                for para in paragraphs:
                    para_tokens = self.count_tokens(para)
                    
                    # If adding this paragraph exceeds chunk size, save current chunk
                    if current_tokens + para_tokens > self.chunk_size and current_chunk:
                        # Save current chunk
                        chunk = {
                            'text': current_chunk.strip(),
                            'chunk_index': chunk_index,
                            'section_title': section_title,
                            **metadata
                        }
                        all_chunks.append(chunk)
                        chunk_index += 1
                        
                        # Start new chunk with overlap (last part of previous chunk)
                        # This prevents losing context between chunks
                        overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                        current_chunk = overlap_text + "\n\n" + para
                        current_tokens = self.count_tokens(current_chunk)
                    
                    # If single paragraph is too large, split by sentences
                    elif para_tokens > self.chunk_size:
                        # Save current chunk first
                        if current_chunk:
                            chunk = {
                                'text': current_chunk.strip(),
                                'chunk_index': chunk_index,
                                'section_title': section_title,
                                **metadata
                            }
                            all_chunks.append(chunk)
                            chunk_index += 1
                            current_chunk = ""
                            current_tokens = 0
                        
                        # Split paragraph by sentences
                        sentences = re.split(r'[.!?]+\s+', para)
                        for sentence in sentences:
                            sent_tokens = self.count_tokens(sentence)
                            if current_tokens + sent_tokens > self.chunk_size:
                                if current_chunk:
                                    chunk = {
                                        'text': current_chunk.strip(),
                                        'chunk_index': chunk_index,
                                        'section_title': section_title,
                                        **metadata
                                    }
                                    all_chunks.append(chunk)
                                    chunk_index += 1
                                    overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                                    current_chunk = overlap_text + " " + sentence
                                    current_tokens = self.count_tokens(current_chunk)
                                else:
                                    current_chunk = sentence
                                    current_tokens = sent_tokens
                            else:
                                current_chunk += " " + sentence if current_chunk else sentence
                                current_tokens += sent_tokens
                    
                    # Normal case: add paragraph to current chunk
                    else:
                        current_chunk += "\n\n" + para if current_chunk else para
                        current_tokens += para_tokens
                
                # Don't forget the last chunk
                if current_chunk.strip():
                    chunk = {
                        'text': current_chunk.strip(),
                        'chunk_index': chunk_index,
                        'section_title': section_title,
                        **metadata
                    }
                    all_chunks.append(chunk)
        
        # Add page numbers if available in metadata
        if 'pages' in metadata:
            self._add_page_numbers(all_chunks, metadata['pages'])
        
        return all_chunks
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """
        Extract the last N tokens from text for overlap between chunks.
        This prevents losing context at chunk boundaries.
        
        Args:
            text: Text to extract from
            overlap_tokens: Number of tokens to extract
            
        Returns:
            Last N tokens as string
        """
        # Encode text to tokens
        tokens = self.tokenizer.encode(text)
        
        # Get last N tokens
        overlap_tokens_list = tokens[-overlap_tokens:] if len(tokens) > overlap_tokens else tokens
        
        # Decode back to text
        return self.tokenizer.decode(overlap_tokens_list)
    
    def _add_page_numbers(self, chunks: List[Dict], pages: List[Dict]) -> None:
        """
        Add page number information to chunks based on their content.
        This helps provide accurate citations (e.g., "see page 5").
        
        Args:
            chunks: List of chunk dictionaries to update
            pages: List of page dictionaries from document extraction
        """
        # Create a mapping of text positions to page numbers
        full_text = '\n\n'.join([page['text'] for page in pages])
        
        for chunk in chunks:
            chunk_text = chunk['text']
            
            # Find where this chunk appears in the full document
            # Simple approach: search for chunk start in full text
            position = full_text.find(chunk_text[:100])  # Use first 100 chars to find position
            
            if position != -1:
                # Calculate which page this position falls in
                current_pos = 0
                for i, page in enumerate(pages):
                    page_length = len(page['text'])
                    if current_pos <= position < current_pos + page_length:
                        chunk['page_number'] = page['page_num']
                        break
                    current_pos += page_length + 2  # +2 for \n\n
            else:
                # Default to page 1 if not found
                chunk['page_number'] = 1


# Example usage (for testing)
if __name__ == "__main__":
    # Initialize chunker
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    
    # Example: Chunk a sample text
    # sample_text = "Section 1.1: Coverage Details...\n\nSection 1.2: Exclusions..."
    # metadata = {'file_name': 'policy.pdf', 'policy_name': 'Travel Insurance Gold'}
    # chunks = chunker.chunk_text(sample_text, metadata)
    # print(f"Created {len(chunks)} chunks")
    pass
