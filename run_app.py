#!/usr/bin/env python3
"""
Launcher script for YouTube Downloader desktop app
This starts the Flask server and opens the browser automatically
"""
import subprocess
import sys
import os
import webbrowser
import threading
import time

def main():
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
        os.chdir(application_path)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # Start the Flask app
    from app import app
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://localhost:3000')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the app
    app.run(host='127.0.0.1', port=3000, debug=False)

if __name__ == '__main__':
    main()
