#!/usr/bin/env python3
"""
SoundBlock K-Cooking YouTube Data API v3 자동 업로드 스크립트

업로드 루틴:
  1. 동영상 업로드 (MP4/WebM)
  2. 타이틀 (ytTitle)
  3. 디스크립션 (인트로 + 사운드블록 레시피 + 아웃트로 + 해시태그)
  4. 아동용 영상 아님 설정 (selfDeclaredMadeForKids=False)
  5. 태그 (요리명, K-Food, SoundBlock 등)
  6. 전체 공개 (public)
  7. 1080p 스냅샷 썸네일 등록
  8. 첫 댓글(First Comment) 자동 등록 (핵심 사운드 블록 복습 가이드)

사용법:
  python3 scripts/upload_to_youtube.py [epId] [--privacy public|private|unlisted]
  예:
  python3 scripts/upload_to_youtube.py doenjang-jjigae --privacy public
"""

import os
import sys
import json
import argparse
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secrets.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"\n❌ [오류] {CLIENT_SECRETS_FILE} 파일이 없습니다!")
                print("Google Cloud Console에서 OAuth 2.0 클라이언트 ID JSON을 다운로드하여 scripts/client_secrets.json 위치에 넣어주세요.\n")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
            
    return build("youtube", "v3", credentials=creds)

def load_episode_metadata(ep_id):
    """KFoodYoutubeStudio.vue 에서 해당 에피소드의 정확한 메타데이터 추출"""
    cmd = [
        "node", "-e", f"""
const fs = require("fs");
const file = fs.readFileSync("docs/.vitepress/components/KFoodYoutubeStudio.vue", "utf8");
const startMarker = "const episodes: CookingEpisode[] = [";
const endMarker = "const currentEpId = ref(";
const startIdx = file.indexOf(startMarker);
const endIdx = file.indexOf(endMarker);
const arrayCode = file.slice(startIdx + startMarker.length - 1, endIdx).trim().replace(/;$/, "");
const fn = new Function("return " + arrayCode);
const episodes = fn();
const ep = episodes.find(e => e.id === '{ep_id}' || e.epNumber === '{ep_id}');
console.log(JSON.stringify(ep || null));
"""
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)

def upload_video(youtube, video_file, title, description, tags, category_id="27", privacy="public"):
    """비디오 파일 업로드 (아동용 영상 아님 체크, 전체 공개 기본)"""
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    print(f"\n🚀 [1/3] 유튜브 업로드 시작: '{title}' (공개 상태: {privacy})")
    print(f"     -> 아동용 영상 아님(Not made for kids): 적용 완료")
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"     진행률: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    print(f"✅ 비디오 업로드 완료! Video ID: {video_id}")
    print(f"🔗 시청 링크: https://youtu.be/{video_id}")
    return video_id

def set_thumbnail(youtube, video_id, thumbnail_path):
    """1080p 커스텀 썸네일 등록"""
    if not os.path.exists(thumbnail_path):
        print(f"⚠️ [2/3] 썸네일 파일이 없습니다: {thumbnail_path}")
        return
    
    print(f"🖼️ [2/3] 1080p 커스텀 썸네일 업로드 중: {thumbnail_path}")
    try:
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        )
        request.execute()
        print("✅ 썸네일 적용 완료!")
    except Exception as e:
        print(f"⚠️ 썸네일 업로드 알림 (채널 전화번호 인증이 필요할 수 있습니다): {e}")

def post_first_comment(youtube, video_id, ep):
    """첫 댓글(Pinned First Comment) 자동 등록"""
    print(f"💬 [3/3] 첫 댓글 등록 중...")
    
    scenes = ep.get("scenes", [])
    step_list = []
    for i, s in enumerate(scenes[:5]):
        bb = s["blocks"][0]["en"]
        core = s["blocks"][1]["en"]
        step_list.append(f"• Step {i+1}: [{bb}] + [{core}]")
    steps_txt = "\n".join(step_list)
    
    comment_text = f"""🎉 Welcome to SoundBlock K-Cooking!
Today's core cooking English blocks for {ep.get('shortTitle', 'Korean Food')}:

{steps_txt}

🔥 Practice speaking out loud with rhythm!
Which K-food recipe should we cook next? Let us know in the comments below! 👇
Don't forget to Like & Subscribe for more delicious SoundBlock K-Cooking! 🍗🍲"""

    try:
        request = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment_text
                        }
                    }
                }
            }
        )
        response = request.execute()
        print(f"✅ 첫 댓글 등록 완료! (Comment ID: {response.get('id')})")
    except Exception as e:
        print(f"⚠️ 첫 댓글 등록 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description="SoundBlock K-Cooking YouTube 원스톱 업로더")
    parser.add_argument("epId", help="에피소드 ID 또는 번호 (예: doenjang-jjigae 또는 EP.11)")
    parser.add_argument("--privacy", default="public", choices=["public", "private", "unlisted"], help="공개 범위 (기본: public)")
    parser.add_argument("--video", help="업로드할 동영상 파일 경로 (생략 시 recordings/{epId}.webm 탐색)")
    args = parser.parse_args()

    # 1) 메타데이터 로드
    ep = load_episode_metadata(args.epId)
    if not ep:
        print(f"❌ 에피소드 '{args.epId}' 정보를 찾을 수 없습니다.")
        sys.exit(1)

    ep_id = ep["id"]
    ep_num = ep["epNumber"]

    # 2) 동영상 파일 경로 탐색
    video_path = args.video
    if not video_path:
        candidates = [
            f"recordings/{ep_id}.webm",
            f"recordings/{ep_id}.mp4",
            f"recordings/{ep_num}_{ep_id}.webm",
            f"recordings/{ep_num}_{ep_id}.mp4"
        ]
        for c in candidates:
            if os.path.exists(c):
                video_path = c
                break

    if not video_path or not os.path.exists(video_path):
        print(f"❌ 녹화된 비디오 파일을 찾을 수 없습니다: recordings/{ep_id}.webm")
        print(f"먼저 'node scripts/record_episode.js {ep_id}' 로 녹화를 완료해 주세요.")
        sys.exit(1)

    # 3) 타이틀, 디스크립션, 태그 준비
    title = ep.get("ytTitle") or f"{ep.get('title')} in Easy English | SoundBlock K-Cooking {ep_num}"
    
    # 8개 장면 레시피 단계 자동 요약
    steps_desc = "\n".join([f"Step {i+1}: {s['blocks'][0]['en']} {s['blocks'][1]['en']} {s['blocks'][2]['en']}" for i, s in enumerate(ep.get("scenes", []))])
    
    description = f"""{ep.get('introNarrationKo')}

Learn authentic Korean cooking while mastering natural English speaking patterns with SoundBlock K-Cooking!

[Recipe Sound Blocks]
{steps_desc}

{ep.get('outroNarrationKo')}

#KFood #KoreanCooking #EnglishSpeaking #LearnEnglish #{ep_id.replace('-', '')} #SoundBlock
"""
    tags = [
        "Korean Food",
        "K-Food",
        "Korean Cooking",
        "Cooking English",
        "English Speaking",
        "Sound Block",
        ep.get("shortTitle", "").replace("🍲", "").replace("🥘", "").replace("🍗", "").strip(),
        ep_id
    ]

    thumb_path = os.path.join("docs/public", ep.get("thumbnailImage", "").lstrip("/"))

    # 4) 인증 및 업로드 실행
    youtube = get_authenticated_service()
    
    # 1. 비디오 업로드 (공개 상태, 아동용 아님 적용)
    video_id = upload_video(youtube, video_path, title, description, tags, privacy=args.privacy)

    # 2. 1080p 커스텀 썸네일 등록
    if thumb_path and os.path.exists(thumb_path):
        set_thumbnail(youtube, video_id, thumb_path)

    # 3. 첫 댓글 등록
    post_first_comment(youtube, video_id, ep)

    print(f"\n🎉 [{ep_num} {ep.get('shortTitle')}] 모든 업로드 및 첫 댓글 작업이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()
