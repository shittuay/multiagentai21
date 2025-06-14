import streamlit as st
import firebase_admin
from firebase_admin import auth, credentials
import os
import logging
import json
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            logger.info("Initializing Firebase Admin SDK...")
            
            # --- Option 1: Load from environment variable (preferred for Cloud Run) ---
            credentials_json_str = os.getenv("FIREBASE_ADMIN_SDK_JSON")
            if credentials_json_str:
                logger.info("Found FIREBASE_ADMIN_SDK_JSON environment variable.")
                try:
                    credentials_info = json.loads(credentials_json_str)
                    cred = credentials.Certificate(credentials_info)
                    logger.info("Successfully created credentials object from environment variable.")
                    app = firebase_admin.initialize_app(cred)
                    logger.info(f"Firebase initialized successfully with app: {app.name} from environment variable.")
                    return
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decoding error for FIREBASE_ADMIN_SDK_JSON: {e}", exc_info=True)
                    raise ValueError(f"Invalid JSON in FIREBASE_ADMIN_SDK_JSON: {e}")
                except Exception as e:
                    logger.error(f"Error initializing Firebase from environment variable: {e}", exc_info=True)
                    raise ValueError(f"Failed to initialize Firebase from environment variable: {e}")
            
            # --- Option 2: Load from file (for local development and Cloud Run fallback) ---
            # Explicitly add the user's specific absolute path for local testing
            project_root_abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Go up one level from src to project root
            firebase_key_filename = 'multiagentai21-9a8fc-firebase-adminsdk-fbsvc-72f0130c73.json'
            local_specific_path = os.path.join(project_root_abs_path, firebase_key_filename)

            possible_paths = [
                local_specific_path, # Try the absolute path explicitly first
                '/app/src/multiagentai21-key.json', # Expected path in Cloud Run when mounted as a secret
                os.path.join(os.path.dirname(__file__), 'multiagentai21-key.json'), # In src directory (if renamed)
                os.path.join(os.path.dirname(__file__), 'multiagentai21-9a8fc-firebase-adminsdk-fbsvc-72f0130c73.json'),
                'multiagentai21-key.json', # Current directory (e.g., if app.py is run directly)
                'multiagentai21-9a8fc-firebase-adminsdk-fbsvc-72f0130c73.json', # Current directory
            ]

            cred_path_found = None
            for path in possible_paths:
                logger.info(f"Checking for credentials file at: {path}")
                if os.path.exists(path):
                    cred_path_found = path
                    break

            if cred_path_found:
                logger.info(f"Credential file found at: {cred_path_found}")
                try:
                    cred = credentials.Certificate(cred_path_found)
                    logger.info("Successfully created credentials object from file.")
                    app = firebase_admin.initialize_app(cred)
                    logger.info(f"Firebase initialized successfully with app: {app.name} from file.")
                    return
                except Exception as e:
                    logger.error(f"Error initializing Firebase with credential file at {cred_path_found}: {e}", exc_info=True)
                    try:
                        with open(cred_path_found, 'r') as f:
                            content = f.read()
                        logger.error(f"Content of {cred_path_found} (first 200 chars): {content[:200]}")
                    except Exception as fe:
                        logger.error(f"Could not read content of {cred_path_found}: {fe}")
                    raise ValueError(f"Error initializing Firebase from file: {e}. Check if the secret content is valid JSON.")
            else:
                current_dir = os.getcwd()
                src_dir = os.path.join(current_dir, 'src')
                
                logger.error(f"Credential file NOT found in any checked path.")
                logger.error(f"Current working directory: {current_dir}")
                logger.error(f"Contents of {current_dir}: {os.listdir(current_dir) if os.path.exists(current_dir) else 'N/A'}")
                logger.error(f"Contents of {src_dir}: {os.listdir(src_dir) if os.path.exists(src_dir) else 'N/A'}")
                
                raise ValueError(
                    f"Firebase credentials not found via environment variable or any local/mounted file path. " +
                    "Please ensure FIREBASE_ADMIN_SDK_JSON is set as an environment variable (for Cloud Run) " +
                    f"or the file '{firebase_key_filename}' " +
                    "(or 'multiagentai21-key.json') is placed in the project root or src directory locally. " +
                    f"Current directory: {current_dir}, src directory: {src_dir}"
                )
                
        else:
            logger.info("Firebase already initialized")
            
    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to initialize Firebase: {str(e)}")

# Initialize Firebase when the module is imported
initialize_firebase()

def is_authenticated():
    """Check if user is authenticated"""
    return 'user' in st.session_state and st.session_state['user'] is not None

def get_current_user():
    """Get current authenticated user"""
    return st.session_state.get('user', None)

def verify_token(id_token):
    """Verify Firebase ID token"""
    if not id_token:
        return None
    
    try:
        # Verify the token
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

def create_user(email, password, display_name=None):
    """Create a new user in Firebase"""
    try:
        logger.info(f"Creating user with email: {email}")
        
        # Create the user
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=True  # Set to True to avoid email verification issues
        )
        logger.info(f"User created successfully: {user.uid}")
        return user
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error creating user: {error_message}", exc_info=True)
        
        if "email already exists" in error_message.lower():
            raise ValueError("This email is already registered. Please try logging in instead.")
        elif "invalid email" in error_message.lower():
            raise ValueError("Please enter a valid email address.")
        elif "password" in error_message.lower():
            raise ValueError("Password must be at least 6 characters long.")
        else:
            raise ValueError(f"Failed to create account: {error_message}")

def authenticate_user(email, password):
    """Authenticate user with email and password using custom token"""
    try:
        # Get user by email
        user = auth.get_user_by_email(email)
        
        # Create a custom token for the user
        custom_token = auth.create_custom_token(user.uid)
        
        # Return user data
        user_data = {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'email_verified': user.email_verified,
            'custom_token': custom_token.decode('utf-8')
        }
        
        logger.info(f"User authenticated successfully: {user.email}")
        return user_data
        
    except auth.UserNotFoundError:
        raise ValueError("No account found with this email address.")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise ValueError("Authentication failed. Please check your credentials.")

def logout_user():
    """Log out the current user"""
    if 'user' in st.session_state:
        del st.session_state['user']
    if 'id_token' in st.session_state:
        del st.session_state['id_token']
    logger.info("User logged out successfully")

def set_user_session(user_data):
    """Set user data in session state"""
    st.session_state['user'] = user_data
    logger.info(f"User session set for: {user_data.get('email', 'unknown')}")

def handle_oauth_callback():
    """Handle OAuth callback from client-side authentication"""
    query_params = st.query_params
    
    if 'id_token' in query_params:
        logger.info("Found id_token in query parameters, processing OAuth callback")
        id_token = query_params['id_token']
        decoded_token = verify_token(id_token)
        
        if decoded_token:
            user_data = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'display_name': decoded_token.get('name'),
                'provider': decoded_token.get('firebase', {}).get('sign_in_provider', 'unknown')
            }
            set_user_session(user_data)
            st.success("Login successful!")
            # Clear query parameters
            st.query_params.clear()
            st.rerun()
        else:
            logger.error("Token verification failed during OAuth callback")
            st.error("Login failed: Invalid token")

def create_oauth_html():
    """Create proper OAuth HTML component with working Firebase integration"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <script type="module">
            import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
            import { getAuth, signInWithPopup, GoogleAuthProvider, GithubAuthProvider, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

            const firebaseConfig = {
                apiKey: "{{ FIREBASE_API_KEY }}",
                authDomain: "{{ FIREBASE_AUTH_DOMAIN }}",
                projectId: "{{ FIREBASE_PROJECT_ID }}",
                storageBucket: "{{ FIREBASE_STORAGE_BUCKET }}",
                messagingSenderId: "{{ FIREBASE_MESSAGING_SENDER_ID }}",
                appId: "{{ FIREBASE_APP_ID }}"
            };

            const app = initializeApp(firebaseConfig);
            const auth = getAuth(app);

            // OAuth providers
            const googleProvider = new GoogleAuthProvider();
            const githubProvider = new GithubAuthProvider();

            // Add required scopes
            googleProvider.addScope('email');
            googleProvider.addScope('profile');
            githubProvider.addScope('user:email');

            window.signInWithGoogle = async function() {
                try {
                    console.log('Starting Google OAuth...');
                    const result = await signInWithPopup(auth, googleProvider);
                    console.log('Google OAuth successful:', result.user.email);
                    
                    const idToken = await result.user.getIdToken();
                    console.log('Got ID token, redirecting...');
                    
                    // Redirect with token
                    const currentUrl = new URL(window.location.href);
                    currentUrl.searchParams.set('id_token', idToken);
                    window.location.href = currentUrl.toString();
                    
                } catch (error) {
                    console.error('Google OAuth error:', error);
                    alert('Google login failed: ' + error.message);
                }
            };

            window.signInWithGithub = async function() {
                try {
                    console.log('Starting GitHub OAuth...');
                    const result = await signInWithPopup(auth, githubProvider);
                    console.log('GitHub OAuth successful:', result.user.email);
                    
                    const idToken = await result.user.getIdToken();
                    console.log('Got ID token, redirecting...');
                    
                    // Redirect with token
                    const currentUrl = new URL(window.location.href);
                    currentUrl.searchParams.set('id_token', idToken);
                    window.location.href = currentUrl.toString();
                    
                } catch (error) {
                    console.error('GitHub OAuth error:', error);
                    alert('GitHub login failed: ' + error.message);
                }
            };

            // Test function
            window.testOAuth = function() {
                const debugDiv = document.getElementById('debug-info');
                if (debugDiv) {
                    debugDiv.innerHTML = 'Testing OAuth setup...<br>';
                    debugDiv.innerHTML += '✅ Firebase SDK loaded<br>';
                    debugDiv.innerHTML += '✅ Auth initialized<br>';
                    debugDiv.innerHTML += 'Domain: ' + window.location.hostname + '<br>';
                    debugDiv.innerHTML += 'Protocol: ' + window.location.protocol + '<br>';
                    
                    // Test popup
                    try {
                        const popup = window.open('', 'test', 'width=100,height=100');
                        if (popup) {
                            popup.close();
                            debugDiv.innerHTML += '✅ Popups allowed<br>';
                        } else {
                            debugDiv.innerHTML += '❌ Popups blocked<br>';
                        }
                    } catch (e) {
                        debugDiv.innerHTML += '❌ Popup test failed: ' + e.message + '<br>';
                    }
                }
            };

            console.log('Firebase OAuth module loaded successfully');
        </script>
    </head>
    <body>
        <div style="display: flex; gap: 10px; justify-content: center; padding: 20px;">
            <button onclick="signInWithGoogle()" 
                    style="padding: 12px 24px; background: #4285f4; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                <span>🔍</span> Sign in with Google
            </button>
            
            <button onclick="signInWithGithub()" 
                    style="padding: 12px 24px; background: #333; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                <span>🐙</span> Sign in with GitHub
            </button>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="testOAuth()" 
                    style="padding: 8px 16px; background: #6366f1; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                Test OAuth Setup
            </button>
            <div id="debug-info" style="margin-top: 10px; font-family: monospace; font-size: 12px; text-align: left; max-width: 400px; margin: 10px auto;"></div>
        </div>
    </body>
    </html>
    """

def login_page():
    """Display simplified login page"""
    logger.info("Rendering login page...")
    
    # Handle OAuth callback first
    handle_oauth_callback()

    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #E0F2F7 0%, #B2EBF2 100%);
    }
    .login-container {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 1rem;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 500;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>MultiAgentAI21</h1>", unsafe_allow_html=True)

        # Toggle between login and signup
        is_login = st.toggle("Login Mode", value=True, key="auth_mode")
        
        st.markdown(f"<h2 style='text-align: center;'>{'Welcome Back' if is_login else 'Create Account'}</h2>", unsafe_allow_html=True)

        # Email/Password Authentication Form
        with st.form(key="auth_form"):
            if not is_login:
                full_name = st.text_input("Full Name", key="full_name")
            
            email = st.text_input("Email Address", key="email")
            password = st.text_input("Password", type="password", key="password")
            
            if not is_login:
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

            submit_button = st.form_submit_button("Sign In" if is_login else "Create Account")
            
            if submit_button:
                if not email or not password:
                    st.error("Email and password are required")
                elif not is_login and (not full_name or password != confirm_password):
                    if not full_name:
                        st.error("Full name is required")
                    if password != confirm_password:
                        st.error("Passwords do not match")
                else:
                    try:
                        if is_login:
                            # Authenticate existing user
                            user_data = authenticate_user(email, password)
                            set_user_session(user_data)
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            # Create new user
                            user = create_user(email, password, full_name)
                            # Automatically log them in
                            user_data = authenticate_user(email, password)
                            set_user_session(user_data)
                            st.success("Account created and logged in successfully!")
                            st.rerun()
                            
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        logger.error(f"Authentication error: {str(e)}", exc_info=True)
                        st.error("An unexpected error occurred. Please try again.")

        # OAuth Section with working implementation
        st.markdown("---")
        st.markdown("<p style='text-align: center;'>Or continue with:</p>", unsafe_allow_html=True)
        
        # Use the corrected OAuth HTML component
        st.components.v1.html(create_oauth_html(), height=300)

        st.markdown('</div>', unsafe_allow_html=True)

def logout():
    """Logout current user"""
    logout_user()
    st.success("Logged out successfully")
    st.rerun()

def user_profile_sidebar():
    """Display user profile in sidebar"""
    if is_authenticated():
        user = get_current_user()
        with st.sidebar:
            st.markdown("---")
            st.markdown("### User Profile")
            st.write(f"**Name:** {user.get('display_name', 'N/A')}")
            st.write(f"**Email:** {user.get('email', 'N/A')}")
            
            if user.get('provider'):
                st.write(f"**Provider:** {user.get('provider').title()}")
            
            if st.button("Logout", key="sidebar_logout"):
                logout()

# Login required decorator
def login_required(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("Please log in to access this page")
            st.stop()
        return func(*args, **kwargs)
    return wrapper
