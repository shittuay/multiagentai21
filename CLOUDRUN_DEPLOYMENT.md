# Google Cloud Run Deployment Guide

This guide will help you deploy the MultiAgentAI21 application to Google Cloud Run.

## Prerequisites

1. ✅ Google Cloud Project (`multiagentai21`)
2. ✅ Google Cloud CLI installed and configured
3. ✅ Required APIs enabled
4. ✅ Service account with proper permissions

## Step 1: Enable Required APIs

```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

## Step 2: Set Up Environment Variables

### Option A: Using Cloud Run Environment Variables
```bash
# Set environment variables for Cloud Run
gcloud run services update multiagentai21 \
  --set-env-vars="GOOGLE_API_KEY=your_gemini_api_key" \
  --set-env-vars="GOOGLE_PROJECT_ID=multiagentai21" \
  --set-env-vars="FIRESTORE_DATABASE_ID=(default)" \
  --set-env-vars="FIRESTORE_COLLECTION_PREFIX=multiagentai21"
```

### Option B: Using Secret Manager (Recommended for Production)
```bash
# Create secrets
echo "your_gemini_api_key" | gcloud secrets create gemini-api-key --data-file=-
echo "your_firestore_key_json" | gcloud secrets create firestore-key --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:multiagentai21@multiagentai21.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 3: Deploy to Cloud Run

### Method 1: Using Cloud Build (Automated)
```bash
# Submit build to Cloud Build
gcloud builds submit --config cloudbuild.yaml .
```

### Method 2: Manual Deployment
```bash
# Build the Docker image
docker build -t gcr.io/multiagentai21/multiagentai21:latest .

# Push to Container Registry
docker push gcr.io/multiagentai21/multiagentai21:latest

# Deploy to Cloud Run
gcloud run deploy multiagentai21 \
  --image gcr.io/multiagentai21/multiagentai21:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --max-instances 10
```

## Step 4: Configure Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service multiagentai21 \
  --domain your-domain.com \
  --region us-central1
```

## Step 5: Set Up CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Google Cloud CLI
      uses: google-github-actions/setup-gcloud@v0
      with:
        project_id: multiagentai21
        service_account_key: ${{ secrets.GCP_SA_KEY }}
    
    - name: Deploy to Cloud Run
      run: |
        gcloud builds submit --config cloudbuild.yaml .
```

## Step 6: Monitor and Scale

### View Logs
```bash
# View Cloud Run logs
gcloud logs read --service=multiagentai21 --limit=50

# View Cloud Build logs
gcloud builds log [BUILD_ID]
```

### Monitor Performance
```bash
# Check service status
gcloud run services describe multiagentai21 --region=us-central1

# View metrics
gcloud monitoring dashboards list
```

## Step 7: Security Best Practices

### 1. Use Secret Manager for Sensitive Data
```bash
# Store API keys in Secret Manager
echo "$GOOGLE_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
```

### 2. Configure IAM Permissions
```bash
# Grant minimal required permissions
gcloud projects add-iam-policy-binding multiagentai21 \
  --member="serviceAccount:multiagentai21@multiagentai21.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 3. Enable Security Scanning
```bash
# Enable Container Analysis
gcloud services enable containeranalysis.googleapis.com
```

## Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
gcloud builds log [BUILD_ID]

# Test locally
docker build -t multiagentai21 .
docker run -p 8080:8080 multiagentai21
```

#### 2. Runtime Errors
```bash
# Check Cloud Run logs
gcloud logs read --service=multiagentai21 --limit=100

# Check environment variables
gcloud run services describe multiagentai21 --region=us-central1
```

#### 3. Permission Issues
```bash
# Verify service account permissions
gcloud projects get-iam-policy multiagentai21
```

### Performance Optimization

#### 1. Cold Start Optimization
- Use container image optimization
- Implement health checks
- Set appropriate memory/CPU limits

#### 2. Cost Optimization
- Set max instances limit
- Use appropriate concurrency settings
- Monitor usage patterns

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Gemini API key | Yes |
| `GOOGLE_PROJECT_ID` | Google Cloud project ID | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account key path | Yes |
| `FIRESTORE_DATABASE_ID` | Firestore database ID | No |
| `FIRESTORE_COLLECTION_PREFIX` | Collection prefix | No |

## Next Steps

1. Set up monitoring and alerting
2. Configure auto-scaling policies
3. Set up backup and disaster recovery
4. Implement CI/CD pipeline
5. Add custom domain and SSL certificate

## Support

For issues with Cloud Run deployment:
- Check [Cloud Run documentation](https://cloud.google.com/run/docs)
- Review [Cloud Build logs](https://console.cloud.google.com/cloud-build/builds)
- Monitor [Cloud Run metrics](https://console.cloud.google.com/run) 