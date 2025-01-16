import os
import json
from pathlib import Path
from dotenv import load_dotenv

def setup_credentials():
    """Set up Firebase credentials from environment variables."""
    # Load environment variables
    load_dotenv()
    
    # Create credentials directory if it doesn't exist
    credentials_dir = Path("credentials")
    credentials_dir.mkdir(exist_ok=True)
    
    # Get credentials from environment variable
    credentials_json = os.getenv("FIREBASE_CREDENTIALS")
    if not credentials_json:
        raise ValueError("FIREBASE_CREDENTIALS environment variable not found")
    
    try:
        # Parse the JSON string to ensure it's valid
        credentials_data = json.loads(credentials_json)
        
        # Write credentials to file
        credentials_file = credentials_dir / "firebase-credentials.json"
        with open(credentials_file, "w") as f:
            json.dump(credentials_data, f, indent=2)
            
        print(f"✅ Credentials written to {credentials_file}")
        
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in FIREBASE_CREDENTIALS environment variable")
    except Exception as e:
        raise Exception(f"Error writing credentials: {str(e)}")

if __name__ == "__main__":
    try:
        setup_credentials()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1) 