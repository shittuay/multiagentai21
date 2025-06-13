# Fix Firestore 403 Permission Errors

## Current Issue
You're getting `403 Missing or insufficient permissions` errors when trying to save chat history to Firestore.

## Step-by-Step Solution

### Step 1: Check Current Service Account Permissions

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (`multiagentai21`)
3. Navigate to **IAM & Admin** → **Service Accounts**
4. Find your service account (likely named something like `multiagentai21-service` or similar)
5. Click on it to view details

### Step 2: Add Required Permissions

1. In the service account details, click **PERMISSIONS** tab
2. Click **GRANT ACCESS**
3. Add these **roles**:
   - **Cloud Datastore User**
   - **Cloud Firestore User** 
   - **Firebase Admin**
   - **Firestore Admin** (if available)
4. Click **SAVE**

### Step 3: Alternative - Create New Service Account with Full Permissions

If the above doesn't work, create a new service account:

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **CREATE SERVICE ACCOUNT**
3. Name: `multiagentai21-firestore-admin`
4. Description: `Service account with full Firestore permissions`
5. Click **CREATE AND CONTINUE**

**Add these roles:**
- **Cloud Datastore Owner**
- **Cloud Firestore Owner**
- **Firebase Admin**
- **Project IAM Admin** (temporary, for testing)

6. Click **CONTINUE** → **DONE**

### Step 4: Generate New Key File

1. Click on your new service account
2. Go to **KEYS** tab
3. Click **ADD KEY** → **CREATE NEW KEY**
4. Choose **JSON** format
5. Click **CREATE**
6. Download the file and save it as `multiagentai21-key.json` in your project root

### Step 5: Update Environment Variables

Update your `.env` file:

```bash
# Google Cloud Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_PROJECT_ID=multiagentai21
GOOGLE_APPLICATION_CREDENTIALS=multiagentai21-key.json

# Firestore specific settings
FIRESTORE_DATABASE_ID=(default)
FIRESTORE_COLLECTION_PREFIX=multiagentai21
```

### Step 6: Update Firestore Security Rules

1. Go to **Firestore Database** → **Rules**
2. Replace the rules with this **permissive** version (for testing):

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow all access for testing (remove this in production)
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

3. Click **PUBLISH**

### Step 7: Test the Fix

Run this command to test Firestore connectivity:

```bash
python test_firestore.py
```

### Step 8: Verify in Firestore Console

1. Go to **Firestore Database** → **Data**
2. You should see collections being created when you run the app:
   - `chats`
   - `sessions` 
   - `agents`

## Troubleshooting

### If Still Getting 403 Errors:

1. **Check Project ID**: Ensure `GOOGLE_PROJECT_ID=multiagentai21` is correct
2. **Verify Key File**: Make sure the JSON key file is in the project root
3. **Check File Permissions**: Ensure the key file is readable
4. **Restart Application**: Restart your Python application after making changes

### Test Service Account Authentication:

```bash
# Test if the service account can authenticate
gcloud auth activate-service-account --key-file=multiagentai21-key.json

# List Firestore collections
gcloud firestore collections list --project=multiagentai21
```

### Alternative: Use Firebase Admin SDK

If Firestore permissions continue to be an issue, you can temporarily disable Firestore saving by modifying the code to skip database operations.

## Security Note

The permissive security rules above are for **testing only**. For production, use more restrictive rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
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

## Quick Fix Summary

1. Add **Cloud Firestore Owner** role to your service account
2. Update Firestore rules to allow all access temporarily
3. Ensure environment variables are correct
4. Test with `python test_firestore.py` 