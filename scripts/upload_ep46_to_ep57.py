#!/usr/bin/env python3
"""
Upload EP.46 ~ EP.57 to YouTube sequentially with 100% All-English metadata.
"""

import os
import sys
import json
import time
import subprocess

TARGET_EPS = [
    "EP.46", "EP.47", "EP.48", "EP.49", "EP.50",
    "EP.51", "EP.52", "EP.53", "EP.54", "EP.55",
    "EP.56", "EP.57"
]

RESULTS_FILE = "scripts/upload_results_s2.json"

def load_results():
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_results(results):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def main():
    results = load_results()
    print("=" * 60)
    print("🚀 SoundBlock K-Cooking Season 2 (EP.46 ~ EP.57) YouTube Upload")
    print("=" * 60)

    for ep_num in TARGET_EPS:
        if ep_num in results and results[ep_num].get("status") == "success":
            print(f"⏩ {ep_num} already uploaded successfully (ID: {results[ep_num].get('video_id')}). Skipping.")
            continue

        print(f"\n▶️ Starting upload for {ep_num}...")
        cmd = [sys.executable, "scripts/upload_to_youtube.py", ep_num, "--privacy", "public"]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        output_lines = []
        video_id = None

        for line in proc.stdout:
            print(line, end="")
            output_lines.append(line)
            if "Video ID:" in line:
                parts = line.strip().split("Video ID:")
                if len(parts) > 1:
                    video_id = parts[1].strip()

        proc.wait()

        full_output = "".join(output_lines)
        if proc.returncode == 0 and video_id:
            print(f"✅ {ep_num} upload succeeded! Video ID: {video_id}")
            results[ep_num] = {
                "status": "success",
                "video_id": video_id,
                "url": f"https://youtu.be/{video_id}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            save_results(results)
        else:
            print(f"❌ {ep_num} upload failed with code {proc.returncode}")
            results[ep_num] = {
                "status": "failed",
                "error": full_output[-500:],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            save_results(results)

            if "quotaExceeded" in full_output or "quota" in full_output.lower():
                print("\n⚠️ [Quota Exceeded] Daily YouTube Data API quota reached!")
                print("Stopping further uploads for today. Please resume tomorrow or request quota increase.")
                break
            else:
                print(f"Continuing to next episode in 5 seconds...")

        time.sleep(3)

    print("\n" + "=" * 60)
    print("📋 Upload Summary:")
    for ep_num in TARGET_EPS:
        res = results.get(ep_num, {"status": "pending"})
        status = res.get("status")
        vid = res.get("video_id", "N/A")
        print(f"  {ep_num}: {status} (ID: {vid})")
    print("=" * 60)

if __name__ == "__main__":
    main()
