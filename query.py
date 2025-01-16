import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QueryError(Exception):
    """Custom exception for query-related errors."""
    pass

class VectorDBQuery:
    def __init__(self):
        """Initialize the vector database query system."""
        self.index_name = "rag-chat-messages-1536"
        self._initialize_credentials()
        self._initialize_vector_store()

    def _initialize_credentials(self) -> None:
        """Initialize and validate required credentials."""
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not all([self.pinecone_api_key, self.openai_api_key]):
            raise QueryError("Missing required API keys. Please set PINECONE_API_KEY and OPENAI_API_KEY.")

    def _initialize_vector_store(self) -> None:
        """Initialize connection to Pinecone vector store."""
        try:
            embeddings = OpenAIEmbeddings()
            self.vectorstore = PineconeVectorStore.from_existing_index(
                index_name=self.index_name,
                embedding=embeddings,
                text_key="content"
            )
        except Exception as e:
            raise QueryError(f"Failed to initialize vector store: {str(e)}")

    def _validate_query(self, query: str) -> None:
        """Validate the query string."""
        if not query or not isinstance(query, str):
            raise QueryError("Query must be a non-empty string")
        if len(query.strip()) < 3:
            raise QueryError("Query must be at least 3 characters long")

    def _format_timestamp(self, timestamp: Optional[float]) -> str:
        """Format timestamp to human-readable string."""
        if not timestamp:
            return "Unknown Time"
        try:
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return str(timestamp)

    def _format_result(self, doc: Any, score: float) -> Dict[str, Any]:
        """Format a single search result."""
        metadata = doc.metadata
        return {
            "relevance_score": 1 - score,  # Convert distance to similarity score
            "message": {
                "content": doc.page_content,
                "channel_id": metadata.get('channel_id', 'Unknown Channel'),
                "user_name": metadata.get('user_name', 'Unknown User'),
                "timestamp": self._format_timestamp(metadata.get('timestamp')),
                "message_id": metadata.get('message_id', 'Unknown ID')
            }
        }

    def query_messages(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for messages similar to the query.
        
        Args:
            query (str): The search query
            top_k (int): Number of results to return (default: 5)
            
        Returns:
            List[Dict]: List of relevant messages with metadata and scores
        """
        try:
            self._validate_query(query)
            
            # Perform similarity search
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=top_k
            )
            
            # Format results
            formatted_results = [
                self._format_result(doc, score)
                for doc, score in results
            ]
            
            return formatted_results
            
        except QueryError:
            raise
        except Exception as e:
            raise QueryError(f"Error performing search: {str(e)}")

# Example usage
if __name__ == "__main__":
    try:
        # Initialize query system
        query_system = VectorDBQuery()
        
        # Test queries
        test_queries = [
            "Python programming help",
            "React features",
            "Docker containers",
            "API design",
            "Testing practices"
        ]
        
        print("Testing Query System")
        print("=" * 50)
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("-" * 50)
            
            results = query_system.query_messages(query)
            for result in results:
                print(f"\nRelevance Score: {result['relevance_score']:.2f}")
                message = result['message']
                print(f"Channel: {message['channel_id']}")
                print(f"User: {message['user_name']}")
                print(f"Time: {message['timestamp']}")
                print(f"Message: {message['content']}")
                print("-" * 50)
                
    except QueryError as e:
        print(f"Query Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}") 