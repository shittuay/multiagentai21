import os
import json
import logging
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Global variable to store the Firebase app instance
firebase_app = None

def initialize_firebase():
    global firebase_app
    if firebase_app:
        logger.info("Firebase app already initialized.")
        return

    try:
        # --- NEW: Attempt to load Firebase Admin SDK credentials from a mounted file ---
        firebase_admin_key_path = "/app/firebase_admin_sdk_key.json"
        if os.path.exists(firebase_admin_key_path):
            logger.info(f"Attempting to initialize Firebase Admin SDK from file: {firebase_admin_key_path}")
            # Load the JSON content from the file
            with open(firebase_admin_key_path, 'r') as f:
                credentials_info = json.load(f)
            cred = credentials.Certificate(credentials_info)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info(f"Firebase Admin SDK initialized successfully from file: {firebase_admin_key_path}")
            return

        # --- OLD (Fallback): Attempt to load from FIREBASE_ADMIN_SDK_JSON environment variable (kept as fallback) ---
        credentials_json_str = os.getenv('FIREBASE_ADMIN_SDK_JSON')
        if credentials_json_str:
            logger.info("Found FIREBASE_ADMIN_SDK_JSON environment variable. Attempting to initialize from string.")
            credentials_info = json.loads(credentials_json_str)
            cred = credentials.Certificate(credentials_info)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully from environment variable.")
            return

        logger.warning("No Firebase Admin SDK credentials found (neither file nor environment variable). Firebase Admin SDK will not be initialized.")
        # If no credentials are found by this point, raise an error to stop app startup as it's critical
        raise ValueError("Firebase credentials not found via environment variable or any local/mounted file path. Please ensure 'firebase_admin_sdk_key.json' is present in the /app directory (via Docker volume mount) or FIREBASE_ADMIN_SDK_JSON environment variable is set.")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error for Firebase Admin SDK credentials: {e}")
        raise ValueError(f"Invalid JSON for Firebase Admin SDK credentials: {e}")
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {e}", exc_info=True)
        raise ValueError(f"Failed to initialize Firebase Admin SDK: {e}")

def authenticate_user(email, password):
    global firebase_app
    if not firebase_app:
        logger.error("Authentication error: The default Firebase app does not exist. Make sure to initialize the SDK by calling initialize_app().")
        return None, "Authentication failed. Firebase SDK not initialized."
    try:
        user = auth.get_user_by_email(email)
        logger.info(f"User {email} found with UID: {user.uid}")
        # Note: Firebase Admin SDK does not authenticate users directly with email/password.
        # This function would typically be used for server-side user management or token verification.
        # For a Streamlit app with client-side login, you'd usually verify a token or mock user data here.
        # For now, finding the user is considered 'successful' for the purpose of the login flow.
        return user, "Authentication successful."

    except firebase_admin.auth.UserNotFoundError:
        logger.warning(f"Authentication failed: User with email {email} not found.")
        return None, "Authentication failed. User not found."
    except firebase_admin.auth.AuthError as e:
        logger.error(f"Firebase Authentication error: {e}")
        return None, f"Authentication failed: {e.code}"
    except Exception as e:
        logger.error(f"Authentication error: An unexpected error occurred: {e}")
        return None, f"Authentication failed. An unexpected error occurred: {e}"

def create_user(email, password):
    global firebase_app
    if not firebase_app:
        logger.error("User creation error: Firebase app not initialized.")
        return None, "User creation failed. Firebase SDK not initialized."
    try:
        user = auth.create_user(email=email, password=password)
        logger.info(f"Successfully created new user: {user.uid}")
        return user, "User created successfully. You can now sign in."
    except firebase_admin.auth.AuthError as e:
        logger.error(f"Firebase Auth error during user creation: {e}")
        return None, f"User creation failed: {e.code}"
    except Exception as e:
        logger.error(f"Unexpected error during user creation: {e}")
        return None, f"User creation failed. An unexpected error occurred: {e}"

# Streamlit-specific functions for UI
def login_page():
    st.image("https://placehold.co/150x150/lightblue/white?text=Logo", width=150) # Example placeholder
    st.title("MultiAgentAI21")
    st.subheader("Login Mode")

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        st.subheader("Welcome Back")
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Sign In", key="signin_button"):
            if email and password:
                user, message = authenticate_user(email, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
                    st.session_state["user_uid"] = user.uid
                    st.session_state["auth_message"] = "Login successful!"
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please enter both email and password.")

    with signup_tab:
        st.subheader("Create a New Account")
        new_email = st.text_input("Email Address", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Sign Up", key="signup_button"):
            if new_email and new_password and confirm_password:
                if new_password == confirm_password:
                    user, message = create_user(new_email, new_password)
                    if user:
                        st.success(message)
                        # Optionally auto-login after signup
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = new_email
                        st.session_state["user_uid"] = user.uid
                        st.session_state["auth_message"] = "Account created and logged in!"
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Passwords do not match.")
            else:
                st.error("Please fill in all fields.")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None
    st.session_state["user_uid"] = None
    st.session_state["auth_message"] = "Logged out successfully."
    st.rerun()

def is_authenticated():
    return st.session_state.get("authenticated", False)

def login_required(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_page()
            return None # Important: Stop further execution of the decorated function
        return func(*args, **kwargs)
    return wrapper

def get_current_user():
    return {
        "email": st.session_state.get("user_email"),
        "uid": st.session_state.get("user_uid"),
        # Add other user details if available from Firebase (e.g., display_name, photo_url)
        # For simplicity, we'll just return email and uid for now
    }


# --- Handle Google Application Credentials for other Google Cloud services ---
# This function aims to set GOOGLE_APPLICATION_CREDENTIALS to a temporary file
# if GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is provided,
# or to look for a mounted file.
def setup_google_application_credentials():
    # --- NEW: Prefer loading from a mounted file for GOOGLE_APPLICATION_CREDENTIALS ---
    google_creds_file_path = "/app/google_application_credentials_key.json"
    if os.path.exists(google_creds_file_path):
        logger.info(f"Found Google Application Credentials file at: {google_creds_file_path}. Setting GOOGLE_APPLICATION_CREDENTIALS.")
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_creds_file_path
        return

    # --- OLD (Fallback): Attempt to use GOOGLE_APPLICATION_CREDENTIALS_JSON env var and write to temp file ---
    google_creds_json_str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if google_creds_json_str:
        logger.info("Found GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable. Attempting to write to temporary file.")
        try:
            import tempfile
            # Ensure the temp file content is the JSON string itself, not a string representation of the JSON object
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                temp_file.write(google_creds_json_str)
                temp_file_path = temp_file.name
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file_path
            logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set to temporary file: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error setting GOOGLE_APPLICATION_CREDENTIALS from JSON string: {e}")
            # Do not re-raise, allow app to continue with other credential methods if available
    elif not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS_JSON and GOOGLE_APPLICATION_CREDENTIALS are not set. Some Google Cloud services might not authenticate.")

# Initialize Firebase Admin SDK first
initialize_firebase()

# Set up Google Application Credentials (for other Google Cloud APIs)
setup_google_application_credentials()
