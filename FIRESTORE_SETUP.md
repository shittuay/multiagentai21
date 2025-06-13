# Firestore Setup Guide for MultiAgentAI21

This guide will help you configure your Google Cloud Firestore database to work with the MultiAgentAI21 application.

## Prerequisites

1. ✅ Google Cloud Project created
2. ✅ Firestore database created
3. ✅ Service account key file downloaded
4. ✅ Environment variables configured

## Step 1: Configure Firestore Database

### 1.1 Enable Firestore API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **Library**
4. Search for "Cloud Firestore API"
5. Click **Enable**

### 1.2 Create Firestore Database
1. Go to **Firestore Database** in the left sidebar
2. Click **Create Database**
3. Choose **Start in production mode**
4. Select a location (choose the closest to your users)
5. Click **Done**

### 1.3 Set Up Security Rules
1. In Firestore, go to **Rules** tab
2. Replace the default rules with:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write access to all documents for authenticated users
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
    
    // Alternative: Allow all access (for development only)
    // match /{document=**} {
    //   allow read, write: if true;
    // }
  }
}
```

3. Click **Publish**

## Step 2: Create Service Account

### 2.1 Create Service Account
1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Enter details:
   - **Name**: `multiagentai21-service`
   - **Description**: `Service account for MultiAgentAI21 application`
4. Click **Create and Continue**

### 2.2 Assign Permissions
1. Add these roles:
   - **Cloud Datastore User**
   - **Cloud Firestore User**
   - **Firebase Admin**
2. Click **Continue**
3. Click **Done**

### 2.3 Generate Key File
1. Click on the service account you just created
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Click **Create**
6. Download the JSON file and save it as `multiagentai21-key.json` in your project root

## Step 3: Configure Environment Variables

### 3.1 Set Environment Variables
Add these to your `.env` file:

```bash
# Google Cloud Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_PROJECT_ID=your_project_id_here
GOOGLE_APPLICATION_CREDENTIALS=multiagentai21-key.json

# Optional: Firestore specific settings
FIRESTORE_DATABASE_ID=(default)
FIRESTORE_COLLECTION_PREFIX=multiagentai21
```

### 3.2 Verify Project ID
1. Go to your Google Cloud Console
2. Copy your **Project ID** from the top navigation
3. Replace `your_project_id_here` with your actual project ID

## Step 4: Test Firestore Connection

### 4.1 Run the Test Script
```bash
python test_agents.py
```

### 4.2 Check Firestore Console
1. Go to **Firestore Database** → **Data**
2. You should see collections being created:
   - `chats` - Chat history
   - `sessions` - Active sessions
   - `agents` - Agent statistics

## Step 5: Troubleshooting

### 5.1 Common Issues

#### **403 Permission Denied**
- **Cause**: Service account doesn't have proper permissions
- **Solution**: 
  1. Check service account roles
  2. Verify the key file is correct
  3. Ensure environment variables are set

#### **Authentication Failed**
- **Cause**: Invalid service account key
- **Solution**:
  1. Regenerate the service account key
  2. Check the JSON file format
  3. Verify the file path in environment variables

#### **Database Not Found**
- **Cause**: Wrong project ID or database not created
- **Solution**:
  1. Verify project ID in environment variables
  2. Ensure Firestore database is created
  3. Check database location settings

### 5.2 Debug Commands

#### **Test Service Account**
```bash
# Test authentication
gcloud auth activate-service-account --key-file=multiagentai21-key.json

# List Firestore collections
gcloud firestore collections list
```

#### **Check Environment**
```bash
# Verify environment variables
echo $GOOGLE_PROJECT_ID
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test Python connection
python -c "
from google.cloud import firestore
client = firestore.Client()
print('Firestore connection successful')
"
```

## Step 6: Production Considerations

### 6.1 Security Rules
For production, use more restrictive rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Only allow access to specific collections
    match /chats/{document} {
      allow read, write: if request.auth != null;
    }
    match /sessions/{document} {
      allow read, write: if request.auth != null;
    }
    match /agents/{document} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### 6.2 Monitoring
1. Set up **Cloud Monitoring** for Firestore
2. Create alerts for:
   - High read/write operations
   - Authentication failures
   - Database errors

### 6.3 Backup
1. Enable **Automated backups** in Firestore settings
2. Set up **Export/Import** schedules
3. Test restore procedures

## Step 7: Verify Setup

### 7.1 Check Collections
After running the application, you should see:

```
Firestore Database
├── chats/
│   ├── [auto-generated-id]
│   │   ├── session_id: "chat_1234567890"
│   │   ├── timestamp: [timestamp]
│   │   ├── request: "User's question"
│   │   ├── response: {agent response data}
│   │   ├── agent_type: "content_creation_and_generation"
│   │   └── metadata: {additional data}
├── sessions/
│   └── [session-id]
│       ├── last_interaction: [timestamp]
│       ├── agent_type: "content_creation_and_generation"
│       └── status: "active"
└── agents/
    └── [agent-type]
        ├── total_requests: 10
        ├── successful_requests: 9
        ├── failed_requests: 1
        └── average_response_time: 15.5
```

### 7.2 Success Indicators
- ✅ No 403 permission errors in logs
- ✅ Chat history being saved
- ✅ Collections appearing in Firestore console
- ✅ Agent statistics being tracked

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all environment variables are set
3. Test with the debug commands
4. Check Google Cloud Console for errors
5. Review Firestore security rules

---

**Note**: This setup provides a production-ready Firestore configuration with proper security, monitoring, and backup considerations. 