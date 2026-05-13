from flask import Flask, request, send_file, render_template_string
import subprocess
import os
import time

app = Flask(__name__)

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Downloader</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { color: #333; margin-bottom: 10px; }
        p { color: #666; margin-bottom: 20px; }
        input {
            width: 100%;
            padding: 14px;
            margin: 15px 0;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 14px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover { background: #5a67d8; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .status {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            display: none;
        }
        .status.show { display: block; }
        .loading { background: #e3f2fd; color: #1565c0; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #ffebee; color: #c62828; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Downloader</h1>
        <p>Paste any YouTube URL - Downloads in highest quality</p>
        <input type="text" id="url" placeholder="https://youtu.be/hyYnjco6dHA" value="https://youtu.be/hyYnjco6dHA">
        <button id="downloadBtn">⬇️ Download Video</button>
        <div id="status" class="status"></div>
    </div>

    <script>
        const urlInput = document.getElementById('url');
        const downloadBtn = document.getElementById('downloadBtn');
        const statusDiv = document.getElementById('status');
        
        function showStatus(message, type) {
            statusDiv.textContent = message;
            statusDiv.className = `status ${type} show`;
            setTimeout(() => {
                statusDiv.className = 'status';
                statusDiv.textContent = '';
            }, 5000);
        }
        
        downloadBtn.addEventListener('click', async () => {
            const url = urlInput.value.trim();
            if (!url) {
                showStatus('Please enter a YouTube URL', 'error');
                return;
            }
            
            downloadBtn.disabled = true;
            showStatus('Downloading video... This may take a moment', 'loading');
            
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                if (!response.ok) {
                    throw new Error('Download failed');
                }
                
                const blob = await response.blob();
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = 'video.mp4';
                a.click();
                URL.revokeObjectURL(a.href);
                
                showStatus('✅ Download complete!', 'success');
            } catch (error) {
                showStatus('❌ Download failed. Make sure the video is public.', 'error');
            } finally {
                downloadBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return 'No URL provided', 400
    
    # Create downloads folder
    os.makedirs('downloads', exist_ok=True)
    
    # Run yt-dlp
    cmd = f'cd downloads && yt-dlp -f "bestvideo+bestaudio" --merge-output-format mp4 "{url}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return 'Download failed', 500
    
    # Find the downloaded file
    files = os.listdir('downloads')
    video_files = [f for f in files if f.endswith(('.mp4', '.mkv'))]
    
    if not video_files:
        return 'No video file found', 500
    
    # Get the newest file
    video_files.sort(key=lambda x: os.path.getctime(os.path.join('downloads', x)), reverse=True)
    file_path = os.path.join('downloads', video_files[0])
    
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)