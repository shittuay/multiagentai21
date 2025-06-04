# File: src/agent_core.py
import os
import json
import time
import mimetypes
from enum import Enum
from typing import Dict, List, Any, Optional, Union, BinaryIO
from dataclasses import dataclass
from abc import ABC, abstractmethod
import tempfile
import shutil
from pathlib import Path

import google.generativeai as genai
from google.cloud import bigquery
import pandas as pd
from .data_analysis import DataAnalyzer


class FileType(Enum):
    """Supported file types for processing"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    UNKNOWN = "unknown"


@dataclass
class FileData:
    """Data class for uploaded file information"""
    filename: str
    file_type: FileType
    mime_type: str
    size: int
    temp_path: Optional[str] = None
    content: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentType(Enum):
    """Enum for different agent types based on the four categories"""
    AUTOMATION = "automation"  # 🧠 Automation of Complex Processes
    DATA_ANALYSIS = "data_analysis"  # 📊 Data Analysis and Insights
    CUSTOMER_SERVICE = "customer_service"  # 🤝 Customer Service and Engagement
    CONTENT_CREATION = "content_creation"  # 📱 Content Creation and Generation


@dataclass
class AgentResponse:
    """Standardized response format for all agents"""
    success: bool
    agent_type: str
    content: str
    data: Optional[Dict[str, Any]] = None
    files: Optional[List[FileData]] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None


class BaseAgent(ABC):
    """Abstract base class for all specialized agents"""
    
    def __init__(self, agent_type: AgentType, model_name: str = "models/gemini-1.5-pro-002"):
        """Initialize the base agent with type and model"""
        self.agent_type = agent_type
        self.model_name = model_name
        self.model = None
        self.temp_dir = None
        self.data_analyzer = None
        self._initialize_temp_dir()
        self._initialize_gemini()
        self._initialize_data_analyzer()
    
    def _initialize_gemini(self):
        """Initialize Gemini AI model"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            print(f"Initializing Gemini with API key: {api_key[:8]}...")
            genai.configure(api_key=api_key)
            
            # Use the confirmed working model
            model_name = self.model_name
            try:
                print(f"Using model: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                # Test the model
                test_response = self.model.generate_content("Test")
                if test_response and hasattr(test_response, 'text'):
                    print(f"Successfully initialized model: {model_name}")
                    return
                else:
                    raise ValueError(f"Model {model_name} did not return a valid response")
                
            except Exception as e:
                print(f"Error initializing model {model_name}: {e}")
                raise ValueError(f"Failed to initialize model {model_name}: {e}")
                
        except Exception as e:
            print(f"Failed to initialize Gemini: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            raise
    
    def _initialize_temp_dir(self):
        """Initialize temporary directory for file processing"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix=f"agent_{self.agent_type.value}_")
            print(f"Initialized temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Failed to initialize temporary directory: {e}")
            self.temp_dir = None
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory and files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"Failed to clean up temporary directory: {e}")
    
    def _get_file_type(self, filename: str, mime_type: str) -> FileType:
        """Determine file type from filename and mime type"""
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
        
        if mime_type:
            if mime_type.startswith('image/'):
                return FileType.IMAGE
            elif mime_type.startswith('video/'):
                return FileType.VIDEO
            elif mime_type.startswith('audio/'):
                return FileType.AUDIO
            elif mime_type in ['application/pdf', 'application/msword', 
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return FileType.DOCUMENT
            elif mime_type in ['application/vnd.ms-excel',
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             'text/csv']:
                return FileType.SPREADSHEET
            elif mime_type.startswith('text/'):
                return FileType.TEXT
        
        # Fallback to extension-based detection
        ext = Path(filename).suffix.lower()
        if ext in ['.txt', '.md', '.py', '.js', '.html', '.css']:
            return FileType.TEXT
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return FileType.IMAGE
        elif ext in ['.mp4', '.avi', '.mov', '.wmv']:
            return FileType.VIDEO
        elif ext in ['.mp3', '.wav', '.ogg']:
            return FileType.AUDIO
        elif ext in ['.pdf', '.doc', '.docx']:
            return FileType.DOCUMENT
        elif ext in ['.xls', '.xlsx', '.csv']:
            return FileType.SPREADSHEET
        
        return FileType.UNKNOWN
    
    def process_file(self, file: BinaryIO, filename: str, mime_type: Optional[str] = None) -> FileData:
        """Process uploaded file and return FileData object"""
        try:
            # Create temporary file
            if not self.temp_dir:
                raise ValueError("Temporary directory not initialized")
            
            temp_path = os.path.join(self.temp_dir, filename)
            with open(temp_path, 'wb') as f:
                f.write(file.read())
            
            # Get file information
            file_size = os.path.getsize(temp_path)
            file_type = self._get_file_type(filename, mime_type)
            
            # Process file based on type
            content = None
            metadata = {}
            
            if file_type == FileType.TEXT:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                metadata['line_count'] = len(content.splitlines())
                metadata['word_count'] = len(content.split())
            
            elif file_type == FileType.SPREADSHEET:
                if filename.endswith('.csv'):
                    content = pd.read_csv(temp_path)
                else:
                    content = pd.read_excel(temp_path)
                metadata['row_count'] = len(content)
                metadata['column_count'] = len(content.columns)
            
            elif file_type in [FileType.IMAGE, FileType.VIDEO, FileType.AUDIO]:
                # For media files, we'll just store the path and basic metadata
                metadata['duration'] = None  # Would implement media duration extraction
                metadata['dimensions'] = None  # Would implement image/video dimension extraction
            
            return FileData(
                filename=filename,
                file_type=file_type,
                mime_type=mime_type or mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                size=file_size,
                temp_path=temp_path,
                content=content,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            raise
    
    def cleanup_files(self):
        """Clean up any processed files"""
        self._cleanup_temp_dir()
    
    @abstractmethod
    def process_request(self, request: str, context: Optional[Dict] = None, files: Optional[List[FileData]] = None) -> AgentResponse:
        """Abstract method for processing requests with optional file handling"""
        pass
    
    def _generate_content(self, prompt: str, files: Optional[List[FileData]] = None) -> str:
        """Generate content using Gemini AI with optional file context"""
        try:
            if not self.model:
                raise ValueError("Gemini model not initialized")
            
            # If files are provided, add file context to the prompt
            if files:
                file_context = "\n\nFile Context:\n"
                for file in files:
                    file_context += f"- {file.filename} ({file.file_type.value}): "
                    if file.content is not None:
                        if isinstance(file.content, pd.DataFrame):
                            file_context += f"DataFrame with {len(file.content)} rows and {len(file.content.columns)} columns\n"
                        else:
                            file_context += f"{str(file.content)[:200]}...\n"
                    else:
                        file_context += f"Size: {file.size} bytes\n"
                prompt = f"{prompt}\n{file_context}"
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    def __del__(self):
        """Cleanup when agent is destroyed"""
        self.cleanup_files()
    
    def _initialize_data_analyzer(self):
        """Initialize the data analyzer with the agent's temp directory"""
        self.data_analyzer = DataAnalyzer(temp_dir=self.temp_dir)
    
    def process_request(self, request: str, files: Optional[List[FileData]] = None) -> AgentResponse:
        """Process a request with optional file data"""
        try:
            # Handle file analysis if files are provided
            if files:
                analysis_results = []
                for file in files:
                    if file.file_type in [FileType.TEXT, FileType.SPREADSHEET, FileType.DOCUMENT]:
                        result = self.data_analyzer.analyze_file(file.temp_path)
                        analysis_results.append({
                            'file_name': file.filename,
                            'analysis': result
                        })
                
                if analysis_results:
                    # Format analysis results for the model
                    analysis_summary = "File Analysis Results:\n"
                    for result in analysis_results:
                        analysis_summary += f"\nFile: {result['file_name']}\n"
                        if 'error' in result['analysis']:
                            analysis_summary += f"Error: {result['analysis']['error']}\n"
                        else:
                            analysis_summary += json.dumps(result['analysis'], indent=2)
                    
                    # Include analysis in the request
                    request = f"{request}\n\n{analysis_summary}"
            
            # Process the request with the model
            response = self._process_with_model(request)
            
            # Clean up after processing
            if self.data_analyzer:
                self.data_analyzer.cleanup()
            
            return response
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Error processing request: {str(e)}",
                error=str(e)
            )
    
    def cleanup(self):
        """Clean up resources"""
        if self.data_analyzer:
            self.data_analyzer.cleanup()
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class AutomationAgent(BaseAgent):
    """🧠 Agent for Automation of Complex Processes"""
    
    def __init__(self):
        super().__init__(AgentType.AUTOMATION)
        self.bigquery_client = None
        self._initialize_bigquery()
    
    def _initialize_bigquery(self):
        """Initialize BigQuery client for process automation"""
        try:
            self.bigquery_client = bigquery.Client()
        except Exception as e:
            print(f"BigQuery initialization failed: {e}")
    
    def process_request(self, request: str, context: Optional[Dict] = None, files: Optional[List[FileData]] = None) -> AgentResponse:
        """Process automation requests with optional file handling"""
        start_time = time.time()
        
        try:
            # Handle simple greetings and basic interactions
            request_lower = request.lower().strip()
            if request_lower in ['hi', 'hello', 'hey', 'greetings']:
                greeting_prompt = f"""
                As an automation expert, provide a friendly greeting that:
                1. Acknowledges the user
                2. Briefly mentions your automation capabilities
                3. Invites them to ask about automation tasks
                
                Keep it concise and natural, like a real conversation.
                """
                
                content = self._generate_content(greeting_prompt)
                return AgentResponse(
                    success=True,
                    agent_type=self.agent_type.value,
                    content=content,
                    execution_time=time.time() - start_time
                )
            
            # For actual automation requests, provide a human-readable analysis
            analysis_prompt = f"""
            Analyze this automation request and provide a clear, human-readable response:
            Request: {request}
            
            Structure your response in a conversational way that:
            1. Starts with a brief overview of what the automation will do
            2. Explains the main steps in simple terms
            3. Describes how each step can be automated
            4. Lists the tools and technologies needed in plain language
            5. Suggests a practical approach to implementation
            6. Explains how to measure success
            
            Keep the technical details but explain them in a way that's easy to understand.
            Use bullet points and clear headings to organize the information.
            Avoid JSON formatting - write it as a natural, well-structured response.
            """
            
            content = self._generate_content(analysis_prompt, files)
            
            # Execute specific automation tasks and get data
            automation_data = self._execute_automation_task(request, context, files)
            
            # Add a friendly conclusion
            conclusion_prompt = f"""
            Based on the automation analysis above, provide a brief, encouraging conclusion that:
            1. Summarizes the key benefits
            2. Acknowledges any challenges
            3. Offers next steps or suggestions
            4. Maintains a helpful, supportive tone
            
            Keep it concise and actionable.
            """
            
            conclusion = self._generate_content(conclusion_prompt)
            content = f"{content}\n\n{conclusion}"
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=True,
                agent_type=self.agent_type.value,
                content=content,
                data=automation_data,
                files=files,  # Include processed files in response
                execution_time=execution_time
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                agent_type=self.agent_type.value,
                content="I apologize, but I encountered an error while processing your request. Please try again or rephrase your question.",
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _execute_automation_task(self, request: str, context: Optional[Dict], files: Optional[List[FileData]] = None) -> Dict[str, Any]:
        """Execute specific automation tasks with optional file handling"""
        automation_data = {
            "task_type": "process_automation",
            "steps_identified": [],
            "tools_required": [],
            "estimated_time_savings": "Unknown",
            "processed_files": []
        }
        
        # Process any uploaded files
        if files:
            for file in files:
                file_info = {
                    "filename": file.filename,
                    "type": file.file_type.value,
                    "size": file.size,
                    "metadata": file.metadata
                }
                automation_data["processed_files"].append(file_info)
        
        # Add logic for specific automation tasks
        if "workflow" in request.lower():
            automation_data["steps_identified"] = [
                "Input validation",
                "Process routing",
                "Automated execution",
                "Result verification",
                "Notification dispatch"
            ]
            automation_data["tools_required"] = ["API integration", "Database", "Notification system"]
        
        return automation_data


class DataAnalysisAgent(BaseAgent):
    """📊 Agent for Data Analysis and Insights"""
    
    def __init__(self):
        super().__init__(AgentType.DATA_ANALYSIS)
        self.bigquery_client = None
        self._initialize_bigquery()
    
    def _initialize_bigquery(self):
        """Initialize BigQuery for data analysis"""
        try:
            self.bigquery_client = bigquery.Client()
        except Exception as e:
            print(f"BigQuery initialization failed: {e}")
    
    def process_request(self, request: str, context: Optional[Dict] = None, files: Optional[List[FileData]] = None) -> AgentResponse:
        """Process data analysis requests with optional file handling"""
        start_time = time.time()
        
        try:
            # Generate analysis insights
            analysis_prompt = f"""
            Provide comprehensive data analysis for this request:
            Request: {request}
            
            Include:
            1. Data requirements
            2. Analysis methodology
            3. Key metrics to track
            4. Visualization suggestions
            5. Actionable insights
            6. Potential SQL queries (if applicable)
            
            Make it practical and implementable.
            """
            
            content = self._generate_content(analysis_prompt, files)
            
            # Perform actual data analysis if data is provided
            analysis_results = self._perform_data_analysis(request, context, files)
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=True,
                agent_type=self.agent_type.value,
                content=content,
                data=analysis_results,
                files=files,  # Include processed files in response
                execution_time=execution_time
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                agent_type=self.agent_type.value,
                content="",
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _perform_data_analysis(self, request: str, context: Optional[Dict], files: Optional[List[FileData]] = None) -> Dict[str, Any]:
        """Perform actual data analysis"""
        analysis_results = {
            "analysis_type": "descriptive",
            "data_sources": [],
            "key_findings": [],
            "recommendations": [],
            "confidence_level": "medium"
        }
        
        # Add sample analysis logic
        if context and "data" in context:
            analysis_results["data_sources"] = ["provided_dataset"]
            analysis_results["key_findings"] = [
                "Data quality assessment completed",
                "Statistical summary generated",
                "Outliers identified"
            ]
        
        # Process any uploaded files
        if files:
            for file in files:
                file_info = {
                    "filename": file.filename,
                    "type": file.file_type.value,
                    "size": file.size,
                    "metadata": file.metadata
                }
                analysis_results["data_sources"].append(file_info)
        
        return analysis_results
    
    def execute_sql_query(self, query: str) -> Optional[pd.DataFrame]:
        """Execute SQL query using BigQuery"""
        if not self.bigquery_client:
            return None
        
        try:
            df = self.bigquery_client.query(query).to_dataframe()
            return df
        except Exception as e:
            print(f"SQL execution error: {e}")
            return None


class CustomerServiceAgent(BaseAgent):
    """🤝 Agent for Customer Service and Engagement"""
    
    def __init__(self):
        super().__init__(AgentType.CUSTOMER_SERVICE)
        self.conversation_history = []
        self.customer_context = {}
    
    def process_request(self, request: str, context: Optional[Dict] = None, files: Optional[List[FileData]] = None) -> AgentResponse:
        """Process customer service requests with optional file handling"""
        start_time = time.time()
        
        try:
            # Update customer context
            if context:
                self.customer_context.update(context)
            
            # Generate customer service response
            service_prompt = f"""
            As a professional customer service agent, respond to this customer inquiry:
            Customer Request: {request}
            
            Context: {self.customer_context}
            
            Provide:
            1. Empathetic acknowledgment
            2. Clear solution or next steps
            3. Additional resources if helpful
            4. Follow-up questions if needed
            
            Maintain a professional, helpful, and friendly tone.
            """
            
            content = self._generate_content(service_prompt, files)
            
            # Log interaction
            interaction_data = self._log_customer_interaction(request, content)
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=True,
                agent_type=self.agent_type.value,
                content=content,
                data=interaction_data,
                files=files,  # Include processed files in response
                execution_time=execution_time
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                agent_type=self.agent_type.value,
                content="I apologize, but I'm experiencing technical difficulties. Please try again or contact our support team.",
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _log_customer_interaction(self, request: str, response: str) -> Dict[str, Any]:
        """Log customer interaction for analysis"""
        interaction = {
            "timestamp": time.time(),
            "customer_request": request[:100],  # Truncate for privacy
            "response_length": len(response),
            "sentiment": "neutral",  # Would implement sentiment analysis
            "resolved": True  # Would implement resolution detection
        }
        
        self.conversation_history.append(interaction)
        
        return {
            "interaction_logged": True,
            "conversation_length": len(self.conversation_history),
            "customer_satisfaction_score": "pending"
        }


class ContentCreationAgent(BaseAgent):
    """📱 Agent for Content Creation and Generation"""
    
    def __init__(self):
        super().__init__(AgentType.CONTENT_CREATION)
        self.content_templates = {
            "blog": "Create an engaging blog post about {topic}",
            "social": "Create social media content for {platform} about {topic}",
            "email": "Create a professional email about {topic}",
            "presentation": "Create presentation content about {topic}",
            "marketing": "Create marketing copy for {product} targeting {audience}"
        }
    
    def process_request(self, request: str, context: Optional[Dict] = None, files: Optional[List[FileData]] = None) -> AgentResponse:
        """Process content creation requests with optional file handling"""
        start_time = time.time()
        
        try:
            # Determine content type and parameters
            content_params = self._analyze_content_request(request, context)
            
            # Generate content
            creation_prompt = f"""
            Create high-quality content based on this request:
            Request: {request}
            
            Content Parameters:
            - Type: {content_params.get('type', 'general')}
            - Target Audience: {content_params.get('audience', 'general')}
            - Tone: {content_params.get('tone', 'professional')}
            - Length: {content_params.get('length', 'medium')}
            
            Requirements:
            1. Engaging and well-structured
            2. Appropriate for the target audience
            3. Clear call-to-action (if applicable)
            4. SEO-friendly (if applicable)
            5. Brand-consistent tone
            
            Provide the complete content ready for use.
            """
            
            content = self._generate_content(creation_prompt, files)
            
            # Add content metadata
            content_data = self._generate_content_metadata(content, content_params)
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=True,
                agent_type=self.agent_type.value,
                content=content,
                data=content_data,
                files=files,  # Include processed files in response
                execution_time=execution_time
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                agent_type=self.agent_type.value,
                content="",
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _analyze_content_request(self, request: str, context: Optional[Dict]) -> Dict[str, str]:
        """Analyze content request to determine parameters"""
        params = {
            "type": "general",
            "audience": "general",
            "tone": "professional",
            "length": "medium"
        }
        
        # Simple keyword analysis
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["blog", "article", "post"]):
            params["type"] = "blog"
        elif any(word in request_lower for word in ["email", "newsletter"]):
            params["type"] = "email"
        elif any(word in request_lower for word in ["social", "twitter", "facebook", "instagram"]):
            params["type"] = "social"
        elif any(word in request_lower for word in ["presentation", "slides"]):
            params["type"] = "presentation"
        
        if context:
            params.update({k: v for k, v in context.items() if k in params})
        
        return params
    
    def _generate_content_metadata(self, content: str, params: Dict[str, str]) -> Dict[str, Any]:
        """Generate metadata for created content"""
        return {
            "content_type": params.get("type", "general"),
            "word_count": len(content.split()),
            "character_count": len(content),
            "estimated_read_time": max(1, len(content.split()) // 200),  # words per minute
            "content_quality_score": "good",  # Would implement quality assessment
            "seo_keywords": [],  # Would implement keyword extraction
            "sentiment": "neutral"  # Would implement sentiment analysis
        }


class MultiAgentCodingAI:
    """Main orchestrator for the multi-agent system"""
    
    def __init__(self):
        self.agents = {
            AgentType.AUTOMATION: AutomationAgent(),
            AgentType.DATA_ANALYSIS: DataAnalysisAgent(),
            AgentType.CUSTOMER_SERVICE: CustomerServiceAgent(),
            AgentType.CONTENT_CREATION: ContentCreationAgent()
        }
        self.conversation_history = []
    
    def route_request(self, request: str, agent_type: Optional[AgentType] = None, context: Optional[Dict] = None) -> AgentResponse:
        """Route request to appropriate agent or auto-detect"""
        
        if not agent_type:
            agent_type = self._detect_agent_type(request)
        
        if agent_type not in self.agents:
            return AgentResponse(
                success=False,
                agent_type="unknown",
                content="",
                error_message=f"Unknown agent type: {agent_type}"
            )
        
        # Process request with selected agent
        response = self.agents[agent_type].process_request(request, context)
        
        # Log conversation
        self._log_conversation(request, response, agent_type)
        
        return response
    
    def _detect_agent_type(self, request: str) -> AgentType:
        """Auto-detect which agent should handle the request"""
        request_lower = request.lower()
        
        # Keywords for each agent type
        automation_keywords = ["automate", "workflow", "process", "schedule", "trigger", "pipeline"]
        data_keywords = ["analyze", "data", "report", "chart", "sql", "query", "insights", "metrics"]
        customer_keywords = ["help", "support", "issue", "problem", "question", "customer", "service"]
        content_keywords = ["write", "create", "content", "blog", "post", "email", "marketing", "copy"]
        
        # Count keyword matches
        scores = {
            AgentType.AUTOMATION: sum(1 for word in automation_keywords if word in request_lower),
            AgentType.DATA_ANALYSIS: sum(1 for word in data_keywords if word in request_lower),
            AgentType.CUSTOMER_SERVICE: sum(1 for word in customer_keywords if word in request_lower),
            AgentType.CONTENT_CREATION: sum(1 for word in content_keywords if word in request_lower)
        }
        
        # Return agent type with highest score, default to content creation
        return max(scores.items(), key=lambda x: x[1])[0] if max(scores.values()) > 0 else AgentType.CONTENT_CREATION
    
    def _log_conversation(self, request: str, response: AgentResponse, agent_type: AgentType):
        """Log conversation for analysis and improvement"""
        conversation_entry = {
            "timestamp": time.time(),
            "request": request,
            "agent_type": agent_type.value,
            "success": response.success,
            "execution_time": response.execution_time,
            "error": response.error_message
        }
        
        self.conversation_history.append(conversation_entry)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {}
        for agent_type, agent in self.agents.items():
            status[agent_type.value] = {
                "initialized": agent.model is not None,
                "type": agent_type.value,
                "ready": True
            }
        
        return status
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history[-10:]  # Return last 10 conversations


# Backward compatibility - keep the old class name
class HackathonAgent(MultiAgentCodingAI):
    """Backward compatibility class"""
    
    def generate_content(self, prompt: str) -> str:
        """Generate content using content creation agent"""
        response = self.route_request(prompt, AgentType.CONTENT_CREATION)
        return response.content if response.success else f"Error: {response.error_message}"
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """Process request and return dictionary format"""
        response = self.route_request(request)
        
        return {
            "status": "success" if response.success else "error",
            "generated_content": response.content,
            "agent_type": response.agent_type,
            "execution_time": response.execution_time,
            "data": response.data,
            "error": response.error_message
        }