import os
import json
import time
import requests
from urllib.parse import urlparse
from yt_dlp import YoutubeDL
import tkinter as tk
from tkinter import filedialog

CONFIG_FILE = "config.json"

# Load or create config
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_download_folder():
    config = load_config()
    if "download_path" in config and os.path.isdir(config["download_path"]):
        return config["download_path"]

    print("📁 First time setup: Please choose a folder to save your downloads.")

    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select Download Folder")

    if not folder:
        print("❌ No folder selected. Using default 'downloads' folder.")
        folder = "downloads"

    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
            print(f"✅ Folder created: {folder}")
        except Exception as e:
            print(f"❌ Error creating folder: {e}")
            return "downloads"

    config["download_path"] = folder
    save_config(config)
    return folder

def check_ffmpeg():
    from shutil import which
    if not which("ffmpeg"):
        print("\n⚠️  FFmpeg is not found in PATH — required for merging YouTube formats.")
        print("➡️  Please install FFmpeg or add it to your system PATH.\n")

def download_video(url, output_dir, custom_filename=None):
    try:
        if "youtube.com" in url or "youtu.be" in url:
            print(f"🎬 Downloading from YouTube: {url}")
            ydl_opts = {
                "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
                "format": "best[height<=1080][ext=mp4]/bestvideo[height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best",
                "merge_output_format": "mp4",
                "noplaylist": True,
                "postprocessors": [{
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }],
                "writesubtitles": False,
                "writeautomaticsub": False,
            }

            if custom_filename:
                ydl_opts["outtmpl"] = os.path.join(output_dir, f"{custom_filename}.%(ext)s")

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        else:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()

            if custom_filename:
                filename = custom_filename
            else:
                filename = os.path.basename(urlparse(url).path)
                if not filename:
                    filename = "video.mp4"

            filepath = os.path.join(output_dir, filename)

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
                        else:
                            print(f"\rDownloaded: {downloaded} bytes", end='')

            print(f"\n✅ Download complete: {filepath}")
            return True

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def download_multiple_videos(urls, output_dir):
    success, fail = 0, 0
    for i, url in enumerate(urls, 1):
        print(f"\n--- Downloading video {i}/{len(urls)} ---")
        if download_video(url, output_dir):
            success += 1
        else:
            fail += 1
        time.sleep(1)
    print(f"\n=== Download Summary ===")
    print(f"✅ Successful: {success}")
    print(f"❌ Failed: {fail}")

# Main entry
if __name__ == "__main__":
    print("🎥 Universal Video Downloader\n")

    check_ffmpeg()
    download_path = get_download_folder()

    choice = input("Download (1) Single video or (2) Multiple videos? ").strip()

    if choice == '1':
        video_url = input("Enter video or YouTube URL: ").strip()
        if video_url:
            custom_name = input("Custom filename (optional): ").strip()
            download_video(video_url, download_path, custom_name if custom_name else None)

    elif choice == '2':
        print("Paste video URLs one per line. Enter an empty line to finish:\n")
        urls = []
        while True:
            line = input()
            if line.strip() == "":
                break
            urls.append(line.strip())
        if urls:
            download_multiple_videos(urls, download_path)
    else:
        print("❌ Invalid choice.")