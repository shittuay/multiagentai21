#!/usr/bin/env python3
"""
Base Agent Class
Provides the foundation for all AI agents in the MultiAgentAI21 system
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

from src.types import AgentType
from src.utils.api_compliance import get_rate_limiter, ComplianceValidator
from src.utils.compliance_monitor import get_compliance_monitor
from src.config.compliance_config import API_LIMITS

# Load environment variables from .env file with robust fallback
try:
    from src.utils.env_loader import ensure_env_loaded, get_api_key
    ensure_env_loaded()
except ImportError:
    # Fallback to simple load_dotenv if env_loader is not available
    load_dotenv()

logger = logging.getLogger(__name__)

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
        
        # Compliance and rate limiting
        self.rate_limiter = get_rate_limiter()
        self.compliance_monitor = get_compliance_monitor()
        self.compliance_enabled = True
        
        # Configure rate limiter with current limits
        from src.utils.api_compliance import configure_rate_limiter
        configure_rate_limiter(
            requests_per_minute=API_LIMITS.get('requests_per_minute', 5),
            requests_per_hour=API_LIMITS.get('requests_per_hour', 50), 
            requests_per_day=API_LIMITS.get('requests_per_day', 200),
            min_request_interval=API_LIMITS.get('min_request_interval', 12.0)
        )
        
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the AI model for the agent - OpenRouter ONLY."""
        try:
            # ONLY use OpenRouter - Gemini disabled due to terms of service violations
            openrouter_key = os.getenv('OPENROUTER_API_KEY')

            if not openrouter_key:
                logger.error("⚠️ OPENROUTER_API_KEY not found in environment variables!")
                logger.error("Please add your OpenRouter API key to app/.env file:")
                logger.error("OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE")
                logger.error("Get your key at: https://openrouter.ai/keys")
                self.model = self._create_fallback_model()
                return

            try:
                from src.utils.openrouter_client import configure_openrouter, GenerativeModel
                configure_openrouter(api_key=openrouter_key)

                # Determine best model for agent type
                use_case_map = {
                    AgentType.CONTENT_CREATION: 'content_creation',
                    AgentType.DATA_ANALYSIS: 'data_analysis',
                    AgentType.AUTOMATION: 'devops',
                    AgentType.CUSTOMER_SERVICE: 'customer_service',
                }
                use_case = use_case_map.get(self.agent_type, 'general')

                self.model = GenerativeModel(use_case)
                logger.info(f"✅ Initialized OpenRouter for {self.agent_type.value} with use_case: {use_case}")
                return

            except Exception as e:
                logger.error(f"❌ OpenRouter initialization failed: {e}")
                logger.error("Please check:")
                logger.error("1. OPENROUTER_API_KEY is correctly set in app/.env")
                logger.error("2. You have credits at https://openrouter.ai/credits")
                logger.error("3. Your API key is valid (starts with sk-or-v1-)")
                self.model = self._create_fallback_model()
                return

        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            self.model = self._create_fallback_model()

    def _create_fallback_model(self):
        """Create a fallback model for when API quota is exceeded."""
        logger.info("Creating fallback model due to API limitations")
        
        class FallbackModel:
            """Fallback model that provides structured DevOps responses when API quota is exceeded."""
            
            def generate_content(self, contents):
                """Generate fallback content based on input."""
                
                # Extract the actual prompt from contents
                if isinstance(contents, list) and contents:
                    prompt = contents[-1].get("parts", [""])[0] if isinstance(contents[-1], dict) else str(contents[-1])
                elif isinstance(contents, str):
                    prompt = contents
                else:
                    prompt = str(contents)
                
                prompt_lower = prompt.lower()
                
                # Generate appropriate fallback response based on prompt content
                if "jenkins" in prompt_lower and "pipeline" in prompt_lower:
                    response_text = self._generate_jenkins_fallback()
                elif "prometheus" in prompt_lower and "monitor" in prompt_lower:
                    response_text = self._generate_prometheus_fallback()
                elif "terraform" in prompt_lower:
                    response_text = self._generate_terraform_fallback()
                elif "docker" in prompt_lower or "container" in prompt_lower:
                    response_text = self._generate_docker_fallback()
                elif "kubernetes" in prompt_lower or "k8s" in prompt_lower:
                    response_text = self._generate_k8s_fallback()
                else:
                    response_text = self._generate_general_devops_fallback()
                
                # Create mock response object
                class MockResponse:
                    def __init__(self, text):
                        self.text = text
                
                return MockResponse(response_text)
            
            def _generate_jenkins_fallback(self):
                return """# Jenkins CI/CD Pipeline for Python Applications

**Complete Jenkinsfile:**

```groovy
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        VENV_NAME = 'myapp-venv'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                python${PYTHON_VERSION} -m venv ${VENV_NAME}
                source ${VENV_NAME}/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }
        
        stage('Lint & Test') {
            steps {
                sh '''
                source ${VENV_NAME}/bin/activate
                flake8 . --max-line-length=88
                pytest tests/ -v --cov=src --cov-report=xml
                '''
            }
        }
        
        stage('Build') {
            steps {
                sh '''
                source ${VENV_NAME}/bin/activate
                python setup.py bdist_wheel
                '''
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                source ${VENV_NAME}/bin/activate
                # Add deployment commands here
                echo "Deploying to production..."
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
```

**Setup Instructions:**
1. Create a new Pipeline job in Jenkins
2. Configure Git repository
3. Set up webhook triggers
4. Add required credentials
5. Install Python and pip on Jenkins agents

**Note:** This is a fallback response due to API quota limitations. For production use, consider upgrading your Google Cloud quota."""
            
            def _generate_prometheus_fallback(self):
                return r"""# Prometheus Monitoring Setup for Microservices

## 1. Prometheus Configuration (prometheus.yml)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'microservices'
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## 2. Alert Rules (alert_rules.yml)

```yaml
groups:
  - name: microservices_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 10% for 5 minutes"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is above 500ms"
```

## 3. Docker Compose Setup

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

**Note:** This is a fallback response due to API quota limitations."""
            
            def _generate_terraform_fallback(self):
                return """# Terraform AWS Infrastructure Configuration

## main.tf
```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_subnet" "public" {
  count = length(var.public_subnets)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}
```

## variables.tf
```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "myproject"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}
```

**Deployment Commands:**
```bash
terraform init
terraform plan
terraform apply
```

**Note:** This is a fallback response due to API quota limitations."""
            
            def _generate_docker_fallback(self):
                return """# Docker Containerization Strategy

## Multi-stage Dockerfile
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Production stage
FROM node:18-alpine AS production
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
USER node
CMD ["npm", "start"]
```

## Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    volumes:
      - ./logs:/app/logs
    depends_on:
      - redis
      - postgres
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
      
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Build Commands:**
```bash
docker build -t myapp .
docker-compose up -d
```

**Note:** This is a fallback response due to API quota limitations."""
            
            def _generate_k8s_fallback(self):
                return """# Kubernetes Deployment Manifests

## deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-url
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

## hpa.yaml
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Deploy Commands:**
```bash
kubectl apply -f deployment.yaml
kubectl apply -f hpa.yaml
```

**Note:** This is a fallback response due to API quota limitations."""
            
            def _generate_general_devops_fallback(self):
                return """# DevOps Automation Solution

## Overview
This is a fallback response due to Google Cloud API quota limitations. For full AI-powered responses, please:

1. **Check your Google Cloud quota**: Visit Google Cloud Console → IAM & Admin → Quotas
2. **Request quota increase**: Request higher limits for Generative AI API
3. **Wait for quota reset**: Quotas typically reset hourly/daily
4. **Use alternative API keys**: If available

## General DevOps Best Practices

### Infrastructure as Code
- Use Terraform for cloud infrastructure
- Implement GitOps workflows
- Version control all configurations

### CI/CD Pipelines
- Implement automated testing
- Use multi-stage deployments
- Monitor deployment metrics

### Monitoring & Observability
- Set up comprehensive logging
- Implement metrics collection
- Create meaningful alerts

### Security
- Implement secrets management
- Regular security scanning
- Follow principle of least privilege

**Note:** This is a limited fallback response. Upgrade your API quota for full DevOps automation assistance."""
        
        return FallbackModel()

    def _process_with_model(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Process prompt with the AI model, including compliance checks, rate limiting and learning."""
        start_time = time.time()
        
        try:
            if not self.model:
                raise ValueError("Model not initialized")
            
            # COMPLIANCE CHECK: Validate content before processing
            if self.compliance_enabled:
                is_compliant, violations = ComplianceValidator.validate_content(prompt)
                if not is_compliant:
                    error_msg = f"Request blocked due to policy violations: {'; '.join(violations)}"
                    logger.warning(error_msg)
                    self.rate_limiter.record_request(success=False)
                    raise ValueError(error_msg)
                
                # RATE LIMITING: Check and wait if needed
                if not self.rate_limiter.wait_if_needed(prompt):
                    error_msg = "Request blocked by rate limiter or compliance check"
                    logger.warning(error_msg)
                    self.rate_limiter.record_request(success=False)
                    raise ValueError(error_msg)
            
            # Apply adaptive prompt improvements
            enhanced_prompt = self._apply_adaptive_improvements(prompt)
            
            logger.info(f"Processing API request (length: {len(enhanced_prompt)} chars)")
            
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
            
            # MAKE API REQUEST with proper error tracking
            try:
                response = self.model.generate_content(contents)

                # Record successful request
                self.rate_limiter.record_request(success=True, quota_exceeded=False)

                if hasattr(response, 'text') and response.text:
                    response_text = response.text.strip()

                    # Log compliance event
                    self.compliance_monitor.log_event(
                        event_type='api_request',
                        agent_type=self.agent_type.value,
                        content_length=len(enhanced_prompt),
                        success=True,
                        metadata={
                            'response_length': len(response_text),
                            'processing_time': time.time() - start_time
                        }
                    )

                    # Record performance metrics
                    self._record_performance_metrics(True, time.time() - start_time)

                    # Learn from this interaction
                    self._learn_from_interaction(prompt, response_text, True, time.time() - start_time)

                    logger.info(f"API request successful (response length: {len(response_text)} chars)")
                    return response_text

                elif hasattr(response, 'parts') and response.parts:
                    response_text = ''.join([part.text for part in response.parts if hasattr(part, 'text')])

                    # Record performance metrics
                    self._record_performance_metrics(True, time.time() - start_time)

                    # Learn from this interaction
                    self._learn_from_interaction(prompt, response_text, True, time.time() - start_time)

                    return response_text
                else:
                    # Record failure
                    self._record_performance_metrics(False, time.time() - start_time)
                    return "Error: No text content in model response"

            except Exception as api_error:
                error_msg = str(api_error).lower()
                quota_exceeded = "quota" in error_msg or "rate" in error_msg or "429" in error_msg

                # Record failed request with quota info
                self.rate_limiter.record_request(success=False, quota_exceeded=quota_exceeded)

                # Log compliance event for failure
                event_type = 'quota_exceeded' if quota_exceeded else 'api_request'
                self.compliance_monitor.log_event(
                    event_type=event_type,
                    agent_type=self.agent_type.value,
                    content_length=len(enhanced_prompt),
                    success=False,
                    error_message=str(api_error),
                    metadata={'processing_time': time.time() - start_time}
                )

                if quota_exceeded:
                    logger.error(f"API quota/rate limit exceeded: {api_error}")
                    raise ValueError(f"API quota exceeded: {api_error}")
                else:
                    logger.error(f"API request failed: {api_error}")
                    raise
                
        except Exception as e:
            # Record failure
            self._record_performance_metrics(False, time.time() - start_time)
            logger.error(f"Error in _process_with_model: {e}")
            return f"Error processing request: {str(e)}"

    def _record_performance_metrics(self, success: bool, response_time: float):
        """Record performance metrics for the agent."""
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
        """Learn from the interaction to improve future responses."""
        # Record the interaction
        self.learning_history.append({
            'prompt': prompt,
            'response': response,
            'success': success,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 interactions
        if len(self.learning_history) > 100:
            self.learning_history = self.learning_history[-100:]
        
        # Learn from failures
        if not success:
            self.performance_metrics['improvement_suggestions'].append({
                'type': 'failure_analysis',
                'suggestion': f'Failed to process: {prompt[:100]}...',
                'timestamp': datetime.now().isoformat()
            })

    def _apply_adaptive_improvements(self, prompt: str) -> str:
        """Apply adaptive improvements to the prompt based on learning."""
        # Simple adaptive improvements - can be enhanced
        for pattern, improvement in self.adaptive_prompts.items():
            if pattern.lower() in prompt.lower():
                prompt = f"{improvement}\n\n{prompt}"
                break
        return prompt

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

    @abstractmethod
    def process(self, input_data: str, session_id: Optional[str] = None, **kwargs) -> Any:
        """Process input data and return a response."""
        pass

