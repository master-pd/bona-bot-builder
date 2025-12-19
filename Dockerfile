# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs storage/uploads storage/proofs storage/backups storage/temp

# Set permissions
RUN chmod +x scripts/*.py

# Run as non-root user
RUN useradd -m -u 1000 bona && chown -R bona:bona /app
USER bona

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]