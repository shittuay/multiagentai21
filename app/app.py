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
import time # Import time for timestamping


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Application starting...")

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.sys.path.insert(0, str(project_root))

logger.info(f"Project root (app.py detected as): {project_root}")
logger.info(f"Python path (sys.path) before import: {sys.path}")

# --- START ADDED DEBUGGING FOR MODULE NOT FOUND ERROR ---
# Explicitly check for the existence of src/auth_manager.py and related paths
logger.info("--- START DEBUGGING PATHS & FILES ---")

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

logger.info("--- END DEBUGGING PATHS & FILES ---")
# --- END ADDED DEBUGGING ---


# Import authentication module
try:
    from src.auth_manager import (
        initialize_firebase,
        login_required,
        login_page,
        logout,
        is_authenticated,
        get_current_user,
        setup_google_application_credentials # Import this to call it early
    )
    logger.info("Successfully imported src.auth_manager.")
except ModuleNotFoundError as e:
    logger.critical(f"ModuleNotFoundError: {e} - Cannot find 'src.auth_manager'. This indicates a pathing issue.", exc_info=True)
    st.error(f"Application failed to start due to a missing module. Please contact support. Error: {e}")
    st.stop() # Stop Streamlit execution if essential module is missing
except Exception as e:
    logger.critical(f"An unexpected error occurred during src.auth_manager import: {e}", exc_info=True)
    st.error(f"Application failed to start due to an unexpected import error. Error: {e}")
    st.stop()


# Initialize Firebase (this call should be after imports and inside app.py)
try:
    initialize_firebase()
    logger.info("Firebase initialization completed successfully in app.py.")
except Exception as e:
    logger.critical(f"Failed to initialize Firebase in app.py: {e}", exc_info=True)
    st.error(f"An error occurred during Firebase initialization: {str(e)}")
    st.stop() # Stop the app if Firebase init fails

# Call setup_google_application_credentials early to ensure GOOGLE_APPLICATION_CREDENTIALS is set
# This is called *after* initialize_firebase in auth_manager.py is executed,
# so the `os.getenv("GOOGLE_APPLICATION_CREDENTIALS")` check will pass.
setup_google_application_credentials()

# --- NEW: Environment check function to consolidate warnings ---
def check_environment():
    issues = []
    
    # Check for Firebase API Key (client-side config)
    if not os.getenv("FIREBASE_API_KEY"):
        issues.append("FIREBASE_API_KEY is not set")
    if not os.getenv("FIREBASE_AUTH_DOMAIN"):
        issues.append("FIREBASE_AUTH_DOMAIN is not set")
    if not os.getenv("FIREBASE_PROJECT_ID"):
        issues.append("FIREBASE_PROJECT_ID is not set")
    if not os.getenv("FIREBASE_STORAGE_BUCKET"):
        issues.append("FIREBASE_STORAGE_BUCKET is not set")
    if not os.getenv("FIREBASE_MESSAGING_SENDER_ID"):
        issues.append("FIREBASE_MESSAGING_SENDER_ID is not set")
    if not os.getenv("FIREBASE_APP_ID"):
        issues.append("FIREBASE_APP_ID is not set")

    # Check for Google API Key (for Gemini etc.)
    if not os.getenv("GOOGLE_API_KEY"):
        issues.append("GOOGLE_API_KEY is not set")
    
    # Check for Google Cloud Project ID
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        issues.append("GOOGLE_CLOUD_PROJECT is not set")

    # IMPORTANT: Check GOOGLE_APPLICATION_CREDENTIALS, which is set by auth_manager.py
    # This is the path to the service account key file.
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        issues.append("GOOGLE_APPLICATION_CREDENTIALS is not set (expected a file path to service account key)")
    
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
# --- END NEW ENVIRONMENT CHECK ---


# Load environment variables (removed _setup_gcloud_credentials_from_json() and _cleanup_temp_key_file() as auth_manager.py now handles this)
logger.info("Environment variables should be set by deployment environment or handled by auth_manager.")

try:
    logger.info("Attempting to import modules...")
    from src.agent_core import AgentType, MultiAgentCodingAI
    from src.data_analysis import DataAnalyzer

    logger.info("Successfully imported modules")
except ImportError as e:
    logger.error(f"Import error: {e}", exc_info=True)
    st.error(f"❌ Failed to import required modules: {e}")
    st.error("Make sure all dependencies are installed")
    st.stop()

# Page configuration
try:
    logger.info("Setting up page configuration...")
    st.set_page_config(
        page_title="MultiAgentAI21 - Advanced AI Assistant",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    logger.info("Page configuration set successfully")
except Exception as e:
    logger.error(f"Error in page configuration: {e}", exc_info=True)
    st.error(f"Error setting up page: {e}")
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

    /* Primary button variant */
    .stButton[data-baseweb="button"][kind="primary"] > button {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);
    }

    .stButton[data-baseweb="button"][kind="primary"] > button:hover {
        background: linear-gradient(135deg, #16a34a, #15803d);
        box-shadow: 0 8px 25px rgba(34, 197, 94, 0.4);
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

    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
    }

    /* Main title styling */
    h1 {
        color: #1a202c !important;
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }

    /* Subtitle styling */
    .main-header p {
        color: #4a5568 !important;
        font-size: 1.2rem !important;
        margin: 0 !important;
    }

    /* Streamlit native elements */
    .stMarkdown {
        color: #1a202c;
    }

    /* Info, success, error boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.95);
        color: #1a202c;
        border-radius: 12px;
    }

    /* Metric styling */
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

# Define chat history storage
CHAT_HISTORY_DIR = os.path.join(project_root, "chat_history")
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)


def save_chat_history(chat_id: str, messages: list):
    """Save chat history to a JSON file."""
    try:
        # Ensure chat_history directory exists
        CHAT_HISTORY_DIR = os.path.join(project_root, "chat_history")
        os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
        
        chat_file = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
        
        # Prepare chat data with metadata
        chat_data = {
            "chat_id": chat_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
        
        # Save to file
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Chat history saved: {chat_file} ({len(messages)} messages)")
        
    except Exception as e:
        logger.error(f"Error saving chat history: {e}", exc_info=True)
        st.error(f"Failed to save chat history: {str(e)}")


def load_chat_history(chat_id: str) -> list:
    """Load chat history from a JSON file."""
    try:
        CHAT_HISTORY_DIR = os.path.join(project_root, "chat_history")
        chat_file = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
        
        if not os.path.exists(chat_file):
            logger.warning(f"Chat history file not found: {chat_file}")
            return []
        
        with open(chat_file, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
        
        # Extract messages from the chat data
        messages = chat_data.get("messages", [])
        logger.info(f"Chat history loaded: {chat_file} ({len(messages)} messages)")
        
        return messages
        
    except Exception as e:
        logger.error(f"Error loading chat history: {e}", exc_info=True)
        st.error(f"Failed to load chat history: {str(e)}")
        return []


def get_available_chats() -> list:
    """Get list of available chat sessions."""
    try:
        CHAT_HISTORY_DIR = os.path.join(project_root, "chat_history")
        
        if not os.path.exists(CHAT_HISTORY_DIR):
            return []
        
        chats = []
        for file in os.listdir(CHAT_HISTORY_DIR):
            if file.endswith('.json'):
                chat_file = os.path.join(CHAT_HISTORY_DIR, file)
                try:
                    with open(chat_file, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                    
                    chat_id = chat_data.get("chat_id", file.replace('.json', ''))
                    created_at = chat_data.get("created_at", datetime.now().isoformat())
                    last_updated = chat_data.get("last_updated", created_at)
                    messages = chat_data.get("messages", [])
                    
                    # Get preview from first user message
                    preview = "New Chat"
                    for message in messages:
                        if message.get("role") == "user":
                            preview = message.get("content", "New Chat")[:50]
                            break
                    
                    chats.append({
                        "id": chat_id,
                        "preview": preview,
                        "created_at": created_at,
                        "last_updated": last_updated,
                        "message_count": len(messages)
                    })
                    
                except Exception as e:
                    logger.error(f"Error reading chat file {file}: {e}")
                    st.sidebar.error(f"Error loading chat: {file} - {str(e)}")
                    continue
        
        # Sort by last updated (most recent first)
        chats.sort(key=lambda x: x["last_updated"], reverse=True)
        
        return chats
        
    except Exception as e:
        logger.error(f"Error getting available chats: {e}", exc_info=True)
        return []


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
    st.session_state.available_chats = get_available_chats()
if "last_analysis_results" not in st.session_state:
    st.session_state.last_analysis_results = None
if "analysis_temp_files" not in st.session_state:
    st.session_state.analysis_temp_files = []


# Use st.cache_resource to create and cache the MultiAgentCodingAI instance
# @st.cache_resource(ttl=3600, max_entries=1)   # Temporarily disabled for testing
def get_agent_system():
    """Create and return the MultiAgentCodingAI instance (cached resource)"""
    try:
        logger.info("Starting MultiAgentCodingAI initialization...")
        
        # Check environment variables
        logger.info("Checking environment variables...")
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            error_msg = "GOOGLE_API_KEY environment variable is not set"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("GOOGLE_API_KEY found")
        
        # Create the agent instance
        logger.info("Creating MultiAgentCodingAI instance...")
        try:
            agent_instance = MultiAgentCodingAI()
            logger.info("MultiAgentCodingAI instance created successfully")
            return agent_instance
        except Exception as e:
            error_msg = f"Error creating MultiAgentCodingAI instance: {str(e)}"
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

    # Cache clearing button for development
    if st.sidebar.button("🔄 Clear Cache & Reload", key="clear_cache_btn"):
        st.cache_resource.clear()
        st.session_state.agent = None
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

    # Display available chats
    available_chats = get_available_chats()
    if not available_chats:
        st.sidebar.info("📝 No previous chats available.")
        return

    st.sidebar.subheader("📚 Previous Chats")
    for chat_info in available_chats:
        chat_id = chat_info['id']
        preview = chat_info['preview']
        created_at = datetime.fromisoformat(chat_info['created_at']).strftime("%Y-%m-%d %H:%M")
        message_count = chat_info['message_count']
        
        # Create a more compact button layout
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button(f"📄 {preview[:30]}...", key=f"chat_{chat_id}"):
                # Load the chat history
                loaded_history = load_chat_history(chat_id)
                if loaded_history:
                    st.session_state.chat_history = loaded_history
                    st.session_state.current_chat_id = chat_id
                    
                    # Try to restore the agent type from the last assistant message
                    agent_type = None
                    for message in reversed(loaded_history):
                        if message.get("role") == "assistant" and "agent_type" in message:
                            agent_type = message["agent_type"]
                            break
                    
                    if agent_type:
                        st.session_state.selected_agent = agent_type
                        st.session_state.agent_locked = True
                        logger.info(f"Restored agent type: {agent_type}")
                    
                    st.success(f"✅ Loaded chat: {preview[:30]}... ({message_count} messages)")
                    logger.info(f"Loaded chat {chat_id} with {len(loaded_history)} messages")
                else:
                    st.error(f"❌ Failed to load chat: {preview[:30]}...")
                st.rerun()
        with col2:
            st.caption(f"{created_at}\n{message_count} msgs")


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
            
            # Save chat history to file
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

    # Save updated chat history
    save_chat_history(st.session_state.current_chat_id, st.session_state.chat_history)


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
            "Help with billing questions",
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
            process_user_request(example)


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
            
            # Save the uploaded file temporarily
            temp_dir = os.path.join(project_root, "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.analysis_temp_files.append(temp_file_path) # Track for cleanup

            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            logger.info(f"Uploaded file saved to: {temp_file_path}")

            # Instantiate DataAnalyzer
            data_analyzer = DataAnalyzer()

            # Perform analysis
            with st.spinner("Analyzing data... This may take a moment."):
                results = data_analyzer.analyze_data(temp_file_path, selected_analysis_types)
                st.session_state.last_analysis_results = results # Store results for display

            if st.session_state.last_analysis_results:
                st.subheader("Analysis Results:")
                for analysis_type, content in st.session_state.last_analysis_results.items():
                    if content:
                        st.markdown(f"**{analysis_type.replace('_', ' ').title()}**")
                        if analysis_type == "visualizations" and isinstance(content, dict):
                            # Handle plotly figures from data_analysis.py
                            for plot_name, fig_json in content.items():
                                try:
                                    fig = go.Figure(json.loads(fig_json))
                                    st.plotly_chart(fig, use_container_width=True)
                                except json.JSONDecodeError:
                                    st.warning(f"Could not load plot '{plot_name}'. Invalid JSON.")
                                    st.json(fig_json) # Show raw JSON for debugging
                        else:
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
    st.markdown("<p style='text-align: center; font-size: small;'>Powered by MultiAgentAI21</p>", unsafe_allow_html=True)


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


# Main application logic
@login_required # Ensure this decorator works after import
def main_app():
    try:
        # Display header
        logger.info("Displaying header...")
        display_enhanced_header()

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
        if not is_authenticated():
            login_page()
        else:
            main_app()
    except Exception as e:
        logger.critical(f"Critical error in main application execution: {e}", exc_info=True)
        st.error(f"A critical error prevented the application from running: {str(e)}")

