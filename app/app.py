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
    
    # Essential variables
    if not os.getenv("GOOGLE_API_KEY"):
        issues.append("GOOGLE_API_KEY is not set (required for Gemini API)")
    
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        issues.append("GOOGLE_APPLICATION_CREDENTIALS is not set (required for Firebase/Firestore)")
    elif not os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
        issues.append(f"GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    
    return issues

# Display environment warnings
environment_issues = check_environment()
if environment_issues:
    st.error("⚠️ Environment Configuration Issues:")
    for issue in environment_issues:
        st.error(f"• {issue}")
    st.info("💡 Please check your .env file or environment variables")
    logger.error(f"Environment issues: {environment_issues}")

# Firebase and Google Cloud imports
try:
    from firebase_admin import credentials, auth
    import firebase_admin
    from google.cloud import firestore
    import google.auth
    import google.oauth2.credentials
    logger.info("Successfully imported Firebase/Google Cloud libraries")
except ImportError as e:
    logger.error(f"Failed to import Firebase/Google Cloud libraries: {e}")
    st.error(f"❌ Missing Firebase dependencies: {e}")
    st.info("Please install: pip install firebase-admin google-cloud-firestore")
    st.stop()

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
    logger.info("Successfully imported auth_manager")
    
    # Setup credentials
    setup_google_application_credentials()
    initialize_firebase()
    
except ModuleNotFoundError as e:
    logger.critical(f"ModuleNotFoundError: {e}")
    st.error(f"❌ Cannot find authentication module: {e}")
    st.error("Please ensure src/auth_manager.py exists and is properly configured")
    st.stop()
except Exception as e:
    logger.critical(f"Authentication setup error: {e}", exc_info=True)
    st.error(f"❌ Authentication setup failed: {e}")
    st.stop()

# Initialize Firestore client
@st.cache_resource
def get_firestore_client():
    """Initialize and cache Firestore client"""
    try:
        PROJECT_ID = "multiagentai21-9a8fc"
        DATABASE_NAME = "multiagentaifirestoredatabase"
        
        db = firestore.Client(project=PROJECT_ID, database=DATABASE_NAME)
        logger.info(f"Firestore client initialized: {PROJECT_ID}/{DATABASE_NAME}")
        return db
        
    except Exception as e:
        logger.error(f"Firestore initialization error: {e}")
        st.error(f"❌ Firestore initialization failed: {e}")
        return None

# Initialize Firestore
db = get_firestore_client()

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
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        # Create agent instance
        agent_instance = MultiAgentCodingAI()
        logger.info("MultiAgentAI21 initialized successfully")
        return agent_instance
        
    except Exception as e:
        logger.error(f"Agent system initialization error: {e}")
        st.error(f"❌ Failed to initialize agent system: {e}")
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

def get_firestore_chat_collection():
    """Get Firestore collection for chat histories"""
    if db is None:
        st.error("Firestore client not initialized")
        return None
    
    user_info = get_current_user()
    user_uid = user_info.get("uid") if user_info else None

    if not user_uid:
        st.error("❌ User not authenticated")
        return None
    
    return db.collection("users").document(user_uid).collection(CHAT_HISTORY_COLLECTION_NAME)

def save_chat_history(chat_id: str, messages: list):
    """Save chat history to Firestore"""
    chat_collection = get_firestore_chat_collection()
    if not chat_collection:
        st.error("❌ Cannot save chat history - user not authenticated")
        return

    try:
        from google.cloud.firestore_v1 import SERVER_TIMESTAMP
        
        chat_ref = chat_collection.document(chat_id)
        doc = chat_ref.get()
        
        chat_data = {
            "chat_id": chat_id,
            "last_updated": SERVER_TIMESTAMP,
            "message_count": len(messages),
            "messages": messages
        }
        
        if not doc.exists:
            chat_data["created_at"] = SERVER_TIMESTAMP
        
        chat_ref.set(chat_data, merge=True)
        logger.info(f"Chat history saved: {chat_id}")
        
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")
        st.error(f"Failed to save chat history: {e}")

def load_chat_history(chat_id: str) -> list:
    """Load chat history from Firestore"""
    chat_collection = get_firestore_chat_collection()
    if not chat_collection:
        st.error("❌ Cannot load chat history - user not authenticated")
        return []

    try:
        doc = chat_collection.document(chat_id).get()
        if doc.exists:
            return doc.to_dict().get("messages", [])
        return []
        
    except Exception as e:
        logger.error(f"Error loading chat history: {e}")
        return []

def get_available_chats() -> list:
    """Get available chat sessions"""
    chat_collection = get_firestore_chat_collection()
    if not chat_collection:
        return []

    try:
        chats = []
        chat_docs = chat_collection.order_by("last_updated", direction=firestore.Query.DESCENDING).stream()
        
        for doc in chat_docs:
            chat_data = doc.to_dict()
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

            chats.append({
                "id": doc.id,
                "preview": preview,
                "created_at": created_at,
                "message_count": len(messages)
            })
        
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
                "title": "Automation Specialist",
                "description": "Process automation and workflow optimization",
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
            "automation_of_complex_processes": {"icon": "⚙️", "title": "Automation Specialist", "color": "#10b981"},
            "content_creation_and_generation": {"icon": "✍️", "title": "Content Creator", "color": "#f59e0b"},
            "customer_service_and_engagement": {"icon": "🎯", "title": "Customer Success", "color": "#764ba2"}
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
                    "Process this file and clean the data",
                    "Generate a Python script to organize files",
                    "Create a workflow for data processing"
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
                    
                    # Add feedback collection for assistant messages
                    if st.session_state.agent and message.get("agent_type"):
                        st.markdown("---")
                        st.markdown("**Rate this response:**")
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        feedback_key = f"feedback_{i}"
                        if feedback_key not in st.session_state:
                            st.session_state[feedback_key] = None
                        
                        with col1:
                            if st.button("😞", key=f"rate_1_{i}", help="Very Dissatisfied"):
                                st.session_state[feedback_key] = 1
                                st.success("Feedback recorded!")
                        
                        with col2:
                            if st.button("😐", key=f"rate_2_{i}", help="Dissatisfied"):
                                st.session_state[feedback_key] = 2
                                st.success("Feedback recorded!")
                        
                        with col3:
                            if st.button("😊", key=f"rate_3_{i}", help="Neutral"):
                                st.session_state[feedback_key] = 3
                                st.success("Feedback recorded!")
                        
                        with col4:
                            if st.button("😄", key=f"rate_4_{i}", help="Satisfied"):
                                st.session_state[feedback_key] = 4
                                st.success("Feedback recorded!")
                        
                        with col5:
                            if st.button("🤩", key=f"rate_5_{i}", help="Very Satisfied"):
                                st.session_state[feedback_key] = 5
                                st.success("Feedback recorded!")
                        
                        # If feedback was given, add it to the agent system
                        if st.session_state[feedback_key] is not None:
                            try:
                                # Get the specific agent instance for feedback
                                agent_type_enum = AgentType(message["agent_type"])
                                if agent_type_enum in st.session_state.agent.agents:
                                    st.session_state.agent.agents[agent_type_enum].add_user_feedback(
                                        st.session_state[feedback_key],
                                        f"Response feedback for message {i+1}"
                                    )
                                # Also record system-wide feedback
                                st.session_state.agent.add_user_feedback(
                                    message["agent_type"],
                                    st.session_state[feedback_key],
                                    f"Response feedback for message {i+1}"
                                )
                            except Exception as e:
                                st.error(f"Error recording feedback: {e}")

def process_and_display_user_message(user_input, uploaded_files=None):
    """Process user message with enhanced file support"""
    if not st.session_state.agent:
        st.error("❌ Agent system not initialized")
        return

    if not st.session_state.selected_agent:
        st.error("❌ Please select an agent first")
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
    
    st.markdown('<div class="claude-card">', unsafe_allow_html=True)
    st.header("💬 AI Assistant")
    
    # Agent selection
    display_claude_agent_selection()

    # Claude chat container
    if st.session_state.agent_locked and st.session_state.selected_agent:
        st.markdown('<div class="claude-chat-container">', unsafe_allow_html=True)
        
        # Chat header
        agent_info = {
            "data_analysis_and_insights": "Data Analysis Expert",
            "automation_of_complex_processes": "Automation Specialist", 
            "content_creation_and_generation": "Content Creator",
            "customer_service_and_engagement": "Customer Success"
        }
        
        agent_title = agent_info.get(st.session_state.selected_agent, "AI Assistant")
        
        st.markdown(f"""
        <div class="claude-chat-header">
            💬 Chat with {agent_title}
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages area
        st.markdown('<div class="claude-chat-messages">', unsafe_allow_html=True)
        display_professional_chat_messages()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Claude input area
        st.markdown('<div class="claude-input-area">', unsafe_allow_html=True)
        
        # Enhanced input area with better styling
        st.markdown("""
        <div style="
            background: #ffffff;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        ">
        """, unsafe_allow_html=True)
        
        # Input controls with Claude styling
        col1, col2, col3 = st.columns([8, 1, 1.5])
        
        with col1:
            user_input = st.text_area(
                "Your message",
                placeholder="Type your request here... (e.g., 'Analyze this data', 'Create a script', 'Write content')",
                height=68,
                key=f"chat_input_{st.session_state.input_counter}",
                label_visibility="collapsed"
            )
        
        with col2:
            if st.button("📎", key="attach_btn", help="Attach files", use_container_width=True):
                st.session_state.show_file_upload = not st.session_state.show_file_upload
                st.rerun()
        
        with col3:
            send_clicked = st.button("Send", key="send_button", type="primary", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
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
            process_and_display_user_message(user_input, uploaded_files)
            # Increment counter to force new input key (clears the input)
            st.session_state.input_counter += 1
            st.session_state.show_file_upload = False
            st.rerun()
        elif send_clicked:
            st.warning("Please enter a message or upload files.")
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close input area
        st.markdown('</div>', unsafe_allow_html=True)  # Close chat container
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close Claude card

def display_enhanced_analytics_dashboard():
    """Display enhanced analytics dashboard with agent performance and learning insights"""
    st.markdown('<div class="claude-card">', unsafe_allow_html=True)
    st.header("📊 Enhanced Analytics Dashboard")
    
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
    
    st.markdown('</div>', unsafe_allow_html=True)

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
    user = get_current_user()
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 User Profile")
        st.write(f"**Name:** {user.get('display_name', 'N/A')}")
        st.write(f"**Email:** {user.get('email', 'N/A')}")
        
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
@login_required
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
            st.markdown('<div class="claude-card">', unsafe_allow_html=True)
            st.header("📚 Documentation")
            
            with st.expander("🚀 Getting Started", expanded=True):
                st.write("**Welcome to MultiAgentAI21**")
                st.write("• Select an AI agent based on your needs")
                st.write("• Upload files for analysis and processing")
                st.write("• Get professional results and insights")
            
            with st.expander("🤖 Agent Capabilities"):
                st.write("**Next-Generation AI Solutions**")
                st.write("• **Data Analysis**: Advanced analytics and insights")
                st.write("• **Automation**: Workflow optimization and scripting")
                st.write("• **Content Creation**: Professional content generation")
                st.write("• **Customer Service**: Support and engagement solutions")
            
            st.markdown('</div>', unsafe_allow_html=True)

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