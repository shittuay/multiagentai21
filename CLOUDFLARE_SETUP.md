# Cloudflare Integration Guide for MultiAgentAI21

This guide will help you configure your Cloudflare domain to work with your Streamlit deployment.

## Prerequisites

1. ✅ Streamlit application deployed and running
2. ✅ Domain name configured in Cloudflare
3. ✅ Cloudflare account with DNS access

## Step 1: Deploy Your Streamlit Application

### Option A: Local Deployment (for testing)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the deployment script
python deploy.py
```

### Option B: Cloud Deployment (recommended)
Deploy to one of these platforms:

#### **Streamlit Cloud (Recommended)**
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set environment variables:
   - `GOOGLE_API_KEY`
   - `GOOGLE_PROJECT_ID`
   - `GOOGLE_APPLICATION_CREDENTIALS`

#### **Railway**
1. Connect your GitHub repository to Railway
2. Set environment variables
3. Deploy

#### **Render**
1. Create a new Web Service
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. Set environment variables

## Step 2: Configure Cloudflare DNS

### 1. Add DNS Records
In your Cloudflare dashboard:

1. Go to **DNS** → **Records**
2. Add a new record:
   - **Type**: `CNAME`
   - **Name**: `@` (or your subdomain like `app`)
   - **Target**: Your deployment URL (e.g., `your-app.onrender.com`)
   - **Proxy status**: 🟠 **Proxied** (important!)

### 2. SSL/TLS Configuration
1. Go to **SSL/TLS** → **Overview**
2. Set SSL/TLS encryption mode to: **Full (strict)**
3. Enable **Always Use HTTPS**

## Step 3: Configure Cloudflare Rules

### 1. Page Rules (Optional)
Create page rules for better performance:

1. Go to **Rules** → **Page Rules**
2. Create a new rule:
   - **URL**: `yourdomain.com/*`
   - **Settings**:
     - Cache Level: Cache Everything
     - Browser Cache TTL: 4 hours
     - Security Level: Medium

### 2. Security Settings
1. Go to **Security** → **Settings**
2. Configure:
   - Security Level: Medium
   - Challenge Passage: 30 minutes
   - Browser Integrity Check: On

## Step 4: Environment Variables Setup

### For Streamlit Cloud:
1. Go to your app settings
2. Add these secrets:
```toml
GEMINI_API_KEY = "your_gemini_api_key"
GOOGLE_APPLICATION_CREDENTIALS = "multiagentai21-key.json"
GOOGLE_CLOUD_PROJECT = "multiagentai21"
```

### For Other Platforms:
Set these environment variables:
```bash
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_PROJECT_ID=multiagentai21
GOOGLE_APPLICATION_CREDENTIALS=multiagentai21-key.json
```

## Step 5: Test Your Setup

1. **Check DNS Propagation**:
   ```bash
   nslookup yourdomain.com
   ```

2. **Test HTTPS**:
   - Visit `https://yourdomain.com`
   - Should redirect to HTTPS automatically

3. **Test Application**:
   - Verify all features work
   - Check console for errors

## Troubleshooting

### Common Issues:

#### 1. **502 Bad Gateway**
- Check if your Streamlit app is running
- Verify the deployment URL is correct
- Check environment variables

#### 2. **CORS Errors**
- Ensure `enableCORS = true` in Streamlit config
- Check Cloudflare proxy settings

#### 3. **SSL Certificate Issues**
- Set SSL/TLS to "Full (strict)"
- Wait for certificate propagation (up to 24 hours)

#### 4. **Application Not Loading**
- Check deployment logs
- Verify all dependencies are installed
- Test locally first

### Debug Commands:
```bash
# Test DNS resolution
dig yourdomain.com

# Test HTTPS
curl -I https://yourdomain.com

# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

## Performance Optimization

### 1. Enable Cloudflare Caching
- Set appropriate cache headers
- Use Cloudflare's CDN for static assets

### 2. Optimize Images
- Use WebP format
- Enable Cloudflare's image optimization

### 3. Enable Compression
- Enable Gzip compression in Cloudflare
- Optimize your application assets

## Security Recommendations

1. **Enable Cloudflare Security Features**:
   - DDoS protection
   - Bot management
   - Rate limiting

2. **Set Security Headers**:
   - Content Security Policy
   - X-Frame-Options
   - X-Content-Type-Options

3. **Monitor Traffic**:
   - Use Cloudflare Analytics
   - Set up alerts for unusual activity

## Final Configuration

Your final setup should look like this:

```
Domain: yourdomain.com
→ Cloudflare Proxy
→ Your Streamlit Deployment (e.g., app.onrender.com)
→ Streamlit Application (port 8501)
```

## Support

If you encounter issues:
1. Check Cloudflare status page
2. Review deployment logs
3. Test locally first
4. Contact Cloudflare support if needed

---

**Note**: This setup provides a production-ready configuration with security, performance, and reliability features enabled through Cloudflare. 