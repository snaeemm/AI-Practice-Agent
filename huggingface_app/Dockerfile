# Hugging Face Spaces Dockerfile for Streamlit
# This uses Docker SDK to run the Granite RFP Bid Assistant

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose Streamlit port (required for Hugging Face Spaces)
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit app
# Note: Hugging Face Spaces requires port 8501 for Streamlit
ENTRYPOINT ["streamlit", "run", "Agent.py", "--server.port=8501", "--server.address=0.0.0.0"]
