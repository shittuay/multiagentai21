import streamlit as st
import os
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin import exceptions # Import exceptions module to access AuthError
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
    if not service_account_key_path:
        error_msg = "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set."
        logger.critical(error_msg)
        # We allow the app to run without this, but auth functions will fail gracefully.
        return None
    
    if not os.path.exists(service_account_key_path):
        error_msg = f"Firebase Admin SDK service account key file not found at {service_account_key_path}. This is required for Firebase Admin SDK."
        logger.critical(error_msg)
        # We allow the app to run without this, but auth functions will fail gracefully.
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
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        local_key_path = "firebase_admin_sdk_key.json"
        if os.path.exists(local_key_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_key_path
            logger.info("GOOGLE_APPLICATION_CREDENTIALS set for local development from firebase_admin_sdk_key.json.")
        else:
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set and firebase_admin_sdk_key.json not found in root. Firebase Admin SDK might fail.")
    elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.info(f"GOOGLE_APPLICATION_CREDENTIALS already set: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable is set but empty or points to a non-existent file.")


# --- Session Management Functions ---
def set_user_session(user_record):
    """Sets user information in session state, including ID token, and creates a session ID."""
    try:
        # Generate custom token for the user, then get ID token from it
        # This is a common pattern for server-side auth to client-side auth continuity
        # However, for Streamlit, we just need to verify the user state.
        # Firebase Admin SDK's `AuthError` handling is key for session validity.
        
        # A lightweight "session" token for Streamlit's state
        st.session_state.user_info = {
            "uid": user_record.uid,
            "email": user_record.email,
            "display_name": user_record.display_name if user_record.display_name else user_record.email,
            "photo_url": user_record.photo_url,
            "provider": user_record.provider_id,
            "last_login_at": datetime.now().isoformat(),
            # A simple session identifier to help detect changes or expiration (not a security token)
            "session_id": f"{user_record.uid}-{int(time.time())}" 
        }
        logger.info(f"User session set for UID: {user_record.uid}")
    except Exception as e:
        logger.error(f"Error setting user session: {e}", exc_info=True)
        clear_user_session() # Clear session if there's an error setting it


def clear_user_session():
    """Clears user information from session state."""
    if "user_info" in st.session_state:
        del st.session_state.user_info
    logger.info("User session cleared.")

def is_authenticated() -> bool:
    """Checks if a user is currently authenticated and re-verifies session periodically."""
    # Ensure st.session_state.user_info exists and is not None before accessing its keys/methods
    if not st.session_state.get("user_info") or not st.session_state.user_info.get("uid"):
        logger.debug("No user info or UID in session state.")
        return False
    
    user_uid = st.session_state.user_info["uid"]
    
    # Re-verify user presence in Firebase periodically to ensure session is still valid
    # This acts as a lightweight session management
    if "last_auth_check" not in st.session_state or \
       (time.time() - st.session_state.last_auth_check) > 300: # Check every 5 minutes
        logger.info(f"Performing periodic authentication check for user: {user_uid}")
        try:
            # Attempt to get the user record from Firebase Auth Admin SDK
            auth.get_user(user_uid)
            st.session_state.last_auth_check = time.time()
            logger.debug(f"User {user_uid} still active.")
            return True
        except exceptions.AuthError as e: # Corrected: Use exceptions.AuthError
            logger.warning(f"Firebase Auth Error during periodic check for {user_uid}: {e}. Clearing session.", exc_info=True)
            clear_user_session()
            st.error("Your session has expired or is invalid. Please log in again.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during periodic auth check for {user_uid}: {e}", exc_info=True)
            # Don't clear session for unexpected errors, might be a temporary network issue.
            return True # Assume authenticated for now to avoid constant logout
    
    logger.debug(f"User {user_uid} authenticated from session state (recent check).")
    return True

def get_current_user() -> dict:
    """Returns the current authenticated user's information from session state."""
    if is_authenticated(): # Call is_authenticated to ensure check and potentially refresh
        logger.debug(f"Returning current user from session state: {st.session_state.user_info.get('email')}")
        return st.session_state.user_info
    logger.debug("No current user found in session state.")
    return {}

# --- Authentication Pages ---
def login_page():
    # Only set page config if not already set by main app
    # This flag prevents Streamlit from complaining about multiple st.set_page_config calls.
    # It assumes the main app.py will call it first.
    if not hasattr(st, '_page_config_set') or not st.session_state.get('page_config_set', False):
        st.set_page_config(
            page_title="MultiAgentAI21 - Login",
            page_icon="🔒",
            layout="centered",
            initial_sidebar_state="collapsed",
        )
        st.session_state._page_config_set = True # Set a flag to indicate it's been called

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
                # In a real app with Streamlit backend + Firebase Auth, you would typically:
                # 1. Use a client-side (e.g., JavaScript) Firebase SDK to sign in the user.
                # 2. Get the ID token from the client-side authentication.
                # 3. Send this ID token to your Streamlit backend.
                # 4. Verify the ID token using `auth.verify_id_token(id_token)` with Firebase Admin SDK.
                # This ensures secure password handling and session management.

                # For this demonstration, as a simplified example (NOT PRODUCTION-READY for password auth):
                # We assume a successful email match means a "login". This bypasses password verification on the backend.
                # This is OK for testing but highly INSECURE for production without a proper client-side auth flow.
                user_record = auth.get_user_by_email(email)
                st.success(f"Logged in as {user_record.email}!")
                set_user_session(user_record) # Set session after "login"
                st.rerun()
            except exceptions.AuthError as e: # Corrected: Use exceptions.AuthError
                error_message = e.code.replace('_', ' ', 1).title() if e.code else "Unknown Error"
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
            except exceptions.AuthError as e: # Corrected: Use exceptions.AuthError
                error_message = e.code.replace('_', ' ', 1).title() if e.code else "Unknown Error"
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
        # The Streamlit app reruns on every interaction.
        # is_authenticated() will check session state and re-verify periodically.
        if not is_authenticated():
            login_page()
            return None # Stop execution of the decorated function
        return func(*args, **kwargs)
    return wrapper
