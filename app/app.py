#!/usr/bin/env python3
"""
MultiAgentAI21 - Complete Streamlit Application
Advanced Multi-Agent AI System with Enhanced Capabilities
"""

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
import uuid
import firebase_admin.firestore as firestore
from dotenv import load_dotenv

# Load environment variables from .env file EARLY
load_dotenv()

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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger.info(f"Project root: {project_root}")
logger.info("Application starting...")

# Check environment variables
def check_environment():
    """Check essential environment variables"""
    issues = []

    # Check for OpenRouter API key (required - Gemini is disabled)
    # Check both st.secrets (Streamlit Cloud) and os.getenv (local)
    openrouter_key = None
    try:
        openrouter_key = st.secrets.get("OPENROUTER_API_KEY")
    except (AttributeError, FileNotFoundError):
        pass

    if not openrouter_key:
        openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not openrouter_key:
        issues.append("OPENROUTER_API_KEY is not set (required for AI features)")

    return issues

# Display environment warnings
environment_issues = check_environment()
if environment_issues:
    st.warning("⚠️ Environment Configuration Issues:")
    for issue in environment_issues:
        st.warning(f"• {issue}")
    st.info("💡 Please set your OPENROUTER_API_KEY environment variable in Streamlit Cloud secrets")
    logger.warning(f"Environment issues: {environment_issues}")

# Import authentication module
try:
    from src.auth_manager import (
        login_page,
        logout,
        is_authenticated,
        get_user_email,
        get_user_name,
        get_user_uid,
        require_auth
    )
    logger.info("Successfully imported auth_manager")
    
except ModuleNotFoundError as e:
    logger.critical(f"ModuleNotFoundError: {e}")
    st.error(f"❌ Cannot find authentication module: {e}")
    st.error("Please ensure src/auth_manager.py exists and is properly configured")
    st.stop()
except Exception as e:
    logger.critical(f"Authentication setup error: {e}", exc_info=True)
    st.error(f"❌ Authentication setup failed: {e}")
    st.stop()

# Simple chat history storage (in-memory for now)
def get_chat_storage():
    """Get simple chat storage"""
    return {}

# Initialize chat storage
chat_storage = get_chat_storage()

# Import agent modules
try:
    from src.agent_core import AgentType, MultiAgentCodingAI
    from src.data_analysis import DataAnalyzer
    logger.info("Successfully imported agent modules")
except ImportError as e:
    logger.error(f"Agent import error: {e}")
    st.error(f"❌ Failed to import agent modules: {e}")
    st.error("Please ensure src/agent_core.py and src/data_analysis.py exist")
    st.stop()

# Initialize agent system
@st.cache_resource
def get_agent_system():
    """Create and return the MultiAgentAI21 instance (cached resource)"""
    try:
        logger.info("Initializing MultiAgentAI21...")

        # Check API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("OPENROUTER_API_KEY not set - AI features will be limited")
            # Continue without API key for basic functionality

        # Create agent instance
        agent_instance = MultiAgentCodingAI()
        logger.info("MultiAgentAI21 initialized successfully")
        return agent_instance

    except Exception as e:
        logger.error(f"Agent system initialization error: {e}")
        st.warning(f"⚠️ Agent system initialization warning: {e}")
        st.info("Some features may be limited without proper configuration")
        return None

# Claude AI Inspired Professional UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* Reset and Base Styles */
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    /* Claude AI Inspired Global App Styling */
    .stApp {
        background: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1a1a1a;
        min-height: 100vh;
    }

    /* Claude AI Header */
    .claude-header {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-bottom: 1px solid #e2e8f0;
        padding: 1.5rem 2rem;
        text-align: center;
        position: relative;
    }

    .claude-logo {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin: 0 auto 1rem auto;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    .claude-header h1 {
        font-size: 2.25rem;
        font-weight: 800;
        margin: 0 0 0.5rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.025em;
    }

    .claude-header p {
        color: #64748b;
        font-size: 1.125rem;
        margin: 0 0 1.5rem 0;
        font-weight: 400;
        line-height: 1.6;
    }

    .claude-badges {
        display: flex;
        justify-content: center;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .claude-badge {
        background: rgba(102, 126, 234, 0.1);
        color: #667eea;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }

    /* Claude AI Cards */
    .claude-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }

    .claude-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-1px);
    }

    /* Claude AI Chat Interface */
    .claude-chat-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        overflow: hidden;
        margin-top: 1rem;
        display: flex;
        flex-direction: column;
        min-height: 300px;
        max-height: 400px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .claude-chat-header {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        color: #1a1a1a;
        padding: 1.25rem 2rem;
        font-weight: 600;
        font-size: 1.125rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border-bottom: 1px solid #e2e8f0;
    }

    .claude-chat-messages {
        flex: 1;
        padding: 0.5rem;
        overflow-y: auto;
        background: #fafafa;
        max-height: 200px;
    }

    .claude-input-area {
        background: #ffffff;
        border-top: 1px solid #e2e8f0;
        padding: 0.75rem 1rem;
    }

    /* Claude AI Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 0.875rem 2rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Claude AI Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #1a1a1a !important;
        font-weight: 600;
        margin: 0 0 1rem 0 !important;
    }

    h1 {
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    h2 {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }

    h3 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
    }

    /* Claude AI Sidebar */
    .css-1d391kg {
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* Claude AI Status Badge */
    .claude-status {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
        margin: 1rem 0;
    }

    /* Claude AI Input Fields */
    .stTextArea > div > div > textarea {
        background: #ffffff !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px;
        padding: 1rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: #1a1a1a !important;
        transition: all 0.2s ease;
        resize: none;
    }

    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none;
    }

    .stTextArea > div > div > textarea::placeholder {
        color: #94a3b8 !important;
    }

    /* Claude AI File Upload */
    .stFileUploader > div {
        background: #ffffff !important;
        border: 2px dashed #cbd5e1 !important;
        border-radius: 12px;
        transition: all 0.2s ease;
    }

    .stFileUploader > div:hover {
        border-color: #667eea !important;
        background: rgba(102, 126, 234, 0.02) !important;
    }

    /* Claude AI Chat Messages */
    .claude-message {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .claude-message.user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 2rem;
        border: none;
    }

    .claude-message.assistant {
        background: #ffffff;
        margin-right: 2rem;
        border-left: 4px solid #667eea;
    }

    /* Claude AI Radio Buttons */
    .stRadio > div > label {
        color: #1a1a1a !important;
        font-weight: 500;
    }

    /* Claude AI Expander */
    .streamlit-expanderHeader {
        background: #f8fafc !important;
        color: #1a1a1a !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }

    /* Claude AI Agent Selection Cards */
    .claude-agent-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .claude-agent-card:hover {
        background: rgba(102, 126, 234, 0.02);
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }

    .claude-agent-icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
    }

    .claude-agent-title {
        color: #667eea;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 1.125rem;
    }

    .claude-agent-description {
        color: #64748b;
        font-size: 0.875rem;
        line-height: 1.5;
    }

    /* Claude AI Success/Info Messages */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        color: #059669 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    .stInfo {
        background: rgba(102, 126, 234, 0.1) !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        color: #667eea !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    .stWarning {
        background: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid rgba(245, 158, 11, 0.2) !important;
        color: #d97706 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        color: #dc2626 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    /* Remove default Streamlit spacing */
    .block-container {
        padding: 1rem 2rem !important;
        max-width: 1200px !important;
    }

    /* Claude AI Sidebar Styling */
    .css-1d391kg .css-1d391kg {
        padding: 1rem !important;
        margin: 0 !important;
    }

    /* Claude AI Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }

    /* Claude AI Responsive Design */
    @media (max-width: 768px) {
        .claude-header {
            padding: 1rem;
        }
        
        .claude-header h1 {
            font-size: 1.75rem !important;
        }
        
        .claude-card {
            padding: 1.5rem;
        }
        
        .claude-badges {
            flex-direction: column;
            align-items: center;
        }
        
        .block-container {
            padding: 0.5rem 1rem !important;
        }
    }

    /* Claude AI Loading Animation */
    .claude-loading {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid #e2e8f0;
        border-radius: 50%;
        border-top-color: #667eea;
        animation: claude-spin 1s ease-in-out infinite;
    }

    @keyframes claude-spin {
        to { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        "agent": None,
        "chat_history": [],
        "selected_agent": None,
        "agent_locked": False,
        "current_chat_id": f"chat_{int(time.time())}",
        "available_chats": [],
        "last_analysis_results": None,
        "analysis_temp_files": [],
        "user_info": None,
        "page": "🤖 Agent Chat",
        "show_file_upload": False,
        "temp_files": []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Chat history management
CHAT_HISTORY_COLLECTION_NAME = "chat_histories"

# Initialize Firestore client for database operations
@st.cache_resource
def get_firestore_client():
    """Get Firestore client instance (cached resource)"""
    try:
        from src.api.firestore import FirestoreClient
        client = FirestoreClient()
        if client.initialized:
            logger.info("Firestore client initialized successfully")
        else:
            logger.warning("Firestore client not initialized - running in offline mode")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Firestore client: {e}")
        return None

def save_chat_history(chat_id: str, messages: list):
    """Save chat history to both session state and database"""
    try:
        # Save to session state (for immediate access)
        if "chat_histories" not in st.session_state:
            st.session_state.chat_histories = {}
        
        st.session_state.chat_histories[chat_id] = {
            "chat_id": chat_id,
            "last_updated": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
        
        # Save to database (for persistence)
        firestore_client = get_firestore_client()
        if firestore_client and firestore_client.initialized:
            try:
                # Get user info for database storage
                user_email = get_user_email() if is_authenticated() else "anonymous"
                user_uid = get_user_uid() if is_authenticated() else "anonymous"
                
                # Prepare data for database
                chat_data = {
                    'chat_id': chat_id,
                    'user_email': user_email,
                    'user_uid': user_uid,
                    'last_updated': datetime.now().isoformat(),
                    'message_count': len(messages),
                    'messages': messages,
                    'created_at': st.session_state.chat_histories[chat_id].get('created_at', datetime.now().isoformat())
                }
                
                # Save to Firestore
                doc_ref = firestore_client.db.collection('chat_histories').document(chat_id)
                doc_ref.set(chat_data, merge=True)
                logger.info(f"Chat history saved to database: {chat_id}")
                
            except Exception as db_error:
                logger.error(f"Database save error: {db_error}")
                # Continue with session state only if database fails
        
        logger.info(f"Chat history saved: {chat_id}")
        
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")

def load_chat_history(chat_id: str) -> list:
    """Load chat history from database first, then session state as fallback"""
    try:
        # Try to load from database first
        firestore_client = get_firestore_client()
        if firestore_client and firestore_client.initialized:
            try:
                # Get user info for database query
                user_email = get_user_email() if is_authenticated() else "anonymous"
                user_uid = get_user_uid() if is_authenticated() else "anonymous"
                
                # Query database for this user's chat
                chat_ref = firestore_client.db.collection('chat_histories').document(chat_id)
                chat_doc = chat_ref.get()
                
                if chat_doc.exists:
                    chat_data = chat_doc.to_dict()
                    # Verify this chat belongs to the current user
                    if chat_data.get('user_uid') == user_uid or chat_data.get('user_email') == user_email:
                        messages = chat_data.get('messages', [])
                        logger.info(f"Loaded chat history from database: {chat_id}")
                        
                        # Update session state with loaded data
                        if "chat_histories" not in st.session_state:
                            st.session_state.chat_histories = {}
                        st.session_state.chat_histories[chat_id] = chat_data
                        
                        return messages
                    else:
                        logger.warning(f"Chat {chat_id} does not belong to current user")
                        return []
                        
            except Exception as db_error:
                logger.error(f"Database load error: {db_error}")
                # Fall back to session state
        
        # Fallback to session state
        if "chat_histories" not in st.session_state:
            return []
        
        chat_data = st.session_state.chat_histories.get(chat_id, {})
        return chat_data.get("messages", [])
        
    except Exception as e:
        logger.error(f"Error loading chat history: {e}")
        return []

def get_available_chats() -> list:
    """Get available chat sessions from database first, then session state as fallback"""
    try:
        # Try to load from database first
        firestore_client = get_firestore_client()
        if firestore_client and firestore_client.initialized:
            try:
                # Get user info for database query
                user_email = get_user_email() if is_authenticated() else "anonymous"
                user_uid = get_user_uid() if is_authenticated() else "anonymous"
                
                # Query database for this user's chats
                chats_query = firestore_client.db.collection('chat_histories').where(
                    'user_uid', '==', user_uid
                ).order_by('last_updated', direction=firestore.Query.DESCENDING)
                
                chat_docs = chats_query.stream()
                chats = []
                
                for doc in chat_docs:
                    chat_data = doc.to_dict()
                    messages = chat_data.get('messages', [])
                    
                    preview = "New Chat"
                    for message in messages:
                        if message.get("role") == "user":
                            preview = message.get("content", "New Chat")[:50]
                            break
                    
                    chats.append({
                        "id": chat_data.get('chat_id'),
                        "preview": preview,
                        "created_at": chat_data.get('created_at', datetime.now().isoformat()),
                        "message_count": len(messages)
                    })
                
                # Update session state with loaded data
                if "chat_histories" not in st.session_state:
                    st.session_state.chat_histories = {}
                
                for chat in chats:
                    chat_id = chat["id"]
                    chat_ref = firestore_client.db.collection('chat_histories').document(chat_id)
                    chat_doc = chat_ref.get()
                    if chat_doc.exists:
                        st.session_state.chat_histories[chat_id] = chat_doc.to_dict()
                
                logger.info(f"Loaded {len(chats)} chats from database")
                return chats
                
            except Exception as db_error:
                logger.error(f"Database query error: {db_error}")
                # Fall back to session state
        
        # Fallback to session state
        if "chat_histories" not in st.session_state:
            return []
        
        chats = []
        for chat_id, chat_data in st.session_state.chat_histories.items():
            messages = chat_data.get("messages", [])
            
            preview = "New Chat"
            for message in messages:
                if message.get("role") == "user":
                    preview = message.get("content", "New Chat")[:50]
                    break
            
            created_at = chat_data.get("created_at", datetime.now().isoformat())

            chats.append({
                "id": chat_id,
                "preview": preview,
                "created_at": created_at,
                "message_count": len(messages)
            })
        
        # Sort by last updated
        chats.sort(key=lambda x: x["created_at"], reverse=True)
        return chats
        
    except Exception as e:
        logger.error(f"Error getting available chats: {e}")
        return []

# UI Components
def display_claude_header():
    """Display the Claude AI inspired header"""
    st.markdown("""
    <div class="claude-header">
        <div class="claude-logo">🤖</div>
        <h1>MultiAgentAI21</h1>
        <p>Next-Generation Multi-Agent AI System for Enterprise Solutions</p>
        <div class="claude-badges">
            <span class="claude-badge">🚀 AI-Powered</span>
            <span class="claude-badge">⚡ Real-time</span>
            <span class="claude-badge">🔒 Secure</span>
            <span class="claude-badge">🎯 Enterprise</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_claude_agent_selection():
    """Display Claude AI inspired agent selection interface"""
    if not st.session_state.agent_locked:
        st.subheader("🤖 Choose Your AI Agent")
        
        agent_options = {
            AgentType.DATA_ANALYSIS.value: {
                "icon": "📊",
                "title": "Data Analysis Expert",
                "description": "Advanced analytics, insights, and data visualization",
                "color": "#667eea"
            },
            AgentType.AUTOMATION.value: {
                "icon": "⚙️", 
                "title": "DevOps Automation Expert",
                "description": "Infrastructure as Code, CI/CD pipelines, Kubernetes, monitoring, and security automation",
                "color": "#10b981"
            },
            AgentType.CONTENT_CREATION.value: {
                "icon": "✍️",
                "title": "Content Creator",
                "description": "Professional content and marketing materials",
                "color": "#f59e0b"
            },
            AgentType.CUSTOMER_SERVICE.value: {
                "icon": "🎯",
                "title": "Customer Success",
                "description": "Support and engagement solutions",
                "color": "#764ba2"
            }
            
        }
        
        # Create a 2x2 grid for agent selection
        cols = st.columns(2)
        for i, (agent_type, info) in enumerate(agent_options.items()):
            with cols[i % 2]:
                st.markdown(f"""
                <div class="claude-agent-card" style="border-color: {info['color']}20;">
                    <div class="claude-agent-icon">{info['icon']}</div>
                    <div class="claude-agent-title">{info['title']}</div>
                    <div class="claude-agent-description">{info['description']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select {info['title']}", key=f"select_{agent_type}", use_container_width=True):
                    st.session_state.selected_agent = agent_type
                    st.session_state.agent_locked = True
                    # Auto-start new chat for new agent
                    st.session_state.current_chat_id = f"chat_{int(time.time())}"
                    st.session_state.chat_history = []
                    st.success(f"✅ Connected to {info['title']}! New chat started automatically.")
                    st.rerun()
    else:
        agent_info = {
            "data_analysis_and_insights": {"icon": "📊", "title": "Data Analysis Expert", "color": "#667eea"},
            "automation_of_complex_processes": {"icon": "⚙️", "title": "DevOps Automation Expert", "color": "#10b981"},
            "content_creation_and_generation": {"icon": "✍️", "title": "Content Creator", "color": "#f59e0b"},
            "customer_service_and_engagement": {"icon": "🎯", "title": "Customer Success", "color": "#764ba2"},
            
        }
        
        info = agent_info.get(st.session_state.selected_agent, {"icon": "🤖", "title": "AI Agent", "color": "#667eea"})
        
        st.markdown(f"""
        <div class="claude-status" style="background: linear-gradient(135deg, {info['color']} 0%, {info['color']}dd 100%);">
            {info['icon']} Active: {info['title']}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Change Agent", key="change_agent_btn", help="Switch to a different AI agent"):
            st.session_state.agent_locked = False
            st.session_state.selected_agent = None
            # Clear current chat when changing agents
            st.session_state.chat_history = []
            st.rerun()

def display_professional_chat_messages():
    """Display professional chat messages with enhanced formatting and feedback collection"""
    if not st.session_state.chat_history:
        # Show welcome message with examples
        if st.session_state.selected_agent:
            agent_examples = {
                "data_analysis_and_insights": [
                    "Analyze this CSV file and show insights",
                    "Calculate the average of 125000, 135000, 145000",
                    "Show me the first 5 rows and data types"
                ],
                "automation_of_complex_processes": [
                    "Create a Terraform configuration for AWS infrastructure",
                    "Design a Jenkins CI/CD pipeline for Python applications",
                    "Set up Prometheus monitoring for microservices",
                    "Automate Kubernetes deployment with Helm charts",
                    "Implement security scanning and compliance automation"
                ],
                "content_creation_and_generation": [
                    "Write a blog post about AI trends",
                    "Create LinkedIn content about data science",
                    "Generate marketing copy for an AI product"
                ],
                "customer_service_and_engagement": [
                    "How do I use the data analysis features?",
                    "What can the automation agent do?",
                    "Help me choose the right agent"
                ]
               
            }
            
            examples = agent_examples.get(st.session_state.selected_agent, [])
            
            # Create a compact welcome message with Claude AI styling
            st.markdown(f"""
            <div style="
                text-align: center; 
                padding: 1rem; 
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                border-radius: 12px;
                margin: 0.5rem 0;
                border: 1px solid #e2e8f0;
            ">
                <div style="
                    width: 48px;
                    height: 48px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    margin: 0 auto 1rem auto;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                ">
                    🤖
                </div>
                <h4 style="
                    color: #1a1a1a; 
                    font-size: 1.25rem; 
                    font-weight: 700; 
                    margin-bottom: 0.5rem;
                ">
                    Welcome to {st.session_state.selected_agent.replace('_', ' ').title()}!
                </h4>
                <p style="
                    color: #64748b; 
                    font-size: 0.9rem; 
                    margin-bottom: 1rem;
                    line-height: 1.5;
                ">
                    I'm ready to help you with your tasks. Here are some examples to get started:
                </p>
                <div style="
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                    max-width: 400px;
                    margin: 0 auto;
                ">
            """, unsafe_allow_html=True)
            
            for i, example in enumerate(examples):
                st.markdown(f"""
                <div style="
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 0.75rem;
                    text-align: left;
                    transition: all 0.2s ease;
                    cursor: pointer;
                " onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 2px 8px rgba(102, 126, 234, 0.1)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                    <div style="color: #667eea; font-weight: 600; margin-bottom: 0.25rem; font-size: 0.8rem;">💡 Example {i+1}</div>
                    <div style="color: #1a1a1a; font-size: 0.85rem;">{example}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Try this example", key=f"example_{i}", use_container_width=True):
                    process_and_display_user_message(example)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="
                text-align: center; 
                padding: 3rem 2rem; 
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                border-radius: 16px;
                margin: 2rem 0;
                border: 1px solid #e2e8f0;
            ">
                <div style="
                    width: 64px;
                    height: 64px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 32px;
                    margin: 0 auto 1.5rem auto;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                ">
                    🚀
                </div>
                <h3 style="color: #1a1a1a; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">
                    Welcome to MultiAgentAI21
                </h3>
                <p style="color: #64748b; font-size: 1rem; margin-bottom: 1rem;">
                    Please select an AI agent above to start chatting and get professional assistance.
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Display actual chat messages with professional styling and feedback
        for i, message in enumerate(st.session_state.chat_history):
            with st.chat_message(message["role"]):
                if message["role"] == "assistant" and not message.get("success", True):
                    st.error(message["content"])
                else:
                    st.markdown(message["content"])
                
                # Add metadata for assistant messages
                if message["role"] == "assistant":
                    metadata = []
                    if "execution_time" in message:
                        metadata.append(f"⏱️ {message['execution_time']:.2f}s")
                    if "agent_type" in message:
                        metadata.append(f"🤖 {message['agent_type'].replace('_', ' ').title()}")
                    if "timestamp" in message:
                        try:
                            timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%H:%M:%S")
                            metadata.append(f"🕐 {timestamp}")
                        except:
                            pass
                    
                    if metadata:
                        st.caption(" | ".join(metadata))

def is_acknowledgment(message: str) -> bool:
    """Check if the message is an acknowledgment like 'thank you', 'thanks', 'ok', etc."""
    if not message or not isinstance(message, str):
        return False

    # Convert to lowercase and remove punctuation for comparison
    clean_message = message.lower().strip()
    clean_message = ''.join(c for c in clean_message if c.isalnum() or c.isspace())

    # Only match very specific, exact acknowledgment phrases to avoid false positives
    # Must be a short message (5 words or less) to be considered acknowledgment
    words = clean_message.split()
    if len(words) > 5:
        return False

    # Exact match acknowledgment phrases
    exact_acknowledgments = [
        'thank you', 'thanks', 'thankyou', 'thx', 'ty',
        'ok', 'okay',
        'bye', 'goodbye',
        'got it', 'gotit',
        'k'
    ]

    # Check if the entire message is an acknowledgment
    if clean_message in exact_acknowledgments:
        return True

    # Check if it starts with thank/thanks
    if words[0] in ['thank', 'thanks', 'thankyou', 'thx', 'ty']:
        return True

    return False

def generate_acknowledgment_response() -> str:
    """Generate an appropriate acknowledgment response."""
    import random
    
    responses = [
        "You're welcome! 😊 I'm glad I could help.",
        "Happy to help! 🎉 Is there anything else you'd like me to assist you with?",
        "You're very welcome! ✨ Feel free to ask if you need anything more.",
        "My pleasure! 🚀 I'm here whenever you need assistance.",
        "Anytime! 😄 Don't hesitate to reach out if you have more questions.",
        "Glad I could be of help! 🌟 What else can I do for you today?",
        "You're welcome! 🎯 Ready for your next request whenever you are.",
        "Happy to assist! 💫 Let me know if you need anything else.",
        "My pleasure! 🎊 I'm here to help with whatever you need.",
        "Anytime! 🚀 Looking forward to helping you with your next task."
    ]
    
    return random.choice(responses)

def process_and_display_user_message(user_input, uploaded_files=None):
    """Process user message with enhanced file support and acknowledgment handling"""
    if not st.session_state.agent:
        st.error("❌ Agent system not initialized")
        return

    if not st.session_state.selected_agent:
        st.error("❌ Please select an agent first")
        return

    # Check if this is an acknowledgment message
    if is_acknowledgment(user_input):
        # Handle acknowledgment without calling the agent
        acknowledgment_response = generate_acknowledgment_response()
        
        # Add user message to chat history
        user_message = {
            "role": "user", 
            "content": user_input, 
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.chat_history.append(user_message)
        
        # Add acknowledgment response
        assistant_message = {
            "role": "assistant", 
            "content": acknowledgment_response,
            "timestamp": datetime.now().isoformat(),
            "execution_time": 0.0,
            "agent_type": "acknowledgment",
            "success": True
        }
        st.session_state.chat_history.append(assistant_message)
        
        # Save to Firestore
        save_chat_history(st.session_state.current_chat_id, st.session_state.chat_history)
        
        # Show acknowledgment message
        st.success("💬 Acknowledgment received!")
        st.rerun()
        return

    # Prepare message content
    message_content = user_input
    if uploaded_files:
        files_info = []
        for file in uploaded_files:
            file_size = f"{file.size / 1024:.1f} KB" if file.size < 1024*1024 else f"{file.size / (1024*1024):.1f} MB"
            files_info.append(f"📎 {file.name} ({file_size})")
        message_content += f"\n\n**Attached Files:** {', '.join(files_info)}"

    # Add user message to chat history
    user_message = {
        "role": "user", 
        "content": message_content, 
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.chat_history.append(user_message)

    try:
        # Convert to AgentType enum
        agent_type = AgentType(st.session_state.selected_agent)
        
        # Prepare context
        context = {
            "chat_history": st.session_state.chat_history[:-1],
            "session_id": st.session_state.current_chat_id
        }
        
        # Process with enhanced routing
        with st.spinner("🤖 Processing your request..."):
            response = st.session_state.agent.route_request(
                request=user_input,
                agent_type=agent_type,
                context=context,
                session_id=st.session_state.current_chat_id,
                files=uploaded_files
            )

        if response and response.content:
            # Add assistant response
            assistant_message = {
                "role": "assistant", 
                "content": response.content,
                "timestamp": datetime.now().isoformat(),
                "execution_time": getattr(response, 'execution_time', 0),
                "agent_type": st.session_state.selected_agent,
                "success": getattr(response, 'success', True)
            }
            st.session_state.chat_history.append(assistant_message)
            
            # Save to Firestore
            save_chat_history(st.session_state.current_chat_id, st.session_state.chat_history)
            
            # Show success message
            exec_time = getattr(response, 'execution_time', 0)
            st.success(f"✅ Response from {agent_type.value.replace('_', ' ').title()} Agent (⏱️ {exec_time:.2f}s)")
            
        else:
            error_msg = getattr(response, 'error_message', 'Unknown error')
            st.error(f"❌ Error: {error_msg}")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        st.error(f"❌ System Error: {e}")

    st.rerun()

def display_claude_chat_interface():
    """Display the Claude AI inspired chat interface"""
    # Initialize variables at function scope
    uploaded_files = None
    send_clicked = False

    # Initialize session state for input clearing
    if "input_counter" not in st.session_state:
        st.session_state.input_counter = 0

    st.header("💬 AI Assistant")

    # Agent selection
    display_claude_agent_selection()

    # Chat interface
    if st.session_state.agent_locked and st.session_state.selected_agent:
        agent_info = {
            "data_analysis_and_insights": "Data Analysis Expert",
            "automation_of_complex_processes": "DevOps Automation Expert",
            "content_creation_and_generation": "Content Creator",
            "customer_service_and_engagement": "Customer Success",
        }

        agent_title = agent_info.get(st.session_state.selected_agent, "AI Assistant")
        st.subheader(f"💬 {agent_title}")

        # Chat messages area
        display_professional_chat_messages()

        st.markdown("---")

        # Input controls
        col1, col2, col3 = st.columns([8, 1, 1.5])

        with col1:
            user_input = st.text_area(
                "Your message",
                placeholder="Type your request here... (e.g., 'Analyze this data', 'Create a script', 'Write content')",
                height=100,
                key=f"chat_input_{st.session_state.input_counter}",
                label_visibility="collapsed"
            )

        with col2:
            if st.button("📎", key="attach_btn", help="Attach files", use_container_width=True):
                st.session_state.show_file_upload = not st.session_state.show_file_upload
                st.rerun()

        with col3:
            send_clicked = st.button("Send", key="send_button", type="primary", use_container_width=True)
        
        # File upload with Claude styling
        if st.session_state.show_file_upload:
            uploaded_files = st.file_uploader(
                "📎 Attach Files",
                accept_multiple_files=True,
                key="chat_file_upload",
                type=['csv', 'xlsx', 'xls', 'txt', 'pdf', 'json', 'py', 'js', 'html', 'css', 'md'],
                help="Upload files for analysis and processing"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} file(s) ready for processing")
                for file in uploaded_files:
                    file_size = f"{file.size / 1024:.1f} KB" if file.size < 1024*1024 else f"{file.size / (1024*1024):.1f} MB"
                    st.caption(f"📄 {file.name} ({file_size})")
        
        # Process message
        if send_clicked and (user_input.strip() or (uploaded_files and len(uploaded_files) > 0)):
            # Check if this is an acknowledgment before processing
            if is_acknowledgment(user_input.strip()):
                st.info("💬 **Acknowledgment Detected** - Processing your polite response...")

            process_and_display_user_message(user_input, uploaded_files)
            # Increment counter to force new input key (clears the input)
            st.session_state.input_counter += 1
            st.session_state.show_file_upload = False
            st.rerun()
        elif send_clicked:
            st.warning("Please enter a message or upload files.")

def display_enhanced_analytics_dashboard():
    """Display enhanced analytics dashboard with agent performance and learning insights"""
    st.header("📊 Analytics Dashboard")

    # Check if agent system is available
    if not st.session_state.agent:
        st.warning("⚠️ Agent system not initialized. Please use the Agent Chat first.")
        return
    
    # System Overview
    st.subheader("🚀 System Overview")
    
    try:
        system_report = st.session_state.agent.get_system_performance_report()
        
        if 'status' in system_report and system_report['status'] == 'No performance data available':
            st.info("📈 No performance data available yet. Start using the agents to see analytics!")
        else:
            # Display system metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Requests", system_report['system_overview']['total_requests'])
            
            with col2:
                st.metric("Success Rate", system_report['system_overview']['overall_success_rate'])
            
            with col3:
                st.metric("Avg Response Time", system_report['system_overview']['average_response_time'])
            
            with col4:
                st.metric("System Uptime", system_report['system_overview']['system_uptime'])
            
            # Agent Performance Details
            st.subheader("🤖 Agent Performance")
            
            agent_performance = system_report.get('agent_performance', {})
            if agent_performance:
                for agent_type, metrics in agent_performance.items():
                    with st.expander(f"📊 {agent_type.replace('_', ' ').title()}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Requests", metrics['total_requests'])
                        
                        with col2:
                            st.metric("Success Rate", metrics['success_rate'])
                        
                        with col3:
                            st.metric("Avg Response Time", metrics['average_response_time'])
                        
                        # Get detailed learning insights
                        if st.button(f"🔍 Get Learning Insights", key=f"insights_{agent_type}"):
                            insights = st.session_state.agent.get_agent_learning_insights(agent_type)
                            if 'error' not in insights:
                                st.json(insights)
                            else:
                                st.error(f"Error getting insights: {insights['error']}")
            
            # Recent Optimizations
            if system_report.get('recent_optimizations'):
                st.subheader("⚡ Recent System Optimizations")
                for opt in system_report['recent_optimizations']:
                    st.info(f"**{opt['action']}** - {opt['reason']} ({opt['timestamp']})")
        
    except Exception as e:
        st.error(f"❌ Error getting system report: {e}")
    
    # Agent Learning Insights
    st.subheader("🧠 Agent Learning Insights")
    
    # Agent selection for detailed insights
    agent_options = [
        "data_analysis_and_insights",
        "automation_of_complex_processes", 
        "content_creation_and_generation",
        "customer_service_and_engagement"
    ]
    
    selected_agent_for_insights = st.selectbox(
        "Select Agent for Learning Analysis:",
        agent_options,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if st.button("🔍 Analyze Learning Patterns", key="analyze_learning"):
        try:
            insights = st.session_state.agent.get_agent_learning_insights(selected_agent_for_insights)
            
            if 'error' not in insights:
                # Display learning insights
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📈 Performance Summary")
                    performance = insights['performance_summary']
                    st.metric("Total Requests", performance['total_requests'])
                    st.metric("Success Rate", performance['success_rate'])
                    st.metric("Avg Response Time", performance['average_response_time'])
                    st.metric("Learning History Size", performance['learning_history_size'])
                
                with col2:
                    st.subheader("📊 Learning Patterns")
                    patterns = insights['learning_patterns']
                    if 'status' not in patterns:
                        st.metric("Response Time Trend", patterns['recent_response_time_trend'])
                        st.metric("Success Rate Trend", patterns['success_rate_trend'])
                        st.metric("Total Learning Interactions", patterns['total_learning_interactions'])
                    else:
                        st.info(patterns['status'])
                
                # Improvement Opportunities
                st.subheader("🎯 Improvement Opportunities")
                opportunities = insights['improvement_opportunities']
                for opp in opportunities:
                    st.warning(f"• {opp}")
                
                # Recommendations
                st.subheader("💡 Recommendations")
                recommendations = insights['recommendations']
                for rec in recommendations:
                    st.success(f"• {rec}")
                    
            else:
                st.error(f"Error getting insights: {insights['error']}")
                
        except Exception as e:
            st.error(f"❌ Error analyzing learning patterns: {e}")
    
    # System Optimization Controls
    st.subheader("⚙️ System Optimization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Optimize All Agents", key="optimize_all"):
            try:
                st.session_state.agent.optimize_all_agents()
                st.success("✅ All agents optimized successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error optimizing agents: {e}")
    
    with col2:
        if st.button("📊 Refresh Metrics", key="refresh_metrics"):
            st.rerun()
    
    # User Feedback Collection
    st.subheader("💬 User Feedback")
    
    feedback_agent = st.selectbox(
        "Select Agent for Feedback:",
        agent_options,
        format_func=lambda x: x.replace('_', ' ').title(),
        key="feedback_agent"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        satisfaction_score = st.slider(
            "Rate your satisfaction (1-5):",
            min_value=1,
            max_value=5,
            value=5,
            key="satisfaction_slider"
        )
    
    with col2:
        feedback_text = st.text_area(
            "Additional feedback (optional):",
            placeholder="Tell us how we can improve...",
            key="feedback_text",
            height=100
        )
    
    if st.button("📤 Submit Feedback", key="submit_feedback"):
        try:
            # Add feedback to the specific agent
            agent_type_enum = AgentType(feedback_agent)
            if agent_type_enum in st.session_state.agent.agents:
                st.session_state.agent.agents[agent_type_enum].add_user_feedback(
                    satisfaction_score,
                    feedback_text
                )
            # Also record system-wide feedback
            st.session_state.agent.add_user_feedback(feedback_agent, satisfaction_score, feedback_text)
            st.success("✅ Thank you for your feedback! It will help us improve.")
        except Exception as e:
            st.error(f"❌ Error submitting feedback: {e}")

def display_chat_history_sidebar():
    """Display chat history in sidebar"""
    st.sidebar.title("💬 Chat History")

    # Control buttons
    if st.sidebar.button("✨ New Chat", key="new_chat_btn"):
        st.session_state.current_chat_id = f"chat_{int(time.time())}"
        st.session_state.chat_history = []
        st.session_state.agent_locked = False
        st.session_state.selected_agent = None
        st.success("New chat started!")
        st.rerun()

    if st.sidebar.button("🔄 Clear Cache", key="clear_cache_btn"):
        st.cache_resource.clear()
        st.session_state.agent = None
        st.success("Cache cleared!")
        st.rerun()

    # Show chats (user must be authenticated to reach this point)
    chats = get_available_chats()
    if chats:
        st.sidebar.subheader("Recent Chats")
        for chat in chats[:10]:  # Show last 10 chats
            preview = chat["preview"][:25] + "..." if len(chat["preview"]) > 25 else chat["preview"]
            if st.sidebar.button(f"💬 {preview}", key=f"chat_{chat['id']}"):
                st.session_state.current_chat_id = chat["id"]
                st.session_state.chat_history = load_chat_history(chat["id"])
                st.session_state.agent_locked = True
                st.success(f"Loaded chat: {preview}")
                st.rerun()
    else:
        st.sidebar.info("No previous chats found")

def user_profile_sidebar():
    """Display user profile in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 User Profile")
        st.write(f"**Name:** {get_user_name() or 'N/A'}")
        st.write(f"**Email:** {get_user_email() or 'N/A'}")
        
        if st.button("Logout", key="sidebar_logout"):
            logout()

def cleanup_temp_files():
    """Clean up temporary files"""
    if "temp_files" in st.session_state and st.session_state.temp_files:
        for file_path in st.session_state.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed temp file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing temp file: {e}")
        st.session_state.temp_files = []

# Main application
@require_auth
def main_app():
    """Main application logic with modern UI"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Display Claude AI header
        display_claude_header()

        # Initialize agent system
        if st.session_state.agent is None:
            st.session_state.agent = get_agent_system()
            if not st.session_state.agent:
                st.error("❌ Failed to initialize agent system")
                return

        # Claude AI sidebar
        with st.sidebar:
            st.markdown("""
            <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0; color: #1a1a1a;">🧭 Navigation</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # User profile with Claude styling
            user_profile_sidebar()
            display_chat_history_sidebar()

            # Page selection with Claude styling
            st.markdown("---")
            st.markdown("### 📄 Pages")
            page = st.radio(
                "Select a page",
                ["🤖 Agent Chat", "📊 Analytics", "📚 Documentation"],
                key="navigation_radio"
            )

        # Display selected page with Claude styling
        if page == "🤖 Agent Chat":
            display_claude_chat_interface()
        elif page == "📊 Analytics":
            display_enhanced_analytics_dashboard()
        elif page == "📚 Documentation":
            st.header("📚 Documentation")

            with st.expander("🚀 Getting Started", expanded=True):
                st.write("**Welcome to MultiAgentAI21**")
                st.write("• Select an AI agent based on your needs")
                st.write("• Upload files for analysis and processing")
                st.write("• Get professional results and insights")

            with st.expander("🤖 Agent Capabilities"):
                st.write("**Next-Generation AI Solutions**")
                st.write("• **Data Analysis**: Advanced analytics and insights")
                st.write("• **DevOps Automation**: CI/CD, Infrastructure as Code, Kubernetes, monitoring")
                st.write("• **Content Creation**: Professional content generation")
                st.write("• **Customer Service**: Support and engagement solutions")

        # Cleanup temp files
        atexit.register(cleanup_temp_files)

    except Exception as e:
        logger.error(f"Error in main app: {e}", exc_info=True)
        st.error(f"❌ Application error: {e}")

# Application entry point
if __name__ == "__main__":
    try:
        logger.info("Starting MultiAgentAI21 application")
        
        # Check authentication and run appropriate page
        if not is_authenticated():
            login_page()
        else:
            main_app()
            
    except Exception as e:
        logger.critical(f"Critical application error: {e}", exc_info=True)
        st.error(f"❌ Critical error: {e}")
        st.info("Please check your environment configuration and try again.")