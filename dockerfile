FROM node:18-slim

# Install Python, pip, ffmpeg, and build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install yt-dlp globally
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install yt-dlp --upgrade

# Verify installation
RUN python3 -m yt_dlp --version

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Expose port
EXPOSE 3000

# Start the server
CMD ["node", "server.js"]