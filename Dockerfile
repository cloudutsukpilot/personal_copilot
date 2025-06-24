# Use lightweight Python base
FROM python:3.10-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Switch to the root user
USER root

# Create the directory and set the appropriate permissions
RUN mkdir -p /usr/local/share/ca-certificates && \
    chmod 755 /usr/local/share/ca-certificates

COPY ./zscalar_root_ca.pem /usr/local/share/ca-certificates/zscalar_root_ca.pem

RUN update-ca-certificates

ENV REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/zscalar_root_ca.pem

# Set environment variables for Ollama
ENV OLLAMA_HOST=192.168.1.9

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
