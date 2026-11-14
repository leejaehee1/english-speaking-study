#!/usr/bin/env bash
# SoundBlock K-Cooking: 전 에피소드 자동 녹화 및 유튜브 순차 업로드 파이프라인
set -e

# 대상 에피소드 목록 (예: 순두부찌개, 된장찌개 등)
EPISODES=("sundubu-jjigae" "samgyetang" "doenjang-jjigae" "budae-jjigae")

echo "=========================================="
echo "🎥 K-Cooking 자동 녹화 & 유튜브 업로드 시작"
echo "=========================================="

for ep in "${EPISODES[@]}"; do
  echo "------------------------------------------"
  echo "▶️ [1/2] 녹화 시작: $ep"
  node scripts/record_episode.js "$ep"

  echo "▶️ [2/2] 유튜브 업로드 시작: $ep (기본: 비공개 private)"
  python3 scripts/upload_to_youtube.py "$ep" --privacy private

  echo "✅ 완료: $ep"
  sleep 5
done

echo "🎉 모든 지정 에피소드 녹화 및 업로드 완료!"
