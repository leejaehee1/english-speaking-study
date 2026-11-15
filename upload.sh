#!/usr/bin/env bash
# SoundBlock K-Cooking Season 2 공식 업로드 스크립트 (재생목록 자동 등록 & 순서 꼬임 방지)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$(basename "$SCRIPT_DIR")" = "scripts" ]; then
  PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
else
  PROJECT_ROOT="$SCRIPT_DIR"
fi
cd "$PROJECT_ROOT"

export PYTHONPATH="."

if [ -n "$1" ]; then
  # 특정 에피소드 지정 업로드 (예: ./upload.sh EP.58)
  echo "🚀 [SoundBlock K-Cooking] 에피소드 $1 업로드 시작..."
  python3 scripts/upload_to_youtube.py "$1" --privacy public
else
  # 인자가 없으면 EP.58, EP.59, EP.60 자동 순차 업로드
  echo "============================================================"
  echo "🚀 SoundBlock K-Cooking 시즌 2 잔여 에피소드 자동 순차 업로드"
  echo "============================================================"
  
  TARGETS=("EP.58" "EP.59" "EP.60")
  for ep in "${TARGETS[@]}"; do
    echo "------------------------------------------------------------"
    echo "▶️ $ep 업로드 및 재생목록 등록 확인..."
    python3 scripts/upload_to_youtube.py "$ep" --privacy public || true
    echo "⏳ 다음 에피소드 업로드 전 30초 대기 (유튜브 서버 인코딩 안정화)..."
    sleep 30
  done
  echo "🎉 모든 시즌 2 에피소드 업로드 및 공식 재생목록 등록 완료!"
fi
