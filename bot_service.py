import os
import time
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase Admin with service account
cred = credentials.Certificate('credentials/firebase-credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Constants
HELP_CHANNEL_ID = 'help'
BOT_USER_ID = os.getenv('BOT_USER_ID')

def is_help_channel(channel_id):
    """Check if the given channel is the help channel."""
    return channel_id == HELP_CHANNEL_ID

def send_bot_message(content, channel_id=HELP_CHANNEL_ID):
    """Send a message as the bot."""
    try:
        # Only allow messages in help channel
        if not is_help_channel(channel_id):
            print(f"Ignoring message for non-help channel: {channel_id}")
            return False
            
        print(f"Sending bot message: {content}")
        messages_ref = db.collection('messages').document(channel_id).collection('messages')
        messages_ref.add({
            'content': content,
            'userId': BOT_USER_ID,
            'userName': 'RAG Assistant',
            'createdAt': firestore.SERVER_TIMESTAMP,
            'isBot': True
        })
        print("Successfully sent bot message")
        return True
    except Exception as e:
        print(f"Error sending bot message: {e}")
        raise e

def handle_query_response(query, response, channel_id=HELP_CHANNEL_ID):
    """Handle a query response by sending messages."""
    try:
        # Only process messages in help channel
        if not is_help_channel(channel_id):
            print(f"Ignoring query response for non-help channel: {channel_id}")
            return
            
        print(f"Handling query response for: {query}")
        
        # Send typing indicator
        send_bot_message("_Thinking..._", channel_id)
        time.sleep(1)  # Brief pause to show typing indicator
        
        # Send the actual response
        send_bot_message(response, channel_id)
        print("Response sent successfully")
                
    except Exception as e:
        print(f"Error handling query response: {e}")
        if is_help_channel(channel_id):
            send_bot_message("Sorry, I encountered an error processing your request. Please try again later.", channel_id)

def main():
    """Main bot service function."""
    print("Starting bot service...")
    
    # Create a reference to the help channel messages
    help_messages_ref = db.collection('messages').document(HELP_CHANNEL_ID).collection('messages')
    
    # Create query for new messages
    query = help_messages_ref.where('createdAt', '>=', datetime.now())
    
    # Watch the query
    watch = query.on_snapshot(on_snapshot)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down bot service...")
        watch.unsubscribe()

if __name__ == "__main__":
    main() 