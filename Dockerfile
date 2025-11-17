# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-dejavu \
    fonts-liberation \
    git \
    curl \
    build-essential \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i 's/policy domain="path" rights="none" pattern="@\*"/policy domain="path" rights="read" pattern="@*"/' /etc/ImageMagick-7/policy.xml

# Download and install Luckiest Guy font
RUN mkdir -p /usr/share/fonts/truetype/luckiest-guy \
    && wget -O /usr/share/fonts/truetype/luckiest-guy/LuckiestGuy-Regular.ttf \
       "https://github.com/google/fonts/raw/main/apache/luckiestguy/LuckiestGuy-Regular.ttf" \
    && fc-cache -f -v

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt optimized_requirements.txt ./

# Install Python dependencies (including optimization dependencies)
RUN pip install --no-cache-dir -r optimized_requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp uploads jobs static

# Set environment variables for optimized performance
ENV FLASK_APP=app_optimized.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the optimized application
CMD ["python", "app_optimized.py"]