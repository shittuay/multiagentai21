#!/usr/bin/env python3
"""
Powerful DevOps Automation Agent
Handles complex automation tasks including infrastructure, CI/CD, monitoring, and more
"""

import logging
import os
import time
import json
import subprocess
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import google.generativeai as genai
from pathlib import Path
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Optional imports for advanced features
try:
    import yaml
except ImportError:
    yaml = None
    logging.warning("PyYAML not available - YAML features disabled")

try:
    import docker
except ImportError:
    docker = None
    logging.warning("Docker SDK not available - Docker features disabled")

try:
    import kubernetes
except ImportError:
    kubernetes = None
    logging.warning("Kubernetes SDK not available - K8s features disabled")

from src.base_agent import BaseAgent
from src.types import AgentType, AgentResponse

logger = logging.getLogger(__name__)

class DevOpsAutomationAgent(BaseAgent):
    """DevOps automation agent that properly inherits from BaseAgent."""

    def __init__(self):
        # Don't call _initialize_model here - BaseAgent does it
        super().__init__(AgentType.AUTOMATION)
        self.name = "DevOpsAutomationAgent"
        self.description = "Powerful DevOps automation specialist for infrastructure, CI/CD, and operations"
        
        # Store chat history and other state
        self.chat_history = []
        self.files = []
        
        # DevOps capabilities
        self.capabilities = {
            "infrastructure": {
                "terraform": "Infrastructure as Code with Terraform",
                "ansible": "Configuration management with Ansible",
                "cloudformation": "AWS CloudFormation templates",
                "docker": "Container automation and orchestration",
                "kubernetes": "K8s cluster management and deployment",
                "helm": "Kubernetes package management"
            },
            "ci_cd": {
                "jenkins": "Jenkins pipeline automation",
                "gitlab_ci": "GitLab CI/CD pipelines",
                "github_actions": "GitHub Actions workflows",
                "azure_devops": "Azure DevOps pipelines",
                "argo_cd": "GitOps continuous deployment"
            },
            "monitoring": {
                "prometheus": "Metrics collection and alerting",
                "grafana": "Monitoring dashboards",
                "elk": "Log aggregation and analysis",
                "datadog": "Application performance monitoring",
                "new_relic": "APM and infrastructure monitoring"
            },
            "cloud": {
                "aws": "Amazon Web Services automation",
                "azure": "Microsoft Azure automation",
                "gcp": "Google Cloud Platform automation",
                "digitalocean": "DigitalOcean automation"
            },
            "security": {
                "iam": "Identity and access management",
                "secrets": "Secrets management (Vault, AWS Secrets Manager)",
                "compliance": "Security compliance automation",
                "scanning": "Vulnerability scanning and remediation"
            },
            "databases": {
                "postgresql": "PostgreSQL automation",
                "mysql": "MySQL automation",
                "mongodb": "MongoDB automation",
                "redis": "Redis automation",
                "backups": "Database backup and recovery"
            }
        }

    def debug_info(self):
        """Print debug information about the agent."""
        logger.info(f"DevOpsAutomationAgent Debug Info:")
        logger.info(f"  - Model initialized: {self.model is not None}")
        logger.info(f"  - Agent type: {self.agent_type}")
        logger.info(f"  - Capabilities: {list(self.capabilities.keys())}")
        
        if self.model:
            logger.info(f"  - Model name: {getattr(self.model, 'model_name', 'Unknown')}")
        
        api_key = os.getenv("GOOGLE_API_KEY")
        logger.info(f"  - API Key set: {api_key is not None}")
        if api_key:
            logger.info(f"  - API Key length: {len(api_key)}")

    def _process_with_model(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Process input using the model - required by BaseAgent."""
        try:
            # Determine the type of automation task
            task_type = self._determine_task_type(prompt)
            logger.info(f"DevOps task type detected: {task_type}")
            
            # Route to appropriate handler
            if task_type == "infrastructure":
                response = self._handle_infrastructure_automation(prompt, chat_history)
            elif task_type == "ci_cd":
                response = self._handle_cicd_automation(prompt, chat_history)
            elif task_type == "monitoring":
                response = self._handle_monitoring_automation(prompt, chat_history)
            elif task_type == "cloud":
                response = self._handle_cloud_automation(prompt, chat_history)
            elif task_type == "security":
                response = self._handle_security_automation(prompt, chat_history)
            elif task_type == "database":
                response = self._handle_database_automation(prompt, chat_history)
            elif task_type == "container":
                response = self._handle_container_automation(prompt, chat_history)
            else:
                response = self._handle_general_automation(prompt, chat_history)
            
            return response if response else "Error: No response generated"
            
        except Exception as e:
            logger.error(f"Error in _process_with_model: {e}")
            return f"Error processing request: {str(e)}"

    def process(self, input_data: str, session_id: Optional[str] = None, **kwargs) -> AgentResponse:
        """Process input data and return a response."""
        try:
            # Get chat history from kwargs if provided
            chat_history = kwargs.get('chat_history', [])
            files = kwargs.get('files', [])
            
            # Store the additional parameters
            if chat_history:
                self.chat_history = chat_history
            if files:
                self.files = files
            
            # Process using the model
            response_text = self._process_with_model(input_data, chat_history)
            
            return AgentResponse(
                content=response_text,
                agent_type=self.agent_type.value,
                metadata={
                    'task_type': self._determine_task_type(input_data),
                    'capabilities_used': self._get_used_capabilities(self._determine_task_type(input_data)),
                    'session_id': session_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error in process: {e}")
            return AgentResponse(
                content=f"Error processing request: {str(e)}",
                agent_type=self.agent_type.value,
                success=False,
                error=str(e),
                metadata={'session_id': session_id}
            )

    def _determine_task_type(self, input_data: str) -> str:
        """Determine the type of DevOps task from the input."""
        input_lower = input_data.lower()
        
        # Infrastructure keywords
        infra_keywords = ["terraform", "ansible", "infrastructure", "provision", "deploy", "infra", "iac"]
        if any(keyword in input_lower for keyword in infra_keywords):
            return "infrastructure"
        
        # CI/CD keywords
        cicd_keywords = ["pipeline", "ci/cd", "jenkins", "gitlab", "github actions", "azure devops", "deployment"]
        if any(keyword in input_lower for keyword in cicd_keywords):
            return "ci_cd"
        
        # Monitoring keywords
        monitoring_keywords = ["monitor", "alert", "prometheus", "grafana", "elk", "logging", "metrics"]
        if any(keyword in input_lower for keyword in monitoring_keywords):
            return "monitoring"
        
        # Cloud keywords
        cloud_keywords = ["aws", "azure", "gcp", "cloud", "ec2", "s3", "lambda", "kubernetes"]
        if any(keyword in input_lower for keyword in cloud_keywords):
            return "cloud"
        
        # Security keywords
        security_keywords = ["security", "iam", "vault", "secrets", "compliance", "scan", "vulnerability"]
        if any(keyword in input_lower for keyword in security_keywords):
            return "security"
        
        # Database keywords
        db_keywords = ["database", "postgres", "mysql", "mongodb", "redis", "backup", "migration"]
        if any(keyword in input_lower for keyword in db_keywords):
            return "database"
        
        # Container keywords
        container_keywords = ["docker", "container", "kubernetes", "k8s", "helm", "pod", "deployment"]
        if any(keyword in input_lower for keyword in container_keywords):
            return "container"
        
        return "general"

    def _handle_infrastructure_automation(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Handle infrastructure automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer. The user needs COMPLETE, WORKING INFRASTRUCTURE CODE.

        User Request: {input_data}

        CRITICAL: Provide actual working code files, not just explanations!

        Response Format:
        1. **Working Code First** (complete files with proper syntax)
        2. **Usage Commands** (exact commands to run)
        3. **Brief Explanation** (what the code does)

        For Terraform requests, provide:
        - Complete .tf files (main.tf, variables.tf, outputs.tf)
        - terraform init, plan, apply commands
        - Provider configurations
        - Resource blocks with all required arguments

        For Ansible requests, provide:
        - Complete playbook.yml with tasks
        - inventory file if needed
        - ansible-playbook run commands
        - Variable definitions

        For CloudFormation requests, provide:
        - Complete template.yaml/json
        - AWS CLI deployment commands
        - Parameters and outputs

        CODE REQUIREMENTS:
        - Complete, runnable files
        - Proper resource names and references
        - Security groups, IAM policies where needed
        - Comments explaining complex sections
        - Production-ready configurations
        - Error handling and validation

        START WITH THE WORKING CODE IMMEDIATELY!
        """
        
        return self._generate_response(prompt, chat_history)

    def _handle_cicd_automation(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Handle CI/CD pipeline automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer. The user needs COMPLETE, WORKING CI/CD PIPELINE CODE.

        User Request: {input_data}

        CRITICAL: Provide actual working pipeline files, not explanations!

        Response Format:
        1. **Complete Pipeline File** (working configuration)
        2. **Setup Commands** (how to implement)
        3. **Trigger Instructions** (how to run)

        For Jenkins requests, provide:
        - Complete Jenkinsfile with all stages
        - Pipeline steps and post actions
        - Environment variables and credentials
        - Build, test, deploy stages

        For GitHub Actions, provide:
        - Complete .github/workflows/[name].yml
        - All workflow steps with proper actions
        - Secrets and environment variables
        - Matrix builds if appropriate

        For GitLab CI, provide:
        - Complete .gitlab-ci.yml
        - All stages and job definitions
        - Docker images and scripts
        - Deployment configurations

        CODE REQUIREMENTS:
        - Complete, functional pipeline files
        - Proper syntax and indentation
        - Error handling and notifications
        - Security scanning integration
        - Deployment strategies
        - Environment-specific configurations

        PROVIDE THE WORKING PIPELINE CODE FIRST!
        """
        
        return self._generate_response(prompt, chat_history)

    def _handle_monitoring_automation(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Handle monitoring and observability automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer specializing in monitoring, observability, and alerting.
        
        User Request: {input_data}
        
        Provide a comprehensive response including:
        1. **Monitoring Strategy**: What to monitor and why
        2. **Tool Stack**: Recommended monitoring tools (Prometheus, Grafana, ELK, etc.)
        3. **Configuration**: Monitoring configuration and dashboards
        4. **Alerting**: Alert rules and notification channels
        5. **Logging**: Log aggregation and analysis setup
        6. **Metrics**: Key performance indicators and SLIs/SLOs
        7. **Troubleshooting**: Common issues and resolution steps
        
        Focus on:
        - Observability best practices
        - Alert fatigue prevention
        - Performance impact minimization
        - Data retention and compliance
        - Incident response automation
        - Capacity planning
        
        Provide actionable monitoring solutions.
        """
        
        return self._generate_response(prompt, chat_history)

    def _handle_cloud_automation(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Handle cloud platform automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer specializing in cloud platform automation (AWS, Azure, GCP).
        
        User Request: {input_data}
        
        Provide a comprehensive response including:
        1. **Cloud Architecture**: Optimal cloud architecture design
        2. **Service Selection**: Best cloud services for the use case
        3. **Automation Scripts**: Cloud automation scripts and templates
        4. **Cost Optimization**: Cost management and optimization strategies
        5. **Security**: Cloud security best practices and compliance
        6. **Scaling**: Auto-scaling and performance optimization
        7. **Disaster Recovery**: Backup and recovery strategies
        
        Focus on:
        - Multi-cloud strategies
        - Serverless architectures
        - Container orchestration
        - Infrastructure as Code
        - Security and compliance
        - Cost management
        - Performance optimization
        
        Provide cloud-native automation solutions.
        """
        
        return self._generate_response(prompt, chat_history)

    def _handle_security_automation(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Handle security automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer specializing in security automation and compliance.
        
        User Request: {input_data}
        
        Provide a comprehensive response including:
        1. **Security Assessment**: Security requirements and risk analysis
        2. **Tool Integration**: Security tools and scanning automation
        3. **Compliance**: Compliance frameworks and automation
        4. **Secrets Management**: Secure secrets and credential management
        5. **Access Control**: IAM and access management automation
        6. **Vulnerability Management**: Vulnerability scanning and remediation
        7. **Incident Response**: Security incident response automation
        
        Focus on:
        - Security best practices
        - Compliance automation
        - Zero-trust architecture
        - Security monitoring
        - Incident response
        - Risk management
        - Audit automation
        
        Provide security-first automation solutions.
        """
        
        return self._generate_response(prompt, chat_history)

    def _handle_database_automation(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Handle database automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer specializing in database automation and management.
        
        User Request: {input_data}
        
        Provide a comprehensive response including:
        1. **Database Strategy**: Database selection and architecture
        2. **Automation Scripts**: Database provisioning and configuration
        3. **Backup Strategy**: Automated backup and recovery procedures
        4. **Migration Tools**: Database migration and versioning
        5. **Performance Optimization**: Database performance tuning
        6. **Scaling**: Database scaling and replication strategies
        7. **Monitoring**: Database monitoring and alerting
        
        Focus on:
        - Database as Code
        - Backup and recovery
        - Performance optimization
        - Security and compliance
        - High availability
        - Data migration
        - Monitoring and alerting
        
        Provide database automation solutions.
        """
        
        return self._generate_response(prompt, chat_history)

    def _handle_container_automation(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Handle container and Kubernetes automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer. The user needs WORKING, PRODUCTION-READY CODE.

        User Request: {input_data}

        IMPORTANT: You MUST provide actual working code/configuration files, not just explanations!

        Response Format:
        1. **Brief Explanation** (2-3 sentences max)
        2. **Complete Working Code** with proper syntax
        3. **Usage Instructions** (how to run/deploy)
        4. **Best Practices** (security, optimization)

        For Docker requests, provide:
        - Complete Dockerfile with all stages
        - docker-compose.yml if needed
        - Build and run commands
        - Security optimizations

        For Kubernetes requests, provide:
        - Complete YAML manifests
        - kubectl apply commands
        - Service definitions
        - ConfigMaps/Secrets if needed

        CODE REQUIREMENTS:
        - Use proper syntax and formatting
        - Include all necessary dependencies
        - Add security best practices
        - Use multi-stage builds when appropriate
        - Include comments explaining key sections
        - Provide complete, runnable examples

        Start your response with the working code, not lengthy explanations!
        """
        
        return self._generate_response(prompt, chat_history)

    def _handle_general_automation(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Handle general automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer specializing in automation and process optimization.
        
        User Request: {input_data}
        
        Provide a comprehensive response including:
        1. **Process Analysis**: Current process analysis and optimization opportunities
        2. **Automation Strategy**: Automation strategy and tool selection
        3. **Implementation Plan**: Step-by-step implementation plan
        4. **Code Examples**: Automation scripts and configurations
        5. **Best Practices**: Automation best practices and patterns
        6. **Monitoring**: Automation monitoring and error handling
        7. **Maintenance**: Ongoing maintenance and improvement strategies
        
        Focus on:
        - Process optimization
        - Tool selection
        - Implementation strategy
        - Error handling
        - Monitoring and alerting
        - Documentation
        - Continuous improvement
        
        Provide comprehensive automation solutions.
        """
        
        return self._generate_response(prompt, chat_history)

    def _generate_response(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Generate response using the AI model."""
        try:
            if not self.model:
                return "Error: AI model not initialized"
            
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
            contents.append({"role": "user", "parts": [prompt]})
            
            # Use generate_content with the entire 'contents' list
            response = self.model.generate_content(contents)
            
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif hasattr(response, 'parts') and response.parts:
                return ''.join([part.text for part in response.parts if hasattr(part, 'text')])
            else:
                return "Error: No text content in model response"
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"

    def _get_used_capabilities(self, task_type: str) -> List[str]:
        """Get the capabilities used for a specific task type."""
        if task_type in self.capabilities:
            return list(self.capabilities[task_type].keys())
        return []

    def test_model_connection(self) -> tuple[bool, str]:
        """Test if the model can be reached and is working."""
        try:
            if not self.model:
                return False, "Model not initialized"
            
            test_response = self.model.generate_content("Test connection")
            if test_response and hasattr(test_response, 'text'):
                return True, "Model connection successful"
            else:
                return False, "Model returned empty response"
        except Exception as e:
            return False, f"Model connection failed: {str(e)}"

    def generate_terraform_config(self, requirements: Dict[str, Any]) -> str:
        """Generate Terraform configuration based on requirements."""
        # This would generate actual Terraform code
        return f"""
# Generated Terraform Configuration
# Requirements: {json.dumps(requirements, indent=2)}

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

# Add your infrastructure resources here based on requirements
"""

    def generate_dockerfile(self, application_type: str, requirements: Dict[str, Any]) -> str:
        """Generate Dockerfile based on application type and requirements."""
        if application_type == "python":
            return f"""
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {requirements.get('port', 8000)}

CMD ["python", "app.py"]
"""
        elif application_type == "nodejs":
            return f"""
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE {requirements.get('port', 3000)}

CMD ["npm", "start"]
"""
        else:
            return "# Generic Dockerfile template"

    def generate_kubernetes_manifests(self, application_name: str, requirements: Dict[str, Any]) -> str:
        """Generate Kubernetes manifests."""
        return f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {application_name}
spec:
  replicas: {requirements.get('replicas', 3)}
  selector:
    matchLabels:
      app: {application_name}
  template:
    metadata:
      labels:
        app: {application_name}
    spec:
      containers:
      - name: {application_name}
        image: {requirements.get('image', 'your-app:latest')}
        ports:
        - containerPort: {requirements.get('port', 8080)}
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: {application_name}-service
spec:
  selector:
    app: {application_name}
  ports:
  - port: 80
    targetPort: {requirements.get('port', 8080)}
  type: ClusterIP
"""

    def generate_jenkins_pipeline(self, project_type: str, requirements: Dict[str, Any]) -> str:
        """Generate Jenkins pipeline configuration."""
        return f"""
pipeline {{
    agent any
    
    environment {{
        PROJECT_NAME = '{requirements.get('project_name', 'my-project')}'
        DOCKER_IMAGE = '{requirements.get('docker_image', 'my-app')}'
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Build') {{
            steps {{
                script {{
                    if ('{project_type}' == 'python') {{
                        sh 'pip install -r requirements.txt'
                    }} else if ('{project_type}' == 'nodejs') {{
                        sh 'npm install'
                    }}
                }}
            }}
        }}
        
        stage('Test') {{
            steps {{
                script {{
                    if ('{project_type}' == 'python') {{
                        sh 'python -m pytest'
                    }} else if ('{project_type}' == 'nodejs') {{
                        sh 'npm test'
                    }}
                }}
            }}
        }}
        
        stage('Build Docker Image') {{
            steps {{
                sh 'docker build -t $DOCKER_IMAGE:$BUILD_NUMBER .'
            }}
        }}
        
        stage('Deploy') {{
            steps {{
                sh 'docker push $DOCKER_IMAGE:$BUILD_NUMBER'
                // Add deployment steps here
            }}
        }}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
    }}
}}
"""

