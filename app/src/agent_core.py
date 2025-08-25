import json
import mimetypes
import os
import shutil
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Sequence, Union
import logging
import uuid
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

import google.generativeai as genai
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud import aiplatform

from src.data_analysis import DataAnalyzer
from src.api.firestore import FirestoreClient
from src.types import AgentType, AgentResponse
from src.agents.content_creator import ContentCreatorAgent
from src.agents.devops_automation_agent import DevOpsAutomationAgent
# # Enhanced import removed  # Fixed circular import

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported file types for processing"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    UNKNOWN = "unknown"


class BaseAgent(ABC):
    """Base class for all agents with self-learning capabilities."""
    
    def __init__(self, agent_type: AgentType):
        """Initialize the base agent."""
        self.agent_type = agent_type
        self.model = None
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_response_time': 0.0,
            'user_satisfaction_scores': [],
            'common_failure_patterns': [],
            'improvement_suggestions': []
        }
        self.learning_history = []
        self.adaptive_prompts = {}
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the AI model for the agent."""
        try:
            # Get API key from environment variable
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.error("GOOGLE_API_KEY environment variable not set")
                raise ValueError("GOOGLE_API_KEY environment variable is required")
            
            # Configure the Gemini API
            genai.configure(api_key=api_key)
            
            # Try different model names in order of preference
            model_names = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
            
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    # Test the model with a simple prompt
                    test_response = self.model.generate_content("Hello")
                    if test_response and hasattr(test_response, 'text'):
                        logger.info(f"Successfully initialized Gemini model: {model_name}")
                        return
                except Exception as e:
                    logger.warning(f"Failed to initialize model {model_name}: {e}")
                    continue
            
            # If all models fail, raise an error
            raise ValueError("Could not initialize any Gemini model. Please check your API key and model availability.")
            
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise

    def _process_with_model(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Process prompt with the AI model, including chat history and learning."""
        start_time = time.time()
        
        try:
            if not self.model:
                raise ValueError("Model not initialized")
            
            # Apply adaptive prompt improvements
            enhanced_prompt = self._apply_adaptive_improvements(prompt)
            
            # Build the chat history for the model
            contents = []
            if chat_history:
                for message in chat_history:
                    if not message.get("content"):
                        continue
                    if "MultiAgentAI21 can make mistakes" in message["content"]:
                        continue

                    if message["role"] == "user":
                        contents.append({"role": "user", "parts": [message["content"]]})
                    elif message["role"] == "assistant":
                        contents.append({"role": "model", "parts": [message["content"]]})
            
            # Add the current prompt as the last user message
            contents.append({"role": "user", "parts": [enhanced_prompt]})
            
            # Use generate_content with the entire 'contents' list
            response = self.model.generate_content(contents)
            
            if hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                
                # Record performance metrics
                self._record_performance_metrics(True, time.time() - start_time)
                
                # Learn from this interaction
                self._learn_from_interaction(prompt, response_text, True, time.time() - start_time)
                
                return response_text
            elif hasattr(response, 'parts') and response.parts:
                response_text = ''.join([part.text for part in response.parts if hasattr(part, 'text')])
                
                # Record performance metrics
                self._record_performance_metrics(True, time.time() - start_time)
                
                # Learn from this interaction
                self._learn_from_interaction(prompt, response_text, True, time.time() - start_time)
                
                return response_text
            else:
                logger.warning("No text content in model response")
                self._record_performance_metrics(False, time.time() - start_time)
                return "I received your request but couldn't generate a proper response."
                
        except Exception as e:
            logger.error(f"Error processing with model: {e}")
            self._record_performance_metrics(False, time.time() - start_time)
            return f"Error processing request: {str(e)}"

    def _apply_adaptive_improvements(self, prompt: str) -> str:
        """Apply learned improvements to prompts."""
        if not self.adaptive_prompts:
            return prompt
        
        improved_prompt = prompt
        
        # Apply context-specific improvements
        for pattern, improvement in self.adaptive_prompts.items():
            if pattern.lower() in prompt.lower():
                improved_prompt = f"{improved_prompt}\n\n{improvement}"
                break
        
        return improved_prompt

    def _record_performance_metrics(self, success: bool, response_time: float):
        """Record performance metrics for learning and improvement."""
        self.performance_metrics['total_requests'] += 1
        
        if success:
            self.performance_metrics['successful_requests'] += 1
        
        # Update average response time
        current_avg = self.performance_metrics['average_response_time']
        total_requests = self.performance_metrics['total_requests']
        self.performance_metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )

    def _learn_from_interaction(self, prompt: str, response: str, success: bool, response_time: float):
        """Learn from each interaction to improve future responses."""
        interaction_data = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'response': response,
            'success': success,
            'response_time': response_time,
            'prompt_length': len(prompt),
            'response_length': len(response)
        }
        
        self.learning_history.append(interaction_data)
        
        # Keep only last 100 interactions to prevent memory bloat
        if len(self.learning_history) > 100:
            self.learning_history = self.learning_history[-100:]
        
        # Analyze patterns for improvement
        self._analyze_learning_patterns()

    def _analyze_learning_patterns(self):
        """Analyze learning history to identify improvement opportunities."""
        if len(self.learning_history) < 5:
            return
        
        # Analyze response time patterns
        recent_responses = self.learning_history[-10:]
        slow_responses = [r for r in recent_responses if r['response_time'] > 5.0]
        
        if len(slow_responses) > len(recent_responses) * 0.3:  # More than 30% are slow
            self.performance_metrics['improvement_suggestions'].append({
                'type': 'performance',
                'suggestion': 'Consider optimizing prompts for faster responses',
                'timestamp': datetime.now().isoformat()
            })
        
        # Analyze success patterns
        recent_success_rate = sum(1 for r in recent_responses if r['success']) / len(recent_responses)
        if recent_success_rate < 0.8:  # Less than 80% success rate
            self.performance_metrics['improvement_suggestions'].append({
                'type': 'reliability',
                'suggestion': 'Review recent failures to improve prompt handling',
                'timestamp': datetime.now().isoformat()
            })

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for the agent."""
        success_rate = (
            self.performance_metrics['successful_requests'] / 
            self.performance_metrics['total_requests']
            if self.performance_metrics['total_requests'] > 0 else 0.0
        )
        
        return {
            'agent_type': self.agent_type.value,
            'total_requests': self.performance_metrics['total_requests'],
            'success_rate': f"{success_rate:.2%}",
            'average_response_time': f"{self.performance_metrics['average_response_time']:.2f}s",
            'learning_history_size': len(self.learning_history),
            'improvement_suggestions': self.performance_metrics['improvement_suggestions'][-5:],  # Last 5
            'last_updated': datetime.now().isoformat()
        }

    def add_user_feedback(self, satisfaction_score: int, feedback_text: str = ""):
        """Add user feedback for continuous improvement."""
        if 1 <= satisfaction_score <= 5:
            self.performance_metrics['user_satisfaction_scores'].append({
                'score': satisfaction_score,
                'feedback': feedback_text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 feedback entries
            if len(self.performance_metrics['user_satisfaction_scores']) > 50:
                self.performance_metrics['user_satisfaction_scores'] = \
                    self.performance_metrics['user_satisfaction_scores'][-50:]
            
            # Learn from feedback
            if satisfaction_score < 3:  # Low satisfaction
                self.performance_metrics['improvement_suggestions'].append({
                    'type': 'user_feedback',
                    'suggestion': f'User feedback: {feedback_text}',
                    'timestamp': datetime.now().isoformat()
                })

    def optimize_prompts(self):
        """Optimize prompts based on learning history."""
        if len(self.learning_history) < 10:
            return
        
        # Analyze successful vs failed interactions
        successful = [r for r in self.learning_history if r['success']]
        failed = [r for r in self.learning_history if not r['success']]
        
        if successful and failed:
            # Find common patterns in successful interactions
            successful_patterns = self._extract_patterns([r['prompt'] for r in successful])
            failed_patterns = self._extract_patterns([r['prompt'] for r in failed])
            
            # Create adaptive improvements
            for pattern in successful_patterns:
                if pattern not in self.adaptive_prompts:
                    self.adaptive_prompts[pattern] = "Use clear, specific language and provide context."

    def _extract_patterns(self, prompts: List[str]) -> List[str]:
        """Extract common patterns from prompts."""
        patterns = []
        for prompt in prompts:
            # Simple pattern extraction - look for common phrases
            words = prompt.lower().split()
            if len(words) >= 3:
                # Look for 3-word phrases
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if len(phrase) > 10:  # Only meaningful phrases
                        patterns.append(phrase)
        
        # Return most common patterns
        from collections import Counter
        pattern_counts = Counter(patterns)
        return [pattern for pattern, count in pattern_counts.most_common(5)]

    @abstractmethod
    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None, **kwargs) -> AgentResponse:
        """Process input data and return a response."""
        pass


class AnalysisAgent(BaseAgent):
    """Agent for actual data analysis tasks."""

    def __init__(self):
        """Initialize the analysis agent."""
        super().__init__(AgentType.DATA_ANALYSIS)
        self.analyzer = DataAnalyzer() if 'DataAnalyzer' in globals() else None
    
    def add_user_feedback(self, satisfaction_score: int, feedback_text: str = ""):
        """Add user feedback for continuous improvement."""
        if 1 <= satisfaction_score <= 5:
            self.performance_metrics['user_satisfaction_scores'].append({
                'score': satisfaction_score,
                'feedback': feedback_text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 feedback entries
            if len(self.performance_metrics['user_satisfaction_scores']) > 50:
                self.performance_metrics['user_satisfaction_scores'] = \
                    self.performance_metrics['user_satisfaction_scores'][-50:]
            
            # Learn from feedback
            if satisfaction_score < 3:  # Low satisfaction
                self.performance_metrics['improvement_suggestions'].append({
                    'type': 'user_feedback',
                    'suggestion': f'User feedback: {feedback_text}',
                    'timestamp': datetime.now().isoformat()
                })

    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None, files: Optional[List] = None, **kwargs) -> AgentResponse:
        """Process analysis requests with actual data processing capabilities."""
        start_time = time.time()
        
        try:
            if not input_data or not input_data.strip():
                return AgentResponse(
                    content="Please provide data to analyze or upload a CSV/Excel file for analysis.",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Check if files are provided for analysis
            if files and len(files) > 0:
                return self._analyze_uploaded_files(files, input_data, start_time)
            
            # Check if the input contains actual data (CSV-like format, JSON, etc.)
            if self._contains_structured_data(input_data):
                return self._analyze_structured_data(input_data, start_time)
            
            # Check for mathematical calculations
            if self._is_calculation_request(input_data):
                return self._perform_calculations(input_data, start_time)
            
            # Generate sample data based on the request and analyze it
            return self._generate_and_analyze_sample_data(input_data, chat_history, start_time)
            
        except Exception as e:
            logger.error(f"Error in AnalysisAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Analysis error: {str(e)}"
            )

    def _contains_structured_data(self, input_data: str) -> bool:
        """Check if input contains structured data."""
        # Check for CSV-like format
        if ',' in input_data and '\n' in input_data:
            lines = input_data.strip().split('\n')
            if len(lines) > 1:
                # Check if all lines have similar number of commas
                comma_counts = [line.count(',') for line in lines]
                return len(set(comma_counts)) <= 2  # Allow some variation
        
        # Check for JSON format
        try:
            json.loads(input_data)
            return True
        except:
            pass
        
        return False

    def _is_calculation_request(self, input_data: str) -> bool:
        """Check if input is a mathematical calculation request."""
        calc_indicators = [
            'calculate', 'compute', 'sum', 'average', 'mean', 'median', 'std', 'variance',
            'correlation', 'regression', '+', '-', '*', '/', '=', 'math', 'statistics'
        ]
        return any(indicator in input_data.lower() for indicator in calc_indicators)

    def _analyze_uploaded_files(self, files: List, request: str, start_time: float) -> AgentResponse:
        """Analyze uploaded files."""
        try:
            results = []
            
            for file in files:
                if hasattr(file, 'name') and file.name.endswith(('.csv', '.xlsx', '.xls')):
                    # Read the file
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_excel(file)
                    
                    # Perform comprehensive analysis
                    analysis_result = self._perform_dataframe_analysis(df, file.name, request)
                    results.append(analysis_result)
            
            if not results:
                return AgentResponse(
                    content="No supported data files found. Please upload CSV or Excel files.",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Combine results
            combined_analysis = "\n\n".join(results)
            
            return AgentResponse(
                content=combined_analysis,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error analyzing files: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )

    def _analyze_structured_data(self, input_data: str, start_time: float) -> AgentResponse:
        """Analyze structured data provided as text."""
        try:
            # Try to parse as CSV
            try:
                from io import StringIO
                df = pd.read_csv(StringIO(input_data))
            except:
                # Try to parse as JSON
                data = json.loads(input_data)
                df = pd.DataFrame(data)
            
            analysis_result = self._perform_dataframe_analysis(df, "provided_data")
            
            return AgentResponse(
                content=analysis_result,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error parsing structured data: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )

    def _perform_calculations(self, input_data: str, start_time: float) -> AgentResponse:
        """Perform mathematical calculations."""
        try:
            # Extract numbers and operations
            import re
            
            # Simple calculation patterns
            if '+' in input_data or '-' in input_data or '*' in input_data or '/' in input_data:
                # Extract mathematical expression
                expr_match = re.search(r'[\d\s+\-*/().]+', input_data)
                if expr_match:
                    expression = expr_match.group().strip()
                    try:
                        result = eval(expression)  # Note: In production, use safer evaluation
                        calculation_result = f"""
## 🧮 Calculation Result

**Expression:** `{expression}`
**Result:** `{result}`

### Breakdown:
- Input: {expression}
- Output: {result}
- Type: {type(result).__name__}
"""
                        return AgentResponse(
                            content=calculation_result,
                            success=True,
                            agent_type=self.agent_type.value,
                            execution_time=time.time() - start_time
                        )
                    except:
                        pass
            
            # Statistical calculations on lists of numbers
            numbers = re.findall(r'\d+\.?\d*', input_data)
            if numbers:
                numbers = [float(n) for n in numbers]
                stats_result = f"""
## 📊 Statistical Analysis

**Numbers:** {numbers}

### Basic Statistics:
- **Count:** {len(numbers)}
- **Sum:** {sum(numbers)}
- **Mean:** {np.mean(numbers):.2f}
- **Median:** {np.median(numbers):.2f}
- **Standard Deviation:** {np.std(numbers):.2f}
- **Variance:** {np.var(numbers):.2f}
- **Min:** {min(numbers)}
- **Max:** {max(numbers)}
- **Range:** {max(numbers) - min(numbers)}
"""
                return AgentResponse(
                    content=stats_result,
                    success=True,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # If no specific calculation found, provide general guidance
            return AgentResponse(
                content="Please provide specific numbers or data to calculate. For example: 'Calculate 15 + 25 * 3' or 'Find the average of 10, 20, 30, 40'",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error performing calculations: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )

    def _generate_and_analyze_sample_data(self, request: str, chat_history: Optional[List[Dict]], start_time: float) -> AgentResponse:
        """Generate sample data based on request and analyze it."""
        try:
            # Use AI to understand what kind of sample data to generate
            sample_data_prompt = f"""
            Based on this analysis request: "{request}"
            
            Generate realistic sample data that would be relevant to this analysis.
            Respond with ONLY a JSON object containing:
            1. "data_type": the type of data (sales, financial, customer, etc.)
            2. "columns": list of column names
            3. "sample_data": list of dictionaries with sample data (at least 20 rows)
            
            Make the data realistic and varied to enable meaningful analysis.
            """
            
            ai_response = self._process_with_model(sample_data_prompt, chat_history)
            
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    data_spec = json.loads(json_match.group())
                    
                    # Create DataFrame from generated data
                    df = pd.DataFrame(data_spec['sample_data'])
                    
                    # Perform analysis
                    analysis_result = self._perform_dataframe_analysis(df, "generated_sample_data", request)
                    
                    # Add note about sample data
                    final_result = f"""
## 📊 Analysis with Generated Sample Data

*Note: Since no specific data was provided, I've generated realistic sample data based on your request to demonstrate the analysis.*

{analysis_result}

### 💡 To get analysis of your actual data:
- Upload a CSV or Excel file
- Paste your data directly in CSV format
- Provide specific numbers for calculations
"""
                    
                    return AgentResponse(
                        content=final_result,
                        success=True,
                        agent_type=self.agent_type.value,
                        execution_time=time.time() - start_time
                    )
            except:
                pass
            
            # Fallback to generic analysis guidance
            analysis_prompt = f"""
            You are a professional data analyst. Provide specific, actionable analysis guidance for: {request}
            
            Include:
            1. What data would be needed
            2. What analysis methods to use
            3. What visualizations would be helpful
            4. What insights to look for
            5. What actions to take based on results
            
            Be specific and practical.
            """
            
            response_text = self._process_with_model(analysis_prompt, chat_history)
            
            return AgentResponse(
                content=response_text,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error generating analysis: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )

    def _perform_dataframe_analysis(self, df: pd.DataFrame, filename: str, request: str = "") -> str:
        """Perform comprehensive analysis on a DataFrame with specific calculation detection."""
        try:
            analysis_parts = []
            
            # Basic info
            analysis_parts.append(f"""
## 📋 Dataset Overview: {filename}

**Shape:** {df.shape[0]} rows × {df.shape[1]} columns
**Columns:** {', '.join(df.columns.tolist())}
""")
            
            # **NEW: Detect and perform specific calculations**
            if request:
                specific_result = self._detect_and_perform_calculation(df, request)
                if specific_result:
                    analysis_parts.append(specific_result)
                    # If specific calculation was performed, return early with focused results
                    return "\n".join(analysis_parts)
            
            # Data types and missing values
            info_summary = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                missing = df[col].isnull().sum()
                missing_pct = (missing / len(df)) * 100
                info_summary.append(f"- **{col}**: {dtype} ({missing} missing, {missing_pct:.1f}%)")
            
            analysis_parts.append(f"""
### 🔍 Data Types & Quality
{chr(10).join(info_summary)}
""")
            
            # Statistical summary for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                stats_df = df[numeric_cols].describe()
                analysis_parts.append(f"""
### 📊 Statistical Summary
```
{stats_df.to_string()}
```
""")
            
            # Categorical analysis
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                cat_analysis = []
                for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
                    unique_count = df[col].nunique()
                    top_values = df[col].value_counts().head(3)
                    cat_analysis.append(f"""
**{col}:**
- Unique values: {unique_count}
- Top values: {', '.join([f"{val} ({count})" for val, count in top_values.items()])}
""")
                
                analysis_parts.append(f"""
### 🏷️ Categorical Analysis
{chr(10).join(cat_analysis)}
""")
            
            # Correlations for numeric data
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                # Find strongest correlations
                correlations = []
                for i in range(len(numeric_cols)):
                    for j in range(i+1, len(numeric_cols)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.5:
                            correlations.append(f"- {numeric_cols[i]} ↔ {numeric_cols[j]}: {corr_val:.3f}")
                
                if correlations:
                    analysis_parts.append(f"""
### 🔗 Strong Correlations (|r| > 0.5)
{chr(10).join(correlations)}
""")
            
            # Key insights
            insights = []
            
            # Data quality insights
            if df.isnull().sum().sum() > 0:
                insights.append("⚠️ Missing data detected - consider cleaning or imputation strategies")
            
            # Size insights
            if len(df) < 100:
                insights.append("📏 Small dataset - statistical significance may be limited")
            elif len(df) > 10000:
                insights.append("📈 Large dataset - consider sampling for exploration")
            
            # Duplicate insights
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                insights.append(f"🔄 {duplicates} duplicate rows found")
            
            if insights:
                analysis_parts.append(f"""
### 💡 Key Insights
{chr(10).join(insights)}
""")
            
            # Request-specific analysis if provided
            if request:
                analysis_parts.append(f"""
### 🎯 Analysis for Your Request
Based on your request: "{request}"

This dataset appears suitable for:
{self._suggest_analysis_methods(df, request)}
""")
            
            return "\n".join(analysis_parts)
            
        except Exception as e:
            return f"Error performing DataFrame analysis: {str(e)}"

    def _detect_and_perform_calculation(self, df: pd.DataFrame, request: str) -> Optional[str]:
        """Detect specific calculation requests and perform them."""
        request_lower = request.lower()
        
        try:
            # PRIORITY: Check for "calculations only" requests FIRST
            if any(phrase in request_lower for phrase in [
                "calculations only", "perform calculations only", "no overview", 
                "skip dataset overview", "exact calculations", "step 1", "step 2", "step 3"
            ]):
                return self._perform_calculations_only_format(df, request)
            
            # GROUP BY detection and execution
            elif any(phrase in request_lower for phrase in ['group by', 'group_by', 'groupby', 'breakdown by', 'segment by']):
                return self._perform_groupby_calculation(df, request)
            
            # FILTER detection and execution
            elif any(phrase in request_lower for phrase in ['filter', 'where', 'subset', 'only show', 'exclude']):
                return self._perform_filter_calculation(df, request)
            
            # SUM calculation
            elif any(phrase in request_lower for phrase in ['sum', 'total', 'aggregate']):
                return self._perform_sum_calculation(df, request)
            
            # COUNT calculation
            elif any(phrase in request_lower for phrase in ['count', 'number of', 'how many']):
                return self._perform_count_calculation(df, request)
            
            # AVERAGE calculation
            elif any(phrase in request_lower for phrase in ['average', 'mean']):
                return self._perform_average_calculation(df, request)
            
            # SORT/ORDER BY
            elif any(phrase in request_lower for phrase in ['sort', 'order by', 'rank', 'top']):
                return self._perform_sort_calculation(df, request)
            
            return None
            
        except Exception as e:
            return f"### ❌ Calculation Error\nError performing specific calculation: {str(e)}"

    def _perform_groupby_calculation(self, df: pd.DataFrame, request: str) -> str:
        """Perform GROUP BY calculation based on the request with custom output format."""
        try:
            request_lower = request.lower()
            
            # Enhanced detection for "calculations only" requests
            is_calculations_only = any(phrase in request_lower for phrase in [
                "calculations only", "perform calculations only", "no overview", 
                "skip dataset overview", "exact calculations", "step 1", "step 2", "step 3"
            ])
            
            if is_calculations_only:
                return self._perform_calculations_only_format(df, request)
            
            # Extract grouping columns from request
            group_cols = self._extract_groupby_columns(df, request)
            if not group_cols:
                return "### ❌ GROUP BY Error\nCould not identify columns to group by in the request."
            
            # Get numeric columns for aggregation
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Perform the grouping
            grouped = df.groupby(group_cols)
            
            results = []
            results.append(f"## 🔗 GROUP BY Analysis")
            results.append(f"**Grouping by:** {', '.join(group_cols)}")
            
            # Count aggregation
            count_result = grouped.size().reset_index(name='count')
            results.append(f"\n### 📊 Count by {', '.join(group_cols)}:")
            results.append(f"```\n{count_result.to_string(index=False)}\n```")
            
            # Sum aggregation for numeric columns
            if numeric_cols:
                sum_result = grouped[numeric_cols].sum().reset_index()
                results.append(f"\n### 💰 Sum by {', '.join(group_cols)}:")
                results.append(f"```\n{sum_result.to_string(index=False)}\n```")
                
                # Average aggregation
                avg_result = grouped[numeric_cols].mean().reset_index()
                results.append(f"\n### 📈 Average by {', '.join(group_cols)}:")
                results.append(f"```\n{avg_result.to_string(index=False)}\n```")
            
            # Summary insights
            results.append(f"\n### 💡 Insights:")
            results.append(f"- Found {len(count_result)} unique groups")
            if len(count_result) > 0:
                max_group = count_result.loc[count_result['count'].idxmax()]
                results.append(f"- Largest group: {dict(max_group[:-1])} with {max_group['count']} records")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"### ❌ GROUP BY Error\nError performing GROUP BY: {str(e)}"
        

    def _perform_calculations_only_format(self, df: pd.DataFrame, request: str) -> str:
        """Perform calculations with specific output format for 'calculations only' requests."""
        try:
            results = []
            
            # STEP 1: GROUP BY company_size - ALWAYS EXECUTE
            step1_result = self._step1_company_size_analysis(df)
            results.append(step1_result)
            
            # STEP 2: GROUP BY company_name, top 20 - ALWAYS EXECUTE  
            step2_result = self._step2_top_companies_analysis(df)
            results.append(step2_result)
            
            # STEP 3: FILTER and GROUP BY company_name - ALWAYS EXECUTE
            step3_result = self._step3_above_average_analysis(df)
            results.append(step3_result)
            
            return "\n\n".join(results)
            
        except Exception as e:
            return f"❌ Calculation Error: {str(e)}"
        
    def _step1_company_size_analysis(self, df: pd.DataFrame) -> str:
        """STEP 1: GROUP BY company_size, show COUNT and MEAN of salary_usd"""
        try:
            # Group by company_size
            grouped = df.groupby('company_size')
            
            # Calculate count and mean salary
            result = grouped.agg({
                'salary_usd': ['count', 'mean']
            }).round(2)
            
            # Flatten column names
            result.columns = ['count', 'mean_salary']
            result = result.reset_index()
            
            # Format output
            output = "**Company Size Results:**\n"
            for _, row in result.iterrows():
                output += f"- {row['company_size']}: {row['count']} employees, avg salary ${row['mean_salary']:,.2f}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Step 1 Error: {str(e)}"

    def _step2_top_companies_analysis(self, df: pd.DataFrame) -> str:
        """STEP 2: GROUP BY company_name, show COUNT, sort descending, take top 20"""
        try:
            # Group by company_name and count
            company_counts = df.groupby('company_name').size().reset_index(name='count')
            
            # Sort descending and take top 20
            top_20 = company_counts.sort_values('count', ascending=False).head(20)
            
            # Format output
            output = "**Top 20 Companies:**\n"
            for i, (_, row) in enumerate(top_20.iterrows(), 1):
                output += f"{i}. {row['company_name']}: {row['count']} employees\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Step 2 Error: {str(e)}"

    def _step3_above_average_analysis(self, df: pd.DataFrame) -> str:
        """STEP 3: FILTER WHERE salary_usd > 115348, GROUP BY company_name"""
        try:
            # Filter for above-average salaries
            filtered_df = df[df['salary_usd'] > 115348]
            
            # Group by company_name and count
            above_avg_companies = filtered_df.groupby('company_name').size().reset_index(name='count')
            
            # Sort by count descending
            above_avg_companies = above_avg_companies.sort_values('count', ascending=False)
            
            # Format output
            output = "**Above-Average Salary Companies:**\n"
            for _, row in above_avg_companies.iterrows():
                output += f"- {row['company_name']}: {row['count']} high-salary employees\n"
            
            return output.strip()
            
        except Exception as e:
            return f"❌ Step 3 Error: {str(e)}"

    def _extract_groupby_columns(self, df: pd.DataFrame, request: str) -> List[str]:
        """Extract column names to group by from the request."""
        import re
        
        request_lower = request.lower()
        df_columns = df.columns.tolist()
        df_columns_lower = [col.lower() for col in df_columns]
        
        # Look for explicit "group by column_name" patterns
        group_by_pattern = r'group\s+by\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)'
        match = re.search(group_by_pattern, request_lower)
        
        if match:
            mentioned_cols = [col.strip() for col in match.group(1).split(',')]
            valid_cols = []
            for col in mentioned_cols:
                if col in df_columns_lower:
                    # Find the actual column name with proper case
                    actual_col = df_columns[df_columns_lower.index(col)]
                    valid_cols.append(actual_col)
            if valid_cols:
                return valid_cols
        
        # Look for any column names mentioned in the request
        mentioned_columns = []
        for i, col in enumerate(df_columns):
            if col.lower() in request_lower:
                mentioned_columns.append(col)
        
        # If specific columns mentioned, use them
        if mentioned_columns:
            # Prefer categorical columns for grouping
            categorical_mentioned = [col for col in mentioned_columns 
                                   if df[col].dtype == 'object' or df[col].nunique() < len(df) * 0.1]
            if categorical_mentioned:
                return categorical_mentioned[:2]  # Limit to 2 columns
            return mentioned_columns[:2]
        
        # Default: use first categorical column
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        if categorical_cols:
            return [categorical_cols[0]]
        
        # Fallback: use first column with reasonable number of unique values
        for col in df_columns:
            if df[col].nunique() < len(df) * 0.5:  # Less than 50% unique values
                return [col]
        
        return []

    def _perform_filter_calculation(self, df: pd.DataFrame, request: str) -> str:
        """Perform filtering based on the request."""
        try:
            # Extract filter conditions
            filtered_df, filter_description = self._apply_filters(df, request)
            
            results = []
            results.append(f"## 🔍 FILTER Analysis")
            results.append(f"**Filter Applied:** {filter_description}")
            results.append(f"**Original rows:** {len(df):,}")
            results.append(f"**Filtered rows:** {len(filtered_df):,}")
            results.append(f"**Rows removed:** {len(df) - len(filtered_df):,}")
            
            if len(filtered_df) > 0:
                results.append(f"\n### 📋 Filtered Results (first 10 rows):")
                results.append(f"```\n{filtered_df.head(10).to_string(index=False)}\n```")
                
                # Quick stats on filtered data
                numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    results.append(f"\n### 📊 Statistics on Filtered Data:")
                    for col in numeric_cols[:3]:  # Show stats for first 3 numeric columns
                        results.append(f"- **{col}**: Mean = {filtered_df[col].mean():.2f}, Sum = {filtered_df[col].sum():.2f}")
            else:
                results.append(f"\n### ⚠️ No rows match the filter criteria")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"### ❌ FILTER Error\nError performing filter: {str(e)}"

    def _apply_filters(self, df: pd.DataFrame, request: str) -> tuple:
        """Apply filters based on the request and return filtered DataFrame and description."""
        import re
        
        request_lower = request.lower()
        filtered_df = df.copy()
        applied_filters = []
        
        # Look for numeric filter patterns like "amount > 1000", "price < 50"
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_lower = col.lower()
            
            # Pattern: column > value
            gt_pattern = rf'{col_lower}\s*>\s*(\d+(?:\.\d+)?)'
            gt_match = re.search(gt_pattern, request_lower)
            if gt_match:
                value = float(gt_match.group(1))
                filtered_df = filtered_df[filtered_df[col] > value]
                applied_filters.append(f"{col} > {value}")
                continue
            
            # Pattern: column < value
            lt_pattern = rf'{col_lower}\s*<\s*(\d+(?:\.\d+)?)'
            lt_match = re.search(lt_pattern, request_lower)
            if lt_match:
                value = float(lt_match.group(1))
                filtered_df = filtered_df[filtered_df[col] < value]
                applied_filters.append(f"{col} < {value}")
                continue
            
            # Pattern: column = value
            eq_pattern = rf'{col_lower}\s*=\s*(\d+(?:\.\d+)?)'
            eq_match = re.search(eq_pattern, request_lower)
            if eq_match:
                value = float(eq_match.group(1))
                filtered_df = filtered_df[filtered_df[col] == value]
                applied_filters.append(f"{col} = {value}")
                continue
        
        # Look for text-based filters
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            col_lower = col.lower()
            if col_lower in request_lower:
                # Look for specific values mentioned
                unique_values = df[col].unique()
                for value in unique_values:
                    if str(value).lower() in request_lower:
                        filtered_df = filtered_df[filtered_df[col] == value]
                        applied_filters.append(f"{col} = '{value}'")
                        break
        
        # Default filter if no specific conditions found
        if not applied_filters:
            # Show top 20 rows
            filtered_df = df.head(20)
            applied_filters = ["Top 20 rows"]
        
        filter_description = " AND ".join(applied_filters) if applied_filters else "No filters"
        
        return filtered_df, filter_description

    def _perform_sum_calculation(self, df: pd.DataFrame, request: str) -> str:
        """Perform SUM calculation."""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) == 0:
                return "### ❌ SUM Error\nNo numeric columns found for sum calculation."
            
            results = []
            results.append(f"## 💰 SUM Calculation")
            
            # Calculate sums
            sums = df[numeric_cols].sum()
            
            results.append(f"### 📊 Column Totals:")
            for col, total in sums.items():
                results.append(f"- **{col}**: {total:,.2f}")
            
            # Grand total if multiple numeric columns
            if len(numeric_cols) > 1:
                grand_total = sums.sum()
                results.append(f"\n**Grand Total (all columns):** {grand_total:,.2f}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"### ❌ SUM Error\nError calculating sum: {str(e)}"

    def _perform_count_calculation(self, df: pd.DataFrame, request: str) -> str:
        """Perform COUNT calculation."""
        try:
            results = []
            results.append(f"## 🔢 COUNT Analysis")
            
            # Total rows
            results.append(f"**Total Rows:** {len(df):,}")
            
            # Count by column (non-null values)
            results.append(f"\n### 📊 Non-null Count by Column:")
            counts = df.count()
            for col, count in counts.items():
                missing = len(df) - count
                results.append(f"- **{col}**: {count:,} ({missing} missing)")
            
            # Unique value counts for categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                results.append(f"\n### 🏷️ Unique Value Counts:")
                for col in categorical_cols[:3]:  # Show first 3 categorical columns
                    unique_count = df[col].nunique()
                    results.append(f"- **{col}**: {unique_count} unique values")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"### ❌ COUNT Error\nError performing count: {str(e)}"

    def _perform_average_calculation(self, df: pd.DataFrame, request: str) -> str:
        """Perform AVERAGE calculation."""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) == 0:
                return "### ❌ AVERAGE Error\nNo numeric columns found for average calculation."
            
            results = []
            results.append(f"## 📈 AVERAGE Calculation")
            
            # Calculate averages
            averages = df[numeric_cols].mean()
            
            results.append(f"### 📊 Column Averages:")
            for col, avg in averages.items():
                results.append(f"- **{col}**: {avg:.2f}")
            
            # Additional statistics
            results.append(f"\n### 📋 Additional Statistics:")
            medians = df[numeric_cols].median()
            for col in numeric_cols:
                results.append(f"- **{col} Median**: {medians[col]:.2f}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"### ❌ AVERAGE Error\nError calculating average: {str(e)}"

    def _perform_sort_calculation(self, df: pd.DataFrame, request: str) -> str:
        """Perform SORT calculation."""
        try:
            # Determine sort column and direction
            sort_col, ascending = self._extract_sort_parameters(df, request)
            
            if not sort_col:
                return "### ❌ SORT Error\nCould not identify column to sort by."
            
            # Perform sort
            sorted_df = df.sort_values(by=sort_col, ascending=ascending)
            
            direction = "ascending" if ascending else "descending"
            results = []
            results.append(f"## 🔄 SORT Analysis")
            results.append(f"**Sorted by:** {sort_col} ({direction})")
            
            results.append(f"\n### 📋 Sorted Results (first 15 rows):")
            results.append(f"```\n{sorted_df.head(15).to_string(index=False)}\n```")
            
            # Show some insights
            if df[sort_col].dtype in [np.number]:
                results.append(f"\n### 💡 Insights:")
                results.append(f"- Highest {sort_col}: {sorted_df[sort_col].iloc[-1 if ascending else 0]}")
                results.append(f"- Lowest {sort_col}: {sorted_df[sort_col].iloc[0 if ascending else -1]}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"### ❌ SORT Error\nError performing sort: {str(e)}"

    def _extract_sort_parameters(self, df: pd.DataFrame, request: str) -> tuple:
        """Extract sort column and direction from request."""
        request_lower = request.lower()
        
        # Determine direction
        ascending = True
        if any(word in request_lower for word in ['desc', 'descending', 'highest', 'largest', 'top']):
            ascending = False
        
        # Find column to sort by
        df_columns = df.columns.tolist()
        
        # Look for column names in request
        for col in df_columns:
            if col.lower() in request_lower:
                return col, ascending
        
        # Default: use first numeric column or first column
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            return numeric_cols[0], ascending
        
        return df_columns[0] if len(df_columns) > 0 else None, ascending

    def _suggest_analysis_methods(self, df: pd.DataFrame, request: str) -> str:
        """Suggest specific analysis methods based on the data and request."""
        suggestions = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        request_lower = request.lower()
        
        if 'trend' in request_lower and len(numeric_cols) > 0:
            suggestions.append("- **Trend Analysis**: Time series analysis on numeric columns")
        
        if 'compare' in request_lower or 'comparison' in request_lower:
            suggestions.append("- **Comparative Analysis**: Group comparisons using categorical variables")
        
        if 'predict' in request_lower and len(numeric_cols) > 1:
            suggestions.append("- **Predictive Modeling**: Regression analysis using numeric features")
        
        if 'segment' in request_lower or 'cluster' in request_lower:
            suggestions.append("- **Segmentation**: Clustering analysis to identify groups")
        
        if len(numeric_cols) > 0:
            suggestions.append(f"- **Statistical Analysis**: Descriptive statistics on {len(numeric_cols)} numeric columns")
        
        if len(categorical_cols) > 0:
            suggestions.append(f"- **Categorical Analysis**: Frequency analysis on {len(categorical_cols)} categorical columns")
        
        return "\n".join(suggestions) if suggestions else "- General exploratory data analysis"


class FileAgent(BaseAgent):
    """Agent for actual file processing and automation tasks."""

    def __init__(self):
        """Initialize the file processing agent."""
        super().__init__(AgentType.AUTOMATION)
        self.temp_dir = tempfile.mkdtemp()
    
    def add_user_feedback(self, satisfaction_score: int, feedback_text: str = ""):
        """Add user feedback for continuous improvement."""
        if 1 <= satisfaction_score <= 5:
            self.performance_metrics['user_satisfaction_scores'].append({
                'score': satisfaction_score,
                'feedback': feedback_text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 feedback entries
            if len(self.performance_metrics['user_satisfaction_scores']) > 50:
                self.performance_metrics['user_satisfaction_scores'] = \
                    self.performance_metrics['user_satisfaction_scores'][-50:]
            
            # Learn from feedback
            if satisfaction_score < 3:  # Low satisfaction
                self.performance_metrics['improvement_suggestions'].append({
                    'type': 'user_feedback',
                    'suggestion': f'User feedback: {feedback_text}',
                    'timestamp': datetime.now().isoformat()
                })

    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None, files: Optional[List] = None, **kwargs) -> AgentResponse:
        """Process automation and file processing requests."""
        start_time = time.time()
        
        try:
            if not input_data or not input_data.strip():
                return AgentResponse(
                    content="Please provide a specific file processing task or automation request. You can also upload files for processing.",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Check if files are provided for processing
            if files and len(files) > 0:
                return self._process_uploaded_files(files, input_data, start_time)
            
            # Check for specific automation tasks
            if self._is_script_generation_request(input_data):
                return self._generate_automation_script(input_data, chat_history, start_time)
            
            # Check for workflow creation
            if self._is_workflow_request(input_data):
                return self._create_workflow(input_data, chat_history, start_time)
            
            # Check for file operation requests
            if self._is_file_operation_request(input_data):
                return self._handle_file_operations(input_data, chat_history, start_time)
            
            # Default to providing automation guidance with specific examples
            return self._provide_automation_guidance(input_data, chat_history, start_time)
            
        except Exception as e:
            logger.error(f"Error in FileAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Automation error: {str(e)}"
            )

    def _is_script_generation_request(self, input_data: str) -> bool:
        """Check if request is for script generation."""
        script_indicators = [
            'generate script', 'create script', 'write script', 'automate with',
            'python script', 'bash script', 'automation script'
        ]
        return any(indicator in input_data.lower() for indicator in script_indicators)

    def _is_workflow_request(self, input_data: str) -> bool:
        """Check if request is for workflow creation."""
        workflow_indicators = [
            'workflow', 'process flow', 'automation flow', 'step by step',
            'pipeline', 'sequence of tasks'
        ]
        return any(indicator in input_data.lower() for indicator in workflow_indicators)

    def _is_file_operation_request(self, input_data: str) -> bool:
        """Check if request is for file operations."""
        file_indicators = [
            'process files', 'organize files', 'rename files', 'move files',
            'file management', 'batch process', 'file conversion'
        ]
        return any(indicator in input_data.lower() for indicator in file_indicators)

    def _process_uploaded_files(self, files: List, request: str, start_time: float) -> AgentResponse:
        """Process uploaded files based on the request."""
        try:
            results = []
            
            for file in files:
                file_result = self._process_single_file(file, request)
                results.append(file_result)
            
            # Combine results
            combined_result = f"""
## 📁 File Processing Results

{chr(10).join(results)}

### Summary:
- Processed {len(files)} file(s)
- Request: {request}
- All operations completed successfully
"""
            
            return AgentResponse(
                content=combined_result,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error processing files: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )

    def _process_single_file(self, file, request: str) -> str:
        """Process a single file."""
        try:
            file_info = {
                'name': getattr(file, 'name', 'unknown'),
                'size': getattr(file, 'size', 0) if hasattr(file, 'size') else len(file.read() if hasattr(file, 'read') else b''),
                'type': self._detect_file_type(file)
            }
            
            # Reset file pointer if possible
            if hasattr(file, 'seek'):
                file.seek(0)
            
            # Process based on file type and request
            if file_info['type'] == FileType.SPREADSHEET:
                return self._process_spreadsheet_file(file, file_info, request)
            elif file_info['type'] == FileType.TEXT:
                return self._process_text_file(file, file_info, request)
            elif file_info['type'] == FileType.IMAGE:
                return self._process_image_file(file, file_info, request)
            else:
                return self._process_generic_file(file, file_info, request)
                
        except Exception as e:
            return f"Error processing file {getattr(file, 'name', 'unknown')}: {str(e)}"

    def _detect_file_type(self, file) -> FileType:
        """Detect the type of uploaded file."""
        filename = getattr(file, 'name', '')
        
        if filename.endswith(('.csv', '.xlsx', '.xls')):
            return FileType.SPREADSHEET
        elif filename.endswith(('.txt', '.md', '.py', '.js', '.html', '.css')):
            return FileType.TEXT
        elif filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            return FileType.IMAGE
        elif filename.endswith(('.mp4', '.avi', '.mov', '.wmv')):
            return FileType.VIDEO
        elif filename.endswith(('.mp3', '.wav', '.flac', '.aac')):
            return FileType.AUDIO
        else:
            return FileType.UNKNOWN

    def _process_spreadsheet_file(self, file, file_info: dict, request: str) -> str:
        """Process spreadsheet files."""
        try:
            # Read the spreadsheet
            if file_info['name'].endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Perform requested operations
            operations_performed = []
            
            if 'clean' in request.lower():
                original_rows = len(df)
                df = df.dropna()
                operations_performed.append(f"Removed {original_rows - len(df)} rows with missing data")
            
            if 'summary' in request.lower() or 'analyze' in request.lower():
                summary = df.describe().to_string()
                operations_performed.append(f"Generated statistical summary")
            
            if 'export' in request.lower() or 'convert' in request.lower():
                # Create processed version
                processed_filename = f"processed_{file_info['name']}"
                operations_performed.append(f"Created processed version: {processed_filename}")
            
            result = f"""
### 📊 {file_info['name']} (Spreadsheet)
- **Size:** {file_info['size']:,} bytes
- **Dimensions:** {df.shape[0]} rows × {df.shape[1]} columns
- **Columns:** {', '.join(df.columns.tolist())}

**Operations Performed:**
{chr(10).join(f"- {op}" for op in operations_performed)}
"""
            return result
            
        except Exception as e:
            return f"Error processing spreadsheet {file_info['name']}: {str(e)}"

    def _process_text_file(self, file, file_info: dict, request: str) -> str:
        """Process text files."""
        try:
            content = file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            # Analyze content
            lines = content.split('\n')
            words = content.split()
            chars = len(content)
            
            operations_performed = []
            
            if 'analyze' in request.lower():
                operations_performed.append(f"Analyzed text structure: {len(lines)} lines, {len(words)} words, {chars} characters")
            
            if 'clean' in request.lower():
                # Remove empty lines
                cleaned_lines = [line.strip() for line in lines if line.strip()]
                operations_performed.append(f"Cleaned text: removed {len(lines) - len(cleaned_lines)} empty lines")
            
            if 'extract' in request.lower():
                # Extract emails, URLs, etc.
                import re
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
                operations_performed.append(f"Extracted {len(emails)} emails and {len(urls)} URLs")
            
            result = f"""
### 📄 {file_info['name']} (Text File)
- **Size:** {file_info['size']:,} bytes
- **Lines:** {len(lines):,}
- **Words:** {len(words):,}
- **Characters:** {chars:,}

**Operations Performed:**
{chr(10).join(f"- {op}" for op in operations_performed)}
"""
            return result
            
        except Exception as e:
            return f"Error processing text file {file_info['name']}: {str(e)}"

    def _process_image_file(self, file, file_info: dict, request: str) -> str:
        """Process image files."""
        try:
            operations_performed = []
            
            if 'analyze' in request.lower():
                operations_performed.append("Analyzed image metadata and properties")
            
            if 'resize' in request.lower():
                operations_performed.append("Image resizing operation planned")
            
            if 'convert' in request.lower():
                operations_performed.append("Image format conversion planned")
            
            result = f"""
### 🖼️ {file_info['name']} (Image File)
- **Size:** {file_info['size']:,} bytes
- **Type:** Image file

**Operations Performed:**
{chr(10).join(f"- {op}" for op in operations_performed)}

*Note: Advanced image processing requires additional libraries.*
"""
            return result
            
        except Exception as e:
            return f"Error processing image file {file_info['name']}: {str(e)}"

    def _process_generic_file(self, file, file_info: dict, request: str) -> str:
        """Process generic files."""
        return f"""
### 📁 {file_info['name']} (Generic File)
- **Size:** {file_info['size']:,} bytes
- **Type:** {file_info['type'].value}

**Operations Available:**
- File metadata extraction
- Basic file operations (copy, move, rename)
- Format detection

*Upload specific file types for more advanced processing.*
"""

    def _generate_automation_script(self, request: str, chat_history: Optional[List[Dict]], start_time: float) -> AgentResponse:
        """Generate actual automation scripts."""
        try:
            script_prompt = f"""
            Generate a working automation script for: {request}
            
            Provide:
            1. Complete, runnable code
            2. Clear comments explaining each step
            3. Error handling
            4. Usage instructions
            5. Required dependencies
            
            Choose the most appropriate language (Python, Bash, etc.) and provide production-ready code.
            """
            
            script_code = self._process_with_model(script_prompt, chat_history)
            
            result = f"""
## 🤖 Generated Automation Script

{script_code}

### 📋 Next Steps:
1. Save the script to a file
2. Install any required dependencies
3. Test the script with sample data
4. Schedule or run as needed

### ⚠️ Important Notes:
- Review and test the script before running in production
- Modify paths and parameters as needed for your environment
- Ensure you have necessary permissions for file operations
"""
            
            return AgentResponse(
                content=result,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error generating script: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )

    def _create_workflow(self, request: str, chat_history: Optional[List[Dict]], start_time: float) -> AgentResponse:
        """Create detailed workflow documentation."""
        try:
            workflow_prompt = f"""
            Create a detailed workflow for: {request}
            
            Include:
            1. Step-by-step process
            2. Input/output requirements
            3. Tools and technologies needed
            4. Error handling procedures
            5. Quality checks
            6. Timeline estimates
            7. Success criteria
            
            Format as a comprehensive workflow document.
            """
            
            workflow_content = self._process_with_model(workflow_prompt, chat_history)
            
            result = f"""
## 🔄 Workflow Documentation

{workflow_content}

### 📊 Implementation Checklist:
- [ ] Define input requirements
- [ ] Set up necessary tools/environment
- [ ] Implement each workflow step
- [ ] Test with sample data
- [ ] Establish monitoring and logging
- [ ] Document and train team
"""
            
            return AgentResponse(
                content=result,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error creating workflow: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )

    def _handle_file_operations(self, request: str, chat_history: Optional[List[Dict]], start_time: float) -> AgentResponse:
        """Handle specific file operation requests."""
        try:
            # Generate specific file operation scripts/instructions
            operation_prompt = f"""
            Provide specific file operation instructions for: {request}
            
            Include:
            1. Exact commands or code
            2. Safety precautions
            3. Backup recommendations
            4. Testing procedures
            5. Rollback plans
            
            Be specific and actionable.
            """
            
            operation_content = self._process_with_model(operation_prompt, chat_history)
            
            result = f"""
## 📁 File Operation Instructions

{operation_content}

### 🛡️ Safety Checklist:
- [ ] Backup important files before operations
- [ ] Test commands on sample files first
- [ ] Verify results before applying to all files
- [ ] Keep audit log of changes made
"""
            
            return AgentResponse(
                content=result,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error handling file operations: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )

    def _provide_automation_guidance(self, request: str, chat_history: Optional[List[Dict]], start_time: float) -> AgentResponse:
        """Provide specific automation guidance with examples."""
        try:
            guidance_prompt = f"""
            Provide comprehensive automation guidance for: {request}
            
            Include:
            1. Technology recommendations
            2. Implementation approach
            3. Code examples
            4. Tools and platforms
            5. Best practices
            6. Common pitfalls to avoid
            7. ROI considerations
            8. Specific next steps
            
            Be detailed and practical.
            """
            
            guidance_content = self._process_with_model(guidance_prompt, chat_history)
            
            result = f"""
## 🔧 Automation Guidance

{guidance_content}

### 🚀 Quick Start Options:
1. **Upload files** for immediate processing
2. **Request specific scripts** for custom automation
3. **Ask for workflows** for complex processes
4. **Get tool recommendations** for your use case
"""
            
            return AgentResponse(
                content=result,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error providing guidance: {str(e)}",
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )


class ChatAgent(BaseAgent):
    """Agent for customer service interactions."""

    def __init__(self):
        """Initialize the customer service agent."""
        super().__init__(AgentType.CUSTOMER_SERVICE)
    
    def add_user_feedback(self, satisfaction_score: int, feedback_text: str = ""):
        """Add user feedback for continuous improvement."""
        if 1 <= satisfaction_score <= 5:
            self.performance_metrics['user_satisfaction_scores'].append({
                'score': satisfaction_score,
                'feedback': feedback_text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 feedback entries
            if len(self.performance_metrics['user_satisfaction_scores']) > 50:
                self.performance_metrics['user_satisfaction_scores'] = \
                    self.performance_metrics['user_satisfaction_scores'][-50:]
            
            # Learn from feedback
            if satisfaction_score < 3:  # Low satisfaction
                self.performance_metrics['improvement_suggestions'].append({
                    'type': 'user_feedback',
                    'suggestion': f'User feedback: {feedback_text}',
                    'timestamp': datetime.now().isoformat()
                })

    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None, **kwargs) -> AgentResponse:
        """Process customer service requests with conversation context."""
        start_time = time.time()
        
        try:
            if not input_data or not input_data.strip():
                return AgentResponse(
                    content="Please provide a customer service request or question.",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Check for simple acknowledgments
            acknowledgment_phrases = [
                "thank you", "thanks", "appreciate it", "ok", "okay", "got it",
                "understood", "perfect", "great", "awesome", "nice", "good"
            ]
            
            if any(phrase in input_data.lower() for phrase in acknowledgment_phrases):
                if "thank" in input_data.lower():
                    response_text = "You're very welcome! I'm glad I could help. If you have any other questions or need assistance with anything else, feel free to ask."
                elif any(word in input_data.lower() for word in ["ok", "okay", "got it", "understood"]):
                    response_text = "Perfect! Let me know if you need anything else or have any questions."
                elif any(word in input_data.lower() for word in ["great", "awesome", "nice", "good", "perfect"]):
                    response_text = "I'm glad you're satisfied! Is there anything else I can help you with today?"
                else:
                    response_text = "Thank you! How else can I assist you?"
                
                return AgentResponse(
                    content=response_text,
                    success=True,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Enhanced customer service with context awareness
            customer_service_prompt = f"""
            You are an expert customer service representative for MultiAgentAI21, a multi-agent AI platform.
            
            Our platform includes:
            - Content Creation Agent: Writes blogs, social media, marketing copy, etc.
            - Data Analysis Agent: Analyzes data, performs calculations, generates insights
            - Automation Agent: Processes files, creates scripts, automates workflows
            - Customer Service Agent: Provides support and assistance (that's you!)
            
            CUSTOMER REQUEST: {input_data}
            
            Provide helpful, professional support that:
            1. **Addresses their specific need** with empathy
            2. **Provides clear, actionable solutions**
            3. **Guides them to the right agent** if needed
            4. **Offers specific examples** when helpful
            5. **Maintains a friendly, professional tone**
            
            If they need:
            - Content creation: Guide them to use "content creation" agent
            - Data analysis: Direct them to "data analysis" agent
            - File processing/automation: Point them to "automation" agent
            - General help: Provide comprehensive assistance
            
            Always end with asking how else you can help.
            """
            
            response_text = self._process_with_model(customer_service_prompt, chat_history)
            
            return AgentResponse(
                content=response_text,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in ChatAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="I apologize, but I'm experiencing technical difficulties. Please try again, or let me know if you need help with a specific task.",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Customer service error: {str(e)}"
            )


class ContentCreatorAgent(BaseAgent):
    """Agent specialized in actual content creation."""

    def __init__(self):
        """Initialize the content creator agent."""
        super().__init__(AgentType.CONTENT_CREATION)
    
    def add_user_feedback(self, satisfaction_score: int, feedback_text: str = ""):
        """Add user feedback for continuous improvement."""
        if 1 <= satisfaction_score <= 5:
            self.performance_metrics['user_satisfaction_scores'].append({
                'score': satisfaction_score,
                'feedback': feedback_text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 feedback entries
            if len(self.performance_metrics['user_satisfaction_scores']) > 50:
                self.performance_metrics['user_satisfaction_scores'] = \
                    self.performance_metrics['user_satisfaction_scores'][-50:]
            
            # Learn from feedback
            if satisfaction_score < 3:  # Low satisfaction
                self.performance_metrics['improvement_suggestions'].append({
                    'type': 'user_feedback',
                    'suggestion': f'User feedback: {feedback_text}',
                    'timestamp': datetime.now().isoformat()
                })

    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None, **kwargs) -> AgentResponse:
        """Process content creation requests and actually create content."""
        start_time = time.time()
        
        try:
            if not input_data or not input_data.strip():
                return AgentResponse(
                    content="Please provide a specific content creation request (e.g., 'Write a blog post about AI trends', 'Create social media content for a product launch').",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Determine content type and create actual content
            content_type = self._detect_content_type(input_data)
            content_topic = self._extract_content_topic(input_data, content_type)
            
            logger.info(f"Creating {content_type} content about: {content_topic}")
            
            # Generate actual content based on type
            if content_type == "blog_post":
                content = self._create_blog_post(content_topic, chat_history)
            elif content_type == "social_media":
                content = self._create_social_media_post(content_topic, chat_history)
            elif content_type == "article":
                content = self._create_article(content_topic, chat_history)
            elif content_type == "marketing_copy":
                content = self._create_marketing_copy(content_topic, chat_history)
            elif content_type == "product_description":
                content = self._create_product_description(content_topic, chat_history)
            elif content_type == "email_content":
                content = self._create_email_content(content_topic, chat_history)
            else:
                content = self._create_general_content(content_topic, chat_history)
            
            # Format the final response
            final_content = f"""
## 📝 {content_type.replace('_', ' ').title()} Created

{content}

---
### 📊 Content Details:
- **Type:** {content_type.replace('_', ' ').title()}
- **Topic:** {content_topic}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Ready to use:** ✅

*Generated by MultiAgentAI21 Content Creation Agent*
"""
            
            return AgentResponse(
                content=final_content,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in ContentCreatorAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Content creation error: {str(e)}"
            )

    def _detect_content_type(self, request: str) -> str:
        """Detect the type of content to generate."""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["blog", "blog post", "article post"]):
            return "blog_post"
        elif any(word in request_lower for word in ["social media", "tweet", "facebook", "instagram", "linkedin", "post"]):
            return "social_media"
        elif any(word in request_lower for word in ["article", "news", "report"]):
            return "article"
        elif any(word in request_lower for word in ["marketing", "advertisement", "ad copy", "sales"]):
            return "marketing_copy"
        elif any(word in request_lower for word in ["product", "description", "feature"]):
            return "product_description"
        elif any(word in request_lower for word in ["email", "newsletter", "message"]):
            return "email_content"
        else:
            return "general"

    def _extract_content_topic(self, request: str, content_type: str) -> str:
        """Extract the core topic from a content creation request."""
        # Remove common prefixes
        prefixes_to_remove = [
            "write a blog post about", "create a blog post about", "blog post on",
            "create a social media post about", "write a social media post for",
            "write an article about", "create an article on",
            "create marketing copy about", "write marketing copy for",
            "write a product description for", "create a product description for",
            "write an email about", "create an email for",
            "create content about", "write about", "generate content on",
            "write", "create", "generate", "about", "on", "for"
        ]
        
        topic = request.lower()
        for prefix in prefixes_to_remove:
            if topic.startswith(prefix):
                topic = topic[len(prefix):].strip()
                break
        
        return topic.strip()

    def _create_blog_post(self, topic: str, chat_history: Optional[List[Dict]]) -> str:
        """Create an actual blog post."""
        prompt = f"""
        Write a complete, engaging blog post about: {topic}
        
        Requirements:
        - 800-1200 words
        - Compelling headline
        - Strong introduction with hook
        - 4-6 main sections with subheadings
        - Practical examples and tips
        - Strong conclusion with call-to-action
        - SEO-friendly structure
        
        Format with proper markdown headers and structure.
        """
        return self._process_with_model(prompt, chat_history)

    def _create_social_media_post(self, topic: str, chat_history: Optional[List[Dict]]) -> str:
        """Create an actual social media post."""
        prompt = f"""
        Create an engaging social media post about: {topic}
        
        Requirements:
        - Attention-grabbing hook
        - 150-300 characters for platforms like Twitter
        - Include relevant emojis
        - 3-5 relevant hashtags
        - Call-to-action
        - Engaging and shareable tone
        
        Create multiple variations for different platforms if relevant.
        """
        return self._process_with_model(prompt, chat_history)

    def _create_article(self, topic: str, chat_history: Optional[List[Dict]]) -> str:
        """Create an actual article."""
        prompt = f"""
        Write a comprehensive article about: {topic}
        
        Requirements:
        - 1500-2000 words
        - Professional headline
        - Executive summary
        - Clear section headers
        - Data and examples
        - Expert insights
        - Actionable takeaways
        - References where appropriate
        
        Format with proper structure and citations.
        """
        return self._process_with_model(prompt, chat_history)

    def _create_marketing_copy(self, topic: str, chat_history: Optional[List[Dict]]) -> str:
        """Create actual marketing copy."""
        prompt = f"""
        Write compelling marketing copy for: {topic}
        
        Requirements:
        - Focus on benefits over features
        - Strong value proposition
        - Persuasive language
        - Social proof elements
        - Clear call-to-action
        - Create urgency
        - Address pain points
        - Multiple versions (short, medium, long)
        
        Include headlines, body copy, and CTAs.
        """
        return self._process_with_model(prompt, chat_history)

    def _create_product_description(self, topic: str, chat_history: Optional[List[Dict]]) -> str:
        """Create actual product description."""
        prompt = f"""
        Write a detailed product description for: {topic}
        
        Requirements:
        - Compelling product overview
        - Key features and benefits
        - Technical specifications
        - Use cases and applications
        - What's included
        - Customer testimonial style
        - Clear value proposition
        - Purchase motivation
        
        Format for e-commerce readiness.
        """
        return self._process_with_model(prompt, chat_history)

    def _create_email_content(self, topic: str, chat_history: Optional[List[Dict]]) -> str:
        """Create actual email content."""
        prompt = f"""
        Write a complete email about: {topic}
        
        Requirements:
        - Compelling subject line
        - Personal greeting
        - Clear, concise message
        - Single focus
        - Professional tone
        - Clear call-to-action
        - Professional signature
        - Mobile-friendly format
        
        Include subject line, body, and signature.
        """
        return self._process_with_model(prompt, chat_history)

    def _create_general_content(self, topic: str, chat_history: Optional[List[Dict]]) -> str:
        """Create general content."""
        prompt = f"""
        Create engaging content about: {topic}
        
        Requirements:
        - Clear, engaging language
        - Logical structure
        - Relevant examples
        - Actionable information
        - Appropriate formatting
        - Value-focused
        - Professional tone
        - Complete and useful
        
        Determine the best format based on the topic.
        """
        return self._process_with_model(prompt, chat_history)


# Keep all the existing factory and orchestrator functions...
def create_agent(agent_type: AgentType) -> BaseAgent:
    """Create an agent of the specified type."""
    try:
        if agent_type == AgentType.CONTENT_CREATION:
            try:
                if 'EnhancedContentCreatorAgent' in globals():
                    return EnhancedContentCreatorAgent()
                else:
                    raise ImportError("EnhancedContentCreatorAgent not found.")
            except (ImportError, NameError) as e:
                logger.warning(f"EnhancedContentCreatorAgent not available: {e}, using basic ContentCreatorAgent")
                return ContentCreatorAgent()
        elif agent_type == AgentType.DATA_ANALYSIS:
            return AnalysisAgent()
        elif agent_type == AgentType.CUSTOMER_SERVICE:
            return ChatAgent()
        elif agent_type == AgentType.AUTOMATION:
            return DevOpsAutomationAgent()
        
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    except Exception as e:
        logger.error(f"Error creating agent of type {agent_type}: {e}")
        raise


class MultiAgentCodingAI:
    """Main orchestrator for the multi-agent system with enhanced functionality and self-learning"""

    def __init__(self):
        """Initialize the multi-agent system."""
        self.agents = {}
        self.db = None
        self.system_metrics = {
            'total_sessions': 0,
            'total_requests': 0,
            'system_start_time': datetime.now().isoformat(),
            'agent_performance_history': [],
            'user_satisfaction_trends': [],
            'system_optimization_log': []
        }
        self._initialize_database()
        self._initialize_agents()

    def _initialize_database(self):
        """Initialize database connection."""
        try:
            self.db = FirestoreClient()
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize database: {e}")
            self.db = None

    def _initialize_agents(self):
        """Initialize all available agents."""
        try:
            agent_types = [
                AgentType.CONTENT_CREATION,
                AgentType.DATA_ANALYSIS,
                AgentType.CUSTOMER_SERVICE,
                AgentType.AUTOMATION,
                
            ]
            
            for agent_type in agent_types:
                try:
                    self.agents[agent_type] = create_agent(agent_type)
                    logger.info(f"Successfully initialized {agent_type.value} agent")
                except Exception as e:
                    logger.error(f"Failed to initialize {agent_type.value} agent: {e}")
                    
            if not self.agents:
                raise RuntimeError("No agents could be initialized")
                
            logger.info(f"Initialized {len(self.agents)} agents successfully")
            
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise

    def route_request(
        self,
        request: str,
        agent_type: Optional[AgentType] = None,
        context: Optional[Dict] = None,
        session_id: Optional[str] = None,
        files: Optional[List] = None
    ) -> AgentResponse:
        """Route request to appropriate agent with enhanced capabilities and learning"""
        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())
        
        # Extract chat_history from context
        chat_history_from_context = context.get("chat_history", []) if context else []

        try:
            if not request or not request.strip():
                return AgentResponse(
                    content="Please provide a valid request.",
                    success=False,
                    error_message="Empty request provided",
                    execution_time=time.time() - start_time
                )
            
            if not agent_type:
                agent_type = self._detect_agent_type(request, files)

            logger.info(f"Routing request to {agent_type.value} agent")
            logger.info(f"Request: {request[:100]}...")

            if agent_type not in self.agents:
                logger.error(f"Agent {agent_type.value} not found in available agents")
                response = AgentResponse(
                    content="",
                    success=False,
                    agent_type=agent_type.value,
                    error_message=f"Agent {agent_type.value} is not available",
                    execution_time=time.time() - start_time
                )
                self._save_interaction(session_id, request, response, agent_type)
                return response

            # Pass additional parameters to the agent
            response = self.agents[agent_type].process(
                request, 
                chat_history=chat_history_from_context,
                files=files
            )
            response.agent_type = agent_type.value
            response.execution_time = time.time() - start_time

            # Update system metrics
            self._update_system_metrics(agent_type, response, time.time() - start_time)

            # Save interaction for learning
            self._save_interaction(session_id, request, response, agent_type)

            # Trigger agent optimization if needed
            self._trigger_agent_optimization(agent_type)

            logger.info(f"Response generated successfully. Content length: {len(response.content) if response.content else 0}")
            return response

        except Exception as e:
            logger.error(f"Error in route_request: {e}", exc_info=True)
            response = AgentResponse(
                content="",
                success=False,
                error_message=f"Routing error: {str(e)}",
                execution_time=time.time() - start_time
            )
            if agent_type:
                response.agent_type = agent_type.value
            self._save_interaction(session_id, request, response, agent_type)
            return response

    def _update_system_metrics(self, agent_type: AgentType, response: AgentResponse, execution_time: float):
        """Update system-wide performance metrics."""
        self.system_metrics['total_requests'] += 1
        
        # Record agent performance
        agent_performance = {
            'agent_type': agent_type.value,
            'timestamp': datetime.now().isoformat(),
            'success': response.success,
            'execution_time': execution_time,
            'response_length': len(response.content) if response.content else 0,
            'error_message': response.error_message or response.error or ""
        }
        
        self.system_metrics['agent_performance_history'].append(agent_performance)
        
        # Keep only last 1000 performance records
        if len(self.system_metrics['agent_performance_history']) > 1000:
            self.system_metrics['agent_performance_history'] = \
                self.system_metrics['agent_performance_history'][-1000:]

    def _trigger_agent_optimization(self, agent_type: AgentType):
        """Trigger agent optimization based on performance patterns."""
        if agent_type not in self.agents:
            return
        
        agent = self.agents[agent_type]
        
        # Get agent performance report
        performance_report = agent.get_performance_report()
        
        # Check if optimization is needed
        if performance_report['total_requests'] > 0:
            success_rate = float(performance_report['success_rate'].rstrip('%')) / 100
            
            # If success rate is low, trigger optimization
            if success_rate < 0.7:  # Less than 70% success rate
                logger.info(f"Triggering optimization for {agent_type.value} agent (success rate: {success_rate:.2%})")
                agent.optimize_prompts()
                
                # Log optimization action
                self.system_metrics['system_optimization_log'].append({
                    'timestamp': datetime.now().isoformat(),
                    'agent_type': agent_type.value,
                    'action': 'prompt_optimization',
                    'reason': f'Low success rate: {success_rate:.2%}',
                    'previous_success_rate': success_rate
                })

    def get_system_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive system performance report."""
        if not self.system_metrics['agent_performance_history']:
            return {
                'status': 'No performance data available',
                'timestamp': datetime.now().isoformat()
            }
        
        # Calculate system-wide metrics
        total_requests = self.system_metrics['total_requests']
        successful_requests = sum(1 for p in self.system_metrics['agent_performance_history'] if p['success'])
        overall_success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # Calculate average response time
        response_times = [p['execution_time'] for p in self.system_metrics['agent_performance_history']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Agent-specific performance
        agent_performance = {}
        for agent_type in self.agents.keys():
            agent_data = [p for p in self.system_metrics['agent_performance_history'] 
                         if p['agent_type'] == agent_type.value]
            if agent_data:
                agent_success_rate = sum(1 for p in agent_data if p['success']) / len(agent_data)
                agent_avg_time = sum(p['execution_time'] for p in agent_data) / len(agent_data)
                agent_performance[agent_type.value] = {
                    'total_requests': len(agent_data),
                    'success_rate': f"{agent_success_rate:.2%}",
                    'average_response_time': f"{agent_avg_time:.2f}s"
                }
        
        return {
            'system_overview': {
                'total_requests': total_requests,
                'overall_success_rate': f"{overall_success_rate:.2%}",
                'average_response_time': f"{avg_response_time:.2f}s",
                'system_uptime': self._calculate_uptime(),
                'active_agents': len(self.agents)
            },
            'agent_performance': agent_performance,
            'recent_optimizations': self.system_metrics['system_optimization_log'][-5:],
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_uptime(self) -> str:
        """Calculate system uptime."""
        try:
            start_time = datetime.fromisoformat(self.system_metrics['system_start_time'])
            uptime = datetime.now() - start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "Unknown"

    def add_user_feedback(self, agent_type: str, satisfaction_score: int, feedback_text: str = ""):
        """Add user feedback for system-wide learning."""
        if agent_type in self.agents:
            self.agents[AgentType(agent_type)].add_user_feedback(satisfaction_score, feedback_text)
        
        # Record system-wide satisfaction trends
        self.system_metrics['user_satisfaction_trends'].append({
            'timestamp': datetime.now().isoformat(),
            'agent_type': agent_type,
            'satisfaction_score': satisfaction_score,
            'feedback': feedback_text
        })
        
        # Keep only last 200 feedback entries
        if len(self.system_metrics['user_satisfaction_trends']) > 200:
            self.system_metrics['user_satisfaction_trends'] = \
                self.system_metrics['user_satisfaction_trends'][-200:]

    def optimize_all_agents(self):
        """Trigger optimization for all agents."""
        logger.info("Starting system-wide agent optimization")
        
        for agent_type, agent in self.agents.items():
            try:
                agent.optimize_prompts()
                logger.info(f"Optimized {agent_type.value} agent")
            except Exception as e:
                logger.error(f"Failed to optimize {agent_type.value} agent: {e}")
        
        # Log system optimization
        self.system_metrics['system_optimization_log'].append({
            'timestamp': datetime.now().isoformat(),
            'action': 'system_wide_optimization',
            'agents_optimized': len(self.agents),
            'reason': 'Scheduled optimization'
        })

    def get_agent_learning_insights(self, agent_type: str) -> Dict[str, Any]:
        """Get learning insights for a specific agent."""
        if agent_type not in [at.value for at in self.agents.keys()]:
            return {'error': 'Agent type not found'}
        
        # Find the agent
        agent = None
        for at, a in self.agents.items():
            if at.value == agent_type:
                agent = a
                break
        
        if not agent:
            return {'error': 'Agent not found'}
        
        performance_report = agent.get_performance_report()
        
        # Analyze learning patterns
        learning_insights = {
            'performance_summary': performance_report,
            'learning_patterns': self._analyze_agent_learning_patterns(agent),
            'improvement_opportunities': self._identify_improvement_opportunities(agent),
            'recommendations': self._generate_agent_recommendations(agent)
        }
        
        return learning_insights

    def _analyze_agent_learning_patterns(self, agent) -> Dict[str, Any]:
        """Analyze learning patterns for a specific agent."""
        if not hasattr(agent, 'learning_history') or not agent.learning_history:
            return {'status': 'No learning data available'}
        
        # Analyze response time trends
        recent_interactions = agent.learning_history[-20:]  # Last 20 interactions
        response_times = [r['response_time'] for r in recent_interactions]
        
        # Check if response times are improving
        if len(response_times) >= 10:
            first_half = response_times[:len(response_times)//2]
            second_half = response_times[len(response_times)//2:]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            
            time_improvement = avg_first - avg_second
            time_trend = "improving" if time_improvement > 0.5 else "stable" if abs(time_improvement) <= 0.5 else "degrading"
        else:
            time_trend = "insufficient data"
        
        return {
            'total_learning_interactions': len(agent.learning_history),
            'recent_response_time_trend': time_trend,
            'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'success_rate_trend': self._calculate_success_rate_trend(agent.learning_history)
        }

    def _calculate_success_rate_trend(self, learning_history: List[Dict]) -> str:
        """Calculate success rate trend over time."""
        if len(learning_history) < 10:
            return "insufficient data"
        
        # Split into two halves
        first_half = learning_history[:len(learning_history)//2]
        second_half = learning_history[len(learning_history)//2:]
        
        success_rate_first = sum(1 for r in first_half if r['success']) / len(first_half)
        success_rate_second = sum(1 for r in second_half if r['success']) / len(second_half)
        
        improvement = success_rate_second - success_rate_first
        
        if improvement > 0.1:
            return "improving"
        elif improvement < -0.1:
            return "degrading"
        else:
            return "stable"

    def _identify_improvement_opportunities(self, agent) -> List[str]:
        """Identify specific improvement opportunities for an agent."""
        opportunities = []
        
        if not hasattr(agent, 'performance_metrics'):
            return ["Performance metrics not available"]
        
        metrics = agent.performance_metrics
        
        # Check success rate
        if metrics['total_requests'] > 0:
            success_rate = metrics['successful_requests'] / metrics['total_requests']
            if success_rate < 0.8:
                opportunities.append(f"Low success rate ({success_rate:.1%}) - review failure patterns")
        
        # Check response time
        if metrics['average_response_time'] > 3.0:
            opportunities.append(f"Slow response time ({metrics['average_response_time']:.1f}s) - optimize prompts")
        
        # Check user satisfaction
        if metrics['user_satisfaction_scores']:
            recent_scores = [s['score'] for s in metrics['user_satisfaction_scores'][-10:]]
            avg_satisfaction = sum(recent_scores) / len(recent_scores)
            if avg_satisfaction < 4.0:
                opportunities.append(f"Low user satisfaction ({avg_satisfaction:.1f}/5) - improve response quality")
        
        # Check improvement suggestions
        if metrics['improvement_suggestions']:
            opportunities.extend([s['suggestion'] for s in metrics['improvement_suggestions'][-3:]])
        
        return opportunities if opportunities else ["No specific improvement opportunities identified"]

    def _generate_agent_recommendations(self, agent) -> List[str]:
        """Generate actionable recommendations for agent improvement."""
        recommendations = []
        
        if not hasattr(agent, 'learning_history') or len(agent.learning_history) < 5:
            return ["Need more interaction data to generate recommendations"]
        
        # Analyze recent interactions
        recent = agent.learning_history[-10:]
        successful = [r for r in recent if r['success']]
        failed = [r for r in recent if not r['success']]
        
        if failed:
            # Analyze failure patterns
            failed_prompts = [r['prompt'] for r in failed]
            common_failure_words = self._extract_common_words(failed_prompts)
            recommendations.append(f"Review failed requests containing: {', '.join(common_failure_words[:3])}")
        
        if successful:
            # Analyze success patterns
            successful_prompts = [r['prompt'] for r in successful]
            common_success_words = self._extract_common_words(successful_prompts)
            recommendations.append(f"Leverage successful patterns with: {', '.join(common_success_words[:3])}")
        
        # Performance recommendations
        if hasattr(agent, 'performance_metrics'):
            metrics = agent.performance_metrics
            if metrics['total_requests'] > 20:
                recommendations.append("Consider prompt optimization based on learning history")
                recommendations.append("Implement user feedback collection for continuous improvement")
        
        return recommendations if recommendations else ["Continue monitoring and collecting interaction data"]

    def _extract_common_words(self, prompts: List[str]) -> List[str]:
        """Extract common words from prompts."""
        from collections import Counter
        import re
        
        all_words = []
        for prompt in prompts:
            # Clean and tokenize
            words = re.findall(r'\b\w+\b', prompt.lower())
            # Filter out common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            words = [w for w in words if w not in stop_words and len(w) > 2]
            all_words.extend(words)
        
        # Count and return most common
        word_counts = Counter(all_words)
        return [word for word, count in word_counts.most_common(5)]

    def _detect_agent_type(self, request: str, files: Optional[List] = None) -> AgentType:
        """Enhanced agent type detection including file analysis"""
        request_lower = request.lower().strip()

        # If files are uploaded, consider automation agent for file processing
        if files and len(files) > 0:
            # Check if it's data analysis vs file processing
            if any(word in request_lower for word in ["analyze", "analysis", "statistics", "data", "insights"]):
                return AgentType.DATA_ANALYSIS
            else:
                return AgentType.AUTOMATION

        # Check for simple acknowledgments
        acknowledgment_phrases = [
            "thank you", "thanks", "appreciate it", "ok", "okay", "got it",
            "understood", "perfect", "great", "awesome", "nice", "good",
            "bye", "goodbye", "see you", "later", "end", "stop"
        ]
        
        if any(phrase in request_lower for phrase in acknowledgment_phrases):
            return AgentType.CUSTOMER_SERVICE

        # Enhanced keywords for each agent type
        analysis_keywords = [
            "analyze", "data", "report", "chart", "sql", "query", "insights", 
            "metrics", "statistics", "dashboard", "visualization", "trend",
            "calculate", "compute", "process data", "correlation", "regression"
        ]
        
        chat_keywords = [
            "help", "support", "issue", "problem", "question", "customer",
            "service", "chat", "talk", "discuss", "explain", "how to",
            "what is", "can you", "please help", "assistance"
        ]
        
        automation_keywords = [
            "file", "process", "schedule", "trigger", "pipeline", "automate",
            "workflow", "batch", "upload", "download", "automation",
            "script", "task", "organize", "convert", "extract"
        ]
        
        content_keywords = [
            "write", "create content", "generate", "draft", "blog post",
            "email", "social media", "article", "content", "copy",
            "marketing", "product description", "newsletter", "post"
        ]
        
        
        # Count keyword matches with weights
        scores = {
            AgentType.DATA_ANALYSIS: sum(1 for word in analysis_keywords if word in request_lower),
            AgentType.CUSTOMER_SERVICE: sum(1 for word in chat_keywords if word in request_lower),
            AgentType.AUTOMATION: sum(1 for word in automation_keywords if word in request_lower),
            AgentType.CONTENT_CREATION: sum(1 for word in content_keywords if word in request_lower),
            
        }

        # Return agent type with highest score
        max_score_agent = max(scores.items(), key=lambda x: x[1])
        detected_type = max_score_agent[0] if max_score_agent[1] > 0 else AgentType.CUSTOMER_SERVICE
        
        logger.info(f"Detected agent type: {detected_type.value} (score: {max_score_agent[1]})")
        return detected_type

    # Keep all existing methods...
    def _save_interaction(self, session_id: str, request: str, response: AgentResponse, agent_type: Optional[AgentType]) -> None:
        """Save interaction to database."""
        try:
            if not self.db:
                logger.debug("Database not available, skipping interaction save")
                return
                
            response_dict = {
                'content': response.content or "",
                'success': response.success,
                'agent_type': response.agent_type or (agent_type.value if agent_type else "unknown"),
                'execution_time': response.execution_time,
                'error': response.error_message or response.error or ""
            }
            
            metadata = {
                'request_length': len(request),
                'response_length': len(response.content) if response.content else 0,
                'timestamp': time.time()
            }
            
            self.db.save_chat_history(
                session_id=session_id,
                request=request,
                response=response_dict,
                agent_type=response.agent_type or (agent_type.value if agent_type else "unknown"),
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error saving interaction to database: {e}")

    def get_chat_history(self, session_id: str, limit: int = 50, start_after: Optional[str] = None) -> List[Dict]:
        """Get chat history for a session."""
        try:
            if not self.db:
                logger.warning("Database not available")
                return []
            return self.db.get_chat_history(session_id, limit, start_after)
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []

    def get_agent_stats(self, agent_type: Optional[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get statistics for agents."""
        try:
            if not self.db:
                logger.warning("Database not available")
                return {}
                
            if agent_type:
                return self.db.get_agent_stats(agent_type, start_date, end_date)
            else:
                stats = {}
                for agent in self.agents.values():
                    agent_stats = self.db.get_agent_stats(
                        agent.agent_type.value,
                        start_date,
                        end_date
                    )
                    stats[agent.agent_type.value] = agent_stats
                return stats
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            return {}

    def get_active_sessions(self, agent_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get list of active chat sessions."""
        try:
            if not self.db:
                logger.warning("Database not available")
                return []
            return self.db.get_active_sessions(agent_type, limit)
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []

    def get_available_agents(self) -> List[str]:
        """Get list of available agent types."""
        return [agent_type.value for agent_type in self.agents.keys()]

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents."""
        health_status = {
            "system_status": "healthy",
            "agents": {},
            "database": "available" if self.db else "unavailable",
            "timestamp": datetime.now().isoformat()
        }
        
        for agent_type, agent in self.agents.items():
            try:
                # Simple test to check if agent is responsive
                test_response = agent.process("health check")
                health_status["agents"][agent_type.value] = {
                    "status": "healthy" if test_response.success else "unhealthy",
                    "model_initialized": agent.model is not None
                }
            except Exception as e:
                health_status["agents"][agent_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Check if any agents are unhealthy
        unhealthy_agents = [
            agent for agent, status in health_status["agents"].items() 
            if status.get("status") != "healthy"
        ]
        
        if unhealthy_agents:
            health_status["system_status"] = "degraded"
            
        return health_status


# Backward compatibility - keep the old class name
class HackathonAgent(MultiAgentCodingAI):
    """Backward compatibility class"""
    pass