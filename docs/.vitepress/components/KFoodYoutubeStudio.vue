<template>
  <div
    ref="studioRoot"
    class="kf-studio-v2"
    :class="{
      'clean-record-mode': isCleanMode,
      'theater-fullscreen': isFullscreenMode
    }"
    @click.stop
    @mousemove="onMouseMoveInStudio"
  >
    <!-- 상단 컨트롤 바 (클린/전체화면 모드에서는 마우스 올릴 때만 슬라이드 다운) -->
    <div class="kf-topbar" :class="{ 'auto-hide-bar': (isCleanMode || isFullscreenMode) && !showFloatingControls }">
      <div class="kf-topbar-left">
        <a
          href="https://www.youtube.com/@SoundBlockKCooking"
          target="_blank"
          rel="noopener noreferrer"
          class="kf-studio-badge"
          title="유튜브 채널 바로가기"
        >
          ▶️ @SoundBlockKCooking V2
        </a>
        <div class="kf-ep-selector">
          <button
            v-for="ep in episodes"
            :key="ep.id"
            type="button"
            class="kf-ep-btn"
            :class="{ active: currentEpId === ep.id }"
            @click="selectEpisode(ep.id)"
          >
            {{ ep.emoji }} {{ ep.shortTitle }}
          </button>
        </div>
      </div>

      <div class="kf-topbar-right">
        <div class="kf-aspect-toggle">
          <button
            type="button"
            class="kf-mode-btn"
            :class="{ active: aspectRatio === '16:9' }"
            @click="aspectRatio = '16:9'"
          >
            📺 16:9 가로형 (Full HD)
          </button>
          <button
            type="button"
            class="kf-mode-btn"
            :class="{ active: aspectRatio === '9:16' }"
            @click="aspectRatio = '9:16'"
          >
            📱 9:16 쇼츠 세로형
          </button>
        </div>

        <button
          type="button"
          class="kf-mode-btn kf-fullscreen-btn"
          :class="{ active: isFullscreenMode }"
          @click="toggleFullscreenBroadcast"
        >
          {{ isFullscreenMode ? '✕ 전체화면 방송 종료 (ESC)' : '🖥️ 1080p 풀스크린 방송 모드' }}
        </button>
      </div>
    </div>

    <!-- ==========================================================
         메인 16:9 / 9:16 방송 캔버스 (Full-Bleed Broadcast Screen)
         ========================================================== -->
    <div class="kf-canvas-wrapper" :class="aspectRatio === '9:16' ? 'is-shorts' : 'is-wide'">
      <div class="kf-broadcast-screen" :class="aspectRatio === '9:16' ? 'screen-shorts' : 'screen-wide'">
        <!-- ----------------------------------------------------
             CASE A: INTRO 슬라이드 (오프닝 훅 화면)
             ---------------------------------------------------- -->
        <div v-if="slideCursor === -1" class="kf-special-slide intro-slide">
          <img
            :src="withBase('/images/kfood/ep1-thumb.jpg')"
            alt="Episode Intro Background"
            class="kf-bg-full ken-burns"
          />
          <div class="kf-special-backdrop"></div>

          <div class="kf-intro-content">
            <div class="kf-intro-top-pill">
              <img :src="withBase('/images/kfood/channel-logo.jpg')" alt="Logo" class="kf-mini-logo" />
              <span>소리블록 K-쿠킹 · SoundBlock K-Cooking</span>
            </div>

            <div class="kf-intro-ep-badge">{{ currentEpisode.epNumber }} · K-FOOD SPEAKING RECIPE</div>
            <h2 class="kf-intro-title">{{ currentEpisode.title }}</h2>
            <p class="kf-intro-sub">
              단어 하나씩 외우지 마세요! 레고처럼 <strong>딱 3개의 소리 블록</strong>만 조립하면 입이 트입니다.
            </p>

            <div class="kf-intro-formula">
              <span class="f-pill bb">① 시작 블록 (I'm gonna / You have to)</span>
              <span class="f-plus">+</span>
              <span class="f-pill core">② 요리 코어 블록 (make Kimchi stew)</span>
              <span class="f-plus">+</span>
              <span class="f-pill db">③ 디테일 블록 (today)</span>
            </div>

            <div class="kf-intro-cta" @click="startEpisodeFromBeginning">
              ▶️ 지금 바로 소리 내어 시작해 볼까요? (Let's get cooking!)
            </div>
          </div>
        </div>

        <!-- ----------------------------------------------------
             CASE B: 본편 요리 장면 (Scene 1 ~ Scene N) — 풀블리드 오버레이
             ---------------------------------------------------- -->
        <div v-else-if="slideCursor >= 0 && slideCursor < currentEpisode.scenes.length" class="kf-main-scene">
          <!-- 1) 100% 풀블리드 배경 이미지 / 일러스트 -->
          <template v-if="activeSceneImage">
            <img
              :key="sceneKey"
              :src="activeSceneImage"
              :alt="currentScene.stepTitle"
              class="kf-bg-full ken-burns"
            />
            <div class="kf-scrim-gradient"></div>
          </template>
          <template v-else>
            <div class="kf-bg-fallback" :style="{ background: currentScene.bgGradient }">
              <div class="kf-fallback-center">
                <div class="kf-fallback-emojis">{{ currentScene.visualEmojis }}</div>
                <div class="kf-fallback-action">{{ currentScene.actionNote }}</div>
              </div>
            </div>
            <div class="kf-scrim-gradient"></div>
          </template>

          <!-- 2) 상단 HUD 바 (채널 로고 + 장면 번호 + 진행 게이지 + 핵심 어휘 배지) -->
          <div class="kf-hud-top">
            <div class="kf-hud-left">
              <img :src="withBase('/images/kfood/channel-logo.jpg')" alt="Logo" class="kf-hud-logo" />
              <div class="kf-hud-brand">
                <span class="hud-ch-name">소리블록 K-쿠킹</span>
                <span class="hud-ep-step">{{ currentEpisode.epNumber }} · {{ currentScene.stepTitle }}</span>
              </div>
            </div>

            <div class="kf-hud-right">
              <div class="kf-hud-vocab">
                <span class="vocab-tag">KEY EXPRESSION</span>
                <strong>{{ currentScene.keyVocab }}</strong>
              </div>
            </div>
          </div>

          <!-- 상단 씬 프로그레스 도트 바 -->
          <div class="kf-hud-progress">
            <span
              class="hud-dot"
              :class="{ active: slideCursor === -1, done: slideCursor > -1 }"
              title="오프닝 인트로"
              @click="goToSlide(-1)"
            ></span>
            <span
              v-for="(sc, idx) in currentEpisode.scenes"
              :key="idx"
              class="hud-dot"
              :class="{ active: idx === slideCursor, done: idx < slideCursor }"
              :title="sc.stepTitle"
              @click="goToSlide(idx)"
            ></span>
            <span
              class="hud-dot"
              :class="{ active: slideCursor === currentEpisode.scenes.length }"
              title="전체 복습 아웃트로"
              @click="goToSlide(currentEpisode.scenes.length)"
            ></span>
          </div>

          <!-- 3) 중앙 상단: 한국어 코칭 버블 or 🎤 YOUR TURN 따라 말하기 배너 -->
          <transition name="kf-pop">
            <div v-if="isShadowingTurn" class="kf-center-turn-modal">
              <div class="turn-header">
                <span class="turn-mic-icon">🎤</span>
                <div class="turn-texts">
                  <strong>YOUR TURN! 큰 소리로 따라 말해 보세요!</strong>
                  <span>소리 블록 3개를 리듬에 맞춰 한 호흡으로 뱉어 보세요</span>
                </div>
                <span class="turn-sec-badge">{{ Math.ceil((100 - shadowingProgress) * 0.04) }}초</span>
              </div>
              <div class="turn-progress-track">
                <div class="turn-progress-bar" :style="{ width: shadowingProgress + '%' }"></div>
              </div>
            </div>

            <div v-else-if="showCoachBubble && currentScene.coachKo" class="kf-coach-banner">
              <span class="coach-icon">💡 요리 상황 코칭</span>
              <span class="coach-text">{{ currentScene.coachKo }}</span>
            </div>
          </transition>

          <!-- 4) 하단 글래스모피즘 방송 자막 독 (Broadcast Lower-Third Caption Dock) -->
          <div class="kf-lower-third">
            <!-- 소리 블록 3단 캡슐 -->
            <div class="kf-blocks-row">
              <div
                v-for="(blk, bIdx) in currentScene.blocks"
                :key="bIdx"
                class="kf-glass-block"
                :class="[blk.role, { active: activeBlockIdx === bIdx }]"
                @click="speakSingleBlock(blk.en, bIdx)"
              >
                <div class="gblk-top">
                  <span class="gblk-badge">
                    {{ blk.role === 'bb' ? '① 시작 블록' : blk.role === 'core' ? '② 코어 블록' : '③ 디테일 블록' }}
                  </span>
                  <span v-if="showPronGuide" class="gblk-pron">[{{ blk.pron }}]</span>
                </div>
                <div class="gblk-en">{{ blk.en }}</div>
              </div>
            </div>

            <!-- 완성 문장 & 한글 리듬 & 번역 바 -->
            <div class="kf-sentence-banner" @click="speakSceneSentence(1.0)">
              <div class="kf-main-en">
                <span class="play-hint-icon">🔊</span>
                {{ currentScene.fullEn }}
              </div>
              <div class="kf-sub-meta">
                <span v-if="showPronGuide" class="kf-meta-pron">
                  🗣️ <strong>{{ currentScene.fullPron }}</strong>
                </span>
                <span v-if="showKoSub" class="kf-meta-ko">
                  🇰🇷 {{ currentScene.fullKo }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- ----------------------------------------------------
             CASE C: OUTRO 슬라이드 (전체 8문장 복습 & 구독 유도)
             ---------------------------------------------------- -->
        <div v-else class="kf-special-slide outro-slide">
          <img
            :src="withBase('/images/kfood/ep1-s8.jpg')"
            alt="Episode Outro Background"
            class="kf-bg-full"
          />
          <div class="kf-special-backdrop outro-backdrop"></div>

          <div class="kf-outro-content">
            <div class="kf-outro-header">
              <span class="outro-badge">🎉 MISSION COMPLETE · 오늘의 소리 블록 총정리</span>
              <h2 class="outro-title">{{ currentEpisode.title }} 핵심 문장 복습</h2>
            </div>

            <div class="kf-review-grid">
              <div
                v-for="(sc, idx) in currentEpisode.scenes"
                :key="idx"
                class="kf-review-item"
                @click="speakText(sc.fullEn, 1.0)"
              >
                <span class="rev-num">0{{ idx + 1 }}</span>
                <div class="rev-body">
                  <div class="rev-en">{{ sc.fullEn }}</div>
                  <div class="rev-ko">{{ sc.fullKo }} · <em>({{ sc.fullPron }})</em></div>
                </div>
              </div>
            </div>

            <div class="kf-outro-footer">
              <div class="outro-cta-box">
                <img :src="withBase('/images/kfood/channel-logo.jpg')" alt="Logo" class="kf-mini-logo" />
                <div>
                  <strong>구독(Subscribe) &amp; 좋아요(Like)</strong>를 누르고 다음 한국 요리도 영어로 말해 봐요!
                  <div class="outro-handle">YouTube · @SoundBlockKCooking</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 풀스크린 방송 모드일 때 우측 상단 미니 리모컨 (마우스 움직일 때만 표시) -->
        <div
          v-if="isFullscreenMode || isCleanMode"
          class="kf-floating-remote"
          :class="{ visible: showFloatingControls }"
        >
          <button type="button" class="rem-btn" @click="prevSlide">◀ 이전</button>
          <button
            type="button"
            class="rem-btn rem-primary"
            :class="{ playing: isAutoPlaying }"
            @click="toggleAutoShow"
          >
            {{ isAutoPlaying ? '⏹️ 방송 정지' : '▶️ 전체 자동 방송 시작' }}
          </button>
          <button type="button" class="rem-btn" @click="playCurrentSlideSequence">🔁 현재 장면 재생</button>
          <button type="button" class="rem-btn" @click="nextSlide">다음 ▶</button>
          <button v-if="isFullscreenMode" type="button" class="rem-btn rem-exit" @click="exitFullscreen">
            ✕ 나가기
          </button>
        </div>
      </div>
    </div>

    <!-- 하단 플레이어 & 녹음 컨트롤 바 -->
    <div v-if="!isFullscreenMode" class="kf-controls-panel">
      <div class="kf-nav-group">
        <button type="button" class="kf-ctrl-btn" @click="goToSlide(-1)">🎬 인트로</button>
        <button type="button" class="kf-ctrl-btn" @click="prevSlide">◀ 이전</button>

        <button
          type="button"
          class="kf-ctrl-btn kf-btn-broadcast"
          :class="{ 'kf-btn-playing': isAutoPlaying }"
          @click="toggleAutoShow"
        >
          {{ isAutoPlaying ? '⏹️ 자동 방송 중지' : '▶️ 전체 장면 자동 방송 (인트로~아웃트로 원테이크 녹화)' }}
        </button>

        <button type="button" class="kf-ctrl-btn kf-btn-step" @click="playCurrentSlideSequence">
          🔁 이 장면 풀 시퀀스 재생 (코칭→블록→따라말하기)
        </button>

        <button type="button" class="kf-ctrl-btn kf-btn-primary" @click="speakSceneSentence(1.0)">
          🔊 영어 문장만 (1.0x)
        </button>

        <button type="button" class="kf-ctrl-btn" @click="nextSlide">다음 ▶</button>
        <button type="button" class="kf-ctrl-btn" @click="goToSlide(currentEpisode.scenes.length)">
          🏁 아웃트로
        </button>
      </div>

      <!-- 방송 연출 세부 옵션 (효과음, 한국어 코칭 음성, 따라 말하기 타이머, 사진 업로드) -->
      <div v-if="!isCleanMode" class="kf-extra-tools">
        <div class="kf-custom-tools">
          <label class="kf-chk">
            <input v-model="enableKoreanCoachVoice" type="checkbox" /> 🇰🇷 한국어 상황 코칭 음성 켜기
          </label>
          <label class="kf-chk">
            <input v-model="enableSoundEffects" type="checkbox" /> 🔔 방송 효과음(딩동·전환음) 켜기
          </label>
          <label class="kf-chk">
            <input v-model="includeShadowingPause" type="checkbox" /> 🎤 따라 말하기(4초) 구간 포함
          </label>
          <label class="kf-chk">
            <input v-model="showCoachBubble" type="checkbox" /> 💡 상단 코칭 배너 표시
          </label>
          <label class="kf-chk">
            <input v-model="showPronGuide" type="checkbox" /> 한글 발음 표시
          </label>
        </div>

        <div class="kf-voice-recorder">
          <label v-if="slideCursor >= 0 && slideCursor < currentEpisode.scenes.length" class="kf-upload-label">
            📷 내 요리 사진 넣기
            <input type="file" accept="image/*" hidden @change="onUploadSceneImage" />
          </label>
          <button
            type="button"
            class="kf-ctrl-btn"
            :class="{ 'kf-btn-rec': isRecording }"
            @click="toggleRecording"
          >
            {{ isRecording ? '⏹️ 녹음 완료' : '🎙️ 내 목소리 테스트 녹음' }}
          </button>
          <audio
            v-if="recordedAudioMap[sceneKey]"
            :src="recordedAudioMap[sceneKey]"
            controls
            class="kf-audio-player"
          ></audio>
        </div>
      </div>

      <!-- 유튜브 업로드 패키지 (제목·설명·자막 원클릭 복사) -->
      <div v-if="!isCleanMode" class="kf-yt-package">
        <div class="kf-yt-package-header" @click="showYtMeta = !showYtMeta">
          <span>📋 <strong>{{ currentEpisode.title }}</strong> · 유튜브 업로드용 제목·설명·태그·자막 패키지</span>
          <span class="kf-toggle-arrow">{{ showYtMeta ? '▲ 접기' : '▼ 펼치기' }}</span>
        </div>
        <div v-if="showYtMeta" class="kf-yt-package-body">
          <div class="kf-meta-row">
            <strong>추천 영상 제목:</strong>
            <code>{{ currentEpisode.ytTitle }}</code>
          </div>
          <div class="kf-meta-row">
            <strong>썸네일 문구:</strong>
            <code>{{ currentEpisode.thumbnailText }}</code>
          </div>
          <div class="kf-meta-row">
            <strong>전체 대본 &amp; 설명란 복사:</strong>
            <button type="button" class="kf-ctrl-btn-sm" @click="copyEpisodeScript">
              {{ copySuccess ? '✅ 복사 완료!' : '📄 전체 한/영 대본 & 태그 복사하기' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { withBase } from 'vitepress'

interface SoundBlockPiece {
  role: 'bb' | 'core' | 'db'
  en: string
  pron: string
}

interface CookingScene {
  stepTitle: string
  visualEmojis: string
  imagePath?: string
  actionNote: string
  coachKo: string
  keyVocab: string
  bgGradient: string
  blocks: SoundBlockPiece[]
  fullEn: string
  fullPron: string
  fullKo: string
}

interface CookingEpisode {
  id: string
  epNumber: string
  emoji: string
  shortTitle: string
  title: string
  ytTitle: string
  thumbnailText: string
  introNarrationKo: string
  outroNarrationKo: string
  scenes: CookingScene[]
}

const studioRoot = ref<HTMLElement | null>(null)
const aspectRatio = ref<'16:9' | '9:16'>('16:9')
const isCleanMode = ref(false)
const isFullscreenMode = ref(false)
const showFloatingControls = ref(true)

const enableKoreanCoachVoice = ref(true)
const enableSoundEffects = ref(true)
const includeShadowingPause = ref(true)
const showCoachBubble = ref(true)
const showPronGuide = ref(true)
const showKoSub = ref(true)
const showYtMeta = ref(false)
const copySuccess = ref(false)

const isShadowingTurn = ref(false)
const shadowingProgress = ref(0)

// slideCursor: -1 = INTRO, 0..(scenes.length-1) = SCENES, scenes.length = OUTRO
const slideCursor = ref(0)

const episodes: CookingEpisode[] = [
  // ==========================================
  // EP 1. 김치찌개 (Kimchi Stew) - 8 Scenes with High-Res Illustrations
  // ==========================================
  {
    id: 'kimchi-stew',
    epNumber: 'EP.01',
    emoji: '🍲',
    shortTitle: '1화 · 김치찌개',
    title: '중학교 단어로 김치찌개 끓이기 (Kimchi Stew)',
    ytTitle: '[소리블록 요리영어 #1] 중학교 단어로 김치찌개 끓이기 🍲 | How to Make Kimchi Stew in Easy English',
    thumbnailText: '"김치찌개 끓일게!" → [I\'m gonna] + [make Kimchi stew]',
    introNarrationKo: '안녕하세요, 소리블록 케이쿠킹입니다! 오늘은 한국인의 소울푸드 김치찌개 끓이는 법을 딱 세 개의 영어 소리 블록으로 조립해 말해 볼게요.',
    outroNarrationKo: '오늘 배운 김치찌개 소리 블록 여덟 문장, 입에 착 붙으셨나요? 구독과 좋아요를 누르고 다음 요리도 함께 입으로 뱉어 봐요!',
    scenes: [
      {
        stepTitle: 'SCENE 1 · 오늘의 요리 소개',
        visualEmojis: '👨‍🍳 🍲 🇰🇷',
        imagePath: '/images/kfood/ep1-s1.jpg',
        actionNote: '앞치마를 입고 부엌에서 밝게 인사하는 오프닝',
        coachKo: '첫 번째 장면입니다. "오늘 김치찌개 끓일 거야!"라고 말할 때, "~할 거야"는 I\'m gonna, "김치찌개를 만들다"는 make Kimchi stew를 붙여 보세요.',
        keyVocab: 'Kimchi stew (김치찌개)',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'make Kimchi stew', pron: '메익 김치 스튜' },
          { role: 'db', en: 'today.', pron: '투데이' }
        ],
        fullEn: "I'm gonna make Kimchi stew today.",
        fullPron: '암거너 + 메익 김치 스튜 + 투데이',
        fullKo: '오늘 저는 김치찌개를 끓일 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · 신김치 비법 공개',
        visualEmojis: '🥬 ✨ 😋',
        imagePath: '/images/kfood/ep1-s2.jpg',
        actionNote: '잘 익은 신김치를 보여주며 핵심 비법 설명',
        coachKo: '김치찌개의 생명은 잘 익은 신김치죠! "꼭 ~해야 해"는 You have to, "신김치를 쓰다"는 use sour kimchi입니다.',
        keyVocab: 'sour kimchi (신김치)',
        bgGradient: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해프터' },
          { role: 'core', en: 'use sour kimchi', pron: '유즈 사워 김치' },
          { role: 'db', en: 'for deep flavor.', pron: '포 딥 플레이버' }
        ],
        fullEn: 'You have to use sour kimchi for deep flavor.',
        fullPron: '유 해프터 + 유즈 사워 김치 + 포 딥 플레이버',
        fullKo: '깊은 맛을 내려면 꼭 신김치를 써야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · 김치와 돼지고기 썰기',
        visualEmojis: '🔪 🥩 🥬',
        imagePath: '/images/kfood/ep1-s3.jpg',
        actionNote: '도마 위에서 김치와 돼지고기를 한 입 크기로 큼직하게 썰기',
        coachKo: '이제 재료를 큼직하게 썰어 볼까요? 큼직하게 썰다는 chop, "한 입 크기로"는 into bite-sized pieces라고 표현합니다.',
        keyVocab: 'chop / bite-sized pieces',
        bgGradient: 'linear-gradient(135deg, #431407 0%, #7c2d12 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'chop the pork and kimchi', pron: '찹 더 포크 앤 김치' },
          { role: 'db', en: 'into bite-sized pieces.', pron: '인투 바잇-사이즈드 피시즈' }
        ],
        fullEn: "I'm gonna chop the pork and kimchi into bite-sized pieces.",
        fullPron: '암거너 + 찹 더 포크 앤 김치 + 인투 바잇-사이즈드 피시즈',
        fullKo: '돼지고기와 김치를 한 입 크기로 썰어 줄게요.'
      },
      {
        stepTitle: 'SCENE 4 · 두부와 대파 손질하기',
        visualEmojis: '⬜ 🌱 🔪',
        imagePath: '/images/kfood/ep1-s4.jpg',
        actionNote: '두부는 납작하게 썰고(slice), 대파는 송송 썰어 준비',
        coachKo: '두부처럼 납작하게 썰 때는 slice를 씁니다. "내가 ~할게"라는 시작 블록 I\'ll 뒤에 slice the tofu를 붙여 보세요!',
        keyVocab: 'slice the tofu (두부를 썰다)',
        bgGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을(올)' },
          { role: 'core', en: 'slice the tofu', pron: '슬라이스 더 토푸' },
          { role: 'db', en: 'and chop the green onion.', pron: '앤 찹 더 그린 어니언' }
        ],
        fullEn: "I'll slice the tofu and chop the green onion.",
        fullPron: '아을 + 슬라이스 더 토푸 + 앤 찹 더 그린 어니언',
        fullKo: '제가 두부는 납작하게 썰고 대파도 썰어 둘게요.'
      },
      {
        stepTitle: 'SCENE 5 · 냄비에 고기와 김치 볶기',
        visualEmojis: '🍲 🔥 🧄',
        imagePath: '/images/kfood/ep1-s5.jpg',
        actionNote: '달궈진 냄비에 돼지고기, 김치, 다진 마늘을 넣고 지글지글 볶기',
        coachKo: '다진 마늘을 넣고 고기와 김치를 먼저 볶아 줘야 국물이 진해지죠! "같이 볶다"는 fry them together입니다.',
        keyVocab: 'fry them together (함께 볶다)',
        bgGradient: 'linear-gradient(135deg, #422006 0%, #713f12 100%)',
        blocks: [
          { role: 'bb', en: 'We have to', pron: '위 해프터' },
          { role: 'core', en: 'fry them together', pron: '프라이 뎀 투게더' },
          { role: 'db', en: 'with minced garlic.', pron: '위드 민스트 갈릭' }
        ],
        fullEn: 'We have to fry them together with minced garlic.',
        fullPron: '위 해프터 + 프라이 뎀 투게더 + 위드 민스트 갈릭',
        fullKo: '다진 마늘을 넣고 재료들을 함께 볶아 줘야 해요.'
      },
      {
        stepTitle: 'SCENE 6 · 물과 김치 국물 붓기',
        visualEmojis: '💧 🥣 🌶️',
        imagePath: '/images/kfood/ep1-s6.jpg',
        actionNote: '물을 붓고 감칠맛의 핵심인 김치 국물(kimchi juice) 한 국자 추가!',
        coachKo: '물을 붓고 빠질 수 없는 비법, 김치 국물을 넣을 차례입니다! 김치 국물은 영어로 귀엽게 kimchi juice라고 부릅니다.',
        keyVocab: 'kimchi juice (김치 국물)',
        bgGradient: 'linear-gradient(135deg, #172554 0%, #1e3a8a 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'pour some water', pron: '포어 썸 워러' },
          { role: 'db', en: 'and add the kimchi juice.', pron: '앤 애드 더 김치 주스' }
        ],
        fullEn: "I'm gonna pour some water and add the kimchi juice.",
        fullPron: '암거너 + 포어 썸 워러 + 앤 애드 더 김치 주스',
        fullKo: '물을 좀 붓고 김치 국물도 넣어 줄게요.'
      },
      {
        stepTitle: 'SCENE 7 · 팔팔 끓인 뒤 푹 끓이기',
        visualEmojis: '♨️ 🍲 ⏲️',
        imagePath: '/images/kfood/ep1-s7.jpg',
        actionNote: '센 불에 팔팔 끓인 뒤 중약불로 줄여 10분간 뭉근히 끓이기',
        coachKo: '센 불에 팔팔 끓이다는 bring it to the boil, 불을 줄여 뭉근히 푹 끓게 두다는 let it simmer입니다!',
        keyVocab: 'bring it to the boil / simmer',
        bgGradient: 'linear-gradient(135deg, #4c0519 0%, #881337 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '워거너' },
          { role: 'core', en: 'bring it to the boil', pron: '브링 잇 투 더 보일' },
          { role: 'db', en: 'and let it simmer.', pron: '앤 레릿 시머' }
        ],
        fullEn: "We're gonna bring it to the boil and let it simmer.",
        fullPron: '워거너 + 브링 잇 투 더 보일 + 앤 레릿 시머',
        fullKo: '팔팔 끓인 다음에 푹(뭉근히) 끓게 둘 거예요.'
      },
      {
        stepTitle: 'SCENE 8 · 국물 맛보기 & 시식',
        visualEmojis: '🥄 🍚 😍',
        imagePath: '/images/kfood/ep1-s8.jpg',
        actionNote: '국물 한 모금(take a sip) 맛보고 따뜻한 흰쌀밥과 한 입!',
        coachKo: '드디어 완성입니다! 뜨거운 국물을 후후 불어 한 모금 맛볼 때는 take a sip 소리 블록을 씁니다.',
        keyVocab: 'take a sip (한 모금 맛보다)',
        bgGradient: 'linear-gradient(135deg, #3b0764 0%, #581c87 100%)',
        blocks: [
          { role: 'bb', en: 'I wanna', pron: '아이 워너' },
          { role: 'core', en: 'take a sip', pron: '테이커 씹' },
          { role: 'db', en: 'right now. Wow, so good!', pron: '롸잇 나우. 와우 쏘 굿!' }
        ],
        fullEn: 'I wanna take a sip right now. Wow, so good!',
        fullPron: '아이 워너 + 테이커 씹 + 롸잇 나우. 와우, 쏘 굿!',
        fullKo: '지금 당장 국물 한 모금 마셔 보고 싶네요. 와, 진짜 맛있어요!'
      }
    ]
  },

  // ==========================================
  // EP 2. 김치볶음밥 (Kimchi Fried Rice)
  // ==========================================
  {
    id: 'kimchi-fried-rice',
    epNumber: 'EP.02',
    emoji: '🍳',
    shortTitle: '2화 · 김치볶음밥',
    title: '5분 완성 김치볶음밥 & 계란프라이 만들기 (Kimchi Fried Rice)',
    ytTitle: '[소리블록 요리영어 #2] 5분 완성 김치볶음밥 영어로 설명하기 🍳 | Kimchi Fried Rice in Easy English',
    thumbnailText: '"계란프라이 올릴게!" → [I\'ll] + [put a fried egg] + [on top]',
    introNarrationKo: '안녕하세요, 소리블록 케이쿠킹입니다! 오늘은 5분 만에 뚝딱 만드는 김치볶음밥과 반숙 계란프라이를 소리 블록으로 말해 볼게요.',
    outroNarrationKo: '오늘 배운 김치볶음밥 소리 블록 여섯 문장도 정말 쉽죠? 구독과 좋아요 누르고 다음 영상에서 또 만나요!',
    scenes: [
      {
        stepTitle: 'SCENE 1 · 김치볶음밥 시작하기',
        visualEmojis: '🍚 🥬 🍳',
        imagePath: '/images/kfood/ep1-s1.jpg',
        actionNote: '찬밥과 잘게 썬 김치를 준비하며 인사',
        coachKo: '점심 메뉴로 김치볶음밥을 만들 때, I\'m gonna 뒤에 make Kimchi fried rice를 붙여 보세요!',
        keyVocab: 'Kimchi fried rice (김치볶음밥)',
        bgGradient: 'linear-gradient(135deg, #431407 0%, #7c2d12 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'make Kimchi fried rice', pron: '메익 김치 프라이드 라이스' },
          { role: 'db', en: 'for lunch.', pron: '포 런치' }
        ],
        fullEn: "I'm gonna make Kimchi fried rice for lunch.",
        fullPron: '암거너 + 메익 김치 프라이드 라이스 + 포 런치',
        fullKo: '점심으로 김치볶음밥을 만들 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · 김치와 베이컨 잘게 썰기',
        visualEmojis: '🔪 🥓 🥬',
        imagePath: '/images/kfood/ep1-s3.jpg',
        actionNote: '볶음밥용으로 김치와 베이컨(또는 스팸)을 잘게 다지듯 썰기',
        coachKo: '볶음밥용 김치는 잘게 썰어야 맛있죠! "잘게 썰다"는 chop finely라고 표현합니다.',
        keyVocab: 'chop finely (잘게 썰다)',
        bgGradient: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해프터' },
          { role: 'core', en: 'chop the kimchi finely', pron: '찹 더 김치 파인리' },
          { role: 'db', en: 'with some bacon.', pron: '위드 썸 베이컨' }
        ],
        fullEn: 'You have to chop the kimchi finely with some bacon.',
        fullPron: '유 해프터 + 찹 더 김치 파인리 + 위드 썸 베이컨',
        fullKo: '베이컨과 함께 김치를 잘게 썰어 줘야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · 고추장 한 스푼 넣고 볶기',
        visualEmojis: '🍳 🔥 🌶️',
        imagePath: '/images/kfood/ep1-s5.jpg',
        actionNote: '팬에 김치와 고추장/간장을 넣고 센 불에 달달 볶기',
        coachKo: '주걱으로 저어가며 센 불에 달달 볶는 건 stir-fry라고 합니다!',
        keyVocab: 'stir-fry (센 불에 저으며 볶다)',
        bgGradient: 'linear-gradient(135deg, #422006 0%, #713f12 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '워거너' },
          { role: 'core', en: 'stir-fry the kimchi', pron: '스터-프라이 더 김치' },
          { role: 'db', en: 'with chili paste.', pron: '위드 칠리 페이스트' }
        ],
        fullEn: "We're gonna stir-fry the kimchi with chili paste.",
        fullPron: '워거너 + 스터-프라이 더 김치 + 위드 칠리 페이스트',
        fullKo: '고추장을 넣고 김치를 센 불에 볶을 거예요.'
      },
      {
        stepTitle: 'SCENE 4 · 밥 넣고 참기름 두르기',
        visualEmojis: '🍚 🫗 ✨',
        imagePath: '/images/kfood/ep1-s2.jpg',
        actionNote: '밥을 넣고 골고루 섞은 뒤 마지막에 고소한 참기름 한 바퀴!',
        coachKo: '밥을 넣고 비빈 뒤 고소한 참기름, sesame oil을 한 바퀴 둘러 줍니다!',
        keyVocab: 'sesame oil (참기름)',
        bgGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'mix in the rice', pron: '믹스 인 더 라이스' },
          { role: 'db', en: 'and add sesame oil.', pron: '앤 애드 세서미 오일' }
        ],
        fullEn: "I'll mix in the rice and add sesame oil.",
        fullPron: '아을 + 믹스 인 더 라이스 + 앤 애드 세서미 오일',
        fullKo: '밥을 넣고 섞은 다음 참기름을 두를게요.'
      },
      {
        stepTitle: 'SCENE 5 · 반숙 계란프라이 올리기',
        visualEmojis: '🥚 🍳 👑',
        imagePath: '/images/kfood/ep1-s7.jpg',
        actionNote: '노른자가 살아 있는 반숙 계란프라이를 맨 위에 얹기',
        coachKo: '김치볶음밥의 화룡점정! 계란프라이를 맨 위에 딱 올릴 때는 put a fried egg right on top!',
        keyVocab: 'put a fried egg right on top',
        bgGradient: 'linear-gradient(135deg, #172554 0%, #1e3a8a 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'put a fried egg', pron: '풋 어 프라이드 에그' },
          { role: 'db', en: 'right on top.', pron: '롸잇 온 탑' }
        ],
        fullEn: "I'm gonna put a fried egg right on top.",
        fullPron: '암거너 + 풋 어 프라이드 에그 + 롸잇 온 탑',
        fullKo: '맨 위에 계란프라이를 딱 얹어 줄 거예요.'
      },
      {
        stepTitle: 'SCENE 6 · 노른자 터뜨려 한 입 먹기',
        visualEmojis: '🥄 😋 👍',
        imagePath: '/images/kfood/ep1-s8.jpg',
        actionNote: '숟가락으로 노른자를 톡 터뜨려 밥과 함께 한 입!',
        coachKo: '음식을 한 입 크게 먹어 볼래? 하고 물어볼 때는 Do you wanna take a bite?를 씁니다.',
        keyVocab: 'take a bite (한 입 먹다)',
        bgGradient: 'linear-gradient(135deg, #3b0764 0%, #581c87 100%)',
        blocks: [
          { role: 'bb', en: 'Do you wanna', pron: '두유워너' },
          { role: 'core', en: 'take a bite', pron: '테이커 바이트' },
          { role: 'db', en: 'right now?', pron: '롸잇 나우?' }
        ],
        fullEn: 'Do you wanna take a bite right now?',
        fullPron: '두유워너 + 테이커 바이트 + 롸잇 나우?',
        fullKo: '지금 당장 한 입 먹어 볼래요?'
      }
    ]
  },

  // ==========================================
  // EP 3. K-라면 맛있게 끓이기 (Korean Ramen)
  // ==========================================
  {
    id: 'korean-ramen',
    epNumber: 'EP.03',
    emoji: '🍜',
    shortTitle: '3화 · K-라면 끓이기',
    title: '영어로 K-라면 꼬들꼬들하게 끓이기 (Korean Instant Noodles)',
    ytTitle: '[소리블록 요리영어 #3] 외국인 친구에게 K-라면 끓이는 법 영어로 말하기 🍜 | How to Cook Korean Ramen',
    thumbnailText: '"스프부터 넣어야 해!" → [You have to] + [put the soup base first]',
    introNarrationKo: '안녕하세요, 소리블록 케이쿠킹입니다! 오늘은 전 세계가 사랑하는 한국 라면 맛있게 끓이는 법을 영어 소리 블록으로 배워 볼게요.',
    outroNarrationKo: '라면 끓이면서 혼자 영어로 중얼거려 보면 절대 안 까먹습니다! 구독과 좋아요 부탁드려요!',
    scenes: [
      {
        stepTitle: 'SCENE 1 · 출출한 밤, 라면 끓이기',
        visualEmojis: '🌙 🍜 🔥',
        imagePath: '/images/kfood/ep1-s1.jpg',
        actionNote: '냄비와 라면 한 봉지를 들고 시작',
        coachKo: '오늘 밤 라면 끓여 먹을 거야! I\'m gonna + make Korean ramen + tonight으로 가볍게 시작해 볼까요?',
        keyVocab: 'make Korean ramen (라면 끓이다)',
        bgGradient: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'make Korean ramen', pron: '메익 코리안 라면' },
          { role: 'db', en: 'tonight.', pron: '투나잇' }
        ],
        fullEn: "I'm gonna make Korean ramen tonight.",
        fullPron: '암거너 + 메익 코리안 라면 + 투나잇',
        fullKo: '오늘 밤엔 한국 라면을 끓여 먹을 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · 물 정량 맞춰 끓이기',
        visualEmojis: '💧 🍲 ♨️',
        imagePath: '/images/kfood/ep1-s6.jpg',
        actionNote: '냄비에 물 550ml를 붓고 센 불에 끓이기',
        coachKo: '라면의 생명은 물 정량이죠! 먼저 물을 끓여야 해는 First, we have to + boil the water입니다.',
        keyVocab: 'boil the water (물을 끓이다)',
        bgGradient: 'linear-gradient(135deg, #172554 0%, #1e3a8a 100%)',
        blocks: [
          { role: 'bb', en: 'First, we have to', pron: '퍼스트, 위 해프터' },
          { role: 'core', en: 'boil the water', pron: '보일 더 워러' },
          { role: 'db', en: 'in a small pot.', pron: '인 어 스몰 팟' }
        ],
        fullEn: 'First, we have to boil the water in a small pot.',
        fullPron: '퍼스트, 위 해프터 + 보일 더 워러 + 인 어 스몰 팟',
        fullKo: '먼저 작은 냄비에 물을 끓여야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · K-라면 꿀팁: 스프 먼저 넣기!',
        visualEmojis: '🌶️ 🥣 💡',
        imagePath: '/images/kfood/ep1-s5.jpg',
        actionNote: '면보다 분말 스프를 먼저 넣는 한국식 꿀팁 설명',
        coachKo: '라면 분말 스프는 영어로 soup base라고 합니다! 면보다 스프를 먼저 넣을게요!',
        keyVocab: 'soup base (라면 분말 스프)',
        bgGradient: 'linear-gradient(135deg, #422006 0%, #713f12 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'put the soup base', pron: '풋 더 숩 베이스' },
          { role: 'db', en: 'before the noodles.', pron: '비포 더 누들즈' }
        ],
        fullEn: "I'll put the soup base before the noodles.",
        fullPron: '아을 + 풋 더 숩 베이스 + 비포 더 누들즈',
        fullKo: '면보다 스프를 먼저 넣을게요.'
      },
      {
        stepTitle: 'SCENE 4 · 면 넣고 계란 하나 톡 깨 넣기',
        visualEmojis: '🍜 🥚 🌱',
        imagePath: '/images/kfood/ep1-s7.jpg',
        actionNote: '면을 넣고 끓인 뒤 계란을 깨 넣고(crack an egg) 대파 얹기',
        coachKo: '계란 껍데기를 톡 깨서 넣는 동작은 break보다 crack an egg를 훨씬 많이 씁니다!',
        keyVocab: 'crack an egg (계란을 깨 넣다)',
        bgGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'crack an egg', pron: '크랙 언 에그' },
          { role: 'db', en: 'into the pot.', pron: '인투 더 팟' }
        ],
        fullEn: "I'm gonna crack an egg into the pot.",
        fullPron: '암거너 + 크랙 언 에그 + 인투 더 팟',
        fullKo: '냄비에 계란을 하나 톡 깨 넣을 거예요.'
      },
      {
        stepTitle: 'SCENE 5 · 신김치 얹어서 한 입 먹기',
        visualEmojis: '🥢 💨 😋',
        imagePath: '/images/kfood/ep1-s8.jpg',
        actionNote: '꼬들꼬들한 면발 위에 김치 한 점 올려 후루룩!',
        coachKo: '잘 익은 김치랑 같이 한 입 먹어 볼래요? Do you wanna + take a bite + with kimchi?',
        keyVocab: 'take a bite with kimchi',
        bgGradient: 'linear-gradient(135deg, #3b0764 0%, #581c87 100%)',
        blocks: [
          { role: 'bb', en: 'Do you wanna', pron: '두유워너' },
          { role: 'core', en: 'take a bite', pron: '테이커 바이트' },
          { role: 'db', en: 'with kimchi?', pron: '위드 김치?' }
        ],
        fullEn: 'Do you wanna take a bite with kimchi?',
        fullPron: '두유워너 + 테이커 바이트 + 위드 김치?',
        fullKo: '김치 얹어서 한 입 드셔 보실래요?'
      }
    ]
  },

  // ==========================================
  // EP 4. 불고기 & 상추쌈 (Bulgogi & Lettuce Wrap)
  // ==========================================
  {
    id: 'bulgogi-bbq',
    epNumber: 'EP.04',
    emoji: '🥩',
    shortTitle: '4화 · 불고기 & 쌈',
    title: '영어로 불고기 재우기 & 상추쌈 싸 먹는 법 설명하기 (Bulgogi)',
    ytTitle: '[소리블록 요리영어 #4] 불고기 양념 재우기부터 상추쌈(Ssam)까지 영어로! 🥩 | Korean Bulgogi',
    thumbnailText: '"상추에 싸 드세요!" → [You have to] + [wrap it in lettuce]',
    introNarrationKo: '안녕하세요, 소리블록 케이쿠킹입니다! 외국인 친구들이 가장 좋아하는 불고기와 상추쌈 싸 먹는 법을 소리 블록으로 배워 볼게요.',
    outroNarrationKo: '불고기와 상추쌈 영어 표현까지 완벽히 마스터하셨습니다! 구독과 좋아요 잊지 마세요!',
    scenes: [
      {
        stepTitle: 'SCENE 1 · 단짠단짠 불고기 소개',
        visualEmojis: '🥩 🧄 🍯',
        imagePath: '/images/kfood/ep1-s1.jpg',
        actionNote: '얇게 썬 소고기와 간장 양념 재료 소개',
        coachKo: '오늘 저녁엔 한국식 불고기를 만들 거예요! We\'re gonna는 워거너로 가볍게 발음하세요.',
        keyVocab: 'make Korean Bulgogi',
        bgGradient: 'linear-gradient(135deg, #431407 0%, #7c2d12 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '워거너' },
          { role: 'core', en: 'make Korean Bulgogi', pron: '메익 코리안 불고기' },
          { role: 'db', en: 'for dinner.', pron: '포 디너' }
        ],
        fullEn: "We're gonna make Korean Bulgogi for dinner.",
        fullPron: '워거너 + 메익 코리안 불고기 + 포 디너',
        fullKo: '저녁으로 한국식 불고기를 만들 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · 고기를 양념에 재우다 (Marinate)',
        visualEmojis: '🥣 🥩 ⏲️',
        imagePath: '/images/kfood/ep1-s3.jpg',
        actionNote: '간장, 설탕, 마늘, 참기름 양념에 고기를 30분간 재워 두기',
        coachKo: '고기를 양념에 재워 두다는 영어로 marinate라고 합니다! 30분 동안 소고기를 재워 둬야 해요.',
        keyVocab: 'marinate the beef (고기를 재우다)',
        bgGradient: 'linear-gradient(135deg, #422006 0%, #713f12 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해프터' },
          { role: 'core', en: 'marinate the beef', pron: '매리네잇 더 비프' },
          { role: 'db', en: 'for 30 minutes.', pron: '포 써리 미닛츠' }
        ],
        fullEn: 'You have to marinate the beef for 30 minutes.',
        fullPron: '유 해프터 + 매리네잇 더 비프 + 포 써리 미닛츠',
        fullKo: '30분 동안 소고기를 양념에 재워 둬야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · 센 불에서 빠르게 굽기',
        visualEmojis: '🍳 🧅 🍄',
        imagePath: '/images/kfood/ep1-s5.jpg',
        actionNote: '달궈진 팬에 양념된 고기와 양파, 버섯을 넣고 빠르게 볶기',
        coachKo: '센 불에서 빠르게 구워야 육즙이 살아 있죠! 센 불에는 on high heat이라고 합니다.',
        keyVocab: 'on high heat (센 불에)',
        bgGradient: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'cook the meat', pron: '쿡 더 밋' },
          { role: 'db', en: 'on high heat.', pron: '온 하이 힛' }
        ],
        fullEn: "I'm gonna cook the meat on high heat.",
        fullPron: '암거너 + 쿡 더 밋 + 온 하이 힛',
        fullKo: '센 불에서 고기를 빠르게 구워 줄게요.'
      },
      {
        stepTitle: 'SCENE 4 · 한국식 상추쌈(Ssam) 싸 먹기',
        visualEmojis: '🥬 🥩 👍',
        imagePath: '/images/kfood/ep1-s8.jpg',
        actionNote: '손바닥 위 상추에 고기, 밥, 쌈장을 올려 한 입에 쏙!',
        coachKo: '한국 고기 요리의 하이라이트, 상추에 고기를 싸 먹다는 wrap the meat in fresh lettuce!',
        keyVocab: 'wrap the meat in fresh lettuce',
        bgGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'wrap the meat', pron: '랩 더 밋' },
          { role: 'db', en: 'in fresh lettuce.', pron: '인 프레쉬 레터스' }
        ],
        fullEn: "I'll wrap the meat in fresh lettuce.",
        fullPron: '아을 + 랩 더 밋 + 인 프레쉬 레터스',
        fullKo: '신선한 상추에 고기를 싸서 먹어 볼게요.'
      }
    ]
  }
]

const currentEpId = ref(episodes[0].id)
const activeBlockIdx = ref<number | null>(null)
const isAutoPlaying = ref(false)
const customMediaMap = ref<Record<string, string>>({})
const recordedAudioMap = ref<Record<string, string>>({})
const isRecording = ref(false)

let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let autoPlayTimers: number[] = []
let shadowingInterval: number | null = null
let hideControlsTimer: number | null = null
let audioCtx: AudioContext | null = null
let activeHtmlAudio: HTMLAudioElement | null = null

const currentEpisode = computed(
  () => episodes.find((e) => e.id === currentEpId.value) || episodes[0]
)

const safeSceneIndex = computed(() => {
  if (slideCursor.value < 0) return 0
  if (slideCursor.value >= currentEpisode.value.scenes.length) {
    return currentEpisode.value.scenes.length - 1
  }
  return slideCursor.value
})

const currentScene = computed(
  () => currentEpisode.value.scenes[safeSceneIndex.value] || currentEpisode.value.scenes[0]
)

const sceneKey = computed(() => `${currentEpId.value}-${safeSceneIndex.value}`)

const activeSceneImage = computed(() => {
  if (customMediaMap.value[sceneKey.value]) {
    return customMediaMap.value[sceneKey.value]
  }
  if (currentScene.value.imagePath) {
    return withBase(currentScene.value.imagePath)
  }
  return ''
})

// ---------------------------------------------------------
// Web Audio API 방송용 효과음 합성기 (외부 mp3 파일 불필요)
// ---------------------------------------------------------
function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  if (!audioCtx) {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (Ctx) audioCtx = new Ctx()
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume().catch(() => {})
  }
  return audioCtx
}

function playTone(freq: number, durationMs: number, type: OscillatorType = 'sine', gainVal = 0.08, delayMs = 0) {
  if (!enableSoundEffects.value) return
  const ctx = getAudioContext()
  if (!ctx) return
  const startAt = ctx.currentTime + delayMs / 1000
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = type
  osc.frequency.setValueAtTime(freq, startAt)
  gain.gain.setValueAtTime(0.001, startAt)
  gain.gain.exponentialRampToValueAtTime(gainVal, startAt + 0.02)
  gain.gain.exponentialRampToValueAtTime(0.0001, startAt + durationMs / 1000)
  osc.connect(gain)
  gain.connect(ctx.destination)
  osc.start(startAt)
  osc.stop(startAt + durationMs / 1000 + 0.02)
}

function playTransitionChime() {
  // 부드러운 방송 전환 코드 (C5 -> E5 -> G5)
  playTone(523.25, 160, 'triangle', 0.06, 0)
  playTone(659.25, 220, 'triangle', 0.06, 90)
}

function playBlockPop(idx: number) {
  const freqs = [440, 554.37, 659.25]
  playTone(freqs[idx % 3], 110, 'sine', 0.05, 0)
}

function playDingDongYourTurn() {
  // 딩-동! (G5 -> E5) 따라 말하기 시작 신호
  playTone(783.99, 220, 'sine', 0.09, 0)
  playTone(659.25, 380, 'sine', 0.09, 180)
}

function playSuccessBell() {
  playTone(587.33, 120, 'triangle', 0.06, 0)
  playTone(880.0, 280, 'triangle', 0.07, 110)
}

// ---------------------------------------------------------
// 스튜디오급 Neural AI MP3 재생기 (+ 브라우저 TTS 안전 폴백)
// ---------------------------------------------------------
function stopActiveAudio() {
  if (activeHtmlAudio) {
    activeHtmlAudio.pause()
    activeHtmlAudio.currentTime = 0
    activeHtmlAudio = null
  }
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel()
  }
}

function playMp3Async(relPath: string, playbackRate = 1.0): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined') {
      resolve(false)
      return
    }
    stopActiveAudio()
    const audio = new Audio(withBase(relPath))
    audio.playbackRate = playbackRate
    activeHtmlAudio = audio

    let settled = false
    const finish = (ok: boolean) => {
      if (!settled) {
        settled = true
        if (activeHtmlAudio === audio) activeHtmlAudio = null
        resolve(ok)
      }
    }

    audio.onended = () => finish(true)
    audio.onerror = () => finish(false)
    audio.play().catch(() => finish(false))
  })
}

function speakAsync(text: string, lang: 'en-US' | 'ko-KR', rate = 1.0): Promise<void> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      resolve()
      return
    }
    stopActiveAudio()
    const synth = window.speechSynthesis

    const utter = new SpeechSynthesisUtterance(text)
    utter.lang = lang
    utter.rate = rate

    const voices = synth.getVoices()
    if (lang === 'en-US') {
      const usVoice =
        voices.find((v) => v.lang === 'en-US' && /Samantha|Ava|Allison|Alex|Google/i.test(v.name)) ||
        voices.find((v) => v.lang.startsWith('en-US') && !/Albert|Bad|Bahh|Bells|Boing|Bubbles|Cellos|Wobble|Eddy|Flo|Grand|Jester|Organ|Superstar|Trinoids|Whisper|Zarvox/i.test(v.name)) ||
        voices.find((v) => v.lang.startsWith('en'))
      if (usVoice) utter.voice = usVoice
    } else {
      const koVoice =
        voices.find((v) => v.lang.startsWith('ko') && /Yuna|Sora|Google|Siri/i.test(v.name)) ||
        voices.find((v) => v.lang.startsWith('ko') && !/Eddy|Flo|Grand|Reed|Rocko|Sandy|Shelley/i.test(v.name)) ||
        voices.find((v) => v.lang.startsWith('ko'))
      if (koVoice) utter.voice = koVoice
    }

    let settled = false
    const finish = () => {
      if (!settled) {
        settled = true
        resolve()
      }
    }
    const fallbackMs = Math.max(2200, text.length * 110)
    const safetyTimer = window.setTimeout(finish, fallbackMs)

    utter.onend = () => {
      window.clearTimeout(safetyTimer)
      finish()
    }
    utter.onerror = () => {
      window.clearTimeout(safetyTimer)
      finish()
    }
    synth.speak(utter)
  })
}

function speakText(text: string, rate = 1.0) {
  speakAsync(text, 'en-US', rate)
}

async function speakSingleBlock(text: string, idx: number) {
  activeBlockIdx.value = idx
  playBlockPop(idx)
  const mp3Url = `/audio/kfood/${currentEpId.value}-s${safeSceneIndex.value}-b${idx}.mp3`
  const ok = await playMp3Async(mp3Url, 1.0)
  if (!ok) {
    await speakAsync(text, 'en-US', 0.92)
  }
  activeBlockIdx.value = null
}

async function speakSceneSentence(rate = 1.0) {
  activeBlockIdx.value = null
  isShadowingTurn.value = false
  const mp3Url = `/audio/kfood/${currentEpId.value}-s${safeSceneIndex.value}-full.mp3`
  const ok = await playMp3Async(mp3Url, rate)
  if (!ok) {
    await speakAsync(currentScene.value.fullEn, 'en-US', rate)
  }
}

// ---------------------------------------------------------
// 슬라이드 이동 & 전체 자동 방송 시퀀스
// ---------------------------------------------------------
let sequenceToken = 0

function clearTimers() {
  sequenceToken++
  autoPlayTimers.forEach((id) => window.clearTimeout(id))
  autoPlayTimers = []
  if (shadowingInterval !== null) {
    window.clearInterval(shadowingInterval)
    shadowingInterval = null
  }
  stopActiveAudio()
  activeBlockIdx.value = null
  isShadowingTurn.value = false
  shadowingProgress.value = 0
}

function waitMs(ms: number, token: number): Promise<boolean> {
  return new Promise((resolve) => {
    const t = window.setTimeout(() => {
      resolve(token === sequenceToken)
    }, ms)
    autoPlayTimers.push(t)
  })
}

function runShadowingCountdown(durationMs: number, token: number): Promise<boolean> {
  return new Promise((resolve) => {
    if (token !== sequenceToken) {
      resolve(false)
      return
    }
    playDingDongYourTurn()
    isShadowingTurn.value = true
    shadowingProgress.value = 0
    const start = Date.now()

    shadowingInterval = window.setInterval(() => {
      if (token !== sequenceToken) {
        if (shadowingInterval !== null) window.clearInterval(shadowingInterval)
        shadowingInterval = null
        isShadowingTurn.value = false
        resolve(false)
        return
      }
      const elapsed = Date.now() - start
      shadowingProgress.value = Math.min(100, Math.round((elapsed / durationMs) * 100))
      if (elapsed >= durationMs) {
        if (shadowingInterval !== null) window.clearInterval(shadowingInterval)
        shadowingInterval = null
        isShadowingTurn.value = false
        playSuccessBell()
        resolve(true)
      }
    }, 50)
  })
}

async function playCurrentSlideSequence(): Promise<boolean> {
  clearTimers()
  const myToken = sequenceToken
  const epId = currentEpId.value
  playTransitionChime()

  // 1) 인트로 슬라이드일 때
  if (slideCursor.value === -1) {
    if (enableKoreanCoachVoice.value) {
      const ok = await playMp3Async(`/audio/kfood/${epId}-intro-ko.mp3`, 1.0)
      if (!ok) await speakAsync(currentEpisode.value.introNarrationKo, 'ko-KR', 1.03)
      if (myToken !== sequenceToken) return false
      if (!(await waitMs(250, myToken))) return false
    }
    const okEn = await playMp3Async('/audio/kfood/common-lets-cook.mp3', 1.0)
    if (!okEn) await speakAsync("Let's get cooking!", 'en-US', 1.0)
    return myToken === sequenceToken
  }

  // 2) 아웃트로 슬라이드일 때
  if (slideCursor.value >= currentEpisode.value.scenes.length) {
    if (enableKoreanCoachVoice.value) {
      const ok = await playMp3Async(`/audio/kfood/${epId}-outro-ko.mp3`, 1.0)
      if (!ok) await speakAsync(currentEpisode.value.outroNarrationKo, 'ko-KR', 1.03)
      if (myToken !== sequenceToken) return false
      if (!(await waitMs(250, myToken))) return false
    }
    const okEn = await playMp3Async('/audio/kfood/common-see-you.mp3', 1.0)
    if (!okEn) await speakAsync('See you in the next video!', 'en-US', 1.0)
    return myToken === sequenceToken
  }

  // 3) 본편 요리 장면 (Scene 1 ~ N)
  const sc = currentScene.value
  const sIdx = safeSceneIndex.value

  // Step A: 한국어 아나운서 성우(SunHiNeural) 상황 코칭 내레이션
  if (enableKoreanCoachVoice.value && sc.coachKo) {
    const okCoach = await playMp3Async(`/audio/kfood/${epId}-s${sIdx}-coach.mp3`, 1.0)
    if (!okCoach) await speakAsync(sc.coachKo, 'ko-KR', 1.05)
    if (myToken !== sequenceToken) return false
    if (!(await waitMs(320, myToken))) return false
  }

  // Step B: 원어민 성우(AvaNeural) 소리 블록 1 -> 2 -> 3 순차 발화
  for (let i = 0; i < sc.blocks.length; i++) {
    if (myToken !== sequenceToken) return false
    activeBlockIdx.value = i
    playBlockPop(i)
    const okBlk = await playMp3Async(`/audio/kfood/${epId}-s${sIdx}-b${i}.mp3`, 1.0)
    if (!okBlk) await speakAsync(sc.blocks[i].en, 'en-US', 0.92)
    if (!(await waitMs(240, myToken))) return false
  }

  // Step C: 전체 문장 자연스러운 속도로 1회 발화
  activeBlockIdx.value = null
  if (!(await waitMs(220, myToken))) return false
  const okFull = await playMp3Async(`/audio/kfood/${epId}-s${sIdx}-full.mp3`, 1.0)
  if (!okFull) await speakAsync(sc.fullEn, 'en-US', 1.0)
  if (myToken !== sequenceToken) return false

  // Step D: YOUR TURN 따라 말하기 4초 카운트다운
  if (includeShadowingPause.value) {
    if (!(await waitMs(280, myToken))) return false
    const ok = await runShadowingCountdown(4000, myToken)
    if (!ok) return false
  }

  return myToken === sequenceToken
}

function stopAutoShow() {
  isAutoPlaying.value = false
  clearTimers()
}

async function toggleAutoShow() {
  if (isAutoPlaying.value) {
    stopAutoShow()
    return
  }
  isAutoPlaying.value = true
  // 만약 마지막 슬라이드에 있었다면 인트로(-1)부터 시작
  if (slideCursor.value >= currentEpisode.value.scenes.length) {
    slideCursor.value = -1
  }

  while (isAutoPlaying.value && slideCursor.value <= currentEpisode.value.scenes.length) {
    const completed = await playCurrentSlideSequence()
    if (!completed || !isAutoPlaying.value) break

    const myToken = sequenceToken
    const ok = await waitMs(650, myToken)
    if (!ok || !isAutoPlaying.value) break

    if (slideCursor.value < currentEpisode.value.scenes.length) {
      slideCursor.value++
    } else {
      isAutoPlaying.value = false
      break
    }
  }
}

function startEpisodeFromBeginning() {
  slideCursor.value = -1
  toggleAutoShow()
}

function selectEpisode(id: string) {
  stopAutoShow()
  currentEpId.value = id
  slideCursor.value = 0
}

function goToSlide(idx: number) {
  stopAutoShow()
  slideCursor.value = idx
}

function prevSlide() {
  stopAutoShow()
  if (slideCursor.value > -1) {
    slideCursor.value--
  } else {
    slideCursor.value = currentEpisode.value.scenes.length
  }
}

function nextSlide() {
  stopAutoShow()
  if (slideCursor.value < currentEpisode.value.scenes.length) {
    slideCursor.value++
  } else {
    slideCursor.value = -1
  }
}

// ---------------------------------------------------------
// 1080p 전체화면 방송 모드 & 마우스 자동 숨김
// ---------------------------------------------------------
async function toggleFullscreenBroadcast() {
  if (isFullscreenMode.value) {
    await exitFullscreen()
    return
  }
  isFullscreenMode.value = true
  if (studioRoot.value && studioRoot.value.requestFullscreen) {
    try {
      await studioRoot.value.requestFullscreen()
    } catch {
      // 브라우저 정책으로 거부될 경우 CSS 전체화면 폴백 유지
    }
  }
}

async function exitFullscreen() {
  isFullscreenMode.value = false
  if (typeof document !== 'undefined' && document.fullscreenElement) {
    try {
      await document.exitFullscreen()
    } catch {
      // ignore
    }
  }
}

function onFullscreenChange() {
  if (typeof document !== 'undefined' && !document.fullscreenElement) {
    isFullscreenMode.value = false
  }
}

function onMouseMoveInStudio() {
  showFloatingControls.value = true
  if (hideControlsTimer !== null) {
    window.clearTimeout(hideControlsTimer)
  }
  hideControlsTimer = window.setTimeout(() => {
    if (isFullscreenMode.value || isCleanMode.value) {
      showFloatingControls.value = false
    }
  }, 2400)
}

function onKeyDown(e: KeyboardEvent) {
  if (!isFullscreenMode.value) return
  if (e.key === 'ArrowRight') {
    e.preventDefault()
    nextSlide()
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault()
    prevSlide()
  } else if (e.key === ' ') {
    e.preventDefault()
    playCurrentSlideSequence()
  }
}

function onUploadSceneImage(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const url = URL.createObjectURL(file)
  customMediaMap.value[sceneKey.value] = url
}

async function toggleRecording() {
  if (isRecording.value) {
    mediaRecorder?.stop()
    isRecording.value = false
    return
  }
  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) return
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = (ev) => {
      if (ev.data.size > 0) audioChunks.push(ev.data)
    }
    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      recordedAudioMap.value[sceneKey.value] = URL.createObjectURL(blob)
      stream.getTracks().forEach((track) => track.stop())
    }
    mediaRecorder.start()
    isRecording.value = true
  } catch {
    isRecording.value = false
  }
}

async function copyEpisodeScript() {
  const ep = currentEpisode.value
  const lines = [
    `[제목] ${ep.ytTitle}`,
    `[썸네일 문구] ${ep.thumbnailText}`,
    '',
    '--- [타임스탬프 & 소리 블록 대본] ---',
    ...ep.scenes.map(
      (s, i) =>
        `0${i}:00 ${s.stepTitle}\n- EN: ${s.fullEn}\n- 블록: ${s.blocks.map((b) => `[${b.en}]`).join(' + ')}\n- 발음: ${s.fullPron}\n- 뜻: ${s.fullKo}\n`
    ),
    '#소리블록K쿠킹 #SoundBlockKCooking #영어회화초보 #요리영어 #소리블록 #한식영어 #KFood #EnglishSpeaking #KimchiStew'
  ]
  try {
    await navigator.clipboard.writeText(lines.join('\n'))
    copySuccess.value = true
    setTimeout(() => {
      copySuccess.value = false
    }, 2000)
  } catch {
    copySuccess.value = false
  }
}

onMounted(() => {
  if (typeof document !== 'undefined') {
    document.addEventListener('fullscreenchange', onFullscreenChange)
    window.addEventListener('keydown', onKeyDown)
  }
})

onBeforeUnmount(() => {
  stopAutoShow()
  if (typeof document !== 'undefined') {
    document.removeEventListener('fullscreenchange', onFullscreenChange)
    window.removeEventListener('keydown', onKeyDown)
  }
})
</script>

<style scoped>
.kf-studio-v2 {
  margin: 1.4rem 0 2.4rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 18px;
  background: #0b0f19;
  overflow: hidden;
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.16);
  position: relative;
}

/* 전체화면 방송 모드 (1080p Full HD 꽉 찬 화면) */
.kf-studio-v2.theater-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  margin: 0;
  border-radius: 0;
  border: none;
  width: 100vw;
  height: 100vh;
  background: #000;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.kf-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.65rem;
  padding: 0.75rem 1.15rem;
  background: var(--vp-c-bg);
  border-bottom: 1px solid var(--vp-c-divider);
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.theater-fullscreen .kf-topbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 40;
  background: rgba(15, 23, 42, 0.9);
  border-bottom-color: rgba(255, 255, 255, 0.12);
}

.kf-topbar.auto-hide-bar {
  opacity: 0;
  pointer-events: none;
  transform: translateY(-100%);
}

.kf-topbar-left,
.kf-topbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.kf-studio-badge {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.24rem 0.65rem;
  border-radius: 999px;
  background: #ef4444;
  color: #fff !important;
  text-decoration: none !important;
  letter-spacing: 0.03em;
}

.kf-ep-selector,
.kf-aspect-toggle {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.kf-ep-btn,
.kf-mode-btn {
  padding: 0.36rem 0.72rem;
  font-size: 0.78rem;
  font-weight: 700;
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-2);
  cursor: pointer;
  transition: all 0.15s ease;
}

.kf-ep-btn.active,
.kf-mode-btn.active {
  background: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  color: #fff;
}

.kf-fullscreen-btn {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

/* ===================================================
   방송 캔버스 래퍼 & 정밀 16:9 / 9:16 비율 고정
   =================================================== */
.kf-canvas-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #050811;
  padding: 0;
}

.theater-fullscreen .kf-canvas-wrapper {
  height: 100vh;
}

.kf-broadcast-screen {
  position: relative;
  overflow: hidden;
  background: #0f172a;
  user-select: none;
}

.screen-wide {
  width: 100%;
  aspect-ratio: 16 / 9;
  max-height: 100vh;
}

.screen-shorts {
  height: 680px;
  aspect-ratio: 9 / 16;
  margin: 1rem auto;
  border-radius: 18px;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.65);
}

.theater-fullscreen .screen-shorts {
  height: 94vh;
}

/* 풀블리드 배경 이미지 & Ken Burns 애니메이션 */
.kf-main-scene,
.kf-special-slide {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.kf-bg-full {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

@keyframes kenBurnsBroadcast {
  0% {
    transform: scale(1) translate(0, 0);
  }
  100% {
    transform: scale(1.08) translate(-1%, -1%);
  }
}

.ken-burns {
  animation: kenBurnsBroadcast 11s ease-out forwards;
}

/* 방송용 다크 스크림 그라데이션 (위쪽 HUD와 아래쪽 자막 가독성 100% 보장) */
.kf-scrim-gradient {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(
    to bottom,
    rgba(9, 13, 24, 0.72) 0%,
    rgba(9, 13, 24, 0.08) 24%,
    rgba(9, 13, 24, 0.18) 54%,
    rgba(9, 13, 24, 0.88) 78%,
    rgba(9, 13, 24, 0.96) 100%
  );
}

.kf-bg-fallback {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kf-fallback-center {
  text-align: center;
  transform: translateY(-15%);
}

.kf-fallback-emojis {
  font-size: 4.5rem;
  margin-bottom: 0.6rem;
}

.kf-fallback-action {
  font-size: 1.1rem;
  font-weight: 700;
  color: #e2e8f0;
}

/* 상단 HUD */
.kf-hud-top {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.9rem 1.35rem 0.35rem;
  gap: 0.75rem;
}

.kf-hud-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(8px);
  padding: 0.35rem 0.85rem 0.35rem 0.45rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.kf-hud-logo {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;
}

.kf-hud-brand {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.hud-ch-name {
  font-size: 0.68rem;
  font-weight: 800;
  color: #facc15;
}

.hud-ep-step {
  font-size: 0.8rem;
  font-weight: 800;
  color: #fff;
}

.kf-hud-vocab {
  background: rgba(15, 23, 42, 0.82);
  backdrop-filter: blur(8px);
  padding: 0.35rem 0.85rem;
  border-radius: 12px;
  border: 1px solid rgba(56, 189, 248, 0.45);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  color: #fff;
}

.vocab-tag {
  font-size: 0.6rem;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.05em;
}

.kf-hud-vocab strong {
  font-size: 0.88rem;
  color: #fff;
}

.kf-hud-progress {
  position: relative;
  z-index: 10;
  display: flex;
  gap: 0.35rem;
  padding: 0 1.35rem;
}

.hud-dot {
  flex: 1;
  height: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.25);
  cursor: pointer;
  transition: all 0.2s ease;
}

.hud-dot.done {
  background: #10b981;
}

.hud-dot.active {
  background: #facc15;
  transform: scaleY(1.4);
}

/* 중앙 코칭 배너 & YOUR TURN 모달 */
.kf-coach-banner {
  position: relative;
  z-index: 10;
  align-self: center;
  max-width: 88%;
  margin: auto 1rem 0.4rem;
  background: rgba(15, 23, 42, 0.84);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(250, 204, 21, 0.45);
  border-radius: 999px;
  padding: 0.42rem 1.05rem;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: #f8fafc;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}

.coach-icon {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: #facc15;
  color: #0f172a;
  white-space: nowrap;
}

.coach-text {
  font-size: 0.86rem;
  font-weight: 600;
  line-height: 1.35;
}

.kf-center-turn-modal {
  position: relative;
  z-index: 12;
  align-self: center;
  width: min(86%, 560px);
  margin: auto 1rem 0.5rem;
  background: linear-gradient(135deg, rgba(5, 150, 105, 0.95), rgba(16, 185, 129, 0.95));
  border: 2px solid #fde047;
  border-radius: 16px;
  padding: 0.75rem 1.15rem;
  color: #fff;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
}

.turn-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.45rem;
}

.turn-mic-icon {
  font-size: 1.5rem;
}

.turn-texts {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.turn-texts strong {
  font-size: 0.98rem;
  color: #fef08a;
}

.turn-texts span {
  font-size: 0.78rem;
  opacity: 0.95;
}

.turn-sec-badge {
  font-size: 0.9rem;
  font-weight: 900;
  padding: 0.2rem 0.6rem;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
}

.turn-progress-track {
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.3);
  overflow: hidden;
}

.turn-progress-bar {
  height: 100%;
  background: #fde047;
  transition: width 0.06s linear;
}

/* ===================================================
   하단 글래스모피즘 자막 바 (Broadcast Lower-Third)
   =================================================== */
.kf-lower-third {
  position: relative;
  z-index: 10;
  padding: 0.5rem 1.35rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.kf-blocks-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.kf-glass-block {
  flex: 1 1 140px;
  padding: 0.5rem 0.85rem;
  border-radius: 12px;
  backdrop-filter: blur(12px);
  cursor: pointer;
  border: 2px solid transparent;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.kf-glass-block.bb {
  background: rgba(37, 99, 235, 0.45);
  border-color: rgba(96, 165, 250, 0.75);
}

.kf-glass-block.core {
  background: rgba(5, 150, 105, 0.45);
  border-color: rgba(52, 211, 153, 0.75);
}

.kf-glass-block.db {
  background: rgba(217, 119, 6, 0.45);
  border-color: rgba(251, 191, 36, 0.75);
}

.kf-glass-block.active {
  transform: translateY(-4px) scale(1.03);
  box-shadow: 0 0 0 3px #fde047, 0 10px 24px rgba(0, 0, 0, 0.45);
}

.gblk-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.15rem;
}

.gblk-badge {
  font-size: 0.66rem;
  font-weight: 800;
  color: #e2e8f0;
}

.gblk-pron {
  font-size: 0.75rem;
  font-weight: 700;
  color: #fef08a;
}

.gblk-en {
  font-size: 1.12rem;
  font-weight: 900;
  color: #fff;
  letter-spacing: -0.01em;
}

.kf-sentence-banner {
  background: rgba(15, 23, 42, 0.82);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 12px;
  padding: 0.6rem 1rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.kf-main-en {
  font-size: 1.32rem;
  font-weight: 900;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.play-hint-icon {
  font-size: 1rem;
}

.kf-sub-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.88rem;
}

.kf-meta-pron {
  color: #38bdf8;
}

.kf-meta-ko {
  color: #f1f5f9;
  font-weight: 700;
}

/* ===================================================
   인트로 & 아웃트로 스페셜 슬라이드
   =================================================== */
.kf-special-backdrop {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: radial-gradient(circle at center, rgba(15, 23, 42, 0.76) 0%, rgba(9, 13, 24, 0.94) 100%);
}

.outro-backdrop {
  background: rgba(9, 13, 24, 0.9);
}

.kf-intro-content,
.kf-outro-content {
  position: relative;
  z-index: 10;
  margin: auto;
  padding: 1.5rem;
  text-align: center;
  color: #fff;
  width: min(92%, 740px);
}

.kf-intro-top-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.9rem 0.3rem 0.4rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 0.8rem;
  font-weight: 700;
  margin-bottom: 0.8rem;
}

.kf-mini-logo {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.kf-intro-ep-badge {
  font-size: 0.78rem;
  font-weight: 900;
  color: #facc15;
  letter-spacing: 0.08em;
  margin-bottom: 0.35rem;
}

.kf-intro-title {
  margin: 0 0 0.5rem !important;
  font-size: 1.85rem !important;
  font-weight: 900;
  color: #fff !important;
  border: none !important;
}

.kf-intro-sub {
  margin: 0 0 1.1rem !important;
  font-size: 0.95rem;
  color: #cbd5e1;
}

.kf-intro-formula {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-bottom: 1.35rem;
}

.f-pill {
  padding: 0.45rem 0.85rem;
  border-radius: 10px;
  font-size: 0.82rem;
  font-weight: 800;
}

.f-pill.bb {
  background: #2563eb;
}
.f-pill.core {
  background: #059669;
}
.f-pill.db {
  background: #d97706;
}

.f-plus {
  font-weight: 900;
  color: #94a3b8;
}

.kf-intro-cta {
  display: inline-block;
  padding: 0.7rem 1.5rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #ef4444, #f97316);
  color: #fff;
  font-size: 0.95rem;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
}

/* 아웃트로 복습 그리드 */
.outro-badge {
  font-size: 0.74rem;
  font-weight: 800;
  color: #34d399;
}

.outro-title {
  margin: 0.2rem 0 0.85rem !important;
  font-size: 1.35rem !important;
  font-weight: 900;
  color: #fff !important;
  border: none !important;
}

.kf-review-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0.45rem;
  text-align: left;
  margin-bottom: 0.9rem;
}

.kf-review-item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.42rem 0.7rem;
  border-radius: 10px;
  background: rgba(30, 41, 59, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.14);
  cursor: pointer;
}

.rev-num {
  font-size: 0.72rem;
  font-weight: 900;
  color: #38bdf8;
}

.rev-en {
  font-size: 0.82rem;
  font-weight: 800;
  color: #fff;
}

.rev-ko {
  font-size: 0.7rem;
  color: #cbd5e1;
}

.outro-cta-box {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.5rem 1.1rem;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.22);
  border: 1px solid rgba(239, 68, 68, 0.55);
  font-size: 0.82rem;
}

.outro-handle {
  font-size: 0.72rem;
  color: #fde047;
  font-weight: 700;
}

/* 플로팅 리모컨 (풀스크린 방송용) */
.kf-floating-remote {
  position: absolute;
  bottom: 0.75rem;
  right: 1rem;
  z-index: 35;
  display: flex;
  gap: 0.35rem;
  background: rgba(15, 23, 42, 0.88);
  padding: 0.35rem 0.55rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.kf-floating-remote.visible {
  opacity: 1;
  pointer-events: auto;
}

.rem-btn {
  padding: 0.28rem 0.65rem;
  font-size: 0.74rem;
  font-weight: 700;
  border-radius: 999px;
  border: none;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  cursor: pointer;
}

.rem-primary {
  background: #10b981;
}

.rem-primary.playing {
  background: #ef4444;
}

.rem-exit {
  background: #475569;
}

/* 하단 컨트롤 패널 */
.kf-controls-panel {
  padding: 0.95rem 1.25rem;
  background: var(--vp-c-bg);
  border-top: 1px solid var(--vp-c-divider);
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.kf-nav-group,
.kf-extra-tools,
.kf-voice-recorder,
.kf-custom-tools {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.kf-extra-tools {
  justify-content: space-between;
  padding-top: 0.65rem;
  border-top: 1px dashed var(--vp-c-divider);
}

.kf-ctrl-btn {
  padding: 0.42rem 0.8rem;
  font-size: 0.8rem;
  font-weight: 700;
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
  cursor: pointer;
}

.kf-ctrl-btn-sm {
  padding: 0.3rem 0.65rem;
  font-size: 0.76rem;
  font-weight: 700;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  cursor: pointer;
}

.kf-btn-broadcast {
  background: linear-gradient(135deg, #2563eb, #059669);
  border: none;
  color: #fff;
}

.kf-btn-primary {
  background: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  color: #fff;
}

.kf-btn-step {
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.45);
}

.kf-btn-playing,
.kf-btn-rec {
  background: #ef4444 !important;
  border-color: #ef4444 !important;
  color: #fff !important;
}

.kf-upload-label {
  padding: 0.35rem 0.7rem;
  font-size: 0.76rem;
  font-weight: 700;
  border-radius: 8px;
  border: 1px dashed var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
  cursor: pointer;
}

.kf-audio-player {
  height: 30px;
  max-width: 190px;
}

.kf-chk {
  font-size: 0.76rem;
  color: var(--vp-c-text-2);
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
}

.kf-yt-package {
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  background: var(--vp-c-bg-soft);
  overflow: hidden;
}

.kf-yt-package-header {
  display: flex;
  justify-content: space-between;
  padding: 0.6rem 0.95rem;
  font-size: 0.82rem;
  cursor: pointer;
}

.kf-yt-package-body {
  padding: 0.75rem 0.95rem;
  border-top: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.82rem;
}

.kf-meta-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.kf-pop-enter-active,
.kf-pop-leave-active {
  transition: all 0.22s ease;
}
.kf-pop-enter-from,
.kf-pop-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
