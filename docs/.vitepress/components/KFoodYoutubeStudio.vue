<template>
  <div class="kf-studio" :class="{ 'clean-record-mode': isCleanMode }" @click.stop>
    <!-- 상단 컨트롤 바 -->
    <div class="kf-topbar">
      <div class="kf-topbar-left">
        <span class="kf-studio-badge">🎬 K-FOOD YOUTUBE STUDIO</span>
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
            📺 16:9 유튜브 가로형
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
          class="kf-mode-btn kf-clean-btn"
          :class="{ active: isCleanMode }"
          @click="isCleanMode = !isCleanMode"
        >
          {{ isCleanMode ? '⚙️ 편집 컨트롤 보이기' : '🎥 화면 녹화 클린 모드' }}
        </button>
      </div>
    </div>

    <!-- 메인 스튜디오 캔버스 영역 -->
    <div class="kf-canvas-wrapper" :class="aspectRatio === '9:16' ? 'is-shorts' : 'is-wide'">
      <div class="kf-screen" :class="aspectRatio === '9:16' ? 'screen-shorts' : 'screen-wide'">
        <!-- 상단 채널 워터마크 & 씬 진행 바 -->
        <div class="kf-screen-header">
          <div class="kf-channel-tag">
            <span class="kf-channel-dot"></span>
            <span>{{ channelName }} · {{ currentEpisode.epNumber }}</span>
          </div>
          <div class="kf-step-counter">
            STEP {{ sceneIndex + 1 }} / {{ currentEpisode.scenes.length }}
          </div>
        </div>

        <div class="kf-progress-dots">
          <span
            v-for="(sc, idx) in currentEpisode.scenes"
            :key="idx"
            class="kf-dot"
            :class="{ active: idx === sceneIndex, done: idx < sceneIndex }"
            @click="goToScene(idx)"
          ></span>
        </div>

        <!-- 비주얼 스테이지 (일러스트 카드 또는 사용자 업로드 사진) -->
        <div class="kf-visual-stage" :style="{ background: currentScene.bgGradient }">
          <template v-if="customMediaMap[sceneKey]">
            <img :src="customMediaMap[sceneKey]" alt="Custom cooking scene" class="kf-custom-img" />
          </template>
          <template v-else>
            <div class="kf-illust-card">
              <div class="kf-illust-emojis">{{ currentScene.visualEmojis }}</div>
              <div class="kf-illust-step-badge">{{ currentScene.stepTitle }}</div>
              <div class="kf-illust-action">{{ currentScene.actionNote }}</div>
            </div>
          </template>

          <!-- 우측 상단 핵심 요리 동사 배지 -->
          <div class="kf-verb-floating">
            <span class="verb-label">핵심 표현</span>
            <strong>{{ currentScene.keyVocab }}</strong>
          </div>
        </div>

        <!-- 하단 소리 블록 자막 영역 (유튜브 캡션 스타일) -->
        <div class="kf-caption-stage">
          <!-- 소리 블록 조각 체인 -->
          <div class="kf-block-pills">
            <div
              v-for="(blk, bIdx) in currentScene.blocks"
              :key="bIdx"
              class="kf-block-pill"
              :class="[blk.role, { speaking: activeBlockIdx === bIdx }]"
              @click="speakText(blk.en, 0.92)"
            >
              <span class="blk-role-label">
                {{ blk.role === 'bb' ? '① 시작 블록' : blk.role === 'core' ? '② 코어 블록' : '③ 디테일 블록' }}
              </span>
              <strong class="blk-en">{{ blk.en }}</strong>
              <span v-if="showPronGuide" class="blk-pron">[{{ blk.pron }}]</span>
            </div>
          </div>

          <!-- 완성 문장 & 한글 리듬 & 번역 -->
          <div class="kf-full-sentence" @click="speakSceneSentence(1.0)">
            {{ currentScene.fullEn }}
          </div>
          <div v-if="showPronGuide" class="kf-pron-line">
            🗣️ 리듬 가이드: <strong>{{ currentScene.fullPron }}</strong>
          </div>
          <div v-if="showKoSub" class="kf-ko-line">
            {{ currentScene.fullKo }}
          </div>
        </div>
      </div>
    </div>

    <!-- 하단 플레이어 & 녹음 컨트롤 바 -->
    <div class="kf-controls-panel">
      <div class="kf-nav-group">
        <button type="button" class="kf-ctrl-btn" @click="prevScene">◀ 이전 장면</button>
        <button type="button" class="kf-ctrl-btn kf-btn-primary" @click="speakSceneSentence(1.0)">
          🔊 원어민 음성 (1.0x)
        </button>
        <button type="button" class="kf-ctrl-btn" @click="speakSceneSentence(0.8)">
          🐢 천천히 (0.8x)
        </button>
        <button type="button" class="kf-ctrl-btn kf-btn-step" @click="speakBlocksSequentially">
          🔁 블록별 끊어→이어 듣기
        </button>
        <button
          type="button"
          class="kf-ctrl-btn"
          :class="{ 'kf-btn-playing': isAutoPlaying }"
          @click="toggleAutoShow"
        >
          {{ isAutoPlaying ? '⏹️ 자동 쇼 중지' : '▶️ 전체 장면 자동 재생 (녹화용)' }}
        </button>
        <button type="button" class="kf-ctrl-btn" @click="nextScene">다음 장면 ▶</button>
      </div>

      <!-- 내 목소리 녹음 & 사진 교체 & 자막 옵션 (클린 모드에서는 숨김) -->
      <div v-if="!isCleanMode" class="kf-extra-tools">
        <div class="kf-voice-recorder">
          <button
            type="button"
            class="kf-ctrl-btn"
            :class="{ 'kf-btn-rec': isRecording }"
            @click="toggleRecording"
          >
            {{ isRecording ? '⏹️ 녹음 완료하기' : '🎙️ 내 목소리로 따라 녹음하기' }}
          </button>
          <audio
            v-if="recordedAudioMap[sceneKey]"
            :src="recordedAudioMap[sceneKey]"
            controls
            class="kf-audio-player"
          ></audio>
        </div>

        <div class="kf-custom-tools">
          <label class="kf-upload-label">
            📷 이 장면에 내 요리 사진 넣기
            <input type="file" accept="image/*" hidden @change="onUploadSceneImage" />
          </label>
          <button
            v-if="customMediaMap[sceneKey]"
            type="button"
            class="kf-ctrl-btn-sm"
            @click="removeSceneImage"
          >
            기본 일러스트로 복원
          </button>
          <label class="kf-chk">
            <input v-model="showPronGuide" type="checkbox" /> 한글 발음 표시
          </label>
          <label class="kf-chk">
            <input v-model="showKoSub" type="checkbox" /> 한국어 뜻 표시
          </label>
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
import { ref, computed, onBeforeUnmount } from 'vue'

interface SoundBlockPiece {
  role: 'bb' | 'core' | 'db'
  en: string
  pron: string
}

interface CookingScene {
  stepTitle: string
  visualEmojis: string
  actionNote: string
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
  scenes: CookingScene[]
}

const channelName = ref('K-Food Block English')
const aspectRatio = ref<'16:9' | '9:16'>('16:9')
const isCleanMode = ref(false)
const showPronGuide = ref(true)
const showKoSub = ref(true)
const showYtMeta = ref(false)
const copySuccess = ref(false)

const episodes: CookingEpisode[] = [
  // ==========================================
  // EP 1. 김치찌개 (Kimchi Stew)
  // ==========================================
  {
    id: 'kimchi-stew',
    epNumber: 'EP.01',
    emoji: '🍲',
    shortTitle: '1화 · 김치찌개',
    title: '영어로 김치찌개 끓이기 (Kimchi Stew)',
    ytTitle: '[소리 블록 요리 영어 #1] 중학교 단어로 김치찌개 끓이기 🍲 | How to Make Kimchi Stew in Easy English',
    thumbnailText: '"김치찌개 끓일게!" → [I\'m gonna] + [make Kimchi stew]',
    scenes: [
      {
        stepTitle: 'SCENE 1 · 오늘의 요리 소개',
        visualEmojis: '👨‍🍳 🍲 🇰🇷',
        actionNote: '앞치마를 입고 부엌에서 밝게 인사하는 오프닝',
        keyVocab: 'Kimchi stew (김치찌개)',
        bgGradient: 'linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%)',
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
        actionNote: '잘 익은 신김치를 보여주며 핵심 비법 설명',
        keyVocab: 'sour (aged) kimchi (신김치)',
        bgGradient: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
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
        actionNote: '도마 위에서 김치와 돼지고기를 한 입 크기로 큼직하게 썰기',
        keyVocab: 'chop / bite-sized pieces',
        bgGradient: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)',
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
        actionNote: '두부는 납작하게 썰고(slice), 대파는 송송 썰어 준비',
        keyVocab: 'slice the tofu (두부를 썰다)',
        bgGradient: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
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
        actionNote: '달궈진 냄비에 돼지고기, 김치, 다진 마늘을 넣고 지글지글 볶기',
        keyVocab: 'fry / sauté (기름에 볶다)',
        bgGradient: 'linear-gradient(135deg, #fefce8 0%, #fef08a 100%)',
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
        actionNote: '물을 붓고 감칠맛의 핵심인 김치 국물(kimchi juice) 한 국자 추가!',
        keyVocab: 'kimchi juice (김치 국물)',
        bgGradient: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
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
        actionNote: '센 불에 팔팔 끓인 뒤 중약불로 줄여 10분간 뭉근히 끓이기',
        keyVocab: 'bring it to the boil / simmer',
        bgGradient: 'linear-gradient(135deg, #fff1f2 0%, #fecdd3 100%)',
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
        actionNote: '국물 한 모금(take a sip) 맛보고 따뜻한 흰쌀밥과 한 입!',
        keyVocab: 'take a sip / take a bite',
        bgGradient: 'linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%)',
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
    title: '영어로 김치볶음밥 & 계란프라이 만들기 (Kimchi Fried Rice)',
    ytTitle: '[소리 블록 요리 영어 #2] 5분 완성 김치볶음밥 영어로 설명하기 🍳 | Kimchi Fried Rice in Easy English',
    thumbnailText: '"계란프라이 올릴게!" → [I\'ll] + [put a fried egg] + [on top]',
    scenes: [
      {
        stepTitle: 'SCENE 1 · 김치볶음밥 시작하기',
        visualEmojis: '🍚 🥬 🍳',
        actionNote: '찬밥과 잘게 썬 김치를 준비하며 인사',
        keyVocab: 'Kimchi fried rice (김치볶음밥)',
        bgGradient: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)',
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
        actionNote: '볶음밥용으로 김치와 베이컨(또는 스팸)을 잘게 다지듯 썰기',
        keyVocab: 'chop finely (잘게 썰다)',
        bgGradient: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
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
        actionNote: '팬에 김치와 고추장/간장을 넣고 센 불에 달달 볶기',
        keyVocab: 'stir-fry (센 불에 저으며 볶다)',
        bgGradient: 'linear-gradient(135deg, #fefce8 0%, #fef08a 100%)',
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
        actionNote: '밥을 넣고 골고루 섞은 뒤 마지막에 고소한 참기름 한 바퀴!',
        keyVocab: 'sesame oil (참기름)',
        bgGradient: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
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
        actionNote: '노른자가 살아 있는 반숙 계란프라이(sunny-side-up egg)를 맨 위에 얹기',
        keyVocab: 'fried egg / on top',
        bgGradient: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
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
        actionNote: '숟가락으로 노른자를 톡 터뜨려 밥과 함께 한 입!',
        keyVocab: 'pop the yolk / take a bite',
        bgGradient: 'linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%)',
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
    ytTitle: '[소리 블록 요리 영어 #3] 외국인 친구에게 K-라면 끓이는 법 영어로 말하기 🍜 | How to Cook Korean Ramen',
    thumbnailText: '"스프부터 넣어야 해!" → [You have to] + [put the soup base first]',
    scenes: [
      {
        stepTitle: 'SCENE 1 · 출출한 밤, 라면 끓이기',
        visualEmojis: '🌙 🍜 🔥',
        actionNote: '냄비와 라면 한 봉지를 들고 시작',
        keyVocab: 'make ramen (라면을 끓이다)',
        bgGradient: 'linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%)',
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
        actionNote: '냄비에 물 550ml를 붓고 센 불에 끓이기',
        keyVocab: 'boil the water (물을 끓이다)',
        bgGradient: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
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
        actionNote: '면보다 분말 스프와 건더기 스프를 먼저 넣는 한국식 꿀팁 설명',
        keyVocab: 'soup base / flakes (분말·건더기 스프)',
        bgGradient: 'linear-gradient(135deg, #fefce8 0%, #fef08a 100%)',
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
        actionNote: '면을 넣고 3분 끓인 뒤 계란을 깨 넣고(crack an egg) 대파 얹기',
        keyVocab: 'crack an egg (계란을 깨 넣다)',
        bgGradient: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
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
        stepTitle: 'SCENE 5 · 면발을 들었다 놨다 (꼬들면 비법)',
        visualEmojis: '🥢 💨 😋',
        actionNote: '젓가락으로 면을 공기와 접촉시켜 쫄깃하게(chewy) 만들기',
        keyVocab: 'chewy noodles (쫄깃한 면발)',
        bgGradient: 'linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%)',
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
    ytTitle: '[소리 블록 요리 영어 #4] 불고기 양념 재우기부터 상추쌈(Ssam)까지 영어로! 🥩 | Korean Bulgogi',
    thumbnailText: '"상추에 싸 드세요!" → [You have to] + [wrap it in lettuce]',
    scenes: [
      {
        stepTitle: 'SCENE 1 · 단짠단짠 불고기 소개',
        visualEmojis: '🥩 🧄 🍯',
        actionNote: '얇게 썬 소고기와 간장 양념 재료 소개',
        keyVocab: 'sweet and savory (단짠단짠)',
        bgGradient: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)',
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
        actionNote: '간장, 설탕, 마늘, 참기름 양념에 고기를 30분간 재워 두기',
        keyVocab: 'marinate the beef (고기를 재우다)',
        bgGradient: 'linear-gradient(135deg, #fefce8 0%, #fef08a 100%)',
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
        stepTitle: 'SCENE 3 · 양파·버섯과 함께 볶기',
        visualEmojis: '🍳 🧅 🍄',
        actionNote: '달궈진 팬에 양념된 고기와 양파, 버섯을 넣고 빠르게 볶기',
        keyVocab: 'cook on high heat (센 불에 익히다)',
        bgGradient: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
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
        actionNote: '손바닥 위 상추에 고기, 밥, 쌈장을 올려 한 입에 쏙!',
        keyVocab: 'wrap it in lettuce (상추에 싸다)',
        bgGradient: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
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
const sceneIndex = ref(0)
const activeBlockIdx = ref<number | null>(null)
const isAutoPlaying = ref(false)
const customMediaMap = ref<Record<string, string>>({})
const recordedAudioMap = ref<Record<string, string>>({})
const isRecording = ref(false)

let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let autoPlayTimers: number[] = []

const currentEpisode = computed(
  () => episodes.find((e) => e.id === currentEpId.value) || episodes[0]
)

const currentScene = computed(
  () => currentEpisode.value.scenes[sceneIndex.value] || currentEpisode.value.scenes[0]
)

const sceneKey = computed(() => `${currentEpId.value}-${sceneIndex.value}`)

function selectEpisode(id: string) {
  stopAutoShow()
  currentEpId.value = id
  sceneIndex.value = 0
}

function goToScene(idx: number) {
  stopAutoShow()
  sceneIndex.value = idx
}

function prevScene() {
  stopAutoShow()
  if (sceneIndex.value > 0) {
    sceneIndex.value--
  } else {
    sceneIndex.value = currentEpisode.value.scenes.length - 1
  }
}

function nextScene() {
  stopAutoShow()
  if (sceneIndex.value < currentEpisode.value.scenes.length - 1) {
    sceneIndex.value++
  } else {
    sceneIndex.value = 0
  }
}

function speakText(text: string, rate = 1.0) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
  const synth = window.speechSynthesis
  synth.cancel()
  const utter = new SpeechSynthesisUtterance(text)
  utter.lang = 'en-US'
  utter.rate = rate
  const voices = synth.getVoices()
  const usVoice =
    voices.find((v) => v.lang === 'en-US' && /Samantha|Alex|Google|Natural|Siri/i.test(v.name)) ||
    voices.find((v) => v.lang.startsWith('en-US')) ||
    voices.find((v) => v.lang.startsWith('en'))
  if (usVoice) utter.voice = usVoice
  synth.speak(utter)
}

function speakSceneSentence(rate = 1.0) {
  activeBlockIdx.value = null
  speakText(currentScene.value.fullEn, rate)
}

function clearTimers() {
  autoPlayTimers.forEach((id) => window.clearTimeout(id))
  autoPlayTimers = []
  activeBlockIdx.value = null
}

function speakBlocksSequentially() {
  clearTimers()
  const blocks = currentScene.value.blocks
  let delay = 0

  blocks.forEach((blk, idx) => {
    const t = window.setTimeout(() => {
      activeBlockIdx.value = idx
      speakText(blk.en, 0.9)
    }, delay)
    autoPlayTimers.push(t)
    delay += 1350
  })

  const finalT = window.setTimeout(() => {
    activeBlockIdx.value = null
    speakText(currentScene.value.fullEn, 1.0)
  }, delay + 200)
  autoPlayTimers.push(finalT)
}

function stopAutoShow() {
  isAutoPlaying.value = false
  clearTimers()
}

function toggleAutoShow() {
  if (isAutoPlaying.value) {
    stopAutoShow()
    return
  }
  isAutoPlaying.value = true
  sceneIndex.value = 0
  runAutoShowStep(0)
}

function runAutoShowStep(idx: number) {
  if (!isAutoPlaying.value) return
  if (idx >= currentEpisode.value.scenes.length) {
    isAutoPlaying.value = false
    return
  }
  sceneIndex.value = idx
  speakBlocksSequentially()

  const nextT = window.setTimeout(() => {
    if (isAutoPlaying.value) {
      runAutoShowStep(idx + 1)
    }
  }, 6800)
  autoPlayTimers.push(nextT)
}

function onUploadSceneImage(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const url = URL.createObjectURL(file)
  customMediaMap.value[sceneKey.value] = url
}

function removeSceneImage() {
  delete customMediaMap.value[sceneKey.value]
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
    '#영어회화초보 #요리영어 #소리블록 #한식영어 #KFood #EnglishSpeaking #KimchiStew'
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

onBeforeUnmount(() => {
  stopAutoShow()
})
</script>

<style scoped>
.kf-studio {
  margin: 1.4rem 0 2.2rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 18px;
  background: var(--vp-c-bg-soft);
  overflow: hidden;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.07);
}

.kf-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.9rem 1.25rem;
  background: var(--vp-c-bg);
  border-bottom: 1px solid var(--vp-c-divider);
}

.kf-topbar-left,
.kf-topbar-right {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.kf-studio-badge {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.22rem 0.6rem;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  letter-spacing: 0.04em;
}

.kf-ep-selector,
.kf-aspect-toggle {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.kf-ep-btn,
.kf-mode-btn {
  padding: 0.38rem 0.75rem;
  font-size: 0.8rem;
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

.kf-clean-btn.active {
  background: #10b981;
  border-color: #10b981;
}

/* 스튜디오 캔버스 */
.kf-canvas-wrapper {
  padding: 1.25rem;
  display: flex;
  justify-content: center;
  background: #0f172a;
}

.kf-screen {
  background: #1e293b;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 2px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45);
}

.screen-wide {
  width: 100%;
  max-width: 820px;
  min-height: 460px;
}

.screen-shorts {
  width: 360px;
  min-height: 620px;
}

.kf-screen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.7rem 1.1rem 0.4rem;
  color: #e2e8f0;
  font-size: 0.78rem;
  font-weight: 700;
}

.kf-channel-tag {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.kf-channel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  display: inline-block;
}

.kf-progress-dots {
  display: flex;
  gap: 0.35rem;
  padding: 0 1.1rem 0.65rem;
}

.kf-dot {
  flex: 1;
  height: 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
}

.kf-dot.done {
  background: rgba(16, 185, 129, 0.7);
}

.kf-dot.active {
  background: #38bdf8;
}

.kf-visual-stage {
  position: relative;
  flex: 1;
  margin: 0 1rem;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  min-height: 200px;
  overflow: hidden;
}

.kf-custom-img {
  width: 100%;
  height: 100%;
  max-height: 280px;
  object-fit: cover;
  border-radius: 10px;
}

.kf-illust-card {
  text-align: center;
  color: #1e293b;
}

.kf-illust-emojis {
  font-size: 3.3rem;
  margin-bottom: 0.5rem;
  line-height: 1.1;
}

.kf-illust-step-badge {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 800;
  padding: 0.2rem 0.75rem;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.85);
  color: #fff;
  margin-bottom: 0.45rem;
}

.kf-illust-action {
  font-size: 0.92rem;
  font-weight: 700;
  color: #334155;
}

.kf-verb-floating {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: rgba(15, 23, 42, 0.88);
  color: #fff;
  padding: 0.35rem 0.75rem;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.verb-label {
  font-size: 0.64rem;
  color: #38bdf8;
  font-weight: 700;
}

.kf-verb-floating strong {
  font-size: 0.84rem;
}

/* 캡션 스테이지 */
.kf-caption-stage {
  padding: 1rem 1.15rem 1.2rem;
  color: #fff;
}

.kf-block-pills {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}

.kf-block-pill {
  flex: 1 1 130px;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border: 2px solid transparent;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.kf-block-pill.speaking {
  transform: scale(1.04);
  box-shadow: 0 0 0 3px #facc15;
}

.kf-block-pill.bb {
  background: rgba(59, 130, 246, 0.28);
  border-color: #60a5fa;
}

.kf-block-pill.core {
  background: rgba(16, 185, 129, 0.28);
  border-color: #34d399;
}

.kf-block-pill.db {
  background: rgba(245, 158, 11, 0.28);
  border-color: #fbbf24;
}

.blk-role-label {
  font-size: 0.66rem;
  font-weight: 700;
  opacity: 0.85;
}

.blk-en {
  font-size: 1.05rem;
  font-weight: 800;
  color: #fff;
}

.blk-pron {
  font-size: 0.78rem;
  color: #fef08a;
  font-weight: 600;
}

.kf-full-sentence {
  font-size: 1.35rem;
  font-weight: 900;
  color: #fff;
  cursor: pointer;
  margin-bottom: 0.25rem;
}

.kf-pron-line {
  font-size: 0.9rem;
  color: #38bdf8;
  margin-bottom: 0.15rem;
}

.kf-ko-line {
  font-size: 0.92rem;
  color: #cbd5e1;
  font-weight: 600;
}

/* 컨트롤 패널 */
.kf-controls-panel {
  padding: 1rem 1.25rem;
  background: var(--vp-c-bg);
  border-top: 1px solid var(--vp-c-divider);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.kf-nav-group,
.kf-extra-tools,
.kf-voice-recorder,
.kf-custom-tools {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.kf-extra-tools {
  justify-content: space-between;
  padding-top: 0.65rem;
  border-top: 1px dashed var(--vp-c-divider);
}

.kf-ctrl-btn {
  padding: 0.45rem 0.85rem;
  font-size: 0.83rem;
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
  background: #ef4444;
  border-color: #ef4444;
  color: #fff;
}

.kf-upload-label {
  padding: 0.38rem 0.75rem;
  font-size: 0.78rem;
  font-weight: 700;
  border-radius: 8px;
  border: 1px dashed var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
  cursor: pointer;
}

.kf-audio-player {
  height: 32px;
  max-width: 210px;
}

.kf-chk {
  font-size: 0.78rem;
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
  padding: 0.65rem 0.95rem;
  font-size: 0.84rem;
  cursor: pointer;
}

.kf-yt-package-body {
  padding: 0.75rem 0.95rem;
  border-top: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.83rem;
}

.kf-meta-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
