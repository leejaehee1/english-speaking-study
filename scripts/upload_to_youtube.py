#!/usr/bin/env python3
"""
SoundBlock K-Cooking YouTube Data API v3 자동 업로드 스크립트 (100% All-English)

업로드 규칙:
  - Title: 100% English
  - Description: 100% English (Zero Korean)
  - Pinned First Comment: 100% English (Zero Korean)
  - Tags: 100% English
  - Privacy: public (전체 공개)
  - MadeForKids: False (아동용 아님)
  - Custom Thumbnail: 1080p 일러스트 적용

사용법:
  python3 scripts/upload_to_youtube.py [epId] [--privacy public|private|unlisted]
  또는 설명 업데이트만:
  python3 scripts/upload_to_youtube.py [epId] --update-desc-only [VIDEO_ID]
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
if not os.path.exists(CLIENT_SECRETS_FILE):
    CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")

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
                print(f"\n❌ [Error] client_secrets.json not found!")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
            
    return build("youtube", "v3", credentials=creds)

def load_episode_metadata(ep_id):
    """KFoodYoutubeStudio.vue 에서 해당 에피소드의 메타데이터 추출"""
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

def build_all_english_description(ep):
    """100% 완전 영어 설명문(Description) 생성 (한글 0%)"""
    title_en = ep.get('title', 'Korean Dish')
    ep_id = ep.get('id', 'kfood')
    
    intro_en = ep.get('introNarrationEn') or f"Welcome to SoundBlock K-Cooking! Today, let's learn how to cook authentic {title_en} using simple English sound blocks. Master natural English speaking rhythm while cooking delicious Korean food! Let's get cooking!"
    outro_en = ep.get('outroNarrationEn') or f"Mission complete! You've mastered all the key sound blocks for {title_en}! Don't forget to Like and Subscribe for more tasty K-Food English lessons. See you in the next video!"

    steps_list = []
    for i, s in enumerate(ep.get("scenes", [])):
        b0 = s['blocks'][0]['en']
        b1 = s['blocks'][1]['en']
        b2 = s['blocks'][2]['en']
        steps_list.append(f"Step {i+1}: [{b0}] + [{b1}] + [{b2}]")
    steps_desc = "\n".join(steps_list)

    description = f"""{intro_en}

🍳 [Recipe Sound Blocks]
{steps_desc}

{outro_en}

--------------------------------------------------
📌 What is SoundBlock K-Cooking?
SoundBlock K-Cooking helps you speak fluent English effortlessly through mouthwatering Korean recipes. By chunking sentences into rhythmic sound blocks ([Starter] + [Core Action] + [Detail]), you'll speak natural English with zero hesitation!

🔔 Subscribe for weekly delicious K-Cooking English lessons!
#KoreanFood #KFood #KoreanCooking #LearnEnglish #EnglishSpeaking #SoundBlock #CookingInEnglish #{ep_id.replace('-', '')}
"""
    return description

def build_all_english_tags(ep):
    """100% 영어 태그 생성 (한글 0%)"""
    title_words = ep.get('title', '').split()
    clean_words = [w for w in title_words if not any(ord(c) > 127 for c in w)]
    clean_title = " ".join(clean_words)
    
    tags = [
        "Korean Food",
        "K-Food",
        "Korean Cooking",
        "Cooking English",
        "English Speaking",
        "Sound Block",
        clean_title,
        ep.get('id', '')
    ]
    return [t for t in tags if t]

def upload_video(youtube, video_file, title, description, tags, category_id="27", privacy="public"):
    """비디오 파일 업로드 (100% All-English 메타데이터, 전체 공개)"""
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    print(f"\n🚀 [1/3] Uploading Video to YouTube: '{title}' (Privacy: {privacy})")
    print(f"     -> Made for kids: No (100% All-English metadata)")
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"     Upload progress: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    print(f"✅ Video Upload Complete! Video ID: {video_id}")
    print(f"🔗 Watch Link: https://youtu.be/{video_id}")
    return video_id

def set_thumbnail(youtube, video_id, thumbnail_path):
    """1080p 커스텀 썸네일 등록"""
    if not os.path.exists(thumbnail_path):
        print(f"⚠️ [2/3] Thumbnail file not found: {thumbnail_path}")
        return
    
    print(f"🖼️ [2/3] Uploading 1080p Custom Thumbnail: {thumbnail_path}")
    try:
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        )
        request.execute()
        print("✅ Custom Thumbnail Applied Successfully!")
    except Exception as e:
        print(f"⚠️ Thumbnail upload note: {e}")

def post_first_comment(youtube, video_id, ep):
    """100% 완전 영어 첫 댓글(Pinned First Comment) 자동 등록"""
    print(f"💬 [3/3] Posting Pinned First Comment (All-English)...")
    
    scenes = ep.get("scenes", [])
    step_list = []
    for i, s in enumerate(scenes[:5]):
        bb = s["blocks"][0]["en"]
        core = s["blocks"][1]["en"]
        step_list.append(f"• Step {i+1}: [{bb}] + [{core}]")
    steps_txt = "\n".join(step_list)
    
    comment_text = f"""🎉 Welcome to SoundBlock K-Cooking!
Today's core cooking English sound blocks for {ep.get('title', 'Korean Food')}:

{steps_txt}

🔥 Practice speaking out loud with natural rhythm!
Which K-food recipe should we cook next? Let us know in the comments below! 👇
Don't forget to Like & Subscribe for more delicious SoundBlock K-Cooking! 🍲🍗"""

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
        print(f"✅ First Comment Posted Successfully! (Comment ID: {response.get('id')})")
    except Exception as e:
        print(f"⚠️ First comment note: {e}")

def update_existing_video_description(youtube, video_id, ep):
    """이미 업로드된 동영상의 설명을 100% All-English로 즉시 수정"""
    print(f"🔄 Updating YouTube video {video_id} description to 100% English...")
    description = build_all_english_description(ep)
    tags = build_all_english_tags(ep)
    title = ep.get("ytTitle") or ep.get("title")

    request = youtube.videos().update(
        part="snippet",
        body={
            "id": video_id,
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "27",
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en"
            }
        }
    )
    request.execute()
    print(f"✅ Video description successfully updated to 100% English! (Zero Korean)")

def main():
    parser = argparse.ArgumentParser(description="SoundBlock K-Cooking 100% All-English YouTube Uploader")
    parser.add_argument("epId", help="에피소드 ID 또는 번호 (예: kimchi-stew 또는 EP.01)")
    parser.add_argument("--privacy", default="public", choices=["public", "private", "unlisted"], help="공개 범위 (기본: public)")
    parser.add_argument("--video", help="업로드할 동영상 파일 경로")
    parser.add_argument("--update-desc-only", help="Update description of an existing video ID to 100 percent English")
    args = parser.parse_args()

    ep = load_episode_metadata(args.epId)
    if not ep:
        print(f"❌ Episode '{args.epId}' metadata not found.")
        sys.exit(1)

    youtube = get_authenticated_service()

    # 설명만 즉시 100% 영어로 갱신하는 모드
    if args.update_desc_only:
        update_existing_video_description(youtube, args.update_desc_only, ep)
        return

    ep_id = ep["id"]
    ep_num = ep["epNumber"]

    video_path = args.video
    if not video_path:
        home_dl = os.path.expanduser("~/Downloads")
        candidates = [
            # 1. 브라우저에서 자동 다운로드된 최신 파일 (Downloads 폴더)
            os.path.join(home_dl, f"[SoundBlock-KCooking]-{ep_num}-{ep_id}-1080p.webm"),
            os.path.join(home_dl, f"[SoundBlock-KCooking]-{ep_num}-{ep_id}-1080p.mp4"),
            os.path.join(home_dl, f"[SoundBlock-KCooking]-{ep_num.replace('.', '')}-{ep_id}-1080p.webm"),
            os.path.join(home_dl, f"[SoundBlock-KCooking]-{ep_num.replace('.', '')}-{ep_id}-1080p.mp4"),
            # 2. recordings 폴더
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
        print(f"❌ Video file not found: recordings/{ep_id}.webm")
        sys.exit(1)

    title = ep.get("ytTitle") or f"How to Cook Authentic {ep.get('title')} in Easy English | SoundBlock K-Cooking {ep_num}"
    description = build_all_english_description(ep)
    tags = build_all_english_tags(ep)
    thumb_path = os.path.join("docs/public", ep.get("thumbnailImage", "").lstrip("/"))

    # 1. 비디오 업로드
    video_id = upload_video(youtube, video_path, title, description, tags, privacy=args.privacy)

    # 2. 1080p 썸네일 등록
    if thumb_path and os.path.exists(thumb_path):
        set_thumbnail(youtube, video_id, thumb_path)

    # 3. 100% 영어 첫 댓글 등록
    post_first_comment(youtube, video_id, ep)

    print(f"\n🎉 [{ep_num}] 100% All-English Upload Complete!")

if __name__ == "__main__":
    main()
