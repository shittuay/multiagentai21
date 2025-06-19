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

# Enhanced CSS styling
st.markdown("""
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

    .page-content-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }

    .integrated-chat-container {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        margin-top: 1rem;
        display: flex;
        flex-direction: column;
        min-height: 400px;
    }

    .integrated-input-area {
        background: rgba(248, 250, 252, 0.95);
        border-top: 1px solid rgba(0, 0, 0, 0.08);
        padding: 1.5rem;
        backdrop-filter: blur(10px);
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
        if "anonymous_user_id" not in st.session_state:
            st.session_state.anonymous_user_id = f"anon_{os.urandom(16).hex()}"
        user_uid = st.session_state.anonymous_user_id
    
    return db.collection("users").document(user_uid).collection(CHAT_HISTORY_COLLECTION_NAME)

def save_chat_history(chat_id: str, messages: list):
    """Save chat history to Firestore"""
    chat_collection = get_firestore_chat_collection()
    if not chat_collection:
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
    if not is_authenticated():
        return []
    
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
def display_enhanced_header():
    """Display the enhanced header"""
    st.markdown("""
    <div class="main-header">
        <div class="logo-container">
            <div class="logo-icon">🚀</div>
            <h1>MultiAgentAI21</h1>
        </div>
        <p>Advanced Multi-Agent AI System for Complex Problem Solving</p>
    </div>
    """, unsafe_allow_html=True)

def display_agent_selection():
    """Display agent selection interface"""
    if not st.session_state.agent_locked:
        st.subheader("🤖 Select an Agent")
        
        agent_descriptions = {
            AgentType.DATA_ANALYSIS.value: "📊 Analyzes data files, performs calculations, generates insights",
            AgentType.AUTOMATION.value: "🤖 Processes files, creates scripts, automates workflows", 
            AgentType.CONTENT_CREATION.value: "📝 Creates blog posts, social media content, marketing copy",
            AgentType.CUSTOMER_SERVICE.value: "💬 Provides support, answers questions, offers guidance"
        }
        
        # Display agent options with descriptions
        for agent_type in AgentType:
            description = agent_descriptions.get(agent_type.value, "")
            if st.button(f"{description}", key=f"select_{agent_type.value}"):
                st.session_state.selected_agent = agent_type.value
                st.session_state.agent_locked = True
                st.success(f"✅ Connected to {agent_type.value.replace('_', ' ').title()} Agent!")
                st.rerun()
    else:
        st.success(f"🤖 Active: {st.session_state.selected_agent.replace('_', ' ').title()} Agent")
        if st.button("🔄 Change Agent", key="change_agent_btn"):
            st.session_state.agent_locked = False
            st.session_state.selected_agent = None
            st.rerun()

def display_chat_messages():
    """Display chat messages with enhanced formatting"""
    if not st.session_state.chat_history:
        # Show welcome message with examples
        if st.session_state.selected_agent:
            agent_examples = {
                "data_analysis": [
                    "Analyze this CSV file and show insights",
                    "Calculate the average of 125000, 135000, 145000",
                    "Show me the first 5 rows and data types"
                ],
                "automation": [
                    "Process this file and clean the data",
                    "Generate a Python script to organize files",
                    "Create a workflow for data processing"
                ],
                "content_creation": [
                    "Write a blog post about AI trends",
                    "Create LinkedIn content about data science",
                    "Generate marketing copy for an AI product"
                ],
                "customer_service": [
                    "How do I use the data analysis features?",
                    "What can the automation agent do?",
                    "Help me choose the right agent"
                ]
            }
            
            examples = agent_examples.get(st.session_state.selected_agent, [])
            
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem; color: #6b7280;">
                <h4 style="color: #374151;">👋 Ready to help with {st.session_state.selected_agent.replace('_', ' ').title()}!</h4>
                <p>Try one of these examples:</p>
            </div>
            """, unsafe_allow_html=True)
            
            for i, example in enumerate(examples):
                if st.button(f"💡 {example}", key=f"example_{i}"):
                    process_and_display_user_message(example)
        else:
            st.info("Select an agent above to start chatting.")
    else:
        # Display actual chat messages
        for message in st.session_state.chat_history:
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

def display_chat_interface():
    """Display the main chat interface"""
    st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
    st.header("💬 Chat with MultiAgentAI21")

    # Agent selection
    display_agent_selection()

    # Chat interface (only if agent selected)
    if st.session_state.agent_locked and st.session_state.selected_agent:
        # Show agent info
        agent_capabilities = {
            "data_analysis": "Analyzes data files, performs calculations, generates insights",
            "automation": "Processes files, creates scripts, automates workflows",
            "content_creation": "Creates blog posts, social media content, marketing copy",
            "customer_service": "Provides support, answers questions, offers guidance"
        }
        
        capability = agent_capabilities.get(st.session_state.selected_agent, "")
        if capability:
            st.info(f"🤖 **{st.session_state.selected_agent.replace('_', ' ').title()} Agent** - {capability}")
        
        # Chat container
        st.markdown('<div class="integrated-chat-container">', unsafe_allow_html=True)
        
        # Display messages
        display_chat_messages()
        
        # Input area
        st.markdown('<div class="integrated-input-area">', unsafe_allow_html=True)
        
        # Input controls
        col1, col2, col3 = st.columns([8, 1, 1.5])
        
        with col1:
            user_input = st.text_area(
                "Message",
                placeholder="Type your message here...",
                height=70,
                key="chat_input",
                label_visibility="collapsed"
            )
        
        with col2:
            if st.button("📎", key="attach_btn", help="Attach files"):
                st.session_state.show_file_upload = not st.session_state.show_file_upload
                st.rerun()
        
        with col3:
            send_clicked = st.button("Send 📤", key="send_button", type="primary")
        
        # File upload area
        uploaded_files = None
        if st.session_state.show_file_upload:
            uploaded_files = st.file_uploader(
                "📎 Attach files",
                accept_multiple_files=True,
                key="chat_file_upload",
                type=['csv', 'xlsx', 'xls', 'txt', 'pdf', 'json', 'py', 'js', 'html', 'css', 'md'],
                help="Upload files for processing and analysis"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} file(s) selected")
                for file in uploaded_files:
                    file_size = f"{file.size / 1024:.1f} KB" if file.size < 1024*1024 else f"{file.size / (1024*1024):.1f} MB"
                    st.caption(f"📄 {file.name} ({file_size})")
        
        # Process message
        if send_clicked and (user_input.strip() or uploaded_files):
            process_and_display_user_message(user_input, uploaded_files)
            st.session_state.show_file_upload = False
            st.rerun()
        elif send_clicked:
            st.warning("Please enter a message or upload files.")
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close input area
        st.markdown('</div>', unsafe_allow_html=True)  # Close chat container
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close page container

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

    # Show chats if authenticated
    if is_authenticated():
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
    else:
        st.sidebar.info("🔒 Please log in to see chat history")

def user_profile_sidebar():
    """Display user profile in sidebar"""
    if is_authenticated():
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
    """Main application logic"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Display header
        display_enhanced_header()

        # Initialize agent system
        if st.session_state.agent is None:
            st.session_state.agent = get_agent_system()
            if not st.session_state.agent:
                st.error("❌ Failed to initialize agent system")
                return

        # Sidebar navigation
        st.sidebar.title("🧭 Navigation")
        
        # User profile and chat history
        user_profile_sidebar()
        display_chat_history_sidebar()

        # Page selection
        page = st.sidebar.radio(
            "Select a page",
            ["🤖 Agent Chat", "📊 Data Analysis", "📚 Help & Examples"],
            key="navigation_radio"
        )

        # Display selected page
        if page == "🤖 Agent Chat":
            display_chat_interface()
        elif page == "📊 Data Analysis":
            st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
            st.header("📊 Data Analysis Dashboard")
            st.info("💡 Use the Agent Chat with Data Analysis Agent for comprehensive data analysis")
            st.markdown("Upload your CSV files in the chat interface and ask for analysis!")
            st.markdown('</div>', unsafe_allow_html=True)
        elif page == "📚 Help & Examples":
            st.markdown('<div class="page-content-container">', unsafe_allow_html=True)
            st.header("📚 Help & Examples")
            
            st.subheader("🤖 Agent Capabilities")
            
            with st.expander("📊 Data Analysis Agent", expanded=True):
                st.write("**What it actually does:**")
                st.write("• Analyzes uploaded CSV/Excel files with real data")
                st.write("• Performs actual mathematical calculations")
                st.write("• Generates statistical insights and summaries")
                st.write("• Creates data visualizations")
                
                st.write("**Example requests:**")
                st.code("Show me the first 5 rows, shape, and data types")
                st.code("Calculate the average of 125000, 135000, 145000")
                st.code("Analyze this sales data and provide insights")
            
            with st.expander("🤖 Automation Agent"):
                st.write("**What it actually does:**")
                st.write("• Processes uploaded files and performs operations")
                st.write("• Generates working Python/Bash scripts")
                st.write("• Creates detailed automation workflows")
                st.write("• Organizes and converts files")
                
                st.write("**Example requests:**")
                st.code("Process this CSV file and clean the data")
                st.code("Generate a Python script to organize files")
                st.code("Create a workflow for data processing")
            
            with st.expander("📝 Content Creation Agent"):
                st.write("**What it actually does:**")
                st.write("• Creates complete, ready-to-use content")
                st.write("• Writes full blog posts and articles")
                st.write("• Generates social media content with hashtags")
                st.write("• Produces marketing copy and email content")
                
                st.write("**Example requests:**")
                st.code("Write a blog post about AI trends in 2024")
                st.code("Create LinkedIn content about data science")
                st.code("Generate marketing copy for an AI product")
            
            with st.expander("💬 Customer Service Agent"):
                st.write("**What it actually does:**")
                st.write("• Provides helpful support and guidance")
                st.write("• Answers questions about platform features")
                st.write("• Helps choose the right agent for tasks")
                st.write("• Offers troubleshooting assistance")
                
                st.write("**Example requests:**")
                st.code("How do I analyze data with this platform?")
                st.code("Which agent should I use for my project?")
                st.code("Help me with file upload issues")
            
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