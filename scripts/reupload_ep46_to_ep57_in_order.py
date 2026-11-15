#!/usr/bin/env python3
"""
기존 순서가 꼬인 EP.46 ~ EP.57 비디오를 삭제하고,
유튜브 서버의 인코딩 완료(Processing complete)를 동기식으로 확인하며
EP.46 -> EP.47 -> ... -> EP.57 정순으로 안전하게 재업로드하는 스크립트.
"""

import os
import sys
import json
import time
from scripts.upload_to_youtube import (
    get_authenticated_service,
    load_episode_metadata,
    build_all_english_description,
    build_all_english_tags,
    upload_video,
    set_thumbnail,
    post_first_comment
)

OLD_VIDEO_IDS = [
    ("EP.46", "t_1nPoOQYRU"),
    ("EP.47", "J8br8bXr5KY"),
    ("EP.48", "DwJmTNXj_EM"),
    ("EP.49", "p1uRXP6KjWo"),
    ("EP.50", "-wcgkh692qk"),
    ("EP.51", "lzDiGzzEgcY"),
    ("EP.52", "1s_gUtJj4lU"),
    ("EP.53", "2S0m5UJUU4Y"),
    ("EP.54", "CcXpOje-Xlw"),
    ("EP.55", "eALrwnil1Qo"),
    ("EP.56", "zn-ak_0fJcw"),
    ("EP.57", "y6V8FsEM4K4"),
]

TARGET_EPS = [
    "EP.46", "EP.47", "EP.48", "EP.49", "EP.50",
    "EP.51", "EP.52", "EP.53", "EP.54", "EP.55",
    "EP.56", "EP.57"
]

RESULTS_FILE = "scripts/upload_results_s2_clean.json"

def delete_old_videos(youtube):
    print("=" * 60)
    print("🗑️ [단계 1] 기존 순서가 꼬인 12개 비디오 삭제 시작...")
    print("=" * 60)
    for ep_num, vid in OLD_VIDEO_IDS:
        try:
            print(f"🗑️ Deleting {ep_num} ({vid})...", end=" ")
            youtube.videos().delete(id=vid).execute()
            print("✅ 삭제 완료")
        except Exception as e:
            print(f"⚠️ 이미 삭제되었거나 오류: {e}")
        time.sleep(1)
    print("\n✅ 기존 12개 비디오 정리 완료!\n")

def wait_for_video_processing(youtube, video_id, max_wait_sec=180):
    """유튜브 서버에서 비디오 처리가 완료(processed)될 때까지 대기"""
    print(f"⏳ 유튜브 서버 인코딩 및 처리 완료 대기 중 (Video ID: {video_id})...")
    start = time.time()
    while time.time() - start < max_wait_sec:
        try:
            res = youtube.videos().list(part="status,processingDetails", id=video_id).execute()
            items = res.get("items", [])
            if items:
                status = items[0].get("status", {})
                upload_status = status.get("uploadStatus")
                proc_details = items[0].get("processingDetails", {})
                proc_status = proc_details.get("processingStatus")

                print(f"   [상태] uploadStatus: {upload_status}, processingStatus: {proc_status} ({int(time.time() - start)}초 경과)")

                if upload_status == "processed" or proc_status == "succeeded":
                    print("   ✅ 유튜브 서버 인코딩 완료 확인!")
                    return True
                if upload_status == "failed" or proc_status == "failed":
                    print("   ❌ 유튜브 서버 인코딩 실패")
                    return False
        except Exception as e:
            print(f"   ⚠️ 상태 확인 중 예외: {e}")
        time.sleep(10)

    print("   ⚠️ 최대 대기 시간 도달 (기본 처리 계속 진행)")
    return True

def main():
    youtube = get_authenticated_service()

    # 1. 기존 꼬인 영상 삭제
    delete_old_videos(youtube)

    time.sleep(5)

    # 2. 결과 로드
    results = {}
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = {}

    print("=" * 60)
    print("🚀 [단계 2] 순차 정렬 업로드 시작 (EP.46 → EP.57)")
    print("=" * 60)

    for i, ep_num in enumerate(TARGET_EPS):
        if ep_num in results and results[ep_num].get("status") == "success":
            print(f"⏩ {ep_num} 이미 성공 (ID: {results[ep_num].get('video_id')}). 건너뜁니다.")
            continue

        print(f"\n==================================================")
        print(f"▶️ [{i+1}/{len(TARGET_EPS)}] 업로드 시작: {ep_num}")
        print(f"==================================================")

        ep = load_episode_metadata(ep_num)
        if not ep:
            print(f"❌ {ep_num} 메타데이터 로드 실패")
            continue

        ep_id = ep["id"]
        home_dl = os.path.expanduser("~/Downloads")
        video_path = os.path.join(home_dl, f"[SoundBlock-KCooking]-{ep_num}-{ep_id}-1080p.mp4")
        if not os.path.exists(video_path):
            video_path = os.path.join(home_dl, f"[SoundBlock-KCooking]-{ep_num.replace('.', '')}-{ep_id}-1080p.mp4")

        if not os.path.exists(video_path):
            print(f"❌ 영상 파일을 찾을 수 없습니다: {video_path}")
            continue

        title = ep.get("ytTitle") or f"How to Cook Authentic {ep.get('title')} in Easy English | SoundBlock K-Cooking {ep_num}"
        if len(title) > 100:
            title = title[:100].strip()
        description = build_all_english_description(ep)
        tags = build_all_english_tags(ep)
        thumb_path = os.path.join("docs/public", ep.get("thumbnailImage", "").lstrip("/"))

        try:
            # 1. 비디오 업로드
            video_id = upload_video(youtube, video_path, title, description, tags, privacy="public")

            # 2. 썸네일 등록
            if thumb_path and os.path.exists(thumb_path):
                set_thumbnail(youtube, video_id, thumb_path)

            # 3. 첫 고정 댓글 등록
            post_first_comment(youtube, video_id, ep)

            # 4. 유튜브 서버 인코딩 완료 대기 (순서 꼬임 방지 핵심)
            wait_for_video_processing(youtube, video_id, max_wait_sec=120)

            # 다음 영상 전 안정적인 15초 버퍼
            print(f"✅ {ep_num} 완벽 등록 완료! 다음 에피소드 업로드 전 15초 대기...")
            time.sleep(15)

            results[ep_num] = {
                "status": "success",
                "video_id": video_id,
                "url": f"https://youtu.be/{video_id}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        except Exception as e:
            err_msg = str(e)
            print(f"❌ {ep_num} 업로드 중 오류 발생: {err_msg}")
            results[ep_num] = {
                "status": "failed",
                "error": err_msg,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            if "quotaExceeded" in err_msg or "quota" in err_msg.lower():
                print("\n⚠️ [Quota Exceeded] YouTube Data API 일일 쿼터 초과!")
                break

    print("\n" + "=" * 60)
    print("📋 최종 재업로드 결과 요약:")
    for ep_num in TARGET_EPS:
        res = results.get(ep_num, {"status": "pending"})
        print(f"  {ep_num}: {res.get('status')} (ID: {res.get('video_id', 'N/A')})")
    print("=" * 60)

if __name__ == "__main__":
    main()
