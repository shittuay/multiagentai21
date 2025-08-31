# MultiAgentAI21 Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd app
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the `app` directory with your Google API key:

```env
GOOGLE_API_KEY=your_google_api_key_here
LOG_LEVEL=INFO
```

**Get your Google API key from:** https://makersuite.google.com/app/apikey

### 3. Run the Application
```bash
streamlit run app.py
```

### 4. Login
Use the demo account or create your own:
- **Demo Account**: `test@example.com` / `test123`
- **Or create a new account** through the signup form

## 🔧 Troubleshooting

### Issue: "GOOGLE_API_KEY not found"
**Solution**: Make sure your `.env` file exists and contains a valid API key

### Issue: "Model initialization failed"
**Solution**: Check that your API key is valid and has access to Gemini models

### Issue: "Agent system not initialized"
**Solution**: Check that all required files exist in the `src/` directory

### Issue: "Authentication failed"
**Solution**: Use the demo account or create a new account

## 🧪 Testing

Run the test script to verify everything is working:
```bash
python test_devops_agent.py
```

## 📋 Test Requests

Try these requests with the DevOps Automation Expert:

1. **Infrastructure**: "Create a Terraform configuration for AWS infrastructure"
2. **CI/CD**: "Set up a CI/CD pipeline with GitHub Actions"
3. **Containers**: "Create a Dockerfile for a Python application"
4. **Monitoring**: "Set up monitoring with Prometheus and Grafana"
5. **Kubernetes**: "Automate Kubernetes deployment with Helm charts"

## 🆘 Need Help?

If you encounter issues:
1. Check the console logs for error messages
2. Verify your API key is valid
3. Make sure all dependencies are installed
4. Try the test script to isolate issues
