from flask import Flask, request, send_file, render_template_string, jsonify
import subprocess
import os
import re
import time
import json
import threading

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Store progress for each download session
progress_data = {}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Downloader</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            width: 100%;
            background: white;
            border-radius: 24px;
            padding: 35px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { font-size: 28px; margin-bottom: 8px; color: #333; text-align: center; }
        .sub { text-align: center; color: #666; margin-bottom: 25px; font-size: 13px; }
        input {
            width: 100%;
            padding: 14px;
            margin-bottom: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 14px;
            outline: none;
            box-sizing: border-box;
        }
        input:focus { border-color: #667eea; }
        .quality-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }
        select {
            width: 100%;
            padding: 14px;
            margin-bottom: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 14px;
            background: white;
            cursor: pointer;
        }
        select:focus { border-color: #667eea; }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
            margin-top: 5px;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .progress-container {
            margin-top: 20px;
            display: none;
        }
        .progress-container.show { display: block; }
        .progress-bar-wrapper {
            background: #e0e0e0;
            border-radius: 20px;
            height: 30px;
            overflow: hidden;
        }
        .progress-fill {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            height: 100%;
            border-radius: 20px;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        .progress-text { margin-top: 8px; font-size: 12px; color: #666; text-align: center; }
        .status {
            margin-top: 15px;
            padding: 10px;
            border-radius: 10px;
            display: none;
            text-align: center;
            font-size: 13px;
        }
        .status.show { display: block; }
        .loading { background: #e3f2fd; color: #1565c0; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #ffebee; color: #c62828; }
        .video-preview {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 16px;
            display: none;
            text-align: center;
        }
        .video-preview.show { display: block; }
        .video-preview img { max-width: 100%; border-radius: 12px; margin-bottom: 10px; }
        .video-preview h3 { font-size: 14px; margin: 8px 0; color: #333; }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            font-size: 12px;
        }
        .mobile-tip {
            margin-top: 20px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 12px;
            font-size: 11px;
            color: #666;
        }
        .mobile-tip summary { cursor: pointer; font-weight: bold; color: #667eea; margin-bottom: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Downloader</h1>
        <div class="sub">Choose quality for faster downloads</div>
        
        <input type="text" id="url" placeholder="Paste YouTube URL here" value="https://youtu.be/hyYnjco6dHA">
        
        <label class="quality-label">📹 Select Quality</label>
        <select id="quality">
            <option value="best">🎬 Best Quality (Largest file)</option>
            <option value="1080p">📺 1080p Full HD</option>
            <option value="720p">📱 720p HD</option>
            <option value="480p">📱 480p</option>
            <option value="360p">📱 360p (Fastest)</option>
            <option value="audio">🎵 Audio Only (MP3)</option>
        </select>
        
        <button id="downloadBtn">⬇️ Download Video</button>
        
        <div id="progressContainer" class="progress-container">
            <div class="progress-bar-wrapper">
                <div id="progressFill" class="progress-fill">0%</div>
            </div>
            <div id="progressText" class="progress-text">Starting download...</div>
        </div>
        
        <div id="status" class="status"></div>
        <div id="videoPreview" class="video-preview"></div>
        
        <details class="mobile-tip">
            <summary>📱 How to save on phone</summary>
            <p><strong>iPhone:</strong> Tap and hold video → "Save to Files"<br>
            <strong>Android:</strong> Video saves automatically to Downloads<br>
            <strong>💡 Tip:</strong> Choose 360p for faster downloads on mobile data!</p>
        </details>
    </div>

    <script>
        const urlInput = document.getElementById('url');
        const qualitySelect = document.getElementById('quality');
        const downloadBtn = document.getElementById('downloadBtn');
        const statusDiv = document.getElementById('status');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const videoPreview = document.getElementById('videoPreview');
        
        let progressInterval = null;
        
        function showStatus(message, type) {
            statusDiv.textContent = message;
            statusDiv.className = `status ${type} show`;
            setTimeout(() => {
                if (statusDiv.textContent === message) {
                    statusDiv.className = 'status';
                    statusDiv.textContent = '';
                }
            }, 5000);
        }
        
        function updateProgress(percentage, statusMsg) {
            const percent = Math.round(percentage);
            progressFill.style.width = percent + '%';
            progressFill.textContent = percent + '%';
            progressText.textContent = statusMsg;
        }
        
        function startProgressMonitoring(sessionId) {
            if (progressInterval) clearInterval(progressInterval);
            
            progressInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/progress/${sessionId}`);
                    const data = await response.json();
                    
                    if (data.percentage >= 100) {
                        updateProgress(100, 'Complete! Processing file...');
                        setTimeout(() => {
                            progressContainer.classList.remove('show');
                        }, 1500);
                        if (progressInterval) clearInterval(progressInterval);
                    } else if (data.percentage > 0) {
                        updateProgress(data.percentage, data.status || 'Downloading...');
                    }
                } catch (e) {
                    console.log('Progress check failed');
                }
            }, 1000);
        }
        
        async function fetchVideoInfo(url) {
            try {
                const response = await fetch('/video-info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                if (response.ok) {
                    const info = await response.json();
                    const videoId = url.split('v=')[1]?.split('&')[0] || url.split('youtu.be/')[1]?.split('?')[0];
                    videoPreview.innerHTML = `
                        <img src="https://img.youtube.com/vi/${videoId}/mqdefault.jpg" alt="Thumbnail">
                        <h3>${escapeHtml(info.title.substring(0, 60))}${info.title.length > 60 ? '...' : ''}</h3>
                        <div class="info-row"><span>⏱️ Duration:</span><span>${Math.floor(info.duration/60)}:${(info.duration%60).toString().padStart(2,'0')}</span></div>
                        <div class="info-row"><span>👤 Uploader:</span><span>${escapeHtml(info.uploader)}</span></div>
                    `;
                    videoPreview.classList.add('show');
                }
            } catch (e) {
                console.log('Could not fetch video info');
            }
        }
        
        downloadBtn.addEventListener('click', async () => {
            const url = urlInput.value.trim();
            const quality = qualitySelect.value;
            
            if (!url) {
                showStatus('Please enter a YouTube URL', 'error');
                return;
            }
            
            progressContainer.classList.remove('show');
            if (progressInterval) clearInterval(progressInterval);
            updateProgress(0, 'Starting...');
            
            downloadBtn.disabled = true;
            showStatus('⏳ Starting download...', 'loading');
            
            const sessionId = Date.now().toString();
            startProgressMonitoring(sessionId);
            progressContainer.classList.add('show');
            
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url, quality: quality, sessionId: sessionId })
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
                progressContainer.classList.remove('show');
            } finally {
                downloadBtn.disabled = false;
                if (progressInterval) setTimeout(() => clearInterval(progressInterval), 3000);
            }
        });
        
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Fetch info when URL changes
        let debounceTimer;
        urlInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const url = urlInput.value.trim();
                if (url && (url.includes('youtube.com') || url.includes('youtu.be'))) {
                    fetchVideoInfo(url);
                } else {
                    videoPreview.classList.remove('show');
                }
            }, 500);
        });
        
        // Load info for default URL
        setTimeout(() => {
            fetchVideoInfo(urlInput.value.trim());
        }, 500);
    </script>
</body>
</html>
'''

def parse_progress(line, session_id):
    percent_match = re.search(r'\[download\]\s+(\d+(?:\.\d+)?)%', line)
    if percent_match:
        percent = float(percent_match.group(1))
        if session_id not in progress_data:
            progress_data[session_id] = {}
        progress_data[session_id]['percentage'] = percent
        progress_data[session_id]['status'] = f'Downloading... {percent:.1f}%'

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video-info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    cmd = f'yt-dlp --dump-json "{url}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        return jsonify({'error': 'Failed to get info'}), 500
    
    try:
        info = json.loads(result.stdout)
        return jsonify({
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', 'Unknown')
        })
    except:
        return jsonify({'error': 'Parse error'}), 500

@app.route('/progress/<session_id>')
def get_progress(session_id):
    data = progress_data.get(session_id, {'percentage': 0, 'status': 'Waiting...'})
    return jsonify({
        'percentage': data.get('percentage', 0),
        'status': data.get('status', 'Downloading...')
    })

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    quality = data.get('quality', 'best')
    session_id = data.get('sessionId', str(int(time.time())))
    
    if not url:
        return 'No URL provided', 400
    
    os.makedirs('downloads', exist_ok=True)
    
    progress_data[session_id] = {'percentage': 0, 'status': 'Starting...'}
    
    quality_map = {
        'best': 'bestvideo+bestaudio/best',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        'audio': 'bestaudio/best'
    }
    
    format_spec = quality_map.get(quality, 'bestvideo+bestaudio/best')
    
    cmd = f'cd downloads && yt-dlp -f "{format_spec}" --merge-output-format mp4 --progress "{url}"'
    
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    for line in process.stdout:
        parse_progress(line, session_id)
    
    process.wait()
    
    if process.returncode != 0:
        return 'Download failed', 500
    
    files = os.listdir('downloads')
    video_files = [f for f in files if f.endswith(('.mp4', '.mkv', '.mp3'))]
    
    if not video_files:
        return 'No video file found', 500
    
    video_files.sort(key=lambda x: os.path.getctime(os.path.join('downloads', x)), reverse=True)
    file_path = os.path.join('downloads', video_files[0])
    
    if session_id in progress_data:
        del progress_data[session_id]
    
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
