#!/usr/bin/env python3
"""
Firebase Configuration Example for Email Verification
Copy this file to firebase_config.py and fill in your Firebase project details
"""

# Firebase Configuration for Email Verification
FIREBASE_CONFIG = {
    # Get these values from your Firebase Console > Project Settings > General > Your Apps
    "apiKey": "your_firebase_api_key_here",
    "authDomain": "your-project.firebaseapp.com",
    "projectId": "your-project-id",
    "storageBucket": "your-project.appspot.com",
    "messagingSenderId": "123456789",
    "appId": "1:123456789:web:abcdef123456"
}

# Environment Variables to set in your .env file:
ENV_VARS = """
# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key_here
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abcdef123456

# Google Application Credentials (for Firebase Admin SDK)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/firebase-admin-sdk-key.json

# Google Gemini API (for AI agents)
GOOGLE_API_KEY=your_gemini_api_key_here
"""

# Setup Instructions:
SETUP_INSTRUCTIONS = """
## 🔥 Firebase Setup for Email Verification

### 1. Create Firebase Project
- Go to https://console.firebase.google.com/
- Create a new project or select existing one
- Enable Authentication in the left sidebar

### 2. Enable Email/Password Authentication
- In Authentication > Sign-in method
- Enable Email/Password provider
- Enable Email link (passwordless sign-in) if desired

### 3. Get Web App Configuration
- In Project Settings > General
- Scroll down to "Your apps" section
- Click the web app icon (</>) to add a web app
- Copy the config values to your .env file

### 4. Download Admin SDK Key
- In Project Settings > Service accounts
- Click "Generate new private key"
- Download the JSON file
- Set GOOGLE_APPLICATION_CREDENTIALS to this file path

### 5. Configure Email Templates (Optional)
- In Authentication > Templates
- Customize email verification template
- Set your app name and branding

### 6. Test the Setup
- Run the app and try to sign up
- Check that verification emails are sent
- Verify the email verification process works
"""

if __name__ == "__main__":
    print("Firebase Configuration Example")
    print("=" * 50)
    print(ENV_VARS)
    print("\n" + "=" * 50)
    print(SETUP_INSTRUCTIONS)
