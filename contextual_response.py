import os
from typing import List, Dict, Any, Tuple
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

from query import VectorDBQuery, QueryError
from response_cache import ResponseCache

class ContextualResponseGenerator:
    def __init__(self, cache_dir: str = ".cache", cache_ttl: int = 24):
        """
        Initialize the contextual response generator.
        
        Args:
            cache_dir (str): Directory to store response cache
            cache_ttl (int): Cache time-to-live in hours
        """
        self._initialize_llm()
        self.query_system = VectorDBQuery()
        self.cache = ResponseCache(cache_dir=cache_dir, ttl_hours=cache_ttl)

    def _initialize_llm(self) -> None:
        """Initialize the LLM with appropriate settings."""
        try:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.7,
            )
        except Exception as e:
            raise QueryError(f"Failed to initialize LLM: {str(e)}")

    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """Format search results into context string for the LLM."""
        context_parts = []
        
        for i, result in enumerate(results, 1):
            message = result['message']
            context_parts.append(
                f"{i}. {message['user_name']} in #{message['channel_id']} "
                f"({message['timestamp']}): {message['content']}"
            )
        
        return "\n".join(context_parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """Create the prompt template for the LLM."""
        template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful chat assistant that provides responses based on previous chat messages.
            Use the provided message history as context to answer the user's question.
            Keep your responses concise and focused on the relevant information from the context.
            If the context doesn't contain relevant information, say so and provide a general response."""),
            ("user", """Context from previous messages:
            {context}
            
            User Question: {query}
            
            Please provide a helpful response based on this context.""")
        ])
        
        return template

    def generate_response(self, query: str, max_context: int = 5, use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate a contextual response using vector search and LLM.
        
        Args:
            query (str): The user's question
            max_context (int): Maximum number of context messages to include
            use_cache (bool): Whether to use response caching
            
        Returns:
            Dict[str, Any]: Response object containing the answer and context
        """
        try:
            # Get relevant messages from vector store
            search_results = self.query_system.query_messages(query, top_k=max_context)
            
            # Check cache first if enabled
            if use_cache:
                cached_response, cache_stats = self.cache.get(query, search_results)
                if cached_response:
                    return cached_response
            
            # Format context for LLM
            context = self._format_context(search_results)
            
            # Create and format prompt
            prompt = self._create_prompt(query, context)
            
            # Generate response using LLM
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "context": context,
                "query": query
            })
            
            # Create response object
            response_obj = {
                "answer": response,
                "context": search_results,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "cached": False
            }
            
            # Cache the response if enabled
            if use_cache:
                self.cache.set(query, search_results, response_obj)
            
            return response_obj
            
        except QueryError:
            raise
        except Exception as e:
            raise QueryError(f"Error generating response: {str(e)}")

    def clear_cache(self) -> Tuple[int, Dict[str, Any]]:
        """
        Clear expired cache entries.
        
        Returns:
            Tuple[int, Dict[str, Any]]:
                - Number of cache entries cleared
                - Current cache statistics
        """
        return self.cache.clear_expired()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get current cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        return self.cache.get_stats()

# Example usage
if __name__ == "__main__":
    try:
        # Initialize response generator
        response_gen = ContextualResponseGenerator()
        
        # Test queries
        test_queries = [
            "What are some recommended VS Code extensions?",
            "How do people handle state management in frontend apps?",
            "What's the consensus on microservices?",
            "Any tips for Python async/await?"
        ]
        
        print("Testing Contextual Response System")
        print("=" * 50)
        
        # Run each query twice to test caching
        for query in test_queries:
            for i in range(2):
                print(f"\nQuestion: {query} (Run {i+1})")
                print("-" * 50)
                
                response = response_gen.generate_response(query)
                
                # Get cache statistics
                stats = response_gen.get_cache_stats()
                print(f"Cache Stats - Hits: {stats['hits']}, Misses: {stats['misses']}, "
                      f"Expired: {stats['expired']}, Errors: {stats['errors']}")

                print("Answer:")
                print(response["answer"])
                print(f"(Cached: {response.get('cached', False)})")
                print("\nBased on these messages:")
                print("-" * 30)
                
                for result in response["context"]:
                    message = result["message"]
                    print(f"- {message['user_name']} in #{message['channel_id']}: {message['content']}")
                
                print("=" * 50)
                
    except QueryError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}") 