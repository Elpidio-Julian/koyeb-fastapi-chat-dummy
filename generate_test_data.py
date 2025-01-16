import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import random
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Sample data for generating messages
USERS = [
    {"id": "user1", "name": "Alice Johnson"},
    {"id": "user2", "name": "Bob Smith"},
    {"id": "user3", "name": "Charlie Brown"},
    {"id": "user4", "name": "Diana Prince"}
]

CHANNELS = [
    {"id": "general", "name": "General Discussion"},
    {"id": "tech", "name": "Technology"},
    {"id": "random", "name": "Random"}
]

SAMPLE_MESSAGES = [
    "Has anyone worked with the new React 18 features?",
    "I'm having trouble with async/await in Python. Any tips?",
    "Just deployed my first ML model to production!",
    "What's everyone's favorite programming language?",
    "Docker containers are amazing for development.",
    "Anyone here use VS Code? What extensions do you recommend?",
    "GraphQL vs REST - thoughts?",
    "Best practices for securing a Node.js application?",
    "Kubernetes is both awesome and complicated.",
    "How do you handle state management in your frontend apps?",
    "TDD has really improved my code quality.",
    "What's your go-to CI/CD pipeline setup?",
    "Microservices: love them or hate them?",
    "Anyone tried the new GPT-4 API?",
    "Best resources for learning system design?"
]

def create_channels():
    """Create test channels in Firestore."""
    print("Creating channels...")
    for channel in CHANNELS:
        try:
            db.collection('channels').document(channel['id']).set({
                'name': channel['name'],
                'createdAt': datetime.now(),
                'isPublic': True
            })
            print(f"Created channel: {channel['name']}")
        except Exception as e:
            print(f"Error creating channel {channel['name']}: {str(e)}")

def generate_message():
    """Generate a random message with metadata."""
    user = random.choice(USERS)
    message = random.choice(SAMPLE_MESSAGES)
    return {
        'content': message,
        'userId': user['id'],
        'userName': user['name'],
        'createdAt': datetime.now() - timedelta(days=random.randint(0, 30))
    }

def create_messages(num_messages=50):
    """Create test messages across channels."""
    print(f"Generating {num_messages} test messages...")
    
    for _ in range(num_messages):
        channel = random.choice(CHANNELS)
        message = generate_message()
        
        try:
            # Add message to the channel's messages subcollection
            db.collection('messages').document(channel['id']).collection('messages').add(message)
            print(f"Added message to {channel['name']}: {message['content'][:30]}...")
            time.sleep(0.1)  # Small delay to avoid overwhelming Firestore
        except Exception as e:
            print(f"Error adding message: {str(e)}")

def main():
    """Main function to generate test data."""
    try:
        # Create channels first
        create_channels()
        
        # Generate messages
        create_messages(50)  # Generate 50 test messages
        
        print("Test data generation completed successfully!")
        
    except Exception as e:
        print(f"Error generating test data: {str(e)}")

if __name__ == "__main__":
    main() 