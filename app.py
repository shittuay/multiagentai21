import json
import logging
import os
import sys
import tempfile
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional
import atexit

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import authentication module
from src.auth import (
    initialize_firebase,
    login_required,
    login_page,
    logout,
    is_authenticated,
    get_current_user
)

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase
try:
    initialize_firebase()
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
logger.info(f"Project root: {project_root}")
logger.info(f"Python path: {sys.path}")

# --- BEGIN Google Cloud Credentials Setup ---
_GCLOUD_TEMP_KEY_FILE = None

def _setup_gcloud_credentials_from_json() -> Optional[str]:
    """Reads GCLOUD_APPLICATION_CREDENTIALS_JSON and sets GOOGLE_APPLICATION_CREDENTIALS."""
    global _GCLOUD_TEMP_KEY_FILE
    credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

    if credentials_json:
        try:
            logger.info("Found GOOGLE_APPLICATION_CREDENTIALS_JSON. Writing to temporary file.")
            # Create a temporary file to store the credentials
            _GCLOUD_TEMP_KEY_FILE = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8')
            _GCLOUD_TEMP_KEY_FILE.write(credentials_json)
            _GCLOUD_TEMP_KEY_FILE.close() # Close to ensure content is written to disk

            # Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _GCLOUD_TEMP_KEY_FILE.name
            logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set to: {_GCLOUD_TEMP_KEY_FILE.name}")
            return _GCLOUD_TEMP_KEY_FILE.name
        except Exception as e:
            logger.error(f"Error setting up GCloud credentials from JSON: {e}", exc_info=True)
    else:
        logger.info("GOOGLE_APPLICATION_CREDENTIALS_JSON not found. Relying on default credential discovery.")
    return None

def _cleanup_temp_key_file():
    """Clean up the temporary key file."""
    global _GCLOUD_TEMP_KEY_FILE
    if _GCLOUD_TEMP_KEY_FILE and os.path.exists(_GCLOUD_TEMP_KEY_FILE.name):
        os.remove(_GCLOUD_TEMP_KEY_FILE.name)
        logger.info(f"Cleaned up temporary key file: {_GCLOUD_TEMP_KEY_FILE.name}")
        _GCLOUD_TEMP_KEY_FILE = None

# Register cleanup function to run on app exit
atexit.register(_cleanup_temp_key_file)

# Call the setup function at the very beginning of the application
_setup_gcloud_credentials_from_json()
# --- END Google Cloud Credentials Setup ---


# Load environment variables (removed load_dotenv() as it's not needed in Cloud Run)
logger.info("Environment variables should be set by deployment environment")

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
        margin-bottom: 2rem;
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


def check_environment() -> list:
    """Checks if essential environment variables are set."""
    issues = []
    if not os.getenv("GOOGLE_API_KEY"):
        issues.append("GOOGLE_API_KEY is not set")
    # Check for GOOGLE_CLOUD_PROJECT (used by Google Cloud libraries)
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        issues.append("GOOGLE_CLOUD_PROJECT is not set")
    # Check for GOOGLE_APPLICATION_CREDENTIALS_JSON (used by FirestoreClient)
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        issues.append("GOOGLE_APPLICATION_CREDENTIALS_JSON is not set")
    return issues


# Use st.cache_resource to create and cache the MultiAgentCodingAI instance
# @st.cache_resource(ttl=3600, max_entries=1)  # Temporarily disabled for testing
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
    if not st.session_state.chat_history:
        st.info("💬 Start a conversation by selecting an agent and typing a message!")
        return

    # Debug information (only show in development)
    if st.checkbox("🔍 Show Debug Info", key="debug_chat"):
        st.write(f"**Debug Info:**")
        st.write(f"- Chat ID: {st.session_state.current_chat_id}")
        st.write(f"- Messages loaded: {len(st.session_state.chat_history)}")
        st.write(f"- Agent type: {st.session_state.selected_agent}")
        st.write(f"- Agent locked: {st.session_state.agent_locked}")
        st.write("**Message structure:**")
        for i, msg in enumerate(st.session_state.chat_history):
            st.write(f"  {i+1}. {msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}...")

    # Display chat messages
    st.subheader(f"💬 Conversation ({len(st.session_state.chat_history)} messages)")
    
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
    """Display the main chat interface."""
    # Initialize session state if needed
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "agent_locked" not in st.session_state:
        st.session_state.agent_locked = False
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = None

    # Only load chat history if we don't already have it loaded
    # This prevents overriding chat history when loading from sidebar
    if not st.session_state.chat_history:
        loaded_history = load_chat_history(st.session_state.current_chat_id)
        if loaded_history:
            st.session_state.chat_history = loaded_history
            logger.info(f"Loaded chat history for {st.session_state.current_chat_id}: {len(loaded_history)} messages")

    # Display chat history in sidebar
    display_chat_history_sidebar()

    # Main chat area
    st.title("MultiAgentAI21 Chat")

    # Display current chat ID and message count
    message_count = len(st.session_state.chat_history)
    st.caption(f"Chat ID: {st.session_state.current_chat_id} | Messages: {message_count}")

    # Agent selection
    display_agent_selection()

    # Display chat messages
    display_chat_messages()

    # Chat input
    logger.info("DEBUG: Checking for chat input...")
    if user_input := st.chat_input("Type your message here..."):
        logger.info(f"DEBUG: Chat input received: {user_input[:50]}...") # Log the received input
        process_and_display_user_message(user_input)
    else:
        logger.info("DEBUG: No chat input received.")


def show_agent_examples():
    """Show examples based on selected agent"""
    if not st.session_state.selected_agent:
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


def display_analytics_dashboard():
    """Display enhanced analytics dashboard"""
    if not st.session_state.chat_history:
        st.info("📊 No analytics data available yet. Start chatting to see metrics!")
        return

    st.markdown('<div class="metric-container">', unsafe_allow_html=True)

    # Calculate metrics
    total_requests = len(st.session_state.chat_history)
    avg_response_time = sum(chat.get("execution_time", 0) for chat in st.session_state.chat_history) / total_requests
    success_rate = (sum(1 for chat in st.session_state.chat_history if chat.get("success", True)) / total_requests) * 100

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Requests", total_requests, delta=None)

    with col2:
        st.metric("Avg Response Time", f"{avg_response_time:.2f}s", delta=None)

    with col3:
        st.metric("Success Rate", f"{success_rate:.1f}%", delta=None)

    st.markdown("</div>", unsafe_allow_html=True)

    # Agent usage chart
    if len(st.session_state.chat_history) > 1:
        agent_usage = {}
        for chat in st.session_state.chat_history:
            agent_type = chat.get("agent_type", "unknown")
            agent_usage[agent_type] = agent_usage.get(agent_type, 0) + 1

        # Create pie chart with better colors for white background
        fig = px.pie(
            values=list(agent_usage.values()),
            names=list(agent_usage.keys()),
            title="Agent Usage Distribution",
            color_discrete_sequence=["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_color="#1a202c",
            title_font_color="#1a202c",
        )
        st.plotly_chart(fig, use_container_width=True)


def process_user_request(user_input: str):
    """Process user request with the multi-agent system"""
    if not st.session_state.agent:
        st.error("Agent system not initialized!")
        return {"content": "Agent system not initialized!", "data": None}

    if not st.session_state.selected_agent:
        st.error("Please select an agent first!")
        return {"content": "Please select an agent first!", "data": None}

    try:
        with st.spinner("🤖 Processing your request..."):
            # Debug logging
            logger.info(f"Selected agent type: {st.session_state.selected_agent}")
            logger.info(f"Available agent types: {[t.value for t in AgentType]}")

            # Lock the agent selection after first message
            st.session_state.agent_locked = True

            # Prepare context from recent conversations
            context = {}
            if len(st.session_state.chat_history) > 0:
                context["previous_requests"] = [
                    msg["content"] for msg in st.session_state.chat_history[-3:] if msg["role"] == "user"
                ]

            # Get the agent type enum value
            try:
                # Convert the stored string value to AgentType enum
                agent_type = AgentType(st.session_state.selected_agent)
                logger.info(f"Using agent type: {agent_type.value}")
            except ValueError as e:
                logger.error(f"Invalid agent type: {st.session_state.selected_agent}")
                st.error(f"Invalid agent type selected. Please select a valid agent.")
                return {
                    "content": "Invalid agent type selected. Please select a valid agent.",
                    "data": None,
                }

            # Route request to selected agent
            start_time = time.time()
            response = st.session_state.agent.route_request(user_input, agent_type, context)
            execution_time = time.time() - start_time

            # Create response dictionary with proper content handling
            response_dict = {
                "content": response.content if response and response.content else "No response received",
                "data": response.data if response and hasattr(response, "data") else None,
            }

            # Show success message
            if response and getattr(response, "success", False):
                st.success(f"✅ Response from {agent_type.value.title()} Agent")
                # Display the response content immediately
                st.write(response_dict["content"])
            else:
                error_msg = getattr(response, "error_message", "Unknown error occurred")
                st.error(f"❌ Error: {error_msg}")
                response_dict["content"] = f"Error: {error_msg}"

            return response_dict

    except Exception as e:
        error_msg = f"Failed to process request: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(f"❌ {error_msg}")
        return {"content": error_msg, "data": None}


def display_data_analysis_section():
    """Display the data analysis section of the app"""
    st.markdown(
        """
    <div class='main-header'>
        <h1>📊 Data Analysis Dashboard</h1>
        <p>Upload your data files for comprehensive analysis and insights</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # File upload section
    uploaded_file = st.file_uploader(
        "Upload your data file (CSV format)",
        type=["csv"],
        help="Upload a CSV file for analysis",
    )

    if uploaded_file is not None:
        try:
            # Save the uploaded file temporarily
            temp_dir = os.path.join(os.getcwd(), "temp_analysis")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, uploaded_file.name)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Initialize analyzer
            analyzer = DataAnalyzer(temp_dir=temp_dir)

            # Perform analysis
            with st.spinner("Analyzing your data..."):
                results = analyzer.analyze_file(file_path)

                if "error" in results:
                    st.error(f"Analysis failed: {results['error']}")
                    return

                # Display summary
                st.markdown("### 📈 Analysis Summary")
                if "summary" in results:
                    summary = results["summary"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Records", summary["total_records"])
                    with col2:
                        st.metric("Columns Analyzed", len(summary["columns"]))
                    with col3:
                        missing = sum(summary["missing_values"].values())
                        st.metric("Missing Values", missing)

                # Display recommendations
                if "recommendations" in results and results["recommendations"]:
                    st.markdown("### 💡 Recommendations")
                    for rec in results["recommendations"]:
                        st.info(rec)

                # Display department analysis if available
                if "department_analysis" in results:
                    st.markdown("### 👥 Department Analysis")
                    dept_analysis = results["department_analysis"]

                    if "salary" in dept_analysis:
                        st.markdown("#### Salary Distribution by Department")
                        salary_data = dept_analysis["salary"]

                        # Create salary box plot
                        fig = go.Figure()
                        for dept, stats in salary_data["mean"].items():
                            fig.add_trace(
                                go.Box(
                                    y=[stats],
                                    name=dept,
                                    boxpoints="all",
                                    jitter=0.3,
                                    pointpos=-1.8,
                                )
                            )
                        fig.update_layout(
                            title="Salary Distribution by Department",
                            yaxis_title="Salary",
                            showlegend=True,
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    if "performance_score" in dept_analysis:
                        st.markdown("#### Performance Scores by Department")
                        perf_data = dept_analysis["performance_score"]

                        # Create performance heatmap
                        depts = list(perf_data["mean"].keys())
                        metrics = ["mean", "median", "min", "max"]
                        values = [[perf_data[m][d] for d in depts] for m in metrics]

                        fig = go.Figure(
                            data=go.Heatmap(
                                z=values,
                                x=depts,
                                y=metrics,
                                colorscale="RdYlGn",
                                text=[[f"{v:.2f}" for v in row] for row in values],
                                texttemplate="%{text}",
                                textfont={"size": 14},
                            )
                        )
                        fig.update_layout(
                            title="Performance Metrics by Department",
                            xaxis_title="Department",
                            yaxis_title="Metric",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                # Display education analysis if available
                if "education_analysis" in results:
                    st.markdown("### 🎓 Education Analysis")
                    edu_analysis = results["education_analysis"]

                    if "salary" in edu_analysis:
                        st.markdown("#### Salary by Education Level")
                        edu_data = pd.DataFrame(
                            {
                                "Education": list(edu_analysis["salary"]["mean"].keys()),
                                "Mean Salary": list(edu_analysis["salary"]["mean"].values()),
                                "Median Salary": list(edu_analysis["salary"]["median"].values()),
                            }
                        )

                        fig = px.bar(
                            edu_data,
                            x="Education",
                            y=["Mean Salary", "Median Salary"],
                            barmode="group",
                            title="Salary Distribution by Education Level",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                # Display interactive visualizations
                if "visualizations" in results:
                    st.markdown("### 📊 Interactive Visualizations")
                    for viz_name, viz_path in results["visualizations"].items():
                        if viz_path.endswith(".html"):
                            st.markdown(f"#### {viz_name.replace('_', ' ').title()}")
                            with open(viz_path, "r") as f:
                                html_content = f.read()
                            st.components.v1.html(html_content, height=600)

                # Save results
                results_file = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(results_file, "w") as f:
                    json.dump(results, f, indent=2)
                st.download_button(
                    label="Download Analysis Results",
                    data=json.dumps(results, indent=2),
                    file_name=results_file,
                    mime="application/json",
                )

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
        finally:
            # Cleanup
            try:
                analyzer.cleanup()
            except:
                pass


def main():
    """Main application entry point"""
    try:
        logger.info("Starting main application...")

        # Check authentication
        if not is_authenticated():
            login_page()
            return

        # Display user info in sidebar
        user = get_current_user()
        with st.sidebar:
            st.write(f"Welcome, {user['email']}")
            if st.button("Logout"):
                logout()
                return

        # Check environment
        logger.info("Checking environment...")
        issues = check_environment()
        if issues:
            logger.error(f"Environment issues found: {issues}")
            st.error("Environment issues detected:")
            for issue in issues:
                st.error(f"- {issue}")
            st.stop()

        # Initialize agent
        logger.info("Initializing agent...")
        st.session_state.agent = get_agent_system()

        # Check if agent initialization was successful
        if st.session_state.agent is None:
            st.error("❌ Failed to initialize the multi-agent system. Please check the logs for details.")
            logger.error("Multi-agent system is None after initialization.")
            # Prevent further execution that requires the agent
            return # Stop main function execution if agent is not initialized

        # Display header
        logger.info("Displaying header...")
        display_enhanced_header()

        # Create sidebar navigation
        logger.info("Setting up navigation...")
        st.sidebar.title("Navigation")
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
            show_agent_examples()

        logger.info("Main application completed successfully")

    except Exception as e:
        logger.error(f"Error in main application: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check the logs for more details")


if __name__ == "__main__":
    try:
        logger.info("Starting application...")
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        st.error("A fatal error occurred. Please check the logs for details.")

# Footer
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #6b7280;'>
    <p>🚀 Powered by MultiAgentAI21 | CopyRight @2025</p>
</div>
""",
    unsafe_allow_html=True,
) 