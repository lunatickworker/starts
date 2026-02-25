FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    libxrandr2 \
    libnss3 \
    libnspr4 \
    fonts-liberation \
    xdg-utils \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir streamlit==1.28.1 playwright==1.45.0

# Install Playwright browsers
RUN playwright install chromium

# Copy app
COPY . .

# Create .streamlit config directory
RUN mkdir -p ~/.streamlit

# Set Streamlit config
RUN echo '[server]
headless = true
port = 8501
enableXsrfProtection = false
[browser]
gatherUsageStats = false
' > ~/.streamlit/config.toml

EXPOSE 8501

CMD ["streamlit", "run", "web_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--logger.level=debug"]
