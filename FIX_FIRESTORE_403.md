# Quick Fix for Firestore 403 Permission Errors

## The Problem
You're getting `403 Missing or insufficient permissions` when saving chat history.

## Quick Solution

### 1. Add Firestore Owner Permission
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project: `multiagentai21`
3. Go to **IAM & Admin** → **Service Accounts**
4. Find your service account and click on it
5. Click **PERMISSIONS** tab → **GRANT ACCESS**
6. Add role: **Cloud Firestore Owner**
7. Click **SAVE**

### 2. Update Firestore Rules (Temporary)
1. Go to **Firestore Database** → **Rules**
2. Replace rules with:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```
3. Click **PUBLISH**

### 3. Test
```bash
python test_firestore.py
```

## If Still Not Working
1. Create new service account with **Cloud Firestore Owner** role
2. Generate new key file
3. Update `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

## Security Note
The permissive rules above are for testing only. Use proper authentication rules for production. 