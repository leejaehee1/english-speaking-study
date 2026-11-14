/**
 * SoundBlock K-Cooking 완전 무인 자동 녹화 & YouTube 자동 업로드 파이프라인
 *
 * 특징:
 * - 사람 마우스 클릭 0번 (Zero User Clicks)
 * - puppeteer-stream 기반 1920x1080 60fps + Opus/AAC 디지털 원음 녹화
 * - 에피소드 완주 자동 감지 (Intro -> Scene 1~8 -> Outro)
 * - ffmpeg-static 초고속 무손실 MP4 리먹싱
 * - upload_to_youtube.py 연동 (100% 영문 메타데이터, 1080p 썸네일, 8개 청크 첫 고정댓글)
 */

import { launch, getStream, wss } from 'puppeteer-stream';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn, execSync } from 'child_process';
import ffmpegPath from 'ffmpeg-static';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');
const RECORDINGS_DIR = path.resolve(ROOT_DIR, 'recordings');

if (!fs.existsSync(RECORDINGS_DIR)) {
  fs.mkdirSync(RECORDINGS_DIR, { recursive: true });
}

// 에피소드 목록 매핑
const EPISODE_ALIAS = {
  '1': 'kimchi-stew',
  '2': 'kimchi-fried-rice',
  '3': 'korean-ramen',
  '4': 'chuncheon-dakgalbi',
  '5': 'tteokbokki',
  'ep01': 'kimchi-stew',
  'ep02': 'kimchi-fried-rice',
  'ep03': 'korean-ramen',
  'ep04': 'chuncheon-dakgalbi',
  'ep05': 'tteokbokki',
  'ep.01': 'kimchi-stew',
  'ep.02': 'kimchi-fried-rice',
  'ep.03': 'korean-ramen',
  'ep.04': 'chuncheon-dakgalbi',
  'ep.05': 'tteokbokki',
};

async function recordAndUploadEpisode(rawEpId) {
  const epId = EPISODE_ALIAS[rawEpId?.toLowerCase()] || rawEpId || 'tteokbokki';
  console.log(`\n=============================================================`);
  console.log(`🎬 [무인 자동화 시작] 에피소드: ${epId}`);
  console.log(`=============================================================`);

  const rawWebmPath = path.join(RECORDINGS_DIR, `${epId}_raw.webm`);
  const finalMp4Path = path.join(RECORDINGS_DIR, `${epId}.mp4`);

  if (fs.existsSync(rawWebmPath)) fs.unlinkSync(rawWebmPath);
  if (fs.existsSync(finalMp4Path)) fs.unlinkSync(finalMp4Path);

  const fileStream = fs.createWriteStream(rawWebmPath);

  // 1) 크롬 브라우저 실행 (puppeteer-stream 1080p 캡처)
  console.log(`🚀 브라우저 1080p 스튜디오 기동 중...`);
  const browser = await launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: false, // 백그라운드 오디오 캡처 안정성 확보
    defaultViewport: {
      width: 1920,
      height: 1080
    },
    args: [
      '--autoplay-policy=no-user-gesture-required',
      '--window-size=1920,1080',
      '--no-sandbox',
      '--disable-setuid-sandbox'
    ]
  });

  const page = await browser.newPage();
  const studioUrl = `http://localhost:5173/english-speaking-study/kfood/?ep=${epId}&fullscreen=1`;
  console.log(`🌐 스튜디오 접속: ${studioUrl}`);
  await page.goto(studioUrl, { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 2500));

  // 2) 탭 오디오 + 비디오 스트림 캡처 연결
  console.log(`🎙️ 1080p + 디지털 원음 스트림 캡처 활성화...`);
  const stream = await getStream(page, {
    audio: true,
    video: true,
    mimeType: 'video/webm;codecs=vp8,opus'
  });
  stream.pipe(fileStream);

  // 3) 녹화 시작 후 1초 대기 후 전체 자동 방송(Auto Broadcast) 시작
  await new Promise(r => setTimeout(r, 1000));
  console.log(`▶️ 전체 자동 방송(Full Auto Broadcast) 시작 트리거...`);
  await page.evaluate(() => {
    // 풀스크린 방송 시작 버튼 클릭
    const btn = document.querySelector('.rem-primary') || document.querySelector('.kf-btn-broadcast');
    if (btn) btn.click();
  });

  // 4) 완주 상태 모니터링 (Intro -> 8 Scenes -> Outro)
  console.log(`⏳ 자동 방송 진행 중... (약 3분 30초 소요)`);
  const startTime = Date.now();
  const maxWaitMs = 6 * 60 * 1000;
  let finished = false;

  while (Date.now() - startTime < maxWaitMs) {
    await new Promise(r => setTimeout(r, 3500));

    const status = await page.evaluate(() => {
      const text = (document.body.innerText || '').toLowerCase();
      const isOutro = text.includes('mission complete') || text.includes('see you in the next video') || text.includes('미션 완료');
      const remBtnText = document.querySelector('.rem-primary')?.innerText || '';
      const isAutoStopped = remBtnText.includes('Start Full Auto') || remBtnText.includes('방송 시작');
      const stepHeader = document.querySelector('.kf-step-header')?.innerText || '';
      return { isOutro, isAutoStopped, stepHeader };
    });

    if (status.stepHeader) {
      process.stdout.write(`\r   [진행 상황] ${status.stepHeader.slice(0, 50)}...`);
    }

    if (status.isOutro) {
      console.log(`\n🎉 [완주 감지] 아웃트로 화면 도달! 마지막 여운 6초 녹화 후 종료...`);
      await new Promise(r => setTimeout(r, 6000));
      finished = true;
      break;
    }
  }

  if (!finished) {
    console.log(`\n⚠️ 최대 녹화 대기 시간 초과로 마감합니다.`);
  }

  // 5) 스트림 정리 및 브라우저 종료
  console.log(`⏹️ 녹화 스트림 마감 및 브라우저 종료...`);
  await stream.destroy();
  fileStream.close();
  await new Promise(r => setTimeout(r, 1000));
  await browser.close();
  try {
    const server = await wss;
    if (server) server.close();
  } catch (e) {}

  // 6) FFmpeg 초고속 H.264 + AAC MP4 변환
  console.log(`🔄 [FFmpeg 인코딩] WebM -> 고화질 H.264 MP4 변환 중...`);
  const remuxCmd = `"${ffmpegPath}" -y -i "${rawWebmPath}" -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k "${finalMp4Path}"`;
  execSync(remuxCmd, { stdio: 'inherit' });

  const mp4SizeMb = (fs.statSync(finalMp4Path).size / (1024 * 1024)).toFixed(2);
  console.log(`✅ [녹화 완성] 파일: ${finalMp4Path} (${mp4SizeMb} MB)`);

  // 7) YouTube 자동 업로드 실행
  console.log(`\n🚀 [유투브 업로드 시작] upload_to_youtube.py 실행...`);
  const pythonBin = path.resolve('/Users/jsoftware/.gemini/antigravity/brain/40d841bc-823c-4414-88bf-2fa32d9374cf/scratch/venv/bin/python');
  const uploaderScript = path.resolve(ROOT_DIR, 'scripts/upload_to_youtube.py');

  const uploadCmd = `"${pythonBin}" "${uploaderScript}" "${epId}" --video "${finalMp4Path}"`;
  execSync(uploadCmd, { stdio: 'inherit' });

  console.log(`\n🎉 [100% 무인 완료] ${epId} 녹화 및 유투브 업로드 전과정 완료!\n`);
}

const target = process.argv[2] || 'tteokbokki';
recordAndUploadEpisode(target).catch(err => {
  console.error('\n❌ 무인 자동화 오류 발생:', err);
  process.exit(1);
});
