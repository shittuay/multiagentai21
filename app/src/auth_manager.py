#!/usr/bin/env python3
"""
Enhanced Authentication Manager with Database Persistence
Uses Firestore for user data storage and session management
"""

import streamlit as st
import os
import logging
import hashlib
import uuid
import bcrypt
import re
import time
import json
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# Initialize Firestore client for user storage
def get_firestore_client():
    """Get Firestore client for user data storage"""
    try:
        from src.api.firestore import FirestoreClient
        return FirestoreClient()
    except Exception as e:
        logger.error(f"Failed to initialize Firestore client: {e}")
        return None

# Simple user storage (fallback when database is not available)
USERS = {}
USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')

def load_users_from_file():
    """Load users from JSON file"""
    global USERS
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                USERS = json.load(f)
                logger.info(f"Loaded {len(USERS)} users from file")
        else:
            logger.info("No users file found, starting with empty user database")
            USERS = {}
    except Exception as e:
        logger.error(f"Error loading users from file: {e}")
        USERS = {}

def save_users_to_file():
    """Save users to JSON file"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

        with open(USERS_FILE, 'w') as f:
            json.dump(USERS, f, indent=2)
            logger.info(f"Saved {len(USERS)} users to file")
        return True
    except Exception as e:
        logger.error(f"Error saving users to file: {e}")
        return False

# Load users on module import
load_users_from_file()

def hash_password(password):
    """Hash password using bcrypt with salt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed):
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, "Valid email"
    return False, "Invalid email format"

# Rate limiting class
class LoginRateLimit:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoginRateLimit, cls).__new__(cls)
            cls._instance.attempts = {}  # {email: [timestamp1, timestamp2, ...]}
            cls._instance.max_attempts = 5
            cls._instance.window_minutes = 15
        return cls._instance
    
    def is_rate_limited(self, email):
        """Check if email is rate limited"""
        now = time.time()
        if email not in self.attempts:
            self.attempts[email] = []
        
        # Remove old attempts outside window
        cutoff = now - (self.window_minutes * 60)
        self.attempts[email] = [t for t in self.attempts[email] if t > cutoff]
        
        if len(self.attempts[email]) >= self.max_attempts:
            # Calculate remaining time
            oldest_attempt = min(self.attempts[email])
            remaining = int((oldest_attempt + (self.window_minutes * 60)) - now)
            return True, remaining
        
        return False, 0
    
    def record_attempt(self, email):
        """Record a login attempt"""
        if email not in self.attempts:
            self.attempts[email] = []
        self.attempts[email].append(time.time())

# Global rate limiter instance
rate_limiter = LoginRateLimit()

# Session persistence helpers
def save_session_to_storage():
    """Save session data using Streamlit's query params for persistence across refreshes"""
    if st.session_state.get('authenticated', False):
        # Create a simple session token (you can make this more secure)
        session_data = {
            'email': st.session_state.get('user_email'),
            'uid': st.session_state.get('user_uid'),
            'name': st.session_state.get('user_name'),
            'created': st.session_state.get('session_created')
        }

        # Store in session_state with a special key that persists
        if 'persisted_session' not in st.session_state:
            st.session_state.persisted_session = session_data

def restore_session_from_storage():
    """Restore session data from persisted storage"""
    if 'persisted_session' in st.session_state and st.session_state.persisted_session:
        session_data = st.session_state.persisted_session

        # Restore session state
        st.session_state.authenticated = True
        st.session_state.user_email = session_data.get('email')
        st.session_state.user_uid = session_data.get('uid')
        st.session_state.user_name = session_data.get('name')
        st.session_state.session_created = session_data.get('created')

        logger.info(f"Session restored for user: {session_data.get('email')}")
        return True
    return False

def is_session_expired():
    """Check if current session has expired"""
    # First check if we need to restore session from browser storage
    if 'session_created' not in st.session_state:
        # Try to restore session from stored session token
        restore_session_from_storage()

    if 'session_created' not in st.session_state:
        return True

    try:
        session_created = datetime.fromisoformat(st.session_state.session_created)
        session_timeout = timedelta(hours=24)  # 24 hour timeout

        return datetime.now() > session_created + session_timeout
    except (ValueError, TypeError):
        return True

def refresh_session():
    """Refresh session timestamp"""
    st.session_state.session_created = datetime.now().isoformat()

def is_authenticated():
    """Check if user is authenticated and session is valid"""
    if not st.session_state.get('authenticated', False):
        return False
    
    # Check if session has expired
    if is_session_expired():
        logout()
        return False
        
    return True

def get_user_email():
    """Get current user email"""
    return st.session_state.get('user_email', None)

def get_user_name():
    """Get current user name"""
    return st.session_state.get('user_name', None)

def get_user_uid():
    """Get current user UID"""
    return st.session_state.get('user_uid', None)

def save_user_to_database(user_data):
    """Save user data to Firestore database or local file"""
    try:
        firestore_client = get_firestore_client()
        if firestore_client and firestore_client.initialized:
            # Save to users collection
            user_ref = firestore_client.db.collection('users').document(user_data['uid'])
            user_ref.set(user_data, merge=True)
            logger.info(f"User saved to database: {user_data['email']}")
            return True
        else:
            # Fallback to in-memory storage and file
            USERS[user_data['email']] = user_data
            save_users_to_file()  # Persist to file
            logger.info(f"User saved to memory and file: {user_data['email']}")
            return True
    except Exception as e:
        logger.error(f"Error saving user to database: {e}")
        # Fallback to in-memory storage and file
        USERS[user_data['email']] = user_data
        save_users_to_file()  # Persist to file
        return True

def get_user_from_database(email):
    """Get user data from Firestore database"""
    try:
        firestore_client = get_firestore_client()
        if firestore_client and firestore_client.initialized:
            # Query users collection by email
            users_query = firestore_client.db.collection('users').where('email', '==', email)
            user_docs = users_query.stream()
            
            for doc in user_docs:
                user_data = doc.to_dict()
                logger.info(f"User loaded from database: {email}")
                return user_data
            
            # User not found in database
            return None
        else:
            # Fallback to in-memory storage
            return USERS.get(email)
    except Exception as e:
        logger.error(f"Error loading user from database: {e}")
        # Fallback to in-memory storage
        return USERS.get(email)

def authenticate_user(email, password):
    """Authenticate user with email and password"""
    try:
        # Check rate limiting
        is_limited, remaining = rate_limiter.is_rate_limited(email)
        if is_limited:
            return False, f"Too many login attempts. Try again in {remaining} seconds."
        
        # Record attempt
        rate_limiter.record_attempt(email)
        
        # Get user data from database or memory
        user_data = get_user_from_database(email)
        
        if user_data:
            stored_password = user_data['password']
            if verify_password(password, stored_password):
                # Set session state
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = user_data.get('name', email.split('@')[0])
                st.session_state.user_uid = user_data.get('uid', str(uuid.uuid4()))
                st.session_state.user_created_at = user_data.get('created_at', datetime.now().isoformat())
                
                # Refresh session timestamp
                refresh_session()

                # Save session for persistence across page refreshes
                save_session_to_storage()

                # Update last login time
                user_data['last_login'] = datetime.now().isoformat()
                save_user_to_database(user_data)

                logger.info(f"User {email} authenticated successfully")
                return True, "Authentication successful"
            else:
                return False, "Invalid password"
        else:
            return False, "User not found"
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False, f"Authentication error: {str(e)}"

def create_user_account(email, password, display_name):
    """Create a new user account"""
    try:
        # Validate email
        email_valid, email_msg = validate_email(email)
        if not email_valid:
            return False, email_msg
        
        # Validate password strength
        password_valid, password_msg = validate_password_strength(password)
        if not password_valid:
            return False, password_msg
        
        # Check rate limiting
        is_limited, remaining = rate_limiter.is_rate_limited(email)
        if is_limited:
            return False, f"Too many attempts. Try again in {remaining} seconds."
        
        # Check if user already exists
        existing_user = get_user_from_database(email)
        if existing_user:
            return False, "User already exists"
        
        # Create new user data
        user_data = {
            "email": email,
            "password": hash_password(password),
            "name": display_name,
            "uid": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Save to database
        if save_user_to_database(user_data):
            logger.info(f"User account created for {email}")
            return True, "Account created successfully"
        else:
            return False, "Failed to create account"
            
    except Exception as e:
        logger.error(f"Account creation error: {e}")
        return False, f"Account creation error: {str(e)}"

def logout():
    """Logout the current user"""
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.user_uid = None
    st.session_state.user_created_at = None
    st.session_state.session_created = None

    # Clear persisted session
    if 'persisted_session' in st.session_state:
        st.session_state.persisted_session = None

    logger.info("User logged out")

def login_page():
    """Display the login/signup page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🔐 MultiAgentAI21</h1>
        <p>Advanced Multi-Agent AI System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for login and signup
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
    
    with tab1:
        st.markdown("### Sign In to Access MultiAgentAI21")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Sign In", type="primary")
            
            if submit_button:
                if email and password:
                    success, message = authenticate_user(email, password)
                    if success:
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("Please enter both email and password")
        
    
    with tab2:
        st.markdown("### Create New Account")
        
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email", placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", key="signup_password", placeholder="Enter your password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            display_name = st.text_input("Display Name", placeholder="Enter your name")
            signup_button = st.form_submit_button("Sign Up", type="primary")
            
            if signup_button:
                if new_email and new_password and confirm_password and display_name:
                    if new_password == confirm_password:
                        success, message = create_user_account(new_email, new_password, display_name)
                        if success:
                            st.success("✅ Account created successfully! You can now sign in.")
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Passwords do not match")
                else:
                    st.warning("⚠️ Please fill in all fields")

def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("❌ Please sign in to access this feature")
            login_page()
            return
        
        # Check session timeout
        if is_session_expired():
            logout()
            st.error("⏰ Your session has expired. Please sign in again.")
            login_page()
            return
            
        return func(*args, **kwargs)
    return wrapper

