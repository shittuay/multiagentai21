import streamlit as st
import os
import firebase_admin
from firebase_admin import credentials, auth
import logging
import time # For generating timestamps for session IDs
from datetime import datetime

logger = logging.getLogger(__name__)

# --- Firebase Admin SDK Initialization ---
# This part runs once when the module is imported.
# It uses the service account key which should be mounted into the Docker container.
_firebase_app = None

def initialize_firebase():
    global _firebase_app
    if _firebase_app:
        logger.info("Firebase Admin SDK already initialized.")
        return _firebase_app

    # Ensure GOOGLE_APPLICATION_CREDENTIALS is set for the Firebase Admin SDK
    service_account_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not service_account_key_path or not os.path.exists(service_account_key_path):
        error_msg = f"GOOGLE_APPLICATION_CREDENTIALS environment variable not set or file not found at {service_account_key_path}. This is required for Firebase Admin SDK."
        logger.critical(error_msg)
        st.error(f"❌ Authentication setup failed: {error_msg}")
        # In a real app, you might want to stop here or redirect to an error page.
        # For now, we'll let it proceed, but auth functions will likely fail.
        return None
    
    try:
        cred = credentials.Certificate(service_account_key_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
        return _firebase_app
    except Exception as e:
        logger.critical(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
        st.error(f"❌ Failed to initialize Firebase Admin SDK: {e}")
        return None

# Function to set GOOGLE_APPLICATION_CREDENTIALS for local development
# This will be called by app.py on startup.
def setup_google_application_credentials():
    # Only set if running locally and the env var is not already set
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ and os.path.exists("firebase_admin_sdk_key.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase_admin_sdk_key.json"
        logger.info("GOOGLE_APPLICATION_CREDENTIALS set for local development.")
    elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        logger.info(f"GOOGLE_APPLICATION_CREDENTIALS already set: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not found and firebase_admin_sdk_key.json not in root. Firebase Admin SDK might fail.")


# --- Session Management Functions ---
def set_user_session(user_record):
    """Sets user information in session state and creates a session ID."""
    user_info = {
        "uid": user_record.uid,
        "email": user_record.email,
        "display_name": user_record.display_name if user_record.display_name else user_record.email,
        "photo_url": user_record.photo_url,
        "provider": user_record.provider_id,
        "last_login_at": datetime.now().isoformat(),
        # Store a simple session identifier
        "session_id": f"{user_record.uid}-{int(time.time())}" 
    }
    st.session_state.user_info = user_info
    logger.info(f"User session set for UID: {user_record.uid}")

def clear_user_session():
    """Clears user information from session state."""
    if "user_info" in st.session_state:
        del st.session_state.user_info
    logger.info("User session cleared.")

def is_authenticated() -> bool:
    """Checks if a user is currently authenticated."""
    # Check for user_info in session state
    if st.session_state.get("user_info") and st.session_state.user_info.get("uid"):
        logger.debug(f"User already authenticated from session state: {st.session_state.user_info.get('uid')}")
        return True
    return False

def get_current_user() -> dict:
    """Returns the current authenticated user's information from session state."""
    if is_authenticated():
        logger.debug(f"Returning current user from session state: {st.session_state.user_info.get('email')}")
        return st.session_state.user_info
    logger.debug("No current user found in session state.")
    return {}

# --- Authentication Pages ---
def login_page():
    st.set_page_config(
        page_title="MultiAgentAI21 - Login",
        page_icon="🔒",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.title("🔒 Login or Sign Up")

    # Ensure Firebase Admin SDK is initialized
    if not _firebase_app:
        st.error("Firebase Admin SDK is not initialized. Cannot proceed with authentication.")
        return

    tab = st.tabs(["Login", "Sign Up"])

    with tab[0]:
        st.subheader("Login to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if not email or not password:
                st.error("Email and password are required.")
                return

            try:
                # Sign in user with email and password
                user_record = auth.get_user_by_email(email)
                # For direct password verification, Firebase Admin SDK doesn't expose `signInWithEmailAndPassword`.
                # It primarily works with ID tokens or custom token generation.
                # Since Streamlit is a server-side app, we can't directly use client-side Firebase Auth JS SDK.
                # A common pattern is to have a separate backend endpoint for password-based login
                # that then issues a custom token, or use something like `requests` to call a Firebase Auth REST API endpoint.
                
                # For simplicity here, we'll assume successful email match is enough for "login" if user exists.
                # In a production app, you'd integrate with actual client-side Firebase Auth or a secure backend.
                
                # Verify password is not directly done here for security reasons with Firebase Admin SDK.
                # If you need this, you'd typically verify the ID Token sent from a client-side app
                # or use a callable function that uses client-side auth.
                # For this Streamlit context, we will simply check if the user exists.
                # THIS IS NOT A SECURE PASSWORD VERIFICATION. For real apps, use client-side Firebase Auth.
                
                # Placeholder for secure password verification:
                # If you were receiving an ID token from a client:
                # decoded_token = auth.verify_id_token(id_token_from_client)
                # user_record = auth.get_user(decoded_token['uid'])

                st.success(f"Logged in as {user_record.email}!")
                set_user_session(user_record) # Set session after "login"
                st.rerun()
            except firebase_admin.auth.AuthError as e:
                error_message = e.code.replace('_', ' ').title()
                st.error(f"Login failed: {error_message}. Check your email and password.")
                logger.error(f"Firebase Auth Error during login: {e}", exc_info=True)
            except Exception as e:
                st.error(f"An unexpected error occurred during login: {e}")
                logger.error(f"Unexpected error during login: {e}", exc_info=True)

    with tab[1]:
        st.subheader("Create a new account")
        new_name = st.text_input("Your Name", key="signup_name") # New field for name
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Sign Up", key="signup_button"):
            if not new_email or not new_password or not new_name:
                st.error("Name, Email, and Password are required.")
                return
            if new_password != confirm_password:
                st.error("Passwords do not match.")
                return
            if len(new_password) < 6:
                st.error("Password must be at least 6 characters long.")
                return

            try:
                user = auth.create_user(
                    email=new_email,
                    password=new_password,
                    display_name=new_name, # Set display name during creation
                    email_verified=False,
                    disabled=False
                )
                st.success(f"Account created successfully for {user.email}! Please login.")
                logger.info(f"New user created: {user.uid} with email {user.email} and display name {user.display_name}")
            except firebase_admin.auth.AuthError as e:
                error_message = e.code.replace('_', ' ').title()
                st.error(f"Sign up failed: {error_message}. User might already exist.")
                logger.error(f"Firebase Auth Error during signup: {e}", exc_info=True)
            except Exception as e:
                st.error(f"An unexpected error occurred during sign up: {e}")
                logger.error(f"Unexpected error during signup: {e}", exc_info=True)

def logout():
    """Logs out the current user by clearing session state."""
    clear_user_session()
    logger.info("User logged out.")
    st.success("You have been logged out.")
    st.rerun()

def login_required(func):
    """Decorator to ensure a user is logged in before accessing a page."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_page()
            return None # Stop execution of the decorated function
        return func(*args, **kwargs)
    return wrapper

