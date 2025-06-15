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
        # Attempt to load Firebase Admin SDK credentials from a mounted file
        firebase_admin_key_path = "/app/firebase_admin_sdk_key.json"
        if os.path.exists(firebase_admin_key_path):
            logger.info(f"Attempting to initialize Firebase Admin SDK from file: {firebase_admin_key_path}")
            with open(firebase_admin_key_path, 'r') as f:
                credentials_info = json.load(f)
            cred = credentials.Certificate(credentials_info)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info(f"Firebase Admin SDK initialized successfully from file: {firebase_admin_key_path}")
            return

        # Fallback: Attempt to load from FIREBASE_ADMIN_SDK_JSON environment variable
        credentials_json_str = os.getenv('FIREBASE_ADMIN_SDK_JSON')
        if credentials_json_str:
            logger.info("Found FIREBASE_ADMIN_SDK_JSON environment variable. Attempting to initialize from string.")
            credentials_info = json.loads(credentials_json_str)
            cred = credentials.Certificate(credentials_info)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully from environment variable.")
            return

        logger.warning("No Firebase Admin SDK credentials found (neither file nor environment variable). Firebase Admin SDK will not be initialized.")
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
        # This part of the authentication is still conceptual for client-side login
        # Firebase Admin SDK is for server-side operations.
        # For a full client-side login, you'd typically use Firebase JS SDK in a web frontend
        # and verify the token on the backend if needed.
        # Here, we're just checking if a user exists with that email for demonstration purposes.
        user = auth.get_user_by_email(email)
        logger.info(f"User {email} found with UID: {user.uid}")
        
        # For simplicity in this Streamlit example, if user is found, consider it authenticated.
        # In a real app, you'd need client-side JS for password auth or to verify ID tokens.
        return user, "Authentication successful."

    except firebase_admin.auth.UserNotFoundError:
        logger.warning(f"Authentication failed: User with email {email} not found.")
        return None, "Authentication failed. User not found. Please check your email or password, or sign up."
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
        # Improve error messages for common errors
        if e.code == 'auth/email-already-exists':
            return None, "User creation failed: This email is already in use. Please log in or use a different email."
        elif e.code == 'auth/invalid-password':
            return None, "User creation failed: Password must be at least 6 characters long."
        elif e.code == 'auth/invalid-email':
            return None, "User creation failed: Invalid email format."
        return None, f"User creation failed: {e.code}"
    except Exception as e:
        logger.error(f"Unexpected error during user creation: {e}")
        return None, f"User creation failed. An unexpected error occurred: {e}"

# Streamlit-specific functions for UI
def login_page():
    # Use a container to center the content and apply custom styling
    with st.container():
        st.markdown(
            """
            <div class="login-container">
                <h1 class="login-title">MultiAgentAI21</h1>
                
                <div class="login-mode-toggle-container">
                    <span class="login-mode-label">Login Mode</span>
                    <label class="switch">
                        <input type="checkbox" id="loginModeToggle" class="st-d3" checked>
                        <span class="slider round"></span>
                    </label>
                </div>

                <div id="loginForm" class="auth-form-card">
                    <h2 class="form-card-title">Welcome Back</h2>
                    <p class="form-card-subtitle">Sign in to your account</p>

                    <div class="input-group">
                        <label for="email_address">Email Address</label>
                        <input type="email" id="email_address" placeholder="you@example.com" class="st-d3" key="login_email_input">
                    </div>

                    <div class="input-group password-input-group">
                        <label for="password_input">Password</label>
                        <input type="password" id="password_input" placeholder="••••••••" class="st-d3" key="login_password_input">
                        <span class="password-toggle-icon" onclick="togglePasswordVisibility('password_input', this)">👁️</span>
                    </div>

                    <div class="forgot-password">
                        <a href="#" class="forgot-password-link">Forgot password?</a>
                    </div>
                    
                    <button class="st-d3 custom-button primary-button" key="signin_button_ui">Sign In</button>

                    <div class="social-login-separator">OR</div>

                    <button class="st-d3 custom-button github-button" key="github_button_ui">
                        <img src="https://img.icons8.com/ios-filled/24/ffffff/github.png" class="button-icon" alt="GitHub icon"/>
                        Sign in with GitHub
                    </button>
                    <button class="st-d3 custom-button google-button" key="google_button_ui">
                        <img src="https://img.icons8.com/color/24/000000/google-logo.png" class="button-icon" alt="Google icon"/>
                        Sign in with Google
                    </button>
                </div>

                <p class="signup-link-text">
                    Don't have an account? <a href="#" class="form-card-subtitle" onclick="toggleAuthMode()">Sign up</a>
                </p>
            </div>

            <script>
                function togglePasswordVisibility(inputId, iconElement) {
                    var input = document.getElementById(inputId);
                    if (input.type === "password") {
                        input.type = "text";
                        iconElement.textContent = "🔒"; // Change icon to locked
                    } else {
                        input.type = "password";
                        iconElement.textContent = "👁️"; // Change icon back to eye
                    }
                }

                function toggleAuthMode() {
                    // This function would typically communicate back to Streamlit
                    // or toggle visibility of login/signup forms.
                    // For now, it's a placeholder.
                    // A real implementation would involve setting a session_state variable
                    // and rerunning Streamlit.
                    console.log("Toggle Auth Mode clicked!");
                }
            </script>
            """,
            unsafe_allow_html=True
        )

    # --- Streamlit's internal handling for login/signup (hidden/moved to the side for UI) ---
    # We will use hidden Streamlit components to capture input and trigger actions
    # This ensures the Python backend logic still works with the custom HTML/CSS frontend
    st.session_state.login_mode_active = True # Default to login mode as per image

    # These are hidden/off-screen elements to capture the actual Streamlit input values
    email_address_val = st.text_input("Email Address Hidden", label_visibility="collapsed", key="hidden_login_email_address_val")
    password_val = st.text_input("Password Hidden", type="password", label_visibility="collapsed", key="hidden_login_password_val")
    
    # We will use custom Javascript to push values from custom HTML inputs to these hidden Streamlit inputs
    # and trigger clicks on the hidden Streamlit buttons.
    # This requires a bit more advanced JS interaction, but for now, the UI is visual.
    
    # Placeholder for Streamlit buttons that *actually* trigger the Python logic
    # These will not be displayed, but their existence allows Streamlit to handle the callback
    if st.button("Actual Sign In", key="actual_signin_button", help="This button is hidden and triggered by custom JS"):
        if email_address_val and password_val:
            user, message = authenticate_user(email_address_val, password_val)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email_address_val
                st.session_state["user_uid"] = user.uid
                st.session_state["auth_message"] = "Login successful!"
                st.rerun()
            else:
                st.error(message)
        else:
            st.error("Please enter both email and password.")

    # Signup functionality (kept as simple Streamlit components for now)
    if st.session_state.get("show_signup_form", False):
        st.subheader("Create a New Account")
        new_email = st.text_input("New Email Address", key="signup_email")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_password")

        if st.button("Sign Up Now", key="signup_button_actual"):
            if new_email and new_password and confirm_password:
                if new_password == confirm_password:
                    user, message = create_user(new_email, new_password)
                    if user:
                        st.success(message)
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

    # This is a hacky way to toggle for now. A more robust solution involves
    # JavaScript sending events back to Streamlit or using st.experimental_set_query_params
    # or a dedicated Streamlit component.
    if st.button("Toggle Signup/Login View (Dev Only)", key="toggle_view"):
        st.session_state.show_signup_form = not st.session_state.get("show_signup_form", False)
        st.rerun()

    # The actual user input values and actions would need to be captured via custom HTML's
    # JS and sent back to Streamlit, e.g., using st.experimental_set_query_params
    # or custom components. For this direct modification, the focus is on the visual
    # replication using provided static elements and the basic Streamlit integration.


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
            # It's important to return None or st.stop() to prevent the main app from running
            # when the user is not authenticated.
            st.stop() # Use st.stop() to halt execution of the decorated function entirely
        return func(*args, **kwargs)
    return wrapper

def get_current_user():
    return {
        "email": st.session_state.get("user_email"),
        "uid": st.session_state.get("user_uid"),
        "display_name": st.session_state.get("user_email"), # Using email as display name for simplicity
        "provider": "Email/Password" # Placeholder
    }


# --- Handle Google Application Credentials for other Google Cloud services ---
# This function aims to set GOOGLE_APPLICATION_CREDENTIALS to a temporary file
# if GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is provided,
# or to look for a mounted file.
def setup_google_application_credentials():
    # Prefer loading from a mounted file for GOOGLE_APPLICATION_CREDENTIALS
    google_creds_file_path = "/app/google_application_credentials_key.json"
    if os.path.exists(google_creds_file_path):
        logger.info(f"Found Google Application Credentials file at: {google_creds_file_path}. Setting GOOGLE_APPLICATION_CREDENTIALS.")
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_creds_file_path
        return

    # Fallback: Attempt to use GOOGLE_APPLICATION_CREDENTIALS_JSON env var and write to temp file
    google_creds_json_str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if google_creds_json_str:
        logger.info("Found GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable. Attempting to write to temporary file.")
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                temp_file.write(google_creds_json_str)
                temp_file_path = temp_file.name
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file_path
            logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set to temporary file: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error setting GOOGLE_APPLICATION_CREDENTIALS from JSON string: {e}")
    elif not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS_JSON and GOOGLE_APPLICATION_CREDENTIALS are not set. Some Google Cloud services might not authenticate.")

# Initialize Firebase Admin SDK first
initialize_firebase()

# Set up Google Application Credentials (for other Google Cloud APIs)
setup_google_application_credentials()

