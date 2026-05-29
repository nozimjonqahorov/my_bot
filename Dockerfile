FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file and install python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . /app

# Expose port (Render will set $PORT, default 8443)
EXPOSE 8443

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1

# Command to run the bot (will use webhook if WEBHOOK_URL is set)
CMD ["python", "main.py"]
