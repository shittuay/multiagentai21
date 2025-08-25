#!/usr/bin/env python3
"""
Test script for the DevOps Automation Agent
Demonstrates capabilities across different automation domains
"""

import os
import sys
import time
from pathlib import Path

# Add the app directory to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "app"))

from src.agents.devops_automation_agent import DevOpsAutomationAgent

def test_devops_automation_agent():
    """Test the DevOps Automation Agent with various automation scenarios."""
    
    print("🚀 Testing DevOps Automation Agent")
    print("=" * 50)
    
    # Initialize the agent
    try:
        agent = DevOpsAutomationAgent()
        print("✅ DevOps Automation Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Test scenarios
    test_scenarios = [
        {
            "category": "Infrastructure as Code",
            "query": "Create a Terraform configuration for a web application with load balancer, auto-scaling group, and RDS database on AWS",
            "expected_capabilities": ["terraform", "aws"]
        },
        {
            "category": "CI/CD Pipeline",
            "query": "Design a Jenkins pipeline for a Python application with automated testing, security scanning, and deployment to Kubernetes",
            "expected_capabilities": ["jenkins", "kubernetes"]
        },
        {
            "category": "Monitoring & Observability",
            "query": "Set up Prometheus and Grafana monitoring for a microservices architecture with custom metrics and alerting",
            "expected_capabilities": ["prometheus", "grafana"]
        },
        {
            "category": "Cloud Automation",
            "query": "Automate the deployment of a serverless application using AWS Lambda, API Gateway, and DynamoDB with CloudFormation",
            "expected_capabilities": ["aws", "cloudformation"]
        },
        {
            "category": "Security Automation",
            "query": "Implement automated security scanning with vulnerability assessment, secrets management, and compliance checks",
            "expected_capabilities": ["security", "secrets", "compliance"]
        },
        {
            "category": "Database Automation",
            "query": "Create automated backup and recovery procedures for PostgreSQL with point-in-time recovery and monitoring",
            "expected_capabilities": ["postgresql", "backups"]
        },
        {
            "category": "Container Orchestration",
            "query": "Deploy a multi-tier application to Kubernetes with Helm charts, service mesh, and horizontal pod autoscaling",
            "expected_capabilities": ["kubernetes", "helm", "docker"]
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}: {scenario['category']}")
        print(f"Query: {scenario['query']}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            response = agent.process(scenario['query'])
            execution_time = time.time() - start_time
            
            if response.success:
                print(f"✅ Success (Execution time: {execution_time:.2f}s)")
                print(f"Task Type: {response.metadata.get('task_type', 'Unknown')}")
                print(f"Capabilities Used: {response.metadata.get('capabilities_used', [])}")
                
                # Show first 200 characters of response
                content_preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
                print(f"Response Preview: {content_preview}")
                
                results.append({
                    "scenario": scenario['category'],
                    "success": True,
                    "execution_time": execution_time,
                    "task_type": response.metadata.get('task_type', 'Unknown'),
                    "capabilities_used": response.metadata.get('capabilities_used', [])
                })
            else:
                print(f"❌ Failed: {response.error}")
                results.append({
                    "scenario": scenario['category'],
                    "success": False,
                    "error": response.error
                })
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                "scenario": scenario['category'],
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"✅ Successful Tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed Tests: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        avg_execution_time = sum(r['execution_time'] for r in successful_tests) / len(successful_tests)
        print(f"⏱️  Average Execution Time: {avg_execution_time:.2f}s")
        
        # Show capabilities used
        all_capabilities = []
        for result in successful_tests:
            all_capabilities.extend(result.get('capabilities_used', []))
        
        if all_capabilities:
            unique_capabilities = list(set(all_capabilities))
            print(f"🔧 Capabilities Demonstrated: {', '.join(unique_capabilities)}")
    
    if failed_tests:
        print("\n❌ Failed Test Details:")
        for result in failed_tests:
            print(f"  - {result['scenario']}: {result.get('error', 'Unknown error')}")
    
    print("\n🎯 DevOps Automation Agent Test Complete!")
    return results

def test_code_generation():
    """Test the code generation capabilities of the DevOps Automation Agent."""
    
    print("\n🔧 Testing Code Generation Capabilities")
    print("=" * 50)
    
    agent = DevOpsAutomationAgent()
    
    # Test Terraform configuration generation
    print("\n📝 Testing Terraform Configuration Generation")
    terraform_req = {
        "provider": "aws",
        "resources": ["vpc", "subnets", "ec2", "rds"],
        "environment": "production"
    }
    
    terraform_config = agent.generate_terraform_config(terraform_req)
    print("Generated Terraform Configuration:")
    print(terraform_config)
    
    # Test Dockerfile generation
    print("\n🐳 Testing Dockerfile Generation")
    docker_req = {"port": 8080}
    
    python_dockerfile = agent.generate_dockerfile("python", docker_req)
    print("Generated Python Dockerfile:")
    print(python_dockerfile)
    
    nodejs_dockerfile = agent.generate_dockerfile("nodejs", docker_req)
    print("Generated Node.js Dockerfile:")
    print(nodejs_dockerfile)
    
    # Test Kubernetes manifests generation
    print("\n☸️  Testing Kubernetes Manifests Generation")
    k8s_req = {
        "replicas": 3,
        "image": "myapp:v1.0.0",
        "port": 8080
    }
    
    k8s_manifests = agent.generate_kubernetes_manifests("myapp", k8s_req)
    print("Generated Kubernetes Manifests:")
    print(k8s_manifests)
    
    # Test Jenkins pipeline generation
    print("\n🔗 Testing Jenkins Pipeline Generation")
    jenkins_req = {
        "project_name": "my-python-app",
        "docker_image": "myapp",
        "project_type": "python"
    }
    
    jenkins_pipeline = agent.generate_jenkins_pipeline("python", jenkins_req)
    print("Generated Jenkins Pipeline:")
    print(jenkins_pipeline)

def main():
    """Main test function."""
    print("🚀 DevOps Automation Agent Comprehensive Test Suite")
    print("=" * 60)
    
    # Check if GOOGLE_API_KEY is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set")
        print("   Some features may not work properly")
        print("   Set it with: export GOOGLE_API_KEY='your-api-key'")
    
    # Run main automation tests
    results = test_devops_automation_agent()
    
    # Run code generation tests
    test_code_generation()
    
    print("\n🎉 All tests completed!")
    print("The DevOps Automation Agent is ready for complex automation tasks!")

if __name__ == "__main__":
    main()
