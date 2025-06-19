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
from datetime import datetime
import io

# --- Streamlit Page Configuration (MUST BE FIRST) ---
if not hasattr(st, '_page_config_set') or not st.session_state.get('page_config_set', False):
    try:
        st.set_page_config(
            page_title="MultiAgentAI21 - Advanced AI Assistant",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        st._page_config_set = True
        st.session_state.page_config_set = True
    except Exception as e:
        if "set_page_config()" in str(e) or "already been called" in str(e):
            print(f"Warning: set_page_config already called by an earlier script rerun: {e}")
        else:
            st.error(f"A critical error occurred at startup (set_page_config): {e}")
            st.stop()

# Configure logging
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

# --- START DEBUGGING FOR MODULE NOT FOUND ERROR ---
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

# Firebase Imports for Firestore (Client SDK)
from firebase_admin import credentials
from firebase_admin import auth
import firebase_admin
from google.cloud import firestore
import google.auth
import google.oauth2.credentials

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

@st.cache_resource
def get_firestore_client():
    """Initializes and caches the Firestore client."""
    global db
    if db:
        logger.info("Firestore client already initialized (from cache).")
        return db

    try:
        # Use your specific project ID and database name
        PROJECT_ID = "multiagentai21-9a8fc"
        DATABASE_NAME = "multiagentaifirestoredatabase"
        
        # Initialize Firestore client with explicit project ID and database name
        db = firestore.Client(project=PROJECT_ID, database=DATABASE_NAME)
        logger.info(f"Firestore client initialized successfully for project: {PROJECT_ID}, database: {DATABASE_NAME}")
        return db
        
    except google.auth.exceptions.DefaultCredentialsError as e:
        logger.critical(f"Google Cloud Default Credentials Error for Firestore: {e}. Please ensure GOOGLE_APPLICATION_CREDENTIALS is correctly set up.", exc_info=True)
        st.error(f"❌ Firestore initialization failed: Google Cloud credentials not found. Error: {e}")
        st.error("Please ensure your service account key is properly configured.")
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
    
    # Check for Google Cloud Project ID with correct project
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        issues.append("GOOGLE_CLOUD_PROJECT is not set (should be 'multiagentai21-9a8fc')")
    elif os.getenv("GOOGLE_CLOUD_PROJECT") != "multiagentai21-9a8fc":
        issues.append(f"GOOGLE_CLOUD_PROJECT is set to '{os.getenv('GOOGLE_CLOUD_PROJECT')}' but should be 'multiagentai21-9a8fc'")

    # IMPORTANT: Check GOOGLE_APPLICATION_CREDENTIALS
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        issues.append("GOOGLE_APPLICATION_CREDENTIALS is not set (expected a file path to service account key for Firebase Admin SDK and Firestore)")
    elif not os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
        issues.append(f"GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    
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

    /* Integrated chat container */
    .integrated-chat-container {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        margin-top: 1rem;
        display: flex;
        flex-direction: column;
        min-height: 500px;
        max-height: 70vh;
    }

    /* Chat messages area */
    .stChatMessageContainer {
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem;
    }

    /* Integrated input area */
    .integrated-input-area {
        background: rgba(248, 250, 252, 0.95);
        border-top: 1px solid rgba(0, 0, 0, 0.08);
        padding: 1.5rem;
        backdrop-filter: blur(10px);
    }

    /* Text area styling */
    .integrated-input-area .stTextArea > div > div > textarea {
        background: white;
        border: 2px solid rgba(226, 232, 240, 0.8);
        border-radius: 16px;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        resize: none;
    }

    .integrated-input-area .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        outline: none;
    }

    /* File upload styling */
    .integrated-input-area .stFileUploader {
        margin-top: 0.5rem;
    }

    .integrated-input-area .stFileUploader > div {
        background: white;
        border: 2px dashed rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.3s ease;
    }

    .integrated-input-area .stFileUploader > div:hover {
        border-color: #3b82f6;
        background: rgba(59, 130, 246, 0.02);
    }

    /* Expander styling for file upload */
    .integrated-input-area .streamlit-expanderHeader {
        background: rgba(59, 130, 246, 0.05);
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: 500;
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

    /* Attach button styling */
    button[key="attach_btn"] {
        background: white !important;
        border: 2px solid rgba(226, 232, 240, 0.8) !important;
        color: #64748b !important;
        font-size: 1.2rem !important;
        padding: 0.5rem !important;
        width: 40px !important;
        height: 40px !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }

    button[key="attach_btn"]:hover {
        border-color: #3b82f6 !important;
        color: #3b82f6 !important;
        background: rgba(59, 130, 246, 0.05) !important;
    }

    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        color: #1a202c;
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

    /* Hide the default Streamlit footer */
    footer {
        visibility: hidden;
        height: 0;
    }

    /* Custom footer styling */
    .custom-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 0.5rem 0;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        z-index: 10;
        text-align: center;
    }

    .custom-footer p {
        margin: 0;
        font-size: 0.875rem;
        color: #6b7280;
    }

    /* Ensure content doesn't go under footer */
    .main {
        padding-bottom: 60px;
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
    
    return db.collection("users").document(user_uid).collection(CHAT_HISTORY_COLLECTION_NAME)

def save_chat_history(chat_id: str, messages: list):
    """Save chat history to Firestore."""
    chat_collection = get_firestore_chat_collection()
    if chat_collection is None:
        logger.error("Attempted to save chat history but Firestore collection is None.")
        return

    try:
        chat_ref = chat_collection.document(chat_id)
        
        # Get current timestamp
        from google.cloud.firestore_v1 import SERVER_TIMESTAMP
        
        # Check if document exists to determine if this is first save
        doc = chat_ref.get()
        
        if doc.exists:
            # Update existing document
            chat_data = {
                "chat_id": chat_id,
                "last_updated": SERVER_TIMESTAMP,
                "message_count": len(messages),
                "messages": messages
            }
        else:
            # Create new document
            chat_data = {
                "chat_id": chat_id,
                "created_at": SERVER_TIMESTAMP,
                "last_updated": SERVER_TIMESTAMP,
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
    
    # Check authentication first
    if not is_authenticated():
        logger.debug("User not authenticated - returning empty chat list")
        return []
    
    # Get current user info for debugging
    user_info = get_current_user()
    user_uid = user_info.get("uid")
    logger.info(f"Getting chats for user: {user_uid}")
    
    chat_collection = get_firestore_chat_collection()
    if chat_collection is None:
        logger.error("Attempted to get available chats but Firestore collection is None.")
        return []

    try:
        chats = []
        
        # Debug: Log collection info (without using .path which doesn't exist)
        logger.info(f"Querying collection for user: {user_uid}")
        
        # Get all documents first to see what's there
        all_docs = list(chat_collection.stream())
        logger.info(f"Total documents in collection: {len(all_docs)}")
        
        # Now query with ordering
        try:
            chat_docs = chat_collection.order_by("last_updated", direction=firestore.Query.DESCENDING).stream()
        except Exception as e:
            logger.warning(f"Could not order by last_updated, falling back to unordered: {e}")
            chat_docs = chat_collection.stream()
        
        for doc in chat_docs:
            try:
                chat_data = doc.to_dict()
                chat_id = doc.id
                
                logger.debug(f"Processing chat {chat_id} with data keys: {list(chat_data.keys())}")
                
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
                
            except Exception as e:
                logger.error(f"Error processing chat document {doc.id}: {e}", exc_info=True)
                continue
        
        logger.info(f"Successfully retrieved {len(chats)} chat histories.")
        return chats
        
    except Exception as e:
        logger.error(f"Error getting available chats from Firestore: {e}", exc_info=True)
        st.error(f"Failed to retrieve available chats from database: {str(e)}")
        return []

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

    # Check authentication
    if not is_authenticated():
        st.sidebar.info("🔒 Please log in to see chat history")
        return

    # Display available chats
    # Re-fetch available chats to reflect latest from Firestore
    if db is not None:
        try:
            st.session_state.available_chats = get_available_chats()
            
            # Display the chats
            if st.session_state.available_chats:
                st.sidebar.subheader("Recent Chats")
                
                # Display current chat indicator
                if st.session_state.current_chat_id:
                    st.sidebar.caption(f"Current: {st.session_state.current_chat_id[:8]}...")
                
                # Display each chat as a button
                for chat in st.session_state.available_chats:
                    chat_id = chat["id"]
                    preview = chat["preview"][:30] + "..." if len(chat["preview"]) > 30 else chat["preview"]
                    message_count = chat.get("message_count", 0)
                    
                    # Format the last updated time
                    try:
                        last_updated = datetime.fromisoformat(chat.get("last_updated", ""))
                        time_str = last_updated.strftime("%m/%d %H:%M")
                    except:
                        time_str = "Unknown"
                    
                    # Highlight current chat
                    is_current = chat_id == st.session_state.current_chat_id
                    button_label = f"{'▶ ' if is_current else ''}💬 {preview} ({message_count} msgs) - {time_str}"
                    
                    if st.sidebar.button(button_label, key=f"chat_{chat_id}", disabled=is_current):
                        # Load the selected chat
                        st.session_state.current_chat_id = chat_id
                        loaded_messages = load_chat_history(chat_id)
                        
                        if loaded_messages:
                            st.session_state.chat_history = loaded_messages
                            st.session_state.agent_locked = True
                            
                            # Extract agent type from chat history if available
                            for msg in loaded_messages:
                                if msg.get("agent_type"):
                                    st.session_state.selected_agent = msg["agent_type"]
                                    st.session_state.agent_locked = True
                                    break
                            
                            st.success(f"Loaded chat: {preview}")
                        else:
                            st.warning("Chat history is empty or could not be loaded.")
                        
                        st.rerun()
                
                # Add delete functionality
                st.sidebar.markdown("---")
                if st.sidebar.button("🗑️ Delete Current Chat", key="delete_chat_btn"):
                    if st.session_state.current_chat_id:
                        try:
                            chat_collection = get_firestore_chat_collection()
                            if chat_collection:
                                chat_collection.document(st.session_state.current_chat_id).delete()
                                st.success("Chat deleted!")
                                # Start a new chat
                                st.session_state.current_chat_id = f"chat_{int(time.time())}"
                                st.session_state.chat_history = []
                                st.session_state.agent_locked = False
                                st.session_state.selected_agent = None
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete chat: {e}")
                            
            else:
                st.sidebar.info("No previous chats found. Start a new conversation!")
                
        except Exception as e:
            logger.error(f"Error displaying chat history: {e}", exc_info=True)
            st.sidebar.error(f"Failed to load chat history: {str(e)}")
    else:
        st.sidebar.warning("Firestore client not available. Cannot load chat history.")

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
    # Show welcome message if chat is empty
    if not st.session_state.chat_history:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #6b7280;">
            <h3 style="color: #4b5563; margin-bottom: 1rem;">Welcome to MultiAgentAI21! 👋</h3>
            <p>Select an agent above and start chatting. You can also attach files to your messages.</p>
            <p style="font-size: 0.9rem; margin-top: 0.5rem;">💡 Tip: Use the 📎 button to attach files</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display chat messages
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

    st.rerun()

def display_chat_interface():
    """Display the main chat interface"""
    st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
    st.header("💬 Chat with MultiAgentAI21")

    # Agent selection (at the top of the chat area)
    display_agent_selection()

    # Chat messages container with integrated input
    st.markdown('<div class="integrated-chat-container">', unsafe_allow_html=True)
    
    # Display chat messages
    display_chat_messages()
    
    # Integrated chat input area at the bottom of chat container
    st.markdown('<div class="integrated-input-area">', unsafe_allow_html=True)
    
    # File upload state management
    if "show_file_upload" not in st.session_state:
        st.session_state.show_file_upload = False
    
    # Main input container
    input_container = st.container()
    
    with input_container:
        # Create the main input row
        input_col1, input_col2 = st.columns([10, 1])
        
        with input_col1:
            user_input = st.text_area(
                "Message",
                placeholder="Type your message here... (Press Ctrl+Enter to send)",
                height=100,
                key="chat_input",
                label_visibility="collapsed"
            )
        
        with input_col2:
            # Attach files button
            if st.button("📎", key="attach_btn", help="Attach files", use_container_width=True):
                st.session_state.show_file_upload = not st.session_state.show_file_upload
                st.rerun()
        
        # File upload area (shown/hidden based on state)
        if st.session_state.show_file_upload:
            with st.expander("📎 Attach files", expanded=True):
                uploaded_files = st.file_uploader(
                    "Drag and drop files here",
                    accept_multiple_files=True,
                    key="chat_file_upload",
                    type=['txt', 'pdf', 'csv', 'xlsx', 'json', 'py', 'js', 'html', 'css', 'md', 
                          'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx', 'xml', 'yaml', 'yml', 'htm'],
                    label_visibility="collapsed"
                )
                
                # Display uploaded files
                if uploaded_files:
                    st.markdown("**Attached files:**")
                    for idx, file in enumerate(uploaded_files):
                        file_size = f"{file.size / 1024:.1f} KB" if file.size < 1024*1024 else f"{file.size / (1024*1024):.1f} MB"
                        col1, col2 = st.columns([10, 1])
                        with col1:
                            st.caption(f"📄 {file.name} ({file_size})")
                        with col2:
                            # Individual file remove buttons could be added here if needed
                            pass
        else:
            uploaded_files = st.session_state.get('chat_file_upload', [])
        
        # Show attached files count if files are uploaded but upload area is hidden
        if uploaded_files and not st.session_state.show_file_upload:
            st.caption(f"📎 {len(uploaded_files)} file(s) attached")
        
        # Send button
        send_col1, send_col2, send_col3 = st.columns([4, 4, 2])
        with send_col3:
            send_clicked = st.button("Send 📤", key="send_button", type="primary", use_container_width=True)
        
        # Process message when send is clicked
        if send_clicked and (user_input or uploaded_files):
            # Prepare the message with file information
            message_parts = []
            
            if user_input:
                message_parts.append(user_input)
            
            if uploaded_files:
                file_info = []
                for uploaded_file in uploaded_files:
                    # Store file temporarily if needed for processing
                    temp_dir = tempfile.mkdtemp()
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Add to temp files for cleanup
                    if "temp_files" not in st.session_state:
                        st.session_state.temp_files = []
                    st.session_state.temp_files.append(file_path)
                    
                    file_info.append({
                        "name": uploaded_file.name,
                        "type": uploaded_file.type,
                        "size": uploaded_file.size,
                        "path": file_path
                    })
                
                # Add file information to message
                files_text = "\n\n📎 **Attached files:**\n"
                for f in file_info:
                    files_text += f"- {f['name']} ({f['type']}, {f['size']} bytes)\n"
                
                message_parts.append(files_text)
            
            # Combine all parts into final message
            full_message = "\n".join(message_parts)
            
            # Process the message
            process_and_display_user_message(full_message)
            
            # Clear the inputs and hide file upload area after sending
            st.session_state.chat_input = ""
            st.session_state.show_file_upload = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close integrated-input-area
    st.markdown('</div>', unsafe_allow_html=True)  # Close integrated-chat-container
    st.markdown('</div>', unsafe_allow_html=True)  # Close page-content-container

def show_agent_examples():
    """Show examples based on selected agent"""
    st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
    st.header("📚 Agent Examples")
    if not st.session_state.selected_agent:
        st.info("Please select an agent in the 'Agent Chat' section to see examples.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    examples = {
        AgentType.AUTOMATION.value: [
            "Automate our customer onboarding process",
            "Create a workflow for invoice processing",
            "Set up automated email responses",
        ],
        AgentType.DATA_ANALYSIS.value: [
            "Analyze sales trends for the last quarter",
            "Create a customer satisfaction dashboard",
            "Generate insights from marketing data",
        ],
        AgentType.CUSTOMER_SERVICE.value: [
            "Handle an angry customer complaint about a defective product",
            "Resolve a technical support issue",
            "Explain our return policy",
        ],
        AgentType.CONTENT_CREATION.value: [
            "Write a blog post about AI trends",
            "Create social media content",
            "Draft a professional email newsletter",
        ],
    }

    agent_examples = examples.get(st.session_state.selected_agent, [])

    st.info("💡 Try these examples:")
    for example in agent_examples:
        if st.button(f"▶️ {example}", key=f"example_{example}"):
            # Navigate to Agent Chat page and send the example
            st.session_state.pending_message = example
            st.session_state.page = "🤖 Agent Chat"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

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

def cleanup_temp_files():
    """Clean up temporary files created during chat."""
    if "temp_files" in st.session_state and st.session_state.temp_files:
        for file_path in st.session_state.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed temporary file: {file_path}")
                # Also try to remove the directory if empty
                dir_path = os.path.dirname(file_path)
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except Exception as e:
                logger.error(f"Error removing temporary file {file_path}: {e}")
        st.session_state.temp_files = []

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
        default=list(analysis_options.keys()),
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
                st.session_state.last_analysis_results = results

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
                                    st.json(fig_json)
                        else:
                            # Check if the content contains our special Plotly JSON tag
                            if isinstance(content, str) and "{PLOT_JSON::" in content:
                                parts = content.split("{PLOT_JSON::")
                                st.markdown(parts[0], unsafe_allow_html=True)
                                for part in parts[1:]:
                                    if "}" in part:
                                        plot_json_str = part.split("}")[0]
                                        try:
                                            fig = go.Figure(json.loads(plot_json_str))
                                            st.plotly_chart(fig, use_container_width=True)
                                        except json.JSONDecodeError:
                                            st.warning(f"Could not load embedded plot. Invalid JSON.")
                                            st.text(plot_json_str)
                                        st.markdown(part.split("}", 1)[1], unsafe_allow_html=True)
                                    else:
                                        st.markdown(part, unsafe_allow_html=True)
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

    st.markdown('</div>', unsafe_allow_html=True)

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
    """Display the global footer with warning message."""
    st.markdown("""
    <div class="custom-footer">
        <p>Powered by Gemini | MultiAgentAI21 can make mistakes. Always verify important information.</p>
    </div>
    """, unsafe_allow_html=True)

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

def debug_firestore_structure():
    """Debug function to check Firestore structure"""
    if not is_authenticated():
        st.error("Please login first")
        return
        
    user_info = get_current_user()
    user_uid = user_info.get("uid")
    
    st.write("### Firestore Debug Info")
    st.write(f"User UID: {user_uid}")
    st.write(f"Project ID: multiagentai21-9a8fc")
    st.write(f"Database: multiagentaifirestoredatabase")
    
    try:
        # Check if user document exists
        user_doc = db.collection("users").document(user_uid).get()
        st.write(f"User document exists: {user_doc.exists}")
        
        # Check chat histories collection
        st.write(f"Chat collection path: users/{user_uid}/{CHAT_HISTORY_COLLECTION_NAME}")
        
        # List all chats
        chats = db.collection("users").document(user_uid).collection(CHAT_HISTORY_COLLECTION_NAME).stream()
        chat_list = list(chats)
        st.write(f"Number of chats found: {len(chat_list)}")
        
        # Show first few chats
        for i, chat in enumerate(chat_list[:3]):
            st.write(f"\nChat {i+1} ID: {chat.id}")
            chat_data = chat.to_dict()
            st.write(f"Keys: {list(chat_data.keys())}")
            if "messages" in chat_data:
                st.write(f"Message count: {len(chat_data['messages'])}")
                
    except Exception as e:
        st.error(f"Debug error: {e}")
        logger.error(f"Firestore debug error: {e}", exc_info=True)

# Main application logic
@login_required
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
                return

        # Create sidebar navigation
        logger.info("Setting up navigation...")
        st.sidebar.title("Navigation")
        
        # Initialize page in session state if not present
        if "page" not in st.session_state:
            st.session_state.page = "🤖 Agent Chat"
        
        # Display user profile and chat history in sidebar
        user_profile_sidebar()
        display_chat_history_sidebar()

        page = st.sidebar.radio(
            "Select a page",
            ["🤖 Agent Chat", "📊 Data Analysis", "📈 Analytics Dashboard", "📚 Examples"],
            key="navigation_radio",
            index=["🤖 Agent Chat", "📊 Data Analysis", "📈 Analytics Dashboard", "📚 Examples"].index(st.session_state.page)
        )
        
        # Update session state page
        st.session_state.page = page

        # Debug button (optional - remove in production)
        if st.sidebar.button("🐛 Debug Firestore", key="debug_firestore_btn"):
            debug_firestore_structure()

        logger.info(f"Selected page: {page}")

        # Handle pending message from examples
        if hasattr(st.session_state, 'pending_message') and st.session_state.pending_message:
            if page == "🤖 Agent Chat":
                # Process the pending message
                pending_msg = st.session_state.pending_message
                st.session_state.pending_message = None
                process_and_display_user_message(pending_msg)

        if page == "🤖 Agent Chat":
            display_chat_interface()
        elif page == "📊 Data Analysis":
            display_data_analysis_section()
        elif page == "📈 Analytics Dashboard":
            display_analytics_dashboard()
        elif page == "📚 Examples":
            show_agent_examples()
        
        logger.info("Main application completed successfully")

        # Clean up temporary files when the app is closed
        atexit.register(cleanup_analysis_files)
        atexit.register(cleanup_temp_files)

        # Display the global footer
        display_footer()

    except Exception as e:
        logger.error(f"Error in main application: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check the logs for more details")

if __name__ == "__main__":
    try:
        logger.info("Entering main execution block.")
        # Check authentication state and run main app or login page.
        if not is_authenticated():
            login_page()
        else:
            main_app()
    except Exception as e:
        logger.critical(f"Critical error in main application execution: {e}", exc_info=True)
        st.error(f"A critical error prevented the application from running: {str(e)}")