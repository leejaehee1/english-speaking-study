#!/usr/bin/env python3
"""
SoundBlock K-Cooking YouTube Data API v3 자동 업로드 스크립트

사전 준비:
  1. Google Cloud Console (https://console.cloud.google.com/) 접속
  2. 새 프로젝트 생성 후 'YouTube Data API v3' 사용 설정
  3. '사용자 인증 정보' -> 'OAuth 2.0 클라이언트 ID' (데스크톱 앱) 생성
  4. 다운로드한 JSON 파일을 이 프로젝트의 'scripts/client_secrets.json' 으로 저장
  5. 패키지 설치:
     pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

사용법:
  python scripts/upload_to_youtube.py [epId] [--privacy private|unlisted|public]
  예:
  python scripts/upload_to_youtube.py samgyetang --privacy private
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
    "https://www.googleapis.com/auth/youtube"
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
const ep = episodes.find(e => e.id === '{ep_id}');
console.log(JSON.stringify(ep || null));
"""
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    ep_data = json.loads(proc.stdout)
    return ep_data

def upload_video(youtube, video_file, title, description, tags, category_id="27", privacy="private"):
    """비디오 파일 업로드"""
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
    print(f"🚀 유튜브 업로드 시작: '{title}' (공개 상태: {privacy})")
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   진행률: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    print(f"✅ 업로드 완료! Video ID: {video_id}")
    print(f"🔗 링크: https://youtu.be/{video_id}")
    return video_id

def set_thumbnail(youtube, video_id, thumbnail_path):
    """1080p 커스텀 썸네일 등록"""
    if not os.path.exists(thumbnail_path):
        print(f"⚠️ 썸네일 파일이 없습니다: {thumbnail_path}")
        return
    
    print(f"🖼️ 커스텀 썸네일 업로드 중: {thumbnail_path}")
    request = youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail_path)
    )
    request.execute()
    print("✅ 썸네일 적용 완료!")

def main():
    parser = argparse.ArgumentParser(description="SoundBlock K-Cooking YouTube 업로더")
    parser.add_argument("epId", help="에피소드 ID (예: samgyetang, doenjang-jjigae)")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"], help="공개 범위 (기본: private)")
    parser.add_argument("--video", help="업로드할 동영상 파일 경로 (생략 시 recordings/{epId}.webm 또는 .mp4 탐색)")
    args = parser.parse_args()

    # 1) 메타데이터 로드
    ep = load_episode_metadata(args.epId)
    if not ep:
        print(f"❌ 에피소드 '{args.epId}' 정보를 찾을 수 없습니다.")
        sys.exit(1)

    # 2) 동영상 파일 경로 탐색
    video_path = args.video
    if not video_path:
        candidates = [
            f"recordings/{args.epId}.webm",
            f"recordings/{args.epId}.mp4",
            f"recordings/{ep['epNumber']}_{args.epId}.mp4"
        ]
        for c in candidates:
            if os.path.exists(c):
                video_path = c
                break

    if not video_path or not os.path.exists(video_path):
        print(f"❌ 녹화된 비디오 파일을 찾을 수 없습니다: recordings/{args.epId}.webm")
        print("먼저 'node scripts/record_episode.js [epId]' 로 녹화를 진행해 주세요.")
        sys.exit(1)

    # 3) 설명문 및 태그 구성
    title = ep.get("ytTitle") or f"How to Cook Authentic Korean {ep.get('title')} in Easy English | SoundBlock EP"
    
    # 레시피 스텝 요약
    steps_desc = "\n".join([f"Step {i+1}: {s['blocks'][0]['en']} {s['blocks'][1]['en']} {s['blocks'][2]['en']}" for i, s in enumerate(ep.get("scenes", []))])
    description = f"""{ep.get('introNarrationKo')}

Learn authentic Korean cooking while mastering natural English speaking patterns with SoundBlock K-Cooking!

[Recipe Sound Blocks]
{steps_desc}

{ep.get('outroNarrationKo')}

#KFood #KoreanCooking #EnglishSpeaking #LearnEnglish #{args.epId.replace('-', '')}
"""
    tags = ["Korean Food", "K-Food", "Cooking English", "English Speaking", "Sound Block", ep.get("shortTitle", ""), args.epId]

    # 썸네일 경로
    thumb_path = os.path.join("docs/public", ep.get("thumbnailImage", "").lstrip("/"))

    # 4) 유튜브 API 클라이언트 초기화 및 업로드 실행
    youtube = get_authenticated_service()
    video_id = upload_video(youtube, video_path, title, description, tags, privacy=args.privacy)

    # 5) 썸네일 등록
    if thumb_path and os.path.exists(thumb_path):
        try:
            set_thumbnail(youtube, video_id, thumb_path)
        except Exception as e:
            print(f"⚠️ 썸네일 업로드 중 알림 (계정 전화번호 인증 필요할 수 있음): {e}")

if __name__ == "__main__":
    main()
