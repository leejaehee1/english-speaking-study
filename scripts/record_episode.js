/**
 * SoundBlock K-Cooking 무인 자동 녹화 스크립트 (Playwright 기반, ESM)
 */

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OUTPUT_DIR = path.resolve(__dirname, '../recordings');
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function recordEpisode(epId = 'kimchi-stew') {
  console.log(`\n========================================`);
  console.log(`🎬 녹화 시작: ${epId}`);
  console.log(`========================================`);

  const browser = await chromium.launch({
    headless: true, // 무인 백그라운드 녹화
    args: [
      '--autoplay-policy=no-user-gesture-required',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1920,1080'
    ]
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: OUTPUT_DIR,
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();

  // 1) 로컬 개발 서버 접속
  const targetUrl = `http://localhost:5173/english-speaking-study/kfood/`;
  console.log(`🌐 페이지 접속 중: ${targetUrl}`);
  await page.goto(targetUrl, { waitUntil: 'networkidle' });

  // 2) 에피소드 선택 (버튼 클릭)
  console.log(`🎯 에피소드 선택 중: ${epId}`);
  const selected = await page.evaluate((targetId) => {
    // 모든 .kf-ep-btn 버튼 중 현재 에피소드에 해당하는 버튼 클릭
    const btns = Array.from(document.querySelectorAll('.kf-ep-btn'));
    // KFoodYoutubeStudio.vue 의 episodes 목록 중 id 매칭
    for (const b of btns) {
      if (b.__vnode?.key === targetId || b.innerText.toLowerCase().includes(targetId.replace('-', ' '))) {
        b.click();
        return true;
      }
    }
    // 첫 번째 에피소드(kimchi-stew)인 경우 기본 선택되어 있음
    if (btns.length > 0) {
      const idxMap = {
        'kimchi-stew': 0,
        'kimchi-fried-rice': 1,
        'korean-ramen': 2,
        'chuncheon-dakgalbi': 3,
        'tteokbokki': 4
      };
      if (targetId in idxMap) {
        btns[idxMap[targetId]].click();
        return true;
      }
    }
    return false;
  }, epId);

  await page.waitForTimeout(1000);

  // 3) 전체 화면 모드 진입
  console.log(`🖥️ 1080p 풀스크린 스튜디오 모드 전환...`);
  const fsBtn = await page.$('.kf-fullscreen-btn');
  if (fsBtn) {
    await fsBtn.click();
    await page.waitForTimeout(500);
  }

  // 4) 자동 쇼 (Auto Broadcast) 시작
  console.log(`▶️ 자동 쇼(Full Auto Broadcast) 시작...`);
  const broadcastBtn = await page.$('.kf-btn-broadcast, .rem-primary');
  if (broadcastBtn) {
    await broadcastBtn.click();
  } else {
    // evaluate fallback
    await page.evaluate(() => {
      const btn = document.querySelector('.kf-btn-broadcast') || document.querySelector('.rem-primary');
      if (btn) btn.click();
    });
  }

  // 5) 에피소드 완주 대기 (약 3분~4분)
  console.log(`⏳ 녹화 진행 중... (약 3분 30초 소요 예정)`);
  
  const maxWaitMs = 5 * 60 * 1000;
  const startTime = Date.now();
  let completed = false;

  while (Date.now() - startTime < maxWaitMs) {
    await page.waitForTimeout(4000);
    const status = await page.evaluate(() => {
      const text = document.body.innerText;
      const isOutro = text.includes('Mission complete') || text.includes('See you in the next video') || text.includes('미션 완료');
      // 현재 진행 씬 확인
      const stepHeader = document.querySelector('.kf-step-header')?.innerText || '';
      return { isOutro, stepHeader };
    });

    if (status.stepHeader) {
      process.stdout.write(`\r   [진행 현황] ${status.stepHeader.slice(0, 45)}...`);
    }

    if (status.isOutro) {
      console.log(`\n🎉 에피소드 아웃트로 완주 감지! 6초 버퍼 후 녹화 종료`);
      await page.waitForTimeout(6000);
      completed = true;
      break;
    }
  }

  if (!completed) {
    console.log(`\n⚠️ 최대 대기 시간 초과로 녹화를 마무리합니다.`);
  }

  // 6) 컨텍스트 및 브라우저 닫기 (비디오 인코딩 완료 대기)
  await context.close();
  await browser.close();

  // 저장된 비디오 파일명 확인 및 rename
  const videoFiles = fs.readdirSync(OUTPUT_DIR).filter(f => f.endsWith('.webm'));
  videoFiles.sort((a, b) => fs.statSync(path.join(OUTPUT_DIR, b)).mtimeMs - fs.statSync(path.join(OUTPUT_DIR, a)).mtimeMs);

  if (videoFiles.length > 0) {
    const latestVideo = path.join(OUTPUT_DIR, videoFiles[0]);
    const finalName = path.join(OUTPUT_DIR, `${epId}.webm`);
    if (latestVideo !== finalName) {
      if (fs.existsSync(finalName)) fs.unlinkSync(finalName);
      fs.renameSync(latestVideo, finalName);
    }
    const fileSizeMb = (fs.statSync(finalName).size / (1024 * 1024)).toFixed(2);
    console.log(`✅ 비디오 파일 저장 완료: ${finalName} (${fileSizeMb} MB)`);
  }
}

const targetEp = process.argv[2] || 'kimchi-stew';
recordEpisode(targetEp).catch(err => {
  console.error('\n❌ 녹화 오류:', err);
  process.exit(1);
});
