import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, MessagingApi, ApiClient
from grammar_checker import EnglishGrammarChecker

def load_env_file(filepath):
    """Simple .env loader"""
    if not os.path.exists(filepath):
        # Try parent directory if not found in current (or passed as relative)
        parent_path = os.path.join(os.path.dirname(__file__), '..', filepath)
        if os.path.exists(parent_path):
           filepath = parent_path
        else:
           print(f"Warning: {filepath} not found.")
           return

    print(f"Loading environment from {filepath}...")
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('\'"')
                if not os.getenv(key):
                    os.environ[key] = value

def verify_integration():
    # Load .env variables
    load_env_file('.env')

    # 1. Verify Environment Variables
    print("\n--- 1. Checking Environment Variables ---")
    required_vars = ["GEMINI_API_KEY", "LINE_CHANNEL_ACCESS_TOKEN", "LINE_CHANNEL_SECRET"]
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing:
        print(f"❌ Missing variables: {', '.join(missing)}")
        print("Please ensure .env file exists and contains these variables.")
        return

    # 2. Verify Gemini API
    print("\n--- 2. Verifying Gemini API Connection ---")
    api_key = os.getenv("GEMINI_API_KEY")
    
    checker = EnglishGrammarChecker(api_key)
    
    try:
        print("Sending test request to Gemini (generating text for 'Hello')...")
        # We'll use the check_and_correct_grammar method which makes a real call
        # Mocking the prompt slightly isn't possible directly on the object without changing checking logic, 
        # so we'll just ask it to check "Hello".
        result = checker.check_and_correct_grammar("Hello")
        
        if "grammar correction service is temporarily unavailable" in result:
             print(f"❌ Gemini API Call Failed. Result: {result}")
        else:
             print("✅ Gemini API Call Successful!")
             print(f"   Response Preview: {result[:50]}...")

    except Exception as e:
        print(f"❌ Gemini API Error: {e}")

    # 3. Verify LINE SDK Configuration
    print("\n--- 3. Verifying LINE Bot Configuration ---")
    try:
        channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        channel_secret = os.getenv("LINE_CHANNEL_SECRET")
        
        # Initialize objects to check for format errors
        configuration = Configuration(access_token=channel_access_token)
        handler = WebhookHandler(channel_secret)
        
        # Try to initialize API Client (lazy connection usually, but valid config check)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            print("✅ LINE Messaging API initialized successfully (Configuration format is valid).")
            # Note: We cannot easily validate the token without making a call, 
            # and most calls require a valid user ID or reply token.
            # But initialization success rules out basic missing/malformed config.
            
    except Exception as e:
        print(f"❌ LINE Bot Configuration Error: {e}")

if __name__ == "__main__":
    verify_integration()
