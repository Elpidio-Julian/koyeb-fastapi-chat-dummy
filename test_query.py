import os
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI and Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
index_name = "rag-chat-messages-1536"

if not all([PINECONE_API_KEY, OPENAI_API_KEY]):
    print("Error: Missing required environment variables.")
    print("Please ensure you have set:")
    print("- PINECONE_API_KEY")
    print("- OPENAI_API_KEY")
    exit(1)

# Initialize embeddings and vector store
embeddings = OpenAIEmbeddings()
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
    text_key="content"
)

def search_messages(query, top_k=5):
    """Search for messages similar to the query."""
    print(f"\nSearching for: '{query}'")
    print("-" * 50)
    
    # Search using similarity search
    results = vectorstore.similarity_search_with_score(
        query=query,
        k=top_k
    )
    
    # Print results
    for doc, score in results:
        metadata = doc.metadata
        print(f"\nRelevance Score: {1 - score:.2f}")  # Convert distance to similarity score
        
        # Print all available metadata for debugging
        print("Available metadata fields:", metadata.keys())
        
        # Access metadata fields safely with get()
        channel_id = metadata.get('channel_id', 'Unknown Channel')
        user_name = metadata.get('user_name', 'Unknown User')
        timestamp = metadata.get('timestamp')
        message_content = doc.page_content  # The actual message content is in page_content
        
        # Convert timestamp if available
        time_str = "Unknown Time"
        if timestamp:
            try:
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = str(timestamp)
        
        print(f"Channel: {channel_id}")
        print(f"User: {user_name}")
        print(f"Time: {time_str}")
        print(f"Message: {message_content}")
        print("-" * 50)

def main():
    """Run some test queries."""
    # Test with different types of queries
    test_queries = [
        "Python programming help",
        "React features",
        "Docker and containers",
        "API design",
        "Testing practices"
    ]
    
    print("Testing RAG System")
    print("=" * 50)
    
    # Run test queries
    for query in test_queries:
        search_messages(query)
        print("\n")

if __name__ == "__main__":
    main() 