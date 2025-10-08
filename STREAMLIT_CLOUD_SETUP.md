# Streamlit Cloud Deployment Guide

## Prerequisites
- Streamlit Cloud account (sign up at https://share.streamlit.io)
- Your GitHub repository connected to Streamlit Cloud
- OpenRouter API key

## Configuration Steps

### 1. Configure Streamlit Cloud Secrets

In your Streamlit Cloud app settings, add the following secrets in TOML format:

```toml
# Required: OpenRouter API Key for AI features
OPENROUTER_API_KEY = "sk-or-v1-your-api-key-here"

# Required: Disable authentication (since Streamlit Cloud has ephemeral file system)
DISABLE_AUTH = true

# Optional: Google Cloud credentials (if using Firestore/BigQuery)
GOOGLE_CLOUD_PROJECT = "your-project-id"
```

### 2. Update Your OpenRouter API Key

Replace `"sk-or-v1-your-api-key-here"` with your actual OpenRouter API key from the `.env` file:
```
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
```

### 3. Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your GitHub repository
4. Set the main file path to: `app/app.py`
5. Click "Deploy"

## Why Authentication is Disabled

Streamlit Cloud uses ephemeral file systems, which means:
- Files created during runtime are deleted when the app redeploys
- The `app/data/users.json` file used for storing user accounts gets deleted
- Users would need to recreate accounts after every deployment

**Solution**: The app now supports a `DISABLE_AUTH` flag that bypasses authentication on Streamlit Cloud, allowing anyone to access the app without logging in.

## Local Development vs Cloud Deployment

### Local Development (with authentication)
- Uses file-based user storage in `app/data/users.json`
- Requires user login with email/password
- User accounts persist across app restarts

### Streamlit Cloud (without authentication)
- Set `DISABLE_AUTH = true` in secrets
- No login required - direct access to the app
- Suitable for demo/public deployments

## Future: Enabling Authentication on Streamlit Cloud

To enable authentication on Streamlit Cloud, you need persistent storage:

### Option 1: Firestore Database (Recommended)
1. Set up Google Cloud Firestore
2. Add service account JSON to Streamlit secrets:
```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "service-account@project.iam.gserviceaccount.com"
# ... other fields
```
3. Remove or set `DISABLE_AUTH = false`

### Option 2: Alternative Database
- Use PostgreSQL, MongoDB, or any cloud database
- Update `auth_manager.py` to use the database instead of JSON files

## Troubleshooting

### Issue: "OPENROUTER_API_KEY is not set"
**Solution**: Make sure you've added `OPENROUTER_API_KEY` to Streamlit Cloud secrets (not just environment variables)

### Issue: App shows login page on Streamlit Cloud
**Solution**: Ensure `DISABLE_AUTH = true` is set in secrets

### Issue: AI features not working
**Solution**: Verify your OpenRouter API key is valid and has credits

## Testing Your Deployment

After deployment:
1. App should load directly without showing login page
2. Select an agent from the sidebar
3. Enter a prompt and test the AI response
4. Check that all agent types work correctly

## Security Note

When authentication is disabled, the app is publicly accessible. Do not:
- Store sensitive data in the app
- Use production API keys with high credit limits
- Deploy sensitive business logic without proper access controls

For production deployments with sensitive data, implement proper authentication using Firestore or another persistent database.
