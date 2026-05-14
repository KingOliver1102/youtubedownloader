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
            border-radius: 28px;
            padding: 35px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
        }
        h1 { font-size: 28px; margin-bottom: 6px; color: #333; text-align: center; }
        .sub { text-align: center; color: #666; margin-bottom: 25px; font-size: 13px; }
        
        input {
            width: 100%;
            padding: 14px 16px;
            margin-bottom: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 14px;
            font-size: 14px;
            outline: none;
            transition: all 0.2s;
        }
        input:focus { border-color: #667eea; }
        
        .radio-group {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding: 10px 0;
        }
        .radio-option {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            padding: 8px 16px;
            background: #f0f2f5;
            border-radius: 40px;
            transition: all 0.2s;
        }
        .radio-option.selected {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .radio-option.selected .radio-label {
            color: white;
        }
        .radio-input {
            width: 18px;
            height: 18px;
            cursor: pointer;
            accent-color: #667eea;
        }
        .radio-label {
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            color: #555;
        }
        
        select {
            width: 100%;
            padding: 14px;
            margin-bottom: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 14px;
            font-size: 14px;
            background: white;
            cursor: pointer;
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102,126,234,0.4); }
        button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        
        .progress-container {
            margin-top: 25px;
            display: none;
        }
        .progress-container.show { display: block; }
        .progress-bar-wrapper {
            background: #e8e8e8;
            border-radius: 30px;
            height: 32px;
            overflow: hidden;
        }
        .progress-fill {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            height: 100%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        .progress-text { margin-top: 10px; font-size: 13px; color: #555; text-align: center; }
        
        .status {
            margin-top: 15px;
            padding: 12px;
            border-radius: 14px;
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
            padding: 20px;
            background: #f8f9fa;
            border-radius: 20px;
            display: none;
            text-align: center;
            animation: fadeIn 0.5s ease;
        }
        .video-preview.show { display: block; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .video-preview img { max-width: 100%; border-radius: 16px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .video-preview h3 { font-size: 18px; margin: 10px 0; color: #333; }
        .info-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
            margin-top: 12px;
        }
        .info-badge {
            background: #e8e8e8;
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 12px;
            color: #555;
        }
        .info-badge strong { color: #667eea; }
        
        .filename-preview {
            margin-top: 15px;
            padding: 12px;
            background: #e8f0fe;
            border-radius: 12px;
            font-size: 12px;
            color: #333;
            word-break: break-all;
            text-align: left;
        }
        
        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal.show {
            display: flex;
        }
        .modal-content {
            background: white;
            border-radius: 28px;
            padding: 30px;
            max-width: 400px;
            width: 90%;
            text-align: center;
            animation: fadeIn 0.3s ease;
        }
        .modal-content h3 {
            font-size: 24px;
            margin-bottom: 15px;
            color: #333;
        }
        .modal-content p {
            margin-bottom: 25px;
            color: #666;
        }
        .modal-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        .modal-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 40px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .modal-btn:hover { transform: translateY(-2px); }
        .modal-btn.yes {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .modal-btn.no {
            background: #e0e0e0;
            color: #555;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Downloader</h1>
        <div class="sub">Paste link → Select type & quality → Download</div>
        
        <input type="text" id="url" placeholder="https://youtu.be/hyYnjco6dHA" value="https://youtu.be/hyYnjco6dHA">
        
        <div class="radio-group">
            <label class="radio-option" id="videoOption">
                <input type="radio" name="downloadType" value="video" class="radio-input" checked> 🎥 Video
            </label>
            <label class="radio-option" id="audioOption">
                <input type="radio" name="downloadType" value="audio" class="radio-input"> 🎵 Audio Only
            </label>
        </div>
        
        <select id="quality">
            <option value="best">🎬 Best Quality</option>
            <option value="1080p">📺 1080p Full HD</option>
            <option value="720p">📱 720p HD</option>
            <option value="480p">📱 480p</option>
            <option value="360p">⚡ 360p (Fastest)</option>
        </select>
        
        <button id="downloadBtn">⬇️ Download Video</button>
        
        <div id="progressContainer" class="progress-container">
            <div class="progress-bar-wrapper">
                <div id="progressFill" class="progress-fill">0%</div>
            </div>
            <div id="progressText" class="progress-text">Initializing...</div>
        </div>
        
        <div id="status" class="status"></div>
        <div id="videoPreview" class="video-preview"></div>
    </div>
    
    <!-- Modal for "Download Another" -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <h3>🎉 Download Complete!</h3>
            <p>Your file has been saved to your Downloads folder.</p>
            <div class="modal-buttons">
                <button class="modal-btn yes" id="downloadAnotherBtn">✅ Download Another</button>
                <button class="modal-btn no" id="closeModalBtn">❌ Close</button>
            </div>
        </div>
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
        const videoOption = document.getElementById('videoOption');
        const audioOption = document.getElementById('audioOption');
        const radioInputs = document.querySelectorAll('.radio-input');
        const modal = document.getElementById('modal');
        const downloadAnotherBtn = document.getElementById('downloadAnotherBtn');
        const closeModalBtn = document.getElementById('closeModalBtn');
        
        let progressInterval = null;
        let currentVideoInfo = null;
        
        // Modal functions
        function showModal() {
            modal.classList.add('show');
        }
        
        function hideModal() {
            modal.classList.remove('show');
        }
        
        function resetForNewDownload() {
            urlInput.value = '';
            urlInput.focus();
            videoPreview.classList.remove('show');
            progressContainer.classList.remove('show');
            statusDiv.className = 'status';
            statusDiv.textContent = '';
            updateProgress(0, 'Ready');
        }
        
        downloadAnotherBtn.addEventListener('click', () => {
            hideModal();
            resetForNewDownload();
        });
        
        closeModalBtn.addEventListener('click', () => {
            hideModal();
        });
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal();
            }
        });
        
        // Radio button styling
        radioInputs.forEach(radio => {
            radio.addEventListener('change', function() {
                document.querySelectorAll('.radio-option').forEach(opt => opt.classList.remove('selected'));
                this.closest('.radio-option').classList.add('selected');
                updateQualityOptions();
                if (currentVideoInfo) updatePreviewWithType();
            });
        });
        
        function updateQualityOptions() {
            const isAudio = getSelectedType() === 'audio';
            qualitySelect.innerHTML = isAudio 
                ? '<option value="audio">🎵 Best Audio (MP3)</option>'
                : '<option value="best">🎬 Best Quality</option><option value="1080p">📺 1080p Full HD</option><option value="720p">📱 720p HD</option><option value="480p">📱 480p</option><option value="360p">⚡ 360p (Fastest)</option>';
        }
        
        function getSelectedType() {
            return document.querySelector('input[name="downloadType"]:checked').value;
        }
        
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
        
        function updatePreviewWithType() {
            if (!currentVideoInfo) return;
            const isAudio = getSelectedType() === 'audio';
            const fileType = isAudio ? '🎵 Audio File' : '🎬 Video File';
            const extension = isAudio ? '.mp3' : '.mp4';
            const filename = `${currentVideoInfo.title.replace(/[^\\w\\s]/gi, '')}${extension}`;
            
            const existingFilename = videoPreview.querySelector('.filename-preview');
            if (existingFilename) existingFilename.innerHTML = `📁 <strong>Will save as:</strong> ${filename.substring(0, 60)}${filename.length > 60 ? '...' : ''}`;
        }
        
        function startProgressMonitoring(sessionId) {
            if (progressInterval) clearInterval(progressInterval);
            progressInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/progress/${sessionId}`);
                    const data = await response.json();
                    if (data.percentage >= 100) {
                        updateProgress(100, 'Complete! Processing...');
                        setTimeout(() => progressContainer.classList.remove('show'), 1500);
                        if (progressInterval) clearInterval(progressInterval);
                    } else if (data.percentage > 0) {
                        updateProgress(data.percentage, data.status || 'Downloading...');
                    }
                } catch (e) {}
            }, 800);
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
                    currentVideoInfo = info;
                    const videoId = url.split('v=')[1]?.split('&')[0] || url.split('youtu.be/')[1]?.split('?')[0];
                    const isAudio = getSelectedType() === 'audio';
                    const fileType = isAudio ? '🎵 Audio' : '🎬 Video';
                    const extension = isAudio ? '.mp3' : '.mp4';
                    const filename = `${info.title.replace(/[^\\w\\s]/gi, '')}${extension}`;
                    
                    videoPreview.innerHTML = `
                        <img src="https://img.youtube.com/vi/${videoId}/mqdefault.jpg" onerror="this.style.display='none'">
                        <h3>${escapeHtml(info.title)}</h3>
                        <div class="info-grid">
                            <span class="info-badge">⏱️ ${Math.floor(info.duration/60)}:${(info.duration%60).toString().padStart(2,'0')}</span>
                            <span class="info-badge">👤 ${escapeHtml(info.uploader)}</span>
                            <span class="info-badge">📀 ${fileType}</span>
                        </div>
                        <div class="filename-preview">
                            📁 <strong>Will save as:</strong> ${filename.substring(0, 70)}${filename.length > 70 ? '...' : ''}
                        </div>
                    `;
                    videoPreview.classList.add('show');
                }
            } catch (e) { console.log('Could not fetch video info'); }
        }
        
        downloadBtn.addEventListener('click', async () => {
            const url = urlInput.value.trim();
            const quality = qualitySelect.value;
            const type = getSelectedType();
            
            if (!url) { showStatus('Please enter a YouTube URL', 'error'); return; }
            
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
                    body: JSON.stringify({ url: url, quality: quality, type: type, sessionId: sessionId })
                });
                
                if (!response.ok) throw new Error('Download failed');
                
                const blob = await response.blob();
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'download.mp4';
                if (contentDisposition) {
                    const match = contentDisposition.match(/filename="(.+)"/);
                    if (match) filename = match[1];
                }
                
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = filename;
                a.click();
                URL.revokeObjectURL(a.href);
                
                showStatus(`✅ ${type === 'audio' ? 'Audio' : 'Video'} downloaded!`, 'success');
                
                // Show the modal asking if they want to download another
                setTimeout(() => {
                    showModal();
                }, 500);
                
            } catch (error) {
                showStatus('❌ Download failed. Make sure the video is public.', 'error');
                progressContainer.classList.remove('show');
            } finally {
                downloadBtn.disabled = false;
                if (progressInterval) setTimeout(() => clearInterval(progressInterval), 2000);
            }
        });
        
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
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
        
        setTimeout(() => fetchVideoInfo(urlInput.value.trim()), 500);
        updateQualityOptions();
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
        progress_data[session_id]['status'] = f'{percent:.1f}%'

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video-info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    cmd = f'yt-dlp --no-playlist --quiet --dump-json "{url}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
    
    if result.returncode != 0:
        return jsonify({'error': 'Failed'}), 500
    
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
    data = progress_data.get(session_id, {'percentage': 0, 'status': 'Starting...'})
    return jsonify({
        'percentage': data.get('percentage', 0),
        'status': data.get('status', 'Downloading...')
    })

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    quality = data.get('quality', 'best')
    download_type = data.get('type', 'video')
    session_id = data.get('sessionId', str(int(time.time())))
    
    if not url:
        return 'No URL provided', 400
    
    os.makedirs('downloads', exist_ok=True)
    
    progress_data[session_id] = {'percentage': 0, 'status': 'Starting...'}
    
    # Get video title first for filename
    title_cmd = f'yt-dlp --no-playlist --quiet --get-title "{url}"'
    title_result = subprocess.run(title_cmd, shell=True, capture_output=True, text=True)
    video_title = title_result.stdout.strip().replace('/', '-').replace('\\', '-')[:100]
    
    if download_type == 'audio':
        format_spec = 'bestaudio/best'
        output_ext = 'mp3'
        cmd = f'cd downloads && yt-dlp --no-playlist --quiet --extract-audio --audio-format mp3 --audio-quality 0 -o "{video_title}.%(ext)s" "{url}"'
    else:
        quality_map = {
            '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
            '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
            '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
            '360p': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]',
            'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        }
        format_spec = quality_map.get(quality, 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best')
        output_ext = 'mp4'
        cmd = f'cd downloads && yt-dlp --no-playlist --quiet -f "{format_spec}" --merge-output-format mp4 -o "{video_title}.%(ext)s" "{url}"'
    
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
        if 'Merging formats into' in line:
            progress_data[session_id]['percentage'] = 95
            progress_data[session_id]['status'] = 'Merging...'
    
    process.wait()
    
    if process.returncode != 0:
        return 'Download failed', 500
    
    files = os.listdir('downloads')
    video_files = [f for f in files if f.endswith(('.mp4', '.mp3', '.m4a'))]
    
    if not video_files:
        return 'No file found', 500
    
    video_files.sort(key=lambda x: os.path.getctime(os.path.join('downloads', x)), reverse=True)
    file_path = os.path.join('downloads', video_files[0])
    original_filename = video_files[0]
    
    # Create a clean filename
    clean_filename = f"{video_title}.{output_ext}"
    new_path = os.path.join('downloads', clean_filename)
    if file_path != new_path and not os.path.exists(new_path):
        os.rename(file_path, new_path)
        file_path = new_path
    
    if session_id in progress_data:
        del progress_data[session_id]
    
    return send_file(file_path, as_attachment=True, download_name=clean_filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)
