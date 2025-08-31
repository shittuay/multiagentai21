#!/bin/bash

# MultiAgentAI21 Docker Deployment - Ubuntu/GCloud VM Version
echo "=== MultiAgentAI21 Docker Deployment ==="

# Clean up existing containers and images
echo "🧹 Cleaning up existing containers..."
docker stop multiagentai21-instance || true 
docker rm multiagentai21-instance || true  
docker rmi multiagentai21-app || true      
docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null || true

# Build the application
echo "🏗️ Building application..."
docker build --no-cache -t multiagentai21-app .

if [ $? -ne 0 ]; then
    echo "❌ Build failed! Check Dockerfile and try again."
    exit 1
fi

# Run the container with CORRECTED configuration
echo "🚀 Running container with corrected configuration..."
docker run -d \
  -p 8080:8080 \
  --name multiagentai21-instance \
  -e PORT=8080 \
  -e GOOGLE_PROJECT_ID="multiagentai21" \
  -e GEMINI_API_KEY="AIzaSyAJuRnv13hyJyPtJRwlOIj7jFC1vvEewA4" \
  -e GOOGLE_API_KEY="AIzaSyAJuRnv13hyJyPtJRwlOIj7jFC1vvEewA4" \
  -e GOOGLE_CLOUD_PROJECT="multiagentai21" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/multiagentai21-7e1267f20729.json" \
  -v "$(pwd)/multiagentai21-7e1267f20729.json":/app/multiagentai21-7e1267f20729.json \
  -v "$(pwd)/.env":/app/.env \
  multiagentai21-app

if [ $? -ne 0 ]; then
    echo "❌ Container failed to start!"
    echo "📝 Check logs with: docker logs multiagentai21-instance"
    exit 1
fi

echo ""
echo "✅ MultiAgentAI21 deployed successfully!"
echo "🌐 Access your app at: https://multiagentai21.com"
echo "📝 Check logs: docker logs multiagentai21-instance"
echo "🛑 Stop with: docker stop multiagentai21-instance"
echo ""
echo "=== KEY CHANGES MADE ==="
echo "✅ Fixed project ID: multiagentai21 (was multiagentai21-9a8fc)"
echo "✅ Using correct key file: multiagentai21-7e1267f20729.json" 
echo "✅ Mounting working .env file"
echo "✅ Corrected environment variables"
echo ""