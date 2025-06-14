"""Firestore database client for storing chat history and other data."""

import logging
import os
import json
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)

class FirestoreClient:
    """Client for interacting with Firestore database."""

    def __init__(self):
        """Initialize Firestore client."""
        self.db = None
        self.chat_collection = None
        self.agent_collection = None
        self.initialized = False
        self._temp_key_file = None

        try:
            # Try to load credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if credentials_json:
                logger.info("Found GOOGLE_APPLICATION_CREDENTIALS_JSON. Writing to temporary file.")
                # Create a temporary file to store the credentials
                self._temp_key_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8')
                self._temp_key_file.write(credentials_json)
                self._temp_key_file.close()
                
                # Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self._temp_key_file.name
                logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set to: {self._temp_key_file.name}")

            self.db = firestore.Client()
            self.chat_collection = self.db.collection('chats')
            self.agent_collection = self.db.collection('agents')
            self.initialized = True
            logger.info("Successfully initialized Firestore client")
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore client: {e}")
            logger.info("Running in offline mode - database operations will be skipped")
        
    def __del__(self):
        """Clean up temporary key file on object destruction."""
        if self._temp_key_file and os.path.exists(self._temp_key_file.name):
            os.remove(self._temp_key_file.name)
            logger.info(f"Cleaned up temporary key file: {self._temp_key_file.name}")

    def save_chat_history(
        self,
        session_id: str,
        request: str,
        response: Dict[str, Any],
        agent_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save a chat interaction to Firestore.
        
        Args:
            session_id: Unique identifier for the chat session
            request: User's request
            response: Agent's response
            agent_type: Type of agent that handled the request
            metadata: Additional metadata about the interaction
            
        Returns:
            Document ID of the saved chat entry
        """
        if not self.initialized:
            logger.debug("Firestore not initialized - skipping chat history save")
            return "offline_mode"
            
        try:
            chat_data = {
                'session_id': session_id,
                'timestamp': datetime.utcnow(),
                'request': request,
                'response': response,
                'agent_type': agent_type,
                'metadata': metadata or {},
                'status': 'completed'
            }
            
            # Add to chats collection
            doc_ref = self.chat_collection.document()
            doc_ref.set(chat_data)
            
            # Update session document with latest interaction
            session_ref = self.db.collection('sessions').document(session_id)
            session_ref.set({
                'last_interaction': datetime.utcnow(),
                'agent_type': agent_type,
                'status': 'active'
            }, merge=True)
            
            logger.info(f"Saved chat history for session {session_id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
            return "error"

    def get_chat_history(
        self,
        session_id: str,
        limit: int = 50,
        start_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve chat history for a session.
        
        Args:
            session_id: Session ID to retrieve history for
            limit: Maximum number of interactions to return
            start_after: Document ID to start after (for pagination)
            
        Returns:
            List of chat interactions
        """
        if not self.initialized:
            logger.debug("Firestore not initialized - returning empty chat history")
            return []
            
        try:
            query = self.chat_collection.where(
                filter=FieldFilter("session_id", "==", session_id)
            ).order_by("timestamp", direction=firestore.Query.DESCENDING)
            
            if start_after:
                start_doc = self.chat_collection.document(start_after).get()
                if start_doc.exists:
                    query = query.start_after(start_doc)
            
            docs = query.limit(limit).stream()
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []

    def get_agent_stats(
        self,
        agent_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistics for a specific agent type.
        
        Args:
            agent_type: Type of agent to get stats for
            start_date: Start date for stats period
            end_date: End date for stats period
            
        Returns:
            Dictionary containing agent statistics
        """
        if not self.initialized:
            logger.debug("Firestore not initialized - returning empty stats")
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0,
                'total_response_time': 0
            }
            
        try:
            query = self.chat_collection.where(
                filter=FieldFilter("agent_type", "==", agent_type)
            )
            
            if start_date:
                query = query.where(
                    filter=FieldFilter("timestamp", ">=", start_date)
                )
            if end_date:
                query = query.where(
                    filter=FieldFilter("timestamp", "<=", end_date)
                )
            
            docs = query.stream()
            
            stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0,
                'total_response_time': 0
            }
            
            for doc in docs:
                data = doc.to_dict()
                stats['total_requests'] += 1
                
                if data.get('response', {}).get('success'):
                    stats['successful_requests'] += 1
                else:
                    stats['failed_requests'] += 1
                
                if 'execution_time' in data.get('response', {}):
                    stats['total_response_time'] += data['response']['execution_time']
            
            if stats['total_requests'] > 0:
                stats['average_response_time'] = (
                    stats['total_response_time'] / stats['total_requests']
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0,
                'total_response_time': 0
            }

    def update_agent_status(
        self,
        agent_type: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update the status of an agent (e.g., for health checks).
        
        Args:
            agent_type: Type of agent
            status: Current status (e.g., 'healthy', 'unhealthy')
            metadata: Additional metadata
        """
        if not self.initialized:
            logger.debug("Firestore not initialized - skipping agent status update")
            return
            
        try:
            agent_doc_ref = self.agent_collection.document(agent_type)
            agent_doc_ref.set({
                'last_updated': datetime.utcnow(),
                'status': status,
                'metadata': metadata or {}
            }, merge=True)
            logger.debug(f"Updated status for agent {agent_type} to {status}")
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")

    def get_active_sessions(
        self,
        agent_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get a list of active chat sessions, optionally filtered by agent type.
        
        Args:
            agent_type: Optional agent type to filter sessions by
            limit: Maximum number of sessions to return
            
        Returns:
            List of active sessions
        """
        if not self.initialized:
            logger.debug("Firestore not initialized - returning empty active sessions")
            return []
            
        try:
            query = self.db.collection('sessions').where(
                filter=FieldFilter("status", "==", "active")
            ).order_by('last_interaction', direction=firestore.Query.DESCENDING)
            
            if agent_type:
                query = query.where(
                    filter=FieldFilter("agent_type", "==", agent_type)
                )
            
            docs = query.limit(limit).stream()
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return [] 