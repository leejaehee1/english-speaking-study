/**
 * SoundBlock K-Cooking 무인 자동 녹화 스크립트 (Playwright 기반)
 * 
 * 사용법:
 *   1. npm i -D playwright
 *   2. npx playwright install chromium
 *   3. node scripts/record_episode.js [epId]
 *      예: node scripts/record_episode.js samgyetang
 *          node scripts/record_episode.js all
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.resolve(__dirname, '../recordings');
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function recordEpisode(epId = 'kimchi-stew') {
  console.log(`\n========================================`);
  console.log(`🎬 녹화 시작: ${epId}`);
  console.log(`========================================`);

  const browser = await chromium.launch({
    headless: false, // 브라우저 창 렌더링 (백그라운드 headless: true 가능)
    args: [
      '--autoplay-policy=no-user-gesture-required',
      '--start-maximized',
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

  // 1) 로컬 개발 서버 또는 배포 URL 접속
  const targetUrl = `http://localhost:5173/english-speaking-study/kfood/`;
  console.log(`🌐 페이지 접속 중: ${targetUrl}`);
  await page.goto(targetUrl, { waitUntil: 'networkidle' });

  // 2) 에피소드 선택 (드롭다운 변경)
  console.log(`🎯 에피소드 선택 중: ${epId}`);
  await page.selectOption('.kf-ep-select', epId);
  await page.waitForTimeout(1000);

  // 3) 전체 화면 모드 진입 (웹 풀스크린 토글)
  const fullscreenBtn = await page.$('.btn-rec-opt:has-text("전체 화면"), .btn-fs-toggle');
  if (fullscreenBtn) {
    await fullscreenBtn.click();
    await page.waitForTimeout(500);
  }

  // 4) 자동 쇼 (Auto Show) 재생 시작
  console.log(`▶️ 자동 재생(Auto Show) 시작...`);
  const playBtn = await page.$('.btn-control.btn-play, button:has-text("자동 재생")');
  if (playBtn) {
    await playBtn.click();
  }

  // 5) 에피소드 완주 대기 (약 3분~4분, 아웃트로 완료 시까지)
  // slideCursor가 마지막 씬을 지나 완료될 때까지 대기
  console.log(`⏳ 녹화 진행 중... (약 3~4분 소요)`);
  
  // 아웃트로 슬라이드가 끝날 때까지 주기적으로 체크 (최대 5분)
  const maxWaitMs = 5 * 60 * 1000;
  const startTime = Date.now();
  
  while (Date.now() - startTime < maxWaitMs) {
    await page.waitForTimeout(3000);
    const isOutroDone = await page.evaluate(() => {
      // 컴포넌트 내부 상태 확인 또는 완료 텍스트 감지
      const outroText = document.body.innerText;
      return outroText.includes('Mission complete') || outroText.includes('See you in the next video');
    });

    if (isOutroDone) {
      console.log(`🎉 에피소드 완주 감지! 5초 추가 버퍼 후 녹화 종료`);
      await page.waitForTimeout(5000);
      break;
    }
  }

  // 6) 컨텍스트 및 브라우저 닫기 (비디오 파일 저장)
  await context.close();
  await browser.close();

  // 방금 저장된 비디오 파일명 조회
  const videoFiles = fs.readdirSync(OUTPUT_DIR).filter(f => f.endsWith('.webm'));
  videoFiles.sort((a, b) => fs.statSync(path.join(OUTPUT_DIR, b)).mtimeMs - fs.statSync(path.join(OUTPUT_DIR, a)).mtimeMs);

  if (videoFiles.length > 0) {
    const latestVideo = path.join(OUTPUT_DIR, videoFiles[0]);
    const finalName = path.join(OUTPUT_DIR, `${epId}.webm`);
    fs.renameSync(latestVideo, finalName);
    console.log(`✅ 비디오 파일 저장 완료: ${finalName}`);
  }
}

const targetEp = process.argv[2] || 'kimchi-stew';
recordEpisode(targetEp).catch(err => {
  console.error('❌ 녹화 오류:', err);
  process.exit(1);
});
