import os
import shutil
import threading
import uuid
from dataclasses import asdict, dataclass, field

from flask import Flask, jsonify, redirect, render_template, request, url_for

import yt_dlp


@dataclass
class DownloadJob:
    job_id: str
    url: str
    format_type: str
    quality: str
    status: str = "Queued"
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    message: str = ""
    output_dir: str = field(default_factory=lambda: os.path.join(os.path.expanduser("~"), "Downloads"))


app = Flask(__name__)
jobs: dict[str, DownloadJob] = {}
jobs_lock = threading.Lock()


def find_ffmpeg_location() -> str | None:
    ffmpeg_binary = shutil.which("ffmpeg")
    if ffmpeg_binary:
        return os.path.dirname(ffmpeg_binary)

    winget_ffmpeg = os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "Microsoft",
        "WinGet",
        "Packages",
        "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe",
        "ffmpeg-8.1.1-full_build",
        "bin",
    )
    if os.path.exists(os.path.join(winget_ffmpeg, "ffmpeg.exe")):
        return winget_ffmpeg

    return None


def build_ydl_options(job: DownloadJob) -> dict:
    options = {
        "outtmpl": os.path.join(job.output_dir, "%(title)s.%(ext)s"),
        "progress_hooks": [lambda data: progress_hook(job.job_id, data)],
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }

    ffmpeg_location = find_ffmpeg_location()
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location

    if job.format_type == "Audio (MP3)":
        options["format"] = "bestaudio/best"
        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
        return options

    if not ffmpeg_location:
        raise RuntimeError("FFmpeg is required for video downloads. Install FFmpeg or add it to PATH, then try again.")

    if job.quality == "Highest":
        options["format"] = "bv*+ba/b"
    elif job.quality == "4K":
        options["format"] = "bv*[height<=2160]+ba/b[height<=2160]/bv*[height<=2160]/b"
    elif job.quality == "1080p":
        options["format"] = "bv*[height<=1080]+ba/b[height<=1080]/bv*[height<=1080]/b"
    elif job.quality == "720p":
        options["format"] = "bv*[height<=720]+ba/b[height<=720]/bv*[height<=720]/b"
    else:
        options["format"] = "bv*+ba/b"

    options["merge_output_format"] = "mkv"
    return options


def progress_hook(job_id: str, data: dict) -> None:
    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        return

    if data.get("status") == "downloading":
        percent_text = data.get("_percent_str", "0.0%").replace("%", "").strip()
        speed = data.get("_speed_str", "N/A")
        eta = data.get("_eta_str", "N/A")

        try:
            progress = float(percent_text)
        except ValueError:
            progress = 0.0

        with jobs_lock:
            job.progress = progress
            job.speed = speed
            job.eta = eta
            job.status = "Downloading"
            job.message = f"{speed} | ETA {eta}"
    elif data.get("status") == "finished":
        with jobs_lock:
            job.status = "Processing"
            job.message = "FFmpeg is finishing the file"


def run_download(job_id: str) -> None:
    with jobs_lock:
        job = jobs[job_id]
        job.status = "Starting"
        job.message = "Preparing download"

    try:
        with yt_dlp.YoutubeDL(build_ydl_options(job)) as ydl:
            ydl.download([job.url])

        with jobs_lock:
            job = jobs[job_id]
            job.status = "Completed"
            job.progress = 100.0
            job.message = "Download complete"
    except Exception as exc:
        with jobs_lock:
            job = jobs[job_id]
            job.status = "Error"
            job.message = str(exc)


def job_to_dict(job: DownloadJob) -> dict:
    return asdict(job)


@app.get("/")
def index():
    return render_template(
        "index.html",
        default_dir=os.path.join(os.path.expanduser("~"), "Downloads"),
        ffmpeg_available=find_ffmpeg_location() is not None,
    )


@app.get("/api/jobs")
def api_jobs():
  with jobs_lock:
    current_jobs = [job_to_dict(job) for job in list(jobs.values())[::-1]]

  return jsonify({"jobs": current_jobs})


@app.post("/add")
def add_job():
    url = request.form.get("url", "").strip()
    if not url:
        return redirect(url_for("index"))

    download_mode = request.form.get("download_mode", "video")
    quality = request.form.get("quality", "Highest")
    output_dir = request.form.get("output_dir", os.path.join(os.path.expanduser("~"), "Downloads")).strip()
    if not output_dir:
        output_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    os.makedirs(output_dir, exist_ok=True)

    format_type = "Audio (MP3)" if download_mode == "audio" else "Video (MKV)"
    job_id = str(uuid.uuid4())
    job = DownloadJob(job_id=job_id, url=url, format_type=format_type, quality=quality, output_dir=output_dir)

    with jobs_lock:
        jobs[job_id] = job

    thread = threading.Thread(target=run_download, args=(job_id,), daemon=True)
    thread.start()

    return redirect(url_for("index"))


def main():
    app.run(host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()