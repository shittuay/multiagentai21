#!/bin/bash

# Clean up existing containers and images
docker stop multiagentai21-instance || true 
docker rm multiagentai21-instance || true  
docker rmi multiagentai21-app || true      
docker rmi $(docker images -f "dangling=true" -q) || true

# Build the application
docker build --no-cache -t multiagentai21-app .

# Run the container with corrected environment variables
docker run -d \
  -p 8080:8080 \
  --name multiagentai21-instance \
  -e PORT=8080 \
  -e GOOGLE_PROJECT_ID="multiagentai21" \
  -e GEMINI_API_KEY="AIzaSyAJuRnv13hyJyPtJRwlOIj7jFC1vvEewA4" \
  -e GOOGLE_API_KEY="AIzaSyAJuRnv13hyJyPtJRwlOIj7jFC1vvEewA4" \
  -e GOOGLE_CLOUD_PROJECT="multiagentai21" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/multiagentai21-key.json" \
  -v $(pwd)/multiagentai21-key.json:/app/multiagentai21-key.json \
  -v $(pwd)/.env:/app/.env \
  multiagentai21-app

echo "✅ MultiAgentAI21 deployed successfully!"
echo "🌐 Access your app at: http://localhost:8080"
echo "📝 Check logs with: docker logs multiagentai21-instance"