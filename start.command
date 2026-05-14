#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "🎬 YouTube Downloader"
echo "========================================"

# Check if yt-dlp is installed
if ! command -v yt-dlp &> /dev/null; then
    echo "📦 Installing yt-dlp..."
    pip3 install yt-dlp --user
fi

# Check if Flask is installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "📦 Installing Flask..."
    pip3 install flask --user
fi

# Kill any existing server on port 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start the server
echo "🚀 Starting server..."
python3 app.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Open browser
echo "🌐 Opening browser..."
open http://localhost:8080

echo ""
echo "✅ YouTube Downloader is running!"
echo "💡 Close this window to stop the server"
echo ""

# Wait for user to close
wait $SERVER_PID
