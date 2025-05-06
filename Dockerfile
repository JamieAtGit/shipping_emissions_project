# Use official Python slim image
FROM python:3.10-slim

# Prevents Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies (for Chrome + scraping)
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    libnss3 libxss1 libasound2 \
    chromium chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all project files
COPY . .

# Set the correct path to Chrome
ENV PATH="/usr/lib/chromium/:$PATH"

# Expose Flask port
EXPOSE 5000

# Add PYTHONPATH so Python sees 'backend' as a top-level module
ENV PYTHONPATH=/app

# Run the Flask app
CMD ["python", "backend/app.py"]
