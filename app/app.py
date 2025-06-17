import sys
import os
from pathlib import Path
import logging
import streamlit as st
import atexit
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import tempfile
import time
from datetime import datetime # Explicitly import datetime here for clarity and robustness
import io # Added this import statement for BytesIO usage


# --- Streamlit Page Configuration (MUST BE FIRST) ---
# This ensures set_page_config is called only once and at the very beginning of script execution.
# Added a more robust check for st._page_config_set and st.session_state.page_config_set
if not hasattr(st, '_page_config_set') or not st.session_state.get('page_config_set', False):
    try:
        st.set_page_config(
            page_title="MultiAgentAI21 - Advanced AI Assistant",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        # Set a flag to indicate that set_page_config has been called.
        st._page_config_set = True # Attribute on st module
        st.session_state.page_config_set = True # Attribute in session_state
    except Exception as e:
        # If set_page_config was already called, log it but continue
        if "set_page_config()" in str(e) or "already been called" in str(e):
            print(f"Warning: set_page_config already called by an earlier script rerun: {e}")
        else:
            # Critical error at startup should stop the app from running further
            st.error(f"A critical error occurred at startup (set_page_config): {e}")
            st.stop()
else:
    # If the flag is already set, it means set_page_config was called in a previous rerun
    # This block is for logging purposes and will not re-call set_page_config
    pass


# Configure logging (moved after st.set_page_config)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Setting up page configuration and logging...")
logger.info("Page configuration set successfully")


logger.info("Application starting...")

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger.info(f"Project root (app.py detected as): {project_root}")
logger.info(f"Python path (sys.path) before import: {sys.path}")

# --- START ADDED DEBUGGING FOR MODULE NOT FOUND ERROR ---
logger.info("--- START DEBUGGING PATHS & FILES ---\n")

# Check if 'src' directory exists relative to project_root
src_dir_path = project_root / "src"
logger.info(f"Checking for 'src' directory at: {src_dir_path}")
if src_dir_path.exists():
    logger.info(f"'src' directory EXISTS at {src_dir_path}")
    logger.info(f"Contents of 'src' directory ({src_dir_path}): {[p.name for p in src_dir_path.iterdir()]}")
else:
    logger.error(f"'src' directory DOES NOT EXIST at {src_dir_path}")
    logger.error(f"Contents of project_root ({project_root}): {[p.name for p in project_root.iterdir()]}")


# Check for auth_manager.py inside src
auth_manager_path = src_dir_path / "auth_manager.py"
logger.info(f"Checking for 'auth_manager.py' at: {auth_manager_path}")
if auth_manager_path.exists():
    logger.info(f"'auth_manager.py' EXISTS at {auth_manager_path}")
else:
    logger.error(f"'auth_manager.py' DOES NOT EXIST at {auth_manager_path}")


# Check for __init__.py inside src
init_py_path = src_dir_path / "__init__.py"
logger.info(f"Checking for '__init__.py' at: {init_py_path}")
if init_py_path.exists():
    logger.info(f"'__init__.py' EXISTS at {init_py_path}")
else:
    logger.error(f"'__init__.py' DOES NOT EXIST at {init_py_path}")

logger.info("\n--- END DEBUGGING PATHS & FILES ---")
# --- END ADDED DEBUGGING ---

# Firebase Imports for Firestore (Client SDK)
from firebase_admin import credentials # For Firebase Admin SDK
from firebase_admin import auth # For Firebase Admin SDK
import firebase_admin # For Firebase Admin SDK
from google.cloud import firestore # For Firestore client library
import google.auth # For handling default credentials
import google.oauth2.credentials # For handling token-based credentials

# Import authentication module
try:
    from src.auth_manager import (
        initialize_firebase,
        login_required,
        login_page,
        logout,
        is_authenticated,
        get_current_user,
        setup_google_application_credentials
    )
    logger.info("Successfully imported src.auth_manager.")
except ModuleNotFoundError as e:
    logger.critical(f"ModuleNotFoundError: {e} - Cannot find 'src.auth_manager'. This indicates a pathing issue.", exc_info=True)
    st.error(f"Application failed to start due to a missing module. Please contact support. Error: {e}")
    st.stop()
except Exception as e:
    logger.critical(f"An unexpected error occurred during src.auth_manager import: {e}", exc_info=True)
    st.error(f"Application failed to start due to an unexpected import error. Error: {e}")
    st.stop()

# Call setup_google_application_credentials early to ensure GOOGLE_APPLICATION_CREDENTIALS is set
setup_google_application_credentials()

# Initialize Firebase Admin SDK first (from auth_manager)
try:
    initialize_firebase()
    logger.info("Firebase Admin SDK initialization completed successfully in app.py.")
except Exception as e:
    logger.critical(f"Failed to initialize Firebase Admin SDK in app.py: {e}", exc_info=True)
    st.error(f"An error occurred during Firebase Admin SDK initialization: {str(e)}")
    st.stop()

# --- Firestore Initialization (Client-Side) ---
# Global Firestore client instance
db = None

# Use the global variables provided by the Canvas environment, with a fallback for local execution
app_id = globals().get('__app_id', 'default-app-id')
firebase_config_str = globals().get('__firebase_config', '{}')
initial_auth_token = globals().get('__initial_auth_token', None)

@st.cache_resource
def get_firestore_client():
    """Initializes and caches the Firestore client."""
    global db
    if db:
        logger.info("Firestore client already initialized (from cache).")
        return db

    try:
        # Parse the firebase config provided by the Canvas environment
        firebase_config = json.loads(firebase_config_str)

        # Initialize Firestore client using the project ID from the config
        db = firestore.Client(project=firebase_config.get("projectId"))
        logger.info("Firestore client initialized successfully.")
        return db
    except google.auth.exceptions.DefaultCredentialsError as e:
        logger.critical(f"Google Cloud Default Credentials Error for Firestore: {e}. Please ensure GOOGLE_APPLICATION_CREDENTIALS is correctly set up.", exc_info=True)
        st.error(f"❌ Firestore initialization failed: Google Cloud credentials not found. Error: {e}")
        st.stop()
    except json.JSONDecodeError as e:
        logger.critical(f"JSON Decoding Error for __firebase_config: {e}", exc_info=True)
        st.error(f"❌ Firestore initialization failed: Invalid Firebase configuration provided. Error: {e}")
        st.stop()
    except Exception as e:
        logger.critical(f"Error initializing Firestore: {e}", exc_info=True)
        st.error(f"❌ An unexpected error occurred during Firestore initialization: {e}")
        st.stop()

# Initialize Firestore client once and cache it
db = get_firestore_client()

# --- Environment check function to consolidate warnings ---
def check_environment():
    issues = []
    
    # Check for Firebase API Key (client-side config)
    if not os.getenv("FIREBASE_API_KEY"):
        issues.append("FIREBASE_API_KEY is not set (may be needed for client-side functionality)")
    if not os.getenv("FIREBASE_AUTH_DOMAIN"):
        issues.append("FIREBASE_AUTH_DOMAIN is not set (may be needed for client-side functionality)")
    if not os.getenv("FIREBASE_PROJECT_ID"):
        issues.append("FIREBASE_PROJECT_ID is not set (may be needed for client-side functionality)")
    if not os.getenv("FIREBASE_STORAGE_BUCKET"):
        issues.append("FIREBASE_STORAGE_BUCKET is not set (may be needed for client-side functionality)")
    if not os.getenv("FIREBASE_MESSAGING_SENDER_ID"):
        issues.append("FIREBASE_MESSAGING_SENDER_ID is not set (may be needed for client-side functionality)")
    if not os.getenv("FIREBASE_APP_ID"):
        issues.append("FIREBASE_APP_ID is not set (may be needed for client-side functionality)")

    # Check for Google API Key (for Gemini etc.)
    if not os.getenv("GOOGLE_API_KEY"):
        issues.append("GOOGLE_API_KEY is not set")
    
    # Check for Google Cloud Project ID
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        issues.append("GOOGLE_CLOUD_PROJECT is not set")

    # IMPORTANT: Check GOOGLE_APPLICATION_CREDENTIALS
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        issues.append("GOOGLE_APPLICATION_CREDENTIALS is not set (expected a file path to service account key for Firebase Admin SDK and Firestore)")
    
    return issues

# Display environment warnings at the top if any issues exist
environment_issues = check_environment()
if environment_issues:
    st.error("Environment issues detected:")
    for issue in environment_issues:
        st.error(f"- {issue}")
    logger.error(f"Environment issues found: {environment_issues}")
else:
    logger.info("All essential environment variables appear to be set.")

try:
    logger.info("Attempting to import modules...")
    from src.agent_core import AgentType, MultiAgentCodingAI
    from src.data_analysis import DataAnalyzer
    logger.info("Successfully imported modules")
except ImportError as e:
    logger.error(f"Import error: {e}", exc_info=True)
    st.error(f"❌ Failed to import required modules: {e}")
    st.stop()

# Enhanced CSS for modern white interface
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        font-family: 'Inter', sans-serif;
        color: #1a202c;
    }

    .main-header {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 3rem 2rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(0, 0, 0, 0.1);
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .logo-icon {
        width: 60px;
        height: 60px;
        background: linear-gradient(45deg, #3b82f6, #8b5cf6);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
        color: white;
    }

    .agent-selection-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }

    .agent-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-top: 1.5rem;
    }

    .agent-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(0, 0, 0, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }

    .agent-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        border-color: rgba(59, 130, 246, 0.3);
    }

    .agent-card.selected {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(74, 222, 128, 0.05));
        border: 2px solid #22c55e;
        box-shadow: 0 0 30px rgba(34, 197, 94, 0.2);
    }

    .agent-card.disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none !important;
    }

    .agent-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .agent-icon {
        width: 50px;
        height: 50px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: white;
    }

    .automation-icon { background: linear-gradient(135deg, #ef4444, #f87171); }
    .data-analysis-icon { background: linear-gradient(135deg, #06b6d4, #0891b2); }
    .customer-service-icon { background: linear-gradient(135deg, #f59e0b, #f97316); }
    .content-creation-icon { background: linear-gradient(135deg, #8b5cf6, #a855f7); }

    .agent-name {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1a202c;
    }

    .agent-description {
        color: #4a5568;
        line-height: 1.6;
        margin-bottom: 1rem;
    }

    .agent-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
        color: #6b7280;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #22c55e;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }

    .chat-message {
        background: rgba(248, 250, 252, 0.8);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
        backdrop-filter: blur(10px);
        color: #1a202c;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .chat-message.ai-response {
        border-left-color: #22c55e;
        background: rgba(240, 253, 244, 0.8);
    }

    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }

    .section-title {
        color: #1a202c;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #2563eb, #1e40af);
    }

    .stButton[data-baseweb="button"][kind="primary"] > button {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        box-shadow: 0 8px 25px rgba(34, 197, 94, 0.3);
    }

    .stButton[data-baseweb="button"][kind="primary"] > button:hover {
        background: linear-gradient(135deg, #16a34a, #15803d);
        box_shadow: 0 8px 25px rgba(34, 197, 94, 0.4);
    }

    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        color: #1a202c;
    }

    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 12px;
        color: #1a202c;
    }

    .stTextArea > div > div > textarea::placeholder {
        color: #9ca3af;
    }

    .no-agent-selected {
        text-align: center;
        color: #6b7280;
        font-style: italic;
        padding: 3rem 2rem;
    }

    .no-agent-selected h3 {
        color: #374151;
        margin-bottom: 1rem;
    }

    .success-glow {
        animation: successGlow 1s ease-in-out;
    }

    @keyframes successGlow {
        0% { box-shadow: 0 0 5px rgba(34, 197, 94, 0.3); }
        50% { box-shadow: 0 0 20px rgba(34, 197, 94, 0.6); }
        100% { box-shadow: 0 0 5px rgba(34, 197, 94, 0.3); }
    }

    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
    }

    h1 {
        color: #1a202c !important;
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }

    .main-header p {
        color: #4a5568 !important;
        font-size: 1.2rem !important;
        margin: 0 !important;
    }

    .stMarkdown {
        color: #1a202c;
    }

    .stAlert {
        background: rgba(255, 255, 255, 0.95);
        color: #1a202c;
        border-radius: 12px;
    }

    .css-1xarl3l {
        color: #1a202c !important;
    }

    .css-1xarl3l .metric-value {
        color: #1a202c !important;
    }

    .page-content-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Define chat history storage (now uses Firestore)
CHAT_HISTORY_COLLECTION_NAME = "chat_histories"

def get_firestore_chat_collection():
    """Returns the Firestore collection reference for chat histories."""
    if db is None:
        st.error("Firestore client is not initialized. Cannot access chat history.")
        return None
    
    user_info = get_current_user()
    user_uid = user_info.get("uid")

    if not user_uid:
        logger.warning("No authenticated user UID found. Using an anonymous ID for chat history.")
        if "anonymous_user_id" not in st.session_state:
            st.session_state.anonymous_user_id = "anon_" + os.urandom(16).hex()
        user_uid = st.session_state.anonymous_user_id
    
    return db.collection("artifacts").document(app_id).collection("users").document(user_uid).collection(CHAT_HISTORY_COLLECTION_NAME)

def save_chat_history(chat_id: str, messages: list):
    """Save chat history to Firestore."""
    chat_collection = get_firestore_chat_collection()
    if chat_collection is None:
        logger.error("Attempted to save chat history but Firestore collection is None.")
        return

    try:
        chat_ref = chat_collection.document(chat_id)
        
        chat_data = {
            "chat_id": chat_id,
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_updated": firestore.SERVER_TIMESTAMP,
            "message_count": len(messages),
            "messages": messages
        }
        
        chat_ref.set(chat_data, merge=True)
        logger.info(f"Chat history saved to Firestore: {chat_id} ({len(messages)} messages)")
        
    except Exception as e:
        logger.error(f"Error saving chat history to Firestore: {e}", exc_info=True)
        st.error(f"Failed to save chat history to database: {str(e)}")

def load_chat_history(chat_id: str) -> list:
    """Load chat history from Firestore."""
    chat_collection = get_firestore_chat_collection()
    if chat_collection is None:
        logger.error("Attempted to load chat history but Firestore collection is None.")
        return []

    try:
        chat_ref = chat_collection.document(chat_id)
        doc = chat_ref.get()
        
        if doc.exists:
            chat_data = doc.to_dict()
            messages = chat_data.get("messages", [])
            logger.info(f"Chat history loaded from Firestore: {chat_id} ({len(messages)} messages)")
            return messages
        else:
            logger.warning(f"Chat history document not found in Firestore: {chat_id}")
            return []
        
    except Exception as e:
        logger.error(f"Error loading chat history from Firestore: {e}", exc_info=True)
        st.error(f"Failed to load chat history from database: {str(e)}")
        return []

def get_available_chats() -> list:
    """Get list of available chat sessions from Firestore."""
    
    # Check authentication first - ADD THIS
    if not is_authenticated():
        logger.debug("User not authenticated - returning empty chat list")
        return []
    
    chat_collection = get_firestore_chat_collection()
    if chat_collection is None:
        logger.error("Attempted to get available chats but Firestore collection is None.")
        return []

    try:
        chats = []
        chat_docs = chat_collection.order_by("last_updated", direction=firestore.Query.DESCENDING).stream()
        
        # COMPLETE THE FUNCTION - ADD THIS BACK:
        for doc in chat_docs:
            chat_data = doc.to_dict()
            chat_id = doc.id
            messages = chat_data.get("messages", [])
            
            preview = "New Chat"
            for message in messages:
                if message.get("role") == "user":
                    preview = message.get("content", "New Chat")[:50]
                    break
            
            created_at = chat_data.get("created_at")
            if created_at and hasattr(created_at, 'isoformat'):
                created_at = created_at.isoformat()
            else:
                created_at = datetime.now().isoformat()

            last_updated = chat_data.get("last_updated")
            if last_updated and hasattr(last_updated, 'isoformat'):
                last_updated = last_updated.isoformat()
            else:
                last_updated = datetime.now().isoformat()

            chats.append({
                "id": chat_id,
                "preview": preview,
                "created_at": created_at,
                "last_updated": last_updated,
                "message_count": len(messages)
            })
        
        logger.info(f"Found {len(chats)} available chat histories in Firestore.")
        return chats
        
    except Exception as e:
        logger.error(f"Error getting available chats from Firestore: {e}", exc_info=True)
        st.error(f"Failed to retrieve available chats from database: {str(e)}")
        return []

# Then continue with your session state initialization...
        
# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None
if "agent_locked" not in st.session_state:
    st.session_state.agent_locked = False
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
if "available_chats" not in st.session_state:
    st.session_state.available_chats = []
if "last_analysis_results" not in st.session_state:
    st.session_state.last_analysis_results = None
if "analysis_temp_files" not in st.session_state:
    st.session_state.analysis_temp_files = []
if "user_info" not in st.session_state:
    st.session_state.user_info = None

@st.cache_resource
def get_agent_system():
    """Create and return the MultiAgentAI21 instance (cached resource)"""
    try:
        logger.info("Starting MultiAgentAI21 initialization...")
        
        logger.info("Checking environment variables...")
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            error_msg = "GOOGLE_API_KEY environment variable is not set"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("GOOGLE_API_KEY found")
        
        logger.info("Creating MultiAgentAI21 instance...")
        try:
            agent_instance = MultiAgentCodingAI()
            logger.info("MultiAgentAI21 instance created successfully")
            return agent_instance
        except Exception as e:
            error_msg = f"Error creating MultiAgentAI21 instance: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)
            
    except Exception as e:
        error_msg = f"Failed to initialize agent system: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(f"❌ {error_msg}")
        return None

def display_enhanced_header():
    """Display the enhanced header with modern design"""
    st.markdown(
        """
    <div class="main-header">
        <div class="logo-container">
            <div class="logo-icon">🚀</div>
            <h1>MultiAgentAI21</h1>
        </div>
        <p>Advanced Multi-Agent AI System for Complex Problem Solving</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

def display_chat_history_sidebar():
    """Display chat history in the sidebar."""
    st.sidebar.title("💬 Chat History")

    if st.sidebar.button("🔄 Clear Cache & Reload", key="clear_cache_btn"):
        st.cache_resource.clear()
        st.session_state.agent = None
        # Clear session state related to user info and auth
        if "user_info" in st.session_state:
            del st.session_state.user_info
        st.success("Cache cleared! Please refresh the page.")
        st.rerun()

    # New Chat button
    if st.sidebar.button("✨ New Chat", key="new_chat_btn"):
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
        st.session_state.chat_history = []
        st.session_state.agent_locked = False
        st.session_state.selected_agent = None
        st.success("New chat started!")
        st.rerun()

    # ADD THIS CHECK - Only load chat history if user is authenticated
    if not is_authenticated():
        st.sidebar.info("🔒 Please log in to see chat history")
        return

    # Display available chats
    # Re-fetch available chats to reflect latest from Firestore
    # Only try to get available chats if db is successfully initialized
    if db is not None:
        st.session_state.available_chats = get_available_chats() 
    else:
        st.session_state.available_chats = [] # Ensure it's always a list
        st.sidebar.warning("Firestore client not available. Cannot load chat history.")

    # ... rest of your existing chat history code remains the same
    # ... rest of your existing chat history code ...


def display_agent_selection():
    """Display agent selection interface."""
    if not st.session_state.agent_locked:
        st.subheader("🤖 Select an Agent")
        agent_type = st.radio(
            "Choose an agent type:",
            [agent.value for agent in AgentType],
            format_func=lambda x: x.replace("_", " ").title(),
            key="agent_selection",
        )

        if st.button("🚀 Start Chat", key="start_chat_btn"):
            st.session_state.selected_agent = agent_type
            st.session_state.agent_locked = True
            st.success(f"Connected to {agent_type.replace('_', ' ').title()} Agent!")
            st.rerun()
    else:
        st.success(f"🤖 Chatting with {st.session_state.selected_agent.replace('_', ' ').title()} Agent")
        if st.button("🔄 Change Agent", key="change_agent_btn"):
            st.session_state.agent_locked = False
            st.session_state.selected_agent = None
            st.rerun()


def display_chat_messages():
    """Display chat messages in the main area."""
    # Add the warning as an assistant message to chat history when it's empty
    if not st.session_state.chat_history:
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": "MultiAgentAI21 can make mistakes. Always verify important information."
        })

    # Display chat messages (no explicit header for conversation count)
    # The messages will fill the available space dynamically
    for i, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Add metadata for assistant messages
            if message["role"] == "assistant":
                metadata = []
                if "execution_time" in message:
                    metadata.append(f"⏱️ {message['execution_time']:.2f}s")
                if "agent_type" in message:
                    metadata.append(f"🤖 {message['agent_type'].replace('_', ' ').title()}")
                if "timestamp" in message:
                    timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%H:%M:%S")
                    metadata.append(f"🕐 {timestamp}")
                
                if metadata:
                    st.caption(" | ".join(metadata))


def process_and_display_user_message(user_input):
    """Process user message and update chat history."""
    if not st.session_state.agent:
        st.error("❌ Agent system not initialized")
        return

    if not st.session_state.selected_agent:
        st.error("❌ Please select an agent first")
        return

    # Add user message to chat history
    user_message = {"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()}
    st.session_state.chat_history.append(user_message)

    try:
        # Convert string to AgentType enum
        agent_type = AgentType(st.session_state.selected_agent)
        
        # Process the request
        with st.spinner("🤖 Processing your request..."):
            response = st.session_state.agent.route_request(
                user_input,
                agent_type,
                {"chat_history": st.session_state.chat_history}
            )

        if response and response.content:
            # Add assistant response to chat history
            assistant_message = {
                "role": "assistant", 
                "content": response.content,
                "timestamp": datetime.now().isoformat(),
                "execution_time": getattr(response, 'execution_time', 0),
                "agent_type": st.session_state.selected_agent
            }
            st.session_state.chat_history.append(assistant_message)
            
            # Save chat history to Firestore
            save_chat_history(st.session_state.current_chat_id, st.session_state.chat_history)
            
            st.success(f"✅ Response from {agent_type.value.replace('_', ' ').title()} Agent")
        else:
            error_message = {
                "role": "assistant",
                "content": "Sorry, I couldn't process your request. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.chat_history.append(error_message)
            st.error("❌ Failed to get response from agent")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        error_message = {
            "role": "assistant",
            "content": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.chat_history.append(error_message)
        st.error(f"❌ Error: {str(e)}")

    # Save updated chat history (redundant but safe after adding to history)
    # save_chat_history(st.session_state.current_chat_id, st.session_state.chat_history)
    st.rerun()


def display_chat_interface():
    """Display the main chat interface"""
    st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
    st.header("💬 Chat with MultiAgentAI21")

    # Agent selection (at the top of the chat area)
    display_agent_selection()

    # Display chat messages (includes system warning if history is empty)
    display_chat_messages()

    # Chat input at the bottom of the main chat area
    # This is the single, primary chat input for the page
    user_input = st.chat_input("Type your message here...")
    if user_input:
        process_and_display_user_message(user_input)

    # The sidebar chat history is handled in main() as it's a global element
    # No more redundant containers or headers here
    st.markdown('</div>', unsafe_allow_html=True) # Close the page-content-container


def show_agent_examples():
    """Show examples based on selected agent"""
    st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
    st.header("📚 Agent Examples")
    if not st.session_state.selected_agent:
        st.info("Please select an agent in the 'Agent Chat' section to see examples.")
        st.markdown('</div>', unsafe_allow_html=True) # Close page-content-container
        return

    examples = {
        AgentType.AUTOMATION: [
            "Automate our customer onboarding process",
            "Create a workflow for invoice processing",
            "Set up automated email responses",
        ],
        AgentType.DATA_ANALYSIS: [
            "Analyze sales trends for the last quarter",
            "Create a customer satisfaction dashboard",
            "Generate insights from marketing data",
        ],
        AgentType.CUSTOMER_SERVICE: [
            "Handle an angry customer complaint about a defective product",
            "Resolve a technical support issue",
            "Explain our return policy",
        ],
        AgentType.CONTENT_CREATION: [
            "Write a blog post about AI trends",
            "Create social media content",
            "Draft a professional email newsletter",
        ],
    }

    agent_examples = examples.get(st.session_state.selected_agent, [])

    st.info("💡 Try these examples:")
    for example in agent_examples:
        if st.button(f"▶️ {example}", key=f"example_{example}"):
            # You would call a function here to send the example to the agent
            # For now, let's just add it to chat history for demonstration
            # process_user_request(example)
            st.session_state.chat_history.append({"role": "user", "content": example, "timestamp": datetime.now().isoformat()})
            st.warning("Example functionality not fully implemented. Add your agent call here!")
            st.rerun()


def cleanup_analysis_files():
    """Clean up temporary analysis files."""
    if st.session_state.analysis_temp_files:
        for file_path in st.session_state.analysis_temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing temporary file {file_path}: {e}")
        st.session_state.analysis_temp_files = []


def display_data_analysis_section():
    """Display the data analysis section of the app"""
    st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
    st.header("📊 Data Analysis Dashboard")
    
    # Analysis type selection
    st.subheader("Select Analysis Types")
    analysis_options = {
        "Summary": "summary",
        "Insights": "insights",
        "Visualizations": "visualizations",
        "Department Analysis": "department_analysis",
        "Education Analysis": "education_analysis",
        "Recommendations": "recommendations"
    }
    selected_analysis_keys = st.multiselect(
        "Choose the types of analysis to perform:",
        options=list(analysis_options.keys()),
        default=list(analysis_options.keys()), # Select all by default
        key="analysis_type_selection"
    )
    selected_analysis_types = [analysis_options[key] for key in selected_analysis_keys]

    # File upload section
    uploaded_file = st.file_uploader(
        "Upload your data file (CSV format)",
        type=["csv"],
        help="Upload a CSV file for analysis",
    )
    
    if uploaded_file is not None:
        try:
            # Clean up any existing temporary files
            cleanup_analysis_files()
            
            # Create a BytesIO object from the uploaded file buffer
            uploaded_file_buffer = io.BytesIO(uploaded_file.getvalue())

            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            logger.info(f"Uploaded file name: {uploaded_file.name}")

            # Instantiate DataAnalyzer
            data_analyzer = DataAnalyzer()

            # Perform analysis
            with st.spinner("Analyzing data... This may take a moment."):
                # Pass the BytesIO object directly to the analyzer
                results = data_analyzer.analyze_data(uploaded_file_buffer, selected_analysis_types)
                st.session_state.last_analysis_results = results # Store results for display

            if st.session_state.last_analysis_results:
                st.subheader("Analysis Results:")
                for analysis_type, content in st.session_state.last_analysis_results.items():
                    if content:
                        if analysis_type == "visualizations" and isinstance(content, dict):
                            st.markdown(f"**{analysis_type.replace('_', ' ').title()}**")
                            # Handle plotly figures from data_analysis.py
                            for plot_name, fig_json in content.items():
                                try:
                                    fig = go.Figure(json.loads(fig_json))
                                    st.plotly_chart(fig, use_container_width=True)
                                except json.JSONDecodeError:
                                    st.warning(f"Could not load plot '{plot_name}'. Invalid JSON.")
                                    st.json(fig_json) # Show raw JSON for debugging
                        else:
                            # Check if the content contains our special Plotly JSON tag
                            if isinstance(content, str) and "{PLOT_JSON::" in content:
                                parts = content.split("{PLOT_JSON::")
                                st.markdown(parts[0], unsafe_allow_html=True) # Display text before plot
                                for part in parts[1:]:
                                    if "}" in part:
                                        plot_json_str = part.split("}")[0]
                                        try:
                                            fig = go.Figure(json.loads(plot_json_str))
                                            st.plotly_chart(fig, use_container_width=True)
                                        except json.JSONDecodeError:
                                            st.warning(f"Could not load embedded plot. Invalid JSON.")
                                            st.text(plot_json_str) # Show raw JSON
                                        st.markdown(part.split("}", 1)[1], unsafe_allow_html=True) # Display text after plot
                                    else:
                                        st.markdown(part, unsafe_allow_html=True) # In case of malformed tag
                            else:
                                st.markdown(f"**{analysis_type.replace('_', ' ').title()}**")
                                st.write(content)
                    else:
                        st.info(f"No {analysis_type.replace('_', ' ')} results to display.")
            else:
                st.warning("No analysis results were generated.")

        except Exception as e:
            st.error(f"Error during data analysis: {e}")
            logger.error(f"Error during data analysis: {e}", exc_info=True)
            if "Authentication" in str(e) or "credentials" in str(e):
                st.warning("It looks like there might be a Google Cloud authentication issue. Please ensure your `google_application_credentials_key.json` is correct and properly mounted.")

    st.markdown('</div>', unsafe_allow_html=True) # Close page-content-container


def display_analytics_dashboard():
    """Display an analytics dashboard."""
    st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
    st.header("📈 Analytics Dashboard")
    st.write("Visualize your data with interactive charts.")
    st.info("Integrate Plotly or Matplotlib for dynamic dashboards.")

    # Mock data for demonstration
    data = {
        'Category': ['A', 'B', 'C', 'D', 'E'],
        'Value1': [10, 20, 15, 25, 30],
        'Value2': [12, 18, 22, 10, 28]
    }
    df = pd.DataFrame(data)

    st.subheader("Sample Bar Chart")
    fig = px.bar(df, x='Category', y='Value1', title='Category vs Value1')
    st.plotly_chart(fig)

    st.subheader("Sample Scatter Plot")
    fig2 = px.scatter(df, x='Value1', y='Value2', color='Category', title='Value1 vs Value2 by Category')
    st.plotly_chart(fig2)
    st.markdown('</div>', unsafe_allow_html=True)


def display_footer():
    """Display the global footer."""
    st.markdown("---")
    st.markdown("<p style='text-align: center; font-size: small;'>Powered by Gemini | MultiAgentAI21 can make mistakes. Always verify important information.</p>", unsafe_allow_html=True)


def user_profile_sidebar():
    """Display user profile in sidebar"""
    # Ensure is_authenticated is checked before trying to get user data
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


# Main application logic
@login_required # Ensure this decorator works after import
def main_app():
    try:
        # Display header
        logger.info("Displaying header...")
        display_enhanced_header()

        # Initialize the agent system (ensure this runs only once)
        if st.session_state.agent is None:
            logger.info("Agent system not yet initialized in session state. Attempting to get it.")
            st.session_state.agent = get_agent_system()
            if st.session_state.agent:
                logger.info("Agent system successfully initialized and assigned to session state.")
            else:
                logger.error("Failed to get agent system. Further agent operations will fail.")
                st.error("Failed to initialize the agent system. Please check logs and environment variables.")
                return # Stop if agent system couldn't be initialized


        # Create sidebar navigation
        logger.info("Setting up navigation...")
        st.sidebar.title("Navigation")
        
        # Display user profile and chat history in sidebar (if logged in)
        user_profile_sidebar()
        display_chat_history_sidebar() # Moved from main_app to a separate function

        page = st.sidebar.radio(
            "Select a page",
            ["🤖 Agent Chat", "📊 Data Analysis", "📈 Analytics Dashboard", "📚 Examples"],
        )

        logger.info(f"Selected page: {page}")

        if page == "🤖 Agent Chat":
            display_chat_interface()
        elif page == "📊 Data Analysis":
            display_data_analysis_section()
        elif page == "📈 Analytics Dashboard":
            display_analytics_dashboard()
        elif page == "📚 Examples":
            show_agent_examples() # Changed to show_agent_examples
        
        logger.info("Main application completed successfully")

        # Clean up temporary files when the app is closed
        atexit.register(cleanup_analysis_files)

        # Display the global footer
        display_footer()

    except Exception as e:
        logger.error(f"Error in main application: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check the logs for more details")


if __name__ == "__main__":
    try:
        logger.info("Entering main execution block.")
        # The st.set_page_config is now handled at the very top of the script globally.
        # Check authentication state and run main app or login page.
        if not is_authenticated():
            login_page()
        else:
            main_app()
    except Exception as e:
        logger.critical(f"Critical error in main application execution: {e}", exc_info=True)
        st.error(f"A critical error prevented the application from running: {str(e)}")
    
