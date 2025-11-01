"""
Vector Store Module
==================
This module handles converting text chunks into embeddings and storing them
in a vector database for fast semantic search.

Uses sentence-transformers for local embeddings (no API required).
"""

import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class VectorStore:
    """
    Manages embedding generation and vector database storage.
    
    How it works:
    1. Converts text chunks into numerical embeddings (vectors) using local model
    2. Stores embeddings in ChromaDB for fast similarity search
    3. Enables semantic search: find relevant chunks even with different wording
    """
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "policy_documents", embedding_model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector store.
        
        Args:
            db_path: Path where ChromaDB will store data
            collection_name: Name of the collection to store policies
            embedding_model_name: Name of sentence-transformer model to use
                                 Options: "all-MiniLM-L6-v2" (fast), "all-mpnet-base-v2" (better quality)
        """
        # Initialize sentence-transformer model for local embeddings
        # This runs locally, no API calls needed
        print(f"Loading embedding model: {embedding_model_name}...")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        print("✓ Embedding model loaded")
        
        # Initialize ChromaDB client
        # Persistent client stores data on disk (not just in memory)
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create the collection
        # Collection is like a table in a database
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Insurance policy documents and chunks"}
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Convert text into an embedding vector using sentence-transformers.
        
        What is an embedding?
        - A list of numbers that represents the "meaning" of text
        - Similar texts have similar embeddings
        - Allows finding semantically similar content
        
        This uses a local model (runs on your machine, no API needed).
        
        Args:
            text: Text to convert to embedding
            
        Returns:
            List of floats (the embedding vector)
        """
        # Generate embedding using local sentence-transformer model
        # encode() returns a numpy array, convert to list
        embedding = self.embedding_model.encode(text, convert_to_numpy=True).tolist()
        return embedding
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts at once (faster for batches).
        
        Args:
            texts: List of texts to convert to embeddings
            
        Returns:
            List of embedding vectors
        """
        # Process in batch for efficiency
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()
    
    def store_chunks(self, chunks: List[Dict[str, any]], policy_name: Optional[str] = None) -> None:
        """
        Store text chunks in the vector database with their embeddings.
        
        Process:
        1. Generate embedding for each chunk (or batch)
        2. Create unique ID for each chunk
        3. Store in ChromaDB with metadata
        
        Args:
            chunks: List of chunk dictionaries (from TextChunker)
            policy_name: Optional name to label all chunks from this policy
        """
        # Prepare data for storage
        ids = []  # Unique IDs for each chunk
        documents = []  # Original text chunks
        metadatas = []  # Metadata (section, page, file name, etc.)
        
        # Extract texts for batch embedding generation
        texts = []
        for i, chunk in enumerate(chunks):
            # Generate unique ID (combination of policy name and chunk index)
            chunk_id = f"{policy_name or 'policy'}_{chunk.get('chunk_index', i)}"
            ids.append(chunk_id)
            
            # Store the original text
            texts.append(chunk['text'])
            documents.append(chunk['text'])
            
            # Store metadata (everything except the text itself)
            metadata = {k: str(v) for k, v in chunk.items() if k != 'text'}
            if policy_name:
                metadata['policy_name'] = policy_name
            metadatas.append(metadata)
        
        # Generate embeddings in batch (much faster than one-by-one)
        print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.generate_embeddings_batch(texts)
        
        # Add to ChromaDB collection
        # ChromaDB automatically handles indexing for fast search
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✓ Stored {len(chunks)} chunks in vector database")
    
    def search(self, query: str, top_k: int = 5, policy_filter: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Search for relevant chunks using semantic similarity.
        
        How semantic search works:
        1. Convert query to embedding
        2. Find chunks with most similar embeddings
        3. Return top K results with metadata
        
        Args:
            query: User's question or search term
            top_k: Number of results to return
            policy_filter: Optional filter to search only in specific policy
            
        Returns:
            List of relevant chunks with similarity scores
        """
        # Generate embedding for the query
        query_embedding = self.generate_embedding(query)
        
        # Prepare filter if policy name specified
        where_filter = None
        if policy_filter:
            where_filter = {"policy_name": policy_filter}
        
        # Search in ChromaDB
        # ChromaDB uses cosine similarity to find closest embeddings
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )
        
        # Format results for easy use
        formatted_results = []
        
        # results['documents'] is a list of lists (one list per query)
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]  # Lower distance = more similar
        
        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
            # Calculate similarity score (1 - distance, converted to percentage)
            similarity = (1 - distance) * 100
            
            formatted_results.append({
                'text': doc,
                'metadata': metadata,
                'similarity_score': similarity,
                'rank': i + 1
            })
        
        return formatted_results
    
    def delete_policy(self, policy_name: str) -> None:
        """
        Delete all chunks belonging to a specific policy.
        Useful when updating or replacing a policy document.
        
        Args:
            policy_name: Name of policy to delete
        """
        # Delete all chunks where policy_name matches
        self.collection.delete(
            where={"policy_name": policy_name}
        )
        print(f"Deleted all chunks for policy: {policy_name}")
    
    def list_policies(self) -> List[str]:
        """
        Get list of all unique policy names in the database.
        
        Returns:
            List of policy names
        """
        # Get all items from collection
        all_items = self.collection.get()
        
        # Extract unique policy names from metadata
        policy_names = set()
        for metadata in all_items.get('metadatas', []):
            if 'policy_name' in metadata:
                policy_names.add(metadata['policy_name'])
        
        return list(policy_names)
    
    def get_collection_info(self) -> Dict:
        """
        Get statistics about the vector database collection.
        
        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()
        policies = self.list_policies()
        
        return {
            'total_chunks': count,
            'policies': policies,
            'policy_count': len(policies)
        }


# Example usage (for testing)
if __name__ == "__main__":
    # Initialize vector store
    # store = VectorStore(db_path="./chroma_db")
    # 
    # # Example: Store chunks
    # chunks = [...]  # From TextChunker
    # store.store_chunks(chunks, policy_name="Travel Insurance Gold")
    # 
    # # Example: Search
    # results = store.search("Does this cover food poisoning?", top_k=5)
    # print(f"Found {len(results)} relevant chunks")
    pass
