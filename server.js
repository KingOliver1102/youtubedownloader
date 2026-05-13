const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

const downloadsDir = path.join(__dirname, 'downloads');
if (!fs.existsSync(downloadsDir)) fs.mkdirSync(downloadsDir);

app.post('/download', async (req, res) => {
    const { url } = req.body;
    
    if (!url) {
        return res.status(400).json({ error: 'No URL provided' });
    }
    
    console.log(`📥 Downloading: ${url}`);
    
    const command = `cd "${downloadsDir}" && yt-dlp -f "bestvideo+bestaudio" --merge-output-format mp4 "${url}"`;
    
    exec(command, { maxBuffer: 50 * 1024 * 1024 }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error: ${error.message}`);
            return res.status(500).json({ error: 'Download failed' });
        }
        
        fs.readdir(downloadsDir, (err, files) => {
            if (err) return res.status(500).json({ error: 'Error finding file' });
            
            const videoFile = files.find(f => f.endsWith('.mp4') || f.endsWith('.mkv'));
            if (!videoFile) return res.status(500).json({ error: 'No video file found' });
            
            const filePath = path.join(downloadsDir, videoFile);
            res.download(filePath, videoFile, (err) => {
                setTimeout(() => fs.unlink(filePath, () => {}), 60000);
            });
        });
    });
});

app.listen(PORT, () => {
    console.log(`✅ Server running at http://localhost:${PORT}`);
});