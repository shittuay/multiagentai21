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

from .base import BaseAgent
from src.types import AgentType, AgentResponse

logger = logging.getLogger(__name__)

class DevOpsAutomationAgent(BaseAgent):
    """
    A powerful DevOps automation agent capable of handling complex automation tasks:
    - Infrastructure as Code (Terraform, CloudFormation, Ansible)
    - CI/CD Pipeline automation (Jenkins, GitLab CI, GitHub Actions, Azure DevOps)
    - Container orchestration (Docker, Kubernetes)
    - Monitoring and logging (Prometheus, Grafana, ELK Stack)
    - Cloud platform automation (AWS, Azure, GCP)
    - Security automation (IAM, secrets management, compliance)
    - Database automation (backups, migrations, scaling)
    - Network automation (load balancers, firewalls, DNS)
    """

    def __init__(self):
        super().__init__(AgentType.AUTOMATION)
        self.name = "DevOpsAutomationAgent"
        self.description = "Powerful DevOps automation specialist for infrastructure, CI/CD, and operations"
        
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

    def _initialize_model(self):
        """Initialize the AI model for DevOps automation tasks."""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GOOGLE_API_KEY not found")
                return None
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-pro")
            logger.info("DevOps Automation Agent model initialized successfully")
            return model
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            return None

    def process(self, input_data: str, session_id: Optional[str] = None) -> AgentResponse:
        """Process DevOps automation requests."""
        start_time = time.time()
        
        try:
            # Determine the type of automation task
            task_type = self._determine_task_type(input_data)
            
            # Route to appropriate handler
            if task_type == "infrastructure":
                response = self._handle_infrastructure_automation(input_data)
            elif task_type == "ci_cd":
                response = self._handle_cicd_automation(input_data)
            elif task_type == "monitoring":
                response = self._handle_monitoring_automation(input_data)
            elif task_type == "cloud":
                response = self._handle_cloud_automation(input_data)
            elif task_type == "security":
                response = self._handle_security_automation(input_data)
            elif task_type == "database":
                response = self._handle_database_automation(input_data)
            elif task_type == "container":
                response = self._handle_container_automation(input_data)
            else:
                response = self._handle_general_automation(input_data)
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                content=response,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=execution_time,
                metadata={
                    'task_type': task_type,
                    'capabilities_used': self._get_used_capabilities(task_type),
                    'session_id': session_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error in DevOpsAutomationAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"DevOps automation error: {str(e)}"
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

    def _handle_infrastructure_automation(self, input_data: str) -> str:
        """Handle infrastructure automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer specializing in Infrastructure as Code and automation.
        
        User Request: {input_data}
        
        Provide a comprehensive response including:
        1. **Analysis**: What infrastructure components are needed
        2. **Tools**: Recommended tools (Terraform, Ansible, CloudFormation, etc.)
        3. **Code Examples**: Practical code snippets and configurations
        4. **Best Practices**: Security, scalability, and maintainability considerations
        5. **Implementation Steps**: Step-by-step guide for implementation
        6. **Monitoring**: How to monitor and maintain the infrastructure
        
        Focus on:
        - Infrastructure as Code principles
        - Security best practices
        - Scalability and performance
        - Cost optimization
        - Disaster recovery
        - Compliance requirements
        
        Provide actionable, production-ready solutions.
        """
        
        return self._generate_response(prompt)

    def _handle_cicd_automation(self, input_data: str) -> str:
        """Handle CI/CD pipeline automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer specializing in CI/CD pipeline automation.
        
        User Request: {input_data}
        
        Provide a comprehensive response including:
        1. **Pipeline Design**: Optimal CI/CD pipeline architecture
        2. **Tool Selection**: Best tools for the specific use case (Jenkins, GitLab CI, GitHub Actions, etc.)
        3. **Configuration**: Pipeline configuration files and scripts
        4. **Security**: Security scanning and compliance checks
        5. **Testing Strategy**: Automated testing integration
        6. **Deployment Strategy**: Blue-green, canary, or rolling deployments
        7. **Monitoring**: Pipeline monitoring and alerting
        
        Focus on:
        - Automation best practices
        - Security and compliance
        - Performance optimization
        - Error handling and rollback strategies
        - Multi-environment deployments
        - GitOps principles
        
        Provide production-ready pipeline configurations.
        """
        
        return self._generate_response(prompt)

    def _handle_monitoring_automation(self, input_data: str) -> str:
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
        
        return self._generate_response(prompt)

    def _handle_cloud_automation(self, input_data: str) -> str:
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
        
        return self._generate_response(prompt)

    def _handle_security_automation(self, input_data: str) -> str:
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
        
        return self._generate_response(prompt)

    def _handle_database_automation(self, input_data: str) -> str:
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
        
        return self._generate_response(prompt)

    def _handle_container_automation(self, input_data: str) -> str:
        """Handle container and Kubernetes automation tasks."""
        prompt = f"""
        You are an expert DevOps engineer specializing in container orchestration and Kubernetes.
        
        User Request: {input_data}
        
        Provide a comprehensive response including:
        1. **Container Strategy**: Containerization strategy and best practices
        2. **Kubernetes Configuration**: K8s manifests and configurations
        3. **Helm Charts**: Helm chart development and deployment
        4. **Service Mesh**: Service mesh implementation (Istio, Linkerd)
        5. **Scaling**: Horizontal and vertical pod autoscaling
        6. **Security**: Container security and RBAC
        7. **Monitoring**: K8s monitoring and observability
        
        Focus on:
        - Container best practices
        - Kubernetes patterns
        - Service mesh architecture
        - Security and compliance
        - Performance optimization
        - GitOps deployment
        - Monitoring and troubleshooting
        
        Provide container-native automation solutions.
        """
        
        return self._generate_response(prompt)

    def _handle_general_automation(self, input_data: str) -> str:
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
        
        return self._generate_response(prompt)

    def _generate_response(self, prompt: str) -> str:
        """Generate response using the AI model."""
        try:
            if not self.model:
                return "Error: AI model not initialized"
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"

    def _get_used_capabilities(self, task_type: str) -> List[str]:
        """Get the capabilities used for a specific task type."""
        if task_type in self.capabilities:
            return list(self.capabilities[task_type].keys())
        return []

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
