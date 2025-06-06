import subprocess
import time
import os
import requests
import sys
from threading import Thread
from flask import Flask

app = Flask('')

# ===== CONFIGURATION =====
STREAM_KEY = "tu5h-gs55-0dtc-wqfh-4r6p"  # From YouTube Studio
VIDEOS = [
    "https://studyti.b-cdn.net/15.mp4",
    "https://studyti.b-cdn.net/16.mp4",
    "https://studyti.b-cdn.net/17.mp4",
    "https://studyti.b-cdn.net/8.mp4",
    "https://studyti.b-cdn.net/9.mp4",
    "https://studyti.b-cdn.net/10.mp4",
    "https://studyti.b-cdn.net/11.mp4",
    "https://studyti.b-cdn.net/12.mp4",
    "https://studyti.b-cdn.net/13.mp4",
    "https://studyti.b-cdn.net/14.mp4",
    # Add your other videos
    # "https://studyti.b-cdn.net/14.mp4",  add like this
]
REPL_URL = "https://5a692154-447d-4195-9cb1-f47ffabead49-00-25a5uedmto1an.sisko.replit.dev:3000/"  # Replace with your actual URL
RESOLUTION = "1280:-2"  # 720p: "1280:-2", 480p: "640:-2"
VIDEO_BITRATE = "1500k"  # 720p: "1500k", 480p: "1000k"

# =========================


# Install FFmpeg for Replit
def install_ffmpeg():
    print("⏳ Installing FFmpeg for Railway environment...")
    try:
        # Install FFmpeg using Nix package manager
        result = subprocess.run("nix-env -iA nixpkgs.ffmpeg",
                                shell=True,
                                capture_output=True,
                                text=True)
        print("FFmpeg install output:")
        print(result.stdout)

        # Verify installation
        result = subprocess.run("ffmpeg -version",
                                shell=True,
                                capture_output=True,
                                text=True)
        if "ffmpeg version" in result.stdout:
            print("✅ FFmpeg installed successfully!")
            return True
        else:
            print("❌ FFmpeg verification failed. Output:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"🚨 FFmpeg installation failed: {str(e)}")
        return False


# Keep Replit awake
def heartbeat():
    while True:
        try:
            if not REPL_URL.startswith("https://YourReplName"):
                requests.get(REPL_URL, timeout=5)
                print("❤️ Keep-alive ping sent")
        except Exception as e:
            print(f"⚠️ Ping failed: {str(e)}")
        time.sleep(300)  # Ping every 5 minutes


# Streaming function
def stream_video(url):
    print(f"🔗 Streaming: {url.split('/')[-1]}")

    # FFmpeg command with optimizations
    cmd = [
        "ffmpeg",
        "-re",
        "-analyzeduration",
        "10M",  # Faster analysis
        "-probesize",
        "32M",  # Larger probe buffer
        "-rw_timeout",
        "5000000",  # 5-second timeout
        "-i",
        url,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-b:v",
        VIDEO_BITRATE,
        "-maxrate",
        VIDEO_BITRATE,
        "-bufsize",
        "4000k",
        "-vf",
        f"scale={RESOLUTION},fps=30",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "44100",
        "-f",
        "flv",
        f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
    ]

    print("🚀 Running command:", " ".join(cmd))
    try:
        # Stream with real-time output
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   text=True,
                                   bufsize=1,
                                   universal_newlines=True)
        # Stream FFmpeg output to console
        if process.stdout:
            for line in process.stdout:
                if "frame=" in line:
                    print(line.strip())
        else:
            print(
                "🚨 process.stdout is None. FFmpeg might have failed to start.")
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"🚨 Streaming error: {str(e)}")
        return False


# Main function
def main():
    print("🔥 Starting 24/7 YouTube Stream 🔥")
    print(f"🎬 Videos in loop: {len(VIDEOS)}")

    # Verify video URLs
    for i, url in enumerate(VIDEOS):
        try:
            response = requests.head(url, timeout=10)
            status = "✅ Found" if response.status_code == 200 else f"❌ Status {response.status_code}"
            print(f"Video {i+1}: {status} - {url.split('/')[-1]}")
        except Exception as e:
            print(f"Video {i+1}: ❌ Error - {str(e)}")

    # Install FFmpeg if needed
    try:
        subprocess.run(["ffmpeg", "-version"],
                       check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        print("✅ FFmpeg is already installed")
    except subprocess.CalledProcessError:
        print("⚠️ FFmpeg not found, attempting installation")
        if not install_ffmpeg():
            print("💥 Critical: FFmpeg installation failed. Exiting.")
            return

    # Start heartbeat thread
    Thread(target=heartbeat, daemon=True).start()

    # Main streaming loop
    video_index = 0
    error_count = 0

    while True:
        current_url = VIDEOS[video_index]
        print(
            f"\n🎬 Now playing video {video_index+1}/{len(VIDEOS)}: {current_url.split('/')[-1]}"
        )

        if stream_video(current_url):
            print(f"✅ Finished video {video_index+1}")
            error_count = 0

            # Move to next video (loop to first after last)
            video_index = (video_index + 1) % len(VIDEOS)
        else:
            error_count += 1
            print(f"⚠️ Stream failed ({error_count}/3 attempts)")

            if error_count >= 3:
                print("💥 Too many errors - moving to next video")
                video_index = (video_index + 1) % len(VIDEOS)
                error_count = 0
                time.sleep(10)
            else:
                print("🔄 Retrying same video in 15 seconds...")
                time.sleep(15)


@app.route('/')
def home():
    return "✅ Sunnie-BOT is alive!"


def run_web():
    app.run(host='0.0.0.0', port=3000)


# Start web server in background
Thread(target=run_web).start()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 Uncaught exception: {e}")
        print("🔄 Restarting script...")
        os.execvp(sys.executable, [sys.executable] + sys.argv)

