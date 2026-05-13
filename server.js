// Endpoint to download video
app.post('/download', async (req, res) => {
    const { url } = req.body;
    
    if (!url) {
        return res.status(400).json({ error: 'No URL provided' });
    }
    
    console.log(`📥 Downloading: ${url}`);
    
    // Use the full path to python3 and yt_dlp
    const command = `cd "${downloadsDir}" && python3 -m yt_dlp -f "bestvideo+bestaudio" --merge-output-format mp4 "${url}"`;
    
    console.log(`Running command: ${command}`);
    
    exec(command, { maxBuffer: 50 * 1024 * 1024, timeout: 120000 }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error: ${error.message}`);
            console.error(`Stderr: ${stderr}`);
            return res.status(500).json({ error: 'Download failed', details: error.message });
        }
        
        console.log(`Stdout: ${stdout}`);
        
        // Find the downloaded file
        fs.readdir(downloadsDir, (err, files) => {
            if (err) {
                console.error(`Readdir error: ${err}`);
                return res.status(500).json({ error: 'Error finding file' });
            }
            
            console.log(`Files in downloads: ${files.join(', ')}`);
            
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
                // Clean up file after sending
                setTimeout(() => {
                    fs.unlink(filePath, () => {});
                }, 60000);
            });
        });
    });
});