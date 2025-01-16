import os
import firebase_admin
from firebase_admin import credentials, firestore
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from datetime import datetime, timezone
import time
from pathlib import Path
from dotenv import load_dotenv
import gc
from time import time, sleep

# Initialize last_call_time for rate limiting
last_call_time = time()

# Load environment variables with explicit path
# base_path = Path(__file__).parent  # Gets the directory containing this script
env_path = '../.env'
print(f"Looking for .env at: {env_path}")
load_dotenv(dotenv_path=env_path)

# Get the credentials file path
CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'credentials/firebase-credentials.json')

# Initialize Firebase Admin
try:
    # Get absolute path to credentials file
    base_path = Path(__file__).parent
    cred_path = base_path / CREDENTIALS_PATH
    
    if not cred_path.exists():
        raise FileNotFoundError(f"Firebase credentials file not found at {cred_path}")
    
    cred = credentials.Certificate(str(cred_path))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully!")
except Exception as e:
    print(f"Error initializing Firebase: {str(e)}")
    print("Please ensure you have:")
    print("1. Downloaded your Firebase service account credentials")
    print("2. Placed them in the credentials directory as 'firebase-credentials.json'")
    print("3. Or set FIREBASE_CREDENTIALS_PATH in your .env file")
    exit(1)

# Initialize OpenAI and Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
index_name = "rag-chat-messages-1536"

print(f"Using Pinecone index: {index_name}")  # Debug print

if not all([PINECONE_API_KEY, OPENAI_API_KEY, index_name]):
    print("Error: Missing required environment variables.")
    print("Please ensure you have set:")
    print("- PINECONE_API_KEY")
    print("- OPENAI_API_KEY")
    print("- PINECONE_INDEX")
    exit(1)

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Initialize Pinecone vector store
try:
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings,
        text_key="content"
    )
    # Test connection with a simple operation
    vectorstore.similarity_search("test", k=1)
    print("Vector store connection verified")
except Exception as e:
    print(f"Error connecting to vector store: {str(e)}")
    exit(1)

def get_all_channels():
    """Fetch all channel IDs from Firestore."""
    channels = db.collection('channels').stream()
    return [channel.id for channel in channels]

def get_messages_for_channel(channel_id, last_indexed_time=None):
    """Fetch messages for a specific channel, optionally after a certain time."""
    messages_ref = db.collection('messages').document(channel_id).collection('messages')
    query = messages_ref
    
    if last_indexed_time:
        query = query.where('createdAt', '>', last_indexed_time)
    
    messages = query.stream()
    return messages

def create_message_vector(message_doc):
    """Create a vector from a message document."""
    message_data = message_doc.to_dict()
    
    # Create the text content to be embedded
    content = message_data.get('content', '').strip()
    if not content:
        print(f"Skipping empty message {message_doc.id}")
        return None
    user_name = message_data.get('userName', 'Unknown User')
    
    # Handle timestamp conversion
    created_at = message_data.get('createdAt')
    if created_at:
        if isinstance(created_at, datetime):
            timestamp = created_at.timestamp()
        else:
            # Handle Firestore timestamp
            timestamp = created_at.seconds + (created_at.nanos / 1e9)
    else:
        timestamp = datetime.now(timezone.utc).timestamp()
    
    # Combine message content with metadata for context
    text_to_embed = f"User {user_name} wrote: {content}"
    
    # Prepare metadata
    metadata = {
        'message_id': message_doc.id,
        'channel_id': message_doc.reference.parent.parent.id,
        'user_id': message_data.get('userId', ''),
        'user_name': user_name,
        'timestamp': timestamp,
        'content': content
    }
    
    return {
        'id': f"{message_doc.reference.parent.parent.id}_{message_doc.id}",
        'text': text_to_embed,
        'metadata': metadata
    }

def rate_limit(calls_per_second=10):
    """Implement adaptive rate limiting"""
    global last_call_time
    current_time = time()
    time_since_last_call = current_time - last_call_time
    time_per_call = 1.0 / calls_per_second
    
    if time_since_last_call < time_per_call:
        sleep_time = time_per_call - time_since_last_call
        sleep(sleep_time)
    
    last_call_time = time()

def index_messages():
    """Main function to index messages."""
    print("Starting message indexing...")
    messages_processed = 0
    try:
        # Get all channels
        channels = get_all_channels()
        print(f"Found {len(channels)} channels")
        
        for channel_id in channels:
            batch = []
            try:
                messages = get_messages_for_channel(channel_id)
                for message in messages:
                    try:
                        # Rate limit message processing
                        rate_limit(calls_per_second=10)
                        
                        vector_data = create_message_vector(message)
                        if vector_data:  # Only append if not None
                            batch.append(vector_data)
                        
                        if len(batch) >= 100:
                            # Rate limit vector store updates
                            rate_limit(calls_per_second=2)  # More conservative rate for Pinecone
                            
                            vectorstore.add_texts(
                                texts=[doc['text'] for doc in batch],
                                metadatas=[doc['metadata'] for doc in batch],
                                ids=[doc['id'] for doc in batch]
                            )
                            print(f"Indexed batch of {len(batch)} messages")
                            messages_processed += len(batch)
                            if messages_processed % 1000 == 0:
                                gc.collect()  # Force garbage collection periodically
                            batch = []
                    except Exception as e:
                        print(f"Error processing message {message.id}: {str(e)}")
                        continue
                
                # Process remaining batch
                if batch:
                    try:
                        # Rate limit final batch
                        rate_limit(calls_per_second=2)
                        
                        vectorstore.add_texts(
                            texts=[doc['text'] for doc in batch],
                            metadatas=[doc['metadata'] for doc in batch],
                            ids=[doc['id'] for doc in batch]
                        )
                        print(f"Indexed final batch of {len(batch)} messages")
                    except Exception as e:
                        print(f"Error processing final batch: {str(e)}")
                
            except Exception as e:
                print(f"Error processing channel {channel_id}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error during indexing: {str(e)}")

if __name__ == "__main__":
    index_messages() 