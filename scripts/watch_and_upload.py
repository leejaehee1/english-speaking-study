#!/usr/bin/env python3
"""
Downloads 폴더 실시간 자동 감지 & YouTube 100% 무인 자동 업로드 데몬

동작 방식:
- ~/Downloads 폴더에 [SoundBlock-KCooking]-EP.*-1080p.mp4 (또는 .webm) 파일이 생성되는지 1초 간격으로 폴링
- 파일 다운로드가 완료(크기 안정화)되면 즉시 upload_to_youtube.py 를 호출하여 자동 업로드
- 업로드 완료된 파일은 처리 완료 목록(processed.json)에 기록하여 중복 업로드 방지
"""

import os
import sys
import time
import json
import re
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
PROCESSED_FILE = os.path.join(SCRIPT_DIR, ".processed_uploads.json")
PYTHON_BIN = sys.executable

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_processed(processed_set):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_set), f, ensure_ascii=False, indent=2)

def is_file_ready(filepath):
    """파일이 아직 브라우저에서 다운로드 중인지(크기 증가 중인지) 확인"""
    try:
        size1 = os.path.getsize(filepath)
        time.sleep(1.2)
        size2 = os.path.getsize(filepath)
        return size1 == size2 and size1 > 5 * 1024 * 1024 # 최소 5MB 이상
    except:
        return False

def extract_ep_id(filename):
    """
    파일명 예시:
    [SoundBlock-KCooking]-EP.06-korean-pancake-1080p.mp4
    [SoundBlock-KCooking]-EP.07-japchae-1080p.mp4
    """
    pattern = r"\[SoundBlock-KCooking\]-(EP\.?\d+)-([a-zA-Z0-9\-]+)-1080p\.(mp4|webm)"
    m = re.match(pattern, filename, re.IGNORECASE)
    if m:
        return m.group(2) # e.g. korean-pancake
    return None

def main():
    print("=======================================================")
    print("👀 [YouTube Auto-Uploader Daemon] Downloads 감시 시작...")
    print(f"📁 감시 폴더: {DOWNLOADS_DIR}")
    print("=======================================================")

    processed = load_processed()
    # 이미 존재하는 이전 파일들은 처리된 것으로 등록
    for f in os.listdir(DOWNLOADS_DIR):
        if f.startswith("[SoundBlock-KCooking]-") and (f.endswith(".mp4") or f.endswith(".webm")):
            processed.add(f)
    save_processed(processed)
    print(f"ℹ️ 기존 녹화본 {len(processed)}개는 이미 완료 목록으로 마킹되었습니다.")
    print("🚀 새 녹화본이 Downloads 폴더에 도착하면 1초 안에 감지하여 즉시 유투브에 업로드합니다!\n")

    while True:
        try:
            files = [f for f in os.listdir(DOWNLOADS_DIR) if f.startswith("[SoundBlock-KCooking]-") and (f.endswith(".mp4") or f.endswith(".webm"))]
            for f in sorted(files):
                if f not in processed:
                    full_path = os.path.join(DOWNLOADS_DIR, f)
                    if is_file_ready(full_path):
                        ep_id = extract_ep_id(f)
                        if not ep_id:
                            print(f"⚠️ 파일명 패턴 불일치 건너뜀: {f}")
                            continue

                        print(f"\n🎯 [새 영상 감지!] 파일: {f} (크기: {os.path.getsize(full_path)/(1024*1024):.1f} MB)")
                        print(f"🚀 EP: {ep_id} YouTube 업로드 실행 중...")

                        uploader_py = os.path.join(SCRIPT_DIR, "upload_to_youtube.py")
                        cmd = [PYTHON_BIN, uploader_py, ep_id, "--video", full_path]
                        res = subprocess.run(cmd)

                        if res.returncode == 0:
                            print(f"✅ {f} YouTube 자동 업로드 성공!")
                            processed.add(f)
                            save_processed(processed)
                        else:
                            print(f"❌ {f} 업로드 중 오류 발생 (코드 {res.returncode})")

            time.sleep(2)
        except KeyboardInterrupt:
            print("\n감시 데몬 종료.")
            break
        except Exception as e:
            print(f"⚠️ 에러 발생: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
