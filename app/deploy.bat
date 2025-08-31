@echo off
echo === MultiAgentAI21 Docker Deployment ===

REM Clean up existing containers and images
echo Stopping existing container...
docker stop multiagentai21-instance >nul 2>&1

echo Removing existing container...
docker rm multiagentai21-instance >nul 2>&1

echo Removing existing image...
docker rmi multiagentai21-app >nul 2>&1

echo Removing dangling images...
for /f "tokens=*" %%i in ('docker images -f "dangling=true" -q') do docker rmi %%i >nul 2>&1

echo Building application...
docker build --no-cache -t multiagentai21-app .

if %ERRORLEVEL% neq 0 (
    echo ❌ Build failed! Check Dockerfile and try again.
    pause
    exit /b 1
)

echo Running container...
docker run -d ^
  -p 8080:8080 ^
  --name multiagentai21-instance ^
  -e PORT=8080 ^
  -e GOOGLE_PROJECT_ID=multiagentai21 ^
  -e GEMINI_API_KEY=AIzaSyAJuRnv13hyJyPtJRwlOIj7jFC1vvEewA4 ^
  -e GOOGLE_API_KEY=AIzaSyAJuRnv13hyJyPtJRwlOIj7jFC1vvEewA4 ^
  -e GOOGLE_CLOUD_PROJECT=multiagentai21 ^
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/multiagentai21-key.json ^
  -v "%cd%\.env":/app/.env ^
  -v "%cd%\multiagentai21-key.json":/app/multiagentai21-key.json ^
  multiagentai21-app

if %ERRORLEVEL% neq 0 (
    echo ❌ Container failed to start! Check logs with: docker logs multiagentai21-instance
    pause
    exit /b 1
)

echo.
echo ✅ MultiAgentAI21 deployed successfully!
echo 🌐 Access your app at: http://localhost:8080
echo 📝 Check logs with: docker logs multiagentai21-instance
echo 🛑 Stop with: docker stop multiagentai21-instance
echo.
pause