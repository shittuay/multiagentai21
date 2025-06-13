# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create src directory
RUN mkdir -p /app/src

# Copy credentials file first and rename it
COPY multiagentai21-9a8fc-firebase-adminsdk-fbsvc-72f0130c73.json /app/src/multiagentai21-key.json

# Copy application code
COPY . .

# Set proper permissions
RUN chmod 644 /app/src/multiagentai21-key.json

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=true
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"] 