# Modern Python YouTube Downloader

A clean, modern YouTube downloader built with Python, Flask, and yt-dlp.

## Features
- **Modern UI**: Dark-themed, responsive web interface with a polished aesthetic.
- **Multithreading**: Core downloading logic runs in a background thread, keeping the web UI responsive.
- **Queue Management**: Add multiple videos or playlists to your queue and download them concurrently.
- **Quality Selection**: Choose between different video resolutions (1080p, 720p) or download audio-only (MP3).
- **FFmpeg Integration**: yt-dlp handles merging video and audio streams flawlessly (FFmpeg required).

## Installation

1. Install Python 3.9+
2. Clone this repository or download the files.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. **Important**: You must have FFmpeg installed and available on your PATH for video downloads. If FFmpeg is missing, the app will still allow audio downloads, but video jobs will fail with a clear message until FFmpeg is installed.
   - Windows: Download from gyan.dev, extract, and add the `bin` folder to your Environment Variables.
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

## Running the App
```bash
python main.py
```

Then open http://127.0.0.1:5000 in your browser. The job list refreshes automatically every few seconds.

## Building a Windows Executable (PyInstaller)

To compile this project into a standalone `.exe` file:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Run the build command from the root directory:
   ```bash
   pyinstaller --noconfirm --onedir --windowed --add-data "ui/styles.qss;ui/" --name "ModernYTDownloader" main.py
   ```
   *Note: Using `--onedir` is often recommended over `--onefile` for PyQt6 apps as it starts faster. If you prefer a single file, change `--onedir` to `--onefile`.*

3. Find the compiled application inside the `dist/ModernYTDownloader/` folder.
