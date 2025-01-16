import os
import json
from pathlib import Path
from datetime import datetime
from firebase_admin import credentials, auth, firestore, initialize_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_bot_account():
    """Create a bot account in Firebase Authentication and Firestore."""
    try:
        # Initialize Firebase Admin
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', '../credentials/firebase-credentials.json')
        cred = credentials.Certificate(cred_path)
        initialize_app(cred)
        
        # Create bot user in Authentication
        bot_email = "rag-assistant@bot.local"
        bot_password = os.urandom(24).hex()  # Generate secure random password
        
        try:
            # Try to create new user
            user = auth.create_user(
                email=bot_email,
                password=bot_password,
                display_name="RAG Assistant",
                photo_url="https://api.dicebear.com/7.x/bottts/svg?seed=rag-assistant",  # Bot avatar
                disabled=False
            )
            print(f"Created bot user with ID: {user.uid}")
        except auth.EmailAlreadyExistsError:
            # If bot user exists, get its details
            user = auth.get_user_by_email(bot_email)
            print(f"Bot user already exists with ID: {user.uid}")
        
        # Initialize Firestore
        db = firestore.client()
        
        # Create/Update bot user document in users collection
        bot_doc = {
            'uid': user.uid,
            'email': bot_email,
            'displayName': 'RAG Assistant',
            'photoURL': "https://api.dicebear.com/7.x/bottts/svg?seed=rag-assistant",
            'isBot': True,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }
        
        db.collection('users').document(user.uid).set(bot_doc, merge=True)
        print("Updated bot user document in Firestore")
        
        # Create help channel if it doesn't exist
        help_channel_ref = db.collection('channels').document('help')
        help_channel = {
            'name': '🤖 Help & Support',
            'description': 'Get help from our AI assistant. Start your message with "Hey Chatbot" to ask questions.',
            'createdBy': user.uid,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
            'isPublic': True
        }
        
        help_channel_ref.set(help_channel, merge=True)
        print("Created/Updated help channel")
        
        # Add bot as member of help channel
        help_channel_members_ref = db.collection('channelMembers').document('help').collection('members').document(user.uid)
        member_doc = {
            'userId': user.uid,
            'role': 'bot',
            'joinedAt': firestore.SERVER_TIMESTAMP
        }
        help_channel_members_ref.set(member_doc)
        print("Added bot as help channel member")
        
        # Save bot credentials securely
        bot_config = {
            'uid': user.uid,
            'email': bot_email,
            'password': bot_password,  # Note: Store this securely in production
            'created_at': datetime.now().isoformat()
        }
        
        # Save to .env file
        env_path = Path('../.env')  # Updated path
        env_content = []
        
        # Read existing content
        if env_path.exists():
            with env_path.open('r') as f:
                env_content = f.readlines()
        
        # Update or add bot configuration
        bot_vars = {
            'BOT_USER_ID': user.uid,
            'BOT_EMAIL': bot_email,
            'BOT_PASSWORD': bot_password
        }
        
        # Remove existing bot variables
        env_content = [line for line in env_content 
                      if not any(line.startswith(key) for key in bot_vars.keys())]
        
        # Add new bot variables
        env_content.extend([f"{k}={v}\n" for k, v in bot_vars.items()])
        
        # Write back to .env
        with env_path.open('w') as f:
            f.writelines(env_content)
        
        print("\nBot configuration saved to .env")
        print(f"Bot User ID: {user.uid}")
        
        return user.uid
        
    except Exception as e:
        print(f"Error creating bot account: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        bot_uid = create_bot_account()
        print("\nBot account setup completed successfully!")
        print(f"Bot UID: {bot_uid}")
        print("\nNext steps:")
        print("1. Use the BOT_USER_ID from .env in your React application")
        print("2. Update your Firebase security rules to allow bot operations")
        print("3. Test the bot by sending a message starting with 'Hey Chatbot' in the help channel")
    except Exception as e:
        print(f"\nFailed to set up bot account: {str(e)}")
        print("Please ensure:")
        print("1. Firebase credentials are correctly set up")
        print("2. FIREBASE_CREDENTIALS_PATH is set in .env")
        print("3. You have necessary Firebase permissions") 