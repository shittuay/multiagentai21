# Render.com Deployment Guide

## Why Render Instead of Streamlit Cloud?

Render.com offers:
- ✅ Free tier (750 hours/month)
- ✅ Custom domains on free tier
- ✅ Better performance
- ✅ More control over environment
- ✅ Automatic deploys from GitHub
- ✅ Easy SSL/HTTPS setup

## Quick Deployment Steps

### 1. Create Render Account
1. Go to https://render.com
2. Sign up with GitHub (recommended) or email
3. Authorize Render to access your repositories

### 2. Deploy Your App

**Option A: Using render.yaml (Recommended)**

1. Push your code to GitHub (render.yaml is already included)
2. In Render dashboard, click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`
5. Add environment variable:
   - Key: `OPENROUTER_API_KEY`
   - Value: `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`
6. Click "Apply"

**Option B: Manual Setup**

1. In Render dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: multiagentai21
   - **Region**: Oregon (or closest to you)
   - **Branch**: main
   - **Root Directory**: (leave blank)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
   - **Plan**: Free
4. Add Environment Variables:
   - `OPENROUTER_API_KEY` = `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`
   - `DISABLE_AUTH` = `true`
   - `DISABLE_RATE_LIMIT` = `true`
5. Click "Create Web Service"

### 3. Wait for Deployment
- First deployment takes 5-10 minutes
- Watch the build logs for any errors
- Once deployed, you'll get a URL like: `https://multiagentai21.onrender.com`

## Environment Variables

Add these in Render dashboard under "Environment":

```
OPENROUTER_API_KEY=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
DISABLE_AUTH=true
DISABLE_RATE_LIMIT=true
```

Optional (if using Google Cloud features):
```
GOOGLE_CLOUD_PROJECT=multiagentai21
```

## Custom Domain Setup

### Using Your Own Domain

1. In Render dashboard, go to your service
2. Click "Settings" → "Custom Domain"
3. Add your domain (e.g., `app.yourdomain.com`)
4. Render will show you DNS records to add:
   - **Type**: CNAME
   - **Name**: app (or @ for root domain)
   - **Value**: [your-app].onrender.com
5. Add these records in your domain registrar (GoDaddy, Namecheap, etc.)
6. Wait for DNS propagation (5 minutes to 48 hours)
7. Render will automatically provision SSL certificate

## Free Tier Limitations

- **750 hours/month** (about 31 days if running 24/7)
- **Spins down after 15 minutes** of inactivity (first request takes ~30 seconds to wake up)
- **512 MB RAM**
- **0.1 CPU**

To prevent spin-down, you can:
1. Upgrade to paid plan ($7/month for always-on)
2. Use a monitoring service to ping your app every 10 minutes

## Troubleshooting

### Build Fails
- Check `requirements.txt` is in root directory
- Verify all dependencies are listed
- Check build logs for specific errors

### App Won't Start
- Verify start command is correct
- Check that `PORT` environment variable is used
- Review application logs

### "Application Error" or Timeout
- App might be too large for free tier
- Check logs for memory issues
- Consider upgrading plan

### Dependencies Not Installing
- Make sure `requirements.txt` includes all packages
- Check for version conflicts
- Try pinning specific versions

## Monitoring Your App

1. **Logs**: View real-time logs in Render dashboard
2. **Metrics**: See CPU, memory, and bandwidth usage
3. **Events**: Track deployments and restarts

## Auto-Deploy from GitHub

Render automatically deploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Render will:
1. Detect the push
2. Pull latest code
3. Run build command
4. Deploy new version
5. Keep old version running until new one is ready (zero-downtime)

## Comparison: Render vs Streamlit Cloud

| Feature | Render | Streamlit Cloud |
|---------|--------|-----------------|
| Free Tier | 750 hrs/month | Unlimited |
| Custom Domain | ✅ Free | ❌ Paid only |
| Always On | ❌ Spins down | ✅ Always on |
| RAM | 512 MB | 1 GB |
| Build Time | ~5-10 min | ~2-5 min |
| Control | More | Less |
| Setup | Medium | Easy |

## Next Steps

1. ✅ Created `render.yaml` configuration
2. ⬜ Push code to GitHub
3. ⬜ Create Render account
4. ⬜ Deploy using Blueprint or manual setup
5. ⬜ Add environment variables
6. ⬜ Test your deployed app
7. ⬜ (Optional) Set up custom domain

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Streamlit Docs: https://docs.streamlit.io

## Cost Optimization

Free tier tips:
- App spins down after 15 min inactivity (saves free hours)
- Monitor usage in Render dashboard
- Consider paid plan ($7/month) if you need always-on

Paid plans start at $7/month for:
- Always-on (no spin down)
- More RAM/CPU
- Better performance
