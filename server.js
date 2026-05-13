const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Create downloads folder
const downloadsDir = path.join(__dirname, 'downloads');
if (!fs.existsSync(downloadsDir)) fs.mkdirSync(downloadsDir);

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).send('OK');
});

// Endpoint to download video
app.post('/download', async (req, res) => {
    const { url } = req.body;
    
    if (!url) {
        return res.status(400).json({ error: 'No URL provided' });
    }
    
    console.log(`📥 Downloading: ${url}`);
    
    // First, check if yt-dlp is installed
    exec('python3 -m yt_dlp --version', (checkError) => {
        if (checkError) {
            console.error('yt-dlp not found, installing...');
            exec('pip3 install yt-dlp --upgrade', (installError) => {
                if (installError) {
                    return res.status(500).json({ error: 'Failed to install yt-dlp' });
                }
                startDownload();
            });
        } else {
            startDownload();
        }
    });
    
    function startDownload() {
        const command = `cd "${downloadsDir}" && python3 -m yt_dlp -f "bestvideo+bestaudio" --merge-output-format mp4 "${url}"`;
        
        exec(command, { maxBuffer: 50 * 1024 * 1024, timeout: 120000 }, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error: ${error.message}`);
                console.error(`Stderr: ${stderr}`);
                return res.status(500).json({ error: 'Download failed', details: error.message });
            }
            
            // Find the downloaded file
            fs.readdir(downloadsDir, (err, files) => {
                if (err) {
                    return res.status(500).json({ error: 'Error finding file' });
                }
                
                const videoFiles = files.filter(f => f.endsWith('.mp4') || f.endsWith('.mkv'));
                if (videoFiles.length === 0) {
                    return res.status(500).json({ error: 'No video file found' });
                }
                
                // Get the most recently created file
                let newestFile = videoFiles[0];
                let newestTime = 0;
                
                videoFiles.forEach(file => {
                    const filePath = path.join(downloadsDir, file);
                    const stats = fs.statSync(filePath);
                    if (stats.ctimeMs > newestTime) {
                        newestTime = stats.ctimeMs;
                        newestFile = file;
                    }
                });
                
                const filePath = path.join(downloadsDir, newestFile);
                console.log(`Sending file: ${newestFile}`);
                
                res.download(filePath, newestFile, (err) => {
                    if (err) console.error('Download send error:', err);
                });
            });
        });
    }
});

// Endpoint to get video info
app.post('/info', async (req, res) => {
    const { url } = req.body;
    
    if (!url) {
        return res.status(400).json({ error: 'No URL provided' });
    }
    
    const command = `python3 -m yt_dlp --dump-json "${url}"`;
    
    exec(command, { maxBuffer: 10 * 1024 * 1024, timeout: 30000 }, (error, stdout, stderr) => {
        if (error) {
            console.error('Info error:', error.message);
            return res.status(500).json({ error: 'Failed to get video info' });
        }
        
        try {
            const info = JSON.parse(stdout);
            res.json({
                title: info.title,
                thumbnail: info.thumbnail,
                duration: info.duration,
                uploader: info.uploader
            });
        } catch (e) {
            console.error('Parse error:', e);
            res.status(500).json({ error: 'Failed to parse video info' });
        }
    });
});

app.listen(PORT, () => {
    console.log(`✅ YouTube Downloader App running on port ${PORT}`);
});