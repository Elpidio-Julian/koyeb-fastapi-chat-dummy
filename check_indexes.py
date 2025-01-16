import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    print("Error: PINECONE_API_KEY not found in environment variables")
    exit(1)

try:
    # Initialize Pinecone with new syntax
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # List all indexes
    indexes = pc.list_indexes()
    print("\nAvailable Indexes:")
    print("=" * 50)
    
    if not indexes:
        print("No indexes found in your Pinecone account")
    else:
        for index in indexes:
            # Get details for each index
            print(f"\nIndex Name: {index.name}")
            print(f"Host: {index.host}")
            print(f"Status: {index.status}")
            print(f"Dimension: {index.dimension}")
            print(f"Metric: {index.metric}")
            print("-" * 50)

except Exception as e:
    print(f"Error checking Pinecone indexes: {str(e)}")
    exit(1) 