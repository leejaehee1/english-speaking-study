<template>
  <div
    ref="studioRoot"
    class="kf-studio-v2"
    :class="[
      'font-' + fontScale,
      {
        'clean-record-mode': isCleanMode,
        'theater-fullscreen': isFullscreenMode
      }
    ]"
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
          title="Visit YouTube Channel"
        >
          ▶️ @SoundBlockKCooking
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
        <!-- 휴대폰/모바일 가독성을 위한 글자 크기 조절기 -->
        <div class="kf-font-toggle">
          <button
            type="button"
            class="kf-mode-btn kf-font-btn"
            :title="'Font Size: ' + fontScaleLabel"
            @click="cycleFontScale"
          >
            🔠 Font: <strong>{{ fontScaleLabel }}</strong>
          </button>
        </div>

        <!-- 🔴 스튜디오 원클릭 자체 비디오 녹화 (내부 사운드 직통) -->
        <label class="kf-mic-chk" title="Optionally mix your microphone into the studio recording">
          <input v-model="includeMicInRecording" type="checkbox" /> 🎙️ My Mic
        </label>
        <button
          type="button"
          class="kf-mode-btn kf-rec-toggle-btn"
          :class="{ 'is-rec-active': isScreenRecording }"
          @click="toggleScreenRecording"
        >
          {{ isScreenRecording ? `⏹️ Stop & Save (${formatRecordTime})` : '🔴 Record 1080p Video' }}
        </button>

        <div class="kf-aspect-toggle">
          <button
            type="button"
            class="kf-mode-btn"
            :class="{ active: aspectRatio === '16:9' }"
            @click="aspectRatio = '16:9'"
          >
            📺 16:9 Landscape (1080p)
          </button>
          <button
            type="button"
            class="kf-mode-btn"
            :class="{ active: aspectRatio === '9:16' }"
            @click="aspectRatio = '9:16'"
          >
            📱 9:16 Shorts (Vertical)
          </button>
        </div>

        <button
          type="button"
          class="kf-mode-btn kf-fullscreen-btn"
          :class="{ active: isFullscreenMode }"
          @click="toggleFullscreenBroadcast"
        >
          {{ isFullscreenMode ? '✕ Exit Fullscreen (ESC)' : '🖥️ 1080p Fullscreen Studio' }}
        </button>
      </div>
    </div>

    <!-- ==========================================================
         메인 16:9 / 9:16 방송 캔버스 (Full-Bleed Broadcast Screen)
         ========================================================== -->
    <div class="kf-canvas-wrapper" :class="aspectRatio === '9:16' ? 'is-shorts' : 'is-wide'">
      <div class="kf-broadcast-screen" :class="aspectRatio === '9:16' ? 'screen-shorts' : 'screen-wide'">
        <!-- 🎬 풀스크린 복원 & 5초 녹화 준비 카운트다운 오버레이 -->
        <transition name="kf-pop">
          <div v-if="countdownToRecord !== null" class="kf-record-countdown-overlay">
            <div class="rc-box">
              <div class="rc-badge">🔴 1080p FULLSCREEN RECORDING READY</div>
              <div class="rc-number">{{ countdownToRecord }}</div>
              <div class="rc-sub">Fullscreen restored! Starting in {{ countdownToRecord }}s...</div>
            </div>
          </div>
        </transition>

<!-- 💡 In-canvas REC badge removed so video is 100% clean -->
        <!-- ----------------------------------------------------
             CASE A: INTRO 슬라이드 (오프닝 훅 화면)
             ---------------------------------------------------- -->
        <div v-if="slideCursor === -1" class="kf-special-slide intro-slide">
          <img
            :src="withBase(currentEpisode.thumbnailImage || '/images/kfood/ep1-thumb.jpg')"
            alt="Episode Intro Background"
            class="kf-bg-full ken-burns"
          />
          <div class="kf-special-backdrop"></div>

          <div class="kf-intro-content">
            <div class="kf-intro-top-pill">
              <img :src="withBase('/images/kfood/channel-logo.jpg')" alt="Logo" class="kf-mini-logo" />
              <span>SoundBlock K-Cooking Studio</span>
            </div>

            <div class="kf-intro-ep-badge">{{ currentEpisode.epNumber }} · K-FOOD SPEAKING RECIPE</div>
            <h2 class="kf-intro-title">{{ currentEpisode.title }}</h2>
            <p class="kf-intro-sub">
              Don't memorize word by word! <strong>Swap and snap Sound Blocks</strong> like Lego to speak naturally.
            </p>

            <div class="kf-intro-formula">
              <span class="f-pill bb">① 1st Block (I'm gonna / You have to)</span>
              <span class="f-plus">+</span>
              <span class="f-pill core">② Core Action Block (make Kimchi stew)</span>
              <span class="f-plus">+</span>
              <span class="f-pill db">③ Detail Block (today)</span>
            </div>

            <div class="kf-intro-cta" @click="startEpisodeFromBeginning">
              ▶️ Let's get cooking! (Click to Start)
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
                <span class="hud-ch-name">SoundBlock K-Cooking</span>
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
              title="Opening Intro"
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
              title="Full Review Outro"
              @click="goToSlide(currentEpisode.scenes.length)"
            ></span>
          </div>

          <!-- 3) 훈련 단계 탭 (시작 블록 3단 교체 / 실전 자석 합체 미션 / 완성 문장 복습) -->
          <div class="kf-stage-tabs">
            <button
              type="button"
              class="stage-tab-btn"
              :class="{ active: activeStage === 'swap' }"
              @click="setStage('swap')"
            >
              🔄 Step 1: Swap 1st Block
            </button>
            <button
              type="button"
              class="stage-tab-btn"
              :class="{ active: activeStage === 'quiz' }"
              @click="setStage('quiz')"
            >
              🧲 Step 2: Snap Blocks
            </button>
            <button
              type="button"
              class="stage-tab-btn"
              :class="{ active: activeStage === 'sentence' }"
              @click="setStage('sentence')"
            >
              🎤 Step 3: YOUR TURN (Speak Out Loud)
            </button>
          </div>

          <!-- 4) 중앙 알림 (코칭 음성 배너 또는 따라 말하기 카운트다운) -->
          <transition name="kf-pop">
            <div v-if="isShadowingTurn" class="kf-center-turn-modal">
              <div class="turn-header">
                <span class="turn-mic-icon">🎤</span>
                <div class="turn-texts">
                  <strong>YOUR TURN! Speak Out Loud!</strong>
                  <span>Say the full sentence in one breath with natural rhythm</span>
                </div>
                <span class="turn-sec-badge">{{ Math.ceil((100 - shadowingProgress) * 0.04) }}s</span>
              </div>
              <div class="turn-progress-track">
                <div class="turn-progress-bar" :style="{ width: shadowingProgress + '%' }"></div>
              </div>
            </div>

            <div v-else-if="showCoachBubble && currentCoachText && activeStage !== 'quiz'" class="kf-coach-banner">
              <span class="coach-icon">{{ activeStage === 'quiz' ? '🎯 SNAP MISSION' : '💡 COOKING TIP' }}</span>
              <span class="coach-text">{{ currentCoachText }}</span>
            </div>
          </transition>

          <!-- 5) 메인 무대: 활성 훈련 단계에 따른 독 (Lower-Third Dock) -->

          <!-- ============================================================
               STAGE 1: 시작 블록 3단 교체 훈련 (안 B: 한글 자막 없이 영어 블록만 초대형 중앙 배치)
               ============================================================ -->
          <div v-if="activeStage === 'swap'" class="kf-lower-third kf-swap-stage">
            <!-- 중앙 컴팩트 코어 블록 배지 -->
            <div class="kf-core-anchor-bar" @click="speakCoreBlock">
              <span class="anchor-badge">② Core Action Block</span>
              <span class="anchor-en">{{ currentScene.blocks[1]?.en || currentScene.keyVocab }}</span>
              <span class="anchor-hint">🔊 Tap to Listen</span>
            </div>

            <!-- 3가지 시작 블록 갈아 끼우기 카드 목록 (초대형 중앙 정렬 레고 블록) -->
            <div class="kf-combo-grid">
              <div
                v-for="(combo, cIdx) in currentScene.combos"
                :key="cIdx"
                class="kf-combo-card"
                :class="{ active: activeComboIdx === cIdx }"
                @click="playComboCard(cIdx)"
              >
                <div class="combo-sentence">
                  <span class="combo-block-pill c-bb">{{ combo.bbEn }}</span>
                  <span class="combo-block-pill c-core">{{ getComboCoreBlock(combo) }}</span>
                  <span v-if="getComboDetailBlock(combo)" class="combo-block-pill c-db">{{ getComboDetailBlock(combo) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ============================================================
               STAGE 2: 실전 자석 합체 미션 (Magnet Snap Quiz)
               ============================================================ -->
          <div v-else-if="activeStage === 'quiz'" class="kf-lower-third kf-quiz-stage">
            <!-- 1) 퀴즈형 미션 배너 (정답 직접 노출 대신 빈칸 챌린지 + 핵심 단서 제공) -->
            <div class="kf-mission-banner" @click="playMissionAudio">
              <span class="m-badge">🎯 MISSION</span>
              <span class="m-text">
                Snap: <strong class="m-puzzle">[ ? ] + [ ? ] + "{{ currentScene.blocks[2]?.en || '...' }}"</strong>
                <span class="m-clue">💡 Clue: <strong>{{ currentScene.keyVocab }}</strong></span>
              </span>
              <span class="m-listen">🔊 Listen</span>
            </div>

            <!-- 2) 자석 결합 타겟 슬롯 (블록별 화사한 테마 컬러 & 겹침 방지 여백) -->
            <div class="kf-snap-target-row" :class="{ snapped: isSnapped }">
              <div
                class="snap-slot slot-bb"
                :class="{ 'is-filled': isSnapped || pickedBb }"
                title="Click to reset"
                @click="clearPicked('bb')"
              >
                <span class="slot-badge">① 1st Block</span>
                <span class="slot-word" :class="{ 'is-qmark': !isSnapped && !pickedBb }">
                  {{ isSnapped ? currentScene.blocks[0].en : (pickedBb || '?') }}
                </span>
              </div>
              <span class="snap-plus">+</span>
              <div
                class="snap-slot slot-core"
                :class="{ 'is-filled': isSnapped || pickedCore }"
                title="Click to reset"
                @click="clearPicked('core')"
              >
                <span class="slot-badge">② Core Action</span>
                <span class="slot-word" :class="{ 'is-qmark': !isSnapped && !pickedCore }">
                  {{ isSnapped ? currentScene.blocks[1].en : (pickedCore || '?') }}
                </span>
              </div>
              <span class="snap-plus">+</span>
              <div class="snap-slot slot-db" :class="{ 'is-filled': isSnapped }">
                <span class="slot-badge">③ Detail Block</span>
                <span class="slot-word">{{ currentScene.blocks[2]?.en || '...' }}</span>
              </div>
            </div>

            <!-- 3) 후보 블록 풀 (알록달록 산뜻한 레고 컬러 테마) -->
            <div class="kf-candidate-pool">
              <!-- 행 1: 1st Starter Block 후보 -->
              <div class="cand-row row-bb">
                <div class="cand-badge-col">
                  <span class="cand-sec-badge badge-bb">① 1st Block</span>
                </div>
                <div class="cand-items">
                  <button
                    v-for="(opt, oIdx) in (currentQuizBbCandidates.length ? currentQuizBbCandidates : currentScene.quizPool.bbCandidates)"
                    :key="opt"
                    type="button"
                    class="cand-btn cand-bb"
                    :class="{
                      selected: pickedBb === opt,
                      correct: isSnapped && opt === currentScene.blocks[0].en
                    }"
                    @click="onPickCandidate('bb', opt)"
                  >
                    {{ opt }}
                  </button>
                </div>
              </div>

              <!-- 행 2: Core Action Block 후보 -->
              <div class="cand-row row-core">
                <div class="cand-badge-col">
                  <span class="cand-sec-badge badge-core">② Core Action</span>
                </div>
                <div class="cand-items">
                  <button
                    v-for="(opt, oIdx) in (currentQuizCoreCandidates.length ? currentQuizCoreCandidates : currentScene.quizPool.coreCandidates)"
                    :key="opt"
                    type="button"
                    class="cand-btn cand-core"
                    :class="{
                      selected: pickedCore === opt,
                      correct: isSnapped && opt === currentScene.blocks[1].en
                    }"
                    @click="onPickCandidate('core', opt)"
                  >
                    {{ opt }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- ============================================================
               STAGE 3: 완성 문장 따라하기 (Full 3-Block Sentence Standard)
               ============================================================ -->
          <div v-else class="kf-lower-third kf-sentence-stage">
            <!-- 소리 블록 3단 캡슐 (대형 모바일 폰트 지원) -->
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
                    {{ blk.role === 'bb' ? '① 1st Block' : blk.role === 'core' ? '② Core Action' : '③ Detail Block' }}
                  </span>
                  </div>
                <div class="gblk-en">{{ blk.en }}</div>
              </div>
            </div>

            <!-- 완성 문장 바 (군더더기 없이 크고 시원한 원라인 완성 문장) -->
            <div class="kf-sentence-banner" @click="speakSceneSentence(1.0)">
              <div class="kf-main-en">
                <span class="play-hint-icon">🔊</span>
                {{ currentScene.fullEn }}
              </div>
            </div>
          </div>
        </div>

        <!-- ----------------------------------------------------
             CASE C: OUTRO 슬라이드 (전체 복습 & 구독 유도)
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
              <span class="outro-badge">🎉 MISSION COMPLETE · Master All Sound Blocks</span>
              <h2 class="outro-title">{{ currentEpisode.title }} · Full Review</h2>
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
                </div>
              </div>
            </div>

            <div class="kf-outro-footer">
              <div class="outro-cta-box">
                <img :src="withBase('/images/kfood/channel-logo.jpg')" alt="Logo" class="kf-mini-logo" />
                <div>
                  <strong>Subscribe &amp; Like</strong> to cook more delicious K-food in easy English!
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
          <button type="button" class="rem-btn" @click="prevSlide">◀ Prev</button>
          <button
            type="button"
            class="rem-btn rem-primary"
            :class="{ playing: isAutoPlaying }"
            @click="toggleAutoShow"
          >
            {{ isAutoPlaying ? '⏹️ Stop Broadcast' : '▶️ Start Full Auto Broadcast' }}
          </button>
          <button type="button" class="rem-btn" @click="playCurrentSlideSequence">🔁 Play Scene</button>
          <button type="button" class="rem-btn" @click="nextSlide">Next ▶</button>
          <button
            type="button"
            class="rem-btn rem-rec"
            :class="{ recording: isScreenRecording }"
            @click="toggleScreenRecording"
          >
            {{ isScreenRecording ? `⏹️ Stop (${formatRecordTime})` : '🔴 Record 1080p' }}
          </button>
          
          <button v-if="isFullscreenMode" type="button" class="rem-btn rem-exit" @click="exitFullscreen">
            ✕ Exit
          </button>
        </div>
      </div>
    </div>

    <!-- 하단 플레이어 & 녹음 컨트롤 바 -->
    <div v-if="!isFullscreenMode" class="kf-controls-panel">
      <!-- 🔴 스튜디오 원클릭 자체 비디오 녹화 패널 -->
      <div class="kf-studio-recorder-box">
        <div class="srec-info">
          <div class="srec-title">
            <span class="srec-icon">🎥</span>
            <strong>Studio 1-Click Video Recording (Clean Digital Audio · 1080p Full HD)</strong>
          </div>
          <p class="srec-desc">
            별도 프로그램 설치 없이, 브라우저가 화면과 AI 성우 목소리를 내부에서 다이렉트로 캡처해 고화질 비디오 파일(<code>.mp4</code>/<code>.webm</code>)로 자동 다운로드해 줍니다. (공유 창에서 '탭 오디오 공유'를 선택하세요)
          </p>
        </div>
        <div class="srec-options">
          <label class="kf-rec-mic-label">
            <input v-model="includeMicInRecording" type="checkbox" />
            🎙️ <strong>Include Microphone Audio</strong> (Mixed with AI voice if checked)
          </label>
        </div>
        <button
          type="button"
          class="kf-ctrl-btn kf-btn-studio-rec"
          :class="{ 'is-rec-active': isScreenRecording }"
          @click="toggleScreenRecording"
        >
          {{ isScreenRecording ? `⏹️ Stop & Download Video (${formatRecordTime})` : '🔴 Start 1080p Video Recording' }}
        </button>
      </div>

      <div class="kf-nav-group">
        <button type="button" class="kf-ctrl-btn" @click="goToSlide(-1)">🎬 Intro</button>
        <button type="button" class="kf-ctrl-btn" @click="prevSlide">◀ Prev</button>

        <button
          type="button"
          class="kf-ctrl-btn kf-btn-broadcast"
          :class="{ 'kf-btn-playing': isAutoPlaying }"
          @click="toggleAutoShow"
        >
          {{ isAutoPlaying ? '⏹️ Stop Auto Broadcast' : '▶️ Full Auto Broadcast (Swap → Snap → Your Turn)' }}
        </button>

        <button type="button" class="kf-ctrl-btn kf-btn-step" @click="playCurrentSlideSequence">
          🔁 Play Scene Sequence
        </button>

        <button type="button" class="kf-ctrl-btn kf-btn-primary" @click="speakSceneSentence(1.0)">
          🔊 Sentence Only (1.0x)
        </button>

        <button type="button" class="kf-ctrl-btn" @click="nextSlide">Next ▶</button>
        <button type="button" class="kf-ctrl-btn" @click="goToSlide(currentEpisode.scenes.length)">
          🏁 Outro
        </button>
      </div>

      <!-- 방송 연출 세부 옵션 (효과음, 한국어 코칭 음성, 따라 말하기 타이머, 사진 업로드) -->
      <div v-if="!isCleanMode" class="kf-extra-tools">
        <div class="kf-custom-tools">
          <label class="kf-chk">
            <input v-model="enableKoreanCoachVoice" type="checkbox" /> 🗣️ English Coach & Mission Voice
          </label>
          <label class="kf-chk">
            <input v-model="enableSoundEffects" type="checkbox" /> 🔔 Sound Effects
          </label>
          <label class="kf-chk">
            <input v-model="includeShadowingPause" type="checkbox" /> 🎤 YOUR TURN (4s) Pause
          </label>
          <label class="kf-chk">
            <input v-model="showCoachBubble" type="checkbox" /> 💡 Coaching Banner
          </label>

        </div>

        <div class="kf-voice-recorder">
          <label v-if="slideCursor >= 0 && slideCursor < currentEpisode.scenes.length" class="kf-upload-label">
            📷 Custom Image
            <input type="file" accept="image/*" hidden @change="onUploadSceneImage" />
          </label>
          <button
            type="button"
            class="kf-ctrl-btn"
            :class="{ 'kf-btn-rec': isRecording }"
            @click="toggleRecording"
          >
            {{ isRecording ? '⏹️ Stop Test' : '🎙️ Test Mic' }}
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
          <span>📋 <strong>{{ currentEpisode.title }}</strong> · YouTube Upload Package (Title, Description, Pinned Comment &amp; Tags)</span>
          <span class="kf-toggle-arrow">{{ showYtMeta ? '▲ Collapse' : '▼ Expand' }}</span>
        </div>
        <div v-if="showYtMeta" class="kf-yt-package-body">
          <div class="kf-meta-row">
            <div class="kf-meta-header-row">
              <strong>1. Video Title:</strong>
              <button type="button" class="kf-copy-mini-btn" @click="copySingleItem('title', currentEpisode.ytTitle)">
                {{ copiedField === 'title' ? '✅ Copied' : '📋 Copy Title' }}
              </button>
            </div>
            <code>{{ currentEpisode.ytTitle }}</code>
          </div>

          <div class="kf-meta-row">
            <div class="kf-meta-header-row">
              <strong>2. Thumbnail Text &amp; Image:</strong>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <button type="button" class="kf-copy-mini-btn" @click="copySingleItem('thumbText', currentEpisode.thumbnailText)">
                  {{ copiedField === 'thumbText' ? '✅ Copied' : '📋 Copy Text' }}
                </button>
                <a
                  :href="withBase(currentEpisode.thumbnailImage || '/images/kfood/ep1-thumb.jpg')"
                  :download="`${currentEpisode.id}-thumb.jpg`"
                  target="_blank"
                  class="kf-ctrl-btn-sm"
                  style="display: inline-flex; align-items: center; gap: 0.35rem; text-decoration: none;"
                >
                  🖼️ Download 1080p Thumbnail (.jpg)
                </a>
              </div>
            </div>
            <code>{{ currentEpisode.thumbnailText }}</code>
          </div>

          <div class="kf-meta-row">
            <div class="kf-meta-header-row">
              <strong>3. Pinned Comment:</strong>
              <button type="button" class="kf-copy-mini-btn" @click="copySingleItem('pinned', currentPinnedComment)">
                {{ copiedField === 'pinned' ? '✅ Copied' : '📋 Copy Pinned Comment' }}
              </button>
            </div>
            <pre class="kf-code-block">{{ currentPinnedComment }}</pre>
          </div>

          <div class="kf-meta-row">
            <div class="kf-meta-header-row">
              <strong>4. Description &amp; Timestamps (Video Details):</strong>
              <button type="button" class="kf-copy-mini-btn" @click="copySingleItem('desc', currentDescriptionText)">
                {{ copiedField === 'desc' ? '✅ Copied' : '📋 Copy Description & Details' }}
              </button>
            </div>
            <textarea
              class="kf-desc-textarea"
              readonly
              :value="currentDescriptionText"
              rows="8"
            ></textarea>
          </div>

          <div class="kf-meta-row">
            <div class="kf-meta-header-row">
              <strong>5. Video Tags (500 chars):</strong>
              <button type="button" class="kf-copy-mini-btn" @click="copySingleItem('tags', getEpisodeTags(currentEpisode))">
                {{ copiedField === 'tags' ? '✅ Copied' : '📋 Copy Tags' }}
              </button>
            </div>
            <code>{{ getEpisodeTags(currentEpisode) }}</code>
          </div>

          <div class="kf-meta-row kf-meta-row-actions">
            <strong>Full Package:</strong>
            <button type="button" class="kf-ctrl-btn-sm" @click="copyEpisodeScript">
              {{ copySuccess ? '✅ Copied All to Clipboard!' : '📄 Copy 100% English Upload Package' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { withBase } from 'vitepress'

interface SoundBlockPiece {
  role: 'bb' | 'core' | 'db'
  en: string
  pron: string
}

interface SwapCombo {
  bbEn: string
  fullEn: string
  fullPron: string
  ko: string
}

interface QuizPool {
  bbCandidates: string[]
  coreCandidates: string[]
}

interface CookingScene {
  stepTitle: string
  visualEmojis: string
  imagePath?: string
  actionNote: string
  coachKo?: string
  coachEn?: string
  missionKo?: string
  missionEn?: string
  keyVocab: string
  bgGradient: string
  blocks: SoundBlockPiece[]
  combos: SwapCombo[]
  quizPool: QuizPool
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
  thumbnailImage?: string
  introNarrationKo: string
  outroNarrationKo: string
  scenes: CookingScene[]
}

const studioRoot = ref<HTMLElement | null>(null)
const aspectRatio = ref<'16:9' | '9:16'>('16:9')
const isCleanMode = ref(false)
const isFullscreenMode = ref(false)
const showFloatingControls = ref(true)

// 🌟 글자 크기 모드: 초대형(왕글씨, 'huge')을 기본값으로 설정 & 새로고침 시에도 유지되도록 localStorage 연동
const fontScale = ref<'normal' | 'large' | 'huge'>('huge')

const fontScaleLabel = computed(() => {
  if (fontScale.value === 'huge') return '👑 초대형(왕글씨)'
  if (fontScale.value === 'large') return '📱 대형'
  return '🖥️ 보통'
})

function cycleFontScale() {
  if (fontScale.value === 'huge') fontScale.value = 'normal'
  else if (fontScale.value === 'normal') fontScale.value = 'large'
  else fontScale.value = 'huge'
}

watch(fontScale, (val) => {
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem('soundblock_font_scale', val)
    } catch {}
  }
})

const enableKoreanCoachVoice = ref(true)
const enableSoundEffects = ref(true)
const includeShadowingPause = ref(true)
const showCoachBubble = ref(true)
const showPronGuide = ref(true)
const showKoSub = ref(false)
const showYtMeta = ref(false)
const copySuccess = ref(false)

// 자체 비디오 녹화기 상태 (마이크 잡음 0% 내부 사운드 직통 녹화)
const isScreenRecording = ref(false)
const countdownToRecord = ref<number | null>(null)
const includeMicInRecording = ref(false) // 기본값 true: 대표님 마이크 목소리 + 컴퓨터 사운드 동시 녹음
let activeMicStream: MediaStream | null = null
let mixerAudioCtx: AudioContext | null = null
const screenRecordSeconds = ref(0)
let screenMediaRecorder: MediaRecorder | null = null
let screenVideoChunks: Blob[] = []
let screenRecordTimer: number | null = null
let activeDisplayStream: MediaStream | null = null

const formatRecordTime = computed(() => {
  const m = Math.floor(screenRecordSeconds.value / 60)
  const s = screenRecordSeconds.value % 60
  return `${m < 10 ? '0' + m : m}:${s < 10 ? '0' + s : s}`
})

async function startScreenRecording() {
  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getDisplayMedia) {
    alert('이 브라우저에서는 화면 및 내부 오디오 녹화 기능을 지원하지 않습니다. Chrome 또는 Edge 브라우저를 권장합니다.')
    return
  }

  // 🚀 1) 사용자가 버튼을 클릭한 즉시 브라우저 사용자 제스처(User Gesture)로 전체 화면 모드 자동 진입!
  // (창모드에서 녹화 시 글자가 짤리거나 2px 오차가 생기는 문제를 방지하고 1080p Full HD 전체 화면으로 캡처 준비)
  await enterFullscreen()
  // 브라우저 뷰포트가 1920x1080 전체 화면으로 완전 리사이즈/안착될 시간을 줍니다.
  await new Promise((resolve) => setTimeout(resolve, 350))

  try {
    // 2) 1920x1080 전체 화면 상태에서 탭 공유 다이얼로그 호출
    const displayStream = await navigator.mediaDevices.getDisplayMedia({
      video: {
        displaySurface: 'browser',
        frameRate: 60,
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: {
        suppressLocalAudioPlayback: false
      },
      preferCurrentTab: true,
      selfBrowserSurface: 'include',
      systemAudio: 'include'
    } as any)

    // 💡 오디오 트랙 유무 검사 (소리 없이 녹화되는 사고 방지)
    const audioTracks = displayStream.getAudioTracks()
    if (audioTracks.length === 0) {
      alert(
        '⚠️ 오디오(소리) 트랙이 감지되지 않았습니다!\n\n' +
        '화면 공유 선택 창에서:\n' +
        '1. 반드시 [Chrome 탭]을 선택해주세요 (창이나 전체 화면 X).\n' +
        '2. 하단의 [탭 오디오도 공유 (Also share tab audio)] 체크박스를 꼭 체크해주세요!'
      )
      displayStream.getTracks().forEach((track) => track.stop())
      await exitFullscreen()
      return
    }

    activeDisplayStream = displayStream

    let recordStream: MediaStream = displayStream

    // 2) 대표님 마이크 목소리도 함께 믹싱할 경우 (Web Audio API 활용)
    if (includeMicInRecording.value && navigator.mediaDevices?.getUserMedia) {
      try {
        const micStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        })
        activeMicStream = micStream

        const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
        mixerAudioCtx = new AudioCtxClass()
        const destination = mixerAudioCtx.createMediaStreamDestination()

        // 탭 내부 사운드 오디오 노드
        const displayAudioTrack = displayStream.getAudioTracks()[0]
        if (displayAudioTrack) {
          const displaySource = mixerAudioCtx.createMediaStreamSource(new MediaStream([displayAudioTrack]))
          displaySource.connect(destination)
        }

        // 마이크 오디오 노드 (대표님 목소리)
        const micAudioTrack = micStream.getAudioTracks()[0]
        if (micAudioTrack) {
          const micSource = mixerAudioCtx.createMediaStreamSource(new MediaStream([micAudioTrack]))
          const micGain = mixerAudioCtx.createGain()
          micGain.gain.value = 1.05 // 대표님 목소리 시원하게 송출
          micSource.connect(micGain)
          micGain.connect(destination)
        }

        // 화면 비디오 + 믹싱된 오디오 결합
        const combinedTracks = [
          ...displayStream.getVideoTracks(),
          ...destination.stream.getAudioTracks()
        ]
        recordStream = new MediaStream(combinedTracks)
      } catch (micErr) {
        console.warn('Microphone access denied or not available, recording tab audio only:', micErr)
      }
    }

    screenVideoChunks = []

    const mimeTypes = [
      'video/mp4;codecs=avc1,mp4a',
      'video/mp4',
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm'
    ]
    let selectedMime = ''
    for (const m of mimeTypes) {
      if (MediaRecorder.isTypeSupported(m)) {
        selectedMime = m
        break
      }
    }

    const options: MediaRecorderOptions = selectedMime
      ? { mimeType: selectedMime, videoBitsPerSecond: 8000000 }
      : { videoBitsPerSecond: 8000000 }

    screenMediaRecorder = new MediaRecorder(recordStream, options)

    screenMediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        screenVideoChunks.push(e.data)
      }
    }

    screenMediaRecorder.onstop = () => {
      const ext = selectedMime.includes('mp4') ? 'mp4' : 'webm'
      const blob = new Blob(screenVideoChunks, { type: selectedMime || 'video/webm' })
      const url = URL.createObjectURL(blob)

      // 파일명 자동 생성: [SoundBlock-KCooking]-EP01-Kimchi-Stew-1080p.mp4
      const filename = `[SoundBlock-KCooking]-${currentEpisode.value.epNumber}-${currentEpisode.value.id}-1080p.${ext}`

      // 자동 다운로드 트리거
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)

      // 스트림 및 믹서 정리
      if (activeDisplayStream) {
        activeDisplayStream.getTracks().forEach((track) => track.stop())
        activeDisplayStream = null
      }
      if (activeMicStream) {
        activeMicStream.getTracks().forEach((track) => track.stop())
        activeMicStream = null
      }
      if (mixerAudioCtx) {
        mixerAudioCtx.close().catch(() => {})
        mixerAudioCtx = null
      }
      if (screenRecordTimer !== null) {
        window.clearInterval(screenRecordTimer)
        screenRecordTimer = null
      }
      isScreenRecording.value = false
      // 녹화 파일 다운로드 완료 후 전체 화면 해제하여 편리하게 원래 화면으로 복귀
      exitFullscreen().catch(() => {})
    }

    displayStream.getVideoTracks()[0].onended = () => {
      if (isScreenRecording.value) {
        stopScreenRecording()
      }
    }

    // 💡 창 공유 선택 직후: 1) 풀스크린 모드 자동 즉시 복원!
    await enterFullscreen()

    // 💡 2) 4초 카운트다운 (전체화면이 완전하게 자리잡고 사용자가 준비할 수 있는 여유 시간 제공)
    countdownToRecord.value = 4
    playTransitionChime()

    for (let c = 4; c >= 1; c--) {
      countdownToRecord.value = c
      playTone(440 + (4 - c) * 70, 120, 'sine', 0.12, 0)
      await new Promise((resolve) => setTimeout(resolve, 950))
    }
    // 💡 카운트다운 오버레이 완전 제거
    countdownToRecord.value = null

    // 💡 오버레이 페이드아웃 및 '1' 잔상이 100% 사라지고 깨끗한 인트로 화면이 정착할 수 있도록 1.2초간 지연 대기
    // (녹화 첫머리에 '1'이 남아 수동으로 잘라내야 했던 문제를 원천 차단)
    await new Promise((resolve) => setTimeout(resolve, 1200))

    // 💡 3) 풀스크린이 완벽히 안착되고 화면이 100% 깨끗해진 상태에서 실제 녹화 시작!
    playSuccessBell()
    screenMediaRecorder.start(1000)
    isScreenRecording.value = true
    screenRecordSeconds.value = 0
    screenRecordTimer = window.setInterval(() => {
      screenRecordSeconds.value++
    }, 1000)

    // 💡 4) 녹화 시작과 동시에 전체 자동 방송 자동 출발 (원클릭 완성)
    if (!isAutoPlaying.value) {
      if (slideCursor.value >= currentEpisode.value.scenes.length) {
        slideCursor.value = -1
      }
      toggleAutoShow()
    }
  } catch (err) {
    console.error('Screen recording cancelled or failed:', err)
    isScreenRecording.value = false
    await exitFullscreen()
  }
}

function stopScreenRecording() {
  if (screenMediaRecorder && screenMediaRecorder.state !== 'inactive') {
    screenMediaRecorder.stop()
  }
}

function toggleScreenRecording() {
  if (isScreenRecording.value) {
    stopScreenRecording()
  } else {
    startScreenRecording()
  }
}

const isShadowingTurn = ref(false)
const shadowingProgress = ref(0)

// 훈련 단계: 'swap' (시작 블록 3단 교체) | 'quiz' (실전 자석 합체) | 'sentence' (완성 문장)
const activeStage = ref<'swap' | 'quiz' | 'sentence'>('swap')
const activeComboIdx = ref<number | null>(null)
const isSnapped = ref(false)
const pickedBb = ref<string | null>(null)
const pickedCore = ref<string | null>(null)

// slideCursor: -1 = INTRO, 0..(scenes.length-1) = SCENES, scenes.length = OUTRO
const slideCursor = ref(-1)

const episodes: CookingEpisode[] = [
  // ==========================================
  // EP 1. 김치찌개 (Kimchi Stew) - 8 Scenes
  // ==========================================
  {
    id: 'kimchi-stew',
    epNumber: 'EP.01',
    emoji: '🍲',
    shortTitle: '🍲 Kimchi Stew',
    title: 'How to Cook Authentic Kimchi Stew',
    ytTitle: 'How to Cook Authentic Kimchi Stew in Easy English 🍲 | SoundBlock K-Cooking EP.01',
    thumbnailText: 'Cook Kimchi Stew in Easy English! [I\'m gonna] + [make Kimchi stew]',
    thumbnailImage: '/images/kfood/ep1-thumb.jpg',
    introNarrationKo: '안녕하세요, 소리블록 케이쿠킹입니다! 오늘은 한국인의 소울푸드 김치찌개 끓이는 법을 소리 블록 교체와 조립으로 마스터해 볼게요.',
    outroNarrationKo: '오늘 배운 김치찌개 소리 블록 조합 훈련, 입에 착 붙으셨나요? 구독과 좋아요를 누르고 다음 요리도 함께 조립해 봐요!',
    scenes: [
      {
        stepTitle: 'SCENE 1 · Introduction to Kimchi Stew',
        visualEmojis: '👨‍🍳 🍲 🇰🇷',
        imagePath: '/images/kfood/ep1-s1.jpg',
        actionNote: '앞치마를 입고 부엌에서 밝게 인사하는 오프닝',
        coachKo: '첫 번째 코어 블록은, 김치찌개를 만들다, 메익 김치 스튜입니다. 앞의 시작 블록만 세 번 갈아 끼워 볼까요?',
        coachEn: 'Our core action is \'make Kimchi stew\'. Let\'s swap the first block: I\'m gonna, I wanna, Do you wanna!',
        missionKo: '실전 조립 미션! 오늘 저는 김치찌개를 끓일 거예요. 블록 세 개를 합쳐 보세요!',
        missionEn: 'Snap Mission! \'I\'m gonna make Kimchi stew today.\' Snap the blocks together!',
        keyVocab: 'Kimchi stew',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'make Kimchi stew', pron: '메익 김치 스튜' },
          { role: 'db', en: 'today.', pron: '투데이' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna make Kimchi stew.", fullPron: '암거너 메익 김치 스튜', ko: '나 김치찌개 끓일 거야.' },
          { bbEn: 'I wanna', fullEn: 'I wanna make Kimchi stew.', fullPron: '아이 워너 메익 김치 스튜', ko: '나 김치찌개 끓이고 싶어.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna make Kimchi stew?', fullPron: '두유 워너 메익 김치 스튜?', ko: '너 김치찌개 끓일래?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'Did you'],
          coreCandidates: ['make Kimchi stew', 'slice the tofu', 'pour some water']
        },
        fullEn: "I'm gonna make Kimchi stew today.",
        fullPron: '암거너 + 메익 김치 스튜 + 투데이',
        fullKo: '오늘 저는 김치찌개를 끓일 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · Secret of Sour Kimchi',
        visualEmojis: '🥬 ✨ 😋',
        imagePath: '/images/kfood/ep1-s2.jpg',
        actionNote: '잘 익은 신김치를 보여주며 핵심 비법 설명',
        coachKo: '두 번째 코어 블록은, 신김치를 쓰다, 유즈 사워 김치입니다. 시작 블록을 바꿔서 조합해 보세요!',
        coachEn: 'Our core action is \'use sour kimchi\'. For deep flavor, sour kimchi is a must!',
        missionKo: '실전 조립 미션! 깊은 맛을 내려면 꼭 신김치를 써야 해요. 어떻게 조립할까요?',
        missionEn: 'Snap Mission! \'You have to use sour kimchi for deep flavor.\' Which blocks snap together?',
        keyVocab: 'sour kimchi',
        bgGradient: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해프터' },
          { role: 'core', en: 'use sour kimchi', pron: '유즈 사워 김치' },
          { role: 'db', en: 'for deep flavor.', pron: '포 딥 플레이버' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to use sour kimchi.', fullPron: '유 해프터 유즈 사워 김치', ko: '꼭 신김치를 써야만 해.' },
          { bbEn: "We're gonna", fullEn: "We're gonna use sour kimchi.", fullPron: '워거너 유즈 사워 김치', ko: '우리 신김치를 쓸 거야.' },
          { bbEn: 'Did you', fullEn: 'Did you use sour kimchi?', fullPron: '디쥬 유즈 사워 김치?', ko: '너 신김치 썼어?' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'll", 'Do you wanna'],
          coreCandidates: ['use sour kimchi', 'chop the pork', 'fry them together']
        },
        fullEn: 'You have to use sour kimchi for deep flavor.',
        fullPron: '유 해프터 + 유즈 사워 김치 + 포 딥 플레이버',
        fullKo: '깊은 맛을 내려면 꼭 신김치를 써야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · Chop the Pork & Kimchi',
        visualEmojis: '🔪 🥩 🥬',
        imagePath: '/images/kfood/ep1-s3.jpg',
        actionNote: '도마 위에서 김치와 돼지고기를 한 입 크기로 큼직하게 썰기',
        coachKo: '세 번째 코어 블록은, 고기와 김치를 큼직하게 썰다, 찹 더 포크 앤 김치입니다. 시작 블록 세 개를 끼워 볼게요!',
        coachEn: 'Our core action is \'chop the pork and kimchi\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 돼지고기와 김치를 한 입 크기로 썰어 줄게요!',
        missionEn: 'Snap Mission! \'I\'m gonna chop the pork and kimchi into bite-sized pieces.\' Assemble the blocks!',
        keyVocab: 'chop the pork and kimchi',
        bgGradient: 'linear-gradient(135deg, #431407 0%, #7c2d12 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'chop the pork and kimchi', pron: '찹 더 포크 앤 김치' },
          { role: 'db', en: 'into bite-sized pieces.', pron: '인투 바잇-사이즈드 피시즈' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna chop the pork and kimchi.", fullPron: '암거너 찹 더 포크 앤 김치', ko: '돼지고기와 김치를 썰어 줄게.' },
          { bbEn: "I'll", fullEn: "I'll chop the pork and kimchi.", fullPron: '아을 찹 더 포크 앤 김치', ko: '내가 돼지고기와 김치 썰어 놓을게.' },
          { bbEn: "You don't have to", fullEn: "You don't have to chop the pork and kimchi.", fullPron: '유 돈 해프터 찹 더 포크 앤 김치', ko: '너 돼지고기랑 김치 안 썰어도 돼.' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", "We're gonna", 'Can you'],
          coreCandidates: ['chop the pork and kimchi', 'bring it to the boil', 'take a sip']
        },
        fullEn: "I'm gonna chop the pork and kimchi into bite-sized pieces.",
        fullPron: '암거너 + 찹 더 포크 앤 김치 + 인투 바잇-사이즈드 피시즈',
        fullKo: '돼지고기와 김치를 한 입 크기로 썰어 줄게요.'
      },
      {
        stepTitle: 'SCENE 4 · Slice the Tofu & Green Onion',
        visualEmojis: '⬜ 🌱 🔪',
        imagePath: '/images/kfood/ep1-s4.jpg',
        actionNote: '두부는 납작하게 썰고(slice), 대파는 송송 썰어 준비',
        coachKo: '네 번째 코어 블록은, 두부를 납작하게 썰다, 슬라이스 더 토푸입니다. 앞 블록만 바꾸면 뜻이 어떻게 달라질까요?',
        coachEn: 'Our core action is \'slice the tofu\'. Let\'s swap the first block to change the meaning!',
        missionKo: '실전 조립 미션! 제가 두부는 납작하게 썰고 대파도 썰어 둘게요!',
        missionEn: 'Snap Mission! \'I\'ll slice the tofu and chop the green onion.\' Snap the blocks!',
        keyVocab: 'slice the tofu',
        bgGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'slice the tofu', pron: '슬라이스 더 토푸' },
          { role: 'db', en: 'and chop the green onion.', pron: '앤 찹 더 그린 어니언' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll slice the tofu.", fullPron: '아을 슬라이스 더 토푸', ko: '내가 두부 썰어 놓을게.' },
          { bbEn: "You don't have to", fullEn: "You don't have to slice the tofu.", fullPron: '유 돈 해프터 슬라이스 더 토푸', ko: '너 두부 썰 필요 없어.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna slice the tofu?', fullPron: '두유 워너 슬라이스 더 토푸?', ko: '너 두부 좀 썰어 볼래?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", 'We have to', 'I used to'],
          coreCandidates: ['slice the tofu', 'use sour kimchi', 'pour some water']
        },
        fullEn: "I'll slice the tofu and chop the green onion.",
        fullPron: '아을 + 슬라이스 더 토푸 + 앤 찹 더 그린 어니언',
        fullKo: '제가 두부는 납작하게 썰고 대파도 썰어 둘게요.'
      },
      {
        stepTitle: 'SCENE 5 · Fry Pork & Kimchi Together',
        visualEmojis: '🍲 🔥 🧄',
        imagePath: '/images/kfood/ep1-s5.jpg',
        actionNote: '달궈진 냄비에 돼지고기, 김치, 다진 마늘을 넣고 지글지글 볶기',
        coachKo: '다섯 번째 코어 블록은, 재료들을 함께 볶다, 프라이 뎀 투게더입니다. 시작 블록 세 가지를 결합해 볼까요?',
        coachEn: 'Our core action is \'fry them together\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 다진 마늘을 넣고 재료들을 함께 볶아 줘야 해요!',
        missionEn: 'Snap Mission! \'We have to fry them together with minced garlic.\' Assemble the blocks!',
        keyVocab: 'fry them together',
        bgGradient: 'linear-gradient(135deg, #422006 0%, #713f12 100%)',
        blocks: [
          { role: 'bb', en: 'We have to', pron: '위 해프터' },
          { role: 'core', en: 'fry them together', pron: '프라이 뎀 투게더' },
          { role: 'db', en: 'with minced garlic.', pron: '위드 민스트 갈릭' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to fry them together.', fullPron: '위 해프터 프라이 뎀 투게더', ko: '재료들을 같이 볶아야 해.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna fry them together.", fullPron: '암거너 프라이 뎀 투게더', ko: '재료들을 같이 볶아 줄게.' },
          { bbEn: 'I used to', fullEn: 'I used to fry them together.', fullPron: '아이 유스투 프라이 뎀 투게더', ko: '예전엔 같이 볶곤 했어.' }
        ],
        quizPool: {
          bbCandidates: ['We have to', "I'm gonna", 'Did you'],
          coreCandidates: ['fry them together', 'crack an egg', 'make Korean ramen']
        },
        fullEn: 'We have to fry them together with minced garlic.',
        fullPron: '위 해프터 + 프라이 뎀 투게더 + 위드 민스트 갈릭',
        fullKo: '다진 마늘을 넣고 재료들을 함께 볶아 줘야 해요.'
      },
      {
        stepTitle: 'SCENE 6 · Pour Water & Kimchi Juice',
        visualEmojis: '💧 🥣 🌶️',
        imagePath: '/images/kfood/ep1-s6.jpg',
        actionNote: '물을 붓고 감칠맛의 핵심인 김치 국물(kimchi juice) 한 국자 추가!',
        coachKo: '여섯 번째 코어 블록은, 물을 좀 붓다, 포어 썸 워러입니다. 시작 블록을 차례대로 갈아 끼워 보세요!',
        coachEn: 'Our core action is \'pour some water\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 물을 좀 붓고 김치 국물도 넣어 줄게요!',
        missionEn: 'Snap Mission! \'I\'m gonna pour some water and add the kimchi juice.\' Snap the blocks!',
        keyVocab: 'kimchi juice',
        bgGradient: 'linear-gradient(135deg, #172554 0%, #1e3a8a 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'pour some water', pron: '포어 썸 워러' },
          { role: 'db', en: 'and add the kimchi juice.', pron: '앤 애드 더 김치 주스' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna pour some water.", fullPron: '암거너 포어 썸 워러', ko: '물을 좀 부어 줄게요.' },
          { bbEn: "I'll", fullEn: "I'll pour some water.", fullPron: '아을 포어 썸 워러', ko: '내가 물 좀 부을게.' },
          { bbEn: 'Did you', fullEn: 'Did you pour some water?', fullPron: '디쥬 포어 썸 워러?', ko: '너 물 좀 부었어?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'I wanna'],
          coreCandidates: ['pour some water', 'slice the tofu', 'take a sip']
        },
        fullEn: "I'm gonna pour some water and add the kimchi juice.",
        fullPron: '암거너 + 포어 썸 워러 + 앤 애드 더 김치 주스',
        fullKo: '물을 좀 붓고 김치 국물도 넣어 줄게요.'
      },
      {
        stepTitle: 'SCENE 7 · Bring to Boil & Simmer',
        visualEmojis: '♨️ 🍲 ⏲️',
        imagePath: '/images/kfood/ep1-s7.jpg',
        actionNote: '센 불에 팔팔 끓인 뒤 중약불로 줄여 10분간 뭉근히 끓이기',
        coachKo: '일곱 번째 코어 블록은, 팔팔 끓이다, 브링 잇 투 더 보일입니다. 시작 블록 세 개와 조합해 볼게요!',
        coachEn: 'Our core action is \'bring it to the boil\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 팔팔 끓인 다음에 푹 끓게 둘 거예요!',
        missionEn: 'Snap Mission! \'We\'re gonna bring it to the boil and let it simmer.\' Let\'s snap!',
        keyVocab: 'bring it to the boil',
        bgGradient: 'linear-gradient(135deg, #4c0519 0%, #881337 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '워거너' },
          { role: 'core', en: 'bring it to the boil', pron: '브링 잇 투 더 보일' },
          { role: 'db', en: 'and let it simmer.', pron: '앤 레릿 시머' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna bring it to the boil.", fullPron: '워거너 브링 잇 투 더 보일', ko: '우린 팔팔 끓여 줄 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to bring it to the boil.', fullPron: '유 해프터 브링 잇 투 더 보일', ko: '센 불에 팔팔 끓여야만 해요.' },
          { bbEn: "I'll", fullEn: "I'll bring it to the boil.", fullPron: '아을 브링 잇 투 더 보일', ko: '내가 팔팔 끓여 놓을게.' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "You don't have to", 'Do you wanna'],
          coreCandidates: ['bring it to the boil', 'marinate the beef', 'fry them together']
        },
        fullEn: "We're gonna bring it to the boil and let it simmer.",
        fullPron: '워거너 + 브링 잇 투 더 보일 + 앤 레릿 시머',
        fullKo: '팔팔 끓인 다음에 푹(뭉근히) 끓게 둘 거예요.'
      },
      {
        stepTitle: 'SCENE 8 · Take a Sip & Taste',
        visualEmojis: '🥄 🍚 😍',
        imagePath: '/images/kfood/ep1-s8.jpg',
        actionNote: '국물 한 모금(take a sip) 맛보고 따뜻한 흰쌀밥과 한 입!',
        coachKo: '여덟 번째 코어 블록은, 국물 한 모금 마시다, 테이커 씹입니다. 시작 블록을 바꿔가며 말해 보세요!',
        coachEn: 'Our core action is \'take a sip\'. Let\'s swap the first block!',
        missionKo: '마지막 조립 미션! 지금 당장 국물 한 모금 마셔 보고 싶네요. 와, 진짜 맛있어요!',
        missionEn: 'Final Snap Mission! \'I wanna take a sip right now. Wow, so good!\' Snap the blocks!',
        keyVocab: 'take a sip',
        bgGradient: 'linear-gradient(135deg, #3b0764 0%, #581c87 100%)',
        blocks: [
          { role: 'bb', en: 'I wanna', pron: '아이 워너' },
          { role: 'core', en: 'take a sip', pron: '테이커 씹' },
          { role: 'db', en: 'right now. Wow, so good!', pron: '롸잇 나우. 와우 쏘 굿!' }
        ],
        combos: [
          { bbEn: 'I wanna', fullEn: 'I wanna take a sip.', fullPron: '아이 워너 테이커 씹', ko: '국물 한 모금 마셔 보고 싶어.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna take a sip?', fullPron: '두유 워너 테이커 씹?', ko: '국물 한 모금 맛볼래?' },
          { bbEn: "I'll", fullEn: "I'll take a sip.", fullPron: '아을 테이커 씹', ko: '내가 국물 한 모금 마셔 볼게.' }
        ],
        quizPool: {
          bbCandidates: ['I wanna', 'You have to', "We're gonna"],
          coreCandidates: ['take a sip', 'make Kimchi stew', 'boil the water']
        },
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
    shortTitle: '🍳 Kimchi Fried Rice',
    title: 'How to Make 5-Minute Kimchi Fried Rice',
    ytTitle: 'How to Make 5-Minute Kimchi Fried Rice in Easy English 🍳 | SoundBlock K-Cooking EP.02',
    thumbnailText: '5-Min Kimchi Fried Rice! [I\'ll] + [put a fried egg on top]',
    thumbnailImage: '/images/kfood/ep2-thumb.jpg',
    introNarrationKo: '안녕하세요, 소리블록 케이쿠킹입니다! 오늘은 5분 만에 뚝딱 만드는 김치볶음밥을 소리 블록 조합으로 말해 볼게요.',
    outroNarrationKo: '오늘 배운 김치볶음밥 소리 블록 조합 훈련도 정말 유익하셨죠? 구독과 좋아요 누르고 다음 영상에서 또 만나요!',
    scenes: [
      {
        stepTitle: 'SCENE 1 · Introduction to Kimchi Fried Rice',
        visualEmojis: '🍚 🥬 🍳',
        imagePath: '/images/kfood/ep1-s1.jpg',
        actionNote: '찬밥과 잘게 썬 김치를 준비하며 인사',
        coachKo: '첫 번째 코어 블록은, 김치볶음밥을 만들다, 메익 김치 프라이드 라이스입니다. 시작 블록 세 개를 갈아 끼워 볼까요?',
        coachEn: 'Our core action is \'make Kimchi fried rice\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 점심으로 김치볶음밥을 만들 거예요!',
        missionEn: 'Snap Mission! \'I\'m gonna make Kimchi fried rice for lunch.\' Snap the blocks!',
        keyVocab: 'Kimchi fried rice',
        bgGradient: 'linear-gradient(135deg, #431407 0%, #7c2d12 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'make Kimchi fried rice', pron: '메익 김치 프라이드 라이스' },
          { role: 'db', en: 'for lunch.', pron: '포 런치' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna make Kimchi fried rice.", fullPron: '암거너 메익 김치 프라이드 라이스', ko: '김치볶음밥을 만들 거야.' },
          { bbEn: 'I wanna', fullEn: 'I wanna make Kimchi fried rice.', fullPron: '아이 워너 메익 김치 프라이드 라이스', ko: '김치볶음밥 만들고 싶어.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna make Kimchi fried rice?', fullPron: '두유 워너 메익 김치 프라이드 라이스?', ko: '김치볶음밥 만들래?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'Did you'],
          coreCandidates: ['make Kimchi fried rice', 'marinate the beef', 'slice the tofu']
        },
        fullEn: "I'm gonna make Kimchi fried rice for lunch.",
        fullPron: '암거너 + 메익 김치 프라이드 라이스 + 포 런치',
        fullKo: '점심으로 김치볶음밥을 만들 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · Chop Kimchi Finely',
        visualEmojis: '🔪 🥓 🥬',
        imagePath: '/images/kfood/ep1-s3.jpg',
        actionNote: '볶음밥용으로 김치와 베이컨을 잘게 다지듯 썰기',
        coachKo: '두 번째 코어 블록은, 김치를 잘게 썰다, 찹 더 김치 파인리입니다. 앞 블록을 바꿔서 조합해 보세요!',
        coachEn: 'Our core action is \'chop the kimchi finely\'. Let\'s swap the starter block!',
        missionKo: '실전 조립 미션! 베이컨과 함께 김치를 잘게 썰어 줘야 해요!',
        missionEn: 'Snap Mission! \'You have to chop the kimchi finely for great texture.\' Assemble the blocks!',
        keyVocab: 'chop the kimchi finely',
        bgGradient: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해프터' },
          { role: 'core', en: 'chop the kimchi finely', pron: '찹 더 김치 파인리' },
          { role: 'db', en: 'with some bacon.', pron: '위드 썸 베이컨' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to chop the kimchi finely.', fullPron: '유 해프터 찹 더 김치 파인리', ko: '김치를 잘게 썰어야만 해.' },
          { bbEn: "I'll", fullEn: "I'll chop the kimchi finely.", fullPron: '아을 찹 더 김치 파인리', ko: '내가 김치 잘게 썰어 놓을게.' },
          { bbEn: "You don't have to", fullEn: "You don't have to chop the kimchi finely.", fullPron: '유 돈 해프터 찹 더 김치 파인리', ko: '김치 안 잘게 썰어도 돼.' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'm gonna", 'Can you'],
          coreCandidates: ['chop the kimchi finely', 'boil the water', 'take a bite']
        },
        fullEn: 'You have to chop the kimchi finely with some bacon.',
        fullPron: '유 해프터 + 찹 더 김치 파인리 + 위드 썸 베이컨',
        fullKo: '베이컨과 함께 김치를 잘게 썰어 줘야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · Stir-Fry with Gochujang',
        visualEmojis: '🍳 🔥 🌶️',
        imagePath: '/images/kfood/ep1-s5.jpg',
        actionNote: '팬에 김치와 고추장/간장을 넣고 센 불에 달달 볶기',
        coachKo: '세 번째 코어 블록은, 김치를 센 불에 볶다, 스터 프라이 더 김치입니다. 시작 블록 세 개와 결합해 볼게요!',
        coachEn: 'Our core action is \'cut the spam into small cubes\'. Let\'s swap the starter block!',
        missionKo: '실전 조립 미션! 고추장을 넣고 김치를 센 불에 볶을 거예요!',
        missionEn: 'Snap Mission! \'I\'ll cut the spam into small cubes.\' Let\'s snap!',
        keyVocab: 'stir-fry',
        bgGradient: 'linear-gradient(135deg, #422006 0%, #713f12 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '워거너' },
          { role: 'core', en: 'stir-fry the kimchi', pron: '스터-프라이 더 김치' },
          { role: 'db', en: 'with chili paste.', pron: '위드 칠리 페이스트' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna stir-fry the kimchi.", fullPron: '워거너 스터 프라이 더 김치', ko: '김치를 센 불에 볶을 거예요.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna stir-fry the kimchi.", fullPron: '암거너 스터 프라이 더 김치', ko: '내가 김치를 볶을게.' },
          { bbEn: 'You have to', fullEn: 'You have to stir-fry the kimchi.', fullPron: '유 해프터 스터 프라이 더 김치', ko: '김치를 센 불에 볶아야 해.' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'll", 'Did you'],
          coreCandidates: ['stir-fry the kimchi', 'pour some water', 'slice the tofu']
        },
        fullEn: "We're gonna stir-fry the kimchi with chili paste.",
        fullPron: '워거너 + 스터-프라이 더 김치 + 위드 칠리 페이스트',
        fullKo: '고추장을 넣고 김치를 센 불에 볶을 거예요.'
      },
      {
        stepTitle: 'SCENE 4 · Add Cold Rice & Sesame Oil',
        visualEmojis: '🍚 🫗 ✨',
        imagePath: '/images/kfood/ep1-s2.jpg',
        actionNote: '밥을 넣고 골고루 섞은 뒤 마지막에 고소한 참기름 한 바퀴!',
        coachKo: '네 번째 코어 블록은, 밥을 넣고 섞다, 믹스 인 더 라이스입니다. 앞 블록을 차례대로 갈아 끼워 보세요!',
        coachEn: 'Our core action is \'stir-fry the kimchi and spam\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 밥을 넣고 섞은 다음 참기름을 두를게요!',
        missionEn: 'Snap Mission! \'We have to stir-fry the kimchi and spam in cooking oil.\' Snap the blocks!',
        keyVocab: 'drizzle sesame oil',
        bgGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'mix in the rice', pron: '믹스 인 더 라이스' },
          { role: 'db', en: 'and add sesame oil.', pron: '앤 애드 세서미 오일' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll mix in the rice.", fullPron: '아을 믹스 인 더 라이스', ko: '내가 밥을 넣고 섞을게.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna mix in the rice.", fullPron: '암거너 믹스 인 더 라이스', ko: '밥을 넣고 섞어 줄게.' },
          { bbEn: 'Did you', fullEn: 'Did you mix in the rice?', fullPron: '디쥬 믹스 인 더 라이스?', ko: '밥 넣고 섞었어?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", 'We have to', 'Do you wanna'],
          coreCandidates: ['mix in the rice', 'put the soup base', 'cook the meat']
        },
        fullEn: "I'll mix in the rice and add sesame oil.",
        fullPron: '아을 + 믹스 인 더 라이스 + 앤 애드 세서미 오일',
        fullKo: '밥을 넣고 섞은 다음 참기름을 두를게요.'
      },
      {
        stepTitle: 'SCENE 5 · Put Fried Egg Right on Top',
        visualEmojis: '🥚 🍳 👑',
        imagePath: '/images/kfood/ep1-s7.jpg',
        actionNote: '노른자가 살아 있는 반숙 계란프라이를 맨 위에 얹기',
        coachKo: '다섯 번째 코어 블록은, 계란프라이를 올리다, 풋 어 프라이드 에그입니다. 시작 블록 세 개를 바꿔 볼까요?',
        coachEn: 'Our core action is \'add the cold rice\'. Let\'s swap the starter block!',
        missionKo: '실전 조립 미션! 맨 위에 계란프라이를 딱 얹어 줄 거예요!',
        missionEn: 'Snap Mission! \'I\'m gonna add the cold rice and break it down.\' Assemble the blocks!',
        keyVocab: 'put a fried egg on top',
        bgGradient: 'linear-gradient(135deg, #172554 0%, #1e3a8a 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'put a fried egg', pron: '풋 어 프라이드 에그' },
          { role: 'db', en: 'right on top.', pron: '롸잇 온 탑' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna put a fried egg.", fullPron: '암거너 풋 어 프라이드 에그', ko: '계란프라이를 올릴 거야.' },
          { bbEn: 'I wanna', fullEn: 'I wanna put a fried egg.', fullPron: '아이 워너 풋 어 프라이드 에그', ko: '계란프라이 올리고 싶어.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna put a fried egg?', fullPron: '두유 워너 풋 어 프라이드 에그?', ko: '계란프라이 올릴래?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", "I'll", 'You have to'],
          coreCandidates: ['put a fried egg', 'crack an egg', 'chop the pork']
        },
        fullEn: "I'm gonna put a fried egg right on top.",
        fullPron: '암거너 + 풋 어 프라이드 에그 + 롸잇 온 탑',
        fullKo: '맨 위에 계란프라이를 딱 얹어 줄 거예요.'
      },
      {
        stepTitle: 'SCENE 6 · Enjoy the Crispy Bottom',
        visualEmojis: '🥄 😋 👍',
        imagePath: '/images/kfood/ep1-s8.jpg',
        actionNote: '숟가락으로 노른자를 톡 터뜨려 밥과 함께 한 입!',
        coachKo: '여섯 번째 코어 블록은, 한 입 먹다, 테이커 바이트입니다. 시작 블록을 바꿔가며 말해 보세요!',
        coachEn: 'Our core action is \'drizzle some sesame oil\'. Let\'s swap the first block!',
        missionKo: '마지막 조립 미션! 지금 당장 한 입 먹어 볼래요?',
        missionEn: 'Snap Mission! \'You have to drizzle some sesame oil at the end.\' Let\'s snap!',
        keyVocab: 'enjoy the crispy bottom',
        bgGradient: 'linear-gradient(135deg, #3b0764 0%, #581c87 100%)',
        blocks: [
          { role: 'bb', en: 'Do you wanna', pron: '두유워너' },
          { role: 'core', en: 'take a bite', pron: '테이커 바이트' },
          { role: 'db', en: 'right now?', pron: '롸잇 나우?' }
        ],
        combos: [
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna take a bite?', fullPron: '두유 워너 테이커 바이트?', ko: '한 입 먹어 볼래?' },
          { bbEn: 'I wanna', fullEn: 'I wanna take a bite.', fullPron: '아이 워너 테이커 바이트', ko: '나 한 입 먹고 싶어.' },
          { bbEn: "I'll", fullEn: "I'll take a bite.", fullPron: '아을 테이커 바이트', ko: '내가 한 입 먹어 볼게.' }
        ],
        quizPool: {
          bbCandidates: ['Do you wanna', "I'm gonna", 'You have to'],
          coreCandidates: ['take a bite', 'take a sip', 'use sour kimchi']
        },
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
    shortTitle: '🍜 Korean Ramen',
    title: 'How to Cook Authentic Korean Ramen',
    ytTitle: 'How to Cook Authentic Korean Ramen in Easy English 🍜 | SoundBlock K-Cooking EP.03',
    thumbnailText: 'Cook K-Ramen Like a Pro! [You have to] + [put the soup base first]',
    thumbnailImage: '/images/kfood/ep3-thumb.jpg',
    introNarrationKo: '안녕하세요, 소리블록 케이쿠킹입니다! 오늘은 전 세계가 사랑하는 한국 라면 맛있게 끓이는 법을 소리 블록으로 배워 볼게요.',
    outroNarrationKo: '라면 끓이면서 혼자 영어로 중얼거려 보면 절대 안 까먹습니다! 구독과 좋아요 부탁드려요!',
    scenes: [
      {
        stepTitle: 'SCENE 1 · Late-Night Korean Ramen',
        visualEmojis: '🌙 🍜 🔥',
        imagePath: '/images/kfood/ep1-s1.jpg',
        actionNote: '냄비와 라면 한 봉지를 들고 시작',
        coachKo: '첫 번째 코어 블록은, 한국 라면을 끓이다, 메익 코리안 라면입니다. 시작 블록 세 개를 갈아 끼워 볼까요?',
        coachEn: 'Our core action is \'cook Korean ramen\'. Let\'s swap the starter block!',
        missionKo: '실전 조립 미션! 오늘 밤엔 한국 라면을 끓여 먹을 거예요!',
        missionEn: 'Snap Mission! \'I\'m gonna cook spicy Korean ramen for late-night snack.\' Snap the blocks!',
        keyVocab: 'cook Korean ramen',
        bgGradient: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'make Korean ramen', pron: '메익 코리안 라면' },
          { role: 'db', en: 'tonight.', pron: '투나잇' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna make Korean ramen.", fullPron: '암거너 메익 코리안 라면', ko: '한국 라면 끓일 거야.' },
          { bbEn: 'I wanna', fullEn: 'I wanna make Korean ramen.', fullPron: '아이 워너 메익 코리안 라면', ko: '한국 라면 끓이고 싶어.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna make Korean ramen?', fullPron: '두유 워너 메익 코리안 라면?', ko: '한국 라면 끓일래?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'First, we have to', 'Did you'],
          coreCandidates: ['make Korean ramen', 'slice the tofu', 'wrap the meat']
        },
        fullEn: "I'm gonna make Korean ramen tonight.",
        fullPron: '암거너 + 메익 코리안 라면 + 투나잇',
        fullKo: '오늘 밤엔 한국 라면을 끓여 먹을 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · Measure 550ml Water & Boil',
        visualEmojis: '💧 🍲 ♨️',
        imagePath: '/images/kfood/ep1-s6.jpg',
        actionNote: '냄비에 물 550ml를 붓고 센 불에 끓이기',
        coachKo: '두 번째 코어 블록은, 물을 끓이다, 보일 더 워러입니다. 시작 블록을 바꿔서 조합해 보세요!',
        coachEn: 'Our core action is \'measure 550 milliliters of water\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 먼저 작은 냄비에 물을 끓여야 해요!',
        missionEn: 'Snap Mission! \'You have to measure 550 milliliters of water exactly.\' Assemble the blocks!',
        keyVocab: 'measure 550ml water',
        bgGradient: 'linear-gradient(135deg, #172554 0%, #1e3a8a 100%)',
        blocks: [
          { role: 'bb', en: 'First, we have to', pron: '퍼스트, 위 해프터' },
          { role: 'core', en: 'boil the water', pron: '보일 더 워러' },
          { role: 'db', en: 'in a small pot.', pron: '인 어 스몰 팟' }
        ],
        combos: [
          { bbEn: 'First, we have to', fullEn: 'First, we have to boil the water.', fullPron: '퍼스트 위 해프터 보일 더 워러', ko: '먼저 물을 끓여야만 해.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna boil the water.", fullPron: '암거너 보일 더 워러', ko: '내가 물을 끓일게.' },
          { bbEn: 'Did you', fullEn: 'Did you boil the water?', fullPron: '디쥬 보일 더 워러?', ko: '너 물 끓였어?' }
        ],
        quizPool: {
          bbCandidates: ['First, we have to', "I'll", 'You have to'],
          coreCandidates: ['boil the water', 'fry them together', 'crack an egg']
        },
        fullEn: 'First, we have to boil the water in a small pot.',
        fullPron: '퍼스트, 위 해프터 + 보일 더 워러 + 인 어 스몰 팟',
        fullKo: '먼저 작은 냄비에 물을 끓여야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · Add Noodles & Soup Powder',
        visualEmojis: '🌶️ 🥣 💡',
        imagePath: '/images/kfood/ep1-s5.jpg',
        actionNote: '면보다 분말 스프를 먼저 넣는 한국식 꿀팁 설명',
        coachKo: '세 번째 코어 블록은, 라면 스프를 넣다, 풋 더 숩 베이스입니다. 시작 블록 세 개와 결합해 볼게요!',
        coachEn: 'Our core action is \'put the noodles and soup powder in\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 면보다 스프를 먼저 넣을게요!',
        missionEn: 'Snap Mission! \'I\'m gonna put the noodles and soup powder into the boiling water.\' Let\'s snap!',
        keyVocab: 'put noodles and soup powder',
        bgGradient: 'linear-gradient(135deg, #422006 0%, #713f12 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'put the soup base', pron: '풋 더 숩 베이스' },
          { role: 'db', en: 'before the noodles.', pron: '비포 더 누들즈' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll put the soup base.", fullPron: '아을 풋 더 숩 베이스', ko: '내가 스프 먼저 넣을게.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna put the soup base.", fullPron: '암거너 풋 더 숩 베이스', ko: '스프를 먼저 넣을 거야.' },
          { bbEn: 'You have to', fullEn: 'You have to put the soup base.', fullPron: '유 해프터 풋 더 숩 베이스', ko: '스프를 꼭 먼저 넣어야 해.' }
        ],
        quizPool: {
          bbCandidates: ["I'll", "We're gonna", 'Do you wanna'],
          coreCandidates: ['put the soup base', 'chop the pork', 'marinate the beef']
        },
        fullEn: "I'll put the soup base before the noodles.",
        fullPron: '아을 + 풋 더 숩 베이스 + 비포 더 누들즈',
        fullKo: '면보다 스프를 먼저 넣을게요.'
      },
      {
        stepTitle: 'SCENE 4 · Crack an Egg into the Pot',
        visualEmojis: '🍜 🥚 🌱',
        imagePath: '/images/kfood/ep1-s7.jpg',
        actionNote: '면을 넣고 끓인 뒤 계란을 깨 넣고 대파 얹기',
        coachKo: '네 번째 코어 블록은, 계란을 톡 깨 넣다, 크랙 언 에그입니다. 앞 블록을 차례대로 갈아 끼워 보세요!',
        coachEn: 'Our core action is \'crack an egg into the pot\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 냄비에 계란을 하나 톡 깨 넣을 거예요!',
        missionEn: 'Snap Mission! \'I\'m gonna crack an fresh egg into the pot.\' Snap the blocks!',
        keyVocab: 'crack an egg into the pot',
        bgGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'crack an egg', pron: '크랙 언 에그' },
          { role: 'db', en: 'into the pot.', pron: '인투 더 팟' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna crack an egg.", fullPron: '암거너 크랙 언 에그', ko: '계란 하나 톡 깨 넣을게.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna crack an egg?', fullPron: '두유 워너 크랙 언 에그?', ko: '계란 하나 깨 넣을래?' },
          { bbEn: "You don't have to", fullEn: "You don't have to crack an egg.", fullPron: '유 돈 해프터 크랙 언 에그', ko: '계란 안 깨 넣어도 돼.' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'We have to', 'I used to'],
          coreCandidates: ['crack an egg', 'use sour kimchi', 'take a sip']
        },
        fullEn: "I'm gonna crack an egg into the pot.",
        fullPron: '암거너 + 크랙 언 에그 + 인투 더 팟',
        fullKo: '냄비에 계란을 하나 톡 깨 넣을 거예요.'
      },
      {
        stepTitle: 'SCENE 5 · Take a Bite with Kimchi',
        visualEmojis: '🥢 💨 😋',
        imagePath: '/images/kfood/ep1-s8.jpg',
        actionNote: '꼬들꼬들한 면발 위에 김치 한 점 올려 후루룩!',
        coachKo: '다섯 번째 코어 블록은, 한 입 먹다, 테이커 바이트입니다. 시작 블록을 바꿔가며 말해 보세요!',
        coachEn: 'Our core action is \'take a bite with kimchi\'. Let\'s swap the first block!',
        missionKo: '마지막 조립 미션! 김치 얹어서 한 입 드셔 보실래요?',
        missionEn: 'Final Snap Mission! \'Do you wanna take a bite with kimchi? It\'s so delicious!\' Snap the blocks!',
        keyVocab: 'take a bite with kimchi',
        bgGradient: 'linear-gradient(135deg, #3b0764 0%, #581c87 100%)',
        blocks: [
          { role: 'bb', en: 'Do you wanna', pron: '두유워너' },
          { role: 'core', en: 'take a bite', pron: '테이커 바이트' },
          { role: 'db', en: 'with kimchi?', pron: '위드 김치?' }
        ],
        combos: [
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna take a bite?', fullPron: '두유 워너 테이커 바이트?', ko: '한 입 드셔 보실래요?' },
          { bbEn: 'I wanna', fullEn: 'I wanna take a bite.', fullPron: '아이 워너 테이커 바이트', ko: '나 한 입 먹고 싶어.' },
          { bbEn: "I'll", fullEn: "I'll take a bite.", fullPron: '아을 테이커 바이트', ko: '내가 한 입 먹어 볼게.' }
        ],
        quizPool: {
          bbCandidates: ['Do you wanna', "I'm gonna", 'You have to'],
          coreCandidates: ['take a bite', 'pour some water', 'slice the tofu']
        },
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
    shortTitle: '🥩 Korean Bulgogi BBQ',
    title: 'How to Cook Authentic Korean Bulgogi Beef BBQ',
    ytTitle: 'How to Make Delicious Korean Bulgogi Beef BBQ in Easy English 🥩 | SoundBlock K-Cooking EP.04',
    thumbnailText: 'Korean Bulgogi & Ssam! [You have to] + [wrap it in lettuce]',
    thumbnailImage: '/images/kfood/ep4-thumb.jpg',
    introNarrationKo: '안녕하세요, 소리블록 케이쿠킹입니다! 외국인 친구들이 가장 좋아하는 불고기와 상추쌈 싸 먹는 법을 소리 블록으로 배워 볼게요.',
    outroNarrationKo: '불고기와 상추쌈 영어 표현까지 완벽히 마스터하셨습니다! 구독과 좋아요 잊지 마세요!',
    scenes: [
      {
        stepTitle: 'SCENE 1 · Introduction to Bulgogi',
        visualEmojis: '🥩 🧄 🍯',
        imagePath: '/images/kfood/ep1-s1.jpg',
        actionNote: '얇게 썬 소고기와 간장 양념 재료 소개',
        coachKo: '첫 번째 코어 블록은, 한국식 불고기를 만들다, 메익 코리안 불고기입니다. 시작 블록 세 개를 갈아 끼워 볼까요?',
        coachEn: 'Our core action is \'make Korean Bulgogi\'. Let\'s swap the starter block!',
        missionKo: '실전 조립 미션! 저녁으로 한국식 불고기를 만들 거예요!',
        missionEn: 'Snap Mission! \'We\'re gonna make Korean Bulgogi for dinner tonight.\' Snap the blocks!',
        keyVocab: 'make Korean Bulgogi',
        bgGradient: 'linear-gradient(135deg, #431407 0%, #7c2d12 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '워거너' },
          { role: 'core', en: 'make Korean Bulgogi', pron: '메익 코리안 불고기' },
          { role: 'db', en: 'for dinner.', pron: '포 디너' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna make Korean Bulgogi.", fullPron: '워거너 메익 코리안 불고기', ko: '한국식 불고기를 만들 거예요.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna make Korean Bulgogi.", fullPron: '암거너 메익 코리안 불고기', ko: '내가 불고기를 만들게.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna make Korean Bulgogi?', fullPron: '두유 워너 메익 코리안 불고기?', ko: '한국식 불고기 만들래?' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'll", 'Did you'],
          coreCandidates: ['make Korean Bulgogi', 'boil the water', 'take a sip']
        },
        fullEn: "We're gonna make Korean Bulgogi for dinner.",
        fullPron: '워거너 + 메익 코리안 불고기 + 포 디너',
        fullKo: '저녁으로 한국식 불고기를 만들 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · Marinate the Beef',
        visualEmojis: '🥣 🥩 ⏲️',
        imagePath: '/images/kfood/ep1-s3.jpg',
        actionNote: '간장, 설탕, 마늘, 참기름 양념에 고기를 30분간 재워 두기',
        coachKo: '두 번째 코어 블록은, 소고기를 양념에 재우다, 매리네잇 더 비프입니다. 시작 블록을 바꿔서 조합해 보세요!',
        coachEn: 'Our core action is \'marinate the beef\'. Let\'s swap the starter block!',
        missionKo: '실전 조립 미션! 30분 동안 소고기를 양념에 재워 둬야 해요!',
        missionEn: 'Snap Mission! \'You have to marinate the beef for 30 minutes.\' Assemble the blocks!',
        keyVocab: 'marinate the beef',
        bgGradient: 'linear-gradient(135deg, #422006 0%, #713f12 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해프터' },
          { role: 'core', en: 'marinate the beef', pron: '매리네잇 더 비프' },
          { role: 'db', en: 'for 30 minutes.', pron: '포 써리 미닛츠' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to marinate the beef.', fullPron: '유 해프터 매리네잇 더 비프', ko: '소고기를 꼭 재워 둬야 해.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna marinate the beef.", fullPron: '암거너 매리네잇 더 비프', ko: '소고기를 양념에 재워 둘게.' },
          { bbEn: 'Did you', fullEn: 'Did you marinate the beef?', fullPron: '디쥬 매리네잇 더 비프?', ko: '소고기 양념에 재워 뒀어?' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'll", 'We have to'],
          coreCandidates: ['marinate the beef', 'slice the tofu', 'crack an egg']
        },
        fullEn: 'You have to marinate the beef for 30 minutes.',
        fullPron: '유 해프터 + 매리네잇 더 비프 + 포 써리 미닛츠',
        fullKo: '30분 동안 소고기를 양념에 재워 둬야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · Cook Meat on High Heat',
        visualEmojis: '🍳 🧅 🍄',
        imagePath: '/images/kfood/ep1-s5.jpg',
        actionNote: '달궈진 팬에 양념된 고기와 양파, 버섯을 넣고 빠르게 볶기',
        coachKo: '세 번째 코어 블록은, 고기를 굽다, 쿡 더 밋입니다. 시작 블록 세 개와 결합해 볼게요!',
        coachEn: 'Our core action is \'cook the meat on high heat\'. Let\'s swap the first block!',
        missionKo: '실전 조립 미션! 센 불에서 고기를 빠르게 구워 줄게요!',
        missionEn: 'Snap Mission! \'I\'m gonna cook the meat on high heat very quickly.\' Snap the blocks!',
        keyVocab: 'cook on high heat',
        bgGradient: 'linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'cook the meat', pron: '쿡 더 밋' },
          { role: 'db', en: 'on high heat.', pron: '온 하이 힛' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna cook the meat.", fullPron: '암거너 쿡 더 밋', ko: '고기를 구워 줄게.' },
          { bbEn: 'We have to', fullEn: 'We have to cook the meat.', fullPron: '위 해프터 쿡 더 밋', ko: '고기를 센 불에 구워야 해.' },
          { bbEn: "I'll", fullEn: "I'll cook the meat.", fullPron: '아을 쿡 더 밋', ko: '내가 고기 구울게.' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", "We're gonna", 'Do you wanna'],
          coreCandidates: ['cook the meat', 'fry them together', 'pour some water']
        },
        fullEn: "I'm gonna cook the meat on high heat.",
        fullPron: '암거너 + 쿡 더 밋 + 온 하이 힛',
        fullKo: '센 불에서 고기를 빠르게 구워 줄게요.'
      },
      {
        stepTitle: 'SCENE 4 · Wrap the Meat in Fresh Lettuce',
        visualEmojis: '🥬 🥩 👍',
        imagePath: '/images/kfood/ep1-s8.jpg',
        actionNote: '손바닥 위 상추에 고기, 밥, 쌈장을 올려 한 입에 쏙!',
        coachKo: '네 번째 코어 블록은, 고기를 싸다, 랩 더 밋입니다. 시작 블록을 바꿔가며 말해 보세요!',
        coachEn: 'Our core action is \'wrap the meat in fresh lettuce\'. Let\'s swap the first block!',
        missionKo: '마지막 조립 미션! 신선한 상추에 고기를 싸서 먹어 볼게요!',
        missionEn: 'Final Snap Mission! \'I\'ll wrap the meat in fresh lettuce with ssamjang.\' Snap the blocks!',
        keyVocab: 'wrap the meat in lettuce',
        bgGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'wrap the meat', pron: '랩 더 밋' },
          { role: 'db', en: 'in fresh lettuce.', pron: '인 프레쉬 레터스' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll wrap the meat.", fullPron: '아을 랩 더 밋', ko: '상추에 고기를 싸 먹을게.' },
          { bbEn: 'You have to', fullEn: 'You have to wrap the meat.', fullPron: '유 해프터 랩 더 밋', ko: '상추에 고기를 싸서 먹어야 해.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna wrap the meat?', fullPron: '두유 워너 랩 더 밋?', ko: '상추에 고기 싸서 먹어 볼래?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", "I'm gonna", 'Did you'],
          coreCandidates: ['wrap the meat', 'take a bite', 'stir-fry the kimchi']
        },
        fullEn: "I'll wrap the meat in fresh lettuce.",
        fullPron: '아을 + 랩 더 밋 + 인 프레쉬 레터스',
        fullKo: '신선한 상추에 고기를 싸서 먹어 볼게요.'
      }
    ]
  },
  // ==========================================
  // EP 5. 매콤달콤 치즈 떡볶이 (Spicy Tteokbokki) - 8 Scenes (~5m 30s)
  // ==========================================
  {
    id: 'tteokbokki',
    epNumber: 'EP.05',
    emoji: '🍢',
    shortTitle: '🍢 Spicy Tteokbokki',
    title: 'How to Make Authentic Korean Tteokbokki with Cheese',
    ytTitle: 'How to Make Authentic Korean Tteokbokki in Easy English 🍢 | SoundBlock K-Cooking EP.05',
    thumbnailText: 'Spicy & Chewy Tteokbokki! [I\'m gonna] + [sprinkle mozzarella cheese on top]',
    thumbnailImage: '/images/kfood/ep5-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let's make authentic Korean street food, spicy and sweet Tteokbokki with cheese, using simple sound blocks. Let's get cooking!",
    outroNarrationKo: "Mission complete! You've mastered all the sound blocks for spicy Tteokbokki! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Soak the Rice Cakes',
        visualEmojis: '🍚 💧 ⏰',
        imagePath: '/images/kfood/ep5-thumb.jpg',
        actionNote: '말랑말랑해지도록 떡을 따뜻한 물에 불리기',
        coachKo: "첫 번째 코어 블록은, 떡을 물에 불리다, 소옥 더 라이스 케익스입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'soak the rice cakes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 따뜻한 물에 떡을 불릴 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna soak the rice cakes in warm water.' Snap the blocks!",
        keyVocab: 'soak the rice cakes',
        bgGradient: 'linear-gradient(135deg, #7c2d12 0%, #b91c1c 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'soak the rice cakes', pron: '소옥 더 라이스 케익스' },
          { role: 'db', en: 'in warm water.', pron: '인 웜 워터' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna soak the rice cakes.", fullPron: '암거너 소옥 더 라이스 케익스', ko: '떡을 불릴게.' },
          { bbEn: "You have to", fullEn: "You have to soak the rice cakes.", fullPron: '유 햅투 소옥 더 라이스 케익스', ko: '떡을 불려야 해.' },
          { bbEn: "Did you", fullEn: "Did you soak the rice cakes?", fullPron: '디쥬 소옥 더 라이스 케익스?', ko: '떡 불려 뒀어?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'Did you'],
          coreCandidates: ['soak the rice cakes', 'slice the tofu', 'pour some water']
        },
        fullEn: "I'm gonna soak the rice cakes in warm water.",
        fullPron: '암거너 + 소옥 더 라이스 케익스 + 인 웜 워터',
        fullKo: '따뜻한 물에 떡을 불려 둘게요.'
      },
      {
        stepTitle: 'SCENE 2 · Golden Sweet & Spicy Sauce',
        visualEmojis: '🌶️ 🍯 🥣',
        imagePath: '/images/kfood/ep5-thumb.jpg',
        actionNote: '황금 비율 고추장과 설탕 양념 섞기',
        coachKo: "두 번째 코어 블록은, 고추장을 섞다, 믹스 레드 칠리 페이스트입니다. 시작 블록을 갈아 끼워 볼까요?",
        coachEn: "Our core action is 'mix red chili paste'. Let's swap the first block!",
        missionKo: "실전 조립 미션! 고추장에 설탕을 섞어야 해요!",
        missionEn: "Snap Mission! 'You have to mix red chili paste with sugar.' Snap the blocks!",
        keyVocab: 'mix red chili paste',
        bgGradient: 'linear-gradient(135deg, #991b1b 0%, #dc2626 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 햅투' },
          { role: 'core', en: 'mix red chili paste', pron: '믹스 레드 칠리 페이스트' },
          { role: 'db', en: 'with sugar.', pron: '위드 슈가' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to mix red chili paste.', fullPron: '유 햅투 믹스 레드 칠리 페이스트', ko: '고추장을 섞어야 해.' },
          { bbEn: "I'll", fullEn: "I'll mix red chili paste.", fullPron: '아을 믹스 레드 칠리 페이스트', ko: '내가 고추장을 섞을게.' },
          { bbEn: 'Can you', fullEn: 'Can you mix red chili paste?', fullPron: '캔유 믹스 레드 칠리 페이스트?', ko: '고추장 좀 섞어 줄래?' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'll", 'Can you'],
          coreCandidates: ['mix red chili paste', 'use sour kimchi', 'chop the pork']
        },
        fullEn: 'You have to mix red chili paste with sugar.',
        fullPron: '유 햅투 + 믹스 레드 칠리 페이스트 + 위드 슈가',
        fullKo: '고추장에 설탕을 잘 섞어 주어야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · Pour the Savory Broth',
        visualEmojis: '🐟 🫗 🥘',
        imagePath: '/images/kfood/ep5-thumb.jpg',
        actionNote: '멸치 다시마 육수를 냄비에 붓기',
        coachKo: "세 번째 코어 블록은, 멸치 육수를 붓다, 포어 디 앤초비 브로스입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour the anchovy broth'. Let's swap the first block!",
        missionKo: "실전 조립 미션! 팬에 멸치 육수를 부을 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna pour the anchovy broth into the pan.' Snap!",
        keyVocab: 'pour the anchovy broth',
        bgGradient: 'linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'pour the anchovy broth', pron: '포어 디 앤초비 브로스' },
          { role: 'db', en: 'into the pan.', pron: '인투 더 팬' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna pour the anchovy broth.", fullPron: '웨어 거너 포어 디 앤초비 브로스', ko: '멸치 육수를 부을 거야.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna pour the anchovy broth.", fullPron: '암거너 포어 디 앤초비 브로스', ko: '내가 멸치 육수를 부을게.' },
          { bbEn: 'Did you', fullEn: 'Did you pour the anchovy broth?', fullPron: '디쥬 포어 디 앤초비 브로스?', ko: '멸치 육수 부었어?' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'm gonna", 'Did you'],
          coreCandidates: ['pour the anchovy broth', 'boil the noodles', 'slice the onion']
        },
        fullEn: "We're gonna pour the anchovy broth into the pan.",
        fullPron: '웨어 거너 + 포어 디 앤초비 브로스 + 인투 더 팬',
        fullKo: '냄비에 멸치 육수를 부어 줄 거예요.'
      },
      {
        stepTitle: 'SCENE 4 · Dissolve the Sauce',
        visualEmojis: '🔥 🥄 🫧',
        imagePath: '/images/kfood/ep5-thumb.jpg',
        actionNote: '끓어오를 때까지 양념을 잘 풀기',
        coachKo: "네 번째 코어 블록은, 양념을 풀다, 디졸브 더 소오스입니다. 시작 블록을 갈아 끼워 볼까요?",
        coachEn: "Our core action is 'dissolve the sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 끓어오를 때까지 양념을 풀게요!",
        missionEn: "Snap Mission! 'I\'ll dissolve the sauce until it boils.' Snap!",
        keyVocab: 'dissolve the sauce',
        bgGradient: 'linear-gradient(135deg, #b45309 0%, #ea580c 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'dissolve the sauce', pron: '디졸브 더 소오스' },
          { role: 'db', en: 'until it boils.', pron: '언틸 잇 보일스' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll dissolve the sauce.", fullPron: '아을 디졸브 더 소오스', ko: '양념을 풀게.' },
          { bbEn: 'You have to', fullEn: 'You have to dissolve the sauce.', fullPron: '유 햅투 디졸브 더 소오스', ko: '양념을 풀어야 해.' },
          { bbEn: 'Can you', fullEn: 'Can you dissolve the sauce?', fullPron: '캔유 디졸브 더 소오스?', ko: '양념 좀 풀어 줄래?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", 'You have to', 'Can you'],
          coreCandidates: ['dissolve the sauce', 'fry them together', 'take a sip']
        },
        fullEn: "I'll dissolve the sauce until it boils.",
        fullPron: '아을 + 디졸브 더 소오스 + 언틸 잇 보일스',
        fullKo: '육수가 끓어오를 때까지 양념을 잘 풀어 줄게요.'
      },
      {
        stepTitle: 'SCENE 5 · Add Rice Cakes and Fish Cakes',
        visualEmojis: '🍢 🍥 🍲',
        imagePath: '/images/kfood/ep5-thumb.jpg',
        actionNote: '불린 떡과 어묵 넣기',
        coachKo: "다섯 번째 코어 블록은, 떡을 넣다, 애드 더 라이스 케익스입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add the rice cakes'. Let's swap!",
        missionKo: "실전 조립 미션! 떡과 썬 어묵을 넣을 수 있어요!",
        missionEn: "Snap Mission! 'You can add the rice cakes and sliced fish cakes.' Snap!",
        keyVocab: 'add the rice cakes',
        bgGradient: 'linear-gradient(135deg, #15803d 0%, #16a34a 100%)',
        blocks: [
          { role: 'bb', en: 'You can', pron: '유 캔' },
          { role: 'core', en: 'add the rice cakes', pron: '애드 더 라이스 케익스' },
          { role: 'db', en: 'and sliced fish cakes.', pron: '앤 슬라이스드 피쉬 케익스' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can add the rice cakes.', fullPron: '유 캔 애드 더 라이스 케익스', ko: '떡을 넣으시면 돼요.' },
          { bbEn: "We're gonna", fullEn: "We're gonna add the rice cakes.", fullPron: '웨어 거너 애드 더 라이스 케익스', ko: '떡을 넣을 거야.' },
          { bbEn: 'Did you', fullEn: 'Did you add the rice cakes?', fullPron: '디쥬 애드 더 라이스 케익스?', ko: '떡 넣었어?' }
        ],
        quizPool: {
          bbCandidates: ['You can', "We're gonna", 'Did you'],
          coreCandidates: ['add the rice cakes', 'wrap the meat', 'chop the kimchi']
        },
        fullEn: 'You can add the rice cakes and sliced fish cakes.',
        fullPron: '유 캔 + 애드 더 라이스 케익스 + 앤 슬라이스드 피쉬 케익스',
        fullKo: '떡과 어묵을 넣고 함께 끓여 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Simmer until Thick',
        visualEmojis: '♨️ ⏳ 🥘',
        imagePath: '/images/kfood/ep5-thumb.jpg',
        actionNote: '국물이 걸쭉해질 때까지 중불로 졸이기',
        coachKo: "여섯 번째 코어 블록은, 중불에 졸이다, 시머 온 미디엄 히이트입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'simmer on medium heat'. Let's swap!",
        missionKo: "실전 조립 미션! 걸쭉해질 때까지 중불에 졸여야 해요!",
        missionEn: "Snap Mission! 'We have to simmer on medium heat until thick.' Snap!",
        keyVocab: 'simmer on medium heat',
        bgGradient: 'linear-gradient(135deg, #9a3412 0%, #c2410c 100%)',
        blocks: [
          { role: 'bb', en: 'We have to', pron: '위 햅투' },
          { role: 'core', en: 'simmer on medium heat', pron: '시머 온 미디엄 히이트' },
          { role: 'db', en: 'until thick.', pron: '언틸 띡' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to simmer on medium heat.', fullPron: '위 햅투 시머 온 미디엄 히이트', ko: '중불로 졸여야 해.' },
          { bbEn: 'You should', fullEn: 'You should simmer on medium heat.', fullPron: '유 슈드 시머 온 미디엄 히이트', ko: '중불로 졸여 주는 게 좋아.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna simmer on medium heat.", fullPron: '암거너 시머 온 미디엄 히이트', ko: '중불로 졸일게.' }
        ],
        quizPool: {
          bbCandidates: ['We have to', 'You should', "I'm gonna"],
          coreCandidates: ['simmer on medium heat', 'mix with vinegar', 'rinse in cold water']
        },
        fullEn: 'We have to simmer on medium heat until thick.',
        fullPron: '위 햅투 + 시머 온 미디엄 히이트 + 언틸 띡',
        fullKo: '국물이 자작하고 걸쭉해질 때까지 중불로 졸여야 해요.'
      },
      {
        stepTitle: 'SCENE 7 · Melted Cheese Topping',
        visualEmojis: '🧀 ✨ 🤤',
        imagePath: '/images/kfood/ep5-thumb.jpg',
        actionNote: '피자 모짜렐라 치즈 듬뿍 뿌리기',
        coachKo: "일곱 번째 코어 블록은, 모짜렐라 치즈를 뿌리다, 스프링클 모짜렐라 치즈입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sprinkle mozzarella cheese'. Let's swap!",
        missionKo: "실전 조립 미션! 바로 위에 모짜렐라 치즈를 뿌릴 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna sprinkle mozzarella cheese right on top.' Snap!",
        keyVocab: 'sprinkle mozzarella cheese',
        bgGradient: 'linear-gradient(135deg, #eab308 0%, #ca8a04 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'sprinkle mozzarella cheese', pron: '스프링클 모짜렐라 치즈' },
          { role: 'db', en: 'right on top.', pron: '롸잇 온 탑' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna sprinkle mozzarella cheese.", fullPron: '암거너 스프링클 모짜렐라 치즈', ko: '모짜렐라 치즈를 뿌릴게.' },
          { bbEn: 'You have to', fullEn: 'You have to sprinkle mozzarella cheese.', fullPron: '유 햅투 스프링클 모짜렐라 치즈', ko: '모짜렐라 치즈를 뿌려야 해.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna sprinkle mozzarella cheese?', fullPron: '두유 워너 스프링클 모짜렐라 치즈?', ko: '모짜렐라 치즈 뿌려 줄까?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'Do you wanna'],
          coreCandidates: ['sprinkle mozzarella cheese', 'put a fried egg', 'add the kimchi juice']
        },
        fullEn: "I'm gonna sprinkle mozzarella cheese right on top.",
        fullPron: '암거너 + 스프링클 모짜렐라 치즈 + 롸잇 온 탑',
        fullKo: '떡볶이 바로 위에 모짜렐라 치즈를 듬뿍 뿌려 줄게요.'
      },
      {
        stepTitle: 'SCENE 8 · Chewy & Spicy Reaction',
        visualEmojis: '🔥 😋 ❤️',
        imagePath: '/images/kfood/ep5-thumb.jpg',
        actionNote: '치즈가 쭈욱 늘어나는 떡볶이 한 입 먹방 리액션',
        coachKo: "여덟 번째 코어 리액션은, 쫄깃하고 매콤하다, 츄이 앤 스파이시입니다! 소리를 느껴 보세요!",
        coachEn: "Our core reaction is 'chewy and spicy'. Wow, listen to that!",
        missionKo: "마지막 실전 조립! 치즈 덕분에 쫄깃하고 매콤해요!",
        missionEn: "Final Snap Mission! 'It\'s so chewy and spicy with melted cheese!' Snap!",
        keyVocab: 'chewy and spicy',
        bgGradient: 'linear-gradient(135deg, #991b1b 0%, #ef4444 100%)',
        blocks: [
          { role: 'bb', en: "It's so", pron: '잇츠 쏘' },
          { role: 'core', en: 'chewy and spicy', pron: '츄이 앤 스파이시' },
          { role: 'db', en: 'with melted cheese!', pron: '위드 멜티드 치즈' }
        ],
        combos: [
          { bbEn: "It's so", fullEn: "It's so chewy and spicy.", fullPron: '잇츠 쏘 츄이 앤 스파이시', ko: '진짜 쫄깃하고 매콤해.' },
          { bbEn: 'This is', fullEn: 'This is so chewy and spicy.', fullPron: '디스 이즈 쏘 츄이 앤 스파이시', ko: '이거 완전 쫄깃하고 매콤하다.' },
          { bbEn: 'Is it', fullEn: 'Is it so chewy and spicy?', fullPron: '이즈 잇 쏘 츄이 앤 스파이시?', ko: '그렇게 쫄깃하고 매콤해?' }
        ],
        quizPool: {
          bbCandidates: ["It's so", 'This is', 'Is it'],
          coreCandidates: ['chewy and spicy', 'crispy and savory', 'rich and comforting']
        },
        fullEn: "It's so chewy and spicy with melted cheese!",
        fullPron: '잇츠 쏘 + 츄이 앤 스파이시 + 위드 멜티드 치즈!',
        fullKo: '녹아내린 치즈 덕분에 정말 쫄깃하고 맛있게 매콤해요!'
      }
    ]
  },

  // ==========================================
  // EP 6. 겉바속촉 해물파전 (Crispy Korean Seafood Pancake) - 8 Scenes (~5m 30s)
  // ==========================================
  {
    id: 'korean-pancake',
    epNumber: 'EP.06',
    emoji: '🥞',
    shortTitle: '🥞 Crispy K-Pancake',
    title: 'How to Make Ultra-Crispy Korean Seafood Pancake',
    ytTitle: 'How to Make Ultra-Crispy Korean Seafood Pancake in Easy English 🥞 | SoundBlock K-Cooking EP.06',
    thumbnailText: 'Super Crispy Korean Pancake! [It\'s so] + [crispy on the outside]',
    thumbnailImage: '/images/kfood/ep6-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let's make ultra-crispy Korean seafood pancakes using simple sound blocks. Let's get cooking!",
    outroNarrationKo: "Mission complete! You've mastered all the sound blocks for crispy Korean pancakes! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Introduction to Crispy Pancakes',
        visualEmojis: '🌧️ 🥞 🥢',
        imagePath: '/images/kfood/ep6-thumb.jpg',
        actionNote: '비 오는 날 최고의 소울푸드 전 부치기 소개',
        coachKo: "첫 번째 코어 블록은, 바삭한 한국식 전을 만들다, 메익 크리스피 코리안 팬케익스입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'make crispy Korean pancakes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 비 오는 날 바삭한 한국식 전을 부칠 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna make crispy Korean pancakes for a rainy day.' Snap!",
        keyVocab: 'make crispy Korean pancakes',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'make crispy Korean pancakes', pron: '메익 크리스피 코리안 팬케익스' },
          { role: 'db', en: 'for a rainy day.', pron: '포어 어 레이니 데이' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna make crispy Korean pancakes.", fullPron: '암거너 메익 크리스피 코리안 팬케익스', ko: '바삭한 전을 부칠게.' },
          { bbEn: 'You have to', fullEn: 'You have to make crispy Korean pancakes.', fullPron: '유 햅투 메익 크리스피 코리안 팬케익스', ko: '바삭한 전을 부쳐야 해.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna make crispy Korean pancakes?', fullPron: '두유 워너 메익 크리스피 코리안 팬케익스?', ko: '바삭한 전 부쳐 먹을래?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'Do you wanna'],
          coreCandidates: ['make crispy Korean pancakes', 'cook Korean ramen', 'slice the green onion']
        },
        fullEn: "I'm gonna make crispy Korean pancakes for a rainy day.",
        fullPron: '암거너 + 메익 크리스피 코리안 팬케익스 + 포어 어 레이니 데이',
        fullKo: '비 오는 날엔 역시 바삭한 한국식 파전을 부쳐야죠.'
      },
      {
        stepTitle: 'SCENE 2 · Ice-Cold Water Secret',
        visualEmojis: '🧊 💧 ⚡',
        imagePath: '/images/kfood/ep6-thumb.jpg',
        actionNote: '바삭함의 비결인 얼음물로 반죽하기',
        coachKo: "두 번째 코어 블록은, 얼음물을 쓰다, 유즈 아이스콜드 워터입니다. 바삭함의 절대 비결!",
        coachEn: "Our core action is 'use ice-cold water'. That's the crispy secret!",
        missionKo: "실전 조립 미션! 극상의 바삭함을 위해 얼음물을 써야 해요!",
        missionEn: "Snap Mission! 'You have to use ice-cold water for extra crunch.' Snap!",
        keyVocab: 'use ice-cold water',
        bgGradient: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 햅투' },
          { role: 'core', en: 'use ice-cold water', pron: '유즈 아이스콜드 워터' },
          { role: 'db', en: 'for extra crunch.', pron: '포어 엑스트라 크런치' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to use ice-cold water.', fullPron: '유 햅투 유즈 아이스콜드 워터', ko: '얼음물을 써야 해.' },
          { bbEn: "I'll", fullEn: "I'll use ice-cold water.", fullPron: '아을 유즈 아이스콜드 워터', ko: '내가 얼음물을 쓸게.' },
          { bbEn: 'Did you', fullEn: 'Did you use ice-cold water?', fullPron: '디쥬 유즈 아이스콜드 워터?', ko: '얼음물 썼어?' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'll", 'Did you'],
          coreCandidates: ['use ice-cold water', 'soak the rice cakes', 'season with soy sauce']
        },
        fullEn: 'You have to use ice-cold water for extra crunch.',
        fullPron: '유 햅투 + 유즈 아이스콜드 워터 + 포어 엑스트라 크런치',
        fullKo: '극강의 바삭함을 위해서는 꼭 차가운 얼음물을 써야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · Fresh Scallions and Seafood',
        visualEmojis: '🦐 🦑 🧅',
        imagePath: '/images/kfood/ep6-thumb.jpg',
        actionNote: '신선한 쪽파와 해물 썰기',
        coachKo: "세 번째 코어 블록은, 신선한 쪽파를 썰다, 찹 프레쉬 그린 어니언스입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'chop fresh green onions'. Let's swap!",
        missionKo: "실전 조립 미션! 싱싱한 쪽파와 모둠 해물을 썰게요!",
        missionEn: "Snap Mission! 'I\'ll chop fresh green onions and mixed seafood.' Snap!",
        keyVocab: 'chop fresh green onions',
        bgGradient: 'linear-gradient(135deg, #15803d 0%, #166534 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'chop fresh green onions', pron: '찹 프레쉬 그린 어니언스' },
          { role: 'db', en: 'and mixed seafood.', pron: '앤 믹스드 씨푸드' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll chop fresh green onions.", fullPron: '아을 찹 프레쉬 그린 어니언스', ko: '신선한 쪽파를 썰게.' },
          { bbEn: "We're gonna", fullEn: "We're gonna chop fresh green onions.", fullPron: '웨어 거너 찹 프레쉬 그린 어니언스', ko: '쪽파를 썰 거야.' },
          { bbEn: 'Can you', fullEn: 'Can you chop fresh green onions?', fullPron: '캔유 찹 프레쉬 그린 어니언스?', ko: '쪽파 좀 썰어 줄래?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", "We're gonna", 'Can you'],
          coreCandidates: ['chop fresh green onions', 'dissolve the sauce', 'add the rice cakes']
        },
        fullEn: "I'll chop fresh green onions and mixed seafood.",
        fullPron: '아을 + 찹 프레쉬 그린 어니언스 + 앤 믹스드 씨푸드',
        fullKo: '신선한 쪽파와 모둠 해물을 알맞게 썰어 둘게요.'
      },
      {
        stepTitle: 'SCENE 4 · Heat the Pan with Plenty of Oil',
        visualEmojis: '🍳 🫒 🔥',
        imagePath: '/images/kfood/ep6-thumb.jpg',
        actionNote: '기름을 넉넉히 두르고 팬 달구기',
        coachKo: "네 번째 코어 블록은, 팬을 달구다, 히이트 더 팬입니다. 기름이 넉넉해야 바삭해요!",
        coachEn: "Our core action is 'heat the pan'. Oil makes it super crisp!",
        missionKo: "실전 조립 미션! 식용유를 넉넉히 두르고 팬을 달굴 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna heat the pan with plenty of cooking oil.' Snap!",
        keyVocab: 'heat the pan',
        bgGradient: 'linear-gradient(135deg, #ea580c 0%, #c2410c 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'heat the pan', pron: '히이트 더 팬' },
          { role: 'db', en: 'with plenty of cooking oil.', pron: '위드 플렌티 오브 쿠킹 오일' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna heat the pan.", fullPron: '웨어 거너 히이트 더 팬', ko: '팬을 달굴 거야.' },
          { bbEn: 'You have to', fullEn: 'You have to heat the pan.', fullPron: '유 햅투 히이트 더 팬', ko: '팬을 달궈야 해.' },
          { bbEn: 'Did you', fullEn: 'Did you heat the pan?', fullPron: '디쥬 히이트 더 팬?', ko: '팬 달궜어?' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", 'You have to', 'Did you'],
          coreCandidates: ['heat the pan', 'pour the broth', 'wrap it in lettuce']
        },
        fullEn: "We're gonna heat the pan with plenty of cooking oil.",
        fullPron: '웨어 거너 + 히이트 더 팬 + 위드 플렌티 오브 쿠킹 오일',
        fullKo: '기름을 넉넉히 두르고 프라이팬을 뜨겁게 달궈 줍니다.'
      },
      {
        stepTitle: 'SCENE 5 · Spread the Batter Thinly',
        visualEmojis: '🥞 🥄 ♨️',
        imagePath: '/images/kfood/ep6-thumb.jpg',
        actionNote: '반죽을 얇고 넓게 펴기',
        coachKo: "다섯 번째 코어 블록은, 반죽을 얇게 펴다, 스프레드 더 배터 띤리입니다. 시작 블록을 갈아 끼워 볼까요?",
        coachEn: "Our core action is 'spread the batter thinly'. Let's swap!",
        missionKo: "실전 조립 미션! 중불에서 반죽을 얇게 펴 바르는 게 좋아요!",
        missionEn: "Snap Mission! 'You should spread the batter thinly over medium heat.' Snap!",
        keyVocab: 'spread the batter thinly',
        bgGradient: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: 'You should', pron: '유 슈드' },
          { role: 'core', en: 'spread the batter thinly', pron: '스프레드 더 배터 띤리' },
          { role: 'db', en: 'over medium heat.', pron: '오버 미디엄 히이트' }
        ],
        combos: [
          { bbEn: 'You should', fullEn: 'You should spread the batter thinly.', fullPron: '유 슈드 스프레드 더 배터 띤리', ko: '반죽을 얇게 펴는 게 좋아.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna spread the batter thinly.", fullPron: '암거너 스프레드 더 배터 띤리', ko: '반죽을 얇게 펼게.' },
          { bbEn: 'Can you', fullEn: 'Can you spread the batter thinly?', fullPron: '캔유 스프레드 더 배터 띤리?', ko: '반죽 얇게 펴 줄래?' }
        ],
        quizPool: {
          bbCandidates: ['You should', "I'm gonna", 'Can you'],
          coreCandidates: ['spread the batter thinly', 'boil the noodles', 'take a sip']
        },
        fullEn: 'You should spread the batter thinly over medium heat.',
        fullPron: '유 슈드 + 스프레드 더 배터 띤리 + 오버 미디엄 히이트',
        fullKo: '중불 위에서 반죽을 최대한 얇고 고르게 펴 주세요.'
      },
      {
        stepTitle: 'SCENE 6 · The Golden Flip',
        visualEmojis: '🍳 🔄 🏆',
        imagePath: '/images/kfood/ep6-thumb.jpg',
        actionNote: '노릇노릇할 때 완벽한 뒤집기 한 판',
        coachKo: "여섯 번째 코어 블록은, 뒤집다, 플립 잇 오버입니다. 타이밍이 생명!",
        coachEn: "Our core action is 'flip it over'. Timing is key!",
        missionKo: "실전 조립 미션! 노릇하고 바삭해졌을 때 뒤집어야 해요!",
        missionEn: "Snap Mission! 'We have to flip it over when golden and crisp.' Snap!",
        keyVocab: 'flip it over',
        bgGradient: 'linear-gradient(135deg, #b45309 0%, #78350f 100%)',
        blocks: [
          { role: 'bb', en: 'We have to', pron: '위 햅투' },
          { role: 'core', en: 'flip it over', pron: '플립 잇 오버' },
          { role: 'db', en: 'when golden and crisp.', pron: '웬 골든 앤 크리스프' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to flip it over.', fullPron: '위 햅투 플립 잇 오버', ko: '뒤집어야 해.' },
          { bbEn: 'You can', fullEn: 'You can flip it over.', fullPron: '유 캔 플립 잇 오버', ko: '뒤집으셔도 돼요.' },
          { bbEn: 'Are you gonna', fullEn: 'Are you gonna flip it over?', fullPron: '아유 거너 플립 잇 오버?', ko: '뒤집을 거야?' }
        ],
        quizPool: {
          bbCandidates: ['We have to', 'You can', 'Are you gonna'],
          coreCandidates: ['flip it over', 'chop the kimchi', 'simmer on medium heat']
        },
        fullEn: 'We have to flip it over when golden and crisp.',
        fullPron: '위 햅투 + 플립 잇 오버 + 웬 골든 앤 크리스프',
        fullKo: '바닥면이 노릇노릇하고 바삭해졌을 때 한 번에 싹 뒤집어 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Tangy Soy Dipping Sauce',
        visualEmojis: '🥢 🥣 🧅',
        imagePath: '/images/kfood/ep6-thumb.jpg',
        actionNote: '식초와 고춧가루 넣은 초간장 만들기',
        coachKo: "일곱 번째 코어 블록은, 간장에 식초를 섞다, 믹스 소이 소스 위드 비네거입니다. 전의 최고 단짝!",
        coachEn: "Our core action is 'mix soy sauce with vinegar'. Let's swap!",
        missionKo: "실전 조립 미션! 간장에 식초와 고춧가루를 섞을게요!",
        missionEn: "Snap Mission! 'I\'m gonna mix soy sauce with vinegar and chili.' Snap!",
        keyVocab: 'mix soy sauce with vinegar',
        bgGradient: 'linear-gradient(135deg, #3f3f46 0%, #18181b 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'mix soy sauce with vinegar', pron: '믹스 소이 소스 위드 비네거' },
          { role: 'db', en: 'and chili.', pron: '앤 칠리' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna mix soy sauce with vinegar.", fullPron: '암거너 믹스 소이 소스 위드 비네거', ko: '간장에 식초를 섞을게.' },
          { bbEn: 'You have to', fullEn: 'You have to mix soy sauce with vinegar.', fullPron: '유 햅투 믹스 소이 소스 위드 비네거', ko: '간장에 식초를 섞어야 해.' },
          { bbEn: 'Can you', fullEn: 'Can you mix soy sauce with vinegar?', fullPron: '캔유 믹스 소이 소스 위드 비네거?', ko: '초간장 좀 섞어 줄래?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'Can you'],
          coreCandidates: ['mix soy sauce with vinegar', 'sprinkle mozzarella cheese', 'stir-fry marinated beef']
        },
        fullEn: "I'm gonna mix soy sauce with vinegar and chili.",
        fullPron: '암거너 + 믹스 소이 소스 위드 비네거 + 앤 칠리',
        fullKo: '간장에 식초와 고춧가루를 타서 새콤짭조름한 초간장을 만들게요.'
      },
      {
        stepTitle: 'SCENE 8 · Crispy Outside & Soft Inside',
        visualEmojis: '🥢 😋 🌟',
        imagePath: '/images/kfood/ep6-thumb.jpg',
        actionNote: '초간장 찍어서 겉바속촉 한 입 먹방 리액션',
        coachKo: "여덟 번째 코어 리액션은, 겉은 바삭하다, 크리스피 온 디 아웃사이드입니다! 겉바속촉의 정석!",
        coachEn: "Our core reaction is 'crispy on the outside'. The ultimate crunch!",
        missionKo: "마지막 실전 조립! 겉은 진짜 바삭하고 속은 부드러워요!",
        missionEn: "Final Snap Mission! 'It\'s so crispy on the outside and tender inside!' Snap!",
        keyVocab: 'crispy on the outside',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #d97706 100%)',
        blocks: [
          { role: 'bb', en: "It's so", pron: '잇츠 쏘' },
          { role: 'core', en: 'crispy on the outside', pron: '크리스피 온 디 아웃사이드' },
          { role: 'db', en: 'and tender inside!', pron: '앤 텐더 인사이드' }
        ],
        combos: [
          { bbEn: "It's so", fullEn: "It's so crispy on the outside.", fullPron: '잇츠 쏘 크리스피 온 디 아웃사이드', ko: '겉이 정말 바삭해.' },
          { bbEn: 'This is', fullEn: 'This is so crispy on the outside.', fullPron: '디스 이즈 쏘 크리스피 온 디 아웃사이드', ko: '이거 겉이 완전 바삭하다.' },
          { bbEn: "Isn't it", fullEn: "Isn't it crispy on the outside?", fullPron: '이즌 잇 크리스피 온 디 아웃사이드?', ko: '겉이 정말 바삭하지 않니?' }
        ],
        quizPool: {
          bbCandidates: ["It's so", 'This is', "Isn't it"],
          coreCandidates: ['crispy on the outside', 'chewy and spicy', 'savory and delicious']
        },
        fullEn: "It's so crispy on the outside and tender inside!",
        fullPron: '잇츠 쏘 + 크리스피 온 디 아웃사이드 + 앤 텐더 인사이드!',
        fullKo: '초간장에 찍어 먹으니 겉은 바삭바삭하고 속은 촉촉해요!'
      }
    ]
  },

  // ==========================================
  // EP 7. 잔치 잡채 (Authentic Korean Japchae) - 8 Scenes (~5m 30s)
  // ==========================================
  {
    id: 'japchae',
    epNumber: 'EP.07',
    emoji: '🥢',
    shortTitle: '🥢 Festive Japchae',
    title: 'How to Make Authentic Korean Japchae Glass Noodles',
    ytTitle: 'How to Make Authentic Korean Japchae in Easy English 🥢 | SoundBlock K-Cooking EP.07',
    thumbnailText: 'Authentic Korean Japchae! [We\'re gonna] + [make authentic Korean Japchae]',
    thumbnailImage: '/images/kfood/ep7-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let's make authentic Korean festive Japchae glass noodles using sound blocks. Let's get cooking!",
    outroNarrationKo: "Mission complete! You've mastered all the sound blocks for traditional Korean Japchae! Subscribe and like for more delicious K-food. See you next time!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Festive Japchae Feast',
        visualEmojis: '🎉 🥢 🥩',
        imagePath: '/images/kfood/ep7-thumb.jpg',
        actionNote: '잔칫날이나 특별한 날 만드는 고급 잡채 소개',
        coachKo: "첫 번째 코어 블록은, 정통 한국 잡채를 만들다, 메익 어센틱 코리안 잡채입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'make authentic Korean Japchae'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 잔칫상을 위해 정통 한국 잡채를 만들 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna make authentic Korean Japchae for a feast.' Snap!",
        keyVocab: 'make authentic Korean Japchae',
        bgGradient: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'make authentic Korean Japchae', pron: '메익 어센틱 코리안 잡채' },
          { role: 'db', en: 'for a feast.', pron: '포어 어 피이스트' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna make authentic Korean Japchae.", fullPron: '웨어 거너 메익 어센틱 코리안 잡채', ko: '정통 잡채를 만들 거야.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna make authentic Korean Japchae.", fullPron: '암거너 메익 어센틱 코리안 잡채', ko: '내가 정통 잡채를 만들게.' },
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna make authentic Korean Japchae?', fullPron: '두유 워너 메익 어센틱 코리안 잡채?', ko: '정통 잡채 만들어 볼래?' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'm gonna", 'Do you wanna'],
          coreCandidates: ['make authentic Korean Japchae', 'make crispy Korean pancakes', 'cook Korean ramen']
        },
        fullEn: "We're gonna make authentic Korean Japchae for a feast.",
        fullPron: '웨어 거너 + 메익 어센틱 코리안 잡채 + 포어 어 피이스트',
        fullKo: '특별한 날을 위해 알록달록 맛있는 정통 잡채를 만들 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · Boil Chewy Glass Noodles',
        visualEmojis: '🥢 ♨️ ⏱️',
        imagePath: '/images/kfood/ep7-thumb.jpg',
        actionNote: '쫄깃한 고구마 당면을 딱 7분간 삶기',
        coachKo: "두 번째 코어 블록은, 당면을 삶다, 보일 더 글래스 누들스입니다. 7분이 황금 시간!",
        coachEn: "Our core action is 'boil the glass noodles'. Seven minutes is perfect!",
        missionKo: "실전 조립 미션! 딱 7분 동안 당면을 삶아야 해요!",
        missionEn: "Snap Mission! 'You have to boil the glass noodles for seven minutes.' Snap!",
        keyVocab: 'boil the glass noodles',
        bgGradient: 'linear-gradient(135deg, #0f766e 0%, #115e59 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 햅투' },
          { role: 'core', en: 'boil the glass noodles', pron: '보일 더 글래스 누들스' },
          { role: 'db', en: 'for seven minutes.', pron: '포어 세븐 미닛츠' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to boil the glass noodles.', fullPron: '유 햅투 보일 더 글래스 누들스', ko: '당면을 삶아야 해.' },
          { bbEn: "I'll", fullEn: "I'll boil the glass noodles.", fullPron: '아을 보일 더 글래스 누들스', ko: '내가 당면을 삶을게.' },
          { bbEn: 'Did you', fullEn: 'Did you boil the glass noodles?', fullPron: '디쥬 보일 더 글래스 누들스?', ko: '당면 삶았어?' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'll", 'Did you'],
          coreCandidates: ['boil the glass noodles', 'use ice-cold water', 'soak the rice cakes']
        },
        fullEn: 'You have to boil the glass noodles for seven minutes.',
        fullPron: '유 햅투 + 보일 더 글래스 누들스 + 포어 세븐 미닛츠',
        fullKo: '쫄깃한 식감을 위해 당면을 끓는 물에 딱 7분간 삶아 주어야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · Rinse in Cold Water',
        visualEmojis: '🚰 💧 🧊',
        imagePath: '/images/kfood/ep7-thumb.jpg',
        actionNote: '찬물에 헹궈 전분기를 빼고 물기 털기',
        coachKo: "세 번째 코어 블록은, 찬물에 헹구다, 린스 뎀 인 콜드 워터입니다. 쫄깃함 유지 비결!",
        coachEn: "Our core action is 'rinse them in cold water'. Keeps them chewy!",
        missionKo: "실전 조립 미션! 찬물에 헹궈서 물기를 쏙 뺄게요!",
        missionEn: "Snap Mission! 'I\'ll rinse them in cold water and drain well.' Snap!",
        keyVocab: 'rinse them in cold water',
        bgGradient: 'linear-gradient(135deg, #0369a1 0%, #075985 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아을' },
          { role: 'core', en: 'rinse them in cold water', pron: '린스 뎀 인 콜드 워터' },
          { role: 'db', en: 'and drain well.', pron: '앤 드레인 웰' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll rinse them in cold water.", fullPron: '아을 린스 뎀 인 콜드 워터', ko: '찬물에 헹굴게.' },
          { bbEn: 'We have to', fullEn: 'We have to rinse them in cold water.', fullPron: '위 햅투 린스 뎀 인 콜드 워터', ko: '찬물에 헹궈야 해.' },
          { bbEn: 'Can you', fullEn: 'Can you rinse them in cold water?', fullPron: '캔유 린스 뎀 인 콜드 워터?', ko: '찬물에 좀 헹궈 줄래?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", 'We have to', 'Can you'],
          coreCandidates: ['rinse them in cold water', 'heat the pan', 'dissolve the sauce']
        },
        fullEn: "I'll rinse them in cold water and drain well.",
        fullPron: '아을 + 린스 뎀 인 콜드 워터 + 앤 드레인 웰',
        fullKo: '삶은 당면을 찬물에 헹궈 전분기를 씻고 물기를 털어 둡니다.'
      },
      {
        stepTitle: 'SCENE 4 · Sauté Colorful Vegetables',
        visualEmojis: '🥕 🫑 🧅',
        imagePath: '/images/kfood/ep7-thumb.jpg',
        actionNote: '당근, 파프리카, 양파, 시금치 채소 볶기',
        coachKo: "네 번째 코어 블록은, 알록달록 채소를 볶다, 쏘테이 컬러풀 페퍼스입니다. 색감이 화려하죠!",
        coachEn: "Our core action is 'sauté colorful peppers'. Look at those bright colors!",
        missionKo: "실전 조립 미션! 다채로운 파프리카와 양파를 볶아야 해요!",
        missionEn: "Snap Mission! 'We have to sauté colorful peppers and sliced onions.' Snap!",
        keyVocab: 'sauté colorful peppers',
        bgGradient: 'linear-gradient(135deg, #15803d 0%, #166534 100%)',
        blocks: [
          { role: 'bb', en: 'We have to', pron: '위 햅투' },
          { role: 'core', en: 'sauté colorful peppers', pron: '쏘테이 컬러풀 페퍼스' },
          { role: 'db', en: 'and sliced onions.', pron: '앤 슬라이스드 어니언스' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to sauté colorful peppers.', fullPron: '위 햅투 쏘테이 컬러풀 페퍼스', ko: '알록달록 채소를 볶아야 해.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna sauté colorful peppers.", fullPron: '암거너 쏘테이 컬러풀 페퍼스', ko: '채소를 볶을게.' },
          { bbEn: 'Did you', fullEn: 'Did you sauté colorful peppers?', fullPron: '디쥬 쏘테이 컬러풀 페퍼스?', ko: '채소 볶았어?' }
        ],
        quizPool: {
          bbCandidates: ['We have to', "I'm gonna", 'Did you'],
          coreCandidates: ['sauté colorful peppers', 'spread the batter thinly', 'add the rice cakes']
        },
        fullEn: 'We have to sauté colorful peppers and sliced onions.',
        fullPron: '위 햅투 + 쏘테이 컬러풀 페퍼스 + 앤 슬라이스드 어니언스',
        fullKo: '채 썬 파프리카와 양파, 시금치를 색감이 살도록 볶아 줍니다.'
      },
      {
        stepTitle: 'SCENE 5 · Stir-Fry Beef and Mushrooms',
        visualEmojis: '🥩 🍄 🔥',
        imagePath: '/images/kfood/ep7-thumb.jpg',
        actionNote: '양념 소고기와 표고버섯 볶기',
        coachKo: "다섯 번째 코어 블록은, 양념 소고기를 볶다, 스터 프라이 매리네이티드 비이프입니다. 고기 향이 일품!",
        coachEn: "Our core action is 'stir-fry marinated beef'. Smells amazing!",
        missionKo: "실전 조립 미션! 양념 소고기와 표고버섯을 볶을 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna stir-fry marinated beef with shiitake mushrooms.' Snap!",
        keyVocab: 'stir-fry marinated beef',
        bgGradient: 'linear-gradient(135deg, #7c2d12 0%, #451a03 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'stir-fry marinated beef', pron: '스터 프라이 매리네이티드 비이프' },
          { role: 'db', en: 'with shiitake mushrooms.', pron: '위드 시이타케 머쉬룸스' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna stir-fry marinated beef.", fullPron: '암거너 스터 프라이 매리네이티드 비이프', ko: '양념 소고기를 볶을게.' },
          { bbEn: 'You have to', fullEn: 'You have to stir-fry marinated beef.', fullPron: '유 햅투 스터 프라이 매리네이티드 비이프', ko: '양념 소고기를 볶아야 해.' },
          { bbEn: 'Are you gonna', fullEn: 'Are you gonna stir-fry marinated beef?', fullPron: '아유 거너 스터 프라이 매리네이티드 비이프?', ko: '양념 소고기 볶을 거야?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'Are you gonna'],
          coreCandidates: ['stir-fry marinated beef', 'flip it over', 'pour the broth']
        },
        fullEn: "I'm gonna stir-fry marinated beef with shiitake mushrooms.",
        fullPron: '암거너 + 스터 프라이 매리네이티드 비이프 + 위드 시이타케 머쉬룸스',
        fullKo: '간장 양념한 소고기와 표고버섯을 센 불에 달달 볶아 줄게요.'
      },
      {
        stepTitle: 'SCENE 6 · Combine in a Large Bowl',
        visualEmojis: '🥣 🥢 ✨',
        imagePath: '/images/kfood/ep7-thumb.jpg',
        actionNote: '큰 볼에 당면과 볶은 모든 재료 합치기',
        coachKo: "여섯 번째 코어 블록은, 모든 재료를 합치다, 컴바인 올 디 인그리디언츠입니다. 큰 볼에 모아 볼까요?",
        coachEn: "Our core action is 'combine all the ingredients'. Let's mix!",
        missionKo: "실전 조립 미션! 큰 볼에 모든 재료를 다 합칠 수 있어요!",
        missionEn: "Snap Mission! 'You can combine all the ingredients in a large bowl.' Snap!",
        keyVocab: 'combine all the ingredients',
        bgGradient: 'linear-gradient(135deg, #4c1d95 0%, #581c87 100%)',
        blocks: [
          { role: 'bb', en: 'You can', pron: '유 캔' },
          { role: 'core', en: 'combine all the ingredients', pron: '컴바인 올 디 인그리디언츠' },
          { role: 'db', en: 'in a large bowl.', pron: '인 어 라아지 볼' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can combine all the ingredients.', fullPron: '유 캔 컴바인 올 디 인그리디언츠', ko: '모든 재료를 합치시면 돼요.' },
          { bbEn: "We're gonna", fullEn: "We're gonna combine all the ingredients.", fullPron: '웨어 거너 컴바인 올 디 인그리디언츠', ko: '모든 재료를 합칠 거야.' },
          { bbEn: 'Can you', fullEn: 'Can you combine all the ingredients?', fullPron: '캔유 컴바인 올 디 인그리디언츠?', ko: '재료들 좀 합쳐 줄래?' }
        ],
        quizPool: {
          bbCandidates: ['You can', "We're gonna", 'Can you'],
          coreCandidates: ['combine all the ingredients', 'mix soy sauce with vinegar', 'simmer on medium heat']
        },
        fullEn: 'You can combine all the ingredients in a large bowl.',
        fullPron: '유 캔 + 컴바인 올 디 인그리디언츠 + 인 어 라아지 볼',
        fullKo: '커다란 믹싱 볼에 삶은 당면과 볶은 고기, 채소를 한데 담습니다.'
      },
      {
        stepTitle: 'SCENE 7 · Sweet Soy & Fragrant Sesame Oil',
        visualEmojis: '🍶 🫒 🤎',
        imagePath: '/images/kfood/ep7-thumb.jpg',
        actionNote: '단짠 간장과 고소한 참깨, 참기름으로 버무리기',
        coachKo: "일곱 번째 코어 블록은, 달콤한 간장으로 간하다, 시즌 위드 스위트 소이 소오스입니다. 윤기 좌르르!",
        coachEn: "Our core action is 'season with sweet soy sauce'. The secret glaze!",
        missionKo: "실전 조립 미션! 달콤한 간장 소스와 참기름으로 간을 맞출 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna season with sweet soy sauce and sesame oil.' Snap!",
        keyVocab: 'season with sweet soy sauce',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #451a03 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'season with sweet soy sauce', pron: '시즌 위드 스위트 소이 소오스' },
          { role: 'db', en: 'and sesame oil.', pron: '앤 세서미 오일' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna season with sweet soy sauce.", fullPron: '웨어 거너 시즌 위드 스위트 소이 소오스', ko: '달콤한 간장으로 간할 거야.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna season with sweet soy sauce.", fullPron: '암거너 시즌 위드 스위트 소이 소오스', ko: '간장 양념으로 간을 맞출게.' },
          { bbEn: 'Did you', fullEn: 'Did you season with sweet soy sauce?', fullPron: '디쥬 시즌 위드 스위트 소이 소오스?', ko: '간장 양념으로 간했어?' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'm gonna", 'Did you'],
          coreCandidates: ['season with sweet soy sauce', 'soak the rice cakes', 'spread the batter thinly']
        },
        fullEn: "We're gonna season with sweet soy sauce and sesame oil.",
        fullPron: '웨어 거너 + 시즌 위드 스위트 소이 소오스 + 앤 세서미 오일',
        fullKo: '진간장, 설탕, 고소한 참기름을 듬뿍 두르고 손으로 골고루 버무려 줍니다.'
      },
      {
        stepTitle: 'SCENE 8 · Savory & Glossy Reaction',
        visualEmojis: '🥢 😋 👑',
        imagePath: '/images/kfood/ep7-thumb.jpg',
        actionNote: '윤기 흐르는 잡채 한 젓가락 시식 리액션',
        coachKo: "여덟 번째 코어 리액션은, 감칠맛 나고 맛있다, 세이보리 앤 딜리셔스입니다! 풍성한 잔칫상 맛!",
        coachEn: "Our core reaction is 'savory and delicious'. Perfect festival flavor!",
        missionKo: "마지막 실전 조립! 한 입 먹을 때마다 감칠맛 나고 맛있어요!",
        missionEn: "Final Snap Mission! 'It tastes so savory and delicious with every bite!' Snap!",
        keyVocab: 'savory and delicious',
        bgGradient: 'linear-gradient(135deg, #b45309 0%, #ca8a04 100%)',
        blocks: [
          { role: 'bb', en: 'It tastes so', pron: '잇 테이스트 쏘' },
          { role: 'core', en: 'savory and delicious', pron: '세이보리 앤 딜리셔스' },
          { role: 'db', en: 'with every bite!', pron: '위드 에브리 바이트' }
        ],
        combos: [
          { bbEn: 'It tastes so', fullEn: 'It tastes so savory and delicious.', fullPron: '잇 테이스트 쏘 세이보리 앤 딜리셔스', ko: '정말 감칠맛 나고 맛있어.' },
          { bbEn: 'This is', fullEn: 'This is so savory and delicious.', fullPron: '디스 이즈 쏘 세이보리 앤 딜리셔스', ko: '이거 완전 감칠맛 나고 맛있다.' },
          { bbEn: "Doesn't it taste", fullEn: "Doesn't it taste savory and delicious?", fullPron: '더즌 잇 테이스트 세이보리 앤 딜리셔스?', ko: '진짜 감칠맛 나고 맛있지 않니?' }
        ],
        quizPool: {
          bbCandidates: ['It tastes so', 'This is', "Doesn't it taste"],
          coreCandidates: ['savory and delicious', 'chewy and spicy', 'crispy on the outside']
        },
        fullEn: 'It tastes so savory and delicious with every bite!',
        fullPron: '잇 테이스트 쏘 + 세이보리 앤 딜리셔스 + 위드 에브리 바이트!',
        fullKo: '탱글탱글한 당면에 참기름 향이 배어 한 입 먹을 때마다 감칠맛이 폭발해요!'
      }
    ]
  },
// ==========================================
  // EP 8. 바삭바삭 양념치킨 (Korean Fried Chicken) - 8 Scenes (~5m 30s)
  // ==========================================
  {
    id: 'korean-fried-chicken',
    epNumber: 'EP.08',
    emoji: '🍗',
    shortTitle: '🍗 Korean Fried Chicken',
    title: 'How to Make Ultra-Crispy Korean Fried Chicken',
    ytTitle: 'How to Make Ultra-Crispy Korean Fried Chicken in Easy English 🍗 | SoundBlock K-Cooking EP.08',
    thumbnailText: 'Ultra-Crispy Yangnyeom Chicken! [I\'m gonna] + [glaze with spicy garlic sauce]',
    thumbnailImage: '/images/kfood/ep8-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let's make ultra-crispy Korean Fried Chicken glazed with sweet and spicy garlic sauce using simple sound blocks. Let's get cooking!",
    outroNarrationKo: "Mission complete! You've mastered all the sound blocks for ultra-crispy Korean Fried Chicken! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Cut into Bite-Sized Pieces',
        visualEmojis: '🍗 🔪 🥣',
        imagePath: '/images/kfood/ep8-thumb.jpg',
        actionNote: '닭고기를 먹기 좋은 한 입 크기로 썰기',
        coachKo: "첫 번째 코어 블록은, 닭고기를 썰다, 컷 더 치킨입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'cut the chicken'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 닭고기를 한 입 크기로 자를 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna cut the chicken into bite-sized pieces.' Snap the blocks!",
        keyVocab: 'cut the chicken',
        bgGradient: 'linear-gradient(135deg, #7c2d12 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'cut the chicken', pron: '컷 더 치킨' },
          { role: 'db', en: 'into bite-sized pieces.', pron: '인투 바이트-사이즈드 피시스' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna cut the chicken.", fullPron: '암거너 컷 더 치킨', ko: '닭고기를 썰 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to cut the chicken.', fullPron: '유 해브 투 컷 더 치킨', ko: '닭고기를 썰어야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you cut the chicken?', fullPron: '캔 유 컷 더 치킨?', ko: '닭고기 좀 썰어 줄 수 있나요?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', 'Can you'],
          coreCandidates: ['cut the chicken', 'soak the rice cakes', 'boil the noodles']
        },
        fullEn: "I'm gonna cut the chicken into bite-sized pieces.",
        fullPron: '암거너 + 컷 더 치킨 + 인투 바이트-사이즈드 피시스.',
        fullKo: '닭고기를 먹기 좋은 한 입 크기로 썰 거예요.'
      },
      {
        stepTitle: 'SCENE 2 · Marinate with Milk & Pepper',
        visualEmojis: '🥛 🧂 ⏰',
        imagePath: '/images/kfood/ep8-thumb.jpg',
        actionNote: '우유와 후추로 닭 비린내를 잡고 부드럽게 재우기',
        coachKo: "두 번째 코어 블록은, 우유에 재우다, 매러네이트 위드 밀크입니다. 첫 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'marinate with milk'. Let's swap the first block!",
        missionKo: "실전 조립 미션! 우유와 흑후추로 닭고기를 재워야 해요!",
        missionEn: "Snap Mission! 'You have to marinate with milk and black pepper.' Snap!",
        keyVocab: 'marinate with milk',
        bgGradient: 'linear-gradient(135deg, #9a3412 0%, #c2410c 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해브 투' },
          { role: 'core', en: 'marinate with milk', pron: '매러네이트 위드 밀크' },
          { role: 'db', en: 'and black pepper.', pron: '앤 블랙 페퍼' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to marinate with milk.', fullPron: '유 해브 투 매러네이트 위드 밀크', ko: '우유에 재워야 해요.' },
          { bbEn: "I'll", fullEn: "I'll marinate with milk.", fullPron: '아일 매러네이트 위드 밀크', ko: '제가 우유에 재울게요.' },
          { bbEn: 'Did you', fullEn: 'Did you marinate with milk?', fullPron: '디쥬 매러네이트 위드 밀크?', ko: '우유에 재웠나요?' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'll", 'Did you'],
          coreCandidates: ['marinate with milk', 'mix pancake batter', 'rinse the noodles']
        },
        fullEn: 'You have to marinate with milk and black pepper.',
        fullPron: '유 해브 투 + 매러네이트 위드 밀크 + 앤 블랙 페퍼.',
        fullKo: '잡내를 잡고 육질을 연하게 하려면 우유와 후추에 재워야 해요.'
      },
      {
        stepTitle: 'SCENE 3 · Coat in Potato Starch',
        visualEmojis: '🥣 🥔 ✨',
        imagePath: '/images/kfood/ep8-thumb.jpg',
        actionNote: '바삭함을 위해 감자 전분을 골고루 입히기',
        coachKo: "세 번째 코어 블록은, 치킨에 튀김옷을 입히다, 코우트 더 치킨입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'coat the chicken'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 감자 전분을 골고루 묻힐 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna coat the chicken in potato starch.' Snap!",
        keyVocab: 'coat the chicken',
        bgGradient: 'linear-gradient(135deg, #b45309 0%, #d97706 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'coat the chicken', pron: '코우트 더 치킨' },
          { role: 'db', en: 'in potato starch.', pron: '인 포테이토 스타치' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna coat the chicken.", fullPron: '웨어 거너 코우트 더 치킨', ko: '튀김옷을 입힐 거예요.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna coat the chicken.", fullPron: '암거너 코우트 더 치킨', ko: '제가 튀김옷을 입힐게요.' },
          { bbEn: 'You should', fullEn: 'You should coat the chicken.', fullPron: '유 슈드 코우트 더 치킨', ko: '튀김옷을 골고루 입혀야 해요.' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'm gonna", 'You should'],
          coreCandidates: ['coat the chicken', 'boil the noodles', 'slice green onions']
        },
        fullEn: "We're gonna coat the chicken in potato starch.",
        fullPron: '웨어 거너 + 코우트 더 치킨 + 인 포테이토 스타치.',
        fullKo: '바삭함을 극대화하기 위해 감자 전분을 골고루 입혀 줄 거예요.'
      },
      {
        stepTitle: 'SCENE 4 · Fry for 8 Minutes (1st Fry)',
        visualEmojis: '🍳 ⏱️ 🔥',
        imagePath: '/images/kfood/ep8-thumb.jpg',
        actionNote: '1차 튀김: 160도 기름에서 8분간 속까지 골고루 익히기',
        coachKo: "네 번째 코어 블록은, 치킨을 튀기다, 프라이 더 치킨입니다. 시작 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'fry the chicken'. Let's swap!",
        missionKo: "실전 조립 미션! 8분 동안 치킨을 튀길 거예요!",
        missionEn: "Snap Mission! 'I\'ll fry the chicken for eight minutes.' Snap!",
        keyVocab: 'fry the chicken',
        bgGradient: 'linear-gradient(135deg, #ea580c 0%, #f97316 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아일' },
          { role: 'core', en: 'fry the chicken', pron: '프라이 더 치킨' },
          { role: 'db', en: 'for eight minutes.', pron: '포 에이트 미닛츠' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll fry the chicken.", fullPron: '아일 프라이 더 치킨', ko: '제가 치킨을 튀길게요.' },
          { bbEn: 'You have to', fullEn: 'You have to fry the chicken.', fullPron: '유 해브 투 프라이 더 치킨', ko: '치킨을 튀겨야 해요.' },
          { bbEn: "We're gonna", fullEn: "We're gonna fry the chicken.", fullPron: '웨어 거너 프라이 더 치킨', ko: '치킨을 튀길 거예요.' }
        ],
        quizPool: {
          bbCandidates: ["I'll", 'You have to', "We're gonna"],
          coreCandidates: ['fry the chicken', 'arrange the green onions', 'marinate the beef']
        },
        fullEn: "I'll fry the chicken for eight minutes.",
        fullPron: '아일 + 프라이 더 치킨 + 포 에이트 미닛츠.',
        fullKo: '1차로 8분 동안 속까지 촉촉하게 익혀 줄게요.'
      },
      {
        stepTitle: 'SCENE 5 · Rest on a Wire Rack',
        visualEmojis: '💨 🌬️ 🥢',
        imagePath: '/images/kfood/ep8-thumb.jpg',
        actionNote: '식힘망에 올려 수분을 날리고 식히기',
        coachKo: "다섯 번째 코어 블록은, 치킨을 한 김 식히다, 레스트 더 치킨입니다. 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'rest the chicken'. Let's swap!",
        missionKo: "실전 조립 미션! 식힘망 위에서 한 김 식혀 줘야 해요!",
        missionEn: "Snap Mission! 'You should rest the chicken on a wire rack.' Snap!",
        keyVocab: 'rest the chicken',
        bgGradient: 'linear-gradient(135deg, #c2410c 0%, #ea580c 100%)',
        blocks: [
          { role: 'bb', en: 'You should', pron: '유 슈드' },
          { role: 'core', en: 'rest the chicken', pron: '레스트 더 치킨' },
          { role: 'db', en: 'on a wire rack.', pron: '온 어 와이어 랙' }
        ],
        combos: [
          { bbEn: 'You should', fullEn: 'You should rest the chicken.', fullPron: '유 슈드 레스트 더 치킨', ko: '치킨을 한 김 식혀야 해요.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna rest the chicken.", fullPron: '암거너 레스트 더 치킨', ko: '치킨을 한 김 식힐게요.' },
          { bbEn: 'Can you', fullEn: 'Can you rest the chicken?', fullPron: '캔 유 레스트 더 치킨?', ko: '치킨 좀 식혀 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ['You should', "I'm gonna", 'Can you'],
          coreCandidates: ['rest the chicken', 'dissolve the sauce', 'pour the batter']
        },
        fullEn: 'You should rest the chicken on a wire rack.',
        fullPron: '유 슈드 + 레스트 더 치킨 + 온 어 와이어 랙.',
        fullKo: '속의 수분이 빠져나가 바삭해지도록 식힘망에 올려 두세요.'
      },
      {
        stepTitle: 'SCENE 6 · Double-Fry for Extra Crunch',
        visualEmojis: '🔥 ⚡ 🌟',
        imagePath: '/images/kfood/ep8-thumb.jpg',
        actionNote: '2차 튀김: 180도 높은 온도에서 2분간 초바삭하게 튀기기',
        coachKo: "여섯 번째 코어 블록은, 두 번 튀기다, 더블-프라이 더 치킨입니다. 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'double-fry the chicken'. Let's swap!",
        missionKo: "실전 조립 미션! 초바삭함을 위해 두 번 튀겨야 해요!",
        missionEn: "Snap Mission! 'We have to double-fry the chicken for extra crunch.' Snap!",
        keyVocab: 'double-fry the chicken',
        bgGradient: 'linear-gradient(135deg, #b91c1c 0%, #dc2626 100%)',
        blocks: [
          { role: 'bb', en: 'We have to', pron: '위 해브 투' },
          { role: 'core', en: 'double-fry the chicken', pron: '더블-프라이 더 치킨' },
          { role: 'db', en: 'for extra crunch.', pron: '포 엑스트라 크런치' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to double-fry the chicken.', fullPron: '위 해브 투 더블-프라이 더 치킨', ko: '두 번 튀겨야 해요.' },
          { bbEn: "I'll", fullEn: "I'll double-fry the chicken.", fullPron: '아일 더블-프라이 더 치킨', ko: '제가 두 번 튀길게요.' },
          { bbEn: 'You can', fullEn: 'You can double-fry the chicken.', fullPron: '유 캔 더블-프라이 더 치킨', ko: '두 번 튀기면 돼요.' }
        ],
        quizPool: {
          bbCandidates: ['We have to', "I'll", 'You can'],
          coreCandidates: ['double-fry the chicken', 'stir-fry colorful veggies', 'flip the pancake']
        },
        fullEn: 'We have to double-fry the chicken for extra crunch.',
        fullPron: '위 해브 투 + 더블-프라이 더 치킨 + 포 엑스트라 크런치.',
        fullKo: '궁극의 바삭한 식감을 완성하기 위해 높은 온도에서 한 번 더 튀깁니다.'
      },
      {
        stepTitle: 'SCENE 7 · Simmer Sweet & Spicy Glaze',
        visualEmojis: '🍯 🧄 🌶️',
        imagePath: '/images/kfood/ep8-thumb.jpg',
        actionNote: '고추장, 케첩, 물엿, 다진 마늘로 윤기 나는 양념 끓이기',
        coachKo: "일곱 번째 코어 블록은, 양념소스를 졸이다, 시머 더 글레이즈입니다. 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'simmer the glaze'. Let's swap!",
        missionKo: "실전 조립 미션! 마늘과 고추장으로 달콤매콤 양념을 끓일 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna simmer the glaze with garlic and chili paste.' Snap!",
        keyVocab: 'simmer the glaze',
        bgGradient: 'linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'simmer the glaze', pron: '시머 더 글레이즈' },
          { role: 'db', en: 'with garlic and chili paste.', pron: '위드 갈릭 앤 칠리 페이스트' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna simmer the glaze.", fullPron: '암거너 시머 더 글레이즈', ko: '양념을 졸일 거예요.' },
          { bbEn: "We're gonna", fullEn: "We're gonna simmer the glaze.", fullPron: '웨어 거너 시머 더 글레이즈', ko: '양념을 같이 졸일 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to simmer the glaze.', fullPron: '유 해브 투 시머 더 글레이즈', ko: '양념을 살짝 끓여야 해요.' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", "We're gonna", 'You have to'],
          coreCandidates: ['simmer the glaze', 'coat with sesame oil', 'dip into soy sauce']
        },
        fullEn: "I'm gonna simmer the glaze with garlic and chili paste.",
        fullPron: '암거너 + 시머 더 글레이즈 + 위드 갈릭 앤 칠리 페이스트.',
        fullKo: '마늘과 고추장, 물엿을 넣고 윤기 나게 양념 소스를 졸여 줍니다.'
      },
      {
        stepTitle: 'SCENE 8 · Crunchy & Sweet Yangnyeom Chicken',
        visualEmojis: '😋 🍗 💥',
        imagePath: '/images/kfood/ep8-thumb.jpg',
        actionNote: '감탄 반응: 달콤매콤한 마늘 양념과 극강의 바삭함!',
        coachKo: "마지막 코어 감탄은, 바삭하고 달콤하다, 크런치 앤 스위트입니다! 소리 내어 말해 보세요!",
        coachEn: "Our core reaction is 'crunchy and sweet'. That crunch is unbelievable!",
        missionKo: "마지막 실전 조립! 마늘 양념과 함께 정말 바삭하고 달콤해요!",
        missionEn: "Final Snap Mission! 'It\'s so crunchy and sweet with savory garlic glaze!' Snap!",
        keyVocab: 'crunchy and sweet',
        bgGradient: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)',
        blocks: [
          { role: 'bb', en: "It's so", pron: '잇츠 쏘' },
          { role: 'core', en: 'crunchy and sweet', pron: '크런치 앤 스위트' },
          { role: 'db', en: 'with savory garlic glaze!', pron: '위드 세이보리 갈릭 글레이즈' }
        ],
        combos: [
          { bbEn: "It's so", fullEn: "It's so crunchy and sweet.", fullPron: '잇츠 쏘 크런치 앤 스위트', ko: '진짜 바삭하고 달콤해.' },
          { bbEn: 'This is', fullEn: 'This is so crunchy and sweet.', fullPron: '디스 이즈 쏘 크런치 앤 스위트', ko: '이거 완전 바삭하고 달콤하다.' },
          { bbEn: 'Is it', fullEn: 'Is it crunchy and sweet?', fullPron: '이즈 잇 크런치 앤 스위트?', ko: '바삭하고 달콤하지 않나요?' }
        ],
        quizPool: {
          bbCandidates: ["It's so", 'This is', 'Is it'],
          coreCandidates: ['crunchy and sweet', 'chewy and spicy', 'savory and delicious']
        },
        fullEn: "It's so crunchy and sweet with savory garlic glaze!",
        fullPron: '잇츠 쏘 + 크런치 앤 스위트 + 위드 세이보리 갈릭 글레이즈!',
        fullKo: '달콤매콤한 마늘 양념 소스가 듬뿍 묻어 겉은 바삭하고 속은 촉촉해요!'
      }
    ]
  },
  // ==========================================
  // EP 9. 지글지글 돌솥 비빔밥 (Sizzling Bibimbap) - 8 Scenes (~5m 30s)
  // ==========================================
  {
    id: 'bibimbap',
    epNumber: 'EP.09',
    emoji: '🥣',
    shortTitle: '🥣 Sizzling Bibimbap',
    title: 'How to Make Sizzling Dolsot Bibimbap',
    ytTitle: 'How to Make Sizzling Korean Bibimbap in Easy English 🥣 | SoundBlock K-Cooking EP.09',
    thumbnailText: 'Sizzling Dolsot Bibimbap! [We\'re gonna] + [mix everything with red chili paste]',
    thumbnailImage: '/images/kfood/ep9-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let's make authentic Korean sizzling Dolsot Bibimbap packed with colorful veggies and spicy gochujang, using simple sound blocks. Let's get cooking!",
    outroNarrationKo: "Mission complete! You've mastered all the sound blocks for sizzling Korean Bibimbap! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Sauté Sliced Carrots',
        visualEmojis: '🥕 🍳 🧂',
        imagePath: '/images/kfood/ep9-thumb.jpg',
        actionNote: '달군 팬에 당근 채를 소금 한 꼬집 넣고 볶기',
        coachKo: "첫 번째 코어 블록은, 당근을 볶다, 소테이 더 캐럿츠입니다. 시작 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'sauté the carrots'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 소금 한 꼬집을 넣고 당근을 볶을 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna sauté the carrots with a pinch of salt.' Snap the blocks!",
        keyVocab: 'sauté the carrots',
        bgGradient: 'linear-gradient(135deg, #c2410c 0%, #ea580c 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'sauté the carrots', pron: '소테이 더 캐럿츠' },
          { role: 'db', en: 'with a pinch of salt.', pron: '위드 어 핀치 오브 솔트' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna sauté the carrots.", fullPron: '암거너 소테이 더 캐럿츠', ko: '당근을 볶을 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to sauté the carrots.', fullPron: '유 해브 투 소테이 더 캐럿츠', ko: '당근을 볶아야 해요.' },
          { bbEn: "I'll", fullEn: "I'll sauté the carrots.", fullPron: '아일 소테이 더 캐럿츠', ko: '제가 당근을 볶을게요.' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', "I'll"],
          coreCandidates: ['sauté the carrots', 'soak the rice cakes', 'cut the chicken']
        },
        fullEn: "I'm gonna sauté the carrots with a pinch of salt.",
        fullPron: '암거너 + 소테이 더 캐럿츠 + 위드 어 핀치 오브 솔트.',
        fullKo: '소금 한 꼬집을 넣고 당근을 아삭하게 볶아 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Season Blanched Spinach',
        visualEmojis: '🥬 🌿 🥢',
        imagePath: '/images/kfood/ep9-thumb.jpg',
        actionNote: '데친 시금치에 참기름과 마늘을 넣고 조물조물 무치기',
        coachKo: "두 번째 코어 블록은, 시금치를 무치다, 시즌 더 스피니치입니다. 첫 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'season the spinach'. Let's swap the first block!",
        missionKo: "실전 조립 미션! 고소한 참기름으로 시금치를 무쳐야 해요!",
        missionEn: "Snap Mission! 'You have to season the spinach with sesame oil.' Snap!",
        keyVocab: 'season the spinach',
        bgGradient: 'linear-gradient(135deg, #15803d 0%, #16a34a 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해브 투' },
          { role: 'core', en: 'season the spinach', pron: '시즌 더 스피니치' },
          { role: 'db', en: 'with sesame oil.', pron: '위드 세서미 오일' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to season the spinach.', fullPron: '유 해브 투 시즌 더 스피니치', ko: '시금치를 무쳐야 해요.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna season the spinach.", fullPron: '암거너 시즌 더 스피니치', ko: '제가 시금치를 무칠게요.' },
          { bbEn: 'Can you', fullEn: 'Can you season the spinach?', fullPron: '캔 유 시즌 더 스피니치?', ko: '시금치 좀 무쳐 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'm gonna", 'Can you'],
          coreCandidates: ['season the spinach', 'fry the chicken', 'mix red chili paste']
        },
        fullEn: 'You have to season the spinach with sesame oil.',
        fullPron: '유 해브 투 + 시즌 더 스피니치 + 위드 세서미 오일.',
        fullKo: '데친 시금치를 고소한 참기름과 함께 조물조물 무쳐 줍니다.'
      },
      {
        stepTitle: 'SCENE 3 · Stir-Fry Marinated Beef',
        visualEmojis: '🥩 🔥 🥢',
        imagePath: '/images/kfood/ep9-thumb.jpg',
        actionNote: '간장 양념에 잰 소고기를 센 불에서 빠르게 볶기',
        coachKo: "세 번째 코어 블록은, 소고기를 볶다, 스터-프라이 더 비프입니다. 시작 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'stir-fry the beef'. Let's swap!",
        missionKo: "실전 조립 미션! 센 불에서 소고기를 빠르게 볶을 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna stir-fry the beef over high heat.' Snap!",
        keyVocab: 'stir-fry the beef',
        bgGradient: 'linear-gradient(135deg, #7c2d12 0%, #991b1b 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'stir-fry the beef', pron: '스터-프라이 더 비프' },
          { role: 'db', en: 'over high heat.', pron: '오버 하이 히트' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna stir-fry the beef.", fullPron: '웨어 거너 스터-프라이 더 비프', ko: '소고기를 볶을 거예요.' },
          { bbEn: "I'll", fullEn: "I'll stir-fry the beef.", fullPron: '아일 스터-프라이 더 비프', ko: '제가 소고기를 볶을게요.' },
          { bbEn: 'You should', fullEn: 'You should stir-fry the beef.', fullPron: '유 슈드 스터-프라이 더 비프', ko: '소고기를 볶아야 해요.' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'll", 'You should'],
          coreCandidates: ['stir-fry the beef', 'rest the chicken', 'pour anchovy broth']
        },
        fullEn: "We're gonna stir-fry the beef over high heat.",
        fullPron: '웨어 거너 + 스터-프라이 더 비프 + 오버 하이 히트.',
        fullKo: '양념된 소고기를 센 불에서 빠르게 볶아 육즙을 가둬 줍니다.'
      },
      {
        stepTitle: 'SCENE 4 · Brush Stone Pot with Oil',
        visualEmojis: '🏺 🫒 ✨',
        imagePath: '/images/kfood/ep9-thumb.jpg',
        actionNote: '돌솥 바닥에 참기름을 골고루 발라 누룽지 준비하기',
        coachKo: "네 번째 코어 블록은, 돌솥에 참기름을 바르다, 브러시 더 스톤 팟입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'brush the stone pot'. Let's swap!",
        missionKo: "실전 조립 미션! 고소한 참기름을 돌솥에 바를 거예요!",
        missionEn: "Snap Mission! 'I\'ll brush the stone pot with fragrant sesame oil.' Snap!",
        keyVocab: 'brush the stone pot',
        bgGradient: 'linear-gradient(135deg, #b45309 0%, #d97706 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아일' },
          { role: 'core', en: 'brush the stone pot', pron: '브러시 더 스톤 팟' },
          { role: 'db', en: 'with fragrant sesame oil.', pron: '위드 프레이그런트 세서미 오일' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll brush the stone pot.", fullPron: '아일 브러시 더 스톤 팟', ko: '돌솥에 참기름을 바를게요.' },
          { bbEn: 'You have to', fullEn: 'You have to brush the stone pot.', fullPron: '유 해브 투 브러시 더 스톤 팟', ko: '돌솥에 기름을 발라야 해요.' },
          { bbEn: 'Did you', fullEn: 'Did you brush the stone pot?', fullPron: '디쥬 브러시 더 스톤 팟?', ko: '돌솥에 기름 발랐나요?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", 'You have to', 'Did you'],
          coreCandidates: ['brush the stone pot', 'simmer on medium heat', 'coat the chicken']
        },
        fullEn: "I'll brush the stone pot with fragrant sesame oil.",
        fullPron: '아일 + 브러시 더 스톤 팟 + 위드 프레이그런트 세서미 오일.',
        fullKo: '돌솥 바닥에 참기름을 듬뿍 발라 바삭한 누룽지를 만듭니다.'
      },
      {
        stepTitle: 'SCENE 5 · Press Warm Rice into Pot',
        visualEmojis: '🍚 🔥 🥄',
        imagePath: '/images/kfood/ep9-thumb.jpg',
        actionNote: '지글거리는 돌솥에 따뜻한 밥을 꼭꼭 눌러 담기',
        coachKo: "다섯 번째 코어 블록은, 따뜻한 밥을 누르다, 프레스 웜 라이스입니다. 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'press warm rice'. Let's swap!",
        missionKo: "실전 조립 미션! 지글거리는 돌솥에 밥을 눌러 담아 주세요!",
        missionEn: "Snap Mission! 'You can press warm rice into the sizzling pot.' Snap!",
        keyVocab: 'press warm rice',
        bgGradient: 'linear-gradient(135deg, #ea580c 0%, #f97316 100%)',
        blocks: [
          { role: 'bb', en: 'You can', pron: '유 캔' },
          { role: 'core', en: 'press warm rice', pron: '프레스 웜 라이스' },
          { role: 'db', en: 'into the sizzling pot.', pron: '인투 더 시즐링 팟' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can press warm rice.', fullPron: '유 캔 프레스 웜 라이스', ko: '따뜻한 밥을 누르면 돼요.' },
          { bbEn: "We're gonna", fullEn: "We're gonna press warm rice.", fullPron: '웨어 거너 프레스 웜 라이스', ko: '따뜻한 밥을 꾹꾹 누를 거예요.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna press warm rice.", fullPron: '암거너 프레스 웜 라이스', ko: '제가 밥을 눌러 담을게요.' }
        ],
        quizPool: {
          bbCandidates: ['You can', "We're gonna", "I'm gonna"],
          coreCandidates: ['press warm rice', 'double-fry the chicken', 'heat plenty of oil']
        },
        fullEn: 'You can press warm rice into the sizzling pot.',
        fullPron: '유 캔 + 프레스 웜 라이스 + 인투 더 시즐링 팟.',
        fullKo: '지글지글 달궈진 돌솥에 따뜻한 밥을 고르게 펴서 눌러 담습니다.'
      },
      {
        stepTitle: 'SCENE 6 · Arrange Veggies in Rainbow Circle',
        visualEmojis: '🌈 🥕 🍄',
        imagePath: '/images/kfood/ep9-thumb.jpg',
        actionNote: '오색 나물과 소고기를 무지개 색깔로 둥글게 둘러 얹기',
        coachKo: "여섯 번째 코어 블록은, 고명을 예쁘게 담다, 어레인지 더 토핑스입니다. 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'arrange the toppings'. Let's swap!",
        missionKo: "실전 조립 미션! 무지개 원 모양으로 고명들을 올릴 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna arrange the toppings in a rainbow circle.' Snap!",
        keyVocab: 'arrange the toppings',
        bgGradient: 'linear-gradient(135deg, #15803d 0%, #ca8a04 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'arrange the toppings', pron: '어레인지 더 토핑스' },
          { role: 'db', en: 'in a rainbow circle.', pron: '인 어 레인보우 서클' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna arrange the toppings.", fullPron: '웨어 거너 어레인지 더 토핑스', ko: '고명을 얹을 거예요.' },
          { bbEn: "I'll", fullEn: "I'll arrange the toppings.", fullPron: '아일 어레인지 더 토핑스', ko: '제가 고명을 얹을게요.' },
          { bbEn: 'You have to', fullEn: 'You have to arrange the toppings.', fullPron: '유 해브 투 어레인지 더 토핑스', ko: '고명을 둘러 얹어야 해요.' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'll", 'You have to'],
          coreCandidates: ['arrange the toppings', 'sprinkle mozzarella cheese', 'marinate with milk']
        },
        fullEn: "We're gonna arrange the toppings in a rainbow circle.",
        fullPron: '웨어 거너 + 어레인지 더 토핑스 + 인 어 레인보우 서클.',
        fullKo: '준비한 오색 나물과 소고기를 무지개 모양으로 둥글게 둘러 얹어 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Place Fried Egg in the Center',
        visualEmojis: '🍳 🥚 💛',
        imagePath: '/images/kfood/ep9-thumb.jpg',
        actionNote: '반숙 계란 후라이를 비빔밥 정중앙에 올리기',
        coachKo: "일곱 번째 코어 블록은, 계란 후라이를 얹다, 플레이스 어 프라이드 에그입니다. 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'place a fried egg'. Let's swap!",
        missionKo: "실전 조립 미션! 중앙에 반숙 계란 후라이를 올릴 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna place a fried egg right in the center.' Snap!",
        keyVocab: 'place a fried egg',
        bgGradient: 'linear-gradient(135deg, #d97706 0%, #eab308 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'place a fried egg', pron: '플레이스 어 프라이드 에그' },
          { role: 'db', en: 'right in the center.', pron: '라이트 인 더 센터' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna place a fried egg.", fullPron: '암거너 플레이스 어 프라이드 에그', ko: '계란 후라이를 올릴 거예요.' },
          { bbEn: 'You can', fullEn: 'You can place a fried egg.', fullPron: '유 캔 플레이스 어 프라이드 에그', ko: '계란 후라이를 올리면 돼요.' },
          { bbEn: 'Did you', fullEn: 'Did you place a fried egg?', fullPron: '디쥬 플레이스 어 프라이드 에그?', ko: '계란 후라이 올렸나요?' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You can', 'Did you'],
          coreCandidates: ['place a fried egg', 'simmer the glaze', 'rinse in cold water']
        },
        fullEn: "I'm gonna place a fried egg right in the center.",
        fullPron: '암거너 + 플레이스 어 프라이드 에그 + 라이트 인 더 센터.',
        fullKo: '노른자가 살아 있는 반숙 계란 후라이를 한가운데에 얹어 줍니다.'
      },
      {
        stepTitle: 'SCENE 8 · Mix with Spicy Chili Paste',
        visualEmojis: '🥄 🌶️ 💥',
        imagePath: '/images/kfood/ep9-thumb.jpg',
        actionNote: '감탄 반응: 매콤한 고추장과 함께 지글지글 비비기',
        coachKo: "마지막 코어 행동은, 다 함께 비비다, 믹스 에브리띵 투게더입니다! 소리 내어 말해 보세요!",
        coachEn: "Our core action is 'mix everything together'. Listen to that sizzle!",
        missionKo: "마지막 실전 조립! 매콤한 고추장과 함께 모두 비벼야 해요!",
        missionEn: "Final Snap Mission! 'We have to mix everything together with spicy red chili paste!' Snap!",
        keyVocab: 'mix everything together',
        bgGradient: 'linear-gradient(135deg, #991b1b 0%, #dc2626 100%)',
        blocks: [
          { role: 'bb', en: 'We have to', pron: '위 해브 투' },
          { role: 'core', en: 'mix everything together', pron: '믹스 에브리띵 투게더' },
          { role: 'db', en: 'with spicy red chili paste!', pron: '위드 스파이시 레드 칠리 페이스트' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to mix everything together.', fullPron: '위 해브 투 믹스 에브리띵 투게더', ko: '모두 같이 비벼야 해요.' },
          { bbEn: 'I wanna', fullEn: 'I wanna mix everything together.', fullPron: '아이 워너 믹스 에브리띵 투게더', ko: '골고루 비비고 싶어요.' },
          { bbEn: "Let's", fullEn: "Let's mix everything together.", fullPron: '렛츠 믹스 에브리띵 투게더', ko: '다 함께 비벼 봐요.' }
        ],
        quizPool: {
          bbCandidates: ['We have to', 'I wanna', "Let's"],
          coreCandidates: ['mix everything together', 'crunchy and sweet', 'savory and delicious']
        },
        fullEn: 'We have to mix everything together with spicy red chili paste!',
        fullPron: '위 해브 투 + 믹스 에브리띵 투게더 + 위드 스파이시 레드 칠리 페이스트!',
        fullKo: '매콤한 고추장과 참기름을 넣고 지글거리는 소리를 들으며 맛있게 비벼 먹어요!'
      }
    ]
  },
  // ==========================================
  // EP 10. 알록달록 야채 김밥 (Classic Kimbap) - 8 Scenes (~5m 30s)
  // ==========================================
  {
    id: 'kimbap',
    epNumber: 'EP.10',
    emoji: '🍙',
    shortTitle: '🍙 Classic Kimbap',
    title: 'How to Roll Perfect Classic Korean Kimbap',
    ytTitle: 'How to Roll Perfect Korean Kimbap in Easy English 🍙 | SoundBlock K-Cooking EP.10',
    thumbnailText: 'Classic Homemade Kimbap! [You have to] + [roll the seaweed tightly]',
    thumbnailImage: '/images/kfood/ep10-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let's roll classic Korean Kimbap packed with colorful vegetables and savory beef using simple sound blocks. Let's get cooking!",
    outroNarrationKo: "Mission complete! You've mastered all the sound blocks for classic Korean Kimbap! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Season Warm Rice',
        visualEmojis: '🍚 🧂 🌿',
        imagePath: '/images/kfood/ep10-thumb.jpg',
        actionNote: '따뜻한 밥에 참기름과 소금으로 밑간하기',
        coachKo: "첫 번째 코어 블록은, 따뜻한 밥을 양념하다, 시즌 더 웜 라이스입니다. 시작 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'season the warm rice'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 참기름과 소금으로 따뜻한 밥을 양념할 거예요!",
        missionEn: "Snap Mission! 'I\'m gonna season the warm rice with sesame oil and salt.' Snap the blocks!",
        keyVocab: 'season the warm rice',
        bgGradient: 'linear-gradient(135deg, #b45309 0%, #d97706 100%)',
        blocks: [
          { role: 'bb', en: "I'm gonna", pron: '암거너' },
          { role: 'core', en: 'season the warm rice', pron: '시즌 더 웜 라이스' },
          { role: 'db', en: 'with sesame oil and salt.', pron: '위드 세서미 오일 앤 솔트' }
        ],
        combos: [
          { bbEn: "I'm gonna", fullEn: "I'm gonna season the warm rice.", fullPron: '암거너 시즌 더 웜 라이스', ko: '따뜻한 밥을 양념할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to season the warm rice.', fullPron: '유 해브 투 시즌 더 웜 라이스', ko: '밥 밑간을 해야 해요.' },
          { bbEn: "I'll", fullEn: "I'll season the warm rice.", fullPron: '아일 시즌 더 웜 라이스', ko: '제가 밥을 양념할게요.' }
        ],
        quizPool: {
          bbCandidates: ["I'm gonna", 'You have to', "I'll"],
          coreCandidates: ['season the warm rice', 'cut the chicken', 'soak the rice cakes']
        },
        fullEn: "I'm gonna season the warm rice with sesame oil and salt.",
        fullPron: '암거너 + 시즌 더 웜 라이스 + 위드 세서미 오일 앤 솔트.',
        fullKo: '따뜻한 밥에 고소한 참기름과 소금으로 밑간을 해 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Place Seaweed on Bamboo Mat',
        visualEmojis: '🥢 🖤 🎋',
        imagePath: '/images/kfood/ep10-thumb.jpg',
        actionNote: '김발 위에 바삭한 김 한 장을 거친 면이 위로 오게 놓기',
        coachKo: "두 번째 코어 블록은, 김을 놓다, 플레이스 더 시위드 시트입니다. 첫 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'place the seaweed sheet'. Let's swap the first block!",
        missionKo: "실전 조립 미션! 김발 위에 김을 놓아야 해요!",
        missionEn: "Snap Mission! 'You have to place the seaweed sheet on a bamboo mat.' Snap!",
        keyVocab: 'place the seaweed sheet',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해브 투' },
          { role: 'core', en: 'place the seaweed sheet', pron: '플레이스 더 시위드 시트' },
          { role: 'db', en: 'on a bamboo mat.', pron: '온 어 밤부 맷' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to place the seaweed sheet.', fullPron: '유 해브 투 플레이스 더 시위드 시트', ko: '김을 올려야 해요.' },
          { bbEn: "I'll", fullEn: "I'll place the seaweed sheet.", fullPron: '아일 플레이스 더 시위드 시트', ko: '제가 김을 올릴게요.' },
          { bbEn: 'Can you', fullEn: 'Can you place the seaweed sheet?', fullPron: '캔 유 플레이스 더 시위드 시트?', ko: '김 좀 올려 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "I'll", 'Can you'],
          coreCandidates: ['place the seaweed sheet', 'sauté the carrots', 'rest the chicken']
        },
        fullEn: 'You have to place the seaweed sheet on a bamboo mat.',
        fullPron: '유 해브 투 + 플레이스 더 시위드 시트 + 온 어 밤부 맷.',
        fullKo: '김발 위에 김의 거친 면이 위를 향하도록 놓아 줍니다.'
      },
      {
        stepTitle: 'SCENE 3 · Spread Rice Evenly',
        visualEmojis: '🍚 🥢 ✨',
        imagePath: '/images/kfood/ep10-thumb.jpg',
        actionNote: '김의 2/3 지점까지 밥을 얇고 고르게 펴기',
        coachKo: "세 번째 코어 블록은, 밥을 골고루 펴다, 스프레드 더 라이스 이븐리입니다. 시작 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'spread the rice evenly'. Let's swap!",
        missionKo: "실전 조립 미션! 김 위에 밥을 고르게 펼 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna spread the rice evenly across the seaweed.' Snap!",
        keyVocab: 'spread the rice evenly',
        bgGradient: 'linear-gradient(135deg, #475569 0%, #64748b 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'spread the rice evenly', pron: '스프레드 더 라이스 이븐리' },
          { role: 'db', en: 'across the seaweed.', pron: '어크로스 더 시위드' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna spread the rice evenly.", fullPron: '웨어 거너 스프레드 더 라이스 이븐리', ko: '밥을 고르게 펼 거예요.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna spread the rice evenly.", fullPron: '암거너 스프레드 더 라이스 이븐리', ko: '제가 밥을 고르게 펼게요.' },
          { bbEn: 'You should', fullEn: 'You should spread the rice evenly.', fullPron: '유 슈드 스프레드 더 라이스 이븐리', ko: '밥을 얇게 펴야 해요.' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'm gonna", 'You should'],
          coreCandidates: ['spread the rice evenly', 'marinate with milk', 'stir-fry the beef']
        },
        fullEn: "We're gonna spread the rice evenly across the seaweed.",
        fullPron: '웨어 거너 + 스프레드 더 라이스 이븐리 + 어크로스 더 시위드.',
        fullKo: '김 위에 양념한 밥을 얇고 균일하게 펴 줍니다.'
      },
      {
        stepTitle: 'SCENE 4 · Line Up Ingredients in Center',
        visualEmojis: '🥒 🥕 🥚 🥩',
        imagePath: '/images/kfood/ep10-thumb.jpg',
        actionNote: '단무지, 당근, 시금치, 계란, 소고기를 중앙에 나란히 올리기',
        coachKo: "네 번째 코어 블록은, 재료들을 나란히 놓다, 라인 업 디 인그리디언츠입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'line up the ingredients'. Let's swap!",
        missionKo: "실전 조립 미션! 중앙을 따라 재료들을 나란히 놓을 거예요!",
        missionEn: "Snap Mission! 'I\'ll line up the ingredients along the center.' Snap!",
        keyVocab: 'line up the ingredients',
        bgGradient: 'linear-gradient(135deg, #15803d 0%, #047857 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아일' },
          { role: 'core', en: 'line up the ingredients', pron: '라인 업 디 인그리디언츠' },
          { role: 'db', en: 'along the center.', pron: '얼롱 더 센터' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll line up the ingredients.", fullPron: '아일 라인 업 디 인그리디언츠', ko: '재료를 나란히 놓을게요.' },
          { bbEn: 'You can', fullEn: 'You can line up the ingredients.', fullPron: '유 캔 라인 업 디 인그리디언츠', ko: '재료들을 올리면 돼요.' },
          { bbEn: 'Did you', fullEn: 'Did you line up the ingredients?', fullPron: '디쥬 라인 업 디 인그리디언츠?', ko: '재료들 나란히 놓았나요?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", 'You can', 'Did you'],
          coreCandidates: ['line up the ingredients', 'brush the stone pot', 'fry the chicken']
        },
        fullEn: "I'll line up the ingredients along the center.",
        fullPron: '아일 + 라인 업 디 인그리디언츠 + 얼롱 더 센터.',
        fullKo: '밥 가운데에 단무지, 당근, 시금치, 계란, 고기를 가지런히 올립니다.'
      },
      {
        stepTitle: 'SCENE 5 · Roll Seaweed Tightly',
        visualEmojis: '🌀 🎋 🤲',
        imagePath: '/images/kfood/ep10-thumb.jpg',
        actionNote: '김발을 이용해 손으로 꾹꾹 누르며 단단하게 말기',
        coachKo: "다섯 번째 코어 블록은, 김을 단단히 말다, 롤 더 시위드 타이트리입니다. 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'roll the seaweed tightly'. Let's swap!",
        missionKo: "실전 조립 미션! 양손으로 꾹꾹 누르며 단단히 말아야 해요!",
        missionEn: "Snap Mission! 'You have to roll the seaweed tightly with both hands.' Snap!",
        keyVocab: 'roll the seaweed tightly',
        bgGradient: 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)',
        blocks: [
          { role: 'bb', en: 'You have to', pron: '유 해브 투' },
          { role: 'core', en: 'roll the seaweed tightly', pron: '롤 더 시위드 타이트리' },
          { role: 'db', en: 'with both hands.', pron: '위드 보우스 핸즈' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to roll the seaweed tightly.', fullPron: '유 해브 투 롤 더 시위드 타이트리', ko: '단단하게 말아야 해요.' },
          { bbEn: "We're gonna", fullEn: "We're gonna roll the seaweed tightly.", fullPron: '웨어 거너 롤 더 시위드 타이트리', ko: '단단하게 말 거예요.' },
          { bbEn: "I'll", fullEn: "I'll roll the seaweed tightly.", fullPron: '아일 롤 더 시위드 타이트리', ko: '제가 단단하게 말게요.' }
        ],
        quizPool: {
          bbCandidates: ['You have to', "We're gonna", "I'll"],
          coreCandidates: ['roll the seaweed tightly', 'press warm rice', 'coat the chicken']
        },
        fullEn: 'You have to roll the seaweed tightly with both hands.',
        fullPron: '유 해브 투 + 롤 더 시위드 타이트리 + 위드 보우스 핸즈.',
        fullKo: '속 재료가 빠지지 않도록 양손으로 꾹꾹 누르며 단단하게 말아 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Brush with Sesame Oil',
        visualEmojis: '🫒 ✨ 🌿',
        imagePath: '/images/kfood/ep10-thumb.jpg',
        actionNote: '말아진 김밥 표면에 고소한 참기름을 듬뿍 바르기',
        coachKo: "여섯 번째 코어 블록은, 참기름을 바르다, 브러시 세서미 오일입니다. 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'brush sesame oil'. Let's swap!",
        missionKo: "실전 조립 미션! 윤기 나는 김밥 위에 참기름을 바를 거예요!",
        missionEn: "Snap Mission! 'We\'re gonna brush sesame oil over the shiny roll.' Snap!",
        keyVocab: 'brush sesame oil',
        bgGradient: 'linear-gradient(135deg, #b45309 0%, #ca8a04 100%)',
        blocks: [
          { role: 'bb', en: "We're gonna", pron: '웨어 거너' },
          { role: 'core', en: 'brush sesame oil', pron: '브러시 세서미 오일' },
          { role: 'db', en: 'over the shiny roll.', pron: '오버 더 샤이니 롤' }
        ],
        combos: [
          { bbEn: "We're gonna", fullEn: "We're gonna brush sesame oil.", fullPron: '웨어 거너 브러시 세서미 오일', ko: '참기름을 바를 거예요.' },
          { bbEn: "I'm gonna", fullEn: "I'm gonna brush sesame oil.", fullPron: '암거너 브러시 세서미 오일', ko: '제가 참기름을 바를게요.' },
          { bbEn: 'You should', fullEn: 'You should brush sesame oil.', fullPron: '유 슈드 브러시 세서미 오일', ko: '참기름을 발라야 해요.' }
        ],
        quizPool: {
          bbCandidates: ["We're gonna", "I'm gonna", 'You should'],
          coreCandidates: ['brush sesame oil', 'season the spinach', 'double-fry the chicken']
        },
        fullEn: "We're gonna brush sesame oil over the shiny roll.",
        fullPron: '웨어 거너 + 브러시 세서미 오일 + 오버 더 샤이니 롤.',
        fullKo: '완성된 김밥 표면에 윤기와 고소함을 더하기 위해 참기름을 바릅니다.'
      },
      {
        stepTitle: 'SCENE 7 · Slice into Bite-Sized Pieces',
        visualEmojis: '🔪 🍙 🥢',
        imagePath: '/images/kfood/ep10-thumb.jpg',
        actionNote: '칼에 참기름을 살짝 묻히고 한 입 크기로 썰기',
        coachKo: "일곱 번째 코어 블록은, 김밥을 썰다, 슬라이스 더 김밥 롤입니다. 블록을 바꿔 보세요!",
        coachEn: "Our core action is 'slice the kimbap roll'. Let's swap!",
        missionKo: "실전 조립 미션! 한 입 크기로 김밥을 예쁘게 썰 거예요!",
        missionEn: "Snap Mission! 'I\'ll slice the kimbap roll into bite-sized pieces.' Snap!",
        keyVocab: 'slice the kimbap roll',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I'll", pron: '아일' },
          { role: 'core', en: 'slice the kimbap roll', pron: '슬라이스 더 김밥 롤' },
          { role: 'db', en: 'into bite-sized pieces.', pron: '인투 바이트-사이즈드 피시스' }
        ],
        combos: [
          { bbEn: "I'll", fullEn: "I'll slice the kimbap roll.", fullPron: '아일 슬라이스 더 김밥 롤', ko: '제가 김밥을 썰게요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice the kimbap roll.', fullPron: '유 해브 투 슬라이스 더 김밥 롤', ko: '김밥을 썰어야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you slice the kimbap roll?', fullPron: '캔 유 슬라이스 더 김밥 롤?', ko: '김밥 좀 썰어 줄 수 있나요?' }
        ],
        quizPool: {
          bbCandidates: ["I'll", 'You have to', 'Can you'],
          coreCandidates: ['slice the kimbap roll', 'arrange the toppings', 'simmer the glaze']
        },
        fullEn: "I'll slice the kimbap roll into bite-sized pieces.",
        fullPron: '아일 + 슬라이스 더 김밥 롤 + 인투 바이트-사이즈드 피시스.',
        fullKo: '칼에 기름을 살짝 묻혀 터지지 않게 한 입 크기로 예쁘게 썰어 줍니다.'
      },
      {
        stepTitle: 'SCENE 8 · Nutty & Savory Homemade Kimbap',
        visualEmojis: '😋 🍙 💚',
        imagePath: '/images/kfood/ep10-thumb.jpg',
        actionNote: '감탄 반응: 고소하고 담백한 집김밥의 풍미!',
        coachKo: "마지막 코어 감탄은, 고소하고 풍미 가득하다, 너티 앤 세이보리입니다! 소리 내어 말해 보세요!",
        coachEn: "Our core reaction is 'nutty and savory'. It tastes so fresh and delicious!",
        missionKo: "마지막 실전 조립! 한 입 먹을 때마다 고소하고 담백해요!",
        missionEn: "Final Snap Mission! 'It\'s so nutty and savory with every single bite!' Snap!",
        keyVocab: 'nutty and savory',
        bgGradient: 'linear-gradient(135deg, #15803d 0%, #166534 100%)',
        blocks: [
          { role: 'bb', en: "It's so", pron: '잇츠 쏘' },
          { role: 'core', en: 'nutty and savory', pron: '너티 앤 세이보리' },
          { role: 'db', en: 'with every single bite!', pron: '위드 에브리 싱글 바이트' }
        ],
        combos: [
          { bbEn: "It's so", fullEn: "It's so nutty and savory.", fullPron: '잇츠 쏘 너티 앤 세이보리', ko: '진짜 고소하고 담백해.' },
          { bbEn: 'This is', fullEn: 'This is so nutty and savory.', fullPron: '디스 이즈 쏘 너티 앤 세이보리', ko: '이거 완전 고소하고 담백하다.' },
          { bbEn: 'Is it', fullEn: 'Is it nutty and savory?', fullPron: '이즈 잇 너티 앤 세이보리?', ko: '고소하고 담백하지 않나요?' }
        ],
        quizPool: {
          bbCandidates: ["It's so", 'This is', 'Is it'],
          coreCandidates: ['nutty and savory', 'crunchy and sweet', 'savory and delicious']
        },
        fullEn: "It's so nutty and savory with every single bite!",
        fullPron: '잇츠 쏘 + 너티 앤 세이보리 + 위드 에브리 싱글 바이트!',
        fullKo: '신선한 채소와 소고기, 고소한 참기름 향이 어우러져 한 입 먹을 때마다 입안 가득 행복해져요!'
      }
    ]
  },
  // ==========================================
  // EP.11. 🍲 Soybean Paste Stew
  // ==========================================
  {
    id: 'doenjang-jjigae',
    epNumber: 'EP.11',
    emoji: '🍲',
    shortTitle: '🍲 Soybean Paste Stew',
    title: 'How to Cook Authentic Korean Soybean Paste Stew',
    ytTitle: 'How to Make Authentic Korean Doenjang Jjigae in Easy English 🍲 | SoundBlock K-Cooking EP.11',
    thumbnailText: 'Rustic Doenjang Jjigae! [You have to] + [dissolve soybean paste into anchovy broth]',
    thumbnailImage: '/images/kfood/ep11-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make comforting Korean Doenjang Jjigae, savory soybean paste stew with tofu and vegetables, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for classic Doenjang Jjigae! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Pour Anchovy Broth',
        visualEmojis: '🐟 💧 🏺',
        imagePath: '/images/kfood/ep11-thumb.jpg',
        actionNote: '뚝배기에 구수한 멸치 다시마 육수 붓기',
        coachKo: "코어 블록은 'pour the anchovy broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour the anchovy broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뚝배기에 감칠맛 나는 멸치 다시마 육수를 부어 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna pour the anchovy broth into an earthen pot.' Snap!",
        keyVocab: 'pour the anchovy broth',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'pour the anchovy broth', pron: '푸어 디 앤초비 브로쓰' },
          { role: 'db', en: 'into an earthen pot.', pron: '인투 언 어슨 팟' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour the anchovy broth.', fullPron: '암거너 푸어 디 앤초비 브로쓰', ko: 'pour the anchovy broth 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour the anchovy broth.', fullPron: '유 해브 투 푸어 디 앤초비 브로쓰', ko: 'pour the anchovy broth 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you pour the anchovy broth?', fullPron: '캔 유 푸어 디 앤초비 브로쓰?', ko: 'pour the anchovy broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['pour the anchovy broth', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna pour the anchovy broth into an earthen pot.",
        fullPron: '암거너 + 푸어 디 앤초비 브로쓰 + 인투 언 어슨 팟.',
        fullKo: '뚝배기에 감칠맛 나는 멸치 다시마 육수를 부어 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Dissolve Soybean Paste',
        visualEmojis: '🥄 🟤 ✨',
        imagePath: '/images/kfood/ep11-thumb.jpg',
        actionNote: '거름망을 이용해 된장을 뭉침 없이 잘 풀기',
        coachKo: "코어 블록은 'dissolve the soybean paste'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'dissolve the soybean paste'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 거름망을 이용해 뭉친 콩 알갱이를 곱게 걸러내며 된장을 풀어 줍니다.",
        missionEn: "Snap Mission! 'You have to dissolve the soybean paste using a fine strainer.' Snap!",
        keyVocab: 'dissolve the soybean paste',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'dissolve the soybean paste', pron: '디졸브 더 소이빈 페이스트' },
          { role: 'db', en: 'using a fine strainer.', pron: '유징 어 파인 스트레이너' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to dissolve the soybean paste.', fullPron: '유 해브 투 디졸브 더 소이빈 페이스트', ko: 'dissolve the soybean paste 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to dissolve the soybean paste.', fullPron: '유 해브 투 디졸브 더 소이빈 페이스트', ko: 'dissolve the soybean paste 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you dissolve the soybean paste?', fullPron: '캔 유 디졸브 더 소이빈 페이스트?', ko: 'dissolve the soybean paste 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['dissolve the soybean paste', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to dissolve the soybean paste using a fine strainer.",
        fullPron: '유 해브 투 + 디졸브 더 소이빈 페이스트 + 유징 어 파인 스트레이너.',
        fullKo: '거름망을 이용해 뭉친 콩 알갱이를 곱게 걸러내며 된장을 풀어 줍니다.'
      },
      {
        stepTitle: 'SCENE 3 · Add Diced Potatoes First',
        visualEmojis: '🥔 🔪 ⏱️',
        imagePath: '/images/kfood/ep11-thumb.jpg',
        actionNote: '익는 데 시간이 걸리는 깍둑썬 감자를 먼저 넣기',
        coachKo: "코어 블록은 'add the diced potatoes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add the diced potatoes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 속까지 부드럽게 잘 익도록 깍둑썬 감자를 먼저 국물에 넣어 줍니다.",
        missionEn: "Snap Mission! 'We\'re gonna add the diced potatoes first so they cook through.' Snap!",
        keyVocab: 'add the diced potatoes',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'add the diced potatoes', pron: '애드 더 다이스드 포테이토우스' },
          { role: 'db', en: 'first so they cook through.', pron: '퍼스트 쏘우 데이 쿡 쓰루' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna add the diced potatoes.', fullPron: '웨어 거너 애드 더 다이스드 포테이토우스', ko: 'add the diced potatoes 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to add the diced potatoes.', fullPron: '유 해브 투 애드 더 다이스드 포테이토우스', ko: 'add the diced potatoes 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you add the diced potatoes?', fullPron: '캔 유 애드 더 다이스드 포테이토우스?', ko: 'add the diced potatoes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['add the diced potatoes', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna add the diced potatoes first so they cook through.",
        fullPron: '웨어 거너 + 애드 더 다이스드 포테이토우스 + 퍼스트 쏘우 데이 쿡 쓰루.',
        fullKo: '속까지 부드럽게 잘 익도록 깍둑썬 감자를 먼저 국물에 넣어 줍니다.'
      },
      {
        stepTitle: 'SCENE 4 · Drop in Sliced Zucchini',
        visualEmojis: '🥒 🍄 🌿',
        imagePath: '/images/kfood/ep11-thumb.jpg',
        actionNote: '애호박과 표고버섯을 썰어 넣기',
        coachKo: "코어 블록은 'drop in sliced zucchini'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'drop in sliced zucchini'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 반달 모양으로 썬 애호박과 쫄깃한 표고버섯을 뚝배기에 퐁당 넣어 줍니다.",
        missionEn: "Snap Mission! 'I\'ll drop in sliced zucchini and mushrooms.' Snap!",
        keyVocab: 'drop in sliced zucchini',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'drop in sliced zucchini', pron: '드랍 인 슬라이스트 주키니' },
          { role: 'db', en: 'and mushrooms.', pron: '앤 머쉬룸스' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll drop in sliced zucchini.', fullPron: '아일 드랍 인 슬라이스트 주키니', ko: 'drop in sliced zucchini 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to drop in sliced zucchini.', fullPron: '유 해브 투 드랍 인 슬라이스트 주키니', ko: 'drop in sliced zucchini 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you drop in sliced zucchini?', fullPron: '캔 유 드랍 인 슬라이스트 주키니?', ko: 'drop in sliced zucchini 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['drop in sliced zucchini', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll drop in sliced zucchini and mushrooms.",
        fullPron: '아일 + 드랍 인 슬라이스트 주키니 + 앤 머쉬룸스.',
        fullKo: '반달 모양으로 썬 애호박과 쫄깃한 표고버섯을 뚝배기에 퐁당 넣어 줍니다.'
      },
      {
        stepTitle: 'SCENE 5 · Add Soft Tofu Cubes',
        visualEmojis: '⬜ 🍲 🥢',
        imagePath: '/images/kfood/ep11-thumb.jpg',
        actionNote: '보글보글 끓는 국물에 두부를 큼직하게 썰어 넣기',
        coachKo: "코어 블록은 'add soft tofu cubes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add soft tofu cubes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 보글보글 끓어오르는 찌개에 부드러운 두부를 큼직하게 썰어 넣습니다.",
        missionEn: "Snap Mission! 'You can add soft tofu cubes right into the bubbling broth.' Snap!",
        keyVocab: 'add soft tofu cubes',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'add soft tofu cubes', pron: '애드 소프트 토푸 큐브스' },
          { role: 'db', en: 'right into the bubbling broth.', pron: '라이트 인투 더 버블링 브로쓰' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can add soft tofu cubes.', fullPron: '유 캔 애드 소프트 토푸 큐브스', ko: 'add soft tofu cubes 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to add soft tofu cubes.', fullPron: '유 해브 투 애드 소프트 토푸 큐브스', ko: 'add soft tofu cubes 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you add soft tofu cubes?', fullPron: '캔 유 애드 소프트 토푸 큐브스?', ko: 'add soft tofu cubes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['add soft tofu cubes', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can add soft tofu cubes right into the bubbling broth.",
        fullPron: '유 캔 + 애드 소프트 토푸 큐브스 + 라이트 인투 더 버블링 브로쓰.',
        fullKo: '보글보글 끓어오르는 찌개에 부드러운 두부를 큼직하게 썰어 넣습니다.'
      },
      {
        stepTitle: 'SCENE 6 · Toss in Garlic & Chili',
        visualEmojis: '🧄 🌶️ 🔥',
        imagePath: '/images/kfood/ep11-thumb.jpg',
        actionNote: '칼칼한 청양고추와 다진 마늘로 개운함 더하기',
        coachKo: "코어 블록은 'toss in minced garlic'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toss in minced garlic'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 칼칼하고 개운한 뒷맛을 위해 다진 마늘과 청양고추를 넣어 줍니다.",
        missionEn: "Snap Mission! 'We have to toss in minced garlic and green chili.' Snap!",
        keyVocab: 'toss in minced garlic',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'toss in minced garlic', pron: '토스 인 민스트 갈릭' },
          { role: 'db', en: 'and green chili.', pron: '앤 그린 칠리' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to toss in minced garlic.', fullPron: '위 해브 투 토스 인 민스트 갈릭', ko: 'toss in minced garlic 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to toss in minced garlic.', fullPron: '유 해브 투 토스 인 민스트 갈릭', ko: 'toss in minced garlic 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you toss in minced garlic?', fullPron: '캔 유 토스 인 민스트 갈릭?', ko: 'toss in minced garlic 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['toss in minced garlic', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to toss in minced garlic and green chili.",
        fullPron: '위 해브 투 + 토스 인 민스트 갈릭 + 앤 그린 칠리.',
        fullKo: '칼칼하고 개운한 뒷맛을 위해 다진 마늘과 청양고추를 넣어 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Simmer on Low Heat',
        visualEmojis: '🔥 ⏱️ 🍲',
        imagePath: '/images/kfood/ep11-thumb.jpg',
        actionNote: '약불에서 5분간 뭉근하게 끓여 맛 어우러지게 하기',
        coachKo: "코어 블록은 'simmer on low heat'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'simmer on low heat'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 채소와 두부에 된장 맛이 깊숙이 배어들도록 약불에서 5분간 더 끓여 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna simmer on low heat for five more minutes.' Snap!",
        keyVocab: 'simmer on low heat',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'simmer on low heat', pron: '시머 온 로우 히트' },
          { role: 'db', en: 'for five more minutes.', pron: '포 파이브 모어 미닛츠' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna simmer on low heat.', fullPron: '암거너 시머 온 로우 히트', ko: 'simmer on low heat 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to simmer on low heat.', fullPron: '유 해브 투 시머 온 로우 히트', ko: 'simmer on low heat 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you simmer on low heat?', fullPron: '캔 유 시머 온 로우 히트?', ko: 'simmer on low heat 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['simmer on low heat', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna simmer on low heat for five more minutes.",
        fullPron: '암거너 + 시머 온 로우 히트 + 포 파이브 모어 미닛츠.',
        fullKo: '채소와 두부에 된장 맛이 깊숙이 배어들도록 약불에서 5분간 더 끓여 줍니다.'
      },
      {
        stepTitle: 'SCENE 8 · Comforting & Deeply Savory Stew',
        visualEmojis: '😋 🍲 ✨',
        imagePath: '/images/kfood/ep11-thumb.jpg',
        actionNote: '감탄 반응: 속이 확 풀리는 구수하고 깊은 집밥의 맛!',
        coachKo: "코어 블록은 'comforting and rich'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'comforting and rich'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 구수한 전통 된장과 부드러운 두부가 어우러져 속이 든든하게 풀려요!",
        missionEn: "Snap Mission! 'It\'s so comforting and rich with deeply savory fermented broth!' Snap!",
        keyVocab: 'comforting and rich',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'comforting and rich', pron: '컴포팅 앤 리치' },
          { role: 'db', en: 'with deeply savory fermented broth!', pron: '위드 디플리 세이보리 퍼멘티드 브로쓰' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so comforting and rich.', fullPron: '잇츠 쏘 컴포팅 앤 리치', ko: 'comforting and rich 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to comforting and rich.', fullPron: '유 해브 투 컴포팅 앤 리치', ko: 'comforting and rich 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you comforting and rich?', fullPron: '캔 유 컴포팅 앤 리치?', ko: 'comforting and rich 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['comforting and rich', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so comforting and rich with deeply savory fermented broth!",
        fullPron: '잇츠 쏘 + 컴포팅 앤 리치 + 위드 디플리 세이보리 퍼멘티드 브로쓰.',
        fullKo: '구수한 전통 된장과 부드러운 두부가 어우러져 속이 든든하게 풀려요!'
      }
    ]
  },
  // ==========================================
  // EP.12. 🥘 Army Base Stew
  // ==========================================
  {
    id: 'budae-jjigae',
    epNumber: 'EP.12',
    emoji: '🥘',
    shortTitle: '🥘 Army Base Stew',
    title: 'How to Make Loaded Korean Army Base Stew',
    ytTitle: 'How to Make Korean Army Base Stew in Easy English 🥘 | SoundBlock K-Cooking EP.12',
    thumbnailText: 'Loaded Budae Jjigae! [We\'re gonna] + [add ramen noodles and sliced sausage]',
    thumbnailImage: '/images/kfood/ep12-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make hearty Korean Army Base Stew, loaded with sausages, spam, ramen, and melted cheese using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for spicy Budae Jjigae! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Slice Spam & Sausages',
        visualEmojis: '🥓 🌭 🔪',
        imagePath: '/images/kfood/ep12-thumb.jpg',
        actionNote: '스팸과 소시지를 먹기 좋은 굵기로 얇게 썰기',
        coachKo: "코어 블록은 'slice the spam and sausages'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice the spam and sausages'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 스팸과 프랑크 소시지를 한 입 크기로 먹기 좋게 썰어 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna slice the spam and sausages into thin rounds.' Snap!",
        keyVocab: 'slice the spam and sausages',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'slice the spam and sausages', pron: '슬라이스 더 스팸 앤 소시지스' },
          { role: 'db', en: 'into thin rounds.', pron: '인투 씬 라운즈' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice the spam and sausages.', fullPron: '암거너 슬라이스 더 스팸 앤 소시지스', ko: 'slice the spam and sausages 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice the spam and sausages.', fullPron: '유 해브 투 슬라이스 더 스팸 앤 소시지스', ko: 'slice the spam and sausages 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you slice the spam and sausages?', fullPron: '캔 유 슬라이스 더 스팸 앤 소시지스?', ko: 'slice the spam and sausages 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['slice the spam and sausages', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna slice the spam and sausages into thin rounds.",
        fullPron: '암거너 + 슬라이스 더 스팸 앤 소시지스 + 인투 씬 라운즈.',
        fullKo: '스팸과 프랑크 소시지를 한 입 크기로 먹기 좋게 썰어 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Arrange in Shallow Pot',
        visualEmojis: '🥘 🥢 ✨',
        imagePath: '/images/kfood/ep12-thumb.jpg',
        actionNote: '넓은 냄비에 햄, 소시지, 두부, 대파를 둘러 담기',
        coachKo: "코어 블록은 'arrange the ingredients'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'arrange the ingredients'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 넓고 얕은 전골 냄비 바깥쪽으로 햄, 소시지, 두부를 가지런히 둘러 담습니다.",
        missionEn: "Snap Mission! 'You have to arrange the ingredients neatly in a shallow pot.' Snap!",
        keyVocab: 'arrange the ingredients',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'arrange the ingredients', pron: '어레인지 디 인그리디언츠' },
          { role: 'db', en: 'neatly in a shallow pot.', pron: '니틀리 인 어 샬로우 팟' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to arrange the ingredients.', fullPron: '유 해브 투 어레인지 디 인그리디언츠', ko: 'arrange the ingredients 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to arrange the ingredients.', fullPron: '유 해브 투 어레인지 디 인그리디언츠', ko: 'arrange the ingredients 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you arrange the ingredients?', fullPron: '캔 유 어레인지 디 인그리디언츠?', ko: 'arrange the ingredients 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['arrange the ingredients', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to arrange the ingredients neatly in a shallow pot.",
        fullPron: '유 해브 투 + 어레인지 디 인그리디언츠 + 니틀리 인 어 샬로우 팟.',
        fullKo: '넓고 얕은 전골 냄비 바깥쪽으로 햄, 소시지, 두부를 가지런히 둘러 담습니다.'
      },
      {
        stepTitle: 'SCENE 3 · Add Baked Beans & Kimchi',
        visualEmojis: '🥫 🥬 🌶️',
        imagePath: '/images/kfood/ep12-thumb.jpg',
        actionNote: '신김치와 베이크드 빈스를 가운데에 듬뿍 얹기',
        coachKo: "코어 블록은 'add baked beans'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add baked beans'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 부대찌개의 핵심인 베이크드 빈스와 새콤한 신김치를 가운데에 올려 줍니다.",
        missionEn: "Snap Mission! 'We\'re gonna add baked beans and sour kimchi in the center.' Snap!",
        keyVocab: 'add baked beans',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'add baked beans', pron: '애드 베이크드 빈스' },
          { role: 'db', en: 'and sour kimchi in the center.', pron: '앤 사워 김치 인 더 센터' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna add baked beans.', fullPron: '웨어 거너 애드 베이크드 빈스', ko: 'add baked beans 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to add baked beans.', fullPron: '유 해브 투 애드 베이크드 빈스', ko: 'add baked beans 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you add baked beans?', fullPron: '캔 유 애드 베이크드 빈스?', ko: 'add baked beans 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['add baked beans', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna add baked beans and sour kimchi in the center.",
        fullPron: '웨어 거너 + 애드 베이크드 빈스 + 앤 사워 김치 인 더 센터.',
        fullKo: '부대찌개의 핵심인 베이크드 빈스와 새콤한 신김치를 가운데에 올려 줍니다.'
      },
      {
        stepTitle: 'SCENE 4 · Pour Beef Bone Broth',
        visualEmojis: '🥛 🍲 💧',
        imagePath: '/images/kfood/ep12-thumb.jpg',
        actionNote: '깊고 진한 사골 육수를 냄비 가장자리로 붓기',
        coachKo: "코어 블록은 'pour the beef bone broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour the beef bone broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 진하고 뽀얀 사골 육수를 냄비 가장자리를 따라 자작하게 부어 줍니다.",
        missionEn: "Snap Mission! 'I\'ll pour the beef bone broth all around the rim.' Snap!",
        keyVocab: 'pour the beef bone broth',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'pour the beef bone broth', pron: '푸어 더 비프 본 브로쓰' },
          { role: 'db', en: 'all around the rim.', pron: '올 어라운드 더 림' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll pour the beef bone broth.', fullPron: '아일 푸어 더 비프 본 브로쓰', ko: 'pour the beef bone broth 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour the beef bone broth.', fullPron: '유 해브 투 푸어 더 비프 본 브로쓰', ko: 'pour the beef bone broth 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you pour the beef bone broth?', fullPron: '캔 유 푸어 더 비프 본 브로쓰?', ko: 'pour the beef bone broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['pour the beef bone broth', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll pour the beef bone broth all around the rim.",
        fullPron: '아일 + 푸어 더 비프 본 브로쓰 + 올 어라운드 더 림.',
        fullKo: '진하고 뽀얀 사골 육수를 냄비 가장자리를 따라 자작하게 부어 줍니다.'
      },
      {
        stepTitle: 'SCENE 5 · Dissolve Spicy Paste',
        visualEmojis: '🌶️ 🧄 🥄',
        imagePath: '/images/kfood/ep12-thumb.jpg',
        actionNote: '고춧가루, 고추장, 간장, 다진 마늘 양념장을 잘 풀기',
        coachKo: "코어 블록은 'dissolve the spicy seasoning paste'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'dissolve the spicy seasoning paste'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 칼칼한 고춧가루와 다진 마늘로 만든 양념장을 육수에 골고루 풀어 줍니다.",
        missionEn: "Snap Mission! 'You can dissolve the spicy seasoning paste with chili flakes.' Snap!",
        keyVocab: 'dissolve the spicy seasoning paste',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'dissolve the spicy seasoning paste', pron: '디졸브 더 스파이시 시즈닝 페이스트' },
          { role: 'db', en: 'with chili flakes.', pron: '위드 칠리 플레이크스' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can dissolve the spicy seasoning paste.', fullPron: '유 캔 디졸브 더 스파이시 시즈닝 페이스트', ko: 'dissolve the spicy seasoning paste 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to dissolve the spicy seasoning paste.', fullPron: '유 해브 투 디졸브 더 스파이시 시즈닝 페이스트', ko: 'dissolve the spicy seasoning paste 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you dissolve the spicy seasoning paste?', fullPron: '캔 유 디졸브 더 스파이시 시즈닝 페이스트?', ko: 'dissolve the spicy seasoning paste 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['dissolve the spicy seasoning paste', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can dissolve the spicy seasoning paste with chili flakes.",
        fullPron: '유 캔 + 디졸브 더 스파이시 시즈닝 페이스트 + 위드 칠리 플레이크스.',
        fullKo: '칼칼한 고춧가루와 다진 마늘로 만든 양념장을 육수에 골고루 풀어 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Add Instant Ramen Noodles',
        visualEmojis: '🍜 🔥 ✨',
        imagePath: '/images/kfood/ep12-thumb.jpg',
        actionNote: '바글바글 끓을 때 라면 사리를 중앙에 투하하기',
        coachKo: "코어 블록은 'add instant ramen noodles'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add instant ramen noodles'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 국물이 바글바글 끓어오를 때 라면 사리를 중앙에 쏙 넣어 줍니다.",
        missionEn: "Snap Mission! 'We have to add instant ramen noodles right on top.' Snap!",
        keyVocab: 'add instant ramen noodles',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'add instant ramen noodles', pron: '애드 인스턴트 라면 누들스' },
          { role: 'db', en: 'right on top.', pron: '라이트 온 탑' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to add instant ramen noodles.', fullPron: '위 해브 투 애드 인스턴트 라면 누들스', ko: 'add instant ramen noodles 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to add instant ramen noodles.', fullPron: '유 해브 투 애드 인스턴트 라면 누들스', ko: 'add instant ramen noodles 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you add instant ramen noodles?', fullPron: '캔 유 애드 인스턴트 라면 누들스?', ko: 'add instant ramen noodles 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['add instant ramen noodles', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to add instant ramen noodles right on top.",
        fullPron: '위 해브 투 + 애드 인스턴트 라면 누들스 + 라이트 온 탑.',
        fullKo: '국물이 바글바글 끓어오를 때 라면 사리를 중앙에 쏙 넣어 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Place Cheddar Cheese on Top',
        visualEmojis: '🧀 💛 🔥',
        imagePath: '/images/kfood/ep12-thumb.jpg',
        actionNote: '라면 위에 노란 체다 치즈 한 장 올려 고소함 더하기',
        coachKo: "코어 블록은 'place a slice of cheese'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'place a slice of cheese'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 익어가는 라면 면발 위에 고소한 체다 치즈 한 장을 얹어 부드러움을 더합니다.",
        missionEn: "Snap Mission! 'I\'m gonna place a slice of cheese directly over the noodles.' Snap!",
        keyVocab: 'place a slice of cheese',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'place a slice of cheese', pron: '플레이스 어 슬라이스 오브 치즈' },
          { role: 'db', en: 'directly over the noodles.', pron: '디렉트리 오버 더 누들스' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna place a slice of cheese.', fullPron: '암거너 플레이스 어 슬라이스 오브 치즈', ko: 'place a slice of cheese 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to place a slice of cheese.', fullPron: '유 해브 투 플레이스 어 슬라이스 오브 치즈', ko: 'place a slice of cheese 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you place a slice of cheese?', fullPron: '캔 유 플레이스 어 슬라이스 오브 치즈?', ko: 'place a slice of cheese 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['place a slice of cheese', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna place a slice of cheese directly over the noodles.",
        fullPron: '암거너 + 플레이스 어 슬라이스 오브 치즈 + 디렉트리 오버 더 누들스.',
        fullKo: '익어가는 라면 면발 위에 고소한 체다 치즈 한 장을 얹어 부드러움을 더합니다.'
      },
      {
        stepTitle: 'SCENE 8 · Hearty & Savory Budae Jjigae',
        visualEmojis: '😋 🥘 💥',
        imagePath: '/images/kfood/ep12-thumb.jpg',
        actionNote: '감탄 반응: 진한 햄 소시지와 매콤 치즈 라면의 궁극 조합!',
        coachKo: "코어 블록은 'hearty and savory'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'hearty and savory'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 짭조름한 햄과 소시지, 치즈가 사르르 녹아든 얼큰한 국물과 꼬들꼬들한 라면이 예술이에요!",
        missionEn: "Snap Mission! 'It\'s so hearty and savory with cheesy ramen noodles!' Snap!",
        keyVocab: 'hearty and savory',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'hearty and savory', pron: '하티 앤 세이보리' },
          { role: 'db', en: 'with cheesy ramen noodles!', pron: '위드 치지 라면 누들스' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so hearty and savory.', fullPron: '잇츠 쏘 하티 앤 세이보리', ko: 'hearty and savory 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to hearty and savory.', fullPron: '유 해브 투 하티 앤 세이보리', ko: 'hearty and savory 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you hearty and savory?', fullPron: '캔 유 하티 앤 세이보리?', ko: 'hearty and savory 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['hearty and savory', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so hearty and savory with cheesy ramen noodles!",
        fullPron: '잇츠 쏘 + 하티 앤 세이보리 + 위드 치지 라면 누들스.',
        fullKo: '짭조름한 햄과 소시지, 치즈가 사르르 녹아든 얼큰한 국물과 꼬들꼬들한 라면이 예술이에요!'
      }
    ]
  },
  // ==========================================
  // EP.13. 🍗 Ginseng Chicken Soup
  // ==========================================
  {
    id: 'samgyetang',
    epNumber: 'EP.13',
    emoji: '🍗',
    shortTitle: '🍗 Ginseng Chicken Soup',
    title: 'How to Make Traditional Korean Ginseng Chicken Soup',
    ytTitle: 'How to Make Authentic Samgyetang in Easy English 🍗 | SoundBlock K-Cooking EP.13',
    thumbnailText: 'Nourishing Samgyetang! [I\'m gonna] + [simmer tender chicken with whole ginseng]',
    thumbnailImage: '/images/kfood/ep13-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make nourishing Korean Ginseng Chicken Soup, tender whole chicken stuffed with sweet rice and ginseng, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for healthy Samgyetang! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Clean Young Chicken',
        visualEmojis: '🍗 💧 🧼',
        imagePath: '/images/kfood/ep13-thumb.jpg',
        actionNote: '닭 내부와 꽁지 기름기를 깨끗하게 손질하기',
        coachKo: "코어 블록은 'clean the young chicken'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'clean the young chicken'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 영계 닭의 뱃속 핏물과 꽁지 기름을 깨끗하게 씻어 손질합니다.",
        missionEn: "Snap Mission! 'I\'m gonna clean the young chicken thoroughly inside and out.' Snap!",
        keyVocab: 'clean the young chicken',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'clean the young chicken', pron: '클린 더 영 치킨' },
          { role: 'db', en: 'thoroughly inside and out.', pron: '써럴리 인사이드 앤 아웃' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna clean the young chicken.', fullPron: '암거너 클린 더 영 치킨', ko: 'clean the young chicken 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to clean the young chicken.', fullPron: '유 해브 투 클린 더 영 치킨', ko: 'clean the young chicken 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you clean the young chicken?', fullPron: '캔 유 클린 더 영 치킨?', ko: 'clean the young chicken 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['clean the young chicken', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna clean the young chicken thoroughly inside and out.",
        fullPron: '암거너 + 클린 더 영 치킨 + 써럴리 인사이드 앤 아웃.',
        fullKo: '영계 닭의 뱃속 핏물과 꽁지 기름을 깨끗하게 씻어 손질합니다.'
      },
      {
        stepTitle: 'SCENE 2 · Stuff with Sweet Rice & Garlic',
        visualEmojis: '🍚 🧄 🥢',
        imagePath: '/images/kfood/ep13-thumb.jpg',
        actionNote: '물에 불린 찹쌀과 통마늘을 뱃속에 꾹꾹 채우기',
        coachKo: "코어 블록은 'stuff with sweet rice'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stuff with sweet rice'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 물에 불린 찹쌀과 달콤한 통마늘을 닭 뱃속에 알차게 채워 넣습니다.",
        missionEn: "Snap Mission! 'You have to stuff with sweet rice and garlic cloves.' Snap!",
        keyVocab: 'stuff with sweet rice',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'stuff with sweet rice', pron: '스터프 위드 스위트 라이스' },
          { role: 'db', en: 'and garlic cloves.', pron: '앤 갈릭 클로브스' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna stuff with sweet rice.', fullPron: '암거너 스터프 위드 스위트 라이스', ko: 'stuff with sweet rice 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to stuff with sweet rice.', fullPron: '유 해브 투 스터프 위드 스위트 라이스', ko: 'stuff with sweet rice 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you stuff with sweet rice?', fullPron: '캔 유 스터프 위드 스위트 라이스?', ko: 'stuff with sweet rice 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['stuff with sweet rice', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to stuff with sweet rice and garlic cloves.",
        fullPron: '유 해브 투 + 스터프 위드 스위트 라이스 + 앤 갈릭 클로브스.',
        fullKo: '물에 불린 찹쌀과 달콤한 통마늘을 닭 뱃속에 알차게 채워 넣습니다.'
      },
      {
        stepTitle: 'SCENE 3 · Insert Ginseng & Jujubes',
        visualEmojis: '🌿 🌰 ✨',
        imagePath: '/images/kfood/ep13-thumb.jpg',
        actionNote: '수삼 한 뿌리와 달콤한 대추 뱃속에 쏙 넣기',
        coachKo: "코어 블록은 'insert fresh ginseng root'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'insert fresh ginseng root'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 원기 회복을 돕는 싱싱한 수삼과 대추를 뱃속에 쏙 넣어 줍니다.",
        missionEn: "Snap Mission! 'We\'re gonna insert fresh ginseng root and sweet red dates.' Snap!",
        keyVocab: 'insert fresh ginseng root',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'insert fresh ginseng root', pron: '인서트 프레시 진생 루트' },
          { role: 'db', en: 'and sweet red dates.', pron: '앤 스위트 레드 데이츠' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna insert fresh ginseng root.', fullPron: '웨어 거너 인서트 프레시 진생 루트', ko: 'insert fresh ginseng root 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to insert fresh ginseng root.', fullPron: '유 해브 투 인서트 프레시 진생 루트', ko: 'insert fresh ginseng root 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you insert fresh ginseng root?', fullPron: '캔 유 인서트 프레시 진생 루트?', ko: 'insert fresh ginseng root 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['insert fresh ginseng root', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna insert fresh ginseng root and sweet red dates.",
        fullPron: '웨어 거너 + 인서트 프레시 진생 루트 + 앤 스위트 레드 데이츠.',
        fullKo: '원기 회복을 돕는 싱싱한 수삼과 대추를 뱃속에 쏙 넣어 줍니다.'
      },
      {
        stepTitle: 'SCENE 4 · Cross Chicken Legs',
        visualEmojis: '🍗 🪢 🥢',
        imagePath: '/images/kfood/ep13-thumb.jpg',
        actionNote: '속 재료가 빠지지 않게 다리를 단단히 교차하기',
        coachKo: "코어 블록은 'cross the chicken legs'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'cross the chicken legs'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 껍질에 칼집을 내어 다리를 꼬아 속 재료가 빠져나오지 않게 고정합니다.",
        missionEn: "Snap Mission! 'I\'ll cross the chicken legs to keep the stuffing inside.' Snap!",
        keyVocab: 'cross the chicken legs',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'cross the chicken legs', pron: '크로스 더 치킨 렉스' },
          { role: 'db', en: 'to keep the stuffing inside.', pron: '투 킵 더 스터핑 인사이드' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll cross the chicken legs.', fullPron: '아일 크로스 더 치킨 렉스', ko: 'cross the chicken legs 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to cross the chicken legs.', fullPron: '유 해브 투 크로스 더 치킨 렉스', ko: 'cross the chicken legs 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you cross the chicken legs?', fullPron: '캔 유 크로스 더 치킨 렉스?', ko: 'cross the chicken legs 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['cross the chicken legs', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll cross the chicken legs to keep the stuffing inside.",
        fullPron: '아일 + 크로스 더 치킨 렉스 + 투 킵 더 스터핑 인사이드.',
        fullKo: '껍질에 칼집을 내어 다리를 꼬아 속 재료가 빠져나오지 않게 고정합니다.'
      },
      {
        stepTitle: 'SCENE 5 · Place in Heavy Stockpot',
        visualEmojis: '🏺 🍲 💧',
        imagePath: '/images/kfood/ep13-thumb.jpg',
        actionNote: '깊은 냄비에 영계를 얌전하게 담기',
        coachKo: "코어 블록은 'place the stuffed chicken'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'place the stuffed chicken'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 속을 채운 닭을 두꺼운 곰솥 냄비에 반듯하게 담아 줍니다.",
        missionEn: "Snap Mission! 'You can place the stuffed chicken in a heavy stockpot.' Snap!",
        keyVocab: 'place the stuffed chicken',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'place the stuffed chicken', pron: '플레이스 더 스터프트 치킨' },
          { role: 'db', en: 'in a heavy stockpot.', pron: '인 어 헤비 스탁팟' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can place the stuffed chicken.', fullPron: '유 캔 플레이스 더 스터프트 치킨', ko: 'place the stuffed chicken 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to place the stuffed chicken.', fullPron: '유 해브 투 플레이스 더 스터프트 치킨', ko: 'place the stuffed chicken 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you place the stuffed chicken?', fullPron: '캔 유 플레이스 더 스터프트 치킨?', ko: 'place the stuffed chicken 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['place the stuffed chicken', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can place the stuffed chicken in a heavy stockpot.",
        fullPron: '유 캔 + 플레이스 더 스터프트 치킨 + 인 어 헤비 스탁팟.',
        fullKo: '속을 채운 닭을 두꺼운 곰솥 냄비에 반듯하게 담아 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Pour Water to Cover',
        visualEmojis: '💧 🌊 🔥',
        imagePath: '/images/kfood/ep13-thumb.jpg',
        actionNote: '닭이 완전히 잠길 때까지 맑은 물 넉넉히 붓기',
        coachKo: "코어 블록은 'pour fresh water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour fresh water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 닭이 푹 잠길 만큼 맑은 물을 넉넉하게 부어 센 불로 끓입니다.",
        missionEn: "Snap Mission! 'We have to pour fresh water until the chicken is submerged.' Snap!",
        keyVocab: 'pour fresh water',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'pour fresh water', pron: '푸어 프레시 워터' },
          { role: 'db', en: 'until the chicken is submerged.', pron: '언틸 더 치킨 이즈 서브머지드' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to pour fresh water.', fullPron: '위 해브 투 푸어 프레시 워터', ko: 'pour fresh water 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour fresh water.', fullPron: '유 해브 투 푸어 프레시 워터', ko: 'pour fresh water 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you pour fresh water?', fullPron: '캔 유 푸어 프레시 워터?', ko: 'pour fresh water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['pour fresh water', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to pour fresh water until the chicken is submerged.",
        fullPron: '위 해브 투 + 푸어 프레시 워터 + 언틸 더 치킨 이즈 서브머지드.',
        fullKo: '닭이 푹 잠길 만큼 맑은 물을 넉넉하게 부어 센 불로 끓입니다.'
      },
      {
        stepTitle: 'SCENE 7 · Simmer for One Hour',
        visualEmojis: '⏱️ 🔥 💨',
        imagePath: '/images/kfood/ep13-thumb.jpg',
        actionNote: '중약불에서 1시간 동안 푹 고아 뼈와 살 분리하기',
        coachKo: "코어 블록은 'simmer for one hour'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'simmer for one hour'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 살이 부드럽게 찢어지고 뽀얀 육수가 우러나오도록 1시간 동안 푹 끓여 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna simmer for one hour until the meat is tender.' Snap!",
        keyVocab: 'simmer for one hour',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'simmer for one hour', pron: '시머 포 원 아워' },
          { role: 'db', en: 'until the meat is tender.', pron: '언틸 더 미트 이즈 텐더' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna simmer for one hour.', fullPron: '암거너 시머 포 원 아워', ko: 'simmer for one hour 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to simmer for one hour.', fullPron: '유 해브 투 시머 포 원 아워', ko: 'simmer for one hour 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you simmer for one hour?', fullPron: '캔 유 시머 포 원 아워?', ko: 'simmer for one hour 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['simmer for one hour', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna simmer for one hour until the meat is tender.",
        fullPron: '암거너 + 시머 포 원 아워 + 언틸 더 미트 이즈 텐더.',
        fullKo: '살이 부드럽게 찢어지고 뽀얀 육수가 우러나오도록 1시간 동안 푹 끓여 줍니다.'
      },
      {
        stepTitle: 'SCENE 8 · Nourishing & Fall-Apart Tender',
        visualEmojis: '😋 🍗 🌟',
        imagePath: '/images/kfood/ep13-thumb.jpg',
        actionNote: '감탄 반응: 부드럽게 녹아내리는 육질과 보약 같은 진한 국물!',
        coachKo: "코어 블록은 'tender and nourishing'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'tender and nourishing'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 부드러운 닭고기와 인삼 향이 가득 밴 진국 국물이 몸과 마음을 채워 줘요!",
        missionEn: "Snap Mission! 'It\'s so tender and nourishing with fragrant herbal broth!' Snap!",
        keyVocab: 'tender and nourishing',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'tender and nourishing', pron: '텐더 앤 너리싱' },
          { role: 'db', en: 'with fragrant herbal broth!', pron: '위드 프레이그런트 허벌 브로쓰' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so tender and nourishing.', fullPron: '잇츠 쏘 텐더 앤 너리싱', ko: 'tender and nourishing 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to tender and nourishing.', fullPron: '유 해브 투 텐더 앤 너리싱', ko: 'tender and nourishing 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you tender and nourishing?', fullPron: '캔 유 텐더 앤 너리싱?', ko: 'tender and nourishing 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['tender and nourishing', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so tender and nourishing with fragrant herbal broth!",
        fullPron: '잇츠 쏘 + 텐더 앤 너리싱 + 위드 프레이그런트 허벌 브로쓰.',
        fullKo: '부드러운 닭고기와 인삼 향이 가득 밴 진국 국물이 몸과 마음을 채워 줘요!'
      }
    ]
  },
  // ==========================================
  // EP.14. 🥣 Beef Seaweed Soup
  // ==========================================
  {
    id: 'miyeok-guk',
    epNumber: 'EP.14',
    emoji: '🥣',
    shortTitle: '🥣 Beef Seaweed Soup',
    title: 'How to Make Korean Beef Seaweed Birthday Soup',
    ytTitle: 'How to Make Korean Beef Seaweed Soup in Easy English 🥣 | SoundBlock K-Cooking EP.14',
    thumbnailText: 'Traditional Miyeok-guk! [We\'re gonna] + [stir-fry soaked seaweed with savory beef]',
    thumbnailImage: '/images/kfood/ep14-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make traditional Korean Beef Seaweed Soup, nourishing Miyeok-guk packed with tender beef and toasted sesame oil, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for comforting Beef Seaweed Soup! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Soak Dried Seaweed',
        visualEmojis: '🌿 💧 ⏰',
        imagePath: '/images/kfood/ep14-thumb.jpg',
        actionNote: '마른 미역을 찬물에 10분간 불려 부드럽게 만들기',
        coachKo: "코어 블록은 'soak the dried seaweed'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'soak the dried seaweed'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 마른 미역을 찬물에 10분 정도 담가 부드럽게 불려 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna soak the dried seaweed in cold water for ten minutes.' Snap!",
        keyVocab: 'soak the dried seaweed',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'soak the dried seaweed', pron: '소옥 더 드라이드 시위드' },
          { role: 'db', en: 'in cold water for ten minutes.', pron: '인 콜드 워터 포 텐 미닛츠' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna soak the dried seaweed.', fullPron: '암거너 소옥 더 드라이드 시위드', ko: 'soak the dried seaweed 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to soak the dried seaweed.', fullPron: '유 해브 투 소옥 더 드라이드 시위드', ko: 'soak the dried seaweed 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you soak the dried seaweed?', fullPron: '캔 유 소옥 더 드라이드 시위드?', ko: 'soak the dried seaweed 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['soak the dried seaweed', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna soak the dried seaweed in cold water for ten minutes.",
        fullPron: '암거너 + 소옥 더 드라이드 시위드 + 인 콜드 워터 포 텐 미닛츠.',
        fullKo: '마른 미역을 찬물에 10분 정도 담가 부드럽게 불려 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Squeeze & Cut Seaweed',
        visualEmojis: '🤲 🔪 🥣',
        imagePath: '/images/kfood/ep14-thumb.jpg',
        actionNote: '물기를 꼭 짠 후 먹기 좋은 한 입 크기로 썰기',
        coachKo: "코어 블록은 'squeeze out the water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'squeeze out the water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 불린 미역의 물기를 두 손으로 꼭 짠 뒤 한 입 크기로 송송 썰어 줍니다.",
        missionEn: "Snap Mission! 'You have to squeeze out the water and cut into pieces.' Snap!",
        keyVocab: 'squeeze out the water',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'squeeze out the water', pron: '스퀴즈 아웃 더 워터' },
          { role: 'db', en: 'and cut into pieces.', pron: '앤 컷 인투 피시스' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to squeeze out the water.', fullPron: '유 해브 투 스퀴즈 아웃 더 워터', ko: 'squeeze out the water 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to squeeze out the water.', fullPron: '유 해브 투 스퀴즈 아웃 더 워터', ko: 'squeeze out the water 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you squeeze out the water?', fullPron: '캔 유 스퀴즈 아웃 더 워터?', ko: 'squeeze out the water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['squeeze out the water', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to squeeze out the water and cut into pieces.",
        fullPron: '유 해브 투 + 스퀴즈 아웃 더 워터 + 앤 컷 인투 피시스.',
        fullKo: '불린 미역의 물기를 두 손으로 꼭 짠 뒤 한 입 크기로 송송 썰어 줍니다.'
      },
      {
        stepTitle: 'SCENE 3 · Heat Sesame Oil in Pot',
        visualEmojis: '🫒 냄비 🔥',
        imagePath: '/images/kfood/ep14-thumb.jpg',
        actionNote: '깊은 냄비에 고소한 참기름을 두르고 달구기',
        coachKo: "코어 블록은 'heat fragrant sesame oil'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'heat fragrant sesame oil'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 냄비 바닥에 고소한 참기름을 넉넉히 두르고 은은하게 달굽니다.",
        missionEn: "Snap Mission! 'We\'re gonna heat fragrant sesame oil in a deep pot.' Snap!",
        keyVocab: 'heat fragrant sesame oil',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'heat fragrant sesame oil', pron: '히트 프레이그런트 세서미 오일' },
          { role: 'db', en: 'in a deep pot.', pron: '인 어 딥 팟' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna heat fragrant sesame oil.', fullPron: '웨어 거너 히트 프레이그런트 세서미 오일', ko: 'heat fragrant sesame oil 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to heat fragrant sesame oil.', fullPron: '유 해브 투 히트 프레이그런트 세서미 오일', ko: 'heat fragrant sesame oil 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you heat fragrant sesame oil?', fullPron: '캔 유 히트 프레이그런트 세서미 오일?', ko: 'heat fragrant sesame oil 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['heat fragrant sesame oil', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna heat fragrant sesame oil in a deep pot.",
        fullPron: '웨어 거너 + 히트 프레이그런트 세서미 오일 + 인 어 딥 팟.',
        fullKo: '냄비 바닥에 고소한 참기름을 넉넉히 두르고 은은하게 달굽니다.'
      },
      {
        stepTitle: 'SCENE 4 · Stir-Fry Beef Brisket',
        visualEmojis: '🥩 🔥 🥢',
        imagePath: '/images/kfood/ep14-thumb.jpg',
        actionNote: '참기름에 소고기 양지를 달달 볶아 육향 끌어올리기',
        coachKo: "코어 블록은 'stir-fry the beef brisket'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir-fry the beef brisket'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 소고기 양지머리를 넣고 겉면이 하얗게 익을 때까지 달달 볶아 줍니다.",
        missionEn: "Snap Mission! 'I\'ll stir-fry the beef brisket until lightly browned.' Snap!",
        keyVocab: 'stir-fry the beef brisket',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'stir-fry the beef brisket', pron: '스터-프라이 더 비프 브리스킷' },
          { role: 'db', en: 'until lightly browned.', pron: '언틸 라이틀리 브라운드' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll stir-fry the beef brisket.', fullPron: '아일 스터-프라이 더 비프 브리스킷', ko: 'stir-fry the beef brisket 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to stir-fry the beef brisket.', fullPron: '유 해브 투 스터-프라이 더 비프 브리스킷', ko: 'stir-fry the beef brisket 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you stir-fry the beef brisket?', fullPron: '캔 유 스터-프라이 더 비프 브리스킷?', ko: 'stir-fry the beef brisket 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['stir-fry the beef brisket', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll stir-fry the beef brisket until lightly browned.",
        fullPron: '아일 + 스터-프라이 더 비프 브리스킷 + 언틸 라이틀리 브라운드.',
        fullKo: '소고기 양지머리를 넣고 겉면이 하얗게 익을 때까지 달달 볶아 줍니다.'
      },
      {
        stepTitle: 'SCENE 5 · Toss in Soaked Seaweed',
        visualEmojis: '🌿 🥢 🍲',
        imagePath: '/images/kfood/ep14-thumb.jpg',
        actionNote: '불린 미역을 넣고 고기와 함께 2분간 볶기',
        coachKo: "코어 블록은 'toss in the seaweed'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toss in the seaweed'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 미역에 고소한 참기름과 소고기 기름이 배도록 2분간 함께 볶습니다.",
        missionEn: "Snap Mission! 'You can toss in the seaweed and sauté for two minutes.' Snap!",
        keyVocab: 'toss in the seaweed',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'toss in the seaweed', pron: '토스 인 더 시위드' },
          { role: 'db', en: 'and sauté for two minutes.', pron: '앤 소테이 포 투 미닛츠' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can toss in the seaweed.', fullPron: '유 캔 토스 인 더 시위드', ko: 'toss in the seaweed 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to toss in the seaweed.', fullPron: '유 해브 투 토스 인 더 시위드', ko: 'toss in the seaweed 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you toss in the seaweed?', fullPron: '캔 유 토스 인 더 시위드?', ko: 'toss in the seaweed 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['toss in the seaweed', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can toss in the seaweed and sauté for two minutes.",
        fullPron: '유 캔 + 토스 인 더 시위드 + 앤 소테이 포 투 미닛츠.',
        fullKo: '미역에 고소한 참기름과 소고기 기름이 배도록 2분간 함께 볶습니다.'
      },
      {
        stepTitle: 'SCENE 6 · Pour Water & Boil Rolling',
        visualEmojis: '💧 🌊 🔥',
        imagePath: '/images/kfood/ep14-thumb.jpg',
        actionNote: '맑은 물을 붓고 센 불에서 바글바글 끓이기',
        coachKo: "코어 블록은 'pour in fresh water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour in fresh water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 물을 넉넉히 붓고 센 불에서 뽀얀 국물이 우러나도록 팔팔 끓여 줍니다.",
        missionEn: "Snap Mission! 'We have to pour in fresh water and bring it to a boil.' Snap!",
        keyVocab: 'pour in fresh water',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'pour in fresh water', pron: '푸어 인 프레시 워터' },
          { role: 'db', en: 'and bring it to a boil.', pron: '앤 브링 잇 투 어 보일' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to pour in fresh water.', fullPron: '위 해브 투 푸어 인 프레시 워터', ko: 'pour in fresh water 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour in fresh water.', fullPron: '유 해브 투 푸어 인 프레시 워터', ko: 'pour in fresh water 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you pour in fresh water?', fullPron: '캔 유 푸어 인 프레시 워터?', ko: 'pour in fresh water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['pour in fresh water', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to pour in fresh water and bring it to a boil.",
        fullPron: '위 해브 투 + 푸어 인 프레시 워터 + 앤 브링 잇 투 어 보일.',
        fullKo: '물을 넉넉히 붓고 센 불에서 뽀얀 국물이 우러나도록 팔팔 끓여 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Season with Soup Soy Sauce',
        visualEmojis: '🍶 🧄 🧂',
        imagePath: '/images/kfood/ep14-thumb.jpg',
        actionNote: '국간장과 다진 마늘로 깊고 개운한 간 맞추기',
        coachKo: "코어 블록은 'season with soup soy sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'season with soup soy sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 조선간장(국간장)과 다진 마늘로 깊고 담백하게 간을 맞춥니다.",
        missionEn: "Snap Mission! 'I\'m gonna season with soup soy sauce and minced garlic.' Snap!",
        keyVocab: 'season with soup soy sauce',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'season with soup soy sauce', pron: '시즌 위드 숲 소이 소스' },
          { role: 'db', en: 'and minced garlic.', pron: '앤 민스트 갈릭' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna season with soup soy sauce.', fullPron: '암거너 시즌 위드 숲 소이 소스', ko: 'season with soup soy sauce 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to season with soup soy sauce.', fullPron: '유 해브 투 시즌 위드 숲 소이 소스', ko: 'season with soup soy sauce 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you season with soup soy sauce?', fullPron: '캔 유 시즌 위드 숲 소이 소스?', ko: 'season with soup soy sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['season with soup soy sauce', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna season with soup soy sauce and minced garlic.",
        fullPron: '암거너 + 시즌 위드 숲 소이 소스 + 앤 민스트 갈릭.',
        fullKo: '조선간장(국간장)과 다진 마늘로 깊고 담백하게 간을 맞춥니다.'
      },
      {
        stepTitle: 'SCENE 8 · Smooth & Savory Birthday Soup',
        visualEmojis: '😋 🥣 ✨',
        imagePath: '/images/kfood/ep14-thumb.jpg',
        actionNote: '감탄 반응: 부드럽게 넘어가는 미역과 깊은 소고기 육수의 진한 맛!',
        coachKo: "코어 블록은 'smooth and savory'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'smooth and savory'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 미역이 부드럽게 호로록 넘어가고 진하고 고소한 국물이 감동적이에요!",
        missionEn: "Snap Mission! 'It\'s so smooth and savory with rich beef and seaweed!' Snap!",
        keyVocab: 'smooth and savory',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'smooth and savory', pron: '스무드 앤 세이보리' },
          { role: 'db', en: 'with rich beef and seaweed!', pron: '위드 리치 비프 앤 시위드' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so smooth and savory.', fullPron: '잇츠 쏘 스무드 앤 세이보리', ko: 'smooth and savory 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to smooth and savory.', fullPron: '유 해브 투 스무드 앤 세이보리', ko: 'smooth and savory 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you smooth and savory?', fullPron: '캔 유 스무드 앤 세이보리?', ko: 'smooth and savory 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['smooth and savory', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so smooth and savory with rich beef and seaweed!",
        fullPron: '잇츠 쏘 + 스무드 앤 세이보리 + 위드 리치 비프 앤 시위드.',
        fullKo: '미역이 부드럽게 호로록 넘어가고 진하고 고소한 국물이 감동적이에요!'
      }
    ]
  },
  // ==========================================
  // EP.15. 🥩 Spicy Pork Stir-Fry
  // ==========================================
  {
    id: 'jeyuk-bokkeum',
    epNumber: 'EP.15',
    emoji: '🥩',
    shortTitle: '🥩 Spicy Pork Stir-Fry',
    title: 'How to Make Fiery Korean Spicy Pork Stir-Fry',
    ytTitle: 'How to Make Spicy Korean Pork Stir-Fry in Easy English 🥩 | SoundBlock K-Cooking EP.15',
    thumbnailText: 'Fiery Jeyuk Bokkeum! [I\'m gonna] + [stir-fry marinated pork over high heat]',
    thumbnailImage: '/images/kfood/ep15-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make spicy Korean Pork Stir-Fry, fiery Jeyuk Bokkeum with sweet onions and smoky glaze, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for sizzling Jeyuk Bokkeum! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Slice Pork Shoulder Strips',
        visualEmojis: '🥩 🔪 🥣',
        imagePath: '/images/kfood/ep15-thumb.jpg',
        actionNote: '돼지 앞다리살을 얇고 넓적하게 썰기',
        coachKo: "코어 블록은 'slice the pork shoulder'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice the pork shoulder'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양념이 쏙쏙 배도록 돼지 앞다리살을 얇은 한 입 크기로 썰어 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna slice the pork shoulder into bite-sized strips.' Snap!",
        keyVocab: 'slice the pork shoulder',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'slice the pork shoulder', pron: '슬라이스 더 포크 숄더' },
          { role: 'db', en: 'into bite-sized strips.', pron: '인투 바이트-사이즈드 스트립스' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice the pork shoulder.', fullPron: '암거너 슬라이스 더 포크 숄더', ko: 'slice the pork shoulder 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice the pork shoulder.', fullPron: '유 해브 투 슬라이스 더 포크 숄더', ko: 'slice the pork shoulder 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you slice the pork shoulder?', fullPron: '캔 유 슬라이스 더 포크 숄더?', ko: 'slice the pork shoulder 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['slice the pork shoulder', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna slice the pork shoulder into bite-sized strips.",
        fullPron: '암거너 + 슬라이스 더 포크 숄더 + 인투 바이트-사이즈드 스트립스.',
        fullKo: '양념이 쏙쏙 배도록 돼지 앞다리살을 얇은 한 입 크기로 썰어 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Mix Fiery Gochujang Marinade',
        visualEmojis: '🌶️ 🧄 🍯',
        imagePath: '/images/kfood/ep15-thumb.jpg',
        actionNote: '고추장, 고춧가루, 간장, 올리고당, 마늘 섞기',
        coachKo: "코어 블록은 'mix red chili paste'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix red chili paste'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고추장과 고춧가루, 간장, 설탕, 마늘을 넣고 감칠맛 나는 양념장을 만듭니다.",
        missionEn: "Snap Mission! 'You have to mix red chili paste with soy sauce and sugar.' Snap!",
        keyVocab: 'mix red chili paste',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'mix red chili paste', pron: '믹스 레드 칠리 페이스트' },
          { role: 'db', en: 'with soy sauce and sugar.', pron: '위드 소이 소스 앤 슈가' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to mix red chili paste.', fullPron: '유 해브 투 믹스 레드 칠리 페이스트', ko: 'mix red chili paste 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix red chili paste.', fullPron: '유 해브 투 믹스 레드 칠리 페이스트', ko: 'mix red chili paste 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you mix red chili paste?', fullPron: '캔 유 믹스 레드 칠리 페이스트?', ko: 'mix red chili paste 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['mix red chili paste', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to mix red chili paste with soy sauce and sugar.",
        fullPron: '유 해브 투 + 믹스 레드 칠리 페이스트 + 위드 소이 소스 앤 슈가.',
        fullKo: '고추장과 고춧가루, 간장, 설탕, 마늘을 넣고 감칠맛 나는 양념장을 만듭니다.'
      },
      {
        stepTitle: 'SCENE 3 · Marinate Pork Slices',
        visualEmojis: '🥩 ⏰ 🥣',
        imagePath: '/images/kfood/ep15-thumb.jpg',
        actionNote: '고기에 양념을 조물조물 버무려 30분간 재우기',
        coachKo: "코어 블록은 'marinate the pork'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'marinate the pork'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양념이 고기 속까지 푹 배어들도록 30분간 조물조물 재워 둡니다.",
        missionEn: "Snap Mission! 'We\'re gonna marinate the pork for thirty minutes.' Snap!",
        keyVocab: 'marinate the pork',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'marinate the pork', pron: '매러네이트 더 포크' },
          { role: 'db', en: 'for thirty minutes.', pron: '포 써티 미닛츠' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna marinate the pork.', fullPron: '웨어 거너 매러네이트 더 포크', ko: 'marinate the pork 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to marinate the pork.', fullPron: '유 해브 투 매러네이트 더 포크', ko: 'marinate the pork 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you marinate the pork?', fullPron: '캔 유 매러네이트 더 포크?', ko: 'marinate the pork 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['marinate the pork', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna marinate the pork for thirty minutes.",
        fullPron: '웨어 거너 + 매러네이트 더 포크 + 포 써티 미닛츠.',
        fullKo: '양념이 고기 속까지 푹 배어들도록 30분간 조물조물 재워 둡니다.'
      },
      {
        stepTitle: 'SCENE 4 · Heat Pan over High Heat',
        visualEmojis: '🍳 🔥 💨',
        imagePath: '/images/kfood/ep15-thumb.jpg',
        actionNote: '팬을 연기가 살짝 날 만큼 강한 불로 달구기',
        coachKo: "코어 블록은 'heat the skillet'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'heat the skillet'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 불맛을 내기 위해 프라이팬을 강한 불에서 뜨겁게 달궈 줍니다.",
        missionEn: "Snap Mission! 'I\'ll heat the skillet over medium-high heat.' Snap!",
        keyVocab: 'heat the skillet',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'heat the skillet', pron: '히트 더 스킬렛' },
          { role: 'db', en: 'over medium-high heat.', pron: '오버 미디엄-하이 히트' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll heat the skillet.', fullPron: '아일 히트 더 스킬렛', ko: 'heat the skillet 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to heat the skillet.', fullPron: '유 해브 투 히트 더 스킬렛', ko: 'heat the skillet 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you heat the skillet?', fullPron: '캔 유 히트 더 스킬렛?', ko: 'heat the skillet 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['heat the skillet', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll heat the skillet over medium-high heat.",
        fullPron: '아일 + 히트 더 스킬렛 + 오버 미디엄-하이 히트.',
        fullKo: '불맛을 내기 위해 프라이팬을 강한 불에서 뜨겁게 달궈 줍니다.'
      },
      {
        stepTitle: 'SCENE 5 · Stir-Fry Pork with Smoky Glaze',
        visualEmojis: '🥩 🔥 🌪️',
        imagePath: '/images/kfood/ep15-thumb.jpg',
        actionNote: '센 불에서 고기를 빠르게 볶아 불향 입히기',
        coachKo: "코어 블록은 'stir-fry the pork'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir-fry the pork'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고기가 노릇노릇 캐러멜라이징되며 불향이 날 때까지 센 불로 볶아 줍니다.",
        missionEn: "Snap Mission! 'You can stir-fry the pork until caramelized and smoky.' Snap!",
        keyVocab: 'stir-fry the pork',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'stir-fry the pork', pron: '스터-프라이 더 포크' },
          { role: 'db', en: 'until caramelized and smoky.', pron: '언틸 캐러멜라이즈드 앤 스모키' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can stir-fry the pork.', fullPron: '유 캔 스터-프라이 더 포크', ko: 'stir-fry the pork 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to stir-fry the pork.', fullPron: '유 해브 투 스터-프라이 더 포크', ko: 'stir-fry the pork 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you stir-fry the pork?', fullPron: '캔 유 스터-프라이 더 포크?', ko: 'stir-fry the pork 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['stir-fry the pork', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can stir-fry the pork until caramelized and smoky.",
        fullPron: '유 캔 + 스터-프라이 더 포크 + 언틸 캐러멜라이즈드 앤 스모키.',
        fullKo: '고기가 노릇노릇 캐러멜라이징되며 불향이 날 때까지 센 불로 볶아 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Add Sliced Sweet Onions',
        visualEmojis: '🧅 🌿 🥢',
        imagePath: '/images/kfood/ep15-thumb.jpg',
        actionNote: '달달한 양파 채와 대파 어슷썰어 넣기',
        coachKo: "코어 블록은 'add sliced onions'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add sliced onions'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 아삭한 단맛을 더해 줄 양파 채와 대파를 넣고 빠르게 볶습니다.",
        missionEn: "Snap Mission! 'We have to add sliced onions and scallions.' Snap!",
        keyVocab: 'add sliced onions',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'add sliced onions', pron: '애드 슬라이스트 어니언스' },
          { role: 'db', en: 'and scallions.', pron: '앤 스캘리언스' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to add sliced onions.', fullPron: '위 해브 투 애드 슬라이스트 어니언스', ko: 'add sliced onions 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to add sliced onions.', fullPron: '유 해브 투 애드 슬라이스트 어니언스', ko: 'add sliced onions 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you add sliced onions?', fullPron: '캔 유 애드 슬라이스트 어니언스?', ko: 'add sliced onions 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['add sliced onions', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to add sliced onions and scallions.",
        fullPron: '위 해브 투 + 애드 슬라이스트 어니언스 + 앤 스캘리언스.',
        fullKo: '아삭한 단맛을 더해 줄 양파 채와 대파를 넣고 빠르게 볶습니다.'
      },
      {
        stepTitle: 'SCENE 7 · Drizzle Sesame Oil & Seeds',
        visualEmojis: '🫒 ✨ 🌿',
        imagePath: '/images/kfood/ep15-thumb.jpg',
        actionNote: '참기름 한 바퀴 두르고 통깨 듬뿍 뿌리기',
        coachKo: "코어 블록은 'drizzle sesame oil'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'drizzle sesame oil'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 불을 끄기 직전 고소한 참기름을 두르고 통깨를 솔솔 뿌려 마무리합니다.",
        missionEn: "Snap Mission! 'I\'m gonna drizzle sesame oil and sprinkle sesame seeds.' Snap!",
        keyVocab: 'drizzle sesame oil',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'drizzle sesame oil', pron: '드리즐 세서미 오일' },
          { role: 'db', en: 'and sprinkle sesame seeds.', pron: '앤 스프링클 세서미 시즈' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna drizzle sesame oil.', fullPron: '암거너 드리즐 세서미 오일', ko: 'drizzle sesame oil 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to drizzle sesame oil.', fullPron: '유 해브 투 드리즐 세서미 오일', ko: 'drizzle sesame oil 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you drizzle sesame oil?', fullPron: '캔 유 드리즐 세서미 오일?', ko: 'drizzle sesame oil 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['drizzle sesame oil', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna drizzle sesame oil and sprinkle sesame seeds.",
        fullPron: '암거너 + 드리즐 세서미 오일 + 앤 스프링클 세서미 시즈.',
        fullKo: '불을 끄기 직전 고소한 참기름을 두르고 통깨를 솔솔 뿌려 마무리합니다.'
      },
      {
        stepTitle: 'SCENE 8 · Spicy & Smoky Ssam Wrap',
        visualEmojis: '😋 🥬 🥩',
        imagePath: '/images/kfood/ep15-thumb.jpg',
        actionNote: '감탄 반응: 싱싱한 상추에 싸 먹는 매콤 달콤 불맛의 끝판왕!',
        coachKo: "코어 블록은 'spicy and smoky'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'spicy and smoky'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 매콤달콤한 불향 고기를 아삭한 상추에 쌈 싸 먹으니 밥도둑이 따로 없어요!",
        missionEn: "Snap Mission! 'It\'s so spicy and smoky wrapped in crisp fresh lettuce!' Snap!",
        keyVocab: 'spicy and smoky',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'spicy and smoky', pron: '스파이시 앤 스모키' },
          { role: 'db', en: 'wrapped in crisp fresh lettuce!', pron: '랩트 인 크리스프 프레시 레터스' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so spicy and smoky.', fullPron: '잇츠 쏘 스파이시 앤 스모키', ko: 'spicy and smoky 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to spicy and smoky.', fullPron: '유 해브 투 스파이시 앤 스모키', ko: 'spicy and smoky 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you spicy and smoky?', fullPron: '캔 유 스파이시 앤 스모키?', ko: 'spicy and smoky 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['spicy and smoky', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so spicy and smoky wrapped in crisp fresh lettuce!",
        fullPron: '잇츠 쏘 + 스파이시 앤 스모키 + 랩트 인 크리스프 프레시 레터스.',
        fullKo: '매콤달콤한 불향 고기를 아삭한 상추에 쌈 싸 먹으니 밥도둑이 따로 없어요!'
      }
    ]
  },
  // ==========================================
  // EP.16. 🍖 Classic Beef Bulgogi
  // ==========================================
  {
    id: 'beef-bulgogi',
    epNumber: 'EP.16',
    emoji: '🍖',
    shortTitle: '🍖 Classic Beef Bulgogi',
    title: 'How to Stir-Fry Classic Korean Beef Bulgogi',
    ytTitle: 'How to Make Classic Beef Bulgogi in Easy English 🍖 | SoundBlock K-Cooking EP.16',
    thumbnailText: 'Classic Beef Bulgogi! [We have to] + [toss tender beef with sliced mushrooms]',
    thumbnailImage: '/images/kfood/ep16-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s stir-fry classic Korean Beef Bulgogi, tender ribeye with sweet soy glaze and colorful mushrooms, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for classic Beef Bulgogi! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Grate Sweet Korean Pear',
        visualEmojis: '🍐 🥣 🥢',
        imagePath: '/images/kfood/ep16-thumb.jpg',
        actionNote: '달콤한 배를 곱게 갈아 자연스러운 연육 작용 돕기',
        coachKo: "코어 블록은 'grate sweet Korean pear'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'grate sweet Korean pear'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 소고기를 입안에서 사르르 녹게 하기 위해 달콤한 배를 곱게 갈아 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna grate sweet Korean pear to tenderize the meat.' Snap!",
        keyVocab: 'grate sweet Korean pear',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'grate sweet Korean pear', pron: '그레이트 스위트 코리안 페어' },
          { role: 'db', en: 'to tenderize the meat.', pron: '투 텐더라이즈 더 미트' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna grate sweet Korean pear.', fullPron: '암거너 그레이트 스위트 코리안 페어', ko: 'grate sweet Korean pear 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to grate sweet Korean pear.', fullPron: '유 해브 투 그레이트 스위트 코리안 페어', ko: 'grate sweet Korean pear 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you grate sweet Korean pear?', fullPron: '캔 유 그레이트 스위트 코리안 페어?', ko: 'grate sweet Korean pear 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['grate sweet Korean pear', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna grate sweet Korean pear to tenderize the meat.",
        fullPron: '암거너 + 그레이트 스위트 코리안 페어 + 투 텐더라이즈 더 미트.',
        fullKo: '소고기를 입안에서 사르르 녹게 하기 위해 달콤한 배를 곱게 갈아 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Whisk Sweet Soy Sauce',
        visualEmojis: '🍶 🧄 🍯',
        imagePath: '/images/kfood/ep16-thumb.jpg',
        actionNote: '간장, 마늘, 흑설탕, 참기름으로 비법 간장 소스 만들기',
        coachKo: "코어 블록은 'whisk soy sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'whisk soy sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양조간장에 다진 마늘과 흑설탕, 참기름을 섞어 특제 불고기 양념을 만듭니다.",
        missionEn: "Snap Mission! 'You have to whisk soy sauce with garlic and brown sugar.' Snap!",
        keyVocab: 'whisk soy sauce',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'whisk soy sauce', pron: '위스크 소이 소스' },
          { role: 'db', en: 'with garlic and brown sugar.', pron: '위드 갈릭 앤 브라운 슈가' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to whisk soy sauce.', fullPron: '유 해브 투 위스크 소이 소스', ko: 'whisk soy sauce 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to whisk soy sauce.', fullPron: '유 해브 투 위스크 소이 소스', ko: 'whisk soy sauce 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you whisk soy sauce?', fullPron: '캔 유 위스크 소이 소스?', ko: 'whisk soy sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['whisk soy sauce', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to whisk soy sauce with garlic and brown sugar.",
        fullPron: '유 해브 투 + 위스크 소이 소스 + 위드 갈릭 앤 브라운 슈가.',
        fullKo: '양조간장에 다진 마늘과 흑설탕, 참기름을 섞어 특제 불고기 양념을 만듭니다.'
      },
      {
        stepTitle: 'SCENE 3 · Marinate Tender Ribeye',
        visualEmojis: '🥩 🤲 🥣',
        imagePath: '/images/kfood/ep16-thumb.jpg',
        actionNote: '얇게 썬 소고기를 한 장씩 떼어 양념에 재우기',
        coachKo: "코어 블록은 'marinate sliced ribeye'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'marinate sliced ribeye'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 얇은 소고기 등심을 손으로 살살 떼어가며 양념을 골고루 재워 둡니다.",
        missionEn: "Snap Mission! 'We\'re gonna marinate sliced ribeye gently with our hands.' Snap!",
        keyVocab: 'marinate sliced ribeye',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'marinate sliced ribeye', pron: '매러네이트 슬라이스트 립아이' },
          { role: 'db', en: 'gently with our hands.', pron: '젠틀리 위드 아워 핸즈' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna marinate sliced ribeye.', fullPron: '웨어 거너 매러네이트 슬라이스트 립아이', ko: 'marinate sliced ribeye 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to marinate sliced ribeye.', fullPron: '유 해브 투 매러네이트 슬라이스트 립아이', ko: 'marinate sliced ribeye 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you marinate sliced ribeye?', fullPron: '캔 유 매러네이트 슬라이스트 립아이?', ko: 'marinate sliced ribeye 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['marinate sliced ribeye', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna marinate sliced ribeye gently with our hands.",
        fullPron: '웨어 거너 + 매러네이트 슬라이스트 립아이 + 젠틀리 위드 아워 핸즈.',
        fullKo: '얇은 소고기 등심을 손으로 살살 떼어가며 양념을 골고루 재워 둡니다.'
      },
      {
        stepTitle: 'SCENE 4 · Slice Onions & Carrots',
        visualEmojis: '🧅 🥕 🔪',
        imagePath: '/images/kfood/ep16-thumb.jpg',
        actionNote: '양파와 당근을 가늘게 채 썰기',
        coachKo: "코어 블록은 'slice sweet onions'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice sweet onions'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 색감과 아삭한 식감을 살리기 위해 양파와 당근을 곱게 채 썰어 놓습니다.",
        missionEn: "Snap Mission! 'I\'ll slice sweet onions and crunchy carrots.' Snap!",
        keyVocab: 'slice sweet onions',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'slice sweet onions', pron: '슬라이스 스위트 어니언스' },
          { role: 'db', en: 'and crunchy carrots.', pron: '앤 크런치 캐럿츠' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll slice sweet onions.', fullPron: '아일 슬라이스 스위트 어니언스', ko: 'slice sweet onions 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice sweet onions.', fullPron: '유 해브 투 슬라이스 스위트 어니언스', ko: 'slice sweet onions 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you slice sweet onions?', fullPron: '캔 유 슬라이스 스위트 어니언스?', ko: 'slice sweet onions 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['slice sweet onions', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll slice sweet onions and crunchy carrots.",
        fullPron: '아일 + 슬라이스 스위트 어니언스 + 앤 크런치 캐럿츠.',
        fullKo: '색감과 아삭한 식감을 살리기 위해 양파와 당근을 곱게 채 썰어 놓습니다.'
      },
      {
        stepTitle: 'SCENE 5 · Heat Skillet over High Heat',
        visualEmojis: '🍳 🔥 ✨',
        imagePath: '/images/kfood/ep16-thumb.jpg',
        actionNote: '달군 팬에서 센 불로 고기를 볶을 준비하기',
        coachKo: "코어 블록은 'heat the skillet'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'heat the skillet'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 육즙이 빠져나가지 않도록 프라이팬을 센 불에서 뜨겁게 달궈 줍니다.",
        missionEn: "Snap Mission! 'You can heat the skillet over high heat.' Snap!",
        keyVocab: 'heat the skillet',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'heat the skillet', pron: '히트 더 스킬렛' },
          { role: 'db', en: 'over high heat.', pron: '오버 하이 히트' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can heat the skillet.', fullPron: '유 캔 히트 더 스킬렛', ko: 'heat the skillet 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to heat the skillet.', fullPron: '유 해브 투 히트 더 스킬렛', ko: 'heat the skillet 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you heat the skillet?', fullPron: '캔 유 히트 더 스킬렛?', ko: 'heat the skillet 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['heat the skillet', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can heat the skillet over high heat.",
        fullPron: '유 캔 + 히트 더 스킬렛 + 오버 하이 히트.',
        fullKo: '육즙이 빠져나가지 않도록 프라이팬을 센 불에서 뜨겁게 달궈 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Stir-Fry Beef Quickly',
        visualEmojis: '🥩 🥢 🔥',
        imagePath: '/images/kfood/ep16-thumb.jpg',
        actionNote: '센 불에서 빠르게 저어가며 볶기',
        coachKo: "코어 블록은 'stir-fry the beef quickly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir-fry the beef quickly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고기가 질겨지지 않도록 센 불에서 젓가락으로 빠르게 흔들며 볶아 줍니다.",
        missionEn: "Snap Mission! 'We have to stir-fry the beef quickly so it stays juicy.' Snap!",
        keyVocab: 'stir-fry the beef quickly',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'stir-fry the beef quickly', pron: '스터-프라이 더 비프 퀵클리' },
          { role: 'db', en: 'so it stays juicy.', pron: '쏘우 잇 스테이스 주시' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to stir-fry the beef quickly.', fullPron: '위 해브 투 스터-프라이 더 비프 퀵클리', ko: 'stir-fry the beef quickly 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to stir-fry the beef quickly.', fullPron: '유 해브 투 스터-프라이 더 비프 퀵클리', ko: 'stir-fry the beef quickly 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you stir-fry the beef quickly?', fullPron: '캔 유 스터-프라이 더 비프 퀵클리?', ko: 'stir-fry the beef quickly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['stir-fry the beef quickly', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to stir-fry the beef quickly so it stays juicy.",
        fullPron: '위 해브 투 + 스터-프라이 더 비프 퀵클리 + 쏘우 잇 스테이스 주시.',
        fullKo: '고기가 질겨지지 않도록 센 불에서 젓가락으로 빠르게 흔들며 볶아 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Add Enoki Mushrooms & Scallions',
        visualEmojis: '🍄 🌿 🥢',
        imagePath: '/images/kfood/ep16-thumb.jpg',
        actionNote: '팽이버섯과 대파를 넣고 살짝 숨 죽이기',
        coachKo: "코어 블록은 'add enoki mushrooms'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add enoki mushrooms'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 마지막에 쫄깃한 팽이버섯과 향긋한 대파를 넣고 가볍게 볶아 냅니다.",
        missionEn: "Snap Mission! 'I\'m gonna add enoki mushrooms and green onions at the end.' Snap!",
        keyVocab: 'add enoki mushrooms',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'add enoki mushrooms', pron: '애드 에노키 머쉬룸스' },
          { role: 'db', en: 'and green onions at the end.', pron: '앤 그린 어니언스 앳 디 엔드' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna add enoki mushrooms.', fullPron: '암거너 애드 에노키 머쉬룸스', ko: 'add enoki mushrooms 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to add enoki mushrooms.', fullPron: '유 해브 투 애드 에노키 머쉬룸스', ko: 'add enoki mushrooms 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you add enoki mushrooms?', fullPron: '캔 유 애드 에노키 머쉬룸스?', ko: 'add enoki mushrooms 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['add enoki mushrooms', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna add enoki mushrooms and green onions at the end.",
        fullPron: '암거너 + 애드 에노키 머쉬룸스 + 앤 그린 어니언스 앳 디 엔드.',
        fullKo: '마지막에 쫄깃한 팽이버섯과 향긋한 대파를 넣고 가볍게 볶아 냅니다.'
      },
      {
        stepTitle: 'SCENE 8 · Melt-in-Mouth Sweet Soy Bulgogi',
        visualEmojis: '😋 🍖 🍚',
        imagePath: '/images/kfood/ep16-thumb.jpg',
        actionNote: '감탄 반응: 달콤짭조름한 소스가 밥 위에 스며드는 환상의 맛!',
        coachKo: "코어 블록은 'tender and sweet'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'tender and sweet'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 야들야들한 소고기에 달콤짭조름한 양념이 배어 밥 한 공기 뚝딱이에요!",
        missionEn: "Snap Mission! 'It\'s so tender and sweet with rich caramelized soy glaze!' Snap!",
        keyVocab: 'tender and sweet',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'tender and sweet', pron: '텐더 앤 스위트' },
          { role: 'db', en: 'with rich caramelized soy glaze!', pron: '위드 리치 캐러멜라이즈드 소이 글레이즈' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so tender and sweet.', fullPron: '잇츠 쏘 텐더 앤 스위트', ko: 'tender and sweet 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to tender and sweet.', fullPron: '유 해브 투 텐더 앤 스위트', ko: 'tender and sweet 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you tender and sweet?', fullPron: '캔 유 텐더 앤 스위트?', ko: 'tender and sweet 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['tender and sweet', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so tender and sweet with rich caramelized soy glaze!",
        fullPron: '잇츠 쏘 + 텐더 앤 스위트 + 위드 리치 캐러멜라이즈드 소이 글레이즈.',
        fullKo: '야들야들한 소고기에 달콤짭조름한 양념이 배어 밥 한 공기 뚝딱이에요!'
      }
    ]
  },
  // ==========================================
  // EP.17. 🥬 Crispy Chive Pancake
  // ==========================================
  {
    id: 'buchujeon',
    epNumber: 'EP.17',
    emoji: '🥬',
    shortTitle: '🥬 Crispy Chive Pancake',
    title: 'How to Make Ultra-Crispy Korean Garlic Chive Pancake',
    ytTitle: 'How to Make Crispy Korean Chive Pancake in Easy English 🥬 | SoundBlock K-Cooking EP.17',
    thumbnailText: 'Ultra-Crispy Buchujeon! [You have to] + [flip the pancake until golden brown]',
    thumbnailImage: '/images/kfood/ep17-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make ultra-crispy Korean Garlic Chive Pancake, savory Buchujeon with green chili peppers, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for crispy Buchujeon! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Chop Fresh Garlic Chives',
        visualEmojis: '🥬 🔪 🧺',
        imagePath: '/images/kfood/ep17-thumb.jpg',
        actionNote: '싱싱한 부추를 5cm 손가락 길이로 썰기',
        coachKo: "코어 블록은 'chop fresh garlic chives'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'chop fresh garlic chives'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 파릇파릇한 영양 부추를 먹기 좋은 손가락 길이로 썰어 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna chop fresh garlic chives into finger-length pieces.' Snap!",
        keyVocab: 'chop fresh garlic chives',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'chop fresh garlic chives', pron: '찹 프레시 갈릭 차이브스' },
          { role: 'db', en: 'into finger-length pieces.', pron: '인투 핑거-렝스 피시스' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna chop fresh garlic chives.', fullPron: '암거너 찹 프레시 갈릭 차이브스', ko: 'chop fresh garlic chives 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to chop fresh garlic chives.', fullPron: '유 해브 투 찹 프레시 갈릭 차이브스', ko: 'chop fresh garlic chives 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you chop fresh garlic chives?', fullPron: '캔 유 찹 프레시 갈릭 차이브스?', ko: 'chop fresh garlic chives 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['chop fresh garlic chives', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna chop fresh garlic chives into finger-length pieces.",
        fullPron: '암거너 + 찹 프레시 갈릭 차이브스 + 인투 핑거-렝스 피시스.',
        fullKo: '파릇파릇한 영양 부추를 먹기 좋은 손가락 길이로 썰어 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Mix Light Pancake Batter',
        visualEmojis: '🥣 🧊 💧',
        imagePath: '/images/kfood/ep17-thumb.jpg',
        actionNote: '부침가루에 얼음물 또는 탄산수를 부어 가볍게 섞기',
        coachKo: "코어 블록은 'mix pancake mix'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix pancake mix'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 바삭한 식감을 위해 부침가루에 얼음물을 붓고 가볍게 훌훌 섞어 줍니다.",
        missionEn: "Snap Mission! 'You have to mix pancake mix with ice-cold water.' Snap!",
        keyVocab: 'mix pancake mix',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'mix pancake mix', pron: '믹스 팬케이크 믹스' },
          { role: 'db', en: 'with ice-cold water.', pron: '위드 아이스-콜드 워터' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to mix pancake mix.', fullPron: '유 해브 투 믹스 팬케이크 믹스', ko: 'mix pancake mix 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix pancake mix.', fullPron: '유 해브 투 믹스 팬케이크 믹스', ko: 'mix pancake mix 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you mix pancake mix?', fullPron: '캔 유 믹스 팬케이크 믹스?', ko: 'mix pancake mix 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['mix pancake mix', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to mix pancake mix with ice-cold water.",
        fullPron: '유 해브 투 + 믹스 팬케이크 믹스 + 위드 아이스-콜드 워터.',
        fullKo: '바삭한 식감을 위해 부침가루에 얼음물을 붓고 가볍게 훌훌 섞어 줍니다.'
      },
      {
        stepTitle: 'SCENE 3 · Coat Chives Lightly',
        visualEmojis: '🥬 🥣 ✨',
        imagePath: '/images/kfood/ep17-thumb.jpg',
        actionNote: '부추에 반죽 옷이 살짝만 묻도록 가볍게 버무리기',
        coachKo: "코어 블록은 'coat the chives lightly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'coat the chives lightly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 반죽이 두껍지 않고 부추의 식감이 살아나도록 최소한의 반죽만 입힙니다.",
        missionEn: "Snap Mission! 'We\'re gonna coat the chives lightly with minimal batter.' Snap!",
        keyVocab: 'coat the chives lightly',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'coat the chives lightly', pron: '코우트 더 차이브스 라이틀리' },
          { role: 'db', en: 'with minimal batter.', pron: '위드 미니멀 배터' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna coat the chives lightly.', fullPron: '웨어 거너 코우트 더 차이브스 라이틀리', ko: 'coat the chives lightly 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to coat the chives lightly.', fullPron: '유 해브 투 코우트 더 차이브스 라이틀리', ko: 'coat the chives lightly 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you coat the chives lightly?', fullPron: '캔 유 코우트 더 차이브스 라이틀리?', ko: 'coat the chives lightly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['coat the chives lightly', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna coat the chives lightly with minimal batter.",
        fullPron: '웨어 거너 + 코우트 더 차이브스 라이틀리 + 위드 미니멀 배터.',
        fullKo: '반죽이 두껍지 않고 부추의 식감이 살아나도록 최소한의 반죽만 입힙니다.'
      },
      {
        stepTitle: 'SCENE 4 · Heat Generous Oil in Pan',
        visualEmojis: '🍳 🫒 🔥',
        imagePath: '/images/kfood/ep17-thumb.jpg',
        actionNote: '팬에 기름을 넉넉히 두르고 뜨겁게 달구기',
        coachKo: "코어 블록은 'heat generous cooking oil'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'heat generous cooking oil'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 전의 가장자리가 튀겨지듯 바삭해지도록 식용유를 넉넉하게 둘러 달굽니다.",
        missionEn: "Snap Mission! 'I\'ll heat generous cooking oil in a wide frying pan.' Snap!",
        keyVocab: 'heat generous cooking oil',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'heat generous cooking oil', pron: '히트 제너러스 쿠킹 오일' },
          { role: 'db', en: 'in a wide frying pan.', pron: '인 어 와이드 프라잉 팬' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll heat generous cooking oil.', fullPron: '아일 히트 제너러스 쿠킹 오일', ko: 'heat generous cooking oil 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to heat generous cooking oil.', fullPron: '유 해브 투 히트 제너러스 쿠킹 오일', ko: 'heat generous cooking oil 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you heat generous cooking oil?', fullPron: '캔 유 히트 제너러스 쿠킹 오일?', ko: 'heat generous cooking oil 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['heat generous cooking oil', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll heat generous cooking oil in a wide frying pan.",
        fullPron: '아일 + 히트 제너러스 쿠킹 오일 + 인 어 와이드 프라잉 팬.',
        fullKo: '전의 가장자리가 튀겨지듯 바삭해지도록 식용유를 넉넉하게 둘러 달굽니다.'
      },
      {
        stepTitle: 'SCENE 5 · Spread Chives Thinly',
        visualEmojis: '🥬 🍳 🥄',
        imagePath: '/images/kfood/ep17-thumb.jpg',
        actionNote: '팬 위에 부추 반죽을 얇고 고르게 펼쳐 올리기',
        coachKo: "코어 블록은 'spread the chives evenly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'spread the chives evenly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달궈진 팬에 부추를 얇고 빈틈없이 동그랗게 펼쳐 줍니다.",
        missionEn: "Snap Mission! 'You can spread the chives evenly across the hot skillet.' Snap!",
        keyVocab: 'spread the chives evenly',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'spread the chives evenly', pron: '스프레드 더 차이브스 이븐리' },
          { role: 'db', en: 'across the hot skillet.', pron: '어크로스 더 핫 스킬렛' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can spread the chives evenly.', fullPron: '유 캔 스프레드 더 차이브스 이븐리', ko: 'spread the chives evenly 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to spread the chives evenly.', fullPron: '유 해브 투 스프레드 더 차이브스 이븐리', ko: 'spread the chives evenly 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you spread the chives evenly?', fullPron: '캔 유 스프레드 더 차이브스 이븐리?', ko: 'spread the chives evenly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['spread the chives evenly', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can spread the chives evenly across the hot skillet.",
        fullPron: '유 캔 + 스프레드 더 차이브스 이븐리 + 어크로스 더 핫 스킬렛.',
        fullKo: '달궈진 팬에 부추를 얇고 빈틈없이 동그랗게 펼쳐 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Top with Red Chili Slices',
        visualEmojis: '🌶️ 🔴 ✨',
        imagePath: '/images/kfood/ep17-thumb.jpg',
        actionNote: '고명으로 붉은 홍고추 채를 얹어 색감과 매콤함 더하기',
        coachKo: "코어 블록은 'top with red chili slices'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'top with red chili slices'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 화사한 색감과 알싸한 맛을 위해 붉은 홍고추 채를 고명으로 올립니다.",
        missionEn: "Snap Mission! 'We have to top with red chili slices for color and heat.' Snap!",
        keyVocab: 'top with red chili slices',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'top with red chili slices', pron: '탑 위드 레드 칠리 슬라이시스' },
          { role: 'db', en: 'for color and heat.', pron: '포 컬러 앤 히트' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to top with red chili slices.', fullPron: '위 해브 투 탑 위드 레드 칠리 슬라이시스', ko: 'top with red chili slices 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to top with red chili slices.', fullPron: '유 해브 투 탑 위드 레드 칠리 슬라이시스', ko: 'top with red chili slices 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you top with red chili slices?', fullPron: '캔 유 탑 위드 레드 칠리 슬라이시스?', ko: 'top with red chili slices 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['top with red chili slices', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to top with red chili slices for color and heat.",
        fullPron: '위 해브 투 + 탑 위드 레드 칠리 슬라이시스 + 포 컬러 앤 히트.',
        fullKo: '화사한 색감과 알싸한 맛을 위해 붉은 홍고추 채를 고명으로 올립니다.'
      },
      {
        stepTitle: 'SCENE 7 · Flip when Edges are Crispy',
        visualEmojis: '🥞 🔄 🔥',
        imagePath: '/images/kfood/ep17-thumb.jpg',
        actionNote: '가장자리가 노릇노릇해지면 단번에 뒤집기',
        coachKo: "코어 블록은 'flip the pancake'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'flip the pancake'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 바닥이 바삭하게 튀겨지듯 익었을 때 손목 스냅으로 단번에 뒤집어 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna flip the pancake once the bottom turns crispy.' Snap!",
        keyVocab: 'flip the pancake',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'flip the pancake', pron: '플립 더 팬케이크' },
          { role: 'db', en: 'once the bottom turns crispy.', pron: '원스 더 바텀 턴즈 크리스피' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna flip the pancake.', fullPron: '암거너 플립 더 팬케이크', ko: 'flip the pancake 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to flip the pancake.', fullPron: '유 해브 투 플립 더 팬케이크', ko: 'flip the pancake 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you flip the pancake?', fullPron: '캔 유 플립 더 팬케이크?', ko: 'flip the pancake 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['flip the pancake', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna flip the pancake once the bottom turns crispy.",
        fullPron: '암거너 + 플립 더 팬케이크 + 원스 더 바텀 턴즈 크리스피.',
        fullKo: '바닥이 바삭하게 튀겨지듯 익었을 때 손목 스냅으로 단번에 뒤집어 줍니다.'
      },
      {
        stepTitle: 'SCENE 8 · Crispy & Fragrant Chive Pancake',
        visualEmojis: '😋 🥢 🍶',
        imagePath: '/images/kfood/ep17-thumb.jpg',
        actionNote: '감탄 반응: 초간장에 콕 찍어 먹는 향긋하고 바삭한 부추전의 맛!',
        coachKo: "코어 블록은 'crispy and fragrant'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'crispy and fragrant'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 겉은 바삭바삭하고 부추 향이 입안 가득 퍼지며 초간장과 찰떡궁합이에요!",
        missionEn: "Snap Mission! 'It\'s so crispy and fragrant in tangy soy vinegar sauce!' Snap!",
        keyVocab: 'crispy and fragrant',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'crispy and fragrant', pron: '크리스피 앤 프레이그런트' },
          { role: 'db', en: 'in tangy soy vinegar sauce!', pron: '인 탱기 소이 비니거 소스' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so crispy and fragrant.', fullPron: '잇츠 쏘 크리스피 앤 프레이그런트', ko: 'crispy and fragrant 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to crispy and fragrant.', fullPron: '유 해브 투 크리스피 앤 프레이그런트', ko: 'crispy and fragrant 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you crispy and fragrant?', fullPron: '캔 유 크리스피 앤 프레이그런트?', ko: 'crispy and fragrant 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['crispy and fragrant', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so crispy and fragrant in tangy soy vinegar sauce!",
        fullPron: '잇츠 쏘 + 크리스피 앤 프레이그런트 + 인 탱기 소이 비니거 소스.',
        fullKo: '겉은 바삭바삭하고 부추 향이 입안 가득 퍼지며 초간장과 찰떡궁합이에요!'
      }
    ]
  },
  // ==========================================
  // EP.18. 🥔 Chewy Potato Pancake
  // ==========================================
  {
    id: 'gamjajeon',
    epNumber: 'EP.18',
    emoji: '🥔',
    shortTitle: '🥔 Chewy Potato Pancake',
    title: 'How to Make 100% Pure Korean Chewy Potato Pancake',
    ytTitle: 'How to Make Chewy Potato Pancake in Easy English 🥔 | SoundBlock K-Cooking EP.18',
    thumbnailText: '100% Pure Gamjajeon! [I\'ll] + [pan-fry grated potatoes until crispy]',
    thumbnailImage: '/images/kfood/ep18-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make authentic Korean Potato Pancake, golden chewy Gamjajeon with ultra-crispy edges, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for chewy Gamjajeon! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Peel & Wash Fresh Potatoes',
        visualEmojis: '🥔 💧 🔪',
        imagePath: '/images/kfood/ep18-thumb.jpg',
        actionNote: '감자 껍질을 벗기고 깨끗이 씻기',
        coachKo: "코어 블록은 'peel the potatoes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'peel the potatoes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 포슬포슬한 감자 껍질을 필러로 벗긴 뒤 찬물에 깨끗이 씻어 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna peel the potatoes and wash them clean.' Snap!",
        keyVocab: 'peel the potatoes',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'peel the potatoes', pron: '필 더 포테이토우스' },
          { role: 'db', en: 'and wash them clean.', pron: '앤 와시 뎀 클린' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna peel the potatoes.', fullPron: '암거너 필 더 포테이토우스', ko: 'peel the potatoes 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to peel the potatoes.', fullPron: '유 해브 투 필 더 포테이토우스', ko: 'peel the potatoes 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you peel the potatoes?', fullPron: '캔 유 필 더 포테이토우스?', ko: 'peel the potatoes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['peel the potatoes', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna peel the potatoes and wash them clean.",
        fullPron: '암거너 + 필 더 포테이토우스 + 앤 와시 뎀 클린.',
        fullKo: '포슬포슬한 감자 껍질을 필러로 벗긴 뒤 찬물에 깨끗이 씻어 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Grate Potatoes on Box Grater',
        visualEmojis: '🥔 ⚙️ 🥣',
        imagePath: '/images/kfood/ep18-thumb.jpg',
        actionNote: '강판에 정성껏 갈아 쫄깃한 식감 살리기',
        coachKo: "코어 블록은 'grate the potatoes finely'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'grate the potatoes finely'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 믹서기 대신 강판에 직접 갈아주어야 감자 특유의 쫄깃한 식감이 극대화됩니다.",
        missionEn: "Snap Mission! 'You have to grate the potatoes finely on a hand grater.' Snap!",
        keyVocab: 'grate the potatoes finely',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'grate the potatoes finely', pron: '그레이트 더 포테이토우스 파인리' },
          { role: 'db', en: 'on a hand grater.', pron: '온 어 핸드 그레이터' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to grate the potatoes finely.', fullPron: '유 해브 투 그레이트 더 포테이토우스 파인리', ko: 'grate the potatoes finely 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to grate the potatoes finely.', fullPron: '유 해브 투 그레이트 더 포테이토우스 파인리', ko: 'grate the potatoes finely 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you grate the potatoes finely?', fullPron: '캔 유 그레이트 더 포테이토우스 파인리?', ko: 'grate the potatoes finely 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['grate the potatoes finely', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to grate the potatoes finely on a hand grater.",
        fullPron: '유 해브 투 + 그레이트 더 포테이토우스 파인리 + 온 어 핸드 그레이터.',
        fullKo: '믹서기 대신 강판에 직접 갈아주어야 감자 특유의 쫄깃한 식감이 극대화됩니다.'
      },
      {
        stepTitle: 'SCENE 3 · Strain over Large Bowl',
        visualEmojis: '🥣 🧺 💧',
        imagePath: '/images/kfood/ep18-thumb.jpg',
        actionNote: '갈아둔 감자를 체에 밭쳐 감자물 분리하기',
        coachKo: "코어 블록은 'strain the grated potatoes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'strain the grated potatoes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 체에 갈아둔 감자를 올려 숟가락으로 꾹 누르며 감자물을 받아냅니다.",
        missionEn: "Snap Mission! 'We\'re gonna strain the grated potatoes over a large bowl.' Snap!",
        keyVocab: 'strain the grated potatoes',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'strain the grated potatoes', pron: '스트레인 더 그레이티드 포테이토우스' },
          { role: 'db', en: 'over a large bowl.', pron: '오버 어 라지 보울' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna strain the grated potatoes.', fullPron: '웨어 거너 스트레인 더 그레이티드 포테이토우스', ko: 'strain the grated potatoes 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to strain the grated potatoes.', fullPron: '유 해브 투 스트레인 더 그레이티드 포테이토우스', ko: 'strain the grated potatoes 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you strain the grated potatoes?', fullPron: '캔 유 스트레인 더 그레이티드 포테이토우스?', ko: 'strain the grated potatoes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['strain the grated potatoes', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna strain the grated potatoes over a large bowl.",
        fullPron: '웨어 거너 + 스트레인 더 그레이티드 포테이토우스 + 오버 어 라지 보울.',
        fullKo: '체에 갈아둔 감자를 올려 숟가락으로 꾹 누르며 감자물을 받아냅니다.'
      },
      {
        stepTitle: 'SCENE 4 · Collect Settled Potato Starch',
        visualEmojis: '⚪ ✨ 🥣',
        imagePath: '/images/kfood/ep18-thumb.jpg',
        actionNote: '가라앉은 뽀얀 100% 순수 감자 전분 모으기',
        coachKo: "코어 블록은 'collect the potato starch'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'collect the potato starch'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 받아둔 감자물을 10분간 두면 바닥에 가라앉는 하얀 순수 전분을 모아 줍니다.",
        missionEn: "Snap Mission! 'I\'ll collect the potato starch from the bottom.' Snap!",
        keyVocab: 'collect the potato starch',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'collect the potato starch', pron: '콜렉트 더 포테이토 스타치' },
          { role: 'db', en: 'from the bottom.', pron: '프럼 더 바텀' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll collect the potato starch.', fullPron: '아일 콜렉트 더 포테이토 스타치', ko: 'collect the potato starch 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to collect the potato starch.', fullPron: '유 해브 투 콜렉트 더 포테이토 스타치', ko: 'collect the potato starch 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you collect the potato starch?', fullPron: '캔 유 콜렉트 더 포테이토 스타치?', ko: 'collect the potato starch 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['collect the potato starch', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll collect the potato starch from the bottom.",
        fullPron: '아일 + 콜렉트 더 포테이토 스타치 + 프럼 더 바텀.',
        fullKo: '받아둔 감자물을 10분간 두면 바닥에 가라앉는 하얀 순수 전분을 모아 줍니다.'
      },
      {
        stepTitle: 'SCENE 5 · Mix Pulp with Starch & Salt',
        visualEmojis: '🥔 ⚪ 🧂',
        imagePath: '/images/kfood/ep18-thumb.jpg',
        actionNote: '건더기와 앙금 전분을 소금 한 꼬집과 섞기',
        coachKo: "코어 블록은 'mix the potato pulp'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix the potato pulp'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 밀가루 없이, 걸러둔 감자 건더기와 바닥의 전분, 소금만 넣고 반죽합니다.",
        missionEn: "Snap Mission! 'You can mix the potato pulp with starch and salt.' Snap!",
        keyVocab: 'mix the potato pulp',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'mix the potato pulp', pron: '믹스 더 포테이토 펄프' },
          { role: 'db', en: 'with starch and salt.', pron: '위드 스타치 앤 솔트' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can mix the potato pulp.', fullPron: '유 캔 믹스 더 포테이토 펄프', ko: 'mix the potato pulp 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix the potato pulp.', fullPron: '유 해브 투 믹스 더 포테이토 펄프', ko: 'mix the potato pulp 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you mix the potato pulp?', fullPron: '캔 유 믹스 더 포테이토 펄프?', ko: 'mix the potato pulp 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['mix the potato pulp', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can mix the potato pulp with starch and salt.",
        fullPron: '유 캔 + 믹스 더 포테이토 펄프 + 위드 스타치 앤 솔트.',
        fullKo: '밀가루 없이, 걸러둔 감자 건더기와 바닥의 전분, 소금만 넣고 반죽합니다.'
      },
      {
        stepTitle: 'SCENE 6 · Spoon into Sizzling Hot Oil',
        visualEmojis: '🍳 🫒 🥄',
        imagePath: '/images/kfood/ep18-thumb.jpg',
        actionNote: '기름 두른 팬에 반죽을 도톰하게 올려 부치기',
        coachKo: "코어 블록은 'spoon the batter'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'spoon the batter'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달궈진 팬에 기름을 넉넉히 두르고 감자 반죽을 동글도톰하게 올려 줍니다.",
        missionEn: "Snap Mission! 'We have to spoon the batter into a hot skillet.' Snap!",
        keyVocab: 'spoon the batter',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'spoon the batter', pron: '스푼 더 배터' },
          { role: 'db', en: 'into a hot skillet.', pron: '인투 어 핫 스킬렛' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to spoon the batter.', fullPron: '위 해브 투 스푼 더 배터', ko: 'spoon the batter 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to spoon the batter.', fullPron: '유 해브 투 스푼 더 배터', ko: 'spoon the batter 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you spoon the batter?', fullPron: '캔 유 스푼 더 배터?', ko: 'spoon the batter 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['spoon the batter', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to spoon the batter into a hot skillet.",
        fullPron: '위 해브 투 + 스푼 더 배터 + 인투 어 핫 스킬렛.',
        fullKo: '달궈진 팬에 기름을 넉넉히 두르고 감자 반죽을 동글도톰하게 올려 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Pan-Fry until Translucent & Crisp',
        visualEmojis: '🔥 🥔 🥞',
        imagePath: '/images/kfood/ep18-thumb.jpg',
        actionNote: '중약불에서 속이 투명해지고 겉이 바삭할 때까지 굽기',
        coachKo: "코어 블록은 'pan-fry on medium heat'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pan-fry on medium heat'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 감자가 투명해지고 가장자리가 바삭한 황금빛이 될 때까지 노릇하게 굽습니다.",
        missionEn: "Snap Mission! 'I\'m gonna pan-fry on medium heat until golden brown.' Snap!",
        keyVocab: 'pan-fry on medium heat',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'pan-fry on medium heat', pron: '팬-프라이 온 미디엄 히트' },
          { role: 'db', en: 'until golden brown.', pron: '언틸 골든 브라운' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pan-fry on medium heat.', fullPron: '암거너 팬-프라이 온 미디엄 히트', ko: 'pan-fry on medium heat 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pan-fry on medium heat.', fullPron: '유 해브 투 팬-프라이 온 미디엄 히트', ko: 'pan-fry on medium heat 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you pan-fry on medium heat?', fullPron: '캔 유 팬-프라이 온 미디엄 히트?', ko: 'pan-fry on medium heat 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['pan-fry on medium heat', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna pan-fry on medium heat until golden brown.",
        fullPron: '암거너 + 팬-프라이 온 미디엄 히트 + 언틸 골든 브라운.',
        fullKo: '감자가 투명해지고 가장자리가 바삭한 황금빛이 될 때까지 노릇하게 굽습니다.'
      },
      {
        stepTitle: 'SCENE 8 · Chewy Center & Ultra-Crisp Edges',
        visualEmojis: '😋 🥔 💥',
        imagePath: '/images/kfood/ep18-thumb.jpg',
        actionNote: '감탄 반응: 밀가루 0%! 감자 본연의 쫀득함과 바삭함의 조화!',
        coachKo: "코어 블록은 'chewy and crispy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'chewy and crispy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 가장자리는 감자칩처럼 파삭하고 가운데는 찰떡처럼 쫀득해서 최고예요!",
        missionEn: "Snap Mission! 'It\'s so chewy and crispy with natural potato flavor!' Snap!",
        keyVocab: 'chewy and crispy',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'chewy and crispy', pron: '츄이 앤 크리스피' },
          { role: 'db', en: 'with natural potato flavor!', pron: '위드 내추럴 포테이토 플레이버' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so chewy and crispy.', fullPron: '잇츠 쏘 츄이 앤 크리스피', ko: 'chewy and crispy 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to chewy and crispy.', fullPron: '유 해브 투 츄이 앤 크리스피', ko: 'chewy and crispy 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you chewy and crispy?', fullPron: '캔 유 츄이 앤 크리스피?', ko: 'chewy and crispy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['chewy and crispy', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so chewy and crispy with natural potato flavor!",
        fullPron: '잇츠 쏘 + 츄이 앤 크리스피 + 위드 내추럴 포테이토 플레이버.',
        fullKo: '가장자리는 감자칩처럼 파삭하고 가운데는 찰떡처럼 쫀득해서 최고예요!'
      }
    ]
  },
  // ==========================================
  // EP.19. 🧊 Refreshing Water Kimchi
  // ==========================================
  {
    id: 'mul-kimchi',
    epNumber: 'EP.19',
    emoji: '🧊',
    shortTitle: '🧊 Refreshing Water Kimchi',
    title: 'How to Make Refreshing Korean Chilled Water Kimchi',
    ytTitle: 'How to Make Korean Water Kimchi in Easy English 🧊 | SoundBlock K-Cooking EP.19',
    thumbnailText: 'Chilled Mul-Kimchi! [We\'re gonna] + [pour cold mineral broth over sliced radish]',
    thumbnailImage: '/images/kfood/ep19-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make refreshing Korean Water Kimchi, chilled sparkling Dongchimi with crisp radish and pear, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for refreshing Water Kimchi! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Cut Radish into Thin Squares',
        visualEmojis: '⚪ 🔪 🧺',
        imagePath: '/images/kfood/ep19-thumb.jpg',
        actionNote: '무를 나박나박 네모나고 얇게 썰기',
        coachKo: "코어 블록은 'cut Korean radish'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'cut Korean radish'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 한 입에 쏙 들어가도록 아삭한 무를 네모나고 얇게 나박 썰어 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna cut Korean radish into thin squares.' Snap!",
        keyVocab: 'cut Korean radish',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'cut Korean radish', pron: '컷 코리안 래디시' },
          { role: 'db', en: 'into thin squares.', pron: '인투 씬 스퀘어스' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna cut Korean radish.', fullPron: '암거너 컷 코리안 래디시', ko: 'cut Korean radish 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to cut Korean radish.', fullPron: '유 해브 투 컷 코리안 래디시', ko: 'cut Korean radish 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you cut Korean radish?', fullPron: '캔 유 컷 코리안 래디시?', ko: 'cut Korean radish 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['cut Korean radish', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna cut Korean radish into thin squares.",
        fullPron: '암거너 + 컷 코리안 래디시 + 인투 씬 스퀘어스.',
        fullKo: '한 입에 쏙 들어가도록 아삭한 무를 네모나고 얇게 나박 썰어 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Toss with Coarse Salt & Sugar',
        visualEmojis: '🧂 🍬 🥣',
        imagePath: '/images/kfood/ep19-thumb.jpg',
        actionNote: '천일염과 설탕을 뿌려 20분간 살짝 절이기',
        coachKo: "코어 블록은 'toss with coarse sea salt'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toss with coarse sea salt'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 굵은 천일염과 설탕 한 꼬집을 넣고 고루 버무려 수분을 촉촉하게 뺍니다.",
        missionEn: "Snap Mission! 'You have to toss with coarse sea salt and a pinch of sugar.' Snap!",
        keyVocab: 'toss with coarse sea salt',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'toss with coarse sea salt', pron: '토스 위드 코어스 씨 솔트' },
          { role: 'db', en: 'and a pinch of sugar.', pron: '앤 어 핀치 오브 슈가' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to toss with coarse sea salt.', fullPron: '유 해브 투 토스 위드 코어스 씨 솔트', ko: 'toss with coarse sea salt 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to toss with coarse sea salt.', fullPron: '유 해브 투 토스 위드 코어스 씨 솔트', ko: 'toss with coarse sea salt 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you toss with coarse sea salt?', fullPron: '캔 유 토스 위드 코어스 씨 솔트?', ko: 'toss with coarse sea salt 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['toss with coarse sea salt', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to toss with coarse sea salt and a pinch of sugar.",
        fullPron: '유 해브 투 + 토스 위드 코어스 씨 솔트 + 앤 어 핀치 오브 슈가.',
        fullKo: '굵은 천일염과 설탕 한 꼬집을 넣고 고루 버무려 수분을 촉촉하게 뺍니다.'
      },
      {
        stepTitle: 'SCENE 3 · Slice Sweet Asian Pear',
        visualEmojis: '🍐 🔪 ✨',
        imagePath: '/images/kfood/ep19-thumb.jpg',
        actionNote: '달콤하고 시원한 배를 같은 크기로 썰기',
        coachKo: "코어 블록은 'slice sweet Asian pear'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice sweet Asian pear'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 자연스러운 단맛과 청량감을 더해 줄 배를 무와 같은 크기로 썰어 줍니다.",
        missionEn: "Snap Mission! 'We\'re gonna slice sweet Asian pear into crisp matching pieces.' Snap!",
        keyVocab: 'slice sweet Asian pear',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'slice sweet Asian pear', pron: '슬라이스 스위트 에이시언 페어' },
          { role: 'db', en: 'into crisp matching pieces.', pron: '인투 크리스프 매칭 피시스' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna slice sweet Asian pear.', fullPron: '웨어 거너 슬라이스 스위트 에이시언 페어', ko: 'slice sweet Asian pear 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice sweet Asian pear.', fullPron: '유 해브 투 슬라이스 스위트 에이시언 페어', ko: 'slice sweet Asian pear 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you slice sweet Asian pear?', fullPron: '캔 유 슬라이스 스위트 에이시언 페어?', ko: 'slice sweet Asian pear 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['slice sweet Asian pear', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna slice sweet Asian pear into crisp matching pieces.",
        fullPron: '웨어 거너 + 슬라이스 스위트 에이시언 페어 + 인투 크리스프 매칭 피시스.',
        fullKo: '자연스러운 단맛과 청량감을 더해 줄 배를 무와 같은 크기로 썰어 줍니다.'
      },
      {
        stepTitle: 'SCENE 4 · Place Garlic & Ginger in Pouch',
        visualEmojis: '🧄 🌿 🧺',
        imagePath: '/images/kfood/ep19-thumb.jpg',
        actionNote: '마늘편과 생강을 다시백에 담아 국물 맑게 유지하기',
        coachKo: "코어 블록은 'place sliced garlic'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'place sliced garlic'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 국물이 지저분해지지 않고 맑게 우러나도록 마늘과 생강을 주머니에 넣습니다.",
        missionEn: "Snap Mission! 'I\'ll place sliced garlic in a spice pouch.' Snap!",
        keyVocab: 'place sliced garlic',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'place sliced garlic', pron: '플레이스 슬라이스트 갈릭' },
          { role: 'db', en: 'in a spice pouch.', pron: '인 어 스파이스 파우치' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll place sliced garlic.', fullPron: '아일 플레이스 슬라이스트 갈릭', ko: 'place sliced garlic 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to place sliced garlic.', fullPron: '유 해브 투 플레이스 슬라이스트 갈릭', ko: 'place sliced garlic 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you place sliced garlic?', fullPron: '캔 유 플레이스 슬라이스트 갈릭?', ko: 'place sliced garlic 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['place sliced garlic', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll place sliced garlic in a spice pouch.",
        fullPron: '아일 + 플레이스 슬라이스트 갈릭 + 인 어 스파이스 파우치.',
        fullKo: '국물이 지저분해지지 않고 맑게 우러나도록 마늘과 생강을 주머니에 넣습니다.'
      },
      {
        stepTitle: 'SCENE 5 · Pack into Clean Glass Jar',
        visualEmojis: '🏺 ⚪ 🍐',
        imagePath: '/images/kfood/ep19-thumb.jpg',
        actionNote: '절인 무와 배, 쪽파를 유리병에 얌전하게 담기',
        coachKo: "코어 블록은 'pack the salted radish'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pack the salted radish'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 깨끗이 소독한 유리병에 절인 무와 배, 쪽파를 차곡차곡 담아 줍니다.",
        missionEn: "Snap Mission! 'You can pack the salted radish into a clean glass jar.' Snap!",
        keyVocab: 'pack the salted radish',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'pack the salted radish', pron: '팩 더 솔티드 래디시' },
          { role: 'db', en: 'into a clean glass jar.', pron: '인투 어 클린 글래스 자' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can pack the salted radish.', fullPron: '유 캔 팩 더 솔티드 래디시', ko: 'pack the salted radish 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pack the salted radish.', fullPron: '유 해브 투 팩 더 솔티드 래디시', ko: 'pack the salted radish 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you pack the salted radish?', fullPron: '캔 유 팩 더 솔티드 래디시?', ko: 'pack the salted radish 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['pack the salted radish', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can pack the salted radish into a clean glass jar.",
        fullPron: '유 캔 + 팩 더 솔티드 래디시 + 인투 어 클린 글래스 자.',
        fullKo: '깨끗이 소독한 유리병에 절인 무와 배, 쪽파를 차곡차곡 담아 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Pour Seasoned Cold Water',
        visualEmojis: '💧 🌊 🧂',
        imagePath: '/images/kfood/ep19-thumb.jpg',
        actionNote: '소금과 매실청으로 간한 생수를 찰랑찰랑 붓기',
        coachKo: "코어 블록은 'pour seasoned mineral water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour seasoned mineral water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 소금과 매실청으로 슴슴하고 시원하게 간을 맞춘 생수를 듬뿍 부어 줍니다.",
        missionEn: "Snap Mission! 'We have to pour seasoned mineral water over all the vegetables.' Snap!",
        keyVocab: 'pour seasoned mineral water',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'pour seasoned mineral water', pron: '푸어 시즌드 미네랄 워터' },
          { role: 'db', en: 'over all the vegetables.', pron: '오버 올 더 베지터블스' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to pour seasoned mineral water.', fullPron: '위 해브 투 푸어 시즌드 미네랄 워터', ko: 'pour seasoned mineral water 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour seasoned mineral water.', fullPron: '유 해브 투 푸어 시즌드 미네랄 워터', ko: 'pour seasoned mineral water 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you pour seasoned mineral water?', fullPron: '캔 유 푸어 시즌드 미네랄 워터?', ko: 'pour seasoned mineral water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['pour seasoned mineral water', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to pour seasoned mineral water over all the vegetables.",
        fullPron: '위 해브 투 + 푸어 시즌드 미네랄 워터 + 오버 올 더 베지터블스.',
        fullKo: '소금과 매실청으로 슴슴하고 시원하게 간을 맞춘 생수를 듬뿍 부어 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Ferment at Room Temperature',
        visualEmojis: '🌡️ ⏰ 🧊',
        imagePath: '/images/kfood/ep19-thumb.jpg',
        actionNote: '실온에서 이틀간 익힌 후 냉장 숙성하기',
        coachKo: "코어 블록은 'ferment at room temperature'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'ferment at room temperature'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 새콤한 기포가 뽀글뽀글 올라올 때까지 실온에서 이틀간 둔 뒤 냉장고에 넣습니다.",
        missionEn: "Snap Mission! 'I\'m gonna ferment at room temperature for two days.' Snap!",
        keyVocab: 'ferment at room temperature',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'ferment at room temperature', pron: '퍼멘트 앳 룸 템퍼러쳐' },
          { role: 'db', en: 'for two days.', pron: '포 투 데이즈' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna ferment at room temperature.', fullPron: '암거너 퍼멘트 앳 룸 템퍼러쳐', ko: 'ferment at room temperature 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to ferment at room temperature.', fullPron: '유 해브 투 퍼멘트 앳 룸 템퍼러쳐', ko: 'ferment at room temperature 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you ferment at room temperature?', fullPron: '캔 유 퍼멘트 앳 룸 템퍼러쳐?', ko: 'ferment at room temperature 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['ferment at room temperature', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna ferment at room temperature for two days.",
        fullPron: '암거너 + 퍼멘트 앳 룸 템퍼러쳐 + 포 투 데이즈.',
        fullKo: '새콤한 기포가 뽀글뽀글 올라올 때까지 실온에서 이틀간 둔 뒤 냉장고에 넣습니다.'
      },
      {
        stepTitle: 'SCENE 8 · Crisp & Tangy Sparkling Broth',
        visualEmojis: '😋 🧊 🌟',
        imagePath: '/images/kfood/ep19-thumb.jpg',
        actionNote: '감탄 반응: 살얼음 동동 띄워 마시는 가슴속까지 뻥 뚫리는 시원함!',
        coachKo: "코어 블록은 'crisp and tangy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'crisp and tangy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 탄산처럼 톡 쏘는 청량한 국물과 아삭아삭한 무가 기름진 속을 싹 씻어 줘요!",
        missionEn: "Snap Mission! 'It\'s so crisp and tangy with ice-cold sparkling broth!' Snap!",
        keyVocab: 'crisp and tangy',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'crisp and tangy', pron: '크리스프 앤 탱기' },
          { role: 'db', en: 'with ice-cold sparkling broth!', pron: '위드 아이스-콜드 스파클링 브로쓰' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so crisp and tangy.', fullPron: '잇츠 쏘 크리스프 앤 탱기', ko: 'crisp and tangy 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to crisp and tangy.', fullPron: '유 해브 투 크리스프 앤 탱기', ko: 'crisp and tangy 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you crisp and tangy?', fullPron: '캔 유 크리스프 앤 탱기?', ko: 'crisp and tangy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['crisp and tangy', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so crisp and tangy with ice-cold sparkling broth!",
        fullPron: '잇츠 쏘 + 크리스프 앤 탱기 + 위드 아이스-콜드 스파클링 브로쓰.',
        fullKo: '탄산처럼 톡 쏘는 청량한 국물과 아삭아삭한 무가 기름진 속을 싹 씻어 줘요!'
      }
    ]
  },
  // ==========================================
  // EP.20. 🌶️ Ponytail Radish Kimchi
  // ==========================================
  {
    id: 'chonggak-kimchi',
    epNumber: 'EP.20',
    emoji: '🌶️',
    shortTitle: '🌶️ Ponytail Radish Kimchi',
    title: 'How to Make Crunchy Korean Ponytail Radish Kimchi',
    ytTitle: 'How to Make Chonggak Kimchi in Easy English 🌶️ | SoundBlock K-Cooking EP.20',
    thumbnailText: 'Crunchy Chonggak Kimchi! [You have to] + [coat crunchy radishes in spicy red paste]',
    thumbnailImage: '/images/kfood/ep20-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make crunchy Korean Ponytail Radish Kimchi, savory Chonggak Kimchi with spicy red paste, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for crunchy Chonggak Kimchi! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Scrub & Trim Ponytail Radishes',
        visualEmojis: '🌱 🔪 🧼',
        imagePath: '/images/kfood/ep20-thumb.jpg',
        actionNote: '총각무의 무청 연결부 흙을 다듬고 겉껍질 살짝 긁기',
        coachKo: "코어 블록은 'trim the ponytail radishes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'trim the ponytail radishes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 무와 무청 연결 부위의 흙을 칼끝으로 꼼꼼히 긁어내고 다듬어 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna trim the ponytail radishes carefully.' Snap!",
        keyVocab: 'trim the ponytail radishes',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'trim the ponytail radishes', pron: '트림 더 포니테일 래디시스' },
          { role: 'db', en: 'carefully.', pron: '케어풀리' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna trim the ponytail radishes.', fullPron: '암거너 트림 더 포니테일 래디시스', ko: 'trim the ponytail radishes 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to trim the ponytail radishes.', fullPron: '유 해브 투 트림 더 포니테일 래디시스', ko: 'trim the ponytail radishes 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you trim the ponytail radishes?', fullPron: '캔 유 트림 더 포니테일 래디시스?', ko: 'trim the ponytail radishes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['trim the ponytail radishes', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna trim the ponytail radishes carefully.",
        fullPron: '암거너 + 트림 더 포니테일 래디시스 + 케어풀리.',
        fullKo: '무와 무청 연결 부위의 흙을 칼끝으로 꼼꼼히 긁어내고 다듬어 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Salt Radishes with Coarse Salt',
        visualEmojis: '🧂 ⏰ 🥣',
        imagePath: '/images/kfood/ep20-thumb.jpg',
        actionNote: '굵은 천일염을 뿌려 2시간 동안 숨 죽이기',
        coachKo: "코어 블록은 'salt the radishes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'salt the radishes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 천일염을 듬뿍 뿌려 무가 탄력 있게 구부러질 때까지 2시간 동안 절여 줍니다.",
        missionEn: "Snap Mission! 'You have to salt the radishes with coarse salt for two hours.' Snap!",
        keyVocab: 'salt the radishes',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'salt the radishes', pron: '솔트 더 래디시스' },
          { role: 'db', en: 'with coarse salt for two hours.', pron: '위드 코어스 솔트 포 투 아워스' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to salt the radishes.', fullPron: '유 해브 투 솔트 더 래디시스', ko: 'salt the radishes 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to salt the radishes.', fullPron: '유 해브 투 솔트 더 래디시스', ko: 'salt the radishes 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you salt the radishes?', fullPron: '캔 유 솔트 더 래디시스?', ko: 'salt the radishes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['salt the radishes', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to salt the radishes with coarse salt for two hours.",
        fullPron: '유 해브 투 + 솔트 더 래디시스 + 위드 코어스 솔트 포 투 아워스.',
        fullKo: '천일염을 듬뿍 뿌려 무가 탄력 있게 구부러질 때까지 2시간 동안 절여 줍니다.'
      },
      {
        stepTitle: 'SCENE 3 · Rinse in Cold Water 3 Times',
        visualEmojis: '💧 🌊 🧺',
        imagePath: '/images/kfood/ep20-thumb.jpg',
        actionNote: '찬물에 3번 헹궈 짠기를 빼고 물기 받치기',
        coachKo: "코어 블록은 'rinse in cold water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'rinse in cold water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 절여진 총각무를 찬물에 세 번 깨끗이 헹군 뒤 소쿠리에 받쳐 물기를 뺍니다.",
        missionEn: "Snap Mission! 'We\'re gonna rinse in cold water three times and drain.' Snap!",
        keyVocab: 'rinse in cold water',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'rinse in cold water', pron: '린스 인 콜드 워터' },
          { role: 'db', en: 'three times and drain.', pron: '쓰리 타임즈 앤 드레인' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna rinse in cold water.', fullPron: '웨어 거너 린스 인 콜드 워터', ko: 'rinse in cold water 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to rinse in cold water.', fullPron: '유 해브 투 린스 인 콜드 워터', ko: 'rinse in cold water 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you rinse in cold water?', fullPron: '캔 유 린스 인 콜드 워터?', ko: 'rinse in cold water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['rinse in cold water', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna rinse in cold water three times and drain.",
        fullPron: '웨어 거너 + 린스 인 콜드 워터 + 쓰리 타임즈 앤 드레인.',
        fullKo: '절여진 총각무를 찬물에 세 번 깨끗이 헹군 뒤 소쿠리에 받쳐 물기를 뺍니다.'
      },
      {
        stepTitle: 'SCENE 4 · Blend Spicy Chili Paste',
        visualEmojis: '🌶️ 🧄 🐟',
        imagePath: '/images/kfood/ep20-thumb.jpg',
        actionNote: '고춧가루, 다진 마늘, 멸치액젓, 새우젓 갈기',
        coachKo: "코어 블록은 'blend the red chili paste'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'blend the red chili paste'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 태양초 고춧가루에 멸치액젓과 새우젓, 다진 마늘, 생강을 넣고 양념을 갑니다.",
        missionEn: "Snap Mission! 'I\'ll blend the red chili paste with garlic and fish sauce.' Snap!",
        keyVocab: 'blend the red chili paste',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'blend the red chili paste', pron: '블렌드 더 레드 칠리 페이스트' },
          { role: 'db', en: 'with garlic and fish sauce.', pron: '위드 갈릭 앤 피시 소스' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll blend the red chili paste.', fullPron: '아일 블렌드 더 레드 칠리 페이스트', ko: 'blend the red chili paste 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to blend the red chili paste.', fullPron: '유 해브 투 블렌드 더 레드 칠리 페이스트', ko: 'blend the red chili paste 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you blend the red chili paste?', fullPron: '캔 유 블렌드 더 레드 칠리 페이스트?', ko: 'blend the red chili paste 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['blend the red chili paste', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll blend the red chili paste with garlic and fish sauce.",
        fullPron: '아일 + 블렌드 더 레드 칠리 페이스트 + 위드 갈릭 앤 피시 소스.',
        fullKo: '태양초 고춧가루에 멸치액젓과 새우젓, 다진 마늘, 생강을 넣고 양념을 갑니다.'
      },
      {
        stepTitle: 'SCENE 5 · Fold in Sweet Rice Porridge',
        visualEmojis: '🥣 🍚 ✨',
        imagePath: '/images/kfood/ep20-thumb.jpg',
        actionNote: '찹쌀풀을 섞어 양념의 감칠맛과 발효 돕기',
        coachKo: "코어 블록은 'fold in sweet rice porridge'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fold in sweet rice porridge'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양념이 착 달라붙고 유산균이 잘 번식하도록 쑨 찹쌀풀을 고루 섞어 줍니다.",
        missionEn: "Snap Mission! 'You can fold in sweet rice porridge to help fermentation.' Snap!",
        keyVocab: 'fold in sweet rice porridge',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'fold in sweet rice porridge', pron: '폴드 인 스위트 라이스 포리지' },
          { role: 'db', en: 'to help fermentation.', pron: '투 헬프 퍼멘테이션' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can fold in sweet rice porridge.', fullPron: '유 캔 폴드 인 스위트 라이스 포리지', ko: 'fold in sweet rice porridge 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to fold in sweet rice porridge.', fullPron: '유 해브 투 폴드 인 스위트 라이스 포리지', ko: 'fold in sweet rice porridge 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you fold in sweet rice porridge?', fullPron: '캔 유 폴드 인 스위트 라이스 포리지?', ko: 'fold in sweet rice porridge 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['fold in sweet rice porridge', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can fold in sweet rice porridge to help fermentation.",
        fullPron: '유 캔 + 폴드 인 스위트 라이스 포리지 + 투 헬프 퍼멘테이션.',
        fullKo: '양념이 착 달라붙고 유산균이 잘 번식하도록 쑨 찹쌀풀을 고루 섞어 줍니다.'
      },
      {
        stepTitle: 'SCENE 6 · Coat Each Radish Generously',
        visualEmojis: '🌶️ 🤲 🌿',
        imagePath: '/images/kfood/ep20-thumb.jpg',
        actionNote: '빨간 양념을 총각무와 무청에 듬뿍 버무리기',
        coachKo: "코어 블록은 'coat each radish'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'coat each radish'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 진하고 빨간 양념장을 총각무 하나하나와 무청 사이사이에 골고루 바릅니다.",
        missionEn: "Snap Mission! 'We have to coat each radish and stem generously.' Snap!",
        keyVocab: 'coat each radish',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'coat each radish', pron: '코우트 이치 래디시' },
          { role: 'db', en: 'and stem generously.', pron: '앤 스템 제너러스리' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to coat each radish.', fullPron: '위 해브 투 코우트 이치 래디시', ko: 'coat each radish 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to coat each radish.', fullPron: '유 해브 투 코우트 이치 래디시', ko: 'coat each radish 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you coat each radish?', fullPron: '캔 유 코우트 이치 래디시?', ko: 'coat each radish 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['coat each radish', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to coat each radish and stem generously.",
        fullPron: '위 해브 투 + 코우트 이치 래디시 + 앤 스템 제너러스리.',
        fullKo: '진하고 빨간 양념장을 총각무 하나하나와 무청 사이사이에 골고루 바릅니다.'
      },
      {
        stepTitle: 'SCENE 7 · Pack Neatly into Jar',
        visualEmojis: '🏺 🥬 🤲',
        imagePath: '/images/kfood/ep20-thumb.jpg',
        actionNote: '무청을 무에 돌돌 말아 김치통에 차곡차곡 담기',
        coachKo: "코어 블록은 'pack into a jar'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pack into a jar'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 무청으로 무를 감싸서 공기가 통하지 않도록 김치통에 꾹꾹 눌러 담습니다.",
        missionEn: "Snap Mission! 'I\'m gonna pack into a jar neatly in layers.' Snap!",
        keyVocab: 'pack into a jar',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'pack into a jar', pron: '팩 인투 어 자' },
          { role: 'db', en: 'neatly in layers.', pron: '니틀리 인 레이어스' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pack into a jar.', fullPron: '암거너 팩 인투 어 자', ko: 'pack into a jar 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pack into a jar.', fullPron: '유 해브 투 팩 인투 어 자', ko: 'pack into a jar 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you pack into a jar?', fullPron: '캔 유 팩 인투 어 자?', ko: 'pack into a jar 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['pack into a jar', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna pack into a jar neatly in layers.",
        fullPron: '암거너 + 팩 인투 어 자 + 니틀리 인 레이어스.',
        fullKo: '무청으로 무를 감싸서 공기가 통하지 않도록 김치통에 꾹꾹 눌러 담습니다.'
      },
      {
        stepTitle: 'SCENE 8 · Crunchy Sound & Bold Spicy Flavor',
        visualEmojis: '😋 🌶️ 💥',
        imagePath: '/images/kfood/ep20-thumb.jpg',
        actionNote: '감탄 반응: 한 입 베어 물면 와작! 소리 나는 전설의 밥도둑!',
        coachKo: "코어 블록은 'crunchy and bold'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'crunchy and bold'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 베어 물 때마다 아삭아삭 와작와작 소리가 나며 진한 양념이 끝내줘요!",
        missionEn: "Snap Mission! 'It\'s so crunchy and bold with authentic garlicky kick!' Snap!",
        keyVocab: 'crunchy and bold',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'crunchy and bold', pron: '크런치 앤 볼드' },
          { role: 'db', en: 'with authentic garlicky kick!', pron: '위드 어쎈틱 갈리키 킥' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so crunchy and bold.', fullPron: '잇츠 쏘 크런치 앤 볼드', ko: 'crunchy and bold 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to crunchy and bold.', fullPron: '유 해브 투 크런치 앤 볼드', ko: 'crunchy and bold 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you crunchy and bold?', fullPron: '캔 유 크런치 앤 볼드?', ko: 'crunchy and bold 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['crunchy and bold', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so crunchy and bold with authentic garlicky kick!",
        fullPron: '잇츠 쏘 + 크런치 앤 볼드 + 위드 어쎈틱 갈리키 킥.',
        fullKo: '베어 물 때마다 아삭아삭 와작와작 소리가 나며 진한 양념이 끝내줘요!'
      }
    ]
  },
  // ==========================================
  // EP.21. 🥗 Fresh Quick Kimchi
  // ==========================================
  {
    id: 'geotjeori',
    epNumber: 'EP.21',
    emoji: '🥗',
    shortTitle: '🥗 Fresh Quick Kimchi',
    title: 'How to Make Fresh Korean Quick Napa Cabbage Kimchi',
    ytTitle: 'How to Make Fresh Cabbage Kimchi in Easy English 🥗 | SoundBlock K-Cooking EP.21',
    thumbnailText: 'Fresh Quick Kimchi! [I\'m gonna] + [toss fresh cabbage leaves in savory red sauce]',
    thumbnailImage: '/images/kfood/ep21-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make fresh Korean Quick Kimchi, crunchy Napa Cabbage Geotjeori tossed in spicy garlic sauce, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for fresh Geotjeori! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Tear Cabbage Leaves',
        visualEmojis: '🥬 🔪 🥣',
        imagePath: '/images/kfood/ep21-thumb.jpg',
        actionNote: '알배기 배추를 손으로 어슷어슷 먹기 좋게 찢기',
        coachKo: "코어 블록은 'tear the cabbage leaves'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'tear the cabbage leaves'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 칼로 반듯하게 자르기보다 손과 칼로 어슷하게 쳐내어 식감을 살려 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna tear the cabbage leaves into bite-sized pieces.' Snap!",
        keyVocab: 'tear the cabbage leaves',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'tear the cabbage leaves', pron: '테어 더 캐비지 리브스' },
          { role: 'db', en: 'into bite-sized pieces.', pron: '인투 바이트-사이즈드 피시스' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna tear the cabbage leaves.', fullPron: '암거너 테어 더 캐비지 리브스', ko: 'tear the cabbage leaves 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to tear the cabbage leaves.', fullPron: '유 해브 투 테어 더 캐비지 리브스', ko: 'tear the cabbage leaves 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you tear the cabbage leaves?', fullPron: '캔 유 테어 더 캐비지 리브스?', ko: 'tear the cabbage leaves 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['tear the cabbage leaves', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna tear the cabbage leaves into bite-sized pieces.",
        fullPron: '암거너 + 테어 더 캐비지 리브스 + 인투 바이트-사이즈드 피시스.',
        fullKo: '칼로 반듯하게 자르기보다 손과 칼로 어슷하게 쳐내어 식감을 살려 줍니다.'
      },
      {
        stepTitle: 'SCENE 2 · Quick Salt for 30 Minutes',
        visualEmojis: '🧂 ⏰ 🥬',
        imagePath: '/images/kfood/ep21-thumb.jpg',
        actionNote: '소금을 살짝 뿌려 30분만 숨 죽이기',
        coachKo: "코어 블록은 'salt the cabbage lightly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'salt the cabbage lightly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 아삭함을 유지하기 위해 소금을 살짝만 뿌려 딱 30분 동안만 숨을 죽입니다.",
        missionEn: "Snap Mission! 'You have to salt the cabbage lightly for thirty minutes.' Snap!",
        keyVocab: 'salt the cabbage lightly',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: '유 해브 투' },
          { role: 'core', en: 'salt the cabbage lightly', pron: '솔트 더 캐비지 라이틀리' },
          { role: 'db', en: 'for thirty minutes.', pron: '포 써티 미닛츠' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to salt the cabbage lightly.', fullPron: '유 해브 투 솔트 더 캐비지 라이틀리', ko: 'salt the cabbage lightly 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to salt the cabbage lightly.', fullPron: '유 해브 투 솔트 더 캐비지 라이틀리', ko: 'salt the cabbage lightly 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you salt the cabbage lightly?', fullPron: '캔 유 솔트 더 캐비지 라이틀리?', ko: 'salt the cabbage lightly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "You have to", "Can you"],
          coreCandidates: ['salt the cabbage lightly', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You have to salt the cabbage lightly for thirty minutes.",
        fullPron: '유 해브 투 + 솔트 더 캐비지 라이틀리 + 포 써티 미닛츠.',
        fullKo: '아삭함을 유지하기 위해 소금을 살짝만 뿌려 딱 30분 동안만 숨을 죽입니다.'
      },
      {
        stepTitle: 'SCENE 3 · Rinse & Shake Off Water',
        visualEmojis: '💧 🧺 🤲',
        imagePath: '/images/kfood/ep21-thumb.jpg',
        actionNote: '가볍게 한 번만 헹군 뒤 물기 훌훌 털어내기',
        coachKo: "코어 블록은 'rinse once'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'rinse once'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 배추의 달콤한 맛이 빠져나가지 않게 가볍게 한 번 헹궈 물기를 털어냅니다.",
        missionEn: "Snap Mission! 'We\'re gonna rinse once and shake off the water.' Snap!",
        keyVocab: 'rinse once',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: '웨어 거너' },
          { role: 'core', en: 'rinse once', pron: '린스 원스' },
          { role: 'db', en: 'and shake off the water.', pron: '앤 셰이크 오프 더 워터' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna rinse once.', fullPron: '웨어 거너 린스 원스', ko: 'rinse once 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to rinse once.', fullPron: '유 해브 투 린스 원스', ko: 'rinse once 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you rinse once?', fullPron: '캔 유 린스 원스?', ko: 'rinse once 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "You have to", "Can you"],
          coreCandidates: ['rinse once', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We\'re gonna rinse once and shake off the water.",
        fullPron: '웨어 거너 + 린스 원스 + 앤 셰이크 오프 더 워터.',
        fullKo: '배추의 달콤한 맛이 빠져나가지 않게 가볍게 한 번 헹궈 물기를 털어냅니다.'
      },
      {
        stepTitle: 'SCENE 4 · Mix Red Pepper Flakes Sauce',
        visualEmojis: '🌶️ 🧄 🍶',
        imagePath: '/images/kfood/ep21-thumb.jpg',
        actionNote: '고춧가루, 액젓, 다진 마늘, 매실청 섞기',
        coachKo: "코어 블록은 'mix chili powder'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix chili powder'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 칼칼한 고춧가루에 멸치액젓, 다진 마늘을 듬뿍 넣고 매실청으로 감칠맛을 더합니다.",
        missionEn: "Snap Mission! 'I\'ll mix chili powder with fish sauce and garlic.' Snap!",
        keyVocab: 'mix chili powder',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: '아일' },
          { role: 'core', en: 'mix chili powder', pron: '믹스 칠리 파우더' },
          { role: 'db', en: 'with fish sauce and garlic.', pron: '위드 피시 소스 앤 갈릭' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll mix chili powder.', fullPron: '아일 믹스 칠리 파우더', ko: 'mix chili powder 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix chili powder.', fullPron: '유 해브 투 믹스 칠리 파우더', ko: 'mix chili powder 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you mix chili powder?', fullPron: '캔 유 믹스 칠리 파우더?', ko: 'mix chili powder 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "You have to", "Can you"],
          coreCandidates: ['mix chili powder', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'ll mix chili powder with fish sauce and garlic.",
        fullPron: '아일 + 믹스 칠리 파우더 + 위드 피시 소스 앤 갈릭.',
        fullKo: '칼칼한 고춧가루에 멸치액젓, 다진 마늘을 듬뿍 넣고 매실청으로 감칠맛을 더합니다.'
      },
      {
        stepTitle: 'SCENE 5 · Add Sliced Scallions & Onions',
        visualEmojis: '🧅 🌿 🥣',
        imagePath: '/images/kfood/ep21-thumb.jpg',
        actionNote: '볼에 썬 쪽파와 양파 채 함께 넣기',
        coachKo: "코어 블록은 'add sliced scallions'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add sliced scallions'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 알싸하고 싱그러운 맛을 더하기 위해 썬 쪽파와 양파 채를 볼에 넣습니다.",
        missionEn: "Snap Mission! 'You can add sliced scallions to the mixing bowl.' Snap!",
        keyVocab: 'add sliced scallions',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "You can", pron: '유 캔' },
          { role: 'core', en: 'add sliced scallions', pron: '애드 슬라이스트 스캘리언스' },
          { role: 'db', en: 'to the mixing bowl.', pron: '투 더 믹싱 보울' }
        ],
        combos: [
          { bbEn: 'You can', fullEn: 'You can add sliced scallions.', fullPron: '유 캔 애드 슬라이스트 스캘리언스', ko: 'add sliced scallions 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to add sliced scallions.', fullPron: '유 해브 투 애드 슬라이스트 스캘리언스', ko: 'add sliced scallions 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you add sliced scallions?', fullPron: '캔 유 애드 슬라이스트 스캘리언스?', ko: 'add sliced scallions 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You can", "You have to", "Can you"],
          coreCandidates: ['add sliced scallions', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "You can add sliced scallions to the mixing bowl.",
        fullPron: '유 캔 + 애드 슬라이스트 스캘리언스 + 투 더 믹싱 보울.',
        fullKo: '알싸하고 싱그러운 맛을 더하기 위해 썬 쪽파와 양파 채를 볼에 넣습니다.'
      },
      {
        stepTitle: 'SCENE 6 · Toss Gently with Gloved Hands',
        visualEmojis: '🤲 🥬 🌶️',
        imagePath: '/images/kfood/ep21-thumb.jpg',
        actionNote: '배추 숨이 죽지 않게 손으로 살살 버무리기',
        coachKo: "코어 블록은 'toss everything gently'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toss everything gently'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 배추 풋내가 나지 않도록 위아래로 손을 흔들며 양념을 살살 버무려 줍니다.",
        missionEn: "Snap Mission! 'We have to toss everything gently without bruising the leaves.' Snap!",
        keyVocab: 'toss everything gently',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "We have to", pron: '위 해브 투' },
          { role: 'core', en: 'toss everything gently', pron: '토스 에브리띵 젠틀리' },
          { role: 'db', en: 'without bruising the leaves.', pron: '위드아웃 브루징 더 리브스' }
        ],
        combos: [
          { bbEn: 'We have to', fullEn: 'We have to toss everything gently.', fullPron: '위 해브 투 토스 에브리띵 젠틀리', ko: 'toss everything gently 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to toss everything gently.', fullPron: '유 해브 투 토스 에브리띵 젠틀리', ko: 'toss everything gently 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you toss everything gently?', fullPron: '캔 유 토스 에브리띵 젠틀리?', ko: 'toss everything gently 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We have to", "You have to", "Can you"],
          coreCandidates: ['toss everything gently', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "We have to toss everything gently without bruising the leaves.",
        fullPron: '위 해브 투 + 토스 에브리띵 젠틀리 + 위드아웃 브루징 더 리브스.',
        fullKo: '배추 풋내가 나지 않도록 위아래로 손을 흔들며 양념을 살살 버무려 줍니다.'
      },
      {
        stepTitle: 'SCENE 7 · Finish with Sesame Seeds & Oil',
        visualEmojis: '🫒 ✨ 🌿',
        imagePath: '/images/kfood/ep21-thumb.jpg',
        actionNote: '고소한 통깨와 참기름 똑 떨어뜨려 완성하기',
        coachKo: "코어 블록은 'finish with sesame seeds'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'finish with sesame seeds'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 마지막으로 고소한 통깨를 아낌없이 뿌리고 참기름을 살짝 둘러 줍니다.",
        missionEn: "Snap Mission! 'I\'m gonna finish with sesame seeds and fragrant sesame oil.' Snap!",
        keyVocab: 'finish with sesame seeds',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: '암거너' },
          { role: 'core', en: 'finish with sesame seeds', pron: '피니시 위드 세서미 시즈' },
          { role: 'db', en: 'and fragrant sesame oil.', pron: '앤 프레이그런트 세서미 오일' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna finish with sesame seeds.', fullPron: '암거너 피니시 위드 세서미 시즈', ko: 'finish with sesame seeds 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to finish with sesame seeds.', fullPron: '유 해브 투 피니시 위드 세서미 시즈', ko: 'finish with sesame seeds 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you finish with sesame seeds?', fullPron: '캔 유 피니시 위드 세서미 시즈?', ko: 'finish with sesame seeds 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "Can you"],
          coreCandidates: ['finish with sesame seeds', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "I\'m gonna finish with sesame seeds and fragrant sesame oil.",
        fullPron: '암거너 + 피니시 위드 세서미 시즈 + 앤 프레이그런트 세서미 오일.',
        fullKo: '마지막으로 고소한 통깨를 아낌없이 뿌리고 참기름을 살짝 둘러 줍니다.'
      },
      {
        stepTitle: 'SCENE 8 · Super Fresh & Crunchy Kimchi',
        visualEmojis: '😋 🥗 💥',
        imagePath: '/images/kfood/ep21-thumb.jpg',
        actionNote: '감탄 반응: 담그자마자 따뜻한 칼국수나 흰쌀밥 위에 얹어 먹는 아삭함!',
        coachKo: "코어 블록은 'fresh and crunchy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fresh and crunchy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 갓 버무려 알싸한 마늘 향과 배추 본연의 달큰하고 아삭한 맛이 예술이에요!",
        missionEn: "Snap Mission! 'It\'s so fresh and crunchy with spicy sweet garlic aroma!' Snap!",
        keyVocab: 'fresh and crunchy',
        bgGradient: 'linear-gradient(135deg, #78350f 0%, #b45309 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: '잇츠 쏘' },
          { role: 'core', en: 'fresh and crunchy', pron: '프레시 앤 크런치' },
          { role: 'db', en: 'with spicy sweet garlic aroma!', pron: '위드 스파이시 스위트 갈릭 어로마' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so fresh and crunchy.', fullPron: '잇츠 쏘 프레시 앤 크런치', ko: 'fresh and crunchy 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to fresh and crunchy.', fullPron: '유 해브 투 프레시 앤 크런치', ko: 'fresh and crunchy 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you fresh and crunchy?', fullPron: '캔 유 프레시 앤 크런치?', ko: 'fresh and crunchy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['fresh and crunchy', 'stir-fry the beef', 'pour the broth']
        },
        fullEn: "It\'s so fresh and crunchy with spicy sweet garlic aroma!",
        fullPron: '잇츠 쏘 + 프레시 앤 크런치 + 위드 스파이시 스위트 갈릭 어로마.',
        fullKo: '갓 버무려 알싸한 마늘 향과 배추 본연의 달큰하고 아삭한 맛이 예술이에요!'
      }
    ]
  },
  // ==========================================
  // EP.22. 🍲 Soft Tofu Stew
  // ==========================================
  {
    id: 'sundubu-jjigae',
    epNumber: 'EP.22',
    emoji: '🍲',
    shortTitle: '🍲 Soft Tofu Stew',
    title: 'How to Make Sizzling Korean Soft Tofu Stew (Sundubu Jjigae)',
    ytTitle: 'How to Make Authentic Soft Tofu Stew in Easy English 🍲 | SoundBlock K-Cooking EP.22',
    thumbnailText: 'Sizzling Soft Tofu Stew! [I\'m gonna] + [simmer silken tofu with spicy chili oil]',
    thumbnailImage: '/images/kfood/ep22-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make sizzling Korean Soft Tofu Stew with silken tofu and aromatic chili oil using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for spicy Soft Tofu Stew! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Make Red Chili Oil',
        visualEmojis: '🧄 🌶️ 🍳',
        imagePath: '/images/kfood/ep22-thumb.jpg',
        actionNote: '냄비에 대파와 고춧가루를 기름에 달달 볶아 고추기름 내기',
        coachKo: "코어 블록은 'make fragrant chili oil'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'make fragrant chili oil'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 냄비에 대파와 고춧가루를 기름에 달달 볶아 고추기름 내기",
        missionEn: "Snap Mission! 'I\'m gonna make fragrant chili oil with minced garlic and scallions.' Snap!",
        keyVocab: 'make fragrant chili oil',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'make fragrant chili oil', pron: 'make fragrant chili oil' },
          { role: 'db', en: 'with minced garlic and scallions.', pron: 'with minced garlic and scallions.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna make fragrant chili oil.', fullPron: 'I\'m gonna make fragrant chili oil', ko: 'make fragrant chili oil 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to make fragrant chili oil.', fullPron: 'You have to make fragrant chili oil', ko: 'make fragrant chili oil 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll make fragrant chili oil?', fullPron: 'I\'ll make fragrant chili oil?', ko: 'make fragrant chili oil 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['make fragrant chili oil', 'pour the broth', 'slice the pork']
        },
        fullEn: "I\'m gonna make fragrant chili oil with minced garlic and scallions.",
        fullPron: 'I\'m gonna + make fragrant chili oil + with minced garlic and scallions.',
        fullKo: '냄비에 대파와 고춧가루를 기름에 달달 볶아 고추기름 내기'
      },
      {
        stepTitle: 'SCENE 2 · Stir-Fry Ground Pork & Clams',
        visualEmojis: '🥩 🦪 🥢',
        imagePath: '/images/kfood/ep22-thumb.jpg',
        actionNote: '다진 돼지고기와 싱싱한 바지락 조개를 볶아 감칠맛 더하기',
        coachKo: "코어 블록은 'stir-fry ground pork'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir-fry ground pork'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 다진 돼지고기와 싱싱한 바지락 조개를 볶아 감칠맛 더하기",
        missionEn: "Snap Mission! 'You have to stir-fry ground pork and fresh Manila clams.' Snap!",
        keyVocab: 'stir-fry ground pork',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'stir-fry ground pork', pron: 'stir-fry ground pork' },
          { role: 'db', en: 'and fresh Manila clams.', pron: 'and fresh Manila clams.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to stir-fry ground pork.', fullPron: 'You have to stir-fry ground pork', ko: 'stir-fry ground pork 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna stir-fry ground pork.', fullPron: 'I\'m gonna stir-fry ground pork', ko: 'stir-fry ground pork 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna stir-fry ground pork?', fullPron: 'We\'re gonna stir-fry ground pork?', ko: 'stir-fry ground pork 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['stir-fry ground pork', 'cut the tofu', 'boil the soup']
        },
        fullEn: "You have to stir-fry ground pork and fresh Manila clams.",
        fullPron: 'You have to + stir-fry ground pork + and fresh Manila clams.',
        fullKo: '다진 돼지고기와 싱싱한 바지락 조개를 볶아 감칠맛 더하기'
      },
      {
        stepTitle: 'SCENE 3 · Pour Anchovy Kelp Broth',
        visualEmojis: '🥣 💧 🌊',
        imagePath: '/images/kfood/ep22-thumb.jpg',
        actionNote: '시원하고 깊은 멸치 다시마 육수를 자작하게 붓기',
        coachKo: "코어 블록은 'pour anchovy broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour anchovy broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 시원하고 깊은 멸치 다시마 육수를 자작하게 붓기",
        missionEn: "Snap Mission! 'We\'re gonna pour anchovy broth right into the sizzling pot.' Snap!",
        keyVocab: 'pour anchovy broth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'pour anchovy broth', pron: 'pour anchovy broth' },
          { role: 'db', en: 'right into the sizzling pot.', pron: 'right into the sizzling pot.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna pour anchovy broth.', fullPron: 'We\'re gonna pour anchovy broth', ko: 'pour anchovy broth 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour anchovy broth.', fullPron: 'I\'m gonna pour anchovy broth', ko: 'pour anchovy broth 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour anchovy broth?', fullPron: 'You have to pour anchovy broth?', ko: 'pour anchovy broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['pour anchovy broth', 'stir-fry the meat', 'crack an egg']
        },
        fullEn: "We\'re gonna pour anchovy broth right into the sizzling pot.",
        fullPron: 'We\'re gonna + pour anchovy broth + right into the sizzling pot.',
        fullKo: '시원하고 깊은 멸치 다시마 육수를 자작하게 붓기'
      },
      {
        stepTitle: 'SCENE 4 · Spoon in Silken Tofu',
        visualEmojis: '🥄 🤍 🍲',
        imagePath: '/images/kfood/ep22-thumb.jpg',
        actionNote: '부드럽고 몽글몽글한 순두부를 큼직하게 뚝뚝 떼어 넣기',
        coachKo: "코어 블록은 'spoon in silken tofu'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'spoon in silken tofu'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 부드럽고 몽글몽글한 순두부를 큼직하게 뚝뚝 떼어 넣기",
        missionEn: "Snap Mission! 'I\'ll spoon in silken tofu in large generous chunks.' Snap!",
        keyVocab: 'spoon in silken tofu',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'spoon in silken tofu', pron: 'spoon in silken tofu' },
          { role: 'db', en: 'in large generous chunks.', pron: 'in large generous chunks.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll spoon in silken tofu.', fullPron: 'I\'ll spoon in silken tofu', ko: 'spoon in silken tofu 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna spoon in silken tofu.', fullPron: 'I\'m gonna spoon in silken tofu', ko: 'spoon in silken tofu 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to spoon in silken tofu?', fullPron: 'You have to spoon in silken tofu?', ko: 'spoon in silken tofu 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['spoon in silken tofu', 'season with salt', 'chop the scallions']
        },
        fullEn: "I\'ll spoon in silken tofu in large generous chunks.",
        fullPron: 'I\'ll + spoon in silken tofu + in large generous chunks.',
        fullKo: '부드럽고 몽글몽글한 순두부를 큼직하게 뚝뚝 떼어 넣기'
      },
      {
        stepTitle: 'SCENE 5 · Season with Fish Sauce',
        visualEmojis: '🧂 🫙 ✨',
        imagePath: '/images/kfood/ep22-thumb.jpg',
        actionNote: '국간장과 액젓으로 깊고 감칠맛 나는 간 맞추기',
        coachKo: "코어 블록은 'season with fish sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'season with fish sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 국간장과 액젓으로 깊고 감칠맛 나는 간 맞추기",
        missionEn: "Snap Mission! 'You have to season with fish sauce and a pinch of salt.' Snap!",
        keyVocab: 'season with fish sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'season with fish sauce', pron: 'season with fish sauce' },
          { role: 'db', en: 'and a pinch of salt.', pron: 'and a pinch of salt.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to season with fish sauce.', fullPron: 'You have to season with fish sauce', ko: 'season with fish sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna season with fish sauce.', fullPron: 'I\'m gonna season with fish sauce', ko: 'season with fish sauce 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll season with fish sauce?', fullPron: 'I\'ll season with fish sauce?', ko: 'season with fish sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['season with fish sauce', 'make chili oil', 'pour cold water']
        },
        fullEn: "You have to season with fish sauce and a pinch of salt.",
        fullPron: 'You have to + season with fish sauce + and a pinch of salt.',
        fullKo: '국간장과 액젓으로 깊고 감칠맛 나는 간 맞추기'
      },
      {
        stepTitle: 'SCENE 6 · Boil on Rolling Heat',
        visualEmojis: '🔥 🍲 💨',
        imagePath: '/images/kfood/ep22-thumb.jpg',
        actionNote: '보글보글 거품이 올라올 때까지 센 불에서 화끈하게 끓이기',
        coachKo: "코어 블록은 'boil on high heat'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'boil on high heat'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 보글보글 거품이 올라올 때까지 센 불에서 화끈하게 끓이기",
        missionEn: "Snap Mission! 'We\'re gonna boil on high heat until it bubbles vigorously.' Snap!",
        keyVocab: 'boil on high heat',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'boil on high heat', pron: 'boil on high heat' },
          { role: 'db', en: 'until it bubbles vigorously.', pron: 'until it bubbles vigorously.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna boil on high heat.', fullPron: 'We\'re gonna boil on high heat', ko: 'boil on high heat 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna boil on high heat.', fullPron: 'I\'m gonna boil on high heat', ko: 'boil on high heat 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to boil on high heat?', fullPron: 'You have to boil on high heat?', ko: 'boil on high heat 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['boil on high heat', 'simmer gently', 'stir-fry pork']
        },
        fullEn: "We\'re gonna boil on high heat until it bubbles vigorously.",
        fullPron: 'We\'re gonna + boil on high heat + until it bubbles vigorously.',
        fullKo: '보글보글 거품이 올라올 때까지 센 불에서 화끈하게 끓이기'
      },
      {
        stepTitle: 'SCENE 7 · Crack Fresh Raw Egg on Top',
        visualEmojis: '🥚 💥 🌟',
        imagePath: '/images/kfood/ep22-thumb.jpg',
        actionNote: '뚝배기 한가운데에 신선한 생달걀을 탁 깨 넣기',
        coachKo: "코어 블록은 'crack a fresh raw egg'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'crack a fresh raw egg'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뚝배기 한가운데에 신선한 생달걀을 탁 깨 넣기",
        missionEn: "Snap Mission! 'I\'m gonna crack a fresh raw egg right in the bubbling center.' Snap!",
        keyVocab: 'crack a fresh raw egg',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'crack a fresh raw egg', pron: 'crack a fresh raw egg' },
          { role: 'db', en: 'right in the bubbling center.', pron: 'right in the bubbling center.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna crack a fresh raw egg.', fullPron: 'I\'m gonna crack a fresh raw egg', ko: 'crack a fresh raw egg 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to crack a fresh raw egg.', fullPron: 'You have to crack a fresh raw egg', ko: 'crack a fresh raw egg 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll crack a fresh raw egg?', fullPron: 'I\'ll crack a fresh raw egg?', ko: 'crack a fresh raw egg 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['crack a fresh raw egg', 'spoon in tofu', 'pour the broth']
        },
        fullEn: "I\'m gonna crack a fresh raw egg right in the bubbling center.",
        fullPron: 'I\'m gonna + crack a fresh raw egg + right in the bubbling center.',
        fullKo: '뚝배기 한가운데에 신선한 생달걀을 탁 깨 넣기'
      },
      {
        stepTitle: 'SCENE 8 · Silky Spicy & Comforting',
        visualEmojis: '😋 🍲 🥄',
        imagePath: '/images/kfood/ep22-thumb.jpg',
        actionNote: '얼큰하고 칼칼한 국물과 입안에서 사르르 녹는 순두부 맛보기',
        coachKo: "코어 블록은 'silky spicy and comforting'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'silky spicy and comforting'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 얼큰하고 칼칼한 국물과 입안에서 사르르 녹는 순두부 맛보기",
        missionEn: "Snap Mission! 'It\'s so silky spicy and comforting with that velvety rich broth!' Snap!",
        keyVocab: 'silky spicy and comforting',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'silky spicy and comforting', pron: 'silky spicy and comforting' },
          { role: 'db', en: 'with that velvety rich broth!', pron: 'with that velvety rich broth!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so silky spicy and comforting.', fullPron: 'It\'s so silky spicy and comforting', ko: 'silky spicy and comforting 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to silky spicy and comforting.', fullPron: 'You have to silky spicy and comforting', ko: 'silky spicy and comforting 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you silky spicy and comforting?', fullPron: 'Can you silky spicy and comforting?', ko: 'silky spicy and comforting 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['silky spicy and comforting', 'boil on heat', 'make chili oil']
        },
        fullEn: "It\'s so silky spicy and comforting with that velvety rich broth!",
        fullPron: 'It\'s so + silky spicy and comforting + with that velvety rich broth!',
        fullKo: '얼큰하고 칼칼한 국물과 입안에서 사르르 녹는 순두부 맛보기'
      }
    ]
  },
  // ==========================================
  // EP.23. 🥩 Sizzling Pork Belly BBQ
  // ==========================================
  {
    id: 'samgyeopsal-bbq',
    epNumber: 'EP.23',
    emoji: '🥩',
    shortTitle: '🥩 Sizzling Pork Belly BBQ',
    title: 'How to Grill Korean Pork Belly BBQ (Samgyeopsal & Ssam)',
    ytTitle: 'How to Grill Authentic Korean Pork Belly BBQ in Easy English 🥩 | SoundBlock K-Cooking EP.23',
    thumbnailText: 'Crispy Samgyeopsal BBQ! [We\'re gonna] + [grill thick pork belly with sliced garlic]',
    thumbnailImage: '/images/kfood/ep23-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s grill sizzling Korean pork belly BBQ with crisp lettuce wraps and savory ssamjang, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for iconic Samgyeopsal BBQ! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Heat the Heavy Iron Grill Pan',
        visualEmojis: '🍳 🔥 💨',
        imagePath: '/images/kfood/ep23-thumb.jpg',
        actionNote: '무쇠 불판을 연기가 살짝 날 때까지 뜨겁게 달구기',
        coachKo: "코어 블록은 'heat the heavy grill pan'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'heat the heavy grill pan'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 무쇠 불판을 연기가 살짝 날 때까지 뜨겁게 달구기",
        missionEn: "Snap Mission! 'You have to heat the heavy grill pan until it\'s smoking hot.' Snap!",
        keyVocab: 'heat the heavy grill pan',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'heat the heavy grill pan', pron: 'heat the heavy grill pan' },
          { role: 'db', en: 'until it\'s smoking hot.', pron: 'until it\'s smoking hot.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to heat the heavy grill pan.', fullPron: 'You have to heat the heavy grill pan', ko: 'heat the heavy grill pan 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna heat the heavy grill pan.', fullPron: 'I\'m gonna heat the heavy grill pan', ko: 'heat the heavy grill pan 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna heat the heavy grill pan?', fullPron: 'We\'re gonna heat the heavy grill pan?', ko: 'heat the heavy grill pan 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['heat the heavy grill pan', 'cut the meat', 'wrap in lettuce']
        },
        fullEn: "You have to heat the heavy grill pan until it\'s smoking hot.",
        fullPron: 'You have to + heat the heavy grill pan + until it\'s smoking hot.',
        fullKo: '무쇠 불판을 연기가 살짝 날 때까지 뜨겁게 달구기'
      },
      {
        stepTitle: 'SCENE 2 · Lay Down Thick Pork Belly Strips',
        visualEmojis: '🥩 🥓 💥',
        imagePath: '/images/kfood/ep23-thumb.jpg',
        actionNote: '두툼한 삼겹살을 불판 위에 촤아악 소리 나게 올리기',
        coachKo: "코어 블록은 'lay down thick pork belly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'lay down thick pork belly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 두툼한 삼겹살을 불판 위에 촤아악 소리 나게 올리기",
        missionEn: "Snap Mission! 'We\'re gonna lay down thick pork belly and hear that sizzling sound.' Snap!",
        keyVocab: 'lay down thick pork belly',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'lay down thick pork belly', pron: 'lay down thick pork belly' },
          { role: 'db', en: 'and hear that sizzling sound.', pron: 'and hear that sizzling sound.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna lay down thick pork belly.', fullPron: 'We\'re gonna lay down thick pork belly', ko: 'lay down thick pork belly 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna lay down thick pork belly.', fullPron: 'I\'m gonna lay down thick pork belly', ko: 'lay down thick pork belly 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to lay down thick pork belly?', fullPron: 'You have to lay down thick pork belly?', ko: 'lay down thick pork belly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['lay down thick pork belly', 'dip in ssamjang', 'chop green onion']
        },
        fullEn: "We\'re gonna lay down thick pork belly and hear that sizzling sound.",
        fullPron: 'We\'re gonna + lay down thick pork belly + and hear that sizzling sound.',
        fullKo: '두툼한 삼겹살을 불판 위에 촤아악 소리 나게 올리기'
      },
      {
        stepTitle: 'SCENE 3 · Sear Until Golden & Crispy',
        visualEmojis: '⏳ 🔥 ✨',
        imagePath: '/images/kfood/ep23-thumb.jpg',
        actionNote: '육즙을 가두며 겉면이 바삭하고 노릇해질 때까지 굽기',
        coachKo: "코어 블록은 'sear until golden brown'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sear until golden brown'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 육즙을 가두며 겉면이 바삭하고 노릇해질 때까지 굽기",
        missionEn: "Snap Mission! 'I\'m gonna sear until golden brown on both crispy sides.' Snap!",
        keyVocab: 'sear until golden brown',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'sear until golden brown', pron: 'sear until golden brown' },
          { role: 'db', en: 'on both crispy sides.', pron: 'on both crispy sides.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna sear until golden brown.', fullPron: 'I\'m gonna sear until golden brown', ko: 'sear until golden brown 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to sear until golden brown.', fullPron: 'You have to sear until golden brown', ko: 'sear until golden brown 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll sear until golden brown?', fullPron: 'I\'ll sear until golden brown?', ko: 'sear until golden brown 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['sear until golden brown', 'pour the sauce', 'spoon the rice']
        },
        fullEn: "I\'m gonna sear until golden brown on both crispy sides.",
        fullPron: 'I\'m gonna + sear until golden brown + on both crispy sides.',
        fullKo: '육즙을 가두며 겉면이 바삭하고 노릇해질 때까지 굽기'
      },
      {
        stepTitle: 'SCENE 4 · Grill Whole Garlic & Aged Kimchi',
        visualEmojis: '🧄 🥬 🥓',
        imagePath: '/images/kfood/ep23-thumb.jpg',
        actionNote: '돼지기름에 통마늘과 잘 익은 신김치를 함께 굽기',
        coachKo: "코어 블록은 'grill sliced garlic and kimchi'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'grill sliced garlic and kimchi'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 돼지기름에 통마늘과 잘 익은 신김치를 함께 굽기",
        missionEn: "Snap Mission! 'You have to grill sliced garlic and kimchi in that savory pork drippings.' Snap!",
        keyVocab: 'grill sliced garlic and kimchi',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'grill sliced garlic and kimchi', pron: 'grill sliced garlic and kimchi' },
          { role: 'db', en: 'in that savory pork drippings.', pron: 'in that savory pork drippings.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to grill sliced garlic and kimchi.', fullPron: 'You have to grill sliced garlic and kimchi', ko: 'grill sliced garlic and kimchi 할 거예요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna grill sliced garlic and kimchi.', fullPron: 'We\'re gonna grill sliced garlic and kimchi', ko: 'grill sliced garlic and kimchi 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna grill sliced garlic and kimchi?', fullPron: 'I\'m gonna grill sliced garlic and kimchi?', ko: 'grill sliced garlic and kimchi 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "We\'re gonna", "I\'m gonna"],
          coreCandidates: ['grill sliced garlic and kimchi', 'slice the meat', 'boil the stew']
        },
        fullEn: "You have to grill sliced garlic and kimchi in that savory pork drippings.",
        fullPron: 'You have to + grill sliced garlic and kimchi + in that savory pork drippings.',
        fullKo: '돼지기름에 통마늘과 잘 익은 신김치를 함께 굽기'
      },
      {
        stepTitle: 'SCENE 5 · Snip Meat into Bite-Sized Pieces',
        visualEmojis: '✂️ 🥩 🥢',
        imagePath: '/images/kfood/ep23-thumb.jpg',
        actionNote: '가위로 노릇한 삼겹살을 한 입 크기로 먹기 좋게 자르기',
        coachKo: "코어 블록은 'snip into bite-sized pieces'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'snip into bite-sized pieces'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 가위로 노릇한 삼겹살을 한 입 크기로 먹기 좋게 자르기",
        missionEn: "Snap Mission! 'I\'ll snip into bite-sized pieces with clean kitchen shears.' Snap!",
        keyVocab: 'snip into bite-sized pieces',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'snip into bite-sized pieces', pron: 'snip into bite-sized pieces' },
          { role: 'db', en: 'with clean kitchen shears.', pron: 'with clean kitchen shears.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll snip into bite-sized pieces.', fullPron: 'I\'ll snip into bite-sized pieces', ko: 'snip into bite-sized pieces 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna snip into bite-sized pieces.', fullPron: 'I\'m gonna snip into bite-sized pieces', ko: 'snip into bite-sized pieces 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to snip into bite-sized pieces?', fullPron: 'You have to snip into bite-sized pieces?', ko: 'snip into bite-sized pieces 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['snip into bite-sized pieces', 'wrap the lettuce', 'stir-fry kimchi']
        },
        fullEn: "I\'ll snip into bite-sized pieces with clean kitchen shears.",
        fullPron: 'I\'ll + snip into bite-sized pieces + with clean kitchen shears.',
        fullKo: '가위로 노릇한 삼겹살을 한 입 크기로 먹기 좋게 자르기'
      },
      {
        stepTitle: 'SCENE 6 · Prepare Fresh Crisp Lettuce Leaves',
        visualEmojis: '🥬 🌿 💧',
        imagePath: '/images/kfood/ep23-thumb.jpg',
        actionNote: '싱싱한 상추와 깻잎을 깨끗이 씻어 손바닥 위에 펼치기',
        coachKo: "코어 블록은 'place crisp lettuce in hand'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'place crisp lettuce in hand'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 싱싱한 상추와 깻잎을 깨끗이 씻어 손바닥 위에 펼치기",
        missionEn: "Snap Mission! 'You have to place crisp lettuce in hand with a fragrant perilla leaf.' Snap!",
        keyVocab: 'place crisp lettuce in hand',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'place crisp lettuce in hand', pron: 'place crisp lettuce in hand' },
          { role: 'db', en: 'with a fragrant perilla leaf.', pron: 'with a fragrant perilla leaf.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to place crisp lettuce in hand.', fullPron: 'You have to place crisp lettuce in hand', ko: 'place crisp lettuce in hand 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna place crisp lettuce in hand.', fullPron: 'I\'m gonna place crisp lettuce in hand', ko: 'place crisp lettuce in hand 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll place crisp lettuce in hand?', fullPron: 'I\'ll place crisp lettuce in hand?', ko: 'place crisp lettuce in hand 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['place crisp lettuce in hand', 'sear the pork', 'grill the garlic']
        },
        fullEn: "You have to place crisp lettuce in hand with a fragrant perilla leaf.",
        fullPron: 'You have to + place crisp lettuce in hand + with a fragrant perilla leaf.',
        fullKo: '싱싱한 상추와 깻잎을 깨끗이 씻어 손바닥 위에 펼치기'
      },
      {
        stepTitle: 'SCENE 7 · Dab Savory Ssamjang & Grilled Garlic',
        visualEmojis: '🥢 🫙 🧄',
        imagePath: '/images/kfood/ep23-thumb.jpg',
        actionNote: '고기 위에 쌈장 한 점과 노릇하게 구운 마늘 얹기',
        coachKo: "코어 블록은 'dab savory soybean paste'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'dab savory soybean paste'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고기 위에 쌈장 한 점과 노릇하게 구운 마늘 얹기",
        missionEn: "Snap Mission! 'I\'m gonna dab savory soybean paste and roasted garlic on top.' Snap!",
        keyVocab: 'dab savory soybean paste',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'dab savory soybean paste', pron: 'dab savory soybean paste' },
          { role: 'db', en: 'and roasted garlic on top.', pron: 'and roasted garlic on top.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna dab savory soybean paste.', fullPron: 'I\'m gonna dab savory soybean paste', ko: 'dab savory soybean paste 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to dab savory soybean paste.', fullPron: 'You have to dab savory soybean paste', ko: 'dab savory soybean paste 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna dab savory soybean paste?', fullPron: 'We\'re gonna dab savory soybean paste?', ko: 'dab savory soybean paste 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['dab savory soybean paste', 'cut the pork', 'wash the leaves']
        },
        fullEn: "I\'m gonna dab savory soybean paste and roasted garlic on top.",
        fullPron: 'I\'m gonna + dab savory soybean paste + and roasted garlic on top.',
        fullKo: '고기 위에 쌈장 한 점과 노릇하게 구운 마늘 얹기'
      },
      {
        stepTitle: 'SCENE 8 · Wrap Tightly & Take Huge Bite',
        visualEmojis: '😋 🥬 💥',
        imagePath: '/images/kfood/ep23-thumb.jpg',
        actionNote: '야무지게 쌈을 싸서 한 입에 가득 넣고 육즙 즐기기',
        coachKo: "코어 블록은 'wrap tightly into one big bite'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'wrap tightly into one big bite'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 야무지게 쌈을 싸서 한 입에 가득 넣고 육즙 즐기기",
        missionEn: "Snap Mission! 'Do you wanna wrap tightly into one big bite and enjoy the juicy burst?' Snap!",
        keyVocab: 'wrap tightly into one big bite',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "Do you wanna", pron: 'Do you wanna' },
          { role: 'core', en: 'wrap tightly into one big bite', pron: 'wrap tightly into one big bite' },
          { role: 'db', en: 'and enjoy the juicy burst?', pron: 'and enjoy the juicy burst?' }
        ],
        combos: [
          { bbEn: 'Do you wanna', fullEn: 'Do you wanna wrap tightly into one big bite.', fullPron: 'Do you wanna wrap tightly into one big bite', ko: 'wrap tightly into one big bite 할 거예요.' },
          { bbEn: 'I wanna', fullEn: 'I wanna wrap tightly into one big bite.', fullPron: 'I wanna wrap tightly into one big bite', ko: 'wrap tightly into one big bite 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll wrap tightly into one big bite?', fullPron: 'I\'ll wrap tightly into one big bite?', ko: 'wrap tightly into one big bite 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["Do you wanna", "I wanna", "I\'ll"],
          coreCandidates: ['wrap tightly into one big bite', 'sear until brown', 'snip with shears']
        },
        fullEn: "Do you wanna wrap tightly into one big bite and enjoy the juicy burst?",
        fullPron: 'Do you wanna + wrap tightly into one big bite + and enjoy the juicy burst?',
        fullKo: '야무지게 쌈을 싸서 한 입에 가득 넣고 육즙 즐기기'
      }
    ]
  },
  // ==========================================
  // EP.24. 🍖 Beef Short Rib Soup
  // ==========================================
  {
    id: 'galbitang',
    epNumber: 'EP.24',
    emoji: '🍖',
    shortTitle: '🍖 Beef Short Rib Soup',
    title: 'How to Make Hearty Korean Beef Short Rib Soup (Galbitang)',
    ytTitle: 'How to Make Hearty Korean Beef Short Rib Soup in Easy English 🍖 | SoundBlock K-Cooking EP.24',
    thumbnailText: 'Clear Hearty Galbitang! [I\'m gonna] + [simmer tender beef ribs with sweet radish]',
    thumbnailImage: '/images/kfood/ep24-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s simmer clear and nourishing Korean Beef Short Rib Soup with glass noodles and sweet radish, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for comforting Galbitang! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Soak Short Ribs in Cold Water',
        visualEmojis: '🍖 💧 ⏳',
        imagePath: '/images/kfood/ep24-thumb.jpg',
        actionNote: '소갈비를 찬물에 2시간 동안 담가 핏물을 깨끗이 빼기',
        coachKo: "코어 블록은 'soak short ribs in cold water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'soak short ribs in cold water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 소갈비를 찬물에 2시간 동안 담가 핏물을 깨끗이 빼기",
        missionEn: "Snap Mission! 'You have to soak short ribs in cold water to remove excess blood.' Snap!",
        keyVocab: 'soak short ribs in cold water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'soak short ribs in cold water', pron: 'soak short ribs in cold water' },
          { role: 'db', en: 'to remove excess blood.', pron: 'to remove excess blood.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to soak short ribs in cold water.', fullPron: 'You have to soak short ribs in cold water', ko: 'soak short ribs in cold water 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna soak short ribs in cold water.', fullPron: 'I\'m gonna soak short ribs in cold water', ko: 'soak short ribs in cold water 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll soak short ribs in cold water?', fullPron: 'I\'ll soak short ribs in cold water?', ko: 'soak short ribs in cold water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['soak short ribs in cold water', 'parboil the ribs', 'cut the radish']
        },
        fullEn: "You have to soak short ribs in cold water to remove excess blood.",
        fullPron: 'You have to + soak short ribs in cold water + to remove excess blood.',
        fullKo: '소갈비를 찬물에 2시간 동안 담가 핏물을 깨끗이 빼기'
      },
      {
        stepTitle: 'SCENE 2 · Parboil Ribs with Rice Wine',
        visualEmojis: '🔥 🍲 🍶',
        imagePath: '/images/kfood/ep24-thumb.jpg',
        actionNote: '끓는 물에 청주를 넣고 갈비를 5분간 데쳐 불순물 제거하기',
        coachKo: "코어 블록은 'parboil the beef ribs'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'parboil the beef ribs'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 끓는 물에 청주를 넣고 갈비를 5분간 데쳐 불순물 제거하기",
        missionEn: "Snap Mission! 'We\'re gonna parboil the beef ribs for five minutes with wine.' Snap!",
        keyVocab: 'parboil the beef ribs',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'parboil the beef ribs', pron: 'parboil the beef ribs' },
          { role: 'db', en: 'for five minutes with wine.', pron: 'for five minutes with wine.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna parboil the beef ribs.', fullPron: 'We\'re gonna parboil the beef ribs', ko: 'parboil the beef ribs 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna parboil the beef ribs.', fullPron: 'I\'m gonna parboil the beef ribs', ko: 'parboil the beef ribs 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to parboil the beef ribs?', fullPron: 'You have to parboil the beef ribs?', ko: 'parboil the beef ribs 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['parboil the beef ribs', 'soak the glass noodles', 'skim the fat']
        },
        fullEn: "We\'re gonna parboil the beef ribs for five minutes with wine.",
        fullPron: 'We\'re gonna + parboil the beef ribs + for five minutes with wine.',
        fullKo: '끓는 물에 청주를 넣고 갈비를 5분간 데쳐 불순물 제거하기'
      },
      {
        stepTitle: 'SCENE 3 · Rinse Under Cold Running Water',
        visualEmojis: '💧 🧼 🍖',
        imagePath: '/images/kfood/ep24-thumb.jpg',
        actionNote: '데친 갈비 겉면의 응고된 찌꺼기를 찬물에 깨끗이 씻기',
        coachKo: "코어 블록은 'rinse under cold running water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'rinse under cold running water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 데친 갈비 겉면의 응고된 찌꺼기를 찬물에 깨끗이 씻기",
        missionEn: "Snap Mission! 'You have to rinse under cold running water to keep the broth crystal clear.' Snap!",
        keyVocab: 'rinse under cold running water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'rinse under cold running water', pron: 'rinse under cold running water' },
          { role: 'db', en: 'to keep the broth crystal clear.', pron: 'to keep the broth crystal clear.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to rinse under cold running water.', fullPron: 'You have to rinse under cold running water', ko: 'rinse under cold running water 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll rinse under cold running water.', fullPron: 'I\'ll rinse under cold running water', ko: 'rinse under cold running water 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna rinse under cold running water?', fullPron: 'I\'m gonna rinse under cold running water?', ko: 'rinse under cold running water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['rinse under cold running water', 'simmer for hours', 'season with sauce']
        },
        fullEn: "You have to rinse under cold running water to keep the broth crystal clear.",
        fullPron: 'You have to + rinse under cold running water + to keep the broth crystal clear.',
        fullKo: '데친 갈비 겉면의 응고된 찌꺼기를 찬물에 깨끗이 씻기'
      },
      {
        stepTitle: 'SCENE 4 · Simmer with Sweet Korean Radish',
        visualEmojis: '🧅 🧄 🍲',
        imagePath: '/images/kfood/ep24-thumb.jpg',
        actionNote: '무, 대파, 통마늘과 함께 약불에서 1시간 반 동안 푹 고기',
        coachKo: "코어 블록은 'simmer with sweet Korean radish'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'simmer with sweet Korean radish'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 무, 대파, 통마늘과 함께 약불에서 1시간 반 동안 푹 고기",
        missionEn: "Snap Mission! 'I\'m gonna simmer with sweet Korean radish for one and a half hours.' Snap!",
        keyVocab: 'simmer with sweet Korean radish',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'simmer with sweet Korean radish', pron: 'simmer with sweet Korean radish' },
          { role: 'db', en: 'for one and a half hours.', pron: 'for one and a half hours.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna simmer with sweet Korean radish.', fullPron: 'I\'m gonna simmer with sweet Korean radish', ko: 'simmer with sweet Korean radish 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to simmer with sweet Korean radish.', fullPron: 'You have to simmer with sweet Korean radish', ko: 'simmer with sweet Korean radish 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna simmer with sweet Korean radish?', fullPron: 'We\'re gonna simmer with sweet Korean radish?', ko: 'simmer with sweet Korean radish 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['simmer with sweet Korean radish', 'parboil the beef', 'soak in water']
        },
        fullEn: "I\'m gonna simmer with sweet Korean radish for one and a half hours.",
        fullPron: 'I\'m gonna + simmer with sweet Korean radish + for one and a half hours.',
        fullKo: '무, 대파, 통마늘과 함께 약불에서 1시간 반 동안 푹 고기'
      },
      {
        stepTitle: 'SCENE 5 · Skim Off Floating Oil & Foam',
        visualEmojis: '🥄 🫙 ✨',
        imagePath: '/images/kfood/ep24-thumb.jpg',
        actionNote: '국물 표면에 떠오르는 기름기와 거품을 정성껏 걷어내기',
        coachKo: "코어 블록은 'skim off floating oil and foam'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'skim off floating oil and foam'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 국물 표면에 떠오르는 기름기와 거품을 정성껏 걷어내기",
        missionEn: "Snap Mission! 'You have to skim off floating oil and foam with a fine mesh strainer.' Snap!",
        keyVocab: 'skim off floating oil and foam',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'skim off floating oil and foam', pron: 'skim off floating oil and foam' },
          { role: 'db', en: 'with a fine mesh strainer.', pron: 'with a fine mesh strainer.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to skim off floating oil and foam.', fullPron: 'You have to skim off floating oil and foam', ko: 'skim off floating oil and foam 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll skim off floating oil and foam.', fullPron: 'I\'ll skim off floating oil and foam', ko: 'skim off floating oil and foam 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna skim off floating oil and foam?', fullPron: 'I\'m gonna skim off floating oil and foam?', ko: 'skim off floating oil and foam 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['skim off floating oil and foam', 'add glass noodles', 'slice the scallions']
        },
        fullEn: "You have to skim off floating oil and foam with a fine mesh strainer.",
        fullPron: 'You have to + skim off floating oil and foam + with a fine mesh strainer.',
        fullKo: '국물 표면에 떠오르는 기름기와 거품을 정성껏 걷어내기'
      },
      {
        stepTitle: 'SCENE 6 · Add Chewy Soaked Glass Noodles',
        visualEmojis: '🍜 🥢 🍲',
        imagePath: '/images/kfood/ep24-thumb.jpg',
        actionNote: '물에 불린 쫄깃한 당면을 뚝배기 밑바닥에 소복이 깔기',
        coachKo: "코어 블록은 'add chewy soaked glass noodles'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add chewy soaked glass noodles'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 물에 불린 쫄깃한 당면을 뚝배기 밑바닥에 소복이 깔기",
        missionEn: "Snap Mission! 'We\'re gonna add chewy soaked glass noodles right into the serving bowl.' Snap!",
        keyVocab: 'add chewy soaked glass noodles',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'add chewy soaked glass noodles', pron: 'add chewy soaked glass noodles' },
          { role: 'db', en: 'right into the serving bowl.', pron: 'right into the serving bowl.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna add chewy soaked glass noodles.', fullPron: 'We\'re gonna add chewy soaked glass noodles', ko: 'add chewy soaked glass noodles 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna add chewy soaked glass noodles.', fullPron: 'I\'m gonna add chewy soaked glass noodles', ko: 'add chewy soaked glass noodles 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to add chewy soaked glass noodles?', fullPron: 'You have to add chewy soaked glass noodles?', ko: 'add chewy soaked glass noodles 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['add chewy soaked glass noodles', 'simmer the ribs', 'rinse under water']
        },
        fullEn: "We\'re gonna add chewy soaked glass noodles right into the serving bowl.",
        fullPron: 'We\'re gonna + add chewy soaked glass noodles + right into the serving bowl.',
        fullKo: '물에 불린 쫄깃한 당면을 뚝배기 밑바닥에 소복이 깔기'
      },
      {
        stepTitle: 'SCENE 7 · Garnish with Green Onions & Pepper',
        visualEmojis: '🌿 🧂 ✨',
        imagePath: '/images/kfood/ep24-thumb.jpg',
        actionNote: '송송 썬 대파와 후춧가루를 톡톡 뿌려 깔끔함 더하기',
        coachKo: "코어 블록은 'garnish with fresh scallions'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'garnish with fresh scallions'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 송송 썬 대파와 후춧가루를 톡톡 뿌려 깔끔함 더하기",
        missionEn: "Snap Mission! 'I\'ll garnish with fresh scallions and freshly cracked black pepper.' Snap!",
        keyVocab: 'garnish with fresh scallions',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'garnish with fresh scallions', pron: 'garnish with fresh scallions' },
          { role: 'db', en: 'and freshly cracked black pepper.', pron: 'and freshly cracked black pepper.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll garnish with fresh scallions.', fullPron: 'I\'ll garnish with fresh scallions', ko: 'garnish with fresh scallions 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna garnish with fresh scallions.', fullPron: 'I\'m gonna garnish with fresh scallions', ko: 'garnish with fresh scallions 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to garnish with fresh scallions?', fullPron: 'You have to garnish with fresh scallions?', ko: 'garnish with fresh scallions 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['garnish with fresh scallions', 'skim off foam', 'parboil ribs']
        },
        fullEn: "I\'ll garnish with fresh scallions and freshly cracked black pepper.",
        fullPron: 'I\'ll + garnish with fresh scallions + and freshly cracked black pepper.',
        fullKo: '송송 썬 대파와 후춧가루를 톡톡 뿌려 깔끔함 더하기'
      },
      {
        stepTitle: 'SCENE 8 · Fall-Off-The-Bone Tender',
        visualEmojis: '😋 🍖 🥣',
        imagePath: '/images/kfood/ep24-thumb.jpg',
        actionNote: '뼈에서 고기가 스르륵 떨어지는 야들야들한 갈비 맛보기',
        coachKo: "코어 블록은 'fall-off-the-bone tender'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fall-off-the-bone tender'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뼈에서 고기가 스르륵 떨어지는 야들야들한 갈비 맛보기",
        missionEn: "Snap Mission! 'It\'s so fall-off-the-bone tender with deeply nourishing broth!' Snap!",
        keyVocab: 'fall-off-the-bone tender',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'fall-off-the-bone tender', pron: 'fall-off-the-bone tender' },
          { role: 'db', en: 'with deeply nourishing broth!', pron: 'with deeply nourishing broth!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so fall-off-the-bone tender.', fullPron: 'It\'s so fall-off-the-bone tender', ko: 'fall-off-the-bone tender 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to fall-off-the-bone tender.', fullPron: 'You have to fall-off-the-bone tender', ko: 'fall-off-the-bone tender 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you fall-off-the-bone tender?', fullPron: 'Can you fall-off-the-bone tender?', ko: 'fall-off-the-bone tender 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['fall-off-the-bone tender', 'soak in water', 'simmer with radish']
        },
        fullEn: "It\'s so fall-off-the-bone tender with deeply nourishing broth!",
        fullPron: 'It\'s so + fall-off-the-bone tender + with deeply nourishing broth!',
        fullKo: '뼈에서 고기가 스르륵 떨어지는 야들야들한 갈비 맛보기'
      }
    ]
  },
  // ==========================================
  // EP.25. 🥣 Rich Ox Bone Soup
  // ==========================================
  {
    id: 'seolleongtang',
    epNumber: 'EP.25',
    emoji: '🥣',
    shortTitle: '🥣 Rich Ox Bone Soup',
    title: 'How to Enjoy Rich Korean Ox Bone Soup (Seolleongtang)',
    ytTitle: 'How to Make Milky Korean Ox Bone Soup in Easy English 🥣 | SoundBlock K-Cooking EP.25',
    thumbnailText: 'Milky White Seolleongtang! [We\'re gonna] + [simmer ox bones into rich milky broth]',
    thumbnailImage: '/images/kfood/ep25-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s simmer rich, milky Korean Ox Bone Soup with sliced beef brisket and somen noodles, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for soul-warming Seolleongtang! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Soak Ox Bones in Fresh Water',
        visualEmojis: '🦴 💧 ⏳',
        imagePath: '/images/kfood/ep25-thumb.jpg',
        actionNote: '사골과 소뼈를 반나절 동안 찬물에 담가 핏물 완벽 제거하기',
        coachKo: "코어 블록은 'soak ox bones in fresh water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'soak ox bones in fresh water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 사골과 소뼈를 반나절 동안 찬물에 담가 핏물 완벽 제거하기",
        missionEn: "Snap Mission! 'You have to soak ox bones in fresh water for at least six hours.' Snap!",
        keyVocab: 'soak ox bones in fresh water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'soak ox bones in fresh water', pron: 'soak ox bones in fresh water' },
          { role: 'db', en: 'for at least six hours.', pron: 'for at least six hours.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to soak ox bones in fresh water.', fullPron: 'You have to soak ox bones in fresh water', ko: 'soak ox bones in fresh water 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna soak ox bones in fresh water.', fullPron: 'I\'m gonna soak ox bones in fresh water', ko: 'soak ox bones in fresh water 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll soak ox bones in fresh water?', fullPron: 'I\'ll soak ox bones in fresh water?', ko: 'soak ox bones in fresh water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['soak ox bones in fresh water', 'boil the noodles', 'slice the beef']
        },
        fullEn: "You have to soak ox bones in fresh water for at least six hours.",
        fullPron: 'You have to + soak ox bones in fresh water + for at least six hours.',
        fullKo: '사골과 소뼈를 반나절 동안 찬물에 담가 핏물 완벽 제거하기'
      },
      {
        stepTitle: 'SCENE 2 · Boil Once & Discard First Water',
        visualEmojis: '🔥 🍲 🚿',
        imagePath: '/images/kfood/ep25-thumb.jpg',
        actionNote: '첫 끓인 물을 과감하게 버려 잡내와 불순물 완전히 없애기',
        coachKo: "코어 블록은 'discard the first boiling water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'discard the first boiling water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 첫 끓인 물을 과감하게 버려 잡내와 불순물 완전히 없애기",
        missionEn: "Snap Mission! 'We\'re gonna discard the first boiling water to remove all impurities.' Snap!",
        keyVocab: 'discard the first boiling water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'discard the first boiling water', pron: 'discard the first boiling water' },
          { role: 'db', en: 'to remove all impurities.', pron: 'to remove all impurities.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna discard the first boiling water.', fullPron: 'We\'re gonna discard the first boiling water', ko: 'discard the first boiling water 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna discard the first boiling water.', fullPron: 'I\'m gonna discard the first boiling water', ko: 'discard the first boiling water 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to discard the first boiling water?', fullPron: 'You have to discard the first boiling water?', ko: 'discard the first boiling water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['discard the first boiling water', 'simmer for hours', 'add sea salt']
        },
        fullEn: "We\'re gonna discard the first boiling water to remove all impurities.",
        fullPron: 'We\'re gonna + discard the first boiling water + to remove all impurities.',
        fullKo: '첫 끓인 물을 과감하게 버려 잡내와 불순물 완전히 없애기'
      },
      {
        stepTitle: 'SCENE 3 · Simmer on Rolling Heat for Hours',
        visualEmojis: '⏳ 🔥 🥛',
        imagePath: '/images/kfood/ep25-thumb.jpg',
        actionNote: '물을 다시 붓고 뽀얀 우윳빛 국물이 우러날 때까지 푹 고기',
        coachKo: "코어 블록은 'simmer into milky white broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'simmer into milky white broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 물을 다시 붓고 뽀얀 우윳빛 국물이 우러날 때까지 푹 고기",
        missionEn: "Snap Mission! 'I\'m gonna simmer into milky white broth over gentle steady heat.' Snap!",
        keyVocab: 'simmer into milky white broth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'simmer into milky white broth', pron: 'simmer into milky white broth' },
          { role: 'db', en: 'over gentle steady heat.', pron: 'over gentle steady heat.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna simmer into milky white broth.', fullPron: 'I\'m gonna simmer into milky white broth', ko: 'simmer into milky white broth 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to simmer into milky white broth.', fullPron: 'You have to simmer into milky white broth', ko: 'simmer into milky white broth 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna simmer into milky white broth?', fullPron: 'We\'re gonna simmer into milky white broth?', ko: 'simmer into milky white broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['simmer into milky white broth', 'soak the bones', 'season with scallions']
        },
        fullEn: "I\'m gonna simmer into milky white broth over gentle steady heat.",
        fullPron: 'I\'m gonna + simmer into milky white broth + over gentle steady heat.',
        fullKo: '물을 다시 붓고 뽀얀 우윳빛 국물이 우러날 때까지 푹 고기'
      },
      {
        stepTitle: 'SCENE 4 · Boil Beef Brisket Until Tender',
        visualEmojis: '🥩 🍲 ⏱️',
        imagePath: '/images/kfood/ep25-thumb.jpg',
        actionNote: '부드러운 양지머리 고기를 국물에 넣어 푹 삶아내기',
        coachKo: "코어 블록은 'boil beef brisket until tender'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'boil beef brisket until tender'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 부드러운 양지머리 고기를 국물에 넣어 푹 삶아내기",
        missionEn: "Snap Mission! 'You have to boil beef brisket until tender inside that rich bone broth.' Snap!",
        keyVocab: 'boil beef brisket until tender',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'boil beef brisket until tender', pron: 'boil beef brisket until tender' },
          { role: 'db', en: 'inside that rich bone broth.', pron: 'inside that rich bone broth.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to boil beef brisket until tender.', fullPron: 'You have to boil beef brisket until tender', ko: 'boil beef brisket until tender 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll boil beef brisket until tender.', fullPron: 'I\'ll boil beef brisket until tender', ko: 'boil beef brisket until tender 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna boil beef brisket until tender?', fullPron: 'I\'m gonna boil beef brisket until tender?', ko: 'boil beef brisket until tender 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['boil beef brisket until tender', 'discard the water', 'drain the noodles']
        },
        fullEn: "You have to boil beef brisket until tender inside that rich bone broth.",
        fullPron: 'You have to + boil beef brisket until tender + inside that rich bone broth.',
        fullKo: '부드러운 양지머리 고기를 국물에 넣어 푹 삶아내기'
      },
      {
        stepTitle: 'SCENE 5 · Slice Boiled Beef Thinly',
        visualEmojis: '🔪 🥩 🥢',
        imagePath: '/images/kfood/ep25-thumb.jpg',
        actionNote: '한 김 식힌 양지 고기를 결 반대 방향으로 얇게 저미기',
        coachKo: "코어 블록은 'slice boiled beef thinly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice boiled beef thinly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 한 김 식힌 양지 고기를 결 반대 방향으로 얇게 저미기",
        missionEn: "Snap Mission! 'I\'ll slice boiled beef thinly into delicate bite-sized cuts.' Snap!",
        keyVocab: 'slice boiled beef thinly',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'slice boiled beef thinly', pron: 'slice boiled beef thinly' },
          { role: 'db', en: 'into delicate bite-sized cuts.', pron: 'into delicate bite-sized cuts.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll slice boiled beef thinly.', fullPron: 'I\'ll slice boiled beef thinly', ko: 'slice boiled beef thinly 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice boiled beef thinly.', fullPron: 'I\'m gonna slice boiled beef thinly', ko: 'slice boiled beef thinly 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice boiled beef thinly?', fullPron: 'You have to slice boiled beef thinly?', ko: 'slice boiled beef thinly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['slice boiled beef thinly', 'simmer the bones', 'pour into bowl']
        },
        fullEn: "I\'ll slice boiled beef thinly into delicate bite-sized cuts.",
        fullPron: 'I\'ll + slice boiled beef thinly + into delicate bite-sized cuts.',
        fullKo: '한 김 식힌 양지 고기를 결 반대 방향으로 얇게 저미기'
      },
      {
        stepTitle: 'SCENE 6 · Add Warm Somen Wheat Noodles',
        visualEmojis: '🍜 🥣 🥢',
        imagePath: '/images/kfood/ep25-thumb.jpg',
        actionNote: '삶아둔 소면을 그릇에 담고 뜨거운 국물로 토렴하기',
        coachKo: "코어 블록은 'place warm wheat noodles'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'place warm wheat noodles'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 삶아둔 소면을 그릇에 담고 뜨거운 국물로 토렴하기",
        missionEn: "Snap Mission! 'We\'re gonna place warm wheat noodles at the bottom of the bowl.' Snap!",
        keyVocab: 'place warm wheat noodles',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'place warm wheat noodles', pron: 'place warm wheat noodles' },
          { role: 'db', en: 'at the bottom of the bowl.', pron: 'at the bottom of the bowl.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna place warm wheat noodles.', fullPron: 'We\'re gonna place warm wheat noodles', ko: 'place warm wheat noodles 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna place warm wheat noodles.', fullPron: 'I\'m gonna place warm wheat noodles', ko: 'place warm wheat noodles 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to place warm wheat noodles?', fullPron: 'You have to place warm wheat noodles?', ko: 'place warm wheat noodles 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['place warm wheat noodles', 'soak the bones', 'season with salt']
        },
        fullEn: "We\'re gonna place warm wheat noodles at the bottom of the bowl.",
        fullPron: 'We\'re gonna + place warm wheat noodles + at the bottom of the bowl.',
        fullKo: '삶아둔 소면을 그릇에 담고 뜨거운 국물로 토렴하기'
      },
      {
        stepTitle: 'SCENE 7 · Heap Mountains of Fresh Scallions',
        visualEmojis: '🌿 🧂 🫙',
        imagePath: '/images/kfood/ep25-thumb.jpg',
        actionNote: '송송 썬 파를 듬뿍 얹고 굵은 천일염과 후추로 간하기',
        coachKo: "코어 블록은 'heap plenty of chopped scallions'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'heap plenty of chopped scallions'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 송송 썬 파를 듬뿍 얹고 굵은 천일염과 후추로 간하기",
        missionEn: "Snap Mission! 'You have to heap plenty of chopped scallions with coarse sea salt and pepper.' Snap!",
        keyVocab: 'heap plenty of chopped scallions',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'heap plenty of chopped scallions', pron: 'heap plenty of chopped scallions' },
          { role: 'db', en: 'with coarse sea salt and pepper.', pron: 'with coarse sea salt and pepper.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to heap plenty of chopped scallions.', fullPron: 'You have to heap plenty of chopped scallions', ko: 'heap plenty of chopped scallions 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna heap plenty of chopped scallions.', fullPron: 'I\'m gonna heap plenty of chopped scallions', ko: 'heap plenty of chopped scallions 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll heap plenty of chopped scallions?', fullPron: 'I\'ll heap plenty of chopped scallions?', ko: 'heap plenty of chopped scallions 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['heap plenty of chopped scallions', 'slice the meat', 'boil the broth']
        },
        fullEn: "You have to heap plenty of chopped scallions with coarse sea salt and pepper.",
        fullPron: 'You have to + heap plenty of chopped scallions + with coarse sea salt and pepper.',
        fullKo: '송송 썬 파를 듬뿍 얹고 굵은 천일염과 후추로 간하기'
      },
      {
        stepTitle: 'SCENE 8 · Velvety Deep & Soul-Warming',
        visualEmojis: '😋 🥣 🤍',
        imagePath: '/images/kfood/ep25-thumb.jpg',
        actionNote: '입안 가득 감도는 고소함과 깍두기 국물을 곁들인 환상의 맛',
        coachKo: "코어 블록은 'velvety deep and soul-warming'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'velvety deep and soul-warming'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 입안 가득 감도는 고소함과 깍두기 국물을 곁들인 환상의 맛",
        missionEn: "Snap Mission! 'It\'s so velvety deep and soul-warming with crisp radish kimchi!' Snap!",
        keyVocab: 'velvety deep and soul-warming',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'velvety deep and soul-warming', pron: 'velvety deep and soul-warming' },
          { role: 'db', en: 'with crisp radish kimchi!', pron: 'with crisp radish kimchi!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so velvety deep and soul-warming.', fullPron: 'It\'s so velvety deep and soul-warming', ko: 'velvety deep and soul-warming 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to velvety deep and soul-warming.', fullPron: 'You have to velvety deep and soul-warming', ko: 'velvety deep and soul-warming 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you velvety deep and soul-warming?', fullPron: 'Can you velvety deep and soul-warming?', ko: 'velvety deep and soul-warming 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['velvety deep and soul-warming', 'soak ox bones', 'simmer into broth']
        },
        fullEn: "It\'s so velvety deep and soul-warming with crisp radish kimchi!",
        fullPron: 'It\'s so + velvety deep and soul-warming + with crisp radish kimchi!',
        fullKo: '입안 가득 감도는 고소함과 깍두기 국물을 곁들인 환상의 맛'
      }
    ]
  },
  // ==========================================
  // EP.26. 🥘 Spicy Pork Backbone Stew
  // ==========================================
  {
    id: 'gamjatang',
    epNumber: 'EP.26',
    emoji: '🥘',
    shortTitle: '🥘 Spicy Pork Backbone Stew',
    title: 'How to Cook Spicy Korean Pork Backbone Stew (Gamjatang)',
    ytTitle: 'How to Make Authentic Gamjatang in Easy English 🥘 | SoundBlock K-Cooking EP.26',
    thumbnailText: 'Spicy Pork Backbone Stew! [We\'re gonna] + [simmer tender pork bones with wild perilla]',
    thumbnailImage: '/images/kfood/ep26-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s cook hearty Korean Pork Backbone Stew with tender meat, soft potatoes, and nutty perilla seeds, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for rich Gamjatang! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Soak Pork Backbones in Cold Water',
        visualEmojis: '🍖 💧 ⏳',
        imagePath: '/images/kfood/ep26-thumb.jpg',
        actionNote: '돼지 등뼈의 핏물을 찬물에서 3시간 동안 빼내기',
        coachKo: "코어 블록은 'soak pork backbones in cold water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'soak pork backbones in cold water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 돼지 등뼈의 핏물을 찬물에서 3시간 동안 빼내기",
        missionEn: "Snap Mission! 'You have to soak pork backbones in cold water to ensure clean flavor.' Snap!",
        keyVocab: 'soak pork backbones in cold water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'soak pork backbones in cold water', pron: 'soak pork backbones in cold water' },
          { role: 'db', en: 'to ensure clean flavor.', pron: 'to ensure clean flavor.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to soak pork backbones in cold water.', fullPron: 'You have to soak pork backbones in cold water', ko: 'soak pork backbones in cold water 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna soak pork backbones in cold water.', fullPron: 'I\'m gonna soak pork backbones in cold water', ko: 'soak pork backbones in cold water 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll soak pork backbones in cold water?', fullPron: 'I\'ll soak pork backbones in cold water?', ko: 'soak pork backbones in cold water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['soak pork backbones in cold water', 'parboil the bones', 'peel the potatoes']
        },
        fullEn: "You have to soak pork backbones in cold water to ensure clean flavor.",
        fullPron: 'You have to + soak pork backbones in cold water + to ensure clean flavor.',
        fullKo: '돼지 등뼈의 핏물을 찬물에서 3시간 동안 빼내기'
      },
      {
        stepTitle: 'SCENE 2 · Parboil with Ginger & Rice Wine',
        visualEmojis: '🔥 🫚 🍶',
        imagePath: '/images/kfood/ep26-thumb.jpg',
        actionNote: '생강과 통후추, 된장을 넣고 끓여 등뼈의 잡내 날리기',
        coachKo: "코어 블록은 'parboil with fresh ginger'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'parboil with fresh ginger'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 생강과 통후추, 된장을 넣고 끓여 등뼈의 잡내 날리기",
        missionEn: "Snap Mission! 'We\'re gonna parboil with fresh ginger and a tablespoon of soybean paste.' Snap!",
        keyVocab: 'parboil with fresh ginger',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'parboil with fresh ginger', pron: 'parboil with fresh ginger' },
          { role: 'db', en: 'and a tablespoon of soybean paste.', pron: 'and a tablespoon of soybean paste.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna parboil with fresh ginger.', fullPron: 'We\'re gonna parboil with fresh ginger', ko: 'parboil with fresh ginger 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna parboil with fresh ginger.', fullPron: 'I\'m gonna parboil with fresh ginger', ko: 'parboil with fresh ginger 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to parboil with fresh ginger?', fullPron: 'You have to parboil with fresh ginger?', ko: 'parboil with fresh ginger 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['parboil with fresh ginger', 'season with perilla', 'simmer with radish greens']
        },
        fullEn: "We\'re gonna parboil with fresh ginger and a tablespoon of soybean paste.",
        fullPron: 'We\'re gonna + parboil with fresh ginger + and a tablespoon of soybean paste.',
        fullKo: '생강과 통후추, 된장을 넣고 끓여 등뼈의 잡내 날리기'
      },
      {
        stepTitle: 'SCENE 3 · Mix Spicy Gochujang Sauce',
        visualEmojis: '🌶️ 🧄 🫙',
        imagePath: '/images/kfood/ep26-thumb.jpg',
        actionNote: '고춧가루, 다진 마늘, 된장, 국간장으로 특제 양념장 만들기',
        coachKo: "코어 블록은 'mix spicy red chili paste'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix spicy red chili paste'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고춧가루, 다진 마늘, 된장, 국간장으로 특제 양념장 만들기",
        missionEn: "Snap Mission! 'I\'m gonna mix spicy red chili paste with minced garlic and soybean paste.' Snap!",
        keyVocab: 'mix spicy red chili paste',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'mix spicy red chili paste', pron: 'mix spicy red chili paste' },
          { role: 'db', en: 'with minced garlic and soybean paste.', pron: 'with minced garlic and soybean paste.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix spicy red chili paste.', fullPron: 'I\'m gonna mix spicy red chili paste', ko: 'mix spicy red chili paste 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix spicy red chili paste.', fullPron: 'You have to mix spicy red chili paste', ko: 'mix spicy red chili paste 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll mix spicy red chili paste?', fullPron: 'I\'ll mix spicy red chili paste?', ko: 'mix spicy red chili paste 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['mix spicy red chili paste', 'soak backbones', 'peel potatoes']
        },
        fullEn: "I\'m gonna mix spicy red chili paste with minced garlic and soybean paste.",
        fullPron: 'I\'m gonna + mix spicy red chili paste + with minced garlic and soybean paste.',
        fullKo: '고춧가루, 다진 마늘, 된장, 국간장으로 특제 양념장 만들기'
      },
      {
        stepTitle: 'SCENE 4 · Simmer Bones for Two Hours',
        visualEmojis: '⏳ 🍲 🔥',
        imagePath: '/images/kfood/ep26-thumb.jpg',
        actionNote: '등뼈 살코기가 부드럽게 뜯어질 때까지 푹 삶기',
        coachKo: "코어 블록은 'simmer bones for two hours'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'simmer bones for two hours'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 등뼈 살코기가 부드럽게 뜯어질 때까지 푹 삶기",
        missionEn: "Snap Mission! 'You have to simmer bones for two hours until meat is fork-tender.' Snap!",
        keyVocab: 'simmer bones for two hours',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'simmer bones for two hours', pron: 'simmer bones for two hours' },
          { role: 'db', en: 'until meat is fork-tender.', pron: 'until meat is fork-tender.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to simmer bones for two hours.', fullPron: 'You have to simmer bones for two hours', ko: 'simmer bones for two hours 할 거예요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna simmer bones for two hours.', fullPron: 'We\'re gonna simmer bones for two hours', ko: 'simmer bones for two hours 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna simmer bones for two hours?', fullPron: 'I\'m gonna simmer bones for two hours?', ko: 'simmer bones for two hours 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "We\'re gonna", "I\'m gonna"],
          coreCandidates: ['simmer bones for two hours', 'add whole potatoes', 'garnish with perilla']
        },
        fullEn: "You have to simmer bones for two hours until meat is fork-tender.",
        fullPron: 'You have to + simmer bones for two hours + until meat is fork-tender.',
        fullKo: '등뼈 살코기가 부드럽게 뜯어질 때까지 푹 삶기'
      },
      {
        stepTitle: 'SCENE 5 · Add Soft Boiled Radish Greens',
        visualEmojis: '🥬 🍲 ✨',
        imagePath: '/images/kfood/ep26-thumb.jpg',
        actionNote: '구수한 시래기와 양념장을 넣고 국물에 깊은 맛 배게 하기',
        coachKo: "코어 블록은 'add seasoned dried radish greens'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add seasoned dried radish greens'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 구수한 시래기와 양념장을 넣고 국물에 깊은 맛 배게 하기",
        missionEn: "Snap Mission! 'We\'re gonna add seasoned dried radish greens into the bubbling deep broth.' Snap!",
        keyVocab: 'add seasoned dried radish greens',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'add seasoned dried radish greens', pron: 'add seasoned dried radish greens' },
          { role: 'db', en: 'into the bubbling deep broth.', pron: 'into the bubbling deep broth.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna add seasoned dried radish greens.', fullPron: 'We\'re gonna add seasoned dried radish greens', ko: 'add seasoned dried radish greens 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna add seasoned dried radish greens.', fullPron: 'I\'m gonna add seasoned dried radish greens', ko: 'add seasoned dried radish greens 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to add seasoned dried radish greens?', fullPron: 'You have to add seasoned dried radish greens?', ko: 'add seasoned dried radish greens 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['add seasoned dried radish greens', 'parboil with ginger', 'peel the potatoes']
        },
        fullEn: "We\'re gonna add seasoned dried radish greens into the bubbling deep broth.",
        fullPron: 'We\'re gonna + add seasoned dried radish greens + into the bubbling deep broth.',
        fullKo: '구수한 시래기와 양념장을 넣고 국물에 깊은 맛 배게 하기'
      },
      {
        stepTitle: 'SCENE 6 · Drop in Whole Chunky Potatoes',
        visualEmojis: '🥔 🍲 ⏱️',
        imagePath: '/images/kfood/ep26-thumb.jpg',
        actionNote: '포슬포슬한 통감자를 듬뿍 넣고 포근하게 익히기',
        coachKo: "코어 블록은 'drop in whole chunky potatoes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'drop in whole chunky potatoes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 포슬포슬한 통감자를 듬뿍 넣고 포근하게 익히기",
        missionEn: "Snap Mission! 'I\'ll drop in whole chunky potatoes until they\'re melt-in-mouth soft.' Snap!",
        keyVocab: 'drop in whole chunky potatoes',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'drop in whole chunky potatoes', pron: 'drop in whole chunky potatoes' },
          { role: 'db', en: 'until they\'re melt-in-mouth soft.', pron: 'until they\'re melt-in-mouth soft.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll drop in whole chunky potatoes.', fullPron: 'I\'ll drop in whole chunky potatoes', ko: 'drop in whole chunky potatoes 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna drop in whole chunky potatoes.', fullPron: 'I\'m gonna drop in whole chunky potatoes', ko: 'drop in whole chunky potatoes 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to drop in whole chunky potatoes?', fullPron: 'You have to drop in whole chunky potatoes?', ko: 'drop in whole chunky potatoes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['drop in whole chunky potatoes', 'soak pork bones', 'mix chili paste']
        },
        fullEn: "I\'ll drop in whole chunky potatoes until they\'re melt-in-mouth soft.",
        fullPron: 'I\'ll + drop in whole chunky potatoes + until they\'re melt-in-mouth soft.',
        fullKo: '포슬포슬한 통감자를 듬뿍 넣고 포근하게 익히기'
      },
      {
        stepTitle: 'SCENE 7 · Heap Toasted Wild Perilla Powder',
        visualEmojis: '🌰 🌿 ✨',
        imagePath: '/images/kfood/ep26-thumb.jpg',
        actionNote: '고소한 들깨가루와 향긋한 깻잎을 산더미처럼 얹기',
        coachKo: "코어 블록은 'heap toasted wild perilla seed powder'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'heap toasted wild perilla seed powder'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고소한 들깨가루와 향긋한 깻잎을 산더미처럼 얹기",
        missionEn: "Snap Mission! 'You have to heap toasted wild perilla seed powder and fresh torn perilla leaves.' Snap!",
        keyVocab: 'heap toasted wild perilla seed powder',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'heap toasted wild perilla seed powder', pron: 'heap toasted wild perilla seed powder' },
          { role: 'db', en: 'and fresh torn perilla leaves.', pron: 'and fresh torn perilla leaves.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to heap toasted wild perilla seed powder.', fullPron: 'You have to heap toasted wild perilla seed powder', ko: 'heap toasted wild perilla seed powder 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna heap toasted wild perilla seed powder.', fullPron: 'I\'m gonna heap toasted wild perilla seed powder', ko: 'heap toasted wild perilla seed powder 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna heap toasted wild perilla seed powder?', fullPron: 'We\'re gonna heap toasted wild perilla seed powder?', ko: 'heap toasted wild perilla seed powder 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['heap toasted wild perilla seed powder', 'simmer for hours', 'drop in potatoes']
        },
        fullEn: "You have to heap toasted wild perilla seed powder and fresh torn perilla leaves.",
        fullPron: 'You have to + heap toasted wild perilla seed powder + and fresh torn perilla leaves.',
        fullKo: '고소한 들깨가루와 향긋한 깻잎을 산더미처럼 얹기'
      },
      {
        stepTitle: 'SCENE 8 · Melt-In-Your-Mouth Rich Flavor',
        visualEmojis: '😋 🍖 🥘',
        imagePath: '/images/kfood/ep26-thumb.jpg',
        actionNote: '뼈 사이사이 부드러운 고기와 진한 들깨 국물 맛보기',
        coachKo: "코어 블록은 'melt-in-your-mouth rich and spicy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'melt-in-your-mouth rich and spicy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뼈 사이사이 부드러운 고기와 진한 들깨 국물 맛보기",
        missionEn: "Snap Mission! 'It\'s so melt-in-your-mouth rich and spicy with heavenly tender meat!' Snap!",
        keyVocab: 'melt-in-your-mouth rich and spicy',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'melt-in-your-mouth rich and spicy', pron: 'melt-in-your-mouth rich and spicy' },
          { role: 'db', en: 'with heavenly tender meat!', pron: 'with heavenly tender meat!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so melt-in-your-mouth rich and spicy.', fullPron: 'It\'s so melt-in-your-mouth rich and spicy', ko: 'melt-in-your-mouth rich and spicy 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to melt-in-your-mouth rich and spicy.', fullPron: 'You have to melt-in-your-mouth rich and spicy', ko: 'melt-in-your-mouth rich and spicy 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you melt-in-your-mouth rich and spicy?', fullPron: 'Can you melt-in-your-mouth rich and spicy?', ko: 'melt-in-your-mouth rich and spicy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['melt-in-your-mouth rich and spicy', 'soak backbones', 'add perilla powder']
        },
        fullEn: "It\'s so melt-in-your-mouth rich and spicy with heavenly tender meat!",
        fullPron: 'It\'s so + melt-in-your-mouth rich and spicy + with heavenly tender meat!',
        fullKo: '뼈 사이사이 부드러운 고기와 진한 들깨 국물 맛보기'
      }
    ]
  },
  // ==========================================
  // EP.27. 🥣 Beef Radish Soup
  // ==========================================
  {
    id: 'beef-radish-soup',
    epNumber: 'EP.27',
    emoji: '🥣',
    shortTitle: '🥣 Beef Radish Soup',
    title: 'How to Make Comforting Korean Beef Radish Soup',
    ytTitle: 'How to Cook Clear Korean Beef Radish Soup in Easy English 🥣 | SoundBlock K-Cooking EP.27',
    thumbnailText: 'Clear Beef Radish Soup! [I\'m gonna] + [stir-fry tender beef with sweet radish]',
    thumbnailImage: '/images/kfood/ep27-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make comforting Korean Beef Radish Soup, a classic home-style soup with sweet radish and savory beef, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for home-style Beef Radish Soup! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Slice Korean Radish into Thin Squares',
        visualEmojis: '🔪 🤍 🥣',
        imagePath: '/images/kfood/ep27-thumb.jpg',
        actionNote: '시원하고 달큰한 조선무를 나박나박 네모나게 썰기',
        coachKo: "코어 블록은 'slice sweet Korean radish'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice sweet Korean radish'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 시원하고 달큰한 조선무를 나박나박 네모나게 썰기",
        missionEn: "Snap Mission! 'You have to slice sweet Korean radish into thin flat bite-sized squares.' Snap!",
        keyVocab: 'slice sweet Korean radish',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'slice sweet Korean radish', pron: 'slice sweet Korean radish' },
          { role: 'db', en: 'into thin flat bite-sized squares.', pron: 'into thin flat bite-sized squares.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to slice sweet Korean radish.', fullPron: 'You have to slice sweet Korean radish', ko: 'slice sweet Korean radish 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice sweet Korean radish.', fullPron: 'I\'m gonna slice sweet Korean radish', ko: 'slice sweet Korean radish 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll slice sweet Korean radish?', fullPron: 'I\'ll slice sweet Korean radish?', ko: 'slice sweet Korean radish 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['slice sweet Korean radish', 'stir-fry the beef', 'pour cold water']
        },
        fullEn: "You have to slice sweet Korean radish into thin flat bite-sized squares.",
        fullPron: 'You have to + slice sweet Korean radish + into thin flat bite-sized squares.',
        fullKo: '시원하고 달큰한 조선무를 나박나박 네모나게 썰기'
      },
      {
        stepTitle: 'SCENE 2 · Chop Tender Beef Brisket',
        visualEmojis: '🥩 🔪 🥢',
        imagePath: '/images/kfood/ep27-thumb.jpg',
        actionNote: '소고기 양지머리를 결 반대로 한 입 크기로 썰기',
        coachKo: "코어 블록은 'chop tender beef brisket'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'chop tender beef brisket'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 소고기 양지머리를 결 반대로 한 입 크기로 썰기",
        missionEn: "Snap Mission! 'I\'m gonna chop tender beef brisket into small thin pieces.' Snap!",
        keyVocab: 'chop tender beef brisket',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'chop tender beef brisket', pron: 'chop tender beef brisket' },
          { role: 'db', en: 'into small thin pieces.', pron: 'into small thin pieces.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna chop tender beef brisket.', fullPron: 'I\'m gonna chop tender beef brisket', ko: 'chop tender beef brisket 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to chop tender beef brisket.', fullPron: 'You have to chop tender beef brisket', ko: 'chop tender beef brisket 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna chop tender beef brisket?', fullPron: 'We\'re gonna chop tender beef brisket?', ko: 'chop tender beef brisket 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['chop tender beef brisket', 'slice the radish', 'season with salt']
        },
        fullEn: "I\'m gonna chop tender beef brisket into small thin pieces.",
        fullPron: 'I\'m gonna + chop tender beef brisket + into small thin pieces.',
        fullKo: '소고기 양지머리를 결 반대로 한 입 크기로 썰기'
      },
      {
        stepTitle: 'SCENE 3 · Stir-Fry Beef in Toasted Sesame Oil',
        visualEmojis: '🍳 🥩 🫙',
        imagePath: '/images/kfood/ep27-thumb.jpg',
        actionNote: '참기름을 두르고 고소한 냄새가 날 때까지 소고기 볶기',
        coachKo: "코어 블록은 'stir-fry beef in sesame oil'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir-fry beef in sesame oil'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 참기름을 두르고 고소한 냄새가 날 때까지 소고기 볶기",
        missionEn: "Snap Mission! 'We\'re gonna stir-fry beef in sesame oil until the surface turns brown.' Snap!",
        keyVocab: 'stir-fry beef in sesame oil',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'stir-fry beef in sesame oil', pron: 'stir-fry beef in sesame oil' },
          { role: 'db', en: 'until the surface turns brown.', pron: 'until the surface turns brown.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna stir-fry beef in sesame oil.', fullPron: 'We\'re gonna stir-fry beef in sesame oil', ko: 'stir-fry beef in sesame oil 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna stir-fry beef in sesame oil.', fullPron: 'I\'m gonna stir-fry beef in sesame oil', ko: 'stir-fry beef in sesame oil 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to stir-fry beef in sesame oil?', fullPron: 'You have to stir-fry beef in sesame oil?', ko: 'stir-fry beef in sesame oil 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['stir-fry beef in sesame oil', 'pour cold water', 'slice scallions']
        },
        fullEn: "We\'re gonna stir-fry beef in sesame oil until the surface turns brown.",
        fullPron: 'We\'re gonna + stir-fry beef in sesame oil + until the surface turns brown.',
        fullKo: '참기름을 두르고 고소한 냄새가 날 때까지 소고기 볶기'
      },
      {
        stepTitle: 'SCENE 4 · Add Sliced Radish and Toss Together',
        visualEmojis: '🤍 🥩 🔥',
        imagePath: '/images/kfood/ep27-thumb.jpg',
        actionNote: '나박 썬 무를 넣고 투명해질 때까지 고기와 함께 볶기',
        coachKo: "코어 블록은 'toss sliced radish together'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toss sliced radish together'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 나박 썬 무를 넣고 투명해질 때까지 고기와 함께 볶기",
        missionEn: "Snap Mission! 'You have to toss sliced radish together until edges look translucent.' Snap!",
        keyVocab: 'toss sliced radish together',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'toss sliced radish together', pron: 'toss sliced radish together' },
          { role: 'db', en: 'until edges look translucent.', pron: 'until edges look translucent.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to toss sliced radish together.', fullPron: 'You have to toss sliced radish together', ko: 'toss sliced radish together 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll toss sliced radish together.', fullPron: 'I\'ll toss sliced radish together', ko: 'toss sliced radish together 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna toss sliced radish together?', fullPron: 'I\'m gonna toss sliced radish together?', ko: 'toss sliced radish together 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['toss sliced radish together', 'pour the water', 'skim off foam']
        },
        fullEn: "You have to toss sliced radish together until edges look translucent.",
        fullPron: 'You have to + toss sliced radish together + until edges look translucent.',
        fullKo: '나박 썬 무를 넣고 투명해질 때까지 고기와 함께 볶기'
      },
      {
        stepTitle: 'SCENE 5 · Pour Fresh Cold Water and Boil',
        visualEmojis: '💧 🍲 🔥',
        imagePath: '/images/kfood/ep27-thumb.jpg',
        actionNote: '찬물을 넉넉히 붓고 센 불에서 팔팔 끓어오르게 두기',
        coachKo: "코어 블록은 'pour fresh cold water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour fresh cold water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 찬물을 넉넉히 붓고 센 불에서 팔팔 끓어오르게 두기",
        missionEn: "Snap Mission! 'I\'ll pour fresh cold water and bring to rolling boil.' Snap!",
        keyVocab: 'pour fresh cold water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'pour fresh cold water', pron: 'pour fresh cold water' },
          { role: 'db', en: 'and bring to rolling boil.', pron: 'and bring to rolling boil.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll pour fresh cold water.', fullPron: 'I\'ll pour fresh cold water', ko: 'pour fresh cold water 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour fresh cold water.', fullPron: 'I\'m gonna pour fresh cold water', ko: 'pour fresh cold water 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour fresh cold water?', fullPron: 'You have to pour fresh cold water?', ko: 'pour fresh cold water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['pour fresh cold water', 'stir-fry beef', 'chop the radish']
        },
        fullEn: "I\'ll pour fresh cold water and bring to rolling boil.",
        fullPron: 'I\'ll + pour fresh cold water + and bring to rolling boil.',
        fullKo: '찬물을 넉넉히 붓고 센 불에서 팔팔 끓어오르게 두기'
      },
      {
        stepTitle: 'SCENE 6 · Skim Off Brown Foam for Clarity',
        visualEmojis: '🥄 🫙 ✨',
        imagePath: '/images/kfood/ep27-thumb.jpg',
        actionNote: '맑고 깔끔한 국물을 위해 위로 뜨는 거품 걷어내기',
        coachKo: "코어 블록은 'skim off floating foam'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'skim off floating foam'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 맑고 깔끔한 국물을 위해 위로 뜨는 거품 걷어내기",
        missionEn: "Snap Mission! 'You have to skim off floating foam to keep the soup crystal clear.' Snap!",
        keyVocab: 'skim off floating foam',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'skim off floating foam', pron: 'skim off floating foam' },
          { role: 'db', en: 'to keep the soup crystal clear.', pron: 'to keep the soup crystal clear.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to skim off floating foam.', fullPron: 'You have to skim off floating foam', ko: 'skim off floating foam 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna skim off floating foam.', fullPron: 'I\'m gonna skim off floating foam', ko: 'skim off floating foam 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna skim off floating foam?', fullPron: 'We\'re gonna skim off floating foam?', ko: 'skim off floating foam 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['skim off floating foam', 'season with soy sauce', 'add scallions']
        },
        fullEn: "You have to skim off floating foam to keep the soup crystal clear.",
        fullPron: 'You have to + skim off floating foam + to keep the soup crystal clear.',
        fullKo: '맑고 깔끔한 국물을 위해 위로 뜨는 거품 걷어내기'
      },
      {
        stepTitle: 'SCENE 7 · Season with Soup Soy Sauce & Garlic',
        visualEmojis: '🫙 🧄 🌿',
        imagePath: '/images/kfood/ep27-thumb.jpg',
        actionNote: '국간장과 다진 마늘, 송송 썬 대파로 깔끔한 풍미 내기',
        coachKo: "코어 블록은 'season with soup soy sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'season with soup soy sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 국간장과 다진 마늘, 송송 썬 대파로 깔끔한 풍미 내기",
        missionEn: "Snap Mission! 'I\'m gonna season with soup soy sauce and fragrant minced garlic.' Snap!",
        keyVocab: 'season with soup soy sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'season with soup soy sauce', pron: 'season with soup soy sauce' },
          { role: 'db', en: 'and fragrant minced garlic.', pron: 'and fragrant minced garlic.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna season with soup soy sauce.', fullPron: 'I\'m gonna season with soup soy sauce', ko: 'season with soup soy sauce 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to season with soup soy sauce.', fullPron: 'You have to season with soup soy sauce', ko: 'season with soup soy sauce 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll season with soup soy sauce?', fullPron: 'I\'ll season with soup soy sauce?', ko: 'season with soup soy sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['season with soup soy sauce', 'stir-fry in sesame oil', 'pour cold water']
        },
        fullEn: "I\'m gonna season with soup soy sauce and fragrant minced garlic.",
        fullPron: 'I\'m gonna + season with soup soy sauce + and fragrant minced garlic.',
        fullKo: '국간장과 다진 마늘, 송송 썬 대파로 깔끔한 풍미 내기'
      },
      {
        stepTitle: 'SCENE 8 · Sweet Clean & Heartwarming',
        visualEmojis: '😋 🥣 ✨',
        imagePath: '/images/kfood/ep27-thumb.jpg',
        actionNote: '무의 달큼한 감칠맛과 소고기 육즙이 어우러진 맑은 국물',
        coachKo: "코어 블록은 'sweet clean and heartwarming'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sweet clean and heartwarming'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 무의 달큼한 감칠맛과 소고기 육즙이 어우러진 맑은 국물",
        missionEn: "Snap Mission! 'It\'s so sweet clean and heartwarming with pure comforting flavors!' Snap!",
        keyVocab: 'sweet clean and heartwarming',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'sweet clean and heartwarming', pron: 'sweet clean and heartwarming' },
          { role: 'db', en: 'with pure comforting flavors!', pron: 'with pure comforting flavors!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so sweet clean and heartwarming.', fullPron: 'It\'s so sweet clean and heartwarming', ko: 'sweet clean and heartwarming 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to sweet clean and heartwarming.', fullPron: 'You have to sweet clean and heartwarming', ko: 'sweet clean and heartwarming 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you sweet clean and heartwarming?', fullPron: 'Can you sweet clean and heartwarming?', ko: 'sweet clean and heartwarming 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['sweet clean and heartwarming', 'slice sweet radish', 'skim off foam']
        },
        fullEn: "It\'s so sweet clean and heartwarming with pure comforting flavors!",
        fullPron: 'It\'s so + sweet clean and heartwarming + with pure comforting flavors!',
        fullKo: '무의 달큼한 감칠맛과 소고기 육즙이 어우러진 맑은 국물'
      }
    ]
  },
  // ==========================================
  // EP.28. 🍚 Bean Sprout Soup & Rice
  // ==========================================
  {
    id: 'kongnamul-gukbap',
    epNumber: 'EP.28',
    emoji: '🍚',
    shortTitle: '🍚 Bean Sprout Soup & Rice',
    title: 'How to Make Korean Bean Sprout Hangover Soup with Rice',
    ytTitle: 'How to Make Korean Bean Sprout Hangover Soup in Easy English 🍚 | SoundBlock K-Cooking EP.28',
    thumbnailText: 'Crunchy Bean Sprout Gukbap! [You have to] + [boil crisp bean sprouts in anchovy broth]',
    thumbnailImage: '/images/kfood/ep28-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make soothing Korean Bean Sprout Hangover Soup with warm rice, crisp sprouts, and soft poached egg, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for refreshing Bean Sprout Gukbap! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Wash Crisp Bean Sprouts Thoroughly',
        visualEmojis: '🌱 💧 🧼',
        imagePath: '/images/kfood/ep28-thumb.jpg',
        actionNote: '싱싱하고 아삭한 콩나물을 찬물에 두세 번 깨끗이 헹구기',
        coachKo: "코어 블록은 'wash crisp bean sprouts thoroughly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'wash crisp bean sprouts thoroughly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 싱싱하고 아삭한 콩나물을 찬물에 두세 번 깨끗이 헹구기",
        missionEn: "Snap Mission! 'You have to wash crisp bean sprouts thoroughly in cold running water.' Snap!",
        keyVocab: 'wash crisp bean sprouts thoroughly',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'wash crisp bean sprouts thoroughly', pron: 'wash crisp bean sprouts thoroughly' },
          { role: 'db', en: 'in cold running water.', pron: 'in cold running water.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to wash crisp bean sprouts thoroughly.', fullPron: 'You have to wash crisp bean sprouts thoroughly', ko: 'wash crisp bean sprouts thoroughly 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna wash crisp bean sprouts thoroughly.', fullPron: 'I\'m gonna wash crisp bean sprouts thoroughly', ko: 'wash crisp bean sprouts thoroughly 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll wash crisp bean sprouts thoroughly?', fullPron: 'I\'ll wash crisp bean sprouts thoroughly?', ko: 'wash crisp bean sprouts thoroughly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['wash crisp bean sprouts thoroughly', 'boil anchovy broth', 'poach the egg']
        },
        fullEn: "You have to wash crisp bean sprouts thoroughly in cold running water.",
        fullPron: 'You have to + wash crisp bean sprouts thoroughly + in cold running water.',
        fullKo: '싱싱하고 아삭한 콩나물을 찬물에 두세 번 깨끗이 헹구기'
      },
      {
        stepTitle: 'SCENE 2 · Brew Deep Dried Pollack & Anchovy Broth',
        visualEmojis: '🐟 🍲 🌊',
        imagePath: '/images/kfood/ep28-thumb.jpg',
        actionNote: '황태채와 멸치, 다시마로 속이 확 풀리는 시원한 육수 내기',
        coachKo: "코어 블록은 'brew dried pollack anchovy broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'brew dried pollack anchovy broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 황태채와 멸치, 다시마로 속이 확 풀리는 시원한 육수 내기",
        missionEn: "Snap Mission! 'We\'re gonna brew dried pollack anchovy broth for that deeply refreshing base.' Snap!",
        keyVocab: 'brew dried pollack anchovy broth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'brew dried pollack anchovy broth', pron: 'brew dried pollack anchovy broth' },
          { role: 'db', en: 'for that deeply refreshing base.', pron: 'for that deeply refreshing base.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna brew dried pollack anchovy broth.', fullPron: 'We\'re gonna brew dried pollack anchovy broth', ko: 'brew dried pollack anchovy broth 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna brew dried pollack anchovy broth.', fullPron: 'I\'m gonna brew dried pollack anchovy broth', ko: 'brew dried pollack anchovy broth 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to brew dried pollack anchovy broth?', fullPron: 'You have to brew dried pollack anchovy broth?', ko: 'brew dried pollack anchovy broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['brew dried pollack anchovy broth', 'wash bean sprouts', 'dice the squid']
        },
        fullEn: "We\'re gonna brew dried pollack anchovy broth for that deeply refreshing base.",
        fullPron: 'We\'re gonna + brew dried pollack anchovy broth + for that deeply refreshing base.',
        fullKo: '황태채와 멸치, 다시마로 속이 확 풀리는 시원한 육수 내기'
      },
      {
        stepTitle: 'SCENE 3 · Dice Boiled Squid into Tiny Cubes',
        visualEmojis: '🦑 🔪 🥣',
        imagePath: '/images/kfood/ep28-thumb.jpg',
        actionNote: '쫄깃하게 데친 오징어를 잘게 썰어 고명 준비하기',
        coachKo: "코어 블록은 'dice boiled squid into cubes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'dice boiled squid into cubes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 쫄깃하게 데친 오징어를 잘게 썰어 고명 준비하기",
        missionEn: "Snap Mission! 'I\'m gonna dice boiled squid into cubes to add delicious chewy texture.' Snap!",
        keyVocab: 'dice boiled squid into cubes',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'dice boiled squid into cubes', pron: 'dice boiled squid into cubes' },
          { role: 'db', en: 'to add delicious chewy texture.', pron: 'to add delicious chewy texture.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna dice boiled squid into cubes.', fullPron: 'I\'m gonna dice boiled squid into cubes', ko: 'dice boiled squid into cubes 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to dice boiled squid into cubes.', fullPron: 'You have to dice boiled squid into cubes', ko: 'dice boiled squid into cubes 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll dice boiled squid into cubes?', fullPron: 'I\'ll dice boiled squid into cubes?', ko: 'dice boiled squid into cubes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['dice boiled squid into cubes', 'wash bean sprouts', 'boil on high heat']
        },
        fullEn: "I\'m gonna dice boiled squid into cubes to add delicious chewy texture.",
        fullPron: 'I\'m gonna + dice boiled squid into cubes + to add delicious chewy texture.',
        fullKo: '쫄깃하게 데친 오징어를 잘게 썰어 고명 준비하기'
      },
      {
        stepTitle: 'SCENE 4 · Boil Sprouts with Lid Open',
        visualEmojis: '🌱 🔥 🍲',
        imagePath: '/images/kfood/ep28-thumb.jpg',
        actionNote: '비린내를 없애기 위해 뚜껑을 열고 아삭하게 끓이기',
        coachKo: "코어 블록은 'boil bean sprouts with lid open'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'boil bean sprouts with lid open'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 비린내를 없애기 위해 뚜껑을 열고 아삭하게 끓이기",
        missionEn: "Snap Mission! 'You have to boil bean sprouts with lid open so they stay perfectly crunchy.' Snap!",
        keyVocab: 'boil bean sprouts with lid open',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'boil bean sprouts with lid open', pron: 'boil bean sprouts with lid open' },
          { role: 'db', en: 'so they stay perfectly crunchy.', pron: 'so they stay perfectly crunchy.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to boil bean sprouts with lid open.', fullPron: 'You have to boil bean sprouts with lid open', ko: 'boil bean sprouts with lid open 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna boil bean sprouts with lid open.', fullPron: 'I\'m gonna boil bean sprouts with lid open', ko: 'boil bean sprouts with lid open 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna boil bean sprouts with lid open?', fullPron: 'We\'re gonna boil bean sprouts with lid open?', ko: 'boil bean sprouts with lid open 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['boil bean sprouts with lid open', 'dice boiled squid', 'brew pollack broth']
        },
        fullEn: "You have to boil bean sprouts with lid open so they stay perfectly crunchy.",
        fullPron: 'You have to + boil bean sprouts with lid open + so they stay perfectly crunchy.',
        fullKo: '비린내를 없애기 위해 뚜껑을 열고 아삭하게 끓이기'
      },
      {
        stepTitle: 'SCENE 5 · Season with Salted Shrimp & Cheongyang',
        visualEmojis: '🦐 🌶️ 🧄',
        imagePath: '/images/kfood/ep28-thumb.jpg',
        actionNote: '새우젓과 다진 청양고추로 칼칼하고 시원한 간 맞추기',
        coachKo: "코어 블록은 'season with salted fermented shrimp'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'season with salted fermented shrimp'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 새우젓과 다진 청양고추로 칼칼하고 시원한 간 맞추기",
        missionEn: "Snap Mission! 'I\'ll season with salted fermented shrimp and spicy green chili peppers.' Snap!",
        keyVocab: 'season with salted fermented shrimp',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'season with salted fermented shrimp', pron: 'season with salted fermented shrimp' },
          { role: 'db', en: 'and spicy green chili peppers.', pron: 'and spicy green chili peppers.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll season with salted fermented shrimp.', fullPron: 'I\'ll season with salted fermented shrimp', ko: 'season with salted fermented shrimp 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna season with salted fermented shrimp.', fullPron: 'I\'m gonna season with salted fermented shrimp', ko: 'season with salted fermented shrimp 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to season with salted fermented shrimp?', fullPron: 'You have to season with salted fermented shrimp?', ko: 'season with salted fermented shrimp 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['season with salted fermented shrimp', 'wash bean sprouts', 'poach soft egg']
        },
        fullEn: "I\'ll season with salted fermented shrimp and spicy green chili peppers.",
        fullPron: 'I\'ll + season with salted fermented shrimp + and spicy green chili peppers.',
        fullKo: '새우젓과 다진 청양고추로 칼칼하고 시원한 간 맞추기'
      },
      {
        stepTitle: 'SCENE 6 · Place Warm Cooked Rice in Earthen Pot',
        visualEmojis: '🍚 🍲 🥢',
        imagePath: '/images/kfood/ep28-thumb.jpg',
        actionNote: '뚝배기 밑바닥에 따뜻한 밥을 담고 콩나물국 붓기',
        coachKo: "코어 블록은 'place warm rice in earthen pot'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'place warm rice in earthen pot'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뚝배기 밑바닥에 따뜻한 밥을 담고 콩나물국 붓기",
        missionEn: "Snap Mission! 'We\'re gonna place warm rice in earthen pot and pour the piping hot soup.' Snap!",
        keyVocab: 'place warm rice in earthen pot',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'place warm rice in earthen pot', pron: 'place warm rice in earthen pot' },
          { role: 'db', en: 'and pour the piping hot soup.', pron: 'and pour the piping hot soup.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna place warm rice in earthen pot.', fullPron: 'We\'re gonna place warm rice in earthen pot', ko: 'place warm rice in earthen pot 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna place warm rice in earthen pot.', fullPron: 'I\'m gonna place warm rice in earthen pot', ko: 'place warm rice in earthen pot 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to place warm rice in earthen pot?', fullPron: 'You have to place warm rice in earthen pot?', ko: 'place warm rice in earthen pot 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['place warm rice in earthen pot', 'dice the squid', 'brew pollack broth']
        },
        fullEn: "We\'re gonna place warm rice in earthen pot and pour the piping hot soup.",
        fullPron: 'We\'re gonna + place warm rice in earthen pot + and pour the piping hot soup.',
        fullKo: '뚝배기 밑바닥에 따뜻한 밥을 담고 콩나물국 붓기'
      },
      {
        stepTitle: 'SCENE 7 · Prepare Warm Poached Egg (Suran)',
        visualEmojis: '🥚 🥣 🌿',
        imagePath: '/images/kfood/ep28-thumb.jpg',
        actionNote: '고소한 김가루와 참기름을 두른 부드러운 수란 곁들이기',
        coachKo: "코어 블록은 'serve with soft poached egg'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'serve with soft poached egg'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고소한 김가루와 참기름을 두른 부드러운 수란 곁들이기",
        missionEn: "Snap Mission! 'You have to serve with soft poached egg and crushed roasted seaweed.' Snap!",
        keyVocab: 'serve with soft poached egg',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'serve with soft poached egg', pron: 'serve with soft poached egg' },
          { role: 'db', en: 'and crushed roasted seaweed.', pron: 'and crushed roasted seaweed.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to serve with soft poached egg.', fullPron: 'You have to serve with soft poached egg', ko: 'serve with soft poached egg 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna serve with soft poached egg.', fullPron: 'I\'m gonna serve with soft poached egg', ko: 'serve with soft poached egg 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll serve with soft poached egg?', fullPron: 'I\'ll serve with soft poached egg?', ko: 'serve with soft poached egg 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['serve with soft poached egg', 'boil bean sprouts', 'season with shrimp']
        },
        fullEn: "You have to serve with soft poached egg and crushed roasted seaweed.",
        fullPron: 'You have to + serve with soft poached egg + and crushed roasted seaweed.',
        fullKo: '고소한 김가루와 참기름을 두른 부드러운 수란 곁들이기'
      },
      {
        stepTitle: 'SCENE 8 · Refreshing Crisp & Hangover-Curing',
        visualEmojis: '😋 🍚 💥',
        imagePath: '/images/kfood/ep28-thumb.jpg',
        actionNote: '속이 확 풀리는 개운한 국물과 아삭한 콩나물의 완벽한 조화',
        coachKo: "코어 블록은 'refreshing crisp and hangover-curing'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'refreshing crisp and hangover-curing'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 속이 확 풀리는 개운한 국물과 아삭한 콩나물의 완벽한 조화",
        missionEn: "Snap Mission! 'It\'s so refreshing crisp and hangover-curing with that revitalizing broth!' Snap!",
        keyVocab: 'refreshing crisp and hangover-curing',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'refreshing crisp and hangover-curing', pron: 'refreshing crisp and hangover-curing' },
          { role: 'db', en: 'with that revitalizing broth!', pron: 'with that revitalizing broth!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so refreshing crisp and hangover-curing.', fullPron: 'It\'s so refreshing crisp and hangover-curing', ko: 'refreshing crisp and hangover-curing 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to refreshing crisp and hangover-curing.', fullPron: 'You have to refreshing crisp and hangover-curing', ko: 'refreshing crisp and hangover-curing 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you refreshing crisp and hangover-curing?', fullPron: 'Can you refreshing crisp and hangover-curing?', ko: 'refreshing crisp and hangover-curing 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['refreshing crisp and hangover-curing', 'wash crisp sprouts', 'serve with egg']
        },
        fullEn: "It\'s so refreshing crisp and hangover-curing with that revitalizing broth!",
        fullPron: 'It\'s so + refreshing crisp and hangover-curing + with that revitalizing broth!',
        fullKo: '속이 확 풀리는 개운한 국물과 아삭한 콩나물의 완벽한 조화'
      }
    ]
  },
  // ==========================================
  // EP.29. 🍜 Classic Black Bean Noodles
  // ==========================================
  {
    id: 'jjajangmyeon',
    epNumber: 'EP.29',
    emoji: '🍜',
    shortTitle: '🍜 Classic Black Bean Noodles',
    title: 'How to Cook Classic Korean Black Bean Noodles (Jjajangmyeon)',
    ytTitle: 'How to Cook Classic Korean Jjajangmyeon in Easy English 🍜 | SoundBlock K-Cooking EP.29',
    thumbnailText: 'Glossy Jjajangmyeon! [We\'re gonna] + [stir-fry black bean paste with diced pork]',
    thumbnailImage: '/images/kfood/ep29-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s cook classic Korean Black Bean Noodles, glossy Jjajangmyeon with savory fried chunjang and pork, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for delicious Jjajangmyeon! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Fry Black Bean Chunjang in Oil',
        visualEmojis: '🫙 🍳 🔥',
        imagePath: '/images/kfood/ep29-thumb.jpg',
        actionNote: '춘장을 기름에 달달 볶아 특유의 떫은맛 없애고 윤기 내기',
        coachKo: "코어 블록은 'fry black bean paste in oil'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fry black bean paste in oil'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 춘장을 기름에 달달 볶아 특유의 떫은맛 없애고 윤기 내기",
        missionEn: "Snap Mission! 'You have to fry black bean paste in oil until fragrant and glossy.' Snap!",
        keyVocab: 'fry black bean paste in oil',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'fry black bean paste in oil', pron: 'fry black bean paste in oil' },
          { role: 'db', en: 'until fragrant and glossy.', pron: 'until fragrant and glossy.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to fry black bean paste in oil.', fullPron: 'You have to fry black bean paste in oil', ko: 'fry black bean paste in oil 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna fry black bean paste in oil.', fullPron: 'I\'m gonna fry black bean paste in oil', ko: 'fry black bean paste in oil 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll fry black bean paste in oil?', fullPron: 'I\'ll fry black bean paste in oil?', ko: 'fry black bean paste in oil 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['fry black bean paste in oil', 'dice the pork', 'boil the noodles']
        },
        fullEn: "You have to fry black bean paste in oil until fragrant and glossy.",
        fullPron: 'You have to + fry black bean paste in oil + until fragrant and glossy.',
        fullKo: '춘장을 기름에 달달 볶아 특유의 떫은맛 없애고 윤기 내기'
      },
      {
        stepTitle: 'SCENE 2 · Dice Pork Belly & Vegetables',
        visualEmojis: '🥩 🧅 🥔',
        imagePath: '/images/kfood/ep29-thumb.jpg',
        actionNote: '돼지고기와 양파, 양배추, 감자를 한 입 크기로 깍둑썰기',
        coachKo: "코어 블록은 'dice pork belly and vegetables'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'dice pork belly and vegetables'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 돼지고기와 양파, 양배추, 감자를 한 입 크기로 깍둑썰기",
        missionEn: "Snap Mission! 'I\'m gonna dice pork belly and vegetables into neat bite-sized cubes.' Snap!",
        keyVocab: 'dice pork belly and vegetables',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'dice pork belly and vegetables', pron: 'dice pork belly and vegetables' },
          { role: 'db', en: 'into neat bite-sized cubes.', pron: 'into neat bite-sized cubes.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna dice pork belly and vegetables.', fullPron: 'I\'m gonna dice pork belly and vegetables', ko: 'dice pork belly and vegetables 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to dice pork belly and vegetables.', fullPron: 'You have to dice pork belly and vegetables', ko: 'dice pork belly and vegetables 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna dice pork belly and vegetables?', fullPron: 'We\'re gonna dice pork belly and vegetables?', ko: 'dice pork belly and vegetables 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['dice pork belly and vegetables', 'fry black bean paste', 'mix potato starch']
        },
        fullEn: "I\'m gonna dice pork belly and vegetables into neat bite-sized cubes.",
        fullPron: 'I\'m gonna + dice pork belly and vegetables + into neat bite-sized cubes.',
        fullKo: '돼지고기와 양파, 양배추, 감자를 한 입 크기로 깍둑썰기'
      },
      {
        stepTitle: 'SCENE 3 · Sizzle Pork and Onions on High Heat',
        visualEmojis: '🔥 🥩 🧅',
        imagePath: '/images/kfood/ep29-thumb.jpg',
        actionNote: '달군 팬에 돼지고기와 양파를 센 불에 불맛 나게 볶기',
        coachKo: "코어 블록은 'sizzle pork and onions'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sizzle pork and onions'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달군 팬에 돼지고기와 양파를 센 불에 불맛 나게 볶기",
        missionEn: "Snap Mission! 'We\'re gonna sizzle pork and onions on blazing high heat.' Snap!",
        keyVocab: 'sizzle pork and onions',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'sizzle pork and onions', pron: 'sizzle pork and onions' },
          { role: 'db', en: 'on blazing high heat.', pron: 'on blazing high heat.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna sizzle pork and onions.', fullPron: 'We\'re gonna sizzle pork and onions', ko: 'sizzle pork and onions 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna sizzle pork and onions.', fullPron: 'I\'m gonna sizzle pork and onions', ko: 'sizzle pork and onions 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to sizzle pork and onions?', fullPron: 'You have to sizzle pork and onions?', ko: 'sizzle pork and onions 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['sizzle pork and onions', 'boil fresh noodles', 'stir in sauce']
        },
        fullEn: "We\'re gonna sizzle pork and onions on blazing high heat.",
        fullPron: 'We\'re gonna + sizzle pork and onions + on blazing high heat.',
        fullKo: '달군 팬에 돼지고기와 양파를 센 불에 불맛 나게 볶기'
      },
      {
        stepTitle: 'SCENE 4 · Pour in Fried Black Bean Paste',
        visualEmojis: '🫙 🍳 🖤',
        imagePath: '/images/kfood/ep29-thumb.jpg',
        actionNote: '볶아둔 춘장과 설탕, 굴소스를 넣고 채소와 함께 볶기',
        coachKo: "코어 블록은 'stir in fried black bean paste'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir in fried black bean paste'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 볶아둔 춘장과 설탕, 굴소스를 넣고 채소와 함께 볶기",
        missionEn: "Snap Mission! 'You have to stir in fried black bean paste with a touch of sweet sugar.' Snap!",
        keyVocab: 'stir in fried black bean paste',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'stir in fried black bean paste', pron: 'stir in fried black bean paste' },
          { role: 'db', en: 'with a touch of sweet sugar.', pron: 'with a touch of sweet sugar.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to stir in fried black bean paste.', fullPron: 'You have to stir in fried black bean paste', ko: 'stir in fried black bean paste 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna stir in fried black bean paste.', fullPron: 'I\'m gonna stir in fried black bean paste', ko: 'stir in fried black bean paste 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll stir in fried black bean paste?', fullPron: 'I\'ll stir in fried black bean paste?', ko: 'stir in fried black bean paste 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['stir in fried black bean paste', 'dice the pork', 'mix potato starch']
        },
        fullEn: "You have to stir in fried black bean paste with a touch of sweet sugar.",
        fullPron: 'You have to + stir in fried black bean paste + with a touch of sweet sugar.',
        fullKo: '볶아둔 춘장과 설탕, 굴소스를 넣고 채소와 함께 볶기'
      },
      {
        stepTitle: 'SCENE 5 · Pour Water & Simmer Smoothly',
        visualEmojis: '💧 🍲 ⏱️',
        imagePath: '/images/kfood/ep29-thumb.jpg',
        actionNote: '물을 자작하게 붓고 채소가 부드러워질 때까지 끓이기',
        coachKo: "코어 블록은 'pour water and simmer'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour water and simmer'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 물을 자작하게 붓고 채소가 부드러워질 때까지 끓이기",
        missionEn: "Snap Mission! 'I\'ll pour water and simmer until vegetables are tender.' Snap!",
        keyVocab: 'pour water and simmer',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'pour water and simmer', pron: 'pour water and simmer' },
          { role: 'db', en: 'until vegetables are tender.', pron: 'until vegetables are tender.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll pour water and simmer.', fullPron: 'I\'ll pour water and simmer', ko: 'pour water and simmer 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour water and simmer.', fullPron: 'I\'m gonna pour water and simmer', ko: 'pour water and simmer 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour water and simmer?', fullPron: 'You have to pour water and simmer?', ko: 'pour water and simmer 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['pour water and simmer', 'fry chunjang', 'boil noodles']
        },
        fullEn: "I\'ll pour water and simmer until vegetables are tender.",
        fullPron: 'I\'ll + pour water and simmer + until vegetables are tender.',
        fullKo: '물을 자작하게 붓고 채소가 부드러워질 때까지 끓이기'
      },
      {
        stepTitle: 'SCENE 6 · Thicken with Potato Starch Slurry',
        visualEmojis: '🥣 🥄 ✨',
        imagePath: '/images/kfood/ep29-thumb.jpg',
        actionNote: '물전분을 둘러 윤기가 자르르 흐르는 걸쭉한 소스 완성하기',
        coachKo: "코어 블록은 'thicken with potato starch slurry'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'thicken with potato starch slurry'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 물전분을 둘러 윤기가 자르르 흐르는 걸쭉한 소스 완성하기",
        missionEn: "Snap Mission! 'You have to thicken with potato starch slurry into a velvety rich sauce.' Snap!",
        keyVocab: 'thicken with potato starch slurry',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'thicken with potato starch slurry', pron: 'thicken with potato starch slurry' },
          { role: 'db', en: 'into a velvety rich sauce.', pron: 'into a velvety rich sauce.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to thicken with potato starch slurry.', fullPron: 'You have to thicken with potato starch slurry', ko: 'thicken with potato starch slurry 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna thicken with potato starch slurry.', fullPron: 'I\'m gonna thicken with potato starch slurry', ko: 'thicken with potato starch slurry 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna thicken with potato starch slurry?', fullPron: 'We\'re gonna thicken with potato starch slurry?', ko: 'thicken with potato starch slurry 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['thicken with potato starch slurry', 'dice the pork', 'sizzle on heat']
        },
        fullEn: "You have to thicken with potato starch slurry into a velvety rich sauce.",
        fullPron: 'You have to + thicken with potato starch slurry + into a velvety rich sauce.',
        fullKo: '물전분을 둘러 윤기가 자르르 흐르는 걸쭉한 소스 완성하기'
      },
      {
        stepTitle: 'SCENE 7 · Boil Chewy Fresh Wheat Noodles',
        visualEmojis: '🍜 💧 🥢',
        imagePath: '/images/kfood/ep29-thumb.jpg',
        actionNote: '탱글탱글한 중화면을 삶아 찬물에 헹군 뒤 그릇에 담기',
        coachKo: "코어 블록은 'boil chewy fresh wheat noodles'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'boil chewy fresh wheat noodles'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 탱글탱글한 중화면을 삶아 찬물에 헹군 뒤 그릇에 담기",
        missionEn: "Snap Mission! 'We\'re gonna boil chewy fresh wheat noodles until wonderfully bouncy.' Snap!",
        keyVocab: 'boil chewy fresh wheat noodles',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'boil chewy fresh wheat noodles', pron: 'boil chewy fresh wheat noodles' },
          { role: 'db', en: 'until wonderfully bouncy.', pron: 'until wonderfully bouncy.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna boil chewy fresh wheat noodles.', fullPron: 'We\'re gonna boil chewy fresh wheat noodles', ko: 'boil chewy fresh wheat noodles 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna boil chewy fresh wheat noodles.', fullPron: 'I\'m gonna boil chewy fresh wheat noodles', ko: 'boil chewy fresh wheat noodles 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to boil chewy fresh wheat noodles?', fullPron: 'You have to boil chewy fresh wheat noodles?', ko: 'boil chewy fresh wheat noodles 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['boil chewy fresh wheat noodles', 'fry black bean paste', 'thicken with starch']
        },
        fullEn: "We\'re gonna boil chewy fresh wheat noodles until wonderfully bouncy.",
        fullPron: 'We\'re gonna + boil chewy fresh wheat noodles + until wonderfully bouncy.',
        fullKo: '탱글탱글한 중화면을 삶아 찬물에 헹군 뒤 그릇에 담기'
      },
      {
        stepTitle: 'SCENE 8 · Savory Glossy & Addictively Sweet',
        visualEmojis: '😋 🍜 🖤',
        imagePath: '/images/kfood/ep29-thumb.jpg',
        actionNote: '짜장 소스를 듬뿍 얹어 오른손 왼손으로 신나게 비벼 맛보기',
        coachKo: "코어 블록은 'savory glossy and addictively sweet'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'savory glossy and addictively sweet'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 짜장 소스를 듬뿍 얹어 오른손 왼손으로 신나게 비벼 맛보기",
        missionEn: "Snap Mission! 'It\'s so savory glossy and addictively sweet with that perfect chewy bite!' Snap!",
        keyVocab: 'savory glossy and addictively sweet',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'savory glossy and addictively sweet', pron: 'savory glossy and addictively sweet' },
          { role: 'db', en: 'with that perfect chewy bite!', pron: 'with that perfect chewy bite!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so savory glossy and addictively sweet.', fullPron: 'It\'s so savory glossy and addictively sweet', ko: 'savory glossy and addictively sweet 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to savory glossy and addictively sweet.', fullPron: 'You have to savory glossy and addictively sweet', ko: 'savory glossy and addictively sweet 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you savory glossy and addictively sweet?', fullPron: 'Can you savory glossy and addictively sweet?', ko: 'savory glossy and addictively sweet 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['savory glossy and addictively sweet', 'fry chunjang', 'boil fresh noodles']
        },
        fullEn: "It\'s so savory glossy and addictively sweet with that perfect chewy bite!",
        fullPron: 'It\'s so + savory glossy and addictively sweet + with that perfect chewy bite!',
        fullKo: '짜장 소스를 듬뿍 얹어 오른손 왼손으로 신나게 비벼 맛보기'
      }
    ]
  },
  // ==========================================
  // EP.30. 🍜 Spicy Seafood Noodles
  // ==========================================
  {
    id: 'jjamppong',
    epNumber: 'EP.30',
    emoji: '🍜',
    shortTitle: '🍜 Spicy Seafood Noodles',
    title: 'How to Make Fiery Korean Spicy Seafood Noodles (Jjamppong)',
    ytTitle: 'How to Cook Fiery Korean Seafood Jjamppong in Easy English 🍜 | SoundBlock K-Cooking EP.30',
    thumbnailText: 'Fiery Seafood Jjamppong! [We\'re gonna] + [stir-fry fresh seafood with smoky chili oil]',
    thumbnailImage: '/images/kfood/ep30-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s cook fiery Korean Spicy Seafood Noodles with smoky chili oil, fresh squid, and hearty broth, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for spicy Jjamppong! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Prep Fresh Squid Shrimp & Mussels',
        visualEmojis: '🦑 🦐 🦪',
        imagePath: '/images/kfood/ep30-thumb.jpg',
        actionNote: '신선한 오징어 칼집 내고 새우와 홍합 깨끗이 손질하기',
        coachKo: "코어 블록은 'clean fresh squid and mussels'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'clean fresh squid and mussels'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 신선한 오징어 칼집 내고 새우와 홍합 깨끗이 손질하기",
        missionEn: "Snap Mission! 'You have to clean fresh squid and mussels in cold salted water.' Snap!",
        keyVocab: 'clean fresh squid and mussels',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'clean fresh squid and mussels', pron: 'clean fresh squid and mussels' },
          { role: 'db', en: 'in cold salted water.', pron: 'in cold salted water.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to clean fresh squid and mussels.', fullPron: 'You have to clean fresh squid and mussels', ko: 'clean fresh squid and mussels 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna clean fresh squid and mussels.', fullPron: 'I\'m gonna clean fresh squid and mussels', ko: 'clean fresh squid and mussels 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll clean fresh squid and mussels?', fullPron: 'I\'ll clean fresh squid and mussels?', ko: 'clean fresh squid and mussels 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['clean fresh squid and mussels', 'stir-fry with chili', 'boil the noodles']
        },
        fullEn: "You have to clean fresh squid and mussels in cold salted water.",
        fullPron: 'You have to + clean fresh squid and mussels + in cold salted water.',
        fullKo: '신선한 오징어 칼집 내고 새우와 홍합 깨끗이 손질하기'
      },
      {
        stepTitle: 'SCENE 2 · Sizzle Garlic & Chili in Smoking Wok',
        visualEmojis: '🍳 🔥 🌶️',
        imagePath: '/images/kfood/ep30-thumb.jpg',
        actionNote: '달군 웍에 파, 마늘, 고춧가루를 볶아 불향 나는 고추기름 내기',
        coachKo: "코어 블록은 'create smoky red chili oil'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'create smoky red chili oil'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달군 웍에 파, 마늘, 고춧가루를 볶아 불향 나는 고추기름 내기",
        missionEn: "Snap Mission! 'We\'re gonna create smoky red chili oil in a smoking hot wok.' Snap!",
        keyVocab: 'create smoky red chili oil',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'create smoky red chili oil', pron: 'create smoky red chili oil' },
          { role: 'db', en: 'in a smoking hot wok.', pron: 'in a smoking hot wok.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna create smoky red chili oil.', fullPron: 'We\'re gonna create smoky red chili oil', ko: 'create smoky red chili oil 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna create smoky red chili oil.', fullPron: 'I\'m gonna create smoky red chili oil', ko: 'create smoky red chili oil 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to create smoky red chili oil?', fullPron: 'You have to create smoky red chili oil?', ko: 'create smoky red chili oil 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['create smoky red chili oil', 'clean fresh squid', 'pour rich broth']
        },
        fullEn: "We\'re gonna create smoky red chili oil in a smoking hot wok.",
        fullPron: 'We\'re gonna + create smoky red chili oil + in a smoking hot wok.',
        fullKo: '달군 웍에 파, 마늘, 고춧가루를 볶아 불향 나는 고추기름 내기'
      },
      {
        stepTitle: 'SCENE 3 · Stir-Fry Pork and Sliced Cabbage',
        visualEmojis: '🥩 🥬 🔥',
        imagePath: '/images/kfood/ep30-thumb.jpg',
        actionNote: '돼지고기와 채 썬 양배추, 양파를 센 불에 빠르게 볶기',
        coachKo: "코어 블록은 'stir-fry pork and cabbage'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir-fry pork and cabbage'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 돼지고기와 채 썬 양배추, 양파를 센 불에 빠르게 볶기",
        missionEn: "Snap Mission! 'I\'m gonna stir-fry pork and cabbage to infuse smoky wok aroma.' Snap!",
        keyVocab: 'stir-fry pork and cabbage',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'stir-fry pork and cabbage', pron: 'stir-fry pork and cabbage' },
          { role: 'db', en: 'to infuse smoky wok aroma.', pron: 'to infuse smoky wok aroma.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna stir-fry pork and cabbage.', fullPron: 'I\'m gonna stir-fry pork and cabbage', ko: 'stir-fry pork and cabbage 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to stir-fry pork and cabbage.', fullPron: 'You have to stir-fry pork and cabbage', ko: 'stir-fry pork and cabbage 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll stir-fry pork and cabbage?', fullPron: 'I\'ll stir-fry pork and cabbage?', ko: 'stir-fry pork and cabbage 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['stir-fry pork and cabbage', 'clean the mussels', 'boil the noodles']
        },
        fullEn: "I\'m gonna stir-fry pork and cabbage to infuse smoky wok aroma.",
        fullPron: 'I\'m gonna + stir-fry pork and cabbage + to infuse smoky wok aroma.',
        fullKo: '돼지고기와 채 썬 양배추, 양파를 센 불에 빠르게 볶기'
      },
      {
        stepTitle: 'SCENE 4 · Toss in Fresh Prepared Seafood',
        visualEmojis: '🦑 🦐 🦪',
        imagePath: '/images/kfood/ep30-thumb.jpg',
        actionNote: '손질한 오징어, 홍합, 새우를 넣고 센 불에서 화르륵 볶기',
        coachKo: "코어 블록은 'toss in fresh seafood'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toss in fresh seafood'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 손질한 오징어, 홍합, 새우를 넣고 센 불에서 화르륵 볶기",
        missionEn: "Snap Mission! 'You have to toss in fresh seafood over blazing high heat.' Snap!",
        keyVocab: 'toss in fresh seafood',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'toss in fresh seafood', pron: 'toss in fresh seafood' },
          { role: 'db', en: 'over blazing high heat.', pron: 'over blazing high heat.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to toss in fresh seafood.', fullPron: 'You have to toss in fresh seafood', ko: 'toss in fresh seafood 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna toss in fresh seafood.', fullPron: 'I\'m gonna toss in fresh seafood', ko: 'toss in fresh seafood 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna toss in fresh seafood?', fullPron: 'We\'re gonna toss in fresh seafood?', ko: 'toss in fresh seafood 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['toss in fresh seafood', 'pour rich broth', 'season with sauce']
        },
        fullEn: "You have to toss in fresh seafood over blazing high heat.",
        fullPron: 'You have to + toss in fresh seafood + over blazing high heat.',
        fullKo: '손질한 오징어, 홍합, 새우를 넣고 센 불에서 화르륵 볶기'
      },
      {
        stepTitle: 'SCENE 5 · Pour Deep Rich Stock & Bring to Boil',
        visualEmojis: '💧 🍲 🔥',
        imagePath: '/images/kfood/ep30-thumb.jpg',
        actionNote: '육수를 붓고 해산물 향이 진하게 우러나도록 팔팔 끓이기',
        coachKo: "코어 블록은 'pour deep rich chicken stock'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour deep rich chicken stock'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 육수를 붓고 해산물 향이 진하게 우러나도록 팔팔 끓이기",
        missionEn: "Snap Mission! 'We\'re gonna pour deep rich chicken stock and bring to roaring boil.' Snap!",
        keyVocab: 'pour deep rich chicken stock',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'pour deep rich chicken stock', pron: 'pour deep rich chicken stock' },
          { role: 'db', en: 'and bring to roaring boil.', pron: 'and bring to roaring boil.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna pour deep rich chicken stock.', fullPron: 'We\'re gonna pour deep rich chicken stock', ko: 'pour deep rich chicken stock 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour deep rich chicken stock.', fullPron: 'I\'m gonna pour deep rich chicken stock', ko: 'pour deep rich chicken stock 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour deep rich chicken stock?', fullPron: 'You have to pour deep rich chicken stock?', ko: 'pour deep rich chicken stock 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['pour deep rich chicken stock', 'stir-fry pork', 'clean the squid']
        },
        fullEn: "We\'re gonna pour deep rich chicken stock and bring to roaring boil.",
        fullPron: 'We\'re gonna + pour deep rich chicken stock + and bring to roaring boil.',
        fullKo: '육수를 붓고 해산물 향이 진하게 우러나도록 팔팔 끓이기'
      },
      {
        stepTitle: 'SCENE 6 · Season with Soy Sauce & Oyster Sauce',
        visualEmojis: '🫙 🧂 ✨',
        imagePath: '/images/kfood/ep30-thumb.jpg',
        actionNote: '진간장과 굴소스, 후추로 입에 착 감기는 감칠맛 완성하기',
        coachKo: "코어 블록은 'season with savory oyster sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'season with savory oyster sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 진간장과 굴소스, 후추로 입에 착 감기는 감칠맛 완성하기",
        missionEn: "Snap Mission! 'I\'ll season with savory oyster sauce and a dash of black pepper.' Snap!",
        keyVocab: 'season with savory oyster sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'season with savory oyster sauce', pron: 'season with savory oyster sauce' },
          { role: 'db', en: 'and a dash of black pepper.', pron: 'and a dash of black pepper.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll season with savory oyster sauce.', fullPron: 'I\'ll season with savory oyster sauce', ko: 'season with savory oyster sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna season with savory oyster sauce.', fullPron: 'I\'m gonna season with savory oyster sauce', ko: 'season with savory oyster sauce 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to season with savory oyster sauce?', fullPron: 'You have to season with savory oyster sauce?', ko: 'season with savory oyster sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['season with savory oyster sauce', 'create chili oil', 'boil the noodles']
        },
        fullEn: "I\'ll season with savory oyster sauce and a dash of black pepper.",
        fullPron: 'I\'ll + season with savory oyster sauce + and a dash of black pepper.',
        fullKo: '진간장과 굴소스, 후추로 입에 착 감기는 감칠맛 완성하기'
      },
      {
        stepTitle: 'SCENE 7 · Cook Fresh Chewy Wheat Noodles',
        visualEmojis: '🍜 🥢 🥣',
        imagePath: '/images/kfood/ep30-thumb.jpg',
        actionNote: '삶은 탱글한 중화면을 찬물에 헹궈 온기를 담아 그릇에 깔기',
        coachKo: "코어 블록은 'cook fresh chewy noodles'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'cook fresh chewy noodles'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 삶은 탱글한 중화면을 찬물에 헹궈 온기를 담아 그릇에 깔기",
        missionEn: "Snap Mission! 'You have to cook fresh chewy noodles until perfectly springy.' Snap!",
        keyVocab: 'cook fresh chewy noodles',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'cook fresh chewy noodles', pron: 'cook fresh chewy noodles' },
          { role: 'db', en: 'until perfectly springy.', pron: 'until perfectly springy.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to cook fresh chewy noodles.', fullPron: 'You have to cook fresh chewy noodles', ko: 'cook fresh chewy noodles 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna cook fresh chewy noodles.', fullPron: 'I\'m gonna cook fresh chewy noodles', ko: 'cook fresh chewy noodles 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll cook fresh chewy noodles?', fullPron: 'I\'ll cook fresh chewy noodles?', ko: 'cook fresh chewy noodles 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['cook fresh chewy noodles', 'clean fresh seafood', 'pour rich stock']
        },
        fullEn: "You have to cook fresh chewy noodles until perfectly springy.",
        fullPron: 'You have to + cook fresh chewy noodles + until perfectly springy.',
        fullKo: '삶은 탱글한 중화면을 찬물에 헹궈 온기를 담아 그릇에 깔기'
      },
      {
        stepTitle: 'SCENE 8 · Fiery Smoky & Packed with Seafood',
        visualEmojis: '😋 🍜 🔥',
        imagePath: '/images/kfood/ep30-thumb.jpg',
        actionNote: '불향 가득 얼큰한 국물과 푸짐한 해산물을 후루룩 면치기',
        coachKo: "코어 블록은 'fiery smoky and seafood-packed'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fiery smoky and seafood-packed'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 불향 가득 얼큰한 국물과 푸짐한 해산물을 후루룩 면치기",
        missionEn: "Snap Mission! 'It\'s so fiery smoky and seafood-packed with incredible wok flavor!' Snap!",
        keyVocab: 'fiery smoky and seafood-packed',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'fiery smoky and seafood-packed', pron: 'fiery smoky and seafood-packed' },
          { role: 'db', en: 'with incredible wok flavor!', pron: 'with incredible wok flavor!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so fiery smoky and seafood-packed.', fullPron: 'It\'s so fiery smoky and seafood-packed', ko: 'fiery smoky and seafood-packed 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to fiery smoky and seafood-packed.', fullPron: 'You have to fiery smoky and seafood-packed', ko: 'fiery smoky and seafood-packed 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you fiery smoky and seafood-packed?', fullPron: 'Can you fiery smoky and seafood-packed?', ko: 'fiery smoky and seafood-packed 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['fiery smoky and seafood-packed', 'create smoky chili oil', 'cook fresh noodles']
        },
        fullEn: "It\'s so fiery smoky and seafood-packed with incredible wok flavor!",
        fullPron: 'It\'s so + fiery smoky and seafood-packed + with incredible wok flavor!',
        fullKo: '불향 가득 얼큰한 국물과 푸짐한 해산물을 후루룩 면치기'
      }
    ]
  },
  // ==========================================
  // EP.31. 🍜 Clam Knife-Cut Noodles
  // ==========================================
  {
    id: 'bajirak-kalguksu',
    epNumber: 'EP.31',
    emoji: '🍜',
    shortTitle: '🍜 Clam Knife-Cut Noodles',
    title: 'How to Cook Korean Handmade Clam Noodle Soup (Bajirak Kalguksu)',
    ytTitle: 'How to Cook Korean Clam Knife-Cut Noodles in Easy English 🍜 | SoundBlock K-Cooking EP.31',
    thumbnailText: 'Fresh Clam Kalguksu! [We\'re gonna] + [boil knife-cut noodles with sweet Manila clams]',
    thumbnailImage: '/images/kfood/ep31-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s cook refreshing Korean Handmade Clam Noodle Soup with fresh Manila clams and chewy noodles, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for comforting Clam Kalguksu! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Purge Manila Clams in Saltwater',
        visualEmojis: '🦪 💧 ⏳',
        imagePath: '/images/kfood/ep31-thumb.jpg',
        actionNote: '바지락을 소금물에 담가 어둡게 덮어 모래와 해감 완벽히 빼기',
        coachKo: "코어 블록은 'purge Manila clams in saltwater'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'purge Manila clams in saltwater'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 바지락을 소금물에 담가 어둡게 덮어 모래와 해감 완벽히 빼기",
        missionEn: "Snap Mission! 'You have to purge Manila clams in saltwater in the dark for two hours.' Snap!",
        keyVocab: 'purge Manila clams in saltwater',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'purge Manila clams in saltwater', pron: 'purge Manila clams in saltwater' },
          { role: 'db', en: 'in the dark for two hours.', pron: 'in the dark for two hours.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to purge Manila clams in saltwater.', fullPron: 'You have to purge Manila clams in saltwater', ko: 'purge Manila clams in saltwater 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna purge Manila clams in saltwater.', fullPron: 'I\'m gonna purge Manila clams in saltwater', ko: 'purge Manila clams in saltwater 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll purge Manila clams in saltwater?', fullPron: 'I\'ll purge Manila clams in saltwater?', ko: 'purge Manila clams in saltwater 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['purge Manila clams in saltwater', 'knead the dough', 'slice zucchini']
        },
        fullEn: "You have to purge Manila clams in saltwater in the dark for two hours.",
        fullPron: 'You have to + purge Manila clams in saltwater + in the dark for two hours.',
        fullKo: '바지락을 소금물에 담가 어둡게 덮어 모래와 해감 완벽히 빼기'
      },
      {
        stepTitle: 'SCENE 2 · Brew Golden Anchovy Kelp Broth',
        visualEmojis: '🐟 🍲 🌊',
        imagePath: '/images/kfood/ep31-thumb.jpg',
        actionNote: '멸치와 다시마, 마른 대파 뿌리로 맑고 깊은 황금빛 육수 내기',
        coachKo: "코어 블록은 'brew golden anchovy kelp broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'brew golden anchovy kelp broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 멸치와 다시마, 마른 대파 뿌리로 맑고 깊은 황금빛 육수 내기",
        missionEn: "Snap Mission! 'We\'re gonna brew golden anchovy kelp broth for that pristine sea flavor.' Snap!",
        keyVocab: 'brew golden anchovy kelp broth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'brew golden anchovy kelp broth', pron: 'brew golden anchovy kelp broth' },
          { role: 'db', en: 'for that pristine sea flavor.', pron: 'for that pristine sea flavor.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna brew golden anchovy kelp broth.', fullPron: 'We\'re gonna brew golden anchovy kelp broth', ko: 'brew golden anchovy kelp broth 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna brew golden anchovy kelp broth.', fullPron: 'I\'m gonna brew golden anchovy kelp broth', ko: 'brew golden anchovy kelp broth 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to brew golden anchovy kelp broth?', fullPron: 'You have to brew golden anchovy kelp broth?', ko: 'brew golden anchovy kelp broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['brew golden anchovy kelp broth', 'purge Manila clams', 'roll out dough']
        },
        fullEn: "We\'re gonna brew golden anchovy kelp broth for that pristine sea flavor.",
        fullPron: 'We\'re gonna + brew golden anchovy kelp broth + for that pristine sea flavor.',
        fullKo: '멸치와 다시마, 마른 대파 뿌리로 맑고 깊은 황금빛 육수 내기'
      },
      {
        stepTitle: 'SCENE 3 · Knead & Roll Chewy Wheat Dough',
        visualEmojis: '🌾 🧑‍🍳 🥢',
        imagePath: '/images/kfood/ep31-thumb.jpg',
        actionNote: '밀가루 반죽을 쫄깃하게 치댄 뒤 얇게 밀어 칼로 썰기',
        coachKo: "코어 블록은 'roll out homemade noodle dough'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'roll out homemade noodle dough'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 밀가루 반죽을 쫄깃하게 치댄 뒤 얇게 밀어 칼로 썰기",
        missionEn: "Snap Mission! 'I\'m gonna roll out homemade noodle dough and slice into thick ribbons.' Snap!",
        keyVocab: 'roll out homemade noodle dough',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'roll out homemade noodle dough', pron: 'roll out homemade noodle dough' },
          { role: 'db', en: 'and slice into thick ribbons.', pron: 'and slice into thick ribbons.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna roll out homemade noodle dough.', fullPron: 'I\'m gonna roll out homemade noodle dough', ko: 'roll out homemade noodle dough 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to roll out homemade noodle dough.', fullPron: 'You have to roll out homemade noodle dough', ko: 'roll out homemade noodle dough 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll roll out homemade noodle dough?', fullPron: 'I\'ll roll out homemade noodle dough?', ko: 'roll out homemade noodle dough 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['roll out homemade noodle dough', 'shake off starch', 'drop in clams']
        },
        fullEn: "I\'m gonna roll out homemade noodle dough and slice into thick ribbons.",
        fullPron: 'I\'m gonna + roll out homemade noodle dough + and slice into thick ribbons.',
        fullKo: '밀가루 반죽을 쫄깃하게 치댄 뒤 얇게 밀어 칼로 썰기'
      },
      {
        stepTitle: 'SCENE 4 · Shake Off Excess Flour Starch',
        visualEmojis: '🌾 💨 🥣',
        imagePath: '/images/kfood/ep31-thumb.jpg',
        actionNote: '국물이 텁텁해지지 않도록 면발의 덧가루를 가볍게 털어내기',
        coachKo: "코어 블록은 'shake off excess flour starch'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'shake off excess flour starch'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 국물이 텁텁해지지 않도록 면발의 덧가루를 가볍게 털어내기",
        missionEn: "Snap Mission! 'You have to shake off excess flour starch to keep the broth clear.' Snap!",
        keyVocab: 'shake off excess flour starch',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'shake off excess flour starch', pron: 'shake off excess flour starch' },
          { role: 'db', en: 'to keep the broth clear.', pron: 'to keep the broth clear.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to shake off excess flour starch.', fullPron: 'You have to shake off excess flour starch', ko: 'shake off excess flour starch 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna shake off excess flour starch.', fullPron: 'I\'m gonna shake off excess flour starch', ko: 'shake off excess flour starch 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna shake off excess flour starch?', fullPron: 'We\'re gonna shake off excess flour starch?', ko: 'shake off excess flour starch 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['shake off excess flour starch', 'brew golden broth', 'purge Manila clams']
        },
        fullEn: "You have to shake off excess flour starch to keep the broth clear.",
        fullPron: 'You have to + shake off excess flour starch + to keep the broth clear.',
        fullKo: '국물이 텁텁해지지 않도록 면발의 덧가루를 가볍게 털어내기'
      },
      {
        stepTitle: 'SCENE 5 · Drop in Fresh Plump Clams',
        visualEmojis: '🦪 🍲 🔥',
        imagePath: '/images/kfood/ep31-thumb.jpg',
        actionNote: '육수가 끓을 때 바지락을 넣고 입을 벌릴 때까지 끓이기',
        coachKo: "코어 블록은 'drop in fresh plump clams'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'drop in fresh plump clams'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 육수가 끓을 때 바지락을 넣고 입을 벌릴 때까지 끓이기",
        missionEn: "Snap Mission! 'We\'re gonna drop in fresh plump clams until all the shells pop open.' Snap!",
        keyVocab: 'drop in fresh plump clams',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'drop in fresh plump clams', pron: 'drop in fresh plump clams' },
          { role: 'db', en: 'until all the shells pop open.', pron: 'until all the shells pop open.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna drop in fresh plump clams.', fullPron: 'We\'re gonna drop in fresh plump clams', ko: 'drop in fresh plump clams 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna drop in fresh plump clams.', fullPron: 'I\'m gonna drop in fresh plump clams', ko: 'drop in fresh plump clams 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to drop in fresh plump clams?', fullPron: 'You have to drop in fresh plump clams?', ko: 'drop in fresh plump clams 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['drop in fresh plump clams', 'slice zucchini', 'shake off starch']
        },
        fullEn: "We\'re gonna drop in fresh plump clams until all the shells pop open.",
        fullPron: 'We\'re gonna + drop in fresh plump clams + until all the shells pop open.',
        fullKo: '육수가 끓을 때 바지락을 넣고 입을 벌릴 때까지 끓이기'
      },
      {
        stepTitle: 'SCENE 6 · Add Sliced Zucchini & Potatoes',
        visualEmojis: '🥒 🥔 🍲',
        imagePath: '/images/kfood/ep31-thumb.jpg',
        actionNote: '채 썬 애호박과 감자를 넣고 은은한 단맛 국물에 우려내기',
        coachKo: "코어 블록은 'add sliced zucchini and potatoes'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add sliced zucchini and potatoes'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 채 썬 애호박과 감자를 넣고 은은한 단맛 국물에 우려내기",
        missionEn: "Snap Mission! 'I\'ll add sliced zucchini and potatoes for natural sweet balance.' Snap!",
        keyVocab: 'add sliced zucchini and potatoes',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'add sliced zucchini and potatoes', pron: 'add sliced zucchini and potatoes' },
          { role: 'db', en: 'for natural sweet balance.', pron: 'for natural sweet balance.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll add sliced zucchini and potatoes.', fullPron: 'I\'ll add sliced zucchini and potatoes', ko: 'add sliced zucchini and potatoes 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna add sliced zucchini and potatoes.', fullPron: 'I\'m gonna add sliced zucchini and potatoes', ko: 'add sliced zucchini and potatoes 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to add sliced zucchini and potatoes?', fullPron: 'You have to add sliced zucchini and potatoes?', ko: 'add sliced zucchini and potatoes 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['add sliced zucchini and potatoes', 'roll out dough', 'brew anchovy broth']
        },
        fullEn: "I\'ll add sliced zucchini and potatoes for natural sweet balance.",
        fullPron: 'I\'ll + add sliced zucchini and potatoes + for natural sweet balance.',
        fullKo: '채 썬 애호박과 감자를 넣고 은은한 단맛 국물에 우려내기'
      },
      {
        stepTitle: 'SCENE 7 · Boil Knife-Cut Noodles Together',
        visualEmojis: '🍜 🔥 ⏱️',
        imagePath: '/images/kfood/ep31-thumb.jpg',
        actionNote: '칼국수 면을 넣고 면발이 투명하고 쫄깃해질 때까지 삶기',
        coachKo: "코어 블록은 'boil knife-cut noodles together'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'boil knife-cut noodles together'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 칼국수 면을 넣고 면발이 투명하고 쫄깃해질 때까지 삶기",
        missionEn: "Snap Mission! 'You have to boil knife-cut noodles together for five glorious minutes.' Snap!",
        keyVocab: 'boil knife-cut noodles together',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'boil knife-cut noodles together', pron: 'boil knife-cut noodles together' },
          { role: 'db', en: 'for five glorious minutes.', pron: 'for five glorious minutes.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to boil knife-cut noodles together.', fullPron: 'You have to boil knife-cut noodles together', ko: 'boil knife-cut noodles together 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna boil knife-cut noodles together.', fullPron: 'I\'m gonna boil knife-cut noodles together', ko: 'boil knife-cut noodles together 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll boil knife-cut noodles together?', fullPron: 'I\'ll boil knife-cut noodles together?', ko: 'boil knife-cut noodles together 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['boil knife-cut noodles together', 'drop in clams', 'shake off starch']
        },
        fullEn: "You have to boil knife-cut noodles together for five glorious minutes.",
        fullPron: 'You have to + boil knife-cut noodles together + for five glorious minutes.',
        fullKo: '칼국수 면을 넣고 면발이 투명하고 쫄깃해질 때까지 삶기'
      },
      {
        stepTitle: 'SCENE 8 · Refreshing Ocean Broth & Chewy Bite',
        visualEmojis: '😋 🍜 🦪',
        imagePath: '/images/kfood/ep31-thumb.jpg',
        actionNote: '바다향 가득 시원한 국물과 겉절이 김치를 척 얹어 먹는 맛',
        coachKo: "코어 블록은 'refreshing ocean broth and chewy bite'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'refreshing ocean broth and chewy bite'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 바다향 가득 시원한 국물과 겉절이 김치를 척 얹어 먹는 맛",
        missionEn: "Snap Mission! 'It\'s so refreshing ocean broth and chewy bite with spicy fresh kimchi!' Snap!",
        keyVocab: 'refreshing ocean broth and chewy bite',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'refreshing ocean broth and chewy bite', pron: 'refreshing ocean broth and chewy bite' },
          { role: 'db', en: 'with spicy fresh kimchi!', pron: 'with spicy fresh kimchi!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so refreshing ocean broth and chewy bite.', fullPron: 'It\'s so refreshing ocean broth and chewy bite', ko: 'refreshing ocean broth and chewy bite 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to refreshing ocean broth and chewy bite.', fullPron: 'You have to refreshing ocean broth and chewy bite', ko: 'refreshing ocean broth and chewy bite 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you refreshing ocean broth and chewy bite?', fullPron: 'Can you refreshing ocean broth and chewy bite?', ko: 'refreshing ocean broth and chewy bite 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['refreshing ocean broth and chewy bite', 'purge Manila clams', 'boil knife-cut noodles']
        },
        fullEn: "It\'s so refreshing ocean broth and chewy bite with spicy fresh kimchi!",
        fullPron: 'It\'s so + refreshing ocean broth and chewy bite + with spicy fresh kimchi!',
        fullKo: '바다향 가득 시원한 국물과 겉절이 김치를 척 얹어 먹는 맛'
      }
    ]
  },
  // ==========================================
  // EP.32. 🍜 Warm Banquet Noodles
  // ==========================================
  {
    id: 'janchi-guksu',
    epNumber: 'EP.32',
    emoji: '🍜',
    shortTitle: '🍜 Warm Banquet Noodles',
    title: 'How to Make Traditional Korean Warm Banquet Noodles (Janchi Guksu)',
    ytTitle: 'How to Cook Warm Korean Banquet Noodles in Easy English 🍜 | SoundBlock K-Cooking EP.32',
    thumbnailText: 'Comforting Janchi Guksu! [I\'m gonna] + [pour warm anchovy broth over thin somen noodles]',
    thumbnailImage: '/images/kfood/ep32-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s cook comforting Korean Warm Banquet Noodles with delicate somen noodles and aromatic anchovy broth, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for heartwarming Janchi Guksu! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Roast Dried Anchovies in Dry Pan',
        visualEmojis: '🐟 🍳 🔥',
        imagePath: '/images/kfood/ep32-thumb.jpg',
        actionNote: '국물 멸치의 내장을 떼고 마른 팬에 볶아 비린내 완전히 잡기',
        coachKo: "코어 블록은 'roast dried anchovies in pan'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'roast dried anchovies in pan'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 국물 멸치의 내장을 떼고 마른 팬에 볶아 비린내 완전히 잡기",
        missionEn: "Snap Mission! 'You have to roast dried anchovies in pan until smoky and aromatic.' Snap!",
        keyVocab: 'roast dried anchovies in pan',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'roast dried anchovies in pan', pron: 'roast dried anchovies in pan' },
          { role: 'db', en: 'until smoky and aromatic.', pron: 'until smoky and aromatic.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to roast dried anchovies in pan.', fullPron: 'You have to roast dried anchovies in pan', ko: 'roast dried anchovies in pan 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna roast dried anchovies in pan.', fullPron: 'I\'m gonna roast dried anchovies in pan', ko: 'roast dried anchovies in pan 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll roast dried anchovies in pan?', fullPron: 'I\'ll roast dried anchovies in pan?', ko: 'roast dried anchovies in pan 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['roast dried anchovies in pan', 'boil thin somen', 'slice zucchini']
        },
        fullEn: "You have to roast dried anchovies in pan until smoky and aromatic.",
        fullPron: 'You have to + roast dried anchovies in pan + until smoky and aromatic.',
        fullKo: '국물 멸치의 내장을 떼고 마른 팬에 볶아 비린내 완전히 잡기'
      },
      {
        stepTitle: 'SCENE 2 · Simmer Anchovy Broth with Radish',
        visualEmojis: '🧅 🤍 🍲',
        imagePath: '/images/kfood/ep32-thumb.jpg',
        actionNote: '다시마, 무, 대파를 넣고 맑고 개운하게 30분간 푹 우려내기',
        coachKo: "코어 블록은 'simmer fragrant anchovy broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'simmer fragrant anchovy broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 다시마, 무, 대파를 넣고 맑고 개운하게 30분간 푹 우려내기",
        missionEn: "Snap Mission! 'We\'re gonna simmer fragrant anchovy broth with sweet radish and kelp.' Snap!",
        keyVocab: 'simmer fragrant anchovy broth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'simmer fragrant anchovy broth', pron: 'simmer fragrant anchovy broth' },
          { role: 'db', en: 'with sweet radish and kelp.', pron: 'with sweet radish and kelp.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna simmer fragrant anchovy broth.', fullPron: 'We\'re gonna simmer fragrant anchovy broth', ko: 'simmer fragrant anchovy broth 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna simmer fragrant anchovy broth.', fullPron: 'I\'m gonna simmer fragrant anchovy broth', ko: 'simmer fragrant anchovy broth 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to simmer fragrant anchovy broth?', fullPron: 'You have to simmer fragrant anchovy broth?', ko: 'simmer fragrant anchovy broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['simmer fragrant anchovy broth', 'roast dried anchovies', 'fry egg strips']
        },
        fullEn: "We\'re gonna simmer fragrant anchovy broth with sweet radish and kelp.",
        fullPron: 'We\'re gonna + simmer fragrant anchovy broth + with sweet radish and kelp.',
        fullKo: '다시마, 무, 대파를 넣고 맑고 개운하게 30분간 푹 우려내기'
      },
      {
        stepTitle: 'SCENE 3 · Stir-Fry Zucchini & Carrot Matchsticks',
        visualEmojis: '🥒 🥕 🥢',
        imagePath: '/images/kfood/ep32-thumb.jpg',
        actionNote: '애호박과 당근을 가늘게 채 썰어 참기름에 살짝 볶아두기',
        coachKo: "코어 블록은 'stir-fry zucchini matchsticks'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir-fry zucchini matchsticks'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 애호박과 당근을 가늘게 채 썰어 참기름에 살짝 볶아두기",
        missionEn: "Snap Mission! 'I\'m gonna stir-fry zucchini matchsticks in fragrant sesame oil.' Snap!",
        keyVocab: 'stir-fry zucchini matchsticks',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'stir-fry zucchini matchsticks', pron: 'stir-fry zucchini matchsticks' },
          { role: 'db', en: 'in fragrant sesame oil.', pron: 'in fragrant sesame oil.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna stir-fry zucchini matchsticks.', fullPron: 'I\'m gonna stir-fry zucchini matchsticks', ko: 'stir-fry zucchini matchsticks 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to stir-fry zucchini matchsticks.', fullPron: 'You have to stir-fry zucchini matchsticks', ko: 'stir-fry zucchini matchsticks 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll stir-fry zucchini matchsticks?', fullPron: 'I\'ll stir-fry zucchini matchsticks?', ko: 'stir-fry zucchini matchsticks 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['stir-fry zucchini matchsticks', 'boil thin somen', 'mix soy sauce']
        },
        fullEn: "I\'m gonna stir-fry zucchini matchsticks in fragrant sesame oil.",
        fullPron: 'I\'m gonna + stir-fry zucchini matchsticks + in fragrant sesame oil.',
        fullKo: '애호박과 당근을 가늘게 채 썰어 참기름에 살짝 볶아두기'
      },
      {
        stepTitle: 'SCENE 4 · Fry Delicate Egg Jidan Strips',
        visualEmojis: '🍳 🟡 🔪',
        imagePath: '/images/kfood/ep32-thumb.jpg',
        actionNote: '계란 지단을 얇게 부쳐 식힌 뒤 고운 채로 썰어두기',
        coachKo: "코어 블록은 'slice thin yellow egg strips'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice thin yellow egg strips'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 계란 지단을 얇게 부쳐 식힌 뒤 고운 채로 썰어두기",
        missionEn: "Snap Mission! 'You have to slice thin yellow egg strips for traditional colorful garnish.' Snap!",
        keyVocab: 'slice thin yellow egg strips',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'slice thin yellow egg strips', pron: 'slice thin yellow egg strips' },
          { role: 'db', en: 'for traditional colorful garnish.', pron: 'for traditional colorful garnish.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to slice thin yellow egg strips.', fullPron: 'You have to slice thin yellow egg strips', ko: 'slice thin yellow egg strips 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice thin yellow egg strips.', fullPron: 'I\'m gonna slice thin yellow egg strips', ko: 'slice thin yellow egg strips 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna slice thin yellow egg strips?', fullPron: 'We\'re gonna slice thin yellow egg strips?', ko: 'slice thin yellow egg strips 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['slice thin yellow egg strips', 'roast anchovies', 'boil somen noodles']
        },
        fullEn: "You have to slice thin yellow egg strips for traditional colorful garnish.",
        fullPron: 'You have to + slice thin yellow egg strips + for traditional colorful garnish.',
        fullKo: '계란 지단을 얇게 부쳐 식힌 뒤 고운 채로 썰어두기'
      },
      {
        stepTitle: 'SCENE 5 · Mix Spicy Green Chili Soy Sauce',
        visualEmojis: '🫙 🌶️ 🧄',
        imagePath: '/images/kfood/ep32-thumb.jpg',
        actionNote: '간장, 고춧가루, 다진 파, 청양고추, 참기름으로 양념장 만들기',
        coachKo: "코어 블록은 'mix spicy seasoned soy sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix spicy seasoned soy sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 간장, 고춧가루, 다진 파, 청양고추, 참기름으로 양념장 만들기",
        missionEn: "Snap Mission! 'I\'ll mix spicy seasoned soy sauce with sesame and green chili.' Snap!",
        keyVocab: 'mix spicy seasoned soy sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'mix spicy seasoned soy sauce', pron: 'mix spicy seasoned soy sauce' },
          { role: 'db', en: 'with sesame and green chili.', pron: 'with sesame and green chili.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll mix spicy seasoned soy sauce.', fullPron: 'I\'ll mix spicy seasoned soy sauce', ko: 'mix spicy seasoned soy sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix spicy seasoned soy sauce.', fullPron: 'I\'m gonna mix spicy seasoned soy sauce', ko: 'mix spicy seasoned soy sauce 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix spicy seasoned soy sauce?', fullPron: 'You have to mix spicy seasoned soy sauce?', ko: 'mix spicy seasoned soy sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['mix spicy seasoned soy sauce', 'simmer broth', 'stir-fry zucchini']
        },
        fullEn: "I\'ll mix spicy seasoned soy sauce with sesame and green chili.",
        fullPron: 'I\'ll + mix spicy seasoned soy sauce + with sesame and green chili.',
        fullKo: '간장, 고춧가루, 다진 파, 청양고추, 참기름으로 양념장 만들기'
      },
      {
        stepTitle: 'SCENE 6 · Boil Delicate Thin Somen Noodles',
        visualEmojis: '🍜 💧 ⏳',
        imagePath: '/images/kfood/ep32-thumb.jpg',
        actionNote: '소면을 끓는 물에 삶고 찬물에 전분기를 빡빡 씻어내기',
        coachKo: "코어 블록은 'boil delicate thin somen noodles'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'boil delicate thin somen noodles'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 소면을 끓는 물에 삶고 찬물에 전분기를 빡빡 씻어내기",
        missionEn: "Snap Mission! 'We\'re gonna boil delicate thin somen noodles and rinse in icy water.' Snap!",
        keyVocab: 'boil delicate thin somen noodles',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'boil delicate thin somen noodles', pron: 'boil delicate thin somen noodles' },
          { role: 'db', en: 'and rinse in icy water.', pron: 'and rinse in icy water.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna boil delicate thin somen noodles.', fullPron: 'We\'re gonna boil delicate thin somen noodles', ko: 'boil delicate thin somen noodles 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna boil delicate thin somen noodles.', fullPron: 'I\'m gonna boil delicate thin somen noodles', ko: 'boil delicate thin somen noodles 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to boil delicate thin somen noodles?', fullPron: 'You have to boil delicate thin somen noodles?', ko: 'boil delicate thin somen noodles 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['boil delicate thin somen noodles', 'roast anchovies', 'fry egg strips']
        },
        fullEn: "We\'re gonna boil delicate thin somen noodles and rinse in icy water.",
        fullPron: 'We\'re gonna + boil delicate thin somen noodles + and rinse in icy water.',
        fullKo: '소면을 끓는 물에 삶고 찬물에 전분기를 빡빡 씻어내기'
      },
      {
        stepTitle: 'SCENE 7 · Pour Piping Hot Broth Over Noodles',
        visualEmojis: '🥣 🍲 ✨',
        imagePath: '/images/kfood/ep32-thumb.jpg',
        actionNote: '그릇에 면을 말고 뜨거운 멸치 육수를 정갈하게 붓기',
        coachKo: "코어 블록은 'pour piping hot anchovy broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour piping hot anchovy broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 그릇에 면을 말고 뜨거운 멸치 육수를 정갈하게 붓기",
        missionEn: "Snap Mission! 'You have to pour piping hot anchovy broth generously over the noodles.' Snap!",
        keyVocab: 'pour piping hot anchovy broth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'pour piping hot anchovy broth', pron: 'pour piping hot anchovy broth' },
          { role: 'db', en: 'generously over the noodles.', pron: 'generously over the noodles.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to pour piping hot anchovy broth.', fullPron: 'You have to pour piping hot anchovy broth', ko: 'pour piping hot anchovy broth 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour piping hot anchovy broth.', fullPron: 'I\'m gonna pour piping hot anchovy broth', ko: 'pour piping hot anchovy broth 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll pour piping hot anchovy broth?', fullPron: 'I\'ll pour piping hot anchovy broth?', ko: 'pour piping hot anchovy broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['pour piping hot anchovy broth', 'stir-fry zucchini', 'mix seasoned sauce']
        },
        fullEn: "You have to pour piping hot anchovy broth generously over the noodles.",
        fullPron: 'You have to + pour piping hot anchovy broth + generously over the noodles.',
        fullKo: '그릇에 면을 말고 뜨거운 멸치 육수를 정갈하게 붓기'
      },
      {
        stepTitle: 'SCENE 8 · Warm Pure & Deeply Comforting',
        visualEmojis: '😋 🍜 💛',
        imagePath: '/images/kfood/ep32-thumb.jpg',
        actionNote: '호박과 지단을 고명으로 얹고 양념장을 풀어 후루룩 넘기는 맛',
        coachKo: "코어 블록은 'warm pure and deeply comforting'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'warm pure and deeply comforting'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 호박과 지단을 고명으로 얹고 양념장을 풀어 후루룩 넘기는 맛",
        missionEn: "Snap Mission! 'It\'s so warm pure and deeply comforting with soulful home flavor!' Snap!",
        keyVocab: 'warm pure and deeply comforting',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'warm pure and deeply comforting', pron: 'warm pure and deeply comforting' },
          { role: 'db', en: 'with soulful home flavor!', pron: 'with soulful home flavor!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so warm pure and deeply comforting.', fullPron: 'It\'s so warm pure and deeply comforting', ko: 'warm pure and deeply comforting 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to warm pure and deeply comforting.', fullPron: 'You have to warm pure and deeply comforting', ko: 'warm pure and deeply comforting 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you warm pure and deeply comforting?', fullPron: 'Can you warm pure and deeply comforting?', ko: 'warm pure and deeply comforting 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['warm pure and deeply comforting', 'roast dried anchovies', 'pour hot broth']
        },
        fullEn: "It\'s so warm pure and deeply comforting with soulful home flavor!",
        fullPron: 'It\'s so + warm pure and deeply comforting + with soulful home flavor!',
        fullKo: '호박과 지단을 고명으로 얹고 양념장을 풀어 후루룩 넘기는 맛'
      }
    ]
  },
  // ==========================================
  // EP.33. 🥢 Spicy Cold Mixed Noodles
  // ==========================================
  {
    id: 'bibim-guksu',
    epNumber: 'EP.33',
    emoji: '🥢',
    shortTitle: '🥢 Spicy Cold Mixed Noodles',
    title: 'How to Make Spicy Sweet Korean Cold Mixed Noodles (Bibim Guksu)',
    ytTitle: 'How to Make Spicy Korean Mixed Noodles in Easy English 🥢 | SoundBlock K-Cooking EP.33',
    thumbnailText: 'Spicy Sweet Bibim Guksu! [I\'m gonna] + [toss cold somen noodles in sweet chili sauce]',
    thumbnailImage: '/images/kfood/ep33-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s toss vibrant Korean Cold Mixed Noodles with spicy sweet gochujang sauce, crisp cucumber, and boiled egg, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for zesty Bibim Guksu! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Mix Fiery Sweet Gochujang Sauce',
        visualEmojis: '🌶️ 🫙 🍯',
        imagePath: '/images/kfood/ep33-thumb.jpg',
        actionNote: '고추장, 식초, 설탕, 다진 마늘, 매실청을 섞어 특제 비빔장 완성',
        coachKo: "코어 블록은 'mix sweet and tangy chili sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix sweet and tangy chili sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고추장, 식초, 설탕, 다진 마늘, 매실청을 섞어 특제 비빔장 완성",
        missionEn: "Snap Mission! 'You have to mix sweet and tangy chili sauce with vinegar and honey.' Snap!",
        keyVocab: 'mix sweet and tangy chili sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'mix sweet and tangy chili sauce', pron: 'mix sweet and tangy chili sauce' },
          { role: 'db', en: 'with vinegar and honey.', pron: 'with vinegar and honey.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to mix sweet and tangy chili sauce.', fullPron: 'You have to mix sweet and tangy chili sauce', ko: 'mix sweet and tangy chili sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix sweet and tangy chili sauce.', fullPron: 'I\'m gonna mix sweet and tangy chili sauce', ko: 'mix sweet and tangy chili sauce 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll mix sweet and tangy chili sauce?', fullPron: 'I\'ll mix sweet and tangy chili sauce?', ko: 'mix sweet and tangy chili sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['mix sweet and tangy chili sauce', 'boil somen noodles', 'julienne cucumber']
        },
        fullEn: "You have to mix sweet and tangy chili sauce with vinegar and honey.",
        fullPron: 'You have to + mix sweet and tangy chili sauce + with vinegar and honey.',
        fullKo: '고추장, 식초, 설탕, 다진 마늘, 매실청을 섞어 특제 비빔장 완성'
      },
      {
        stepTitle: 'SCENE 2 · Julienne Refreshing Crisp Cucumber',
        visualEmojis: '🥒 🔪 🥣',
        imagePath: '/images/kfood/ep33-thumb.jpg',
        actionNote: '아삭한 오이와 양배추를 얇고 곱게 채 썰어 아삭함 살리기',
        coachKo: "코어 블록은 'julienne crisp fresh cucumber'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'julienne crisp fresh cucumber'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 아삭한 오이와 양배추를 얇고 곱게 채 썰어 아삭함 살리기",
        missionEn: "Snap Mission! 'I\'m gonna julienne crisp fresh cucumber into delicate refreshing strips.' Snap!",
        keyVocab: 'julienne crisp fresh cucumber',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'julienne crisp fresh cucumber', pron: 'julienne crisp fresh cucumber' },
          { role: 'db', en: 'into delicate refreshing strips.', pron: 'into delicate refreshing strips.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna julienne crisp fresh cucumber.', fullPron: 'I\'m gonna julienne crisp fresh cucumber', ko: 'julienne crisp fresh cucumber 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to julienne crisp fresh cucumber.', fullPron: 'You have to julienne crisp fresh cucumber', ko: 'julienne crisp fresh cucumber 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna julienne crisp fresh cucumber?', fullPron: 'We\'re gonna julienne crisp fresh cucumber?', ko: 'julienne crisp fresh cucumber 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['julienne crisp fresh cucumber', 'mix chili sauce', 'boil somen noodles']
        },
        fullEn: "I\'m gonna julienne crisp fresh cucumber into delicate refreshing strips.",
        fullPron: 'I\'m gonna + julienne crisp fresh cucumber + into delicate refreshing strips.',
        fullKo: '아삭한 오이와 양배추를 얇고 곱게 채 썰어 아삭함 살리기'
      },
      {
        stepTitle: 'SCENE 3 · Chop Well-Fermented Kimchi Finely',
        visualEmojis: '🥬 🔪 🫙',
        imagePath: '/images/kfood/ep33-thumb.jpg',
        actionNote: '잘 익은 신김치를 송송 썰어 설탕과 참기름에 조물조물 무치기',
        coachKo: "코어 블록은 'chop aged sour kimchi finely'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'chop aged sour kimchi finely'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 잘 익은 신김치를 송송 썰어 설탕과 참기름에 조물조물 무치기",
        missionEn: "Snap Mission! 'We\'re gonna chop aged sour kimchi finely and toss with sesame oil.' Snap!",
        keyVocab: 'chop aged sour kimchi finely',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'chop aged sour kimchi finely', pron: 'chop aged sour kimchi finely' },
          { role: 'db', en: 'and toss with sesame oil.', pron: 'and toss with sesame oil.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna chop aged sour kimchi finely.', fullPron: 'We\'re gonna chop aged sour kimchi finely', ko: 'chop aged sour kimchi finely 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna chop aged sour kimchi finely.', fullPron: 'I\'m gonna chop aged sour kimchi finely', ko: 'chop aged sour kimchi finely 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to chop aged sour kimchi finely?', fullPron: 'You have to chop aged sour kimchi finely?', ko: 'chop aged sour kimchi finely 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['chop aged sour kimchi finely', 'boil the egg', 'rinse in icy water']
        },
        fullEn: "We\'re gonna chop aged sour kimchi finely and toss with sesame oil.",
        fullPron: 'We\'re gonna + chop aged sour kimchi finely + and toss with sesame oil.',
        fullKo: '잘 익은 신김치를 송송 썰어 설탕과 참기름에 조물조물 무치기'
      },
      {
        stepTitle: 'SCENE 4 · Boil Somen Noodles to Al Dente',
        visualEmojis: '🍜 🔥 ⏱️',
        imagePath: '/images/kfood/ep33-thumb.jpg',
        actionNote: '끓는 물에 소면을 삶다가 찬물을 세 번 끼얹으며 쫄깃하게 익히기',
        coachKo: "코어 블록은 'boil somen noodles until al dente'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'boil somen noodles until al dente'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 끓는 물에 소면을 삶다가 찬물을 세 번 끼얹으며 쫄깃하게 익히기",
        missionEn: "Snap Mission! 'You have to boil somen noodles until al dente adding cold water twice.' Snap!",
        keyVocab: 'boil somen noodles until al dente',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'boil somen noodles until al dente', pron: 'boil somen noodles until al dente' },
          { role: 'db', en: 'adding cold water twice.', pron: 'adding cold water twice.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to boil somen noodles until al dente.', fullPron: 'You have to boil somen noodles until al dente', ko: 'boil somen noodles until al dente 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll boil somen noodles until al dente.', fullPron: 'I\'ll boil somen noodles until al dente', ko: 'boil somen noodles until al dente 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna boil somen noodles until al dente?', fullPron: 'I\'m gonna boil somen noodles until al dente?', ko: 'boil somen noodles until al dente 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['boil somen noodles until al dente', 'mix chili sauce', 'julienne cucumber']
        },
        fullEn: "You have to boil somen noodles until al dente adding cold water twice.",
        fullPron: 'You have to + boil somen noodles until al dente + adding cold water twice.',
        fullKo: '끓는 물에 소면을 삶다가 찬물을 세 번 끼얹으며 쫄깃하게 익히기'
      },
      {
        stepTitle: 'SCENE 5 · Vigorously Rinse in Icy Water',
        visualEmojis: '❄️ 💧 🥢',
        imagePath: '/images/kfood/ep33-thumb.jpg',
        actionNote: '삶아낸 국수를 얼음물에서 전분기가 빠지도록 팍팍 치대기',
        coachKo: "코어 블록은 'rinse vigorously in icy water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'rinse vigorously in icy water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 삶아낸 국수를 얼음물에서 전분기가 빠지도록 팍팍 치대기",
        missionEn: "Snap Mission! 'I\'ll rinse vigorously in icy water so noodles get springy.' Snap!",
        keyVocab: 'rinse vigorously in icy water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'rinse vigorously in icy water', pron: 'rinse vigorously in icy water' },
          { role: 'db', en: 'so noodles get springy.', pron: 'so noodles get springy.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll rinse vigorously in icy water.', fullPron: 'I\'ll rinse vigorously in icy water', ko: 'rinse vigorously in icy water 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna rinse vigorously in icy water.', fullPron: 'I\'m gonna rinse vigorously in icy water', ko: 'rinse vigorously in icy water 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to rinse vigorously in icy water?', fullPron: 'You have to rinse vigorously in icy water?', ko: 'rinse vigorously in icy water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['rinse vigorously in icy water', 'chop sour kimchi', 'toss with sauce']
        },
        fullEn: "I\'ll rinse vigorously in icy water so noodles get springy.",
        fullPron: 'I\'ll + rinse vigorously in icy water + so noodles get springy.',
        fullKo: '삶아낸 국수를 얼음물에서 전분기가 빠지도록 팍팍 치대기'
      },
      {
        stepTitle: 'SCENE 6 · Toss Noodles Hand-in-Hand with Sauce',
        visualEmojis: '🧑‍🍳 🥢 🌶️',
        imagePath: '/images/kfood/ep33-thumb.jpg',
        actionNote: '양념장과 신김치를 넣고 손으로 조물조물 맛있게 비비기',
        coachKo: "코어 블록은 'toss noodles with sweet sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toss noodles with sweet sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양념장과 신김치를 넣고 손으로 조물조물 맛있게 비비기",
        missionEn: "Snap Mission! 'We\'re gonna toss noodles with sweet sauce until every strand is coated.' Snap!",
        keyVocab: 'toss noodles with sweet sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'toss noodles with sweet sauce', pron: 'toss noodles with sweet sauce' },
          { role: 'db', en: 'until every strand is coated.', pron: 'until every strand is coated.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna toss noodles with sweet sauce.', fullPron: 'We\'re gonna toss noodles with sweet sauce', ko: 'toss noodles with sweet sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna toss noodles with sweet sauce.', fullPron: 'I\'m gonna toss noodles with sweet sauce', ko: 'toss noodles with sweet sauce 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to toss noodles with sweet sauce?', fullPron: 'You have to toss noodles with sweet sauce?', ko: 'toss noodles with sweet sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['toss noodles with sweet sauce', 'boil somen noodles', 'julienne cucumber']
        },
        fullEn: "We\'re gonna toss noodles with sweet sauce until every strand is coated.",
        fullPron: 'We\'re gonna + toss noodles with sweet sauce + until every strand is coated.',
        fullKo: '양념장과 신김치를 넣고 손으로 조물조물 맛있게 비비기'
      },
      {
        stepTitle: 'SCENE 7 · Crown with Boiled Egg & Crushed Sesame',
        visualEmojis: '🥚 🌿 ✨',
        imagePath: '/images/kfood/ep33-thumb.jpg',
        actionNote: '삶은 계란 반 쪽, 오이채, 고소한 깨소금을 듬뿍 얹기',
        coachKo: "코어 블록은 'crown with boiled egg half'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'crown with boiled egg half'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 삶은 계란 반 쪽, 오이채, 고소한 깨소금을 듬뿍 얹기",
        missionEn: "Snap Mission! 'You have to crown with boiled egg half and heaps of crushed sesame.' Snap!",
        keyVocab: 'crown with boiled egg half',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'crown with boiled egg half', pron: 'crown with boiled egg half' },
          { role: 'db', en: 'and heaps of crushed sesame.', pron: 'and heaps of crushed sesame.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to crown with boiled egg half.', fullPron: 'You have to crown with boiled egg half', ko: 'crown with boiled egg half 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna crown with boiled egg half.', fullPron: 'I\'m gonna crown with boiled egg half', ko: 'crown with boiled egg half 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll crown with boiled egg half?', fullPron: 'I\'ll crown with boiled egg half?', ko: 'crown with boiled egg half 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['crown with boiled egg half', 'mix chili sauce', 'rinse in icy water']
        },
        fullEn: "You have to crown with boiled egg half and heaps of crushed sesame.",
        fullPron: 'You have to + crown with boiled egg half + and heaps of crushed sesame.',
        fullKo: '삶은 계란 반 쪽, 오이채, 고소한 깨소금을 듬뿍 얹기'
      },
      {
        stepTitle: 'SCENE 8 · Tangy Spicy & Refreshingly Addictive',
        visualEmojis: '😋 🥢 💥',
        imagePath: '/images/kfood/ep33-thumb.jpg',
        actionNote: '매콤달콤새콤 입맛이 확 도는 양념과 쫄깃한 면발의 폭발적 케미',
        coachKo: "코어 블록은 'tangy spicy and refreshingly addictive'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'tangy spicy and refreshingly addictive'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 매콤달콤새콤 입맛이 확 도는 양념과 쫄깃한 면발의 폭발적 케미",
        missionEn: "Snap Mission! 'It\'s so tangy spicy and refreshingly addictive with irresistible lively kick!' Snap!",
        keyVocab: 'tangy spicy and refreshingly addictive',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'tangy spicy and refreshingly addictive', pron: 'tangy spicy and refreshingly addictive' },
          { role: 'db', en: 'with irresistible lively kick!', pron: 'with irresistible lively kick!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so tangy spicy and refreshingly addictive.', fullPron: 'It\'s so tangy spicy and refreshingly addictive', ko: 'tangy spicy and refreshingly addictive 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to tangy spicy and refreshingly addictive.', fullPron: 'You have to tangy spicy and refreshingly addictive', ko: 'tangy spicy and refreshingly addictive 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you tangy spicy and refreshingly addictive?', fullPron: 'Can you tangy spicy and refreshingly addictive?', ko: 'tangy spicy and refreshingly addictive 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['tangy spicy and refreshingly addictive', 'mix sweet chili sauce', 'toss with sauce']
        },
        fullEn: "It\'s so tangy spicy and refreshingly addictive with irresistible lively kick!",
        fullPron: 'It\'s so + tangy spicy and refreshingly addictive + with irresistible lively kick!',
        fullKo: '매콤달콤새콤 입맛이 확 도는 양념과 쫄깃한 면발의 폭발적 케미'
      }
    ]
  },
  // ==========================================
  // EP.34. ❄️ Chilled Cold Noodles
  // ==========================================
  {
    id: 'mul-naengmyeon',
    epNumber: 'EP.34',
    emoji: '❄️',
    shortTitle: '❄️ Chilled Cold Noodles',
    title: 'How to Enjoy Icy Korean Cold Buckwheat Noodles (Mul-Naengmyeon)',
    ytTitle: 'How to Make Icy Korean Cold Noodles in Easy English ❄️ | SoundBlock K-Cooking EP.34',
    thumbnailText: 'Icy Cold Mul-Naengmyeon! [We\'re gonna] + [pour slushy beef dongchimi broth over buckwheat noodles]',
    thumbnailImage: '/images/kfood/ep34-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s assemble refreshing Korean Chilled Cold Noodles with slushy beef dongchimi broth and chewy buckwheat noodles, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for summer-favorite Mul-Naengmyeon! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Freeze Beef & Dongchimi Broth Slushy',
        visualEmojis: '❄️ 🥣 ⏳',
        imagePath: '/images/kfood/ep34-thumb.jpg',
        actionNote: '양지 육수와 동치미 국물을 섞어 살얼음이 얼도록 냉동실에 두기',
        coachKo: "코어 블록은 'chill broth into refreshing slushy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'chill broth into refreshing slushy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양지 육수와 동치미 국물을 섞어 살얼음이 얼도록 냉동실에 두기",
        missionEn: "Snap Mission! 'You have to chill broth into refreshing slushy in freezer for two hours.' Snap!",
        keyVocab: 'chill broth into refreshing slushy',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'chill broth into refreshing slushy', pron: 'chill broth into refreshing slushy' },
          { role: 'db', en: 'in freezer for two hours.', pron: 'in freezer for two hours.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to chill broth into refreshing slushy.', fullPron: 'You have to chill broth into refreshing slushy', ko: 'chill broth into refreshing slushy 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna chill broth into refreshing slushy.', fullPron: 'I\'m gonna chill broth into refreshing slushy', ko: 'chill broth into refreshing slushy 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll chill broth into refreshing slushy?', fullPron: 'I\'ll chill broth into refreshing slushy?', ko: 'chill broth into refreshing slushy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['chill broth into refreshing slushy', 'boil buckwheat noodles', 'slice pickling radish']
        },
        fullEn: "You have to chill broth into refreshing slushy in freezer for two hours.",
        fullPron: 'You have to + chill broth into refreshing slushy + in freezer for two hours.',
        fullKo: '양지 육수와 동치미 국물을 섞어 살얼음이 얼도록 냉동실에 두기'
      },
      {
        stepTitle: 'SCENE 2 · Thinly Slice Radish and Pickled Cucumber',
        visualEmojis: '🤍 🥒 🧂',
        imagePath: '/images/kfood/ep34-thumb.jpg',
        actionNote: '무와 오이를 얇게 썰어 식초와 설탕에 절여 새콤하게 만들기',
        coachKo: "코어 블록은 'pickle sliced radish and cucumber'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pickle sliced radish and cucumber'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 무와 오이를 얇게 썰어 식초와 설탕에 절여 새콤하게 만들기",
        missionEn: "Snap Mission! 'I\'m gonna pickle sliced radish and cucumber in sweet vinegar brine.' Snap!",
        keyVocab: 'pickle sliced radish and cucumber',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'pickle sliced radish and cucumber', pron: 'pickle sliced radish and cucumber' },
          { role: 'db', en: 'in sweet vinegar brine.', pron: 'in sweet vinegar brine.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pickle sliced radish and cucumber.', fullPron: 'I\'m gonna pickle sliced radish and cucumber', ko: 'pickle sliced radish and cucumber 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to pickle sliced radish and cucumber.', fullPron: 'You have to pickle sliced radish and cucumber', ko: 'pickle sliced radish and cucumber 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna pickle sliced radish and cucumber?', fullPron: 'We\'re gonna pickle sliced radish and cucumber?', ko: 'pickle sliced radish and cucumber 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['pickle sliced radish and cucumber', 'chill broth slushy', 'boil buckwheat noodles']
        },
        fullEn: "I\'m gonna pickle sliced radish and cucumber in sweet vinegar brine.",
        fullPron: 'I\'m gonna + pickle sliced radish and cucumber + in sweet vinegar brine.',
        fullKo: '무와 오이를 얇게 썰어 식초와 설탕에 절여 새콤하게 만들기'
      },
      {
        stepTitle: 'SCENE 3 · Boil Chewy Buckwheat Noodles',
        visualEmojis: '🍜 🔥 ⏱️',
        imagePath: '/images/kfood/ep34-thumb.jpg',
        actionNote: '메밀 냉면 면발을 가닥가닥 풀어 끓는 물에 딱 50초간 삶기',
        coachKo: "코어 블록은 'boil chewy buckwheat noodles'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'boil chewy buckwheat noodles'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 메밀 냉면 면발을 가닥가닥 풀어 끓는 물에 딱 50초간 삶기",
        missionEn: "Snap Mission! 'We\'re gonna boil chewy buckwheat noodles for exactly fifty seconds.' Snap!",
        keyVocab: 'boil chewy buckwheat noodles',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'boil chewy buckwheat noodles', pron: 'boil chewy buckwheat noodles' },
          { role: 'db', en: 'for exactly fifty seconds.', pron: 'for exactly fifty seconds.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna boil chewy buckwheat noodles.', fullPron: 'We\'re gonna boil chewy buckwheat noodles', ko: 'boil chewy buckwheat noodles 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna boil chewy buckwheat noodles.', fullPron: 'I\'m gonna boil chewy buckwheat noodles', ko: 'boil chewy buckwheat noodles 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to boil chewy buckwheat noodles?', fullPron: 'You have to boil chewy buckwheat noodles?', ko: 'boil chewy buckwheat noodles 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['boil chewy buckwheat noodles', 'rinse in ice water', 'slice boiled egg']
        },
        fullEn: "We\'re gonna boil chewy buckwheat noodles for exactly fifty seconds.",
        fullPron: 'We\'re gonna + boil chewy buckwheat noodles + for exactly fifty seconds.',
        fullKo: '메밀 냉면 면발을 가닥가닥 풀어 끓는 물에 딱 50초간 삶기'
      },
      {
        stepTitle: 'SCENE 4 · Shock and Wash in Ice-Cold Water',
        visualEmojis: '🧊 💧 🥢',
        imagePath: '/images/kfood/ep34-thumb.jpg',
        actionNote: '삶자마자 얼음물에 담가 손으로 전분을 씻어 쫄깃함 극대화하기',
        coachKo: "코어 블록은 'shock in ice-cold water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'shock in ice-cold water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 삶자마자 얼음물에 담가 손으로 전분을 씻어 쫄깃함 극대화하기",
        missionEn: "Snap Mission! 'You have to shock in ice-cold water to lock in that chewy texture.' Snap!",
        keyVocab: 'shock in ice-cold water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'shock in ice-cold water', pron: 'shock in ice-cold water' },
          { role: 'db', en: 'to lock in that chewy texture.', pron: 'to lock in that chewy texture.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to shock in ice-cold water.', fullPron: 'You have to shock in ice-cold water', ko: 'shock in ice-cold water 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna shock in ice-cold water.', fullPron: 'I\'m gonna shock in ice-cold water', ko: 'shock in ice-cold water 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll shock in ice-cold water?', fullPron: 'I\'ll shock in ice-cold water?', ko: 'shock in ice-cold water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['shock in ice-cold water', 'chill broth slushy', 'pour icy broth']
        },
        fullEn: "You have to shock in ice-cold water to lock in that chewy texture.",
        fullPron: 'You have to + shock in ice-cold water + to lock in that chewy texture.',
        fullKo: '삶자마자 얼음물에 담가 손으로 전분을 씻어 쫄깃함 극대화하기'
      },
      {
        stepTitle: 'SCENE 5 · Twist Noodles into Neat Nest',
        visualEmojis: '🍜 🥣 🥢',
        imagePath: '/images/kfood/ep34-thumb.jpg',
        actionNote: '물기를 꼭 짠 메밀면을 그릇 중앙에 똬리를 틀어 예쁘게 담기',
        coachKo: "코어 블록은 'twist noodles into neat nest'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'twist noodles into neat nest'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 물기를 꼭 짠 메밀면을 그릇 중앙에 똬리를 틀어 예쁘게 담기",
        missionEn: "Snap Mission! 'I\'ll twist noodles into neat nest at the center of chilled bowl.' Snap!",
        keyVocab: 'twist noodles into neat nest',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'twist noodles into neat nest', pron: 'twist noodles into neat nest' },
          { role: 'db', en: 'at the center of chilled bowl.', pron: 'at the center of chilled bowl.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll twist noodles into neat nest.', fullPron: 'I\'ll twist noodles into neat nest', ko: 'twist noodles into neat nest 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna twist noodles into neat nest.', fullPron: 'I\'m gonna twist noodles into neat nest', ko: 'twist noodles into neat nest 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to twist noodles into neat nest?', fullPron: 'You have to twist noodles into neat nest?', ko: 'twist noodles into neat nest 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['twist noodles into neat nest', 'boil buckwheat noodles', 'pickle radish']
        },
        fullEn: "I\'ll twist noodles into neat nest at the center of chilled bowl.",
        fullPron: 'I\'ll + twist noodles into neat nest + at the center of chilled bowl.',
        fullKo: '물기를 꼭 짠 메밀면을 그릇 중앙에 똬리를 틀어 예쁘게 담기'
      },
      {
        stepTitle: 'SCENE 6 · Garnish with Pickled Radish & Boiled Egg',
        visualEmojis: '🥒 🥚 🍐',
        imagePath: '/images/kfood/ep34-thumb.jpg',
        actionNote: '절인 무, 오이, 달콤한 배 조각, 삶은 계란을 단정히 올리기',
        coachKo: "코어 블록은 'garnish with pear and egg'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'garnish with pear and egg'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 절인 무, 오이, 달콤한 배 조각, 삶은 계란을 단정히 올리기",
        missionEn: "Snap Mission! 'We\'re gonna garnish with pear and egg and pickled cucumber slices.' Snap!",
        keyVocab: 'garnish with pear and egg',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'garnish with pear and egg', pron: 'garnish with pear and egg' },
          { role: 'db', en: 'and pickled cucumber slices.', pron: 'and pickled cucumber slices.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna garnish with pear and egg.', fullPron: 'We\'re gonna garnish with pear and egg', ko: 'garnish with pear and egg 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna garnish with pear and egg.', fullPron: 'I\'m gonna garnish with pear and egg', ko: 'garnish with pear and egg 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to garnish with pear and egg?', fullPron: 'You have to garnish with pear and egg?', ko: 'garnish with pear and egg 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['garnish with pear and egg', 'pour slushy broth', 'shock in ice water']
        },
        fullEn: "We\'re gonna garnish with pear and egg and pickled cucumber slices.",
        fullPron: 'We\'re gonna + garnish with pear and egg + and pickled cucumber slices.',
        fullKo: '절인 무, 오이, 달콤한 배 조각, 삶은 계란을 단정히 올리기'
      },
      {
        stepTitle: 'SCENE 7 · Pour Slushy Icy Broth Around Rim',
        visualEmojis: '❄️ 🥣 🧊',
        imagePath: '/images/kfood/ep34-thumb.jpg',
        actionNote: '그릇 가장자리를 따라 살얼음 동동 뜬 육수를 가득 붓기',
        coachKo: "코어 블록은 'pour slushy icy broth generously'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour slushy icy broth generously'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 그릇 가장자리를 따라 살얼음 동동 뜬 육수를 가득 붓기",
        missionEn: "Snap Mission! 'You have to pour slushy icy broth generously all around the noodle nest.' Snap!",
        keyVocab: 'pour slushy icy broth generously',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'pour slushy icy broth generously', pron: 'pour slushy icy broth generously' },
          { role: 'db', en: 'all around the noodle nest.', pron: 'all around the noodle nest.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to pour slushy icy broth generously.', fullPron: 'You have to pour slushy icy broth generously', ko: 'pour slushy icy broth generously 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour slushy icy broth generously.', fullPron: 'I\'m gonna pour slushy icy broth generously', ko: 'pour slushy icy broth generously 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll pour slushy icy broth generously?', fullPron: 'I\'ll pour slushy icy broth generously?', ko: 'pour slushy icy broth generously 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['pour slushy icy broth generously', 'boil buckwheat noodles', 'twist into nest']
        },
        fullEn: "You have to pour slushy icy broth generously all around the noodle nest.",
        fullPron: 'You have to + pour slushy icy broth generously + all around the noodle nest.',
        fullKo: '그릇 가장자리를 따라 살얼음 동동 뜬 육수를 가득 붓기'
      },
      {
        stepTitle: 'SCENE 8 · Crisp Chilly & Spine-Tingling Fresh',
        visualEmojis: '😋 ❄️ 🍜',
        imagePath: '/images/kfood/ep34-thumb.jpg',
        actionNote: '식초와 겨자를 살짝 둘러 살얼음 국물과 면발을 시원하게 흡입',
        coachKo: "코어 블록은 'crisp chilly and spine-tingling'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'crisp chilly and spine-tingling'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 식초와 겨자를 살짝 둘러 살얼음 국물과 면발을 시원하게 흡입",
        missionEn: "Snap Mission! 'It\'s so crisp chilly and spine-tingling with that exhilarating cold punch!' Snap!",
        keyVocab: 'crisp chilly and spine-tingling',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'crisp chilly and spine-tingling', pron: 'crisp chilly and spine-tingling' },
          { role: 'db', en: 'with that exhilarating cold punch!', pron: 'with that exhilarating cold punch!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so crisp chilly and spine-tingling.', fullPron: 'It\'s so crisp chilly and spine-tingling', ko: 'crisp chilly and spine-tingling 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to crisp chilly and spine-tingling.', fullPron: 'You have to crisp chilly and spine-tingling', ko: 'crisp chilly and spine-tingling 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you crisp chilly and spine-tingling?', fullPron: 'Can you crisp chilly and spine-tingling?', ko: 'crisp chilly and spine-tingling 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['crisp chilly and spine-tingling', 'chill broth slushy', 'pour slushy broth']
        },
        fullEn: "It\'s so crisp chilly and spine-tingling with that exhilarating cold punch!",
        fullPron: 'It\'s so + crisp chilly and spine-tingling + with that exhilarating cold punch!',
        fullKo: '식초와 겨자를 살짝 둘러 살얼음 국물과 면발을 시원하게 흡입'
      }
    ]
  },
  // ==========================================
  // EP.35. 🍗 Spicy Braised Chicken
  // ==========================================
  {
    id: 'dakbokkeumtang',
    epNumber: 'EP.35',
    emoji: '🍗',
    shortTitle: '🍗 Spicy Braised Chicken',
    title: 'How to Cook Spicy Braised Korean Chicken (Dakbokkeumtang)',
    ytTitle: 'How to Cook Spicy Korean Braised Chicken in Easy English 🍗 | SoundBlock K-Cooking EP.35',
    thumbnailText: 'Spicy Braised Chicken! [I\'m gonna] + [braise tender chicken with sweet potatoes and chili sauce]',
    thumbnailImage: '/images/kfood/ep35-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s braise spicy, savory Korean Chicken Stew with tender chicken, fluffy potatoes, and rich red chili sauce, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for irresistible Dakbokkeumtang! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Parboil Chicken with Rice Wine',
        visualEmojis: '🍗 🔥 🍶',
        imagePath: '/images/kfood/ep35-thumb.jpg',
        actionNote: '토막 낸 닭고기를 끓는 물에 청주와 함께 3분간 데쳐 불순물 빼기',
        coachKo: "코어 블록은 'parboil bone-in chicken pieces'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'parboil bone-in chicken pieces'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 토막 낸 닭고기를 끓는 물에 청주와 함께 3분간 데쳐 불순물 빼기",
        missionEn: "Snap Mission! 'You have to parboil bone-in chicken pieces for three minutes to clean.' Snap!",
        keyVocab: 'parboil bone-in chicken pieces',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'parboil bone-in chicken pieces', pron: 'parboil bone-in chicken pieces' },
          { role: 'db', en: 'for three minutes to clean.', pron: 'for three minutes to clean.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to parboil bone-in chicken pieces.', fullPron: 'You have to parboil bone-in chicken pieces', ko: 'parboil bone-in chicken pieces 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna parboil bone-in chicken pieces.', fullPron: 'I\'m gonna parboil bone-in chicken pieces', ko: 'parboil bone-in chicken pieces 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll parboil bone-in chicken pieces?', fullPron: 'I\'ll parboil bone-in chicken pieces?', ko: 'parboil bone-in chicken pieces 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['parboil bone-in chicken pieces', 'mix spicy sauce', 'cut chunky potatoes']
        },
        fullEn: "You have to parboil bone-in chicken pieces for three minutes to clean.",
        fullPron: 'You have to + parboil bone-in chicken pieces + for three minutes to clean.',
        fullKo: '토막 낸 닭고기를 끓는 물에 청주와 함께 3분간 데쳐 불순물 빼기'
      },
      {
        stepTitle: 'SCENE 2 · Rinse Under Cold Running Water',
        visualEmojis: '💧 🧼 🍗',
        imagePath: '/images/kfood/ep35-thumb.jpg',
        actionNote: '데친 닭고기를 찬물에 헹궈 기름기와 잔여 찌꺼기 말끔히 씻기',
        coachKo: "코어 블록은 'rinse under cold running water'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'rinse under cold running water'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 데친 닭고기를 찬물에 헹궈 기름기와 잔여 찌꺼기 말끔히 씻기",
        missionEn: "Snap Mission! 'I\'m gonna rinse under cold running water and drain thoroughly.' Snap!",
        keyVocab: 'rinse under cold running water',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'rinse under cold running water', pron: 'rinse under cold running water' },
          { role: 'db', en: 'and drain thoroughly.', pron: 'and drain thoroughly.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna rinse under cold running water.', fullPron: 'I\'m gonna rinse under cold running water', ko: 'rinse under cold running water 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to rinse under cold running water.', fullPron: 'You have to rinse under cold running water', ko: 'rinse under cold running water 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna rinse under cold running water?', fullPron: 'We\'re gonna rinse under cold running water?', ko: 'rinse under cold running water 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['rinse under cold running water', 'cut chunky potatoes', 'mix spicy sauce']
        },
        fullEn: "I\'m gonna rinse under cold running water and drain thoroughly.",
        fullPron: 'I\'m gonna + rinse under cold running water + and drain thoroughly.',
        fullKo: '데친 닭고기를 찬물에 헹궈 기름기와 잔여 찌꺼기 말끔히 씻기'
      },
      {
        stepTitle: 'SCENE 3 · Mix Spicy Sweet Braising Sauce',
        visualEmojis: '🌶️ 🫙 🧄',
        imagePath: '/images/kfood/ep35-thumb.jpg',
        actionNote: '고추장, 고춧가루, 진간장, 올리고당, 다진 마늘로 양념장 배합',
        coachKo: "코어 블록은 'mix rich red chili sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix rich red chili sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고추장, 고춧가루, 진간장, 올리고당, 다진 마늘로 양념장 배합",
        missionEn: "Snap Mission! 'We\'re gonna mix rich red chili sauce with soy sauce and garlic.' Snap!",
        keyVocab: 'mix rich red chili sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'mix rich red chili sauce', pron: 'mix rich red chili sauce' },
          { role: 'db', en: 'with soy sauce and garlic.', pron: 'with soy sauce and garlic.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna mix rich red chili sauce.', fullPron: 'We\'re gonna mix rich red chili sauce', ko: 'mix rich red chili sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix rich red chili sauce.', fullPron: 'I\'m gonna mix rich red chili sauce', ko: 'mix rich red chili sauce 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix rich red chili sauce?', fullPron: 'You have to mix rich red chili sauce?', ko: 'mix rich red chili sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['mix rich red chili sauce', 'parboil chicken', 'cut chunky potatoes']
        },
        fullEn: "We\'re gonna mix rich red chili sauce with soy sauce and garlic.",
        fullPron: 'We\'re gonna + mix rich red chili sauce + with soy sauce and garlic.',
        fullKo: '고추장, 고춧가루, 진간장, 올리고당, 다진 마늘로 양념장 배합'
      },
      {
        stepTitle: 'SCENE 4 · Cut Chunky Potatoes & Carrots',
        visualEmojis: '🥔 🥕 🔪',
        imagePath: '/images/kfood/ep35-thumb.jpg',
        actionNote: '감자와 당근의 모서리를 둥글려 부서짐 없이 큼직하게 썰기',
        coachKo: "코어 블록은 'cut chunky potatoes and carrots'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'cut chunky potatoes and carrots'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 감자와 당근의 모서리를 둥글려 부서짐 없이 큼직하게 썰기",
        missionEn: "Snap Mission! 'You have to cut chunky potatoes and carrots with neatly rounded edges.' Snap!",
        keyVocab: 'cut chunky potatoes and carrots',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'cut chunky potatoes and carrots', pron: 'cut chunky potatoes and carrots' },
          { role: 'db', en: 'with neatly rounded edges.', pron: 'with neatly rounded edges.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to cut chunky potatoes and carrots.', fullPron: 'You have to cut chunky potatoes and carrots', ko: 'cut chunky potatoes and carrots 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna cut chunky potatoes and carrots.', fullPron: 'I\'m gonna cut chunky potatoes and carrots', ko: 'cut chunky potatoes and carrots 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll cut chunky potatoes and carrots?', fullPron: 'I\'ll cut chunky potatoes and carrots?', ko: 'cut chunky potatoes and carrots 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['cut chunky potatoes and carrots', 'braise chicken', 'parboil pieces']
        },
        fullEn: "You have to cut chunky potatoes and carrots with neatly rounded edges.",
        fullPron: 'You have to + cut chunky potatoes and carrots + with neatly rounded edges.',
        fullKo: '감자와 당근의 모서리를 둥글려 부서짐 없이 큼직하게 썰기'
      },
      {
        stepTitle: 'SCENE 5 · Braise Chicken and Sauce Together',
        visualEmojis: '🍗 🍲 🔥',
        imagePath: '/images/kfood/ep35-thumb.jpg',
        actionNote: '냄비에 닭과 물, 특제 양념장을 넣고 센 불에서 끓이기 시작하기',
        coachKo: "코어 블록은 'braise chicken in spicy sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'braise chicken in spicy sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 냄비에 닭과 물, 특제 양념장을 넣고 센 불에서 끓이기 시작하기",
        missionEn: "Snap Mission! 'I\'ll braise chicken in spicy sauce over rolling lively heat.' Snap!",
        keyVocab: 'braise chicken in spicy sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'braise chicken in spicy sauce', pron: 'braise chicken in spicy sauce' },
          { role: 'db', en: 'over rolling lively heat.', pron: 'over rolling lively heat.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll braise chicken in spicy sauce.', fullPron: 'I\'ll braise chicken in spicy sauce', ko: 'braise chicken in spicy sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna braise chicken in spicy sauce.', fullPron: 'I\'m gonna braise chicken in spicy sauce', ko: 'braise chicken in spicy sauce 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to braise chicken in spicy sauce?', fullPron: 'You have to braise chicken in spicy sauce?', ko: 'braise chicken in spicy sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['braise chicken in spicy sauce', 'cut chunky potatoes', 'rinse under water']
        },
        fullEn: "I\'ll braise chicken in spicy sauce over rolling lively heat.",
        fullPron: 'I\'ll + braise chicken in spicy sauce + over rolling lively heat.',
        fullKo: '냄비에 닭과 물, 특제 양념장을 넣고 센 불에서 끓이기 시작하기'
      },
      {
        stepTitle: 'SCENE 6 · Add Chunky Potatoes and Simmer',
        visualEmojis: '🥔 🍲 ⏱️',
        imagePath: '/images/kfood/ep35-thumb.jpg',
        actionNote: '감자와 당근, 양파를 넣고 뚜껑을 덮어 20분간 뭉근히 졸이기',
        coachKo: "코어 블록은 'add chunky potatoes and simmer'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add chunky potatoes and simmer'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 감자와 당근, 양파를 넣고 뚜껑을 덮어 20분간 뭉근히 졸이기",
        missionEn: "Snap Mission! 'We\'re gonna add chunky potatoes and simmer until fork-tender and savory.' Snap!",
        keyVocab: 'add chunky potatoes and simmer',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'add chunky potatoes and simmer', pron: 'add chunky potatoes and simmer' },
          { role: 'db', en: 'until fork-tender and savory.', pron: 'until fork-tender and savory.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna add chunky potatoes and simmer.', fullPron: 'We\'re gonna add chunky potatoes and simmer', ko: 'add chunky potatoes and simmer 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna add chunky potatoes and simmer.', fullPron: 'I\'m gonna add chunky potatoes and simmer', ko: 'add chunky potatoes and simmer 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to add chunky potatoes and simmer?', fullPron: 'You have to add chunky potatoes and simmer?', ko: 'add chunky potatoes and simmer 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['add chunky potatoes and simmer', 'mix red chili sauce', 'parboil chicken']
        },
        fullEn: "We\'re gonna add chunky potatoes and simmer until fork-tender and savory.",
        fullPron: 'We\'re gonna + add chunky potatoes and simmer + until fork-tender and savory.',
        fullKo: '감자와 당근, 양파를 넣고 뚜껑을 덮어 20분간 뭉근히 졸이기'
      },
      {
        stepTitle: 'SCENE 7 · Garnish with Green Chili & Scallions',
        visualEmojis: '🌿 🌶️ 🫙',
        imagePath: '/images/kfood/ep35-thumb.jpg',
        actionNote: '대파와 청양고추를 어슷 썰어 넣고 참기름 한 바퀴 두르기',
        coachKo: "코어 블록은 'garnish with thick scallions'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'garnish with thick scallions'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 대파와 청양고추를 어슷 썰어 넣고 참기름 한 바퀴 두르기",
        missionEn: "Snap Mission! 'You have to garnish with thick scallions and a drizzle of sesame oil.' Snap!",
        keyVocab: 'garnish with thick scallions',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'garnish with thick scallions', pron: 'garnish with thick scallions' },
          { role: 'db', en: 'and a drizzle of sesame oil.', pron: 'and a drizzle of sesame oil.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to garnish with thick scallions.', fullPron: 'You have to garnish with thick scallions', ko: 'garnish with thick scallions 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna garnish with thick scallions.', fullPron: 'I\'m gonna garnish with thick scallions', ko: 'garnish with thick scallions 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll garnish with thick scallions?', fullPron: 'I\'ll garnish with thick scallions?', ko: 'garnish with thick scallions 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['garnish with thick scallions', 'cut chunky potatoes', 'braise in sauce']
        },
        fullEn: "You have to garnish with thick scallions and a drizzle of sesame oil.",
        fullPron: 'You have to + garnish with thick scallions + and a drizzle of sesame oil.',
        fullKo: '대파와 청양고추를 어슷 썰어 넣고 참기름 한 바퀴 두르기'
      },
      {
        stepTitle: 'SCENE 8 · Fiery Sweet & Rice-Stealing Flavor',
        visualEmojis: '😋 🍗 🍚',
        imagePath: '/images/kfood/ep35-thumb.jpg',
        actionNote: '매콤달콤 진한 양념에 푹 익은 감자를 밥 위에 으깨 비벼 먹는 맛',
        coachKo: "코어 블록은 'fiery sweet and rice-stealing'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fiery sweet and rice-stealing'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 매콤달콤 진한 양념에 푹 익은 감자를 밥 위에 으깨 비벼 먹는 맛",
        missionEn: "Snap Mission! 'It\'s so fiery sweet and rice-stealing with delightfully juicy chicken!' Snap!",
        keyVocab: 'fiery sweet and rice-stealing',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'fiery sweet and rice-stealing', pron: 'fiery sweet and rice-stealing' },
          { role: 'db', en: 'with delightfully juicy chicken!', pron: 'with delightfully juicy chicken!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so fiery sweet and rice-stealing.', fullPron: 'It\'s so fiery sweet and rice-stealing', ko: 'fiery sweet and rice-stealing 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to fiery sweet and rice-stealing.', fullPron: 'You have to fiery sweet and rice-stealing', ko: 'fiery sweet and rice-stealing 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you fiery sweet and rice-stealing?', fullPron: 'Can you fiery sweet and rice-stealing?', ko: 'fiery sweet and rice-stealing 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['fiery sweet and rice-stealing', 'parboil chicken', 'add chunky potatoes']
        },
        fullEn: "It\'s so fiery sweet and rice-stealing with delightfully juicy chicken!",
        fullPron: 'It\'s so + fiery sweet and rice-stealing + with delightfully juicy chicken!',
        fullKo: '매콤달콤 진한 양념에 푹 익은 감자를 밥 위에 으깨 비벼 먹는 맛'
      }
    ]
  },
  // ==========================================
  // EP.36. 🦑 Squid & Pork Belly Stir-Fry
  // ==========================================
  {
    id: 'osam-bulgogi',
    epNumber: 'EP.36',
    emoji: '🦑',
    shortTitle: '🦑 Squid & Pork Belly Stir-Fry',
    title: 'How to Stir-Fry Korean Spicy Squid and Pork Belly (Osam Bulgogi)',
    ytTitle: 'How to Stir-Fry Spicy Squid and Pork Belly in Easy English 🦑 | SoundBlock K-Cooking EP.36',
    thumbnailText: 'Spicy Osam Bulgogi! [We\'re gonna] + [stir-fry tender squid and pork belly over high heat]',
    thumbnailImage: '/images/kfood/ep36-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s stir-fry spicy, savory Korean Squid and Pork Belly with smoky gochujang sauce and crisp vegetables, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for sizzling Osam Bulgogi! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Score Squid Body in Diamond Pattern',
        visualEmojis: '🦑 🔪 ✨',
        imagePath: '/images/kfood/ep36-thumb.jpg',
        actionNote: '싱싱한 오징어 안쪽에 예쁜 다이아몬드 칼집을 촘촘히 넣기',
        coachKo: "코어 블록은 'score squid in diamond pattern'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'score squid in diamond pattern'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 싱싱한 오징어 안쪽에 예쁜 다이아몬드 칼집을 촘촘히 넣기",
        missionEn: "Snap Mission! 'You have to score squid in diamond pattern so sauce clings beautifully.' Snap!",
        keyVocab: 'score squid in diamond pattern',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'score squid in diamond pattern', pron: 'score squid in diamond pattern' },
          { role: 'db', en: 'so sauce clings beautifully.', pron: 'so sauce clings beautifully.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to score squid in diamond pattern.', fullPron: 'You have to score squid in diamond pattern', ko: 'score squid in diamond pattern 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna score squid in diamond pattern.', fullPron: 'I\'m gonna score squid in diamond pattern', ko: 'score squid in diamond pattern 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll score squid in diamond pattern?', fullPron: 'I\'ll score squid in diamond pattern?', ko: 'score squid in diamond pattern 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['score squid in diamond pattern', 'slice pork belly', 'mix spicy glaze']
        },
        fullEn: "You have to score squid in diamond pattern so sauce clings beautifully.",
        fullPron: 'You have to + score squid in diamond pattern + so sauce clings beautifully.',
        fullKo: '싱싱한 오징어 안쪽에 예쁜 다이아몬드 칼집을 촘촘히 넣기'
      },
      {
        stepTitle: 'SCENE 2 · Slice Pork Belly into Bite-Sized Cuts',
        visualEmojis: '🥓 🔪 🥩',
        imagePath: '/images/kfood/ep36-thumb.jpg',
        actionNote: '고소한 삼겹살을 오징어 크기에 맞춰 한 입 크기로 썰기',
        coachKo: "코어 블록은 'slice pork belly into pieces'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice pork belly into pieces'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고소한 삼겹살을 오징어 크기에 맞춰 한 입 크기로 썰기",
        missionEn: "Snap Mission! 'I\'m gonna slice pork belly into pieces for balanced savory texture.' Snap!",
        keyVocab: 'slice pork belly into pieces',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'slice pork belly into pieces', pron: 'slice pork belly into pieces' },
          { role: 'db', en: 'for balanced savory texture.', pron: 'for balanced savory texture.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice pork belly into pieces.', fullPron: 'I\'m gonna slice pork belly into pieces', ko: 'slice pork belly into pieces 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice pork belly into pieces.', fullPron: 'You have to slice pork belly into pieces', ko: 'slice pork belly into pieces 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna slice pork belly into pieces?', fullPron: 'We\'re gonna slice pork belly into pieces?', ko: 'slice pork belly into pieces 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['slice pork belly into pieces', 'score squid', 'sizzle on wok']
        },
        fullEn: "I\'m gonna slice pork belly into pieces for balanced savory texture.",
        fullPron: 'I\'m gonna + slice pork belly into pieces + for balanced savory texture.',
        fullKo: '고소한 삼겹살을 오징어 크기에 맞춰 한 입 크기로 썰기'
      },
      {
        stepTitle: 'SCENE 3 · Mix Fiery Smoky Gochujang Glaze',
        visualEmojis: '🌶️ 🫙 🧄',
        imagePath: '/images/kfood/ep36-thumb.jpg',
        actionNote: '고추장, 고춧가루, 간장, 다진 마늘, 생강즙, 물엿으로 양념장 배합',
        coachKo: "코어 블록은 'mix fiery gochujang glaze'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix fiery gochujang glaze'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고추장, 고춧가루, 간장, 다진 마늘, 생강즙, 물엿으로 양념장 배합",
        missionEn: "Snap Mission! 'We\'re gonna mix fiery gochujang glaze with minced garlic and ginger.' Snap!",
        keyVocab: 'mix fiery gochujang glaze',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'mix fiery gochujang glaze', pron: 'mix fiery gochujang glaze' },
          { role: 'db', en: 'with minced garlic and ginger.', pron: 'with minced garlic and ginger.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna mix fiery gochujang glaze.', fullPron: 'We\'re gonna mix fiery gochujang glaze', ko: 'mix fiery gochujang glaze 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix fiery gochujang glaze.', fullPron: 'I\'m gonna mix fiery gochujang glaze', ko: 'mix fiery gochujang glaze 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix fiery gochujang glaze?', fullPron: 'You have to mix fiery gochujang glaze?', ko: 'mix fiery gochujang glaze 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['mix fiery gochujang glaze', 'score squid', 'sear pork belly']
        },
        fullEn: "We\'re gonna mix fiery gochujang glaze with minced garlic and ginger.",
        fullPron: 'We\'re gonna + mix fiery gochujang glaze + with minced garlic and ginger.',
        fullKo: '고추장, 고춧가루, 간장, 다진 마늘, 생강즙, 물엿으로 양념장 배합'
      },
      {
        stepTitle: 'SCENE 4 · Sear Pork Belly First to Render Fat',
        visualEmojis: '🍳 🥓 🔥',
        imagePath: '/images/kfood/ep36-thumb.jpg',
        actionNote: '달군 팬에 삼겹살을 먼저 볶아 고소한 기름을 충분히 내기',
        coachKo: "코어 블록은 'sear pork belly first'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sear pork belly first'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달군 팬에 삼겹살을 먼저 볶아 고소한 기름을 충분히 내기",
        missionEn: "Snap Mission! 'You have to sear pork belly first until golden and fragrant.' Snap!",
        keyVocab: 'sear pork belly first',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'sear pork belly first', pron: 'sear pork belly first' },
          { role: 'db', en: 'until golden and fragrant.', pron: 'until golden and fragrant.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to sear pork belly first.', fullPron: 'You have to sear pork belly first', ko: 'sear pork belly first 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll sear pork belly first.', fullPron: 'I\'ll sear pork belly first', ko: 'sear pork belly first 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna sear pork belly first?', fullPron: 'I\'m gonna sear pork belly first?', ko: 'sear pork belly first 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['sear pork belly first', 'toss in squid', 'mix gochujang glaze']
        },
        fullEn: "You have to sear pork belly first until golden and fragrant.",
        fullPron: 'You have to + sear pork belly first + until golden and fragrant.',
        fullKo: '달군 팬에 삼겹살을 먼저 볶아 고소한 기름을 충분히 내기'
      },
      {
        stepTitle: 'SCENE 5 · Toss in Fresh Squid & Red Glaze',
        visualEmojis: '🦑 🌶️ 🔥',
        imagePath: '/images/kfood/ep36-thumb.jpg',
        actionNote: '칼집 낸 오징어와 특제 양념장을 넣고 센 불에 화르륵 볶기',
        coachKo: "코어 블록은 'toss in squid and glaze'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toss in squid and glaze'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 칼집 낸 오징어와 특제 양념장을 넣고 센 불에 화르륵 볶기",
        missionEn: "Snap Mission! 'I\'ll toss in squid and glaze over roaring high heat.' Snap!",
        keyVocab: 'toss in squid and glaze',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'toss in squid and glaze', pron: 'toss in squid and glaze' },
          { role: 'db', en: 'over roaring high heat.', pron: 'over roaring high heat.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll toss in squid and glaze.', fullPron: 'I\'ll toss in squid and glaze', ko: 'toss in squid and glaze 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna toss in squid and glaze.', fullPron: 'I\'m gonna toss in squid and glaze', ko: 'toss in squid and glaze 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to toss in squid and glaze?', fullPron: 'You have to toss in squid and glaze?', ko: 'toss in squid and glaze 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['toss in squid and glaze', 'score squid', 'sear pork belly']
        },
        fullEn: "I\'ll toss in squid and glaze over roaring high heat.",
        fullPron: 'I\'ll + toss in squid and glaze + over roaring high heat.',
        fullKo: '칼집 낸 오징어와 특제 양념장을 넣고 센 불에 화르륵 볶기'
      },
      {
        stepTitle: 'SCENE 6 · Add Sliced Onions & Green Cabbage',
        visualEmojis: '🧅 🥬 🥢',
        imagePath: '/images/kfood/ep36-thumb.jpg',
        actionNote: '양파, 당근, 대파를 넣고 수분이 나오지 않게 재빠르게 볶기',
        coachKo: "코어 블록은 'add sliced onions and cabbage'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add sliced onions and cabbage'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양파, 당근, 대파를 넣고 수분이 나오지 않게 재빠르게 볶기",
        missionEn: "Snap Mission! 'We\'re gonna add sliced onions and cabbage to keep them wonderfully crisp.' Snap!",
        keyVocab: 'add sliced onions and cabbage',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'add sliced onions and cabbage', pron: 'add sliced onions and cabbage' },
          { role: 'db', en: 'to keep them wonderfully crisp.', pron: 'to keep them wonderfully crisp.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna add sliced onions and cabbage.', fullPron: 'We\'re gonna add sliced onions and cabbage', ko: 'add sliced onions and cabbage 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna add sliced onions and cabbage.', fullPron: 'I\'m gonna add sliced onions and cabbage', ko: 'add sliced onions and cabbage 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to add sliced onions and cabbage?', fullPron: 'You have to add sliced onions and cabbage?', ko: 'add sliced onions and cabbage 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['add sliced onions and cabbage', 'mix gochujang glaze', 'slice pork belly']
        },
        fullEn: "We\'re gonna add sliced onions and cabbage to keep them wonderfully crisp.",
        fullPron: 'We\'re gonna + add sliced onions and cabbage + to keep them wonderfully crisp.',
        fullKo: '양파, 당근, 대파를 넣고 수분이 나오지 않게 재빠르게 볶기'
      },
      {
        stepTitle: 'SCENE 7 · Finish with Sesame Oil & Seeds',
        visualEmojis: '🫙 🌿 ✨',
        imagePath: '/images/kfood/ep36-thumb.jpg',
        actionNote: '불을 끄기 직전 참기름과 볶은 통깨를 솔솔 뿌려 마무리하기',
        coachKo: "코어 블록은 'finish with fragrant sesame oil'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'finish with fragrant sesame oil'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 불을 끄기 직전 참기름과 볶은 통깨를 솔솔 뿌려 마무리하기",
        missionEn: "Snap Mission! 'You have to finish with fragrant sesame oil and toasted sesame seeds.' Snap!",
        keyVocab: 'finish with fragrant sesame oil',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'finish with fragrant sesame oil', pron: 'finish with fragrant sesame oil' },
          { role: 'db', en: 'and toasted sesame seeds.', pron: 'and toasted sesame seeds.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to finish with fragrant sesame oil.', fullPron: 'You have to finish with fragrant sesame oil', ko: 'finish with fragrant sesame oil 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna finish with fragrant sesame oil.', fullPron: 'I\'m gonna finish with fragrant sesame oil', ko: 'finish with fragrant sesame oil 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll finish with fragrant sesame oil?', fullPron: 'I\'ll finish with fragrant sesame oil?', ko: 'finish with fragrant sesame oil 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['finish with fragrant sesame oil', 'score squid', 'toss in glaze']
        },
        fullEn: "You have to finish with fragrant sesame oil and toasted sesame seeds.",
        fullPron: 'You have to + finish with fragrant sesame oil + and toasted sesame seeds.',
        fullKo: '불을 끄기 직전 참기름과 볶은 통깨를 솔솔 뿌려 마무리하기'
      },
      {
        stepTitle: 'SCENE 8 · Smoky Spicy & Chewy Perfection',
        visualEmojis: '😋 🦑 🥬',
        imagePath: '/images/kfood/ep36-thumb.jpg',
        actionNote: '쫄깃한 오징어와 고소한 삼겹살을 상추에 올려 한입 가득 쌈 싸기',
        coachKo: "코어 블록은 'smoky spicy and chewy perfection'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'smoky spicy and chewy perfection'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 쫄깃한 오징어와 고소한 삼겹살을 상추에 올려 한입 가득 쌈 싸기",
        missionEn: "Snap Mission! 'It\'s so smoky spicy and chewy perfection wrapped inside fresh lettuce!' Snap!",
        keyVocab: 'smoky spicy and chewy perfection',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'smoky spicy and chewy perfection', pron: 'smoky spicy and chewy perfection' },
          { role: 'db', en: 'wrapped inside fresh lettuce!', pron: 'wrapped inside fresh lettuce!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so smoky spicy and chewy perfection.', fullPron: 'It\'s so smoky spicy and chewy perfection', ko: 'smoky spicy and chewy perfection 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to smoky spicy and chewy perfection.', fullPron: 'You have to smoky spicy and chewy perfection', ko: 'smoky spicy and chewy perfection 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you smoky spicy and chewy perfection?', fullPron: 'Can you smoky spicy and chewy perfection?', ko: 'smoky spicy and chewy perfection 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['smoky spicy and chewy perfection', 'score squid', 'finish with sesame oil']
        },
        fullEn: "It\'s so smoky spicy and chewy perfection wrapped inside fresh lettuce!",
        fullPron: 'It\'s so + smoky spicy and chewy perfection + wrapped inside fresh lettuce!',
        fullKo: '쫄깃한 오징어와 고소한 삼겹살을 상추에 올려 한입 가득 쌈 싸기'
      }
    ]
  },
  // ==========================================
  // EP.37. 🍖 Sweet Marinated Pork Ribs
  // ==========================================
  {
    id: 'dwaeji-galbi',
    epNumber: 'EP.37',
    emoji: '🍖',
    shortTitle: '🍖 Sweet Marinated Pork Ribs',
    title: 'How to Marinate and Grill Sweet Savory Korean Pork Ribs',
    ytTitle: 'How to Grill Korean Marinated Pork Ribs in Easy English 🍖 | SoundBlock K-Cooking EP.37',
    thumbnailText: 'Caramelized Pork Ribs! [I\'m gonna] + [marinate tender pork ribs in sweet soy fruit sauce]',
    thumbnailImage: '/images/kfood/ep37-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s marinate and grill sweet, savory Korean Pork Ribs with caramelized soy fruit marinade, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for juicy Dwaeji Galbi! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Score Pork Ribs with Diamond Cuts',
        visualEmojis: '🍖 🔪 ✨',
        imagePath: '/images/kfood/ep37-thumb.jpg',
        actionNote: '돼지갈비 살에 깊은 다이아몬드 칼집을 넣어 양념 쏙 배게 하기',
        coachKo: "코어 블록은 'score pork ribs with deep cuts'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'score pork ribs with deep cuts'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 돼지갈비 살에 깊은 다이아몬드 칼집을 넣어 양념 쏙 배게 하기",
        missionEn: "Snap Mission! 'You have to score pork ribs with deep cuts so marinade penetrates deep.' Snap!",
        keyVocab: 'score pork ribs with deep cuts',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'score pork ribs with deep cuts', pron: 'score pork ribs with deep cuts' },
          { role: 'db', en: 'so marinade penetrates deep.', pron: 'so marinade penetrates deep.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to score pork ribs with deep cuts.', fullPron: 'You have to score pork ribs with deep cuts', ko: 'score pork ribs with deep cuts 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna score pork ribs with deep cuts.', fullPron: 'I\'m gonna score pork ribs with deep cuts', ko: 'score pork ribs with deep cuts 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll score pork ribs with deep cuts?', fullPron: 'I\'ll score pork ribs with deep cuts?', ko: 'score pork ribs with deep cuts 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['score pork ribs with deep cuts', 'blend sweet pear', 'sear on charcoal']
        },
        fullEn: "You have to score pork ribs with deep cuts so marinade penetrates deep.",
        fullPron: 'You have to + score pork ribs with deep cuts + so marinade penetrates deep.',
        fullKo: '돼지갈비 살에 깊은 다이아몬드 칼집을 넣어 양념 쏙 배게 하기'
      },
      {
        stepTitle: 'SCENE 2 · Blend Sweet Korean Pear & Onion',
        visualEmojis: '🍐 🧅 🥣',
        imagePath: '/images/kfood/ep37-thumb.jpg',
        actionNote: '달콤한 배와 양파를 믹서에 곱게 갈아 자연스러운 단맛 내기',
        coachKo: "코어 블록은 'blend sweet Korean pear'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'blend sweet Korean pear'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달콤한 배와 양파를 믹서에 곱게 갈아 자연스러운 단맛 내기",
        missionEn: "Snap Mission! 'I\'m gonna blend sweet Korean pear and juicy yellow onions.' Snap!",
        keyVocab: 'blend sweet Korean pear',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'blend sweet Korean pear', pron: 'blend sweet Korean pear' },
          { role: 'db', en: 'and juicy yellow onions.', pron: 'and juicy yellow onions.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna blend sweet Korean pear.', fullPron: 'I\'m gonna blend sweet Korean pear', ko: 'blend sweet Korean pear 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to blend sweet Korean pear.', fullPron: 'You have to blend sweet Korean pear', ko: 'blend sweet Korean pear 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna blend sweet Korean pear?', fullPron: 'We\'re gonna blend sweet Korean pear?', ko: 'blend sweet Korean pear 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['blend sweet Korean pear', 'score pork ribs', 'grill over coals']
        },
        fullEn: "I\'m gonna blend sweet Korean pear and juicy yellow onions.",
        fullPron: 'I\'m gonna + blend sweet Korean pear + and juicy yellow onions.',
        fullKo: '달콤한 배와 양파를 믹서에 곱게 갈아 자연스러운 단맛 내기'
      },
      {
        stepTitle: 'SCENE 3 · Mix Sweet Savory Soy Marinade',
        visualEmojis: '🫙 🧄 🍯',
        imagePath: '/images/kfood/ep37-thumb.jpg',
        actionNote: '진간장, 황설탕, 다진 마늘, 생강, 참기름으로 특제 갈비 양념 배합',
        coachKo: "코어 블록은 'mix sweet savory soy marinade'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix sweet savory soy marinade'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 진간장, 황설탕, 다진 마늘, 생강, 참기름으로 특제 갈비 양념 배합",
        missionEn: "Snap Mission! 'We\'re gonna mix sweet savory soy marinade with fresh ginger and garlic.' Snap!",
        keyVocab: 'mix sweet savory soy marinade',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'mix sweet savory soy marinade', pron: 'mix sweet savory soy marinade' },
          { role: 'db', en: 'with fresh ginger and garlic.', pron: 'with fresh ginger and garlic.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna mix sweet savory soy marinade.', fullPron: 'We\'re gonna mix sweet savory soy marinade', ko: 'mix sweet savory soy marinade 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix sweet savory soy marinade.', fullPron: 'I\'m gonna mix sweet savory soy marinade', ko: 'mix sweet savory soy marinade 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix sweet savory soy marinade?', fullPron: 'You have to mix sweet savory soy marinade?', ko: 'mix sweet savory soy marinade 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['mix sweet savory soy marinade', 'score pork ribs', 'flip frequently']
        },
        fullEn: "We\'re gonna mix sweet savory soy marinade with fresh ginger and garlic.",
        fullPron: 'We\'re gonna + mix sweet savory soy marinade + with fresh ginger and garlic.',
        fullKo: '진간장, 황설탕, 다진 마늘, 생강, 참기름으로 특제 갈비 양념 배합'
      },
      {
        stepTitle: 'SCENE 4 · Marinate Ribs Overnight in Chiller',
        visualEmojis: '🍖 ⏳ ❄️',
        imagePath: '/images/kfood/ep37-thumb.jpg',
        actionNote: '양념에 잰 갈비를 냉장고에서 최소 4시간 이상 숙성하기',
        coachKo: "코어 블록은 'marinate ribs in the fridge'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'marinate ribs in the fridge'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양념에 잰 갈비를 냉장고에서 최소 4시간 이상 숙성하기",
        missionEn: "Snap Mission! 'You have to marinate ribs in the fridge for deep caramelized flavor.' Snap!",
        keyVocab: 'marinate ribs in the fridge',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'marinate ribs in the fridge', pron: 'marinate ribs in the fridge' },
          { role: 'db', en: 'for deep caramelized flavor.', pron: 'for deep caramelized flavor.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to marinate ribs in the fridge.', fullPron: 'You have to marinate ribs in the fridge', ko: 'marinate ribs in the fridge 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll marinate ribs in the fridge.', fullPron: 'I\'ll marinate ribs in the fridge', ko: 'marinate ribs in the fridge 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna marinate ribs in the fridge?', fullPron: 'I\'m gonna marinate ribs in the fridge?', ko: 'marinate ribs in the fridge 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['marinate ribs in the fridge', 'blend sweet pear', 'sear over coals']
        },
        fullEn: "You have to marinate ribs in the fridge for deep caramelized flavor.",
        fullPron: 'You have to + marinate ribs in the fridge + for deep caramelized flavor.',
        fullKo: '양념에 잰 갈비를 냉장고에서 최소 4시간 이상 숙성하기'
      },
      {
        stepTitle: 'SCENE 5 · Heat the Grill or Charcoal BBQ',
        visualEmojis: '🔥 🍳 💨',
        imagePath: '/images/kfood/ep37-thumb.jpg',
        actionNote: '달군 불판이나 숯불 석쇠에 양념을 가볍게 털고 올리기',
        coachKo: "코어 블록은 'heat the charcoal grill hot'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'heat the charcoal grill hot'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달군 불판이나 숯불 석쇠에 양념을 가볍게 털고 올리기",
        missionEn: "Snap Mission! 'I\'ll heat the charcoal grill hot and lay down the ribs.' Snap!",
        keyVocab: 'heat the charcoal grill hot',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'heat the charcoal grill hot', pron: 'heat the charcoal grill hot' },
          { role: 'db', en: 'and lay down the ribs.', pron: 'and lay down the ribs.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll heat the charcoal grill hot.', fullPron: 'I\'ll heat the charcoal grill hot', ko: 'heat the charcoal grill hot 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna heat the charcoal grill hot.', fullPron: 'I\'m gonna heat the charcoal grill hot', ko: 'heat the charcoal grill hot 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to heat the charcoal grill hot?', fullPron: 'You have to heat the charcoal grill hot?', ko: 'heat the charcoal grill hot 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['heat the charcoal grill hot', 'score pork ribs', 'mix soy marinade']
        },
        fullEn: "I\'ll heat the charcoal grill hot and lay down the ribs.",
        fullPron: 'I\'ll + heat the charcoal grill hot + and lay down the ribs.',
        fullKo: '달군 불판이나 숯불 석쇠에 양념을 가볍게 털고 올리기'
      },
      {
        stepTitle: 'SCENE 6 · Flip Frequently to Prevent Burning',
        visualEmojis: '🔄 🔥 🍖',
        imagePath: '/images/kfood/ep37-thumb.jpg',
        actionNote: '양념이 타지 않도록 자주 뒤집어가며 윤기 나게 굽기',
        coachKo: "코어 블록은 'flip ribs frequently on grill'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'flip ribs frequently on grill'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양념이 타지 않도록 자주 뒤집어가며 윤기 나게 굽기",
        missionEn: "Snap Mission! 'You have to flip ribs frequently on grill so sugar caramelizes perfectly.' Snap!",
        keyVocab: 'flip ribs frequently on grill',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'flip ribs frequently on grill', pron: 'flip ribs frequently on grill' },
          { role: 'db', en: 'so sugar caramelizes perfectly.', pron: 'so sugar caramelizes perfectly.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to flip ribs frequently on grill.', fullPron: 'You have to flip ribs frequently on grill', ko: 'flip ribs frequently on grill 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna flip ribs frequently on grill.', fullPron: 'I\'m gonna flip ribs frequently on grill', ko: 'flip ribs frequently on grill 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna flip ribs frequently on grill?', fullPron: 'We\'re gonna flip ribs frequently on grill?', ko: 'flip ribs frequently on grill 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['flip ribs frequently on grill', 'marinate ribs', 'cut into pieces']
        },
        fullEn: "You have to flip ribs frequently on grill so sugar caramelizes perfectly.",
        fullPron: 'You have to + flip ribs frequently on grill + so sugar caramelizes perfectly.',
        fullKo: '양념이 타지 않도록 자주 뒤집어가며 윤기 나게 굽기'
      },
      {
        stepTitle: 'SCENE 7 · Cut Along Bone into Juicy Bites',
        visualEmojis: '✂️ 🍖 🥢',
        imagePath: '/images/kfood/ep37-thumb.jpg',
        actionNote: '가위로 뼈를 따라 살코기를 먹기 좋은 크기로 큼직하게 썰기',
        coachKo: "코어 블록은 'cut along bone into bites'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'cut along bone into bites'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 가위로 뼈를 따라 살코기를 먹기 좋은 크기로 큼직하게 썰기",
        missionEn: "Snap Mission! 'We\'re gonna cut along bone into bites with sharp kitchen scissors.' Snap!",
        keyVocab: 'cut along bone into bites',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'cut along bone into bites', pron: 'cut along bone into bites' },
          { role: 'db', en: 'with sharp kitchen scissors.', pron: 'with sharp kitchen scissors.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna cut along bone into bites.', fullPron: 'We\'re gonna cut along bone into bites', ko: 'cut along bone into bites 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna cut along bone into bites.', fullPron: 'I\'m gonna cut along bone into bites', ko: 'cut along bone into bites 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to cut along bone into bites?', fullPron: 'You have to cut along bone into bites?', ko: 'cut along bone into bites 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['cut along bone into bites', 'blend sweet pear', 'heat the grill']
        },
        fullEn: "We\'re gonna cut along bone into bites with sharp kitchen scissors.",
        fullPron: 'We\'re gonna + cut along bone into bites + with sharp kitchen scissors.',
        fullKo: '가위로 뼈를 따라 살코기를 먹기 좋은 크기로 큼직하게 썰기'
      },
      {
        stepTitle: 'SCENE 8 · Smoky Caramelized & Melt-In-Mouth',
        visualEmojis: '😋 🍖 🍚',
        imagePath: '/images/kfood/ep37-thumb.jpg',
        actionNote: '은은한 불향과 달짝지근한 감칠맛이 폭발하는 밥도둑 갈비',
        coachKo: "코어 블록은 'smoky caramelized and melt-in-mouth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'smoky caramelized and melt-in-mouth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 은은한 불향과 달짝지근한 감칠맛이 폭발하는 밥도둑 갈비",
        missionEn: "Snap Mission! 'It\'s so smoky caramelized and melt-in-mouth with irresistible sweet char!' Snap!",
        keyVocab: 'smoky caramelized and melt-in-mouth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'smoky caramelized and melt-in-mouth', pron: 'smoky caramelized and melt-in-mouth' },
          { role: 'db', en: 'with irresistible sweet char!', pron: 'with irresistible sweet char!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so smoky caramelized and melt-in-mouth.', fullPron: 'It\'s so smoky caramelized and melt-in-mouth', ko: 'smoky caramelized and melt-in-mouth 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to smoky caramelized and melt-in-mouth.', fullPron: 'You have to smoky caramelized and melt-in-mouth', ko: 'smoky caramelized and melt-in-mouth 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you smoky caramelized and melt-in-mouth?', fullPron: 'Can you smoky caramelized and melt-in-mouth?', ko: 'smoky caramelized and melt-in-mouth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['smoky caramelized and melt-in-mouth', 'score pork ribs', 'flip ribs frequently']
        },
        fullEn: "It\'s so smoky caramelized and melt-in-mouth with irresistible sweet char!",
        fullPron: 'It\'s so + smoky caramelized and melt-in-mouth + with irresistible sweet char!',
        fullKo: '은은한 불향과 달짝지근한 감칠맛이 폭발하는 밥도둑 갈비'
      }
    ]
  },
  // ==========================================
  // EP.38. 🍢 Blood Sausage & Tempura
  // ==========================================
  {
    id: 'sundae-twigim',
    epNumber: 'EP.38',
    emoji: '🍢',
    shortTitle: '🍢 Blood Sausage & Tempura',
    title: 'How to Enjoy Korean Street Food Blood Sausage and Crispy Fritters',
    ytTitle: 'How to Enjoy Korean Street Food Sundae & Crispy Fritters in Easy English 🍢 | SoundBlock K-Cooking EP.38',
    thumbnailText: 'Street Sundae & Crispy Fritters! [We\'re gonna] + [dip chewy blood sausage into spicy tteokbokki sauce]',
    thumbnailImage: '/images/kfood/ep38-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s enjoy Korean Street Food classics: chewy steamed blood sausage and ultra-crispy vegetable fritters dipped in tteokbokki sauce, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for street-style Sundae and Twigim! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Steam Plump Sundae in Steamer Basket',
        visualEmojis: '♨️ 🥢 🥟',
        imagePath: '/images/kfood/ep38-thumb.jpg',
        actionNote: '찜기에 김이 오르면 통통한 찰순대를 넣고 10분간 촉촉하게 찌기',
        coachKo: "코어 블록은 'steam plump blood sausage'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'steam plump blood sausage'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 찜기에 김이 오르면 통통한 찰순대를 넣고 10분간 촉촉하게 찌기",
        missionEn: "Snap Mission! 'You have to steam plump blood sausage until warm and bouncy.' Snap!",
        keyVocab: 'steam plump blood sausage',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'steam plump blood sausage', pron: 'steam plump blood sausage' },
          { role: 'db', en: 'until warm and bouncy.', pron: 'until warm and bouncy.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to steam plump blood sausage.', fullPron: 'You have to steam plump blood sausage', ko: 'steam plump blood sausage 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna steam plump blood sausage.', fullPron: 'I\'m gonna steam plump blood sausage', ko: 'steam plump blood sausage 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll steam plump blood sausage?', fullPron: 'I\'ll steam plump blood sausage?', ko: 'steam plump blood sausage 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['steam plump blood sausage', 'mix crispy batter', 'dip in spicy sauce']
        },
        fullEn: "You have to steam plump blood sausage until warm and bouncy.",
        fullPron: 'You have to + steam plump blood sausage + until warm and bouncy.',
        fullKo: '찜기에 김이 오르면 통통한 찰순대를 넣고 10분간 촉촉하게 찌기'
      },
      {
        stepTitle: 'SCENE 2 · Slice Sundae and Steamed Liver Thinly',
        visualEmojis: '🔪 🍢 🥢',
        imagePath: '/images/kfood/ep38-thumb.jpg',
        actionNote: '한 김 식힌 순대와 고소한 간, 허파를 비스듬히 썰기',
        coachKo: "코어 블록은 'slice sundae and liver thinly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice sundae and liver thinly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 한 김 식힌 순대와 고소한 간, 허파를 비스듬히 썰기",
        missionEn: "Snap Mission! 'I\'m gonna slice sundae and liver thinly into neat bite-sized rounds.' Snap!",
        keyVocab: 'slice sundae and liver thinly',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'slice sundae and liver thinly', pron: 'slice sundae and liver thinly' },
          { role: 'db', en: 'into neat bite-sized rounds.', pron: 'into neat bite-sized rounds.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice sundae and liver thinly.', fullPron: 'I\'m gonna slice sundae and liver thinly', ko: 'slice sundae and liver thinly 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice sundae and liver thinly.', fullPron: 'You have to slice sundae and liver thinly', ko: 'slice sundae and liver thinly 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna slice sundae and liver thinly?', fullPron: 'We\'re gonna slice sundae and liver thinly?', ko: 'slice sundae and liver thinly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['slice sundae and liver thinly', 'steam plump sausage', 'deep fry fritters']
        },
        fullEn: "I\'m gonna slice sundae and liver thinly into neat bite-sized rounds.",
        fullPron: 'I\'m gonna + slice sundae and liver thinly + into neat bite-sized rounds.',
        fullKo: '한 김 식힌 순대와 고소한 간, 허파를 비스듬히 썰기'
      },
      {
        stepTitle: 'SCENE 3 · Mix Ice-Cold Crispy Tempura Batter',
        visualEmojis: '❄️ 🥣 🥢',
        imagePath: '/images/kfood/ep38-thumb.jpg',
        actionNote: '얼음물과 튀김가루를 가볍게 섞어 바삭한 튀김옷 만들기',
        coachKo: "코어 블록은 'mix icy crispy tempura batter'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix icy crispy tempura batter'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 얼음물과 튀김가루를 가볍게 섞어 바삭한 튀김옷 만들기",
        missionEn: "Snap Mission! 'We\'re gonna mix icy crispy tempura batter with sparkling ice water.' Snap!",
        keyVocab: 'mix icy crispy tempura batter',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'mix icy crispy tempura batter', pron: 'mix icy crispy tempura batter' },
          { role: 'db', en: 'with sparkling ice water.', pron: 'with sparkling ice water.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna mix icy crispy tempura batter.', fullPron: 'We\'re gonna mix icy crispy tempura batter', ko: 'mix icy crispy tempura batter 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix icy crispy tempura batter.', fullPron: 'I\'m gonna mix icy crispy tempura batter', ko: 'mix icy crispy tempura batter 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix icy crispy tempura batter?', fullPron: 'You have to mix icy crispy tempura batter?', ko: 'mix icy crispy tempura batter 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['mix icy crispy tempura batter', 'slice sundae', 'dip in chili sauce']
        },
        fullEn: "We\'re gonna mix icy crispy tempura batter with sparkling ice water.",
        fullPron: 'We\'re gonna + mix icy crispy tempura batter + with sparkling ice water.',
        fullKo: '얼음물과 튀김가루를 가볍게 섞어 바삭한 튀김옷 만들기'
      },
      {
        stepTitle: 'SCENE 4 · Coat Sweet Potato & Seaweed Rolls',
        visualEmojis: '🍠 🌿 🥢',
        imagePath: '/images/kfood/ep38-thumb.jpg',
        actionNote: '고구마, 오징어, 김말이에 튀김옷을 얇고 고르게 입히기',
        coachKo: "코어 블록은 'coat sweet potatoes and glass noodle rolls'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'coat sweet potatoes and glass noodle rolls'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 고구마, 오징어, 김말이에 튀김옷을 얇고 고르게 입히기",
        missionEn: "Snap Mission! 'You have to coat sweet potatoes and glass noodle rolls in light flour batter.' Snap!",
        keyVocab: 'coat sweet potatoes and glass noodle rolls',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'coat sweet potatoes and glass noodle rolls', pron: 'coat sweet potatoes and glass noodle rolls' },
          { role: 'db', en: 'in light flour batter.', pron: 'in light flour batter.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to coat sweet potatoes and glass noodle rolls.', fullPron: 'You have to coat sweet potatoes and glass noodle rolls', ko: 'coat sweet potatoes and glass noodle rolls 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll coat sweet potatoes and glass noodle rolls.', fullPron: 'I\'ll coat sweet potatoes and glass noodle rolls', ko: 'coat sweet potatoes and glass noodle rolls 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna coat sweet potatoes and glass noodle rolls?', fullPron: 'I\'m gonna coat sweet potatoes and glass noodle rolls?', ko: 'coat sweet potatoes and glass noodle rolls 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['coat sweet potatoes and glass noodle rolls', 'deep fry until golden', 'steam sundae']
        },
        fullEn: "You have to coat sweet potatoes and glass noodle rolls in light flour batter.",
        fullPron: 'You have to + coat sweet potatoes and glass noodle rolls + in light flour batter.',
        fullKo: '고구마, 오징어, 김말이에 튀김옷을 얇고 고르게 입히기'
      },
      {
        stepTitle: 'SCENE 5 · Deep-Fry in Bubbling Hot Oil',
        visualEmojis: '🍳 🔥 💨',
        imagePath: '/images/kfood/ep38-thumb.jpg',
        actionNote: '170도 뜨거운 기름에 바삭바삭 소리 나게 노릇하게 튀겨내기',
        coachKo: "코어 블록은 'deep-fry until golden and crispy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'deep-fry until golden and crispy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 170도 뜨거운 기름에 바삭바삭 소리 나게 노릇하게 튀겨내기",
        missionEn: "Snap Mission! 'I\'ll deep-fry until golden and crispy with sensational sizzling crunch.' Snap!",
        keyVocab: 'deep-fry until golden and crispy',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'deep-fry until golden and crispy', pron: 'deep-fry until golden and crispy' },
          { role: 'db', en: 'with sensational sizzling crunch.', pron: 'with sensational sizzling crunch.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll deep-fry until golden and crispy.', fullPron: 'I\'ll deep-fry until golden and crispy', ko: 'deep-fry until golden and crispy 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna deep-fry until golden and crispy.', fullPron: 'I\'m gonna deep-fry until golden and crispy', ko: 'deep-fry until golden and crispy 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to deep-fry until golden and crispy?', fullPron: 'You have to deep-fry until golden and crispy?', ko: 'deep-fry until golden and crispy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['deep-fry until golden and crispy', 'mix icy batter', 'slice sundae']
        },
        fullEn: "I\'ll deep-fry until golden and crispy with sensational sizzling crunch.",
        fullPron: 'I\'ll + deep-fry until golden and crispy + with sensational sizzling crunch.',
        fullKo: '170도 뜨거운 기름에 바삭바삭 소리 나게 노릇하게 튀겨내기'
      },
      {
        stepTitle: 'SCENE 6 · Drain on Wire Rack for Max Crispiness',
        visualEmojis: '🥢 ⏳ ✨',
        imagePath: '/images/kfood/ep38-thumb.jpg',
        actionNote: '튀김을 건져 식힘망에 세워 기름기를 쏙 빼 바삭함 유지하기',
        coachKo: "코어 블록은 'drain on wire cooling rack'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'drain on wire cooling rack'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 튀김을 건져 식힘망에 세워 기름기를 쏙 빼 바삭함 유지하기",
        missionEn: "Snap Mission! 'We\'re gonna drain on wire cooling rack to keep them ultra-crunchy.' Snap!",
        keyVocab: 'drain on wire cooling rack',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'drain on wire cooling rack', pron: 'drain on wire cooling rack' },
          { role: 'db', en: 'to keep them ultra-crunchy.', pron: 'to keep them ultra-crunchy.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna drain on wire cooling rack.', fullPron: 'We\'re gonna drain on wire cooling rack', ko: 'drain on wire cooling rack 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna drain on wire cooling rack.', fullPron: 'I\'m gonna drain on wire cooling rack', ko: 'drain on wire cooling rack 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to drain on wire cooling rack?', fullPron: 'You have to drain on wire cooling rack?', ko: 'drain on wire cooling rack 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['drain on wire cooling rack', 'steam plump sausage', 'coat with batter']
        },
        fullEn: "We\'re gonna drain on wire cooling rack to keep them ultra-crunchy.",
        fullPron: 'We\'re gonna + drain on wire cooling rack + to keep them ultra-crunchy.',
        fullKo: '튀김을 건져 식힘망에 세워 기름기를 쏙 빼 바삭함 유지하기'
      },
      {
        stepTitle: 'SCENE 7 · Dip in Fiery Red Tteokbokki Sauce',
        visualEmojis: '🌶️ 🍲 🥢',
        imagePath: '/images/kfood/ep38-thumb.jpg',
        actionNote: '바삭한 튀김과 찰순대를 매콤한 떡볶이 국물에 푹 찍기',
        coachKo: "코어 블록은 'dip into spicy tteokbokki sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'dip into spicy tteokbokki sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 바삭한 튀김과 찰순대를 매콤한 떡볶이 국물에 푹 찍기",
        missionEn: "Snap Mission! 'You have to dip into spicy tteokbokki sauce for ultimate street food combo.' Snap!",
        keyVocab: 'dip into spicy tteokbokki sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'dip into spicy tteokbokki sauce', pron: 'dip into spicy tteokbokki sauce' },
          { role: 'db', en: 'for ultimate street food combo.', pron: 'for ultimate street food combo.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to dip into spicy tteokbokki sauce.', fullPron: 'You have to dip into spicy tteokbokki sauce', ko: 'dip into spicy tteokbokki sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna dip into spicy tteokbokki sauce.', fullPron: 'I\'m gonna dip into spicy tteokbokki sauce', ko: 'dip into spicy tteokbokki sauce 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll dip into spicy tteokbokki sauce?', fullPron: 'I\'ll dip into spicy tteokbokki sauce?', ko: 'dip into spicy tteokbokki sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['dip into spicy tteokbokki sauce', 'slice sundae', 'deep fry fritters']
        },
        fullEn: "You have to dip into spicy tteokbokki sauce for ultimate street food combo.",
        fullPron: 'You have to + dip into spicy tteokbokki sauce + for ultimate street food combo.',
        fullKo: '바삭한 튀김과 찰순대를 매콤한 떡볶이 국물에 푹 찍기'
      },
      {
        stepTitle: 'SCENE 8 · Chewy Savory & Addictively Crunchy',
        visualEmojis: '😋 🍢 💥',
        imagePath: '/images/kfood/ep38-thumb.jpg',
        actionNote: '찰진 순대의 구수함과 파사삭 부서지는 튀김의 환상적인 조합',
        coachKo: "코어 블록은 'chewy savory and addictively crunchy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'chewy savory and addictively crunchy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 찰진 순대의 구수함과 파사삭 부서지는 튀김의 환상적인 조합",
        missionEn: "Snap Mission! 'It\'s so chewy savory and addictively crunchy with that spicy saucy dip!' Snap!",
        keyVocab: 'chewy savory and addictively crunchy',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'chewy savory and addictively crunchy', pron: 'chewy savory and addictively crunchy' },
          { role: 'db', en: 'with that spicy saucy dip!', pron: 'with that spicy saucy dip!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so chewy savory and addictively crunchy.', fullPron: 'It\'s so chewy savory and addictively crunchy', ko: 'chewy savory and addictively crunchy 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to chewy savory and addictively crunchy.', fullPron: 'You have to chewy savory and addictively crunchy', ko: 'chewy savory and addictively crunchy 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you chewy savory and addictively crunchy?', fullPron: 'Can you chewy savory and addictively crunchy?', ko: 'chewy savory and addictively crunchy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['chewy savory and addictively crunchy', 'steam plump sausage', 'dip into spicy sauce']
        },
        fullEn: "It\'s so chewy savory and addictively crunchy with that spicy saucy dip!",
        fullPron: 'It\'s so + chewy savory and addictively crunchy + with that spicy saucy dip!',
        fullKo: '찰진 순대의 구수함과 파사삭 부서지는 튀김의 환상적인 조합'
      }
    ]
  },
  // ==========================================
  // EP.39. 🥪 Korean Street Toast
  // ==========================================
  {
    id: 'street-toast',
    epNumber: 'EP.39',
    emoji: '🥪',
    shortTitle: '🥪 Korean Street Toast',
    title: 'How to Make Sweet Savory Korean Street Cabbage Toast',
    ytTitle: 'How to Make Sweet & Savory Korean Street Toast in Easy English 🥪 | SoundBlock K-Cooking EP.39',
    thumbnailText: 'Buttery Street Toast! [I\'m gonna] + [toast fluffy bread with buttery cabbage egg patty]',
    thumbnailImage: '/images/kfood/ep39-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s cook famous Korean Street Cabbage Toast with melted butter, egg cabbage patty, sugar, and ketchup, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for sweet savory Korean Street Toast! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Shred Crisp Cabbage & Carrots Thinly',
        visualEmojis: '🥬 🥕 🔪',
        imagePath: '/images/kfood/ep39-thumb.jpg',
        actionNote: '양배추와 당근, 대파를 아주 얇고 곱게 채 썰어 준비하기',
        coachKo: "코어 블록은 'shred crisp cabbage and carrots'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'shred crisp cabbage and carrots'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 양배추와 당근, 대파를 아주 얇고 곱게 채 썰어 준비하기",
        missionEn: "Snap Mission! 'You have to shred crisp cabbage and carrots into fine delicate ribbons.' Snap!",
        keyVocab: 'shred crisp cabbage and carrots',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'shred crisp cabbage and carrots', pron: 'shred crisp cabbage and carrots' },
          { role: 'db', en: 'into fine delicate ribbons.', pron: 'into fine delicate ribbons.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to shred crisp cabbage and carrots.', fullPron: 'You have to shred crisp cabbage and carrots', ko: 'shred crisp cabbage and carrots 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna shred crisp cabbage and carrots.', fullPron: 'I\'m gonna shred crisp cabbage and carrots', ko: 'shred crisp cabbage and carrots 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll shred crisp cabbage and carrots?', fullPron: 'I\'ll shred crisp cabbage and carrots?', ko: 'shred crisp cabbage and carrots 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['shred crisp cabbage and carrots', 'whisk fresh eggs', 'melt rich butter']
        },
        fullEn: "You have to shred crisp cabbage and carrots into fine delicate ribbons.",
        fullPron: 'You have to + shred crisp cabbage and carrots + into fine delicate ribbons.',
        fullKo: '양배추와 당근, 대파를 아주 얇고 곱게 채 썰어 준비하기'
      },
      {
        stepTitle: 'SCENE 2 · Whisk Eggs with Shredded Vegetables',
        visualEmojis: '🥚 🥣 🥢',
        imagePath: '/images/kfood/ep39-thumb.jpg',
        actionNote: '볼에 달걀을 풀고 채 썬 채소와 소금 한 꼬집 섞기',
        coachKo: "코어 블록은 'whisk fresh eggs with vegetables'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'whisk fresh eggs with vegetables'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 볼에 달걀을 풀고 채 썬 채소와 소금 한 꼬집 섞기",
        missionEn: "Snap Mission! 'I\'m gonna whisk fresh eggs with vegetables until fully incorporated.' Snap!",
        keyVocab: 'whisk fresh eggs with vegetables',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'whisk fresh eggs with vegetables', pron: 'whisk fresh eggs with vegetables' },
          { role: 'db', en: 'until fully incorporated.', pron: 'until fully incorporated.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna whisk fresh eggs with vegetables.', fullPron: 'I\'m gonna whisk fresh eggs with vegetables', ko: 'whisk fresh eggs with vegetables 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to whisk fresh eggs with vegetables.', fullPron: 'You have to whisk fresh eggs with vegetables', ko: 'whisk fresh eggs with vegetables 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna whisk fresh eggs with vegetables?', fullPron: 'We\'re gonna whisk fresh eggs with vegetables?', ko: 'whisk fresh eggs with vegetables 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['whisk fresh eggs with vegetables', 'melt rich butter', 'toast white bread']
        },
        fullEn: "I\'m gonna whisk fresh eggs with vegetables until fully incorporated.",
        fullPron: 'I\'m gonna + whisk fresh eggs with vegetables + until fully incorporated.',
        fullKo: '볼에 달걀을 풀고 채 썬 채소와 소금 한 꼬집 섞기'
      },
      {
        stepTitle: 'SCENE 3 · Melt Rich Butter on Griddle',
        visualEmojis: '🧈 🍳 🔥',
        imagePath: '/images/kfood/ep39-thumb.jpg',
        actionNote: '뜨거운 팬에 고소한 버터를 듬뿍 녹여 풍미 가득 채우기',
        coachKo: "코어 블록은 'melt rich butter on griddle'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'melt rich butter on griddle'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뜨거운 팬에 고소한 버터를 듬뿍 녹여 풍미 가득 채우기",
        missionEn: "Snap Mission! 'We\'re gonna melt rich butter on griddle until bubbling and golden.' Snap!",
        keyVocab: 'melt rich butter on griddle',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'melt rich butter on griddle', pron: 'melt rich butter on griddle' },
          { role: 'db', en: 'until bubbling and golden.', pron: 'until bubbling and golden.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna melt rich butter on griddle.', fullPron: 'We\'re gonna melt rich butter on griddle', ko: 'melt rich butter on griddle 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna melt rich butter on griddle.', fullPron: 'I\'m gonna melt rich butter on griddle', ko: 'melt rich butter on griddle 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to melt rich butter on griddle?', fullPron: 'You have to melt rich butter on griddle?', ko: 'melt rich butter on griddle 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['melt rich butter on griddle', 'whisk fresh eggs', 'toast white bread']
        },
        fullEn: "We\'re gonna melt rich butter on griddle until bubbling and golden.",
        fullPron: 'We\'re gonna + melt rich butter on griddle + until bubbling and golden.',
        fullKo: '뜨거운 팬에 고소한 버터를 듬뿍 녹여 풍미 가득 채우기'
      },
      {
        stepTitle: 'SCENE 4 · Pan-Fry Square Egg Cabbage Patty',
        visualEmojis: '🍳 🥬 🟡',
        imagePath: '/images/kfood/ep39-thumb.jpg',
        actionNote: '달걀 야채 반죽을 식빵 크기 네모난 모양으로 도톰하게 부치기',
        coachKo: "코어 블록은 'pan-fry square cabbage egg patty'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pan-fry square cabbage egg patty'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달걀 야채 반죽을 식빵 크기 네모난 모양으로 도톰하게 부치기",
        missionEn: "Snap Mission! 'You have to pan-fry square cabbage egg patty into bread-sized golden shape.' Snap!",
        keyVocab: 'pan-fry square cabbage egg patty',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'pan-fry square cabbage egg patty', pron: 'pan-fry square cabbage egg patty' },
          { role: 'db', en: 'into bread-sized golden shape.', pron: 'into bread-sized golden shape.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to pan-fry square cabbage egg patty.', fullPron: 'You have to pan-fry square cabbage egg patty', ko: 'pan-fry square cabbage egg patty 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll pan-fry square cabbage egg patty.', fullPron: 'I\'ll pan-fry square cabbage egg patty', ko: 'pan-fry square cabbage egg patty 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pan-fry square cabbage egg patty?', fullPron: 'I\'m gonna pan-fry square cabbage egg patty?', ko: 'pan-fry square cabbage egg patty 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['pan-fry square cabbage egg patty', 'shred crisp cabbage', 'sprinkle sugar']
        },
        fullEn: "You have to pan-fry square cabbage egg patty into bread-sized golden shape.",
        fullPron: 'You have to + pan-fry square cabbage egg patty + into bread-sized golden shape.',
        fullKo: '달걀 야채 반죽을 식빵 크기 네모난 모양으로 도톰하게 부치기'
      },
      {
        stepTitle: 'SCENE 5 · Toast White Bread Golden & Crisp',
        visualEmojis: '🍞 🧈 ✨',
        imagePath: '/images/kfood/ep39-thumb.jpg',
        actionNote: '버터 두른 불판에 식빵을 앞뒤로 노릇노릇 바삭하게 굽기',
        coachKo: "코어 블록은 'toast white bread golden brown'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'toast white bread golden brown'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 버터 두른 불판에 식빵을 앞뒤로 노릇노릇 바삭하게 굽기",
        missionEn: "Snap Mission! 'I\'ll toast white bread golden brown with rich buttery aroma.' Snap!",
        keyVocab: 'toast white bread golden brown',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'toast white bread golden brown', pron: 'toast white bread golden brown' },
          { role: 'db', en: 'with rich buttery aroma.', pron: 'with rich buttery aroma.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll toast white bread golden brown.', fullPron: 'I\'ll toast white bread golden brown', ko: 'toast white bread golden brown 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna toast white bread golden brown.', fullPron: 'I\'m gonna toast white bread golden brown', ko: 'toast white bread golden brown 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to toast white bread golden brown?', fullPron: 'You have to toast white bread golden brown?', ko: 'toast white bread golden brown 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['toast white bread golden brown', 'fry cabbage patty', 'drizzle ketchup']
        },
        fullEn: "I\'ll toast white bread golden brown with rich buttery aroma.",
        fullPron: 'I\'ll + toast white bread golden brown + with rich buttery aroma.',
        fullKo: '버터 두른 불판에 식빵을 앞뒤로 노릇노릇 바삭하게 굽기'
      },
      {
        stepTitle: 'SCENE 6 · Sear Sliced Ham and American Cheese',
        visualEmojis: '🥓 🧀 🔥',
        imagePath: '/images/kfood/ep39-thumb.jpg',
        actionNote: '슬라이스 햄을 살짝 굽고 따뜻한 패티 위에 치즈 얹기',
        coachKo: "코어 블록은 'sear sliced ham and cheese'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sear sliced ham and cheese'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 슬라이스 햄을 살짝 굽고 따뜻한 패티 위에 치즈 얹기",
        missionEn: "Snap Mission! 'We\'re gonna sear sliced ham and cheese until cheese slightly melts.' Snap!",
        keyVocab: 'sear sliced ham and cheese',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'sear sliced ham and cheese', pron: 'sear sliced ham and cheese' },
          { role: 'db', en: 'until cheese slightly melts.', pron: 'until cheese slightly melts.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna sear sliced ham and cheese.', fullPron: 'We\'re gonna sear sliced ham and cheese', ko: 'sear sliced ham and cheese 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna sear sliced ham and cheese.', fullPron: 'I\'m gonna sear sliced ham and cheese', ko: 'sear sliced ham and cheese 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to sear sliced ham and cheese?', fullPron: 'You have to sear sliced ham and cheese?', ko: 'sear sliced ham and cheese 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['sear sliced ham and cheese', 'toast white bread', 'sprinkle sugar']
        },
        fullEn: "We\'re gonna sear sliced ham and cheese until cheese slightly melts.",
        fullPron: 'We\'re gonna + sear sliced ham and cheese + until cheese slightly melts.',
        fullKo: '슬라이스 햄을 살짝 굽고 따뜻한 패티 위에 치즈 얹기'
      },
      {
        stepTitle: 'SCENE 7 · Sprinkle Sugar & Drizzle Ketchup',
        visualEmojis: '🍬 🍅 🫙',
        imagePath: '/images/kfood/ep39-thumb.jpg',
        actionNote: '한국 길거리 토스트의 핵심: 설탕 솔솔 뿌리고 케첩 지그재그 두르기',
        coachKo: "코어 블록은 'sprinkle sugar and drizzle ketchup'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sprinkle sugar and drizzle ketchup'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 한국 길거리 토스트의 핵심: 설탕 솔솔 뿌리고 케첩 지그재그 두르기",
        missionEn: "Snap Mission! 'You have to sprinkle sugar and drizzle ketchup for signature sweet contrast.' Snap!",
        keyVocab: 'sprinkle sugar and drizzle ketchup',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'sprinkle sugar and drizzle ketchup', pron: 'sprinkle sugar and drizzle ketchup' },
          { role: 'db', en: 'for signature sweet contrast.', pron: 'for signature sweet contrast.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to sprinkle sugar and drizzle ketchup.', fullPron: 'You have to sprinkle sugar and drizzle ketchup', ko: 'sprinkle sugar and drizzle ketchup 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna sprinkle sugar and drizzle ketchup.', fullPron: 'I\'m gonna sprinkle sugar and drizzle ketchup', ko: 'sprinkle sugar and drizzle ketchup 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll sprinkle sugar and drizzle ketchup?', fullPron: 'I\'ll sprinkle sugar and drizzle ketchup?', ko: 'sprinkle sugar and drizzle ketchup 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['sprinkle sugar and drizzle ketchup', 'pan-fry egg patty', 'melt butter']
        },
        fullEn: "You have to sprinkle sugar and drizzle ketchup for signature sweet contrast.",
        fullPron: 'You have to + sprinkle sugar and drizzle ketchup + for signature sweet contrast.',
        fullKo: '한국 길거리 토스트의 핵심: 설탕 솔솔 뿌리고 케첩 지그재그 두르기'
      },
      {
        stepTitle: 'SCENE 8 · Sweet Savory Buttery & Irresistible',
        visualEmojis: '😋 🥪 🧈',
        imagePath: '/images/kfood/ep39-thumb.jpg',
        actionNote: '반으로 접어 종이컵에 쏙 넣어 따끈따끈 한 입 베어 물기',
        coachKo: "코어 블록은 'sweet savory buttery and irresistible'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sweet savory buttery and irresistible'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 반으로 접어 종이컵에 쏙 넣어 따끈따끈 한 입 베어 물기",
        missionEn: "Snap Mission! 'It\'s so sweet savory buttery and irresistible with pure nostalgic bliss!' Snap!",
        keyVocab: 'sweet savory buttery and irresistible',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'sweet savory buttery and irresistible', pron: 'sweet savory buttery and irresistible' },
          { role: 'db', en: 'with pure nostalgic bliss!', pron: 'with pure nostalgic bliss!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so sweet savory buttery and irresistible.', fullPron: 'It\'s so sweet savory buttery and irresistible', ko: 'sweet savory buttery and irresistible 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to sweet savory buttery and irresistible.', fullPron: 'You have to sweet savory buttery and irresistible', ko: 'sweet savory buttery and irresistible 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you sweet savory buttery and irresistible?', fullPron: 'Can you sweet savory buttery and irresistible?', ko: 'sweet savory buttery and irresistible 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['sweet savory buttery and irresistible', 'melt rich butter', 'pan-fry square patty']
        },
        fullEn: "It\'s so sweet savory buttery and irresistible with pure nostalgic bliss!",
        fullPron: 'It\'s so + sweet savory buttery and irresistible + with pure nostalgic bliss!',
        fullKo: '반으로 접어 종이컵에 쏙 넣어 따끈따끈 한 입 베어 물기'
      }
    ]
  },
  // ==========================================
  // EP.40. 🥟 Crispy Pan-Fried Dumplings
  // ==========================================
  {
    id: 'crispy-mandu',
    epNumber: 'EP.40',
    emoji: '🥟',
    shortTitle: '🥟 Crispy Pan-Fried Dumplings',
    title: 'How to Pan-Fry Crispy Juicy Korean Dumplings (Gun-Mandu)',
    ytTitle: 'How to Pan-Fry Crispy Korean Dumplings in Easy English 🥟 | SoundBlock K-Cooking EP.40',
    thumbnailText: 'Golden Crispy Gun-Mandu! [We\'re gonna] + [pan-fry juicy dumplings with lace skirt]',
    thumbnailImage: '/images/kfood/ep40-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s pan-fry ultra-crispy, juicy Korean Dumplings with golden lace crust and savory soy dipping sauce, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for crispy Gun-Mandu! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Arrange Plump Dumplings in Spiral Pan',
        visualEmojis: '🥟 🍳 ⭕',
        imagePath: '/images/kfood/ep40-thumb.jpg',
        actionNote: '기름 두른 팬에 통통한 만두를 둥글게 원형으로 정갈하게 놓기',
        coachKo: "코어 블록은 'arrange plump dumplings in pan'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'arrange plump dumplings in pan'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 기름 두른 팬에 통통한 만두를 둥글게 원형으로 정갈하게 놓기",
        missionEn: "Snap Mission! 'You have to arrange plump dumplings in pan in neat circular wheel.' Snap!",
        keyVocab: 'arrange plump dumplings in pan',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'arrange plump dumplings in pan', pron: 'arrange plump dumplings in pan' },
          { role: 'db', en: 'in neat circular wheel.', pron: 'in neat circular wheel.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to arrange plump dumplings in pan.', fullPron: 'You have to arrange plump dumplings in pan', ko: 'arrange plump dumplings in pan 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna arrange plump dumplings in pan.', fullPron: 'I\'m gonna arrange plump dumplings in pan', ko: 'arrange plump dumplings in pan 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll arrange plump dumplings in pan?', fullPron: 'I\'ll arrange plump dumplings in pan?', ko: 'arrange plump dumplings in pan 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['arrange plump dumplings in pan', 'mix flour slurry', 'sear golden bottom']
        },
        fullEn: "You have to arrange plump dumplings in pan in neat circular wheel.",
        fullPron: 'You have to + arrange plump dumplings in pan + in neat circular wheel.',
        fullKo: '기름 두른 팬에 통통한 만두를 둥글게 원형으로 정갈하게 놓기'
      },
      {
        stepTitle: 'SCENE 2 · Sear Bottoms Until Golden Brown',
        visualEmojis: '🔥 🍳 🥟',
        imagePath: '/images/kfood/ep40-thumb.jpg',
        actionNote: '중불에서 만두 밑바닥이 바삭하고 노릇해질 때까지 굽기',
        coachKo: "코어 블록은 'sear bottoms until golden brown'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sear bottoms until golden brown'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 중불에서 만두 밑바닥이 바삭하고 노릇해질 때까지 굽기",
        missionEn: "Snap Mission! 'I\'m gonna sear bottoms until golden brown with sizzling oil pop.' Snap!",
        keyVocab: 'sear bottoms until golden brown',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'sear bottoms until golden brown', pron: 'sear bottoms until golden brown' },
          { role: 'db', en: 'with sizzling oil pop.', pron: 'with sizzling oil pop.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna sear bottoms until golden brown.', fullPron: 'I\'m gonna sear bottoms until golden brown', ko: 'sear bottoms until golden brown 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to sear bottoms until golden brown.', fullPron: 'You have to sear bottoms until golden brown', ko: 'sear bottoms until golden brown 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna sear bottoms until golden brown?', fullPron: 'We\'re gonna sear bottoms until golden brown?', ko: 'sear bottoms until golden brown 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['sear bottoms until golden brown', 'mix flour slurry', 'steam with lid']
        },
        fullEn: "I\'m gonna sear bottoms until golden brown with sizzling oil pop.",
        fullPron: 'I\'m gonna + sear bottoms until golden brown + with sizzling oil pop.',
        fullKo: '중불에서 만두 밑바닥이 바삭하고 노릇해질 때까지 굽기'
      },
      {
        stepTitle: 'SCENE 3 · Mix Starch Water for Crispy Lace Skirt',
        visualEmojis: '🥣 🌾 💧',
        imagePath: '/images/kfood/ep40-thumb.jpg',
        actionNote: '전분과 물을 섞어 만두 밑에 눈꽃 날개를 만들어줄 전분물 준비',
        coachKo: "코어 블록은 'mix light starch water slurry'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix light starch water slurry'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 전분과 물을 섞어 만두 밑에 눈꽃 날개를 만들어줄 전분물 준비",
        missionEn: "Snap Mission! 'We\'re gonna mix light starch water slurry for that crispy lace skirt.' Snap!",
        keyVocab: 'mix light starch water slurry',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'mix light starch water slurry', pron: 'mix light starch water slurry' },
          { role: 'db', en: 'for that crispy lace skirt.', pron: 'for that crispy lace skirt.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna mix light starch water slurry.', fullPron: 'We\'re gonna mix light starch water slurry', ko: 'mix light starch water slurry 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix light starch water slurry.', fullPron: 'I\'m gonna mix light starch water slurry', ko: 'mix light starch water slurry 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix light starch water slurry?', fullPron: 'You have to mix light starch water slurry?', ko: 'mix light starch water slurry 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['mix light starch water slurry', 'arrange dumplings', 'cover with lid']
        },
        fullEn: "We\'re gonna mix light starch water slurry for that crispy lace skirt.",
        fullPron: 'We\'re gonna + mix light starch water slurry + for that crispy lace skirt.',
        fullKo: '전분과 물을 섞어 만두 밑에 눈꽃 날개를 만들어줄 전분물 준비'
      },
      {
        stepTitle: 'SCENE 4 · Pour Slurry & Cover with Tight Lid',
        visualEmojis: '💧 🍲 💨',
        imagePath: '/images/kfood/ep40-thumb.jpg',
        actionNote: '전분물을 부어 자작하게 한 뒤 뚜껑을 덮어 4분간 찌듯이 익히기',
        coachKo: "코어 블록은 'pour slurry and cover tightly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour slurry and cover tightly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 전분물을 부어 자작하게 한 뒤 뚜껑을 덮어 4분간 찌듯이 익히기",
        missionEn: "Snap Mission! 'You have to pour slurry and cover tightly to steam the juicy filling.' Snap!",
        keyVocab: 'pour slurry and cover tightly',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'pour slurry and cover tightly', pron: 'pour slurry and cover tightly' },
          { role: 'db', en: 'to steam the juicy filling.', pron: 'to steam the juicy filling.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to pour slurry and cover tightly.', fullPron: 'You have to pour slurry and cover tightly', ko: 'pour slurry and cover tightly 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll pour slurry and cover tightly.', fullPron: 'I\'ll pour slurry and cover tightly', ko: 'pour slurry and cover tightly 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour slurry and cover tightly?', fullPron: 'I\'m gonna pour slurry and cover tightly?', ko: 'pour slurry and cover tightly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['pour slurry and cover tightly', 'sear bottoms', 'uncover lid']
        },
        fullEn: "You have to pour slurry and cover tightly to steam the juicy filling.",
        fullPron: 'You have to + pour slurry and cover tightly + to steam the juicy filling.',
        fullKo: '전분물을 부어 자작하게 한 뒤 뚜껑을 덮어 4분간 찌듯이 익히기'
      },
      {
        stepTitle: 'SCENE 5 · Uncover to Crisp Up Thin Lace Skirt',
        visualEmojis: '💨 🍳 🥟',
        imagePath: '/images/kfood/ep40-thumb.jpg',
        actionNote: '뚜껑을 열고 수분을 날려 눈꽃 튀김옷이 바삭해지도록 굽기',
        coachKo: "코어 블록은 'uncover to crisp up lace'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'uncover to crisp up lace'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뚜껑을 열고 수분을 날려 눈꽃 튀김옷이 바삭해지도록 굽기",
        missionEn: "Snap Mission! 'I\'ll uncover to crisp up lace until water fully evaporates.' Snap!",
        keyVocab: 'uncover to crisp up lace',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'uncover to crisp up lace', pron: 'uncover to crisp up lace' },
          { role: 'db', en: 'until water fully evaporates.', pron: 'until water fully evaporates.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll uncover to crisp up lace.', fullPron: 'I\'ll uncover to crisp up lace', ko: 'uncover to crisp up lace 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna uncover to crisp up lace.', fullPron: 'I\'m gonna uncover to crisp up lace', ko: 'uncover to crisp up lace 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to uncover to crisp up lace?', fullPron: 'You have to uncover to crisp up lace?', ko: 'uncover to crisp up lace 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['uncover to crisp up lace', 'mix starch slurry', 'make soy dip']
        },
        fullEn: "I\'ll uncover to crisp up lace until water fully evaporates.",
        fullPron: 'I\'ll + uncover to crisp up lace + until water fully evaporates.',
        fullKo: '뚜껑을 열고 수분을 날려 눈꽃 튀김옷이 바삭해지도록 굽기'
      },
      {
        stepTitle: 'SCENE 6 · Invert Golden Crispy Disk onto Plate',
        visualEmojis: '🍽️ 🔄 🥟',
        imagePath: '/images/kfood/ep40-thumb.jpg',
        actionNote: '접시를 팬 위에 대고 한 번에 뒤집어 환상적인 눈꽃 모양 드러내기',
        coachKo: "코어 블록은 'invert crispy dumpling disk'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'invert crispy dumpling disk'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 접시를 팬 위에 대고 한 번에 뒤집어 환상적인 눈꽃 모양 드러내기",
        missionEn: "Snap Mission! 'We\'re gonna invert crispy dumpling disk upside down onto large plate.' Snap!",
        keyVocab: 'invert crispy dumpling disk',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'invert crispy dumpling disk', pron: 'invert crispy dumpling disk' },
          { role: 'db', en: 'upside down onto large plate.', pron: 'upside down onto large plate.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna invert crispy dumpling disk.', fullPron: 'We\'re gonna invert crispy dumpling disk', ko: 'invert crispy dumpling disk 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna invert crispy dumpling disk.', fullPron: 'I\'m gonna invert crispy dumpling disk', ko: 'invert crispy dumpling disk 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to invert crispy dumpling disk?', fullPron: 'You have to invert crispy dumpling disk?', ko: 'invert crispy dumpling disk 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['invert crispy dumpling disk', 'arrange dumplings', 'pour slurry']
        },
        fullEn: "We\'re gonna invert crispy dumpling disk upside down onto large plate.",
        fullPron: 'We\'re gonna + invert crispy dumpling disk + upside down onto large plate.',
        fullKo: '접시를 팬 위에 대고 한 번에 뒤집어 환상적인 눈꽃 모양 드러내기'
      },
      {
        stepTitle: 'SCENE 7 · Mix Tangy Soy Vinegar Dipping Sauce',
        visualEmojis: '🫙 🌶️ 🥢',
        imagePath: '/images/kfood/ep40-thumb.jpg',
        actionNote: '간장, 식초, 고춧가루를 섞어 기름기를 싹 잡아주는 초간장 완성',
        coachKo: "코어 블록은 'mix tangy soy vinegar dip'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix tangy soy vinegar dip'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 간장, 식초, 고춧가루를 섞어 기름기를 싹 잡아주는 초간장 완성",
        missionEn: "Snap Mission! 'You have to mix tangy soy vinegar dip with a pinch of chili flakes.' Snap!",
        keyVocab: 'mix tangy soy vinegar dip',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'mix tangy soy vinegar dip', pron: 'mix tangy soy vinegar dip' },
          { role: 'db', en: 'with a pinch of chili flakes.', pron: 'with a pinch of chili flakes.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to mix tangy soy vinegar dip.', fullPron: 'You have to mix tangy soy vinegar dip', ko: 'mix tangy soy vinegar dip 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix tangy soy vinegar dip.', fullPron: 'I\'m gonna mix tangy soy vinegar dip', ko: 'mix tangy soy vinegar dip 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll mix tangy soy vinegar dip?', fullPron: 'I\'ll mix tangy soy vinegar dip?', ko: 'mix tangy soy vinegar dip 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['mix tangy soy vinegar dip', 'sear bottoms', 'invert crispy disk']
        },
        fullEn: "You have to mix tangy soy vinegar dip with a pinch of chili flakes.",
        fullPron: 'You have to + mix tangy soy vinegar dip + with a pinch of chili flakes.',
        fullKo: '간장, 식초, 고춧가루를 섞어 기름기를 싹 잡아주는 초간장 완성'
      },
      {
        stepTitle: 'SCENE 8 · Super Crunchy Outside & Bursting Juicy',
        visualEmojis: '😋 🥟 💥',
        imagePath: '/images/kfood/ep40-thumb.jpg',
        actionNote: '파사삭 부서지는 눈꽃 튀김옷과 입안 가득 터지는 고기 육즙 즐기기',
        coachKo: "코어 블록은 'super crunchy outside and bursting juicy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'super crunchy outside and bursting juicy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 파사삭 부서지는 눈꽃 튀김옷과 입안 가득 터지는 고기 육즙 즐기기",
        missionEn: "Snap Mission! 'It\'s so super crunchy outside and bursting juicy with savory explosion inside!' Snap!",
        keyVocab: 'super crunchy outside and bursting juicy',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'super crunchy outside and bursting juicy', pron: 'super crunchy outside and bursting juicy' },
          { role: 'db', en: 'with savory explosion inside!', pron: 'with savory explosion inside!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so super crunchy outside and bursting juicy.', fullPron: 'It\'s so super crunchy outside and bursting juicy', ko: 'super crunchy outside and bursting juicy 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to super crunchy outside and bursting juicy.', fullPron: 'You have to super crunchy outside and bursting juicy', ko: 'super crunchy outside and bursting juicy 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you super crunchy outside and bursting juicy?', fullPron: 'Can you super crunchy outside and bursting juicy?', ko: 'super crunchy outside and bursting juicy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['super crunchy outside and bursting juicy', 'arrange plump dumplings', 'invert crispy disk']
        },
        fullEn: "It\'s so super crunchy outside and bursting juicy with savory explosion inside!",
        fullPron: 'It\'s so + super crunchy outside and bursting juicy + with savory explosion inside!',
        fullKo: '파사삭 부서지는 눈꽃 튀김옷과 입안 가득 터지는 고기 육즙 즐기기'
      }
    ]
  },
  // ==========================================
  // EP.41. 🍢 Street Fish Cake Skewers
  // ==========================================
  {
    id: 'eomuk-tang',
    epNumber: 'EP.41',
    emoji: '🍢',
    shortTitle: '🍢 Street Fish Cake Skewers',
    title: 'How to Cook Street-Style Korean Fish Cake Skewers with Warm Broth',
    ytTitle: 'How to Cook Korean Fish Cake Skewers in Easy English 🍢 | SoundBlock K-Cooking EP.41',
    thumbnailText: 'Street Fish Cake Skewers! [We\'re gonna] + [simmer folded fish cakes in rich anchovy broth]',
    thumbnailImage: '/images/kfood/ep41-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s simmer street-style Korean Fish Cake Skewers in steaming, savory radish anchovy broth, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for street-side Eomuk-tang! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Fold Flat Fish Cakes into Accordion',
        visualEmojis: '🍢 🔪 ✨',
        imagePath: '/images/kfood/ep41-thumb.jpg',
        actionNote: '사각 어묵을 3단으로 지그재그 접어 대나무 꼬치에 꿰기',
        coachKo: "코어 블록은 'fold flat fish cakes zigzag'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fold flat fish cakes zigzag'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 사각 어묵을 3단으로 지그재그 접어 대나무 꼬치에 꿰기",
        missionEn: "Snap Mission! 'You have to fold flat fish cakes zigzag and thread onto bamboo skewers.' Snap!",
        keyVocab: 'fold flat fish cakes zigzag',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'fold flat fish cakes zigzag', pron: 'fold flat fish cakes zigzag' },
          { role: 'db', en: 'and thread onto bamboo skewers.', pron: 'and thread onto bamboo skewers.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to fold flat fish cakes zigzag.', fullPron: 'You have to fold flat fish cakes zigzag', ko: 'fold flat fish cakes zigzag 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna fold flat fish cakes zigzag.', fullPron: 'I\'m gonna fold flat fish cakes zigzag', ko: 'fold flat fish cakes zigzag 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll fold flat fish cakes zigzag?', fullPron: 'I\'ll fold flat fish cakes zigzag?', ko: 'fold flat fish cakes zigzag 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['fold flat fish cakes zigzag', 'brew deep anchovy broth', 'simmer skewers']
        },
        fullEn: "You have to fold flat fish cakes zigzag and thread onto bamboo skewers.",
        fullPron: 'You have to + fold flat fish cakes zigzag + and thread onto bamboo skewers.',
        fullKo: '사각 어묵을 3단으로 지그재그 접어 대나무 꼬치에 꿰기'
      },
      {
        stepTitle: 'SCENE 2 · Brew Deep Anchovy Radish Broth',
        visualEmojis: '🐟 🤍 🍲',
        imagePath: '/images/kfood/ep41-thumb.jpg',
        actionNote: '멸치, 다시마, 두툼하게 썬 무, 대파 뿌리로 진한 국물 우려내기',
        coachKo: "코어 블록은 'brew deep anchovy radish broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'brew deep anchovy radish broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 멸치, 다시마, 두툼하게 썬 무, 대파 뿌리로 진한 국물 우려내기",
        missionEn: "Snap Mission! 'We\'re gonna brew deep anchovy radish broth for that comforting street flavor.' Snap!",
        keyVocab: 'brew deep anchovy radish broth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'brew deep anchovy radish broth', pron: 'brew deep anchovy radish broth' },
          { role: 'db', en: 'for that comforting street flavor.', pron: 'for that comforting street flavor.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna brew deep anchovy radish broth.', fullPron: 'We\'re gonna brew deep anchovy radish broth', ko: 'brew deep anchovy radish broth 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna brew deep anchovy radish broth.', fullPron: 'I\'m gonna brew deep anchovy radish broth', ko: 'brew deep anchovy radish broth 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to brew deep anchovy radish broth?', fullPron: 'You have to brew deep anchovy radish broth?', ko: 'brew deep anchovy radish broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['brew deep anchovy radish broth', 'fold flat fish cakes', 'season with soy sauce']
        },
        fullEn: "We\'re gonna brew deep anchovy radish broth for that comforting street flavor.",
        fullPron: 'We\'re gonna + brew deep anchovy radish broth + for that comforting street flavor.',
        fullKo: '멸치, 다시마, 두툼하게 썬 무, 대파 뿌리로 진한 국물 우려내기'
      },
      {
        stepTitle: 'SCENE 3 · Add Crab or Dried Pollack for Sweetness',
        visualEmojis: '🦀 🐟 🌊',
        imagePath: '/images/kfood/ep41-thumb.jpg',
        actionNote: '꽃게나 마른 황태를 넣어 국물에 바다의 시원한 감칠맛 더하기',
        coachKo: "코어 블록은 'add dried seafood for sweetness'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'add dried seafood for sweetness'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 꽃게나 마른 황태를 넣어 국물에 바다의 시원한 감칠맛 더하기",
        missionEn: "Snap Mission! 'I\'m gonna add dried seafood for sweetness to elevate broth richness.' Snap!",
        keyVocab: 'add dried seafood for sweetness',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'add dried seafood for sweetness', pron: 'add dried seafood for sweetness' },
          { role: 'db', en: 'to elevate broth richness.', pron: 'to elevate broth richness.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna add dried seafood for sweetness.', fullPron: 'I\'m gonna add dried seafood for sweetness', ko: 'add dried seafood for sweetness 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to add dried seafood for sweetness.', fullPron: 'You have to add dried seafood for sweetness', ko: 'add dried seafood for sweetness 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll add dried seafood for sweetness?', fullPron: 'I\'ll add dried seafood for sweetness?', ko: 'add dried seafood for sweetness 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "I\'ll"],
          coreCandidates: ['add dried seafood for sweetness', 'fold flat fish cakes', 'simmer skewers']
        },
        fullEn: "I\'m gonna add dried seafood for sweetness to elevate broth richness.",
        fullPron: 'I\'m gonna + add dried seafood for sweetness + to elevate broth richness.',
        fullKo: '꽃게나 마른 황태를 넣어 국물에 바다의 시원한 감칠맛 더하기'
      },
      {
        stepTitle: 'SCENE 4 · Submerge Skewers in Bubbling Broth',
        visualEmojis: '🍢 🍲 🔥',
        imagePath: '/images/kfood/ep41-thumb.jpg',
        actionNote: '육수가 끓으면 꼬치어묵들을 나란히 담가 국물이 쏙 배게 하기',
        coachKo: "코어 블록은 'submerge skewers in bubbling broth'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'submerge skewers in bubbling broth'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 육수가 끓으면 꼬치어묵들을 나란히 담가 국물이 쏙 배게 하기",
        missionEn: "Snap Mission! 'You have to submerge skewers in bubbling broth until delightfully soft and puffy.' Snap!",
        keyVocab: 'submerge skewers in bubbling broth',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'submerge skewers in bubbling broth', pron: 'submerge skewers in bubbling broth' },
          { role: 'db', en: 'until delightfully soft and puffy.', pron: 'until delightfully soft and puffy.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to submerge skewers in bubbling broth.', fullPron: 'You have to submerge skewers in bubbling broth', ko: 'submerge skewers in bubbling broth 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna submerge skewers in bubbling broth.', fullPron: 'I\'m gonna submerge skewers in bubbling broth', ko: 'submerge skewers in bubbling broth 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna submerge skewers in bubbling broth?', fullPron: 'We\'re gonna submerge skewers in bubbling broth?', ko: 'submerge skewers in bubbling broth 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "We\'re gonna"],
          coreCandidates: ['submerge skewers in bubbling broth', 'mix seasoned soy dip', 'fold flat fish cakes']
        },
        fullEn: "You have to submerge skewers in bubbling broth until delightfully soft and puffy.",
        fullPron: 'You have to + submerge skewers in bubbling broth + until delightfully soft and puffy.',
        fullKo: '육수가 끓으면 꼬치어묵들을 나란히 담가 국물이 쏙 배게 하기'
      },
      {
        stepTitle: 'SCENE 5 · Season with Soup Soy Sauce & Mirin',
        visualEmojis: '🫙 🧂 🍶',
        imagePath: '/images/kfood/ep41-thumb.jpg',
        actionNote: '국간장과 맛술, 천일염으로 깔끔하고 맑은 간 맞추기',
        coachKo: "코어 블록은 'season with soup soy sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'season with soup soy sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 국간장과 맛술, 천일염으로 깔끔하고 맑은 간 맞추기",
        missionEn: "Snap Mission! 'I\'ll season with soup soy sauce and a spoonful of mirin.' Snap!",
        keyVocab: 'season with soup soy sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'season with soup soy sauce', pron: 'season with soup soy sauce' },
          { role: 'db', en: 'and a spoonful of mirin.', pron: 'and a spoonful of mirin.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll season with soup soy sauce.', fullPron: 'I\'ll season with soup soy sauce', ko: 'season with soup soy sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna season with soup soy sauce.', fullPron: 'I\'m gonna season with soup soy sauce', ko: 'season with soup soy sauce 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to season with soup soy sauce?', fullPron: 'You have to season with soup soy sauce?', ko: 'season with soup soy sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['season with soup soy sauce', 'brew anchovy broth', 'submerge skewers']
        },
        fullEn: "I\'ll season with soup soy sauce and a spoonful of mirin.",
        fullPron: 'I\'ll + season with soup soy sauce + and a spoonful of mirin.',
        fullKo: '국간장과 맛술, 천일염으로 깔끔하고 맑은 간 맞추기'
      },
      {
        stepTitle: 'SCENE 6 · Slice Spicy Cheongyang & Scallions',
        visualEmojis: '🌶️ 🌿 🔪',
        imagePath: '/images/kfood/ep41-thumb.jpg',
        actionNote: '얼큰하고 칼칼한 국물 맛을 위해 청양고추와 대파 송송 썰기',
        coachKo: "코어 블록은 'slice spicy green chili peppers'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice spicy green chili peppers'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 얼큰하고 칼칼한 국물 맛을 위해 청양고추와 대파 송송 썰기",
        missionEn: "Snap Mission! 'We\'re gonna slice spicy green chili peppers for lively refreshing heat.' Snap!",
        keyVocab: 'slice spicy green chili peppers',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'slice spicy green chili peppers', pron: 'slice spicy green chili peppers' },
          { role: 'db', en: 'for lively refreshing heat.', pron: 'for lively refreshing heat.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna slice spicy green chili peppers.', fullPron: 'We\'re gonna slice spicy green chili peppers', ko: 'slice spicy green chili peppers 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice spicy green chili peppers.', fullPron: 'I\'m gonna slice spicy green chili peppers', ko: 'slice spicy green chili peppers 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to slice spicy green chili peppers?', fullPron: 'You have to slice spicy green chili peppers?', ko: 'slice spicy green chili peppers 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['slice spicy green chili peppers', 'fold fish cakes', 'mix soy dipping sauce']
        },
        fullEn: "We\'re gonna slice spicy green chili peppers for lively refreshing heat.",
        fullPron: 'We\'re gonna + slice spicy green chili peppers + for lively refreshing heat.',
        fullKo: '얼큰하고 칼칼한 국물 맛을 위해 청양고추와 대파 송송 썰기'
      },
      {
        stepTitle: 'SCENE 7 · Mix Seasoned Soy Dipping Sauce',
        visualEmojis: '🫙 🧄 🥢',
        imagePath: '/images/kfood/ep41-thumb.jpg',
        actionNote: '간장, 식초, 다진 파, 참깨를 섞어 꼬치 찍어 먹을 양념장 준비',
        coachKo: "코어 블록은 'mix seasoned soy dipping sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix seasoned soy dipping sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 간장, 식초, 다진 파, 참깨를 섞어 꼬치 찍어 먹을 양념장 준비",
        missionEn: "Snap Mission! 'You have to mix seasoned soy dipping sauce with chopped scallions and sesame.' Snap!",
        keyVocab: 'mix seasoned soy dipping sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'mix seasoned soy dipping sauce', pron: 'mix seasoned soy dipping sauce' },
          { role: 'db', en: 'with chopped scallions and sesame.', pron: 'with chopped scallions and sesame.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to mix seasoned soy dipping sauce.', fullPron: 'You have to mix seasoned soy dipping sauce', ko: 'mix seasoned soy dipping sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix seasoned soy dipping sauce.', fullPron: 'I\'m gonna mix seasoned soy dipping sauce', ko: 'mix seasoned soy dipping sauce 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll mix seasoned soy dipping sauce?', fullPron: 'I\'ll mix seasoned soy dipping sauce?', ko: 'mix seasoned soy dipping sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['mix seasoned soy dipping sauce', 'submerge skewers', 'brew radish broth']
        },
        fullEn: "You have to mix seasoned soy dipping sauce with chopped scallions and sesame.",
        fullPron: 'You have to + mix seasoned soy dipping sauce + with chopped scallions and sesame.',
        fullKo: '간장, 식초, 다진 파, 참깨를 섞어 꼬치 찍어 먹을 양념장 준비'
      },
      {
        stepTitle: 'SCENE 8 · Piping Hot Broth & Tender Chewy Skewer',
        visualEmojis: '😋 🍢 💨',
        imagePath: '/images/kfood/ep41-thumb.jpg',
        actionNote: '종이컵에 뜨거운 국물 호호 불며 떠마시고 어묵 간장에 콕 찍기',
        coachKo: "코어 블록은 'piping hot broth and tender chewy skewer'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'piping hot broth and tender chewy skewer'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 종이컵에 뜨거운 국물 호호 불며 떠마시고 어묵 간장에 콕 찍기",
        missionEn: "Snap Mission! 'It\'s so piping hot broth and tender chewy skewer warming up the entire soul!' Snap!",
        keyVocab: 'piping hot broth and tender chewy skewer',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'piping hot broth and tender chewy skewer', pron: 'piping hot broth and tender chewy skewer' },
          { role: 'db', en: 'warming up the entire soul!', pron: 'warming up the entire soul!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so piping hot broth and tender chewy skewer.', fullPron: 'It\'s so piping hot broth and tender chewy skewer', ko: 'piping hot broth and tender chewy skewer 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to piping hot broth and tender chewy skewer.', fullPron: 'You have to piping hot broth and tender chewy skewer', ko: 'piping hot broth and tender chewy skewer 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you piping hot broth and tender chewy skewer?', fullPron: 'Can you piping hot broth and tender chewy skewer?', ko: 'piping hot broth and tender chewy skewer 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['piping hot broth and tender chewy skewer', 'fold flat fish cakes', 'submerge skewers']
        },
        fullEn: "It\'s so piping hot broth and tender chewy skewer warming up the entire soul!",
        fullPron: 'It\'s so + piping hot broth and tender chewy skewer + warming up the entire soul!',
        fullKo: '종이컵에 뜨거운 국물 호호 불며 떠마시고 어묵 간장에 콕 찍기'
      }
    ]
  },
  // ==========================================
  // EP.42. 🥞 Sweet Hotteok & Fish Pastry
  // ==========================================
  {
    id: 'hotteok-bungeoppang',
    epNumber: 'EP.42',
    emoji: '🥞',
    shortTitle: '🥞 Sweet Hotteok & Fish Pastry',
    title: 'How to Enjoy Korean Winter Street Treats Hotteok and Bungeoppang',
    ytTitle: 'How to Make Korean Winter Hotteok & Fish Pastry in Easy English 🥞 | SoundBlock K-Cooking EP.42',
    thumbnailText: 'Winter Sweet Treats! [I\'m gonna] + [press sweet cinnamon hotteok on sizzling griddle]',
    thumbnailImage: '/images/kfood/ep42-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make Korean winter street legends: sweet cinnamon brown sugar Hotteok and crispy sweet red bean Bungeoppang, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for winter sweet treats! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Knead Soft Chewy Glutinous Dough',
        visualEmojis: '🌾 🥣 🧑‍🍳',
        imagePath: '/images/kfood/ep42-thumb.jpg',
        actionNote: '찹쌀가루와 이스트를 섞어 쫄깃하고 부드럽게 반죽해 발효하기',
        coachKo: "코어 블록은 'knead soft glutinous rice dough'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'knead soft glutinous rice dough'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 찹쌀가루와 이스트를 섞어 쫄깃하고 부드럽게 반죽해 발효하기",
        missionEn: "Snap Mission! 'You have to knead soft glutinous rice dough until smooth and elastic.' Snap!",
        keyVocab: 'knead soft glutinous rice dough',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'knead soft glutinous rice dough', pron: 'knead soft glutinous rice dough' },
          { role: 'db', en: 'until smooth and elastic.', pron: 'until smooth and elastic.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to knead soft glutinous rice dough.', fullPron: 'You have to knead soft glutinous rice dough', ko: 'knead soft glutinous rice dough 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna knead soft glutinous rice dough.', fullPron: 'I\'m gonna knead soft glutinous rice dough', ko: 'knead soft glutinous rice dough 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll knead soft glutinous rice dough?', fullPron: 'I\'ll knead soft glutinous rice dough?', ko: 'knead soft glutinous rice dough 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['knead soft glutinous rice dough', 'mix cinnamon sugar', 'press on hot griddle']
        },
        fullEn: "You have to knead soft glutinous rice dough until smooth and elastic.",
        fullPron: 'You have to + knead soft glutinous rice dough + until smooth and elastic.',
        fullKo: '찹쌀가루와 이스트를 섞어 쫄깃하고 부드럽게 반죽해 발효하기'
      },
      {
        stepTitle: 'SCENE 2 · Mix Brown Sugar Cinnamon Peanut Filling',
        visualEmojis: '🍯 🥜 🧂',
        imagePath: '/images/kfood/ep42-thumb.jpg',
        actionNote: '흑설탕, 계피가루, 다진 땅콩을 듬뿍 섞어 달콤한 꿀소 만들기',
        coachKo: "코어 블록은 'mix brown sugar cinnamon filling'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix brown sugar cinnamon filling'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 흑설탕, 계피가루, 다진 땅콩을 듬뿍 섞어 달콤한 꿀소 만들기",
        missionEn: "Snap Mission! 'I\'m gonna mix brown sugar cinnamon filling with crunchy roasted peanuts.' Snap!",
        keyVocab: 'mix brown sugar cinnamon filling',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'mix brown sugar cinnamon filling', pron: 'mix brown sugar cinnamon filling' },
          { role: 'db', en: 'with crunchy roasted peanuts.', pron: 'with crunchy roasted peanuts.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix brown sugar cinnamon filling.', fullPron: 'I\'m gonna mix brown sugar cinnamon filling', ko: 'mix brown sugar cinnamon filling 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix brown sugar cinnamon filling.', fullPron: 'You have to mix brown sugar cinnamon filling', ko: 'mix brown sugar cinnamon filling 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna mix brown sugar cinnamon filling?', fullPron: 'We\'re gonna mix brown sugar cinnamon filling?', ko: 'mix brown sugar cinnamon filling 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['mix brown sugar cinnamon filling', 'knead rice dough', 'press on griddle']
        },
        fullEn: "I\'m gonna mix brown sugar cinnamon filling with crunchy roasted peanuts.",
        fullPron: 'I\'m gonna + mix brown sugar cinnamon filling + with crunchy roasted peanuts.',
        fullKo: '흑설탕, 계피가루, 다진 땅콩을 듬뿍 섞어 달콤한 꿀소 만들기'
      },
      {
        stepTitle: 'SCENE 3 · Stuff Dough and Seal Firmly',
        visualEmojis: '🥟 👐 🍯',
        imagePath: '/images/kfood/ep42-thumb.jpg',
        actionNote: '반죽 한 덩이를 펴서 흑설탕 속을 듬뿍 넣고 새지 않게 오므리기',
        coachKo: "코어 블록은 'stuff dough and seal firmly'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stuff dough and seal firmly'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 반죽 한 덩이를 펴서 흑설탕 속을 듬뿍 넣고 새지 않게 오므리기",
        missionEn: "Snap Mission! 'We\'re gonna stuff dough and seal firmly into neat seamless round ball.' Snap!",
        keyVocab: 'stuff dough and seal firmly',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'stuff dough and seal firmly', pron: 'stuff dough and seal firmly' },
          { role: 'db', en: 'into neat seamless round ball.', pron: 'into neat seamless round ball.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna stuff dough and seal firmly.', fullPron: 'We\'re gonna stuff dough and seal firmly', ko: 'stuff dough and seal firmly 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna stuff dough and seal firmly.', fullPron: 'I\'m gonna stuff dough and seal firmly', ko: 'stuff dough and seal firmly 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to stuff dough and seal firmly?', fullPron: 'You have to stuff dough and seal firmly?', ko: 'stuff dough and seal firmly 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['stuff dough and seal firmly', 'press on hot griddle', 'pour batter in fish mold']
        },
        fullEn: "We\'re gonna stuff dough and seal firmly into neat seamless round ball.",
        fullPron: 'We\'re gonna + stuff dough and seal firmly + into neat seamless round ball.',
        fullKo: '반죽 한 덩이를 펴서 흑설탕 속을 듬뿍 넣고 새지 않게 오므리기'
      },
      {
        stepTitle: 'SCENE 4 · Press on Sizzling Oiled Griddle',
        visualEmojis: '🍳 🧈 🔥',
        imagePath: '/images/kfood/ep42-thumb.jpg',
        actionNote: '기름 두른 팬에 반죽을 올리고 호떡 누르개로 둥글납작하게 누르기',
        coachKo: "코어 블록은 'press on sizzling hot griddle'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'press on sizzling hot griddle'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 기름 두른 팬에 반죽을 올리고 호떡 누르개로 둥글납작하게 누르기",
        missionEn: "Snap Mission! 'You have to press on sizzling hot griddle with stainless steel press.' Snap!",
        keyVocab: 'press on sizzling hot griddle',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'press on sizzling hot griddle', pron: 'press on sizzling hot griddle' },
          { role: 'db', en: 'with stainless steel press.', pron: 'with stainless steel press.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to press on sizzling hot griddle.', fullPron: 'You have to press on sizzling hot griddle', ko: 'press on sizzling hot griddle 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll press on sizzling hot griddle.', fullPron: 'I\'ll press on sizzling hot griddle', ko: 'press on sizzling hot griddle 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna press on sizzling hot griddle?', fullPron: 'I\'m gonna press on sizzling hot griddle?', ko: 'press on sizzling hot griddle 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['press on sizzling hot griddle', 'knead soft dough', 'mix cinnamon sugar']
        },
        fullEn: "You have to press on sizzling hot griddle with stainless steel press.",
        fullPron: 'You have to + press on sizzling hot griddle + with stainless steel press.',
        fullKo: '기름 두른 팬에 반죽을 올리고 호떡 누르개로 둥글납작하게 누르기'
      },
      {
        stepTitle: 'SCENE 5 · Fry Until Golden Crisp on Both Sides',
        visualEmojis: '⏳ 🔥 ✨',
        imagePath: '/images/kfood/ep42-thumb.jpg',
        actionNote: '속의 설탕이 꿀처럼 녹아내릴 때까지 앞뒤로 노릇노릇 굽기',
        coachKo: "코어 블록은 'fry until golden and crispy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fry until golden and crispy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 속의 설탕이 꿀처럼 녹아내릴 때까지 앞뒤로 노릇노릇 굽기",
        missionEn: "Snap Mission! 'I\'ll fry until golden and crispy with bubbling syrup inside.' Snap!",
        keyVocab: 'fry until golden and crispy',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'fry until golden and crispy', pron: 'fry until golden and crispy' },
          { role: 'db', en: 'with bubbling syrup inside.', pron: 'with bubbling syrup inside.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll fry until golden and crispy.', fullPron: 'I\'ll fry until golden and crispy', ko: 'fry until golden and crispy 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna fry until golden and crispy.', fullPron: 'I\'m gonna fry until golden and crispy', ko: 'fry until golden and crispy 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to fry until golden and crispy?', fullPron: 'You have to fry until golden and crispy?', ko: 'fry until golden and crispy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['fry until golden and crispy', 'stuff dough firmly', 'press on griddle']
        },
        fullEn: "I\'ll fry until golden and crispy with bubbling syrup inside.",
        fullPron: 'I\'ll + fry until golden and crispy + with bubbling syrup inside.',
        fullKo: '속의 설탕이 꿀처럼 녹아내릴 때까지 앞뒤로 노릇노릇 굽기'
      },
      {
        stepTitle: 'SCENE 6 · Pour Batter into Fish-Shaped Mold',
        visualEmojis: '🐟 🍳 🟡',
        imagePath: '/images/kfood/ep42-thumb.jpg',
        actionNote: '뜨거운 붕어빵 틀에 반죽을 얇게 붓고 달콤한 통팥 앙금 얹기',
        coachKo: "코어 블록은 'pour batter in fish-shaped mold'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour batter in fish-shaped mold'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뜨거운 붕어빵 틀에 반죽을 얇게 붓고 달콤한 통팥 앙금 얹기",
        missionEn: "Snap Mission! 'We\'re gonna pour batter in fish-shaped mold and add sweet red bean paste.' Snap!",
        keyVocab: 'pour batter in fish-shaped mold',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'pour batter in fish-shaped mold', pron: 'pour batter in fish-shaped mold' },
          { role: 'db', en: 'and add sweet red bean paste.', pron: 'and add sweet red bean paste.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna pour batter in fish-shaped mold.', fullPron: 'We\'re gonna pour batter in fish-shaped mold', ko: 'pour batter in fish-shaped mold 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour batter in fish-shaped mold.', fullPron: 'I\'m gonna pour batter in fish-shaped mold', ko: 'pour batter in fish-shaped mold 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour batter in fish-shaped mold?', fullPron: 'You have to pour batter in fish-shaped mold?', ko: 'pour batter in fish-shaped mold 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['pour batter in fish-shaped mold', 'knead rice dough', 'press on griddle']
        },
        fullEn: "We\'re gonna pour batter in fish-shaped mold and add sweet red bean paste.",
        fullPron: 'We\'re gonna + pour batter in fish-shaped mold + and add sweet red bean paste.',
        fullKo: '뜨거운 붕어빵 틀에 반죽을 얇게 붓고 달콤한 통팥 앙금 얹기'
      },
      {
        stepTitle: 'SCENE 7 · Flip Mold to Bake Crispy Wings',
        visualEmojis: '🔄 🐟 🔥',
        imagePath: '/images/kfood/ep42-thumb.jpg',
        actionNote: '틀을 돌려가며 꼬리까지 바삭바삭한 황금빛 붕어빵 구워내기',
        coachKo: "코어 블록은 'flip mold to bake crispy wings'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'flip mold to bake crispy wings'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 틀을 돌려가며 꼬리까지 바삭바삭한 황금빛 붕어빵 구워내기",
        missionEn: "Snap Mission! 'You have to flip mold to bake crispy wings until outer crust turns snappy.' Snap!",
        keyVocab: 'flip mold to bake crispy wings',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'flip mold to bake crispy wings', pron: 'flip mold to bake crispy wings' },
          { role: 'db', en: 'until outer crust turns snappy.', pron: 'until outer crust turns snappy.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to flip mold to bake crispy wings.', fullPron: 'You have to flip mold to bake crispy wings', ko: 'flip mold to bake crispy wings 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna flip mold to bake crispy wings.', fullPron: 'I\'m gonna flip mold to bake crispy wings', ko: 'flip mold to bake crispy wings 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll flip mold to bake crispy wings?', fullPron: 'I\'ll flip mold to bake crispy wings?', ko: 'flip mold to bake crispy wings 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['flip mold to bake crispy wings', 'fry until golden', 'mix cinnamon sugar']
        },
        fullEn: "You have to flip mold to bake crispy wings until outer crust turns snappy.",
        fullPron: 'You have to + flip mold to bake crispy wings + until outer crust turns snappy.',
        fullKo: '틀을 돌려가며 꼬리까지 바삭바삭한 황금빛 붕어빵 구워내기'
      },
      {
        stepTitle: 'SCENE 8 · Molten Syrup & Crispy Sweet Comfort',
        visualEmojis: '😋 🥞 🍯',
        imagePath: '/images/kfood/ep42-thumb.jpg',
        actionNote: '종이컵에 든 호떡을 베어 물어 꿀시럽을 후후 불며 맛보기',
        coachKo: "코어 블록은 'molten syrup and crispy sweet comfort'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'molten syrup and crispy sweet comfort'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 종이컵에 든 호떡을 베어 물어 꿀시럽을 후후 불며 맛보기",
        missionEn: "Snap Mission! 'It\'s so molten syrup and crispy sweet comfort heating up freezing winter days!' Snap!",
        keyVocab: 'molten syrup and crispy sweet comfort',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'molten syrup and crispy sweet comfort', pron: 'molten syrup and crispy sweet comfort' },
          { role: 'db', en: 'heating up freezing winter days!', pron: 'heating up freezing winter days!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so molten syrup and crispy sweet comfort.', fullPron: 'It\'s so molten syrup and crispy sweet comfort', ko: 'molten syrup and crispy sweet comfort 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to molten syrup and crispy sweet comfort.', fullPron: 'You have to molten syrup and crispy sweet comfort', ko: 'molten syrup and crispy sweet comfort 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you molten syrup and crispy sweet comfort?', fullPron: 'Can you molten syrup and crispy sweet comfort?', ko: 'molten syrup and crispy sweet comfort 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['molten syrup and crispy sweet comfort', 'knead soft dough', 'press on sizzling griddle']
        },
        fullEn: "It\'s so molten syrup and crispy sweet comfort heating up freezing winter days!",
        fullPron: 'It\'s so + molten syrup and crispy sweet comfort + heating up freezing winter days!',
        fullKo: '종이컵에 든 호떡을 베어 물어 꿀시럽을 후후 불며 맛보기'
      }
    ]
  },
  // ==========================================
  // EP.43. 🍳 Volcanic Steamed Egg
  // ==========================================
  {
    id: 'gyeran-jjim',
    epNumber: 'EP.43',
    emoji: '🍳',
    shortTitle: '🍳 Volcanic Steamed Egg',
    title: 'How to Make Fluffy Korean Volcanic Steamed Egg in an Earthen Pot',
    ytTitle: 'How to Make Fluffy Korean Volcanic Steamed Egg in Easy English 🍳 | SoundBlock K-Cooking EP.43',
    thumbnailText: 'Fluffy Volcanic Steamed Egg! [We\'re gonna] + [puff up whipped eggs in piping hot ttukbaegi]',
    thumbnailImage: '/images/kfood/ep43-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s cook cloud-soft Korean Volcanic Steamed Egg, puffed up high in an authentic earthen pot with scallions and sesame oil, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for fluffy Gyeran-jjim! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Whisk Six Fresh Eggs Vigorously',
        visualEmojis: '🥚 🥣 🥢',
        imagePath: '/images/kfood/ep43-thumb.jpg',
        actionNote: '신선한 달걀 6개를 볼에 깨 넣고 멍울 없이 곱게 풀기',
        coachKo: "코어 블록은 'whisk six fresh eggs vigorously'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'whisk six fresh eggs vigorously'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 신선한 달걀 6개를 볼에 깨 넣고 멍울 없이 곱게 풀기",
        missionEn: "Snap Mission! 'You have to whisk six fresh eggs vigorously until light and foamy.' Snap!",
        keyVocab: 'whisk six fresh eggs vigorously',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'whisk six fresh eggs vigorously', pron: 'whisk six fresh eggs vigorously' },
          { role: 'db', en: 'until light and foamy.', pron: 'until light and foamy.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to whisk six fresh eggs vigorously.', fullPron: 'You have to whisk six fresh eggs vigorously', ko: 'whisk six fresh eggs vigorously 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna whisk six fresh eggs vigorously.', fullPron: 'I\'m gonna whisk six fresh eggs vigorously', ko: 'whisk six fresh eggs vigorously 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll whisk six fresh eggs vigorously?', fullPron: 'I\'ll whisk six fresh eggs vigorously?', ko: 'whisk six fresh eggs vigorously 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['whisk six fresh eggs vigorously', 'season with salted shrimp', 'cover with dome bowl']
        },
        fullEn: "You have to whisk six fresh eggs vigorously until light and foamy.",
        fullPron: 'You have to + whisk six fresh eggs vigorously + until light and foamy.',
        fullKo: '신선한 달걀 6개를 볼에 깨 넣고 멍울 없이 곱게 풀기'
      },
      {
        stepTitle: 'SCENE 2 · Season with Salted Shrimp & Fish Sauce',
        visualEmojis: '🦐 🫙 🧂',
        imagePath: '/images/kfood/ep43-thumb.jpg',
        actionNote: '새우젓 다진 것과 멸치액젓, 참기름으로 고소한 감칠맛 맞추기',
        coachKo: "코어 블록은 'season with finely minced salted shrimp'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'season with finely minced salted shrimp'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 새우젓 다진 것과 멸치액젓, 참기름으로 고소한 감칠맛 맞추기",
        missionEn: "Snap Mission! 'I\'m gonna season with finely minced salted shrimp for authentic savory depth.' Snap!",
        keyVocab: 'season with finely minced salted shrimp',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'season with finely minced salted shrimp', pron: 'season with finely minced salted shrimp' },
          { role: 'db', en: 'for authentic savory depth.', pron: 'for authentic savory depth.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna season with finely minced salted shrimp.', fullPron: 'I\'m gonna season with finely minced salted shrimp', ko: 'season with finely minced salted shrimp 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to season with finely minced salted shrimp.', fullPron: 'You have to season with finely minced salted shrimp', ko: 'season with finely minced salted shrimp 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna season with finely minced salted shrimp?', fullPron: 'We\'re gonna season with finely minced salted shrimp?', ko: 'season with finely minced salted shrimp 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['season with finely minced salted shrimp', 'whisk fresh eggs', 'stir constantly']
        },
        fullEn: "I\'m gonna season with finely minced salted shrimp for authentic savory depth.",
        fullPron: 'I\'m gonna + season with finely minced salted shrimp + for authentic savory depth.',
        fullKo: '새우젓 다진 것과 멸치액젓, 참기름으로 고소한 감칠맛 맞추기'
      },
      {
        stepTitle: 'SCENE 3 · Pour Kelp Broth into Small Earthen Pot',
        visualEmojis: '🍲 💧 🔥',
        imagePath: '/images/kfood/ep43-thumb.jpg',
        actionNote: '뚝배기에 멸치 다시마 육수를 붓고 센 불에서 먼저 끓이기',
        coachKo: "코어 블록은 'pour kelp broth in earthen pot'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour kelp broth in earthen pot'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뚝배기에 멸치 다시마 육수를 붓고 센 불에서 먼저 끓이기",
        missionEn: "Snap Mission! 'We\'re gonna pour kelp broth in earthen pot and bring to rolling boil.' Snap!",
        keyVocab: 'pour kelp broth in earthen pot',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'pour kelp broth in earthen pot', pron: 'pour kelp broth in earthen pot' },
          { role: 'db', en: 'and bring to rolling boil.', pron: 'and bring to rolling boil.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna pour kelp broth in earthen pot.', fullPron: 'We\'re gonna pour kelp broth in earthen pot', ko: 'pour kelp broth in earthen pot 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour kelp broth in earthen pot.', fullPron: 'I\'m gonna pour kelp broth in earthen pot', ko: 'pour kelp broth in earthen pot 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour kelp broth in earthen pot?', fullPron: 'You have to pour kelp broth in earthen pot?', ko: 'pour kelp broth in earthen pot 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['pour kelp broth in earthen pot', 'whisk fresh eggs', 'cover with bowl']
        },
        fullEn: "We\'re gonna pour kelp broth in earthen pot and bring to rolling boil.",
        fullPron: 'We\'re gonna + pour kelp broth in earthen pot + and bring to rolling boil.',
        fullKo: '뚝배기에 멸치 다시마 육수를 붓고 센 불에서 먼저 끓이기'
      },
      {
        stepTitle: 'SCENE 4 · Pour Egg Mixture and Scrape Bottom',
        visualEmojis: '🥚 🍲 🥄',
        imagePath: '/images/kfood/ep43-thumb.jpg',
        actionNote: '육수가 끓으면 계란물을 붓고 바닥이 타지 않게 숟가락으로 긁기',
        coachKo: "코어 블록은 'scrape bottom continuously with spoon'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'scrape bottom continuously with spoon'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 육수가 끓으면 계란물을 붓고 바닥이 타지 않게 숟가락으로 긁기",
        missionEn: "Snap Mission! 'You have to scrape bottom continuously with spoon as soft egg curds begin to form.' Snap!",
        keyVocab: 'scrape bottom continuously with spoon',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'scrape bottom continuously with spoon', pron: 'scrape bottom continuously with spoon' },
          { role: 'db', en: 'as soft egg curds begin to form.', pron: 'as soft egg curds begin to form.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to scrape bottom continuously with spoon.', fullPron: 'You have to scrape bottom continuously with spoon', ko: 'scrape bottom continuously with spoon 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll scrape bottom continuously with spoon.', fullPron: 'I\'ll scrape bottom continuously with spoon', ko: 'scrape bottom continuously with spoon 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna scrape bottom continuously with spoon?', fullPron: 'I\'m gonna scrape bottom continuously with spoon?', ko: 'scrape bottom continuously with spoon 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['scrape bottom continuously with spoon', 'pour kelp broth', 'cover with dome bowl']
        },
        fullEn: "You have to scrape bottom continuously with spoon as soft egg curds begin to form.",
        fullPron: 'You have to + scrape bottom continuously with spoon + as soft egg curds begin to form.',
        fullKo: '육수가 끓으면 계란물을 붓고 바닥이 타지 않게 숟가락으로 긁기'
      },
      {
        stepTitle: 'SCENE 5 · Stir Until Eighty Percent Solidified',
        visualEmojis: '🥄 ⏳ 🔥',
        imagePath: '/images/kfood/ep43-thumb.jpg',
        actionNote: '달걀이 몽글몽글 80% 정도 익을 때까지 계속 저어주기',
        coachKo: "코어 블록은 'stir until eighty percent solidified'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'stir until eighty percent solidified'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달걀이 몽글몽글 80% 정도 익을 때까지 계속 저어주기",
        missionEn: "Snap Mission! 'I\'ll stir until eighty percent solidified into thick creamy scramble.' Snap!",
        keyVocab: 'stir until eighty percent solidified',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'stir until eighty percent solidified', pron: 'stir until eighty percent solidified' },
          { role: 'db', en: 'into thick creamy scramble.', pron: 'into thick creamy scramble.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll stir until eighty percent solidified.', fullPron: 'I\'ll stir until eighty percent solidified', ko: 'stir until eighty percent solidified 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna stir until eighty percent solidified.', fullPron: 'I\'m gonna stir until eighty percent solidified', ko: 'stir until eighty percent solidified 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to stir until eighty percent solidified?', fullPron: 'You have to stir until eighty percent solidified?', ko: 'stir until eighty percent solidified 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['stir until eighty percent solidified', 'whisk fresh eggs', 'season with shrimp']
        },
        fullEn: "I\'ll stir until eighty percent solidified into thick creamy scramble.",
        fullPron: 'I\'ll + stir until eighty percent solidified + into thick creamy scramble.',
        fullKo: '달걀이 몽글몽글 80% 정도 익을 때까지 계속 저어주기'
      },
      {
        stepTitle: 'SCENE 6 · Cover with Domed Glass Bowl on Low Heat',
        visualEmojis: '🥣 🍲 💨',
        imagePath: '/images/kfood/ep43-thumb.jpg',
        actionNote: '약불로 줄이고 오목한 그릇을 뚜껑처럼 덮어 봉긋 솟아오르게 찌기',
        coachKo: "코어 블록은 'cover with domed bowl on low heat'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'cover with domed bowl on low heat'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 약불로 줄이고 오목한 그릇을 뚜껑처럼 덮어 봉긋 솟아오르게 찌기",
        missionEn: "Snap Mission! 'We\'re gonna cover with domed bowl on low heat trapping steam to puff it up.' Snap!",
        keyVocab: 'cover with domed bowl on low heat',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'cover with domed bowl on low heat', pron: 'cover with domed bowl on low heat' },
          { role: 'db', en: 'trapping steam to puff it up.', pron: 'trapping steam to puff it up.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna cover with domed bowl on low heat.', fullPron: 'We\'re gonna cover with domed bowl on low heat', ko: 'cover with domed bowl on low heat 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna cover with domed bowl on low heat.', fullPron: 'I\'m gonna cover with domed bowl on low heat', ko: 'cover with domed bowl on low heat 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to cover with domed bowl on low heat?', fullPron: 'You have to cover with domed bowl on low heat?', ko: 'cover with domed bowl on low heat 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['cover with domed bowl on low heat', 'scrape bottom continuously', 'garnish with scallions']
        },
        fullEn: "We\'re gonna cover with domed bowl on low heat trapping steam to puff it up.",
        fullPron: 'We\'re gonna + cover with domed bowl on low heat + trapping steam to puff it up.',
        fullKo: '약불로 줄이고 오목한 그릇을 뚜껑처럼 덮어 봉긋 솟아오르게 찌기'
      },
      {
        stepTitle: 'SCENE 7 · Garnish with Green Scallions & Sesame',
        visualEmojis: '🌿 🌰 🫙',
        imagePath: '/images/kfood/ep43-thumb.jpg',
        actionNote: '뚜껑을 열고 모락모락 김 나는 봉긋한 달걀 위에 파와 깨 얹기',
        coachKo: "코어 블록은 'garnish with scallions and sesame'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'garnish with scallions and sesame'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 뚜껑을 열고 모락모락 김 나는 봉긋한 달걀 위에 파와 깨 얹기",
        missionEn: "Snap Mission! 'You have to garnish with scallions and sesame and a glossy drop of sesame oil.' Snap!",
        keyVocab: 'garnish with scallions and sesame',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'garnish with scallions and sesame', pron: 'garnish with scallions and sesame' },
          { role: 'db', en: 'and a glossy drop of sesame oil.', pron: 'and a glossy drop of sesame oil.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to garnish with scallions and sesame.', fullPron: 'You have to garnish with scallions and sesame', ko: 'garnish with scallions and sesame 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna garnish with scallions and sesame.', fullPron: 'I\'m gonna garnish with scallions and sesame', ko: 'garnish with scallions and sesame 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll garnish with scallions and sesame?', fullPron: 'I\'ll garnish with scallions and sesame?', ko: 'garnish with scallions and sesame 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['garnish with scallions and sesame', 'whisk fresh eggs', 'cover with dome bowl']
        },
        fullEn: "You have to garnish with scallions and sesame and a glossy drop of sesame oil.",
        fullPron: 'You have to + garnish with scallions and sesame + and a glossy drop of sesame oil.',
        fullKo: '뚜껑을 열고 모락모락 김 나는 봉긋한 달걀 위에 파와 깨 얹기'
      },
      {
        stepTitle: 'SCENE 8 · Cloud-Soft Silky & Pillowy Fluffy',
        visualEmojis: '😋 🍳 🤍',
        imagePath: '/images/kfood/ep43-thumb.jpg',
        actionNote: '숟가락으로 폭신하게 떠서 입안에서 사르르 녹아내리는 부드러움',
        coachKo: "코어 블록은 'cloud-soft silky and pillowy fluffy'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'cloud-soft silky and pillowy fluffy'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 숟가락으로 폭신하게 떠서 입안에서 사르르 녹아내리는 부드러움",
        missionEn: "Snap Mission! 'It\'s so cloud-soft silky and pillowy fluffy melting instantly on tongue!' Snap!",
        keyVocab: 'cloud-soft silky and pillowy fluffy',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'cloud-soft silky and pillowy fluffy', pron: 'cloud-soft silky and pillowy fluffy' },
          { role: 'db', en: 'melting instantly on tongue!', pron: 'melting instantly on tongue!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so cloud-soft silky and pillowy fluffy.', fullPron: 'It\'s so cloud-soft silky and pillowy fluffy', ko: 'cloud-soft silky and pillowy fluffy 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to cloud-soft silky and pillowy fluffy.', fullPron: 'You have to cloud-soft silky and pillowy fluffy', ko: 'cloud-soft silky and pillowy fluffy 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you cloud-soft silky and pillowy fluffy?', fullPron: 'Can you cloud-soft silky and pillowy fluffy?', ko: 'cloud-soft silky and pillowy fluffy 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['cloud-soft silky and pillowy fluffy', 'whisk six eggs', 'cover with domed bowl']
        },
        fullEn: "It\'s so cloud-soft silky and pillowy fluffy melting instantly on tongue!",
        fullPron: 'It\'s so + cloud-soft silky and pillowy fluffy + melting instantly on tongue!',
        fullKo: '숟가락으로 폭신하게 떠서 입안에서 사르르 녹아내리는 부드러움'
      }
    ]
  },
  // ==========================================
  // EP.44. 🍳 Classic Rolled Omelet
  // ==========================================
  {
    id: 'gyeran-mari',
    epNumber: 'EP.44',
    emoji: '🍳',
    shortTitle: '🍳 Classic Rolled Omelet',
    title: 'How to Roll a Classic Korean Lunchbox Egg Omelet (Gyeran-mari)',
    ytTitle: 'How to Make Korean Rolled Egg Omelet in Easy English 🍳 | SoundBlock K-Cooking EP.44',
    thumbnailText: 'Thick Rolled Omelet! [I\'m gonna] + [roll colorful layered egg sheets with tender care]',
    thumbnailImage: '/images/kfood/ep44-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s roll a thick, colorful Korean Egg Omelet with carrots, scallions, and layers of fluffy egg, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for beautiful Gyeran-mari! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Finely Mince Carrots and Scallions',
        visualEmojis: '🥕 🌿 🔪',
        imagePath: '/images/kfood/ep44-thumb.jpg',
        actionNote: '당근과 대파를 아주 곱게 다져 알록달록한 계란말이 고명 준비',
        coachKo: "코어 블록은 'finely mince carrots and scallions'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'finely mince carrots and scallions'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 당근과 대파를 아주 곱게 다져 알록달록한 계란말이 고명 준비",
        missionEn: "Snap Mission! 'You have to finely mince carrots and scallions into tiny colorful confetti.' Snap!",
        keyVocab: 'finely mince carrots and scallions',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'finely mince carrots and scallions', pron: 'finely mince carrots and scallions' },
          { role: 'db', en: 'into tiny colorful confetti.', pron: 'into tiny colorful confetti.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to finely mince carrots and scallions.', fullPron: 'You have to finely mince carrots and scallions', ko: 'finely mince carrots and scallions 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna finely mince carrots and scallions.', fullPron: 'I\'m gonna finely mince carrots and scallions', ko: 'finely mince carrots and scallions 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll finely mince carrots and scallions?', fullPron: 'I\'ll finely mince carrots and scallions?', ko: 'finely mince carrots and scallions 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['finely mince carrots and scallions', 'whisk five eggs', 'roll the first layer']
        },
        fullEn: "You have to finely mince carrots and scallions into tiny colorful confetti.",
        fullPron: 'You have to + finely mince carrots and scallions + into tiny colorful confetti.',
        fullKo: '당근과 대파를 아주 곱게 다져 알록달록한 계란말이 고명 준비'
      },
      {
        stepTitle: 'SCENE 2 · Whisk Five Eggs with Milk & Salt',
        visualEmojis: '🥚 🥛 🧂',
        imagePath: '/images/kfood/ep44-thumb.jpg',
        actionNote: '계란 5개에 우유 한 스푼과 소금을 넣고 부드럽게 풀기',
        coachKo: "코어 블록은 'whisk five eggs with splash of milk'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'whisk five eggs with splash of milk'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 계란 5개에 우유 한 스푼과 소금을 넣고 부드럽게 풀기",
        missionEn: "Snap Mission! 'I\'m gonna whisk five eggs with splash of milk for extra tender velvety texture.' Snap!",
        keyVocab: 'whisk five eggs with splash of milk',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'whisk five eggs with splash of milk', pron: 'whisk five eggs with splash of milk' },
          { role: 'db', en: 'for extra tender velvety texture.', pron: 'for extra tender velvety texture.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna whisk five eggs with splash of milk.', fullPron: 'I\'m gonna whisk five eggs with splash of milk', ko: 'whisk five eggs with splash of milk 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to whisk five eggs with splash of milk.', fullPron: 'You have to whisk five eggs with splash of milk', ko: 'whisk five eggs with splash of milk 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna whisk five eggs with splash of milk?', fullPron: 'We\'re gonna whisk five eggs with splash of milk?', ko: 'whisk five eggs with splash of milk 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['whisk five eggs with splash of milk', 'mince carrots', 'roll the first layer']
        },
        fullEn: "I\'m gonna whisk five eggs with splash of milk for extra tender velvety texture.",
        fullPron: 'I\'m gonna + whisk five eggs with splash of milk + for extra tender velvety texture.',
        fullKo: '계란 5개에 우유 한 스푼과 소금을 넣고 부드럽게 풀기'
      },
      {
        stepTitle: 'SCENE 3 · Mix In Minced Colorful Vegetables',
        visualEmojis: '🥕 🌿 🥣',
        imagePath: '/images/kfood/ep44-thumb.jpg',
        actionNote: '계란물에 다진 채소를 섞고 체에 걸러 알끈 부드럽게 제거하기',
        coachKo: "코어 블록은 'mix in minced colorful vegetables'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'mix in minced colorful vegetables'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 계란물에 다진 채소를 섞고 체에 걸러 알끈 부드럽게 제거하기",
        missionEn: "Snap Mission! 'We\'re gonna mix in minced colorful vegetables and stir evenly throughout.' Snap!",
        keyVocab: 'mix in minced colorful vegetables',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'mix in minced colorful vegetables', pron: 'mix in minced colorful vegetables' },
          { role: 'db', en: 'and stir evenly throughout.', pron: 'and stir evenly throughout.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna mix in minced colorful vegetables.', fullPron: 'We\'re gonna mix in minced colorful vegetables', ko: 'mix in minced colorful vegetables 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna mix in minced colorful vegetables.', fullPron: 'I\'m gonna mix in minced colorful vegetables', ko: 'mix in minced colorful vegetables 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to mix in minced colorful vegetables?', fullPron: 'You have to mix in minced colorful vegetables?', ko: 'mix in minced colorful vegetables 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['mix in minced colorful vegetables', 'oil the rectangular pan', 'flip and roll']
        },
        fullEn: "We\'re gonna mix in minced colorful vegetables and stir evenly throughout.",
        fullPron: 'We\'re gonna + mix in minced colorful vegetables + and stir evenly throughout.',
        fullKo: '계란물에 다진 채소를 섞고 체에 걸러 알끈 부드럽게 제거하기'
      },
      {
        stepTitle: 'SCENE 4 · Lightly Oil Rectangular Egg Pan',
        visualEmojis: '🍳 🫙 🧻',
        imagePath: '/images/kfood/ep44-thumb.jpg',
        actionNote: '달군 사각팬에 기름을 키친타월로 얇게 코팅하듯 바르기',
        coachKo: "코어 블록은 'lightly oil rectangular egg pan'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'lightly oil rectangular egg pan'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 달군 사각팬에 기름을 키친타월로 얇게 코팅하듯 바르기",
        missionEn: "Snap Mission! 'You have to lightly oil rectangular egg pan over gentle low heat.' Snap!",
        keyVocab: 'lightly oil rectangular egg pan',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'lightly oil rectangular egg pan', pron: 'lightly oil rectangular egg pan' },
          { role: 'db', en: 'over gentle low heat.', pron: 'over gentle low heat.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to lightly oil rectangular egg pan.', fullPron: 'You have to lightly oil rectangular egg pan', ko: 'lightly oil rectangular egg pan 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll lightly oil rectangular egg pan.', fullPron: 'I\'ll lightly oil rectangular egg pan', ko: 'lightly oil rectangular egg pan 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna lightly oil rectangular egg pan?', fullPron: 'I\'m gonna lightly oil rectangular egg pan?', ko: 'lightly oil rectangular egg pan 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['lightly oil rectangular egg pan', 'whisk five eggs', 'roll the first layer']
        },
        fullEn: "You have to lightly oil rectangular egg pan over gentle low heat.",
        fullPron: 'You have to + lightly oil rectangular egg pan + over gentle low heat.',
        fullKo: '달군 사각팬에 기름을 키친타월로 얇게 코팅하듯 바르기'
      },
      {
        stepTitle: 'SCENE 5 · Pour Thin Layer and Roll Gently',
        visualEmojis: '🟡 🍳 🥢',
        imagePath: '/images/kfood/ep44-thumb.jpg',
        actionNote: '계란물을 얇게 붓고 반쯤 익었을 때 젓가락으로 살살 말아주기',
        coachKo: "코어 블록은 'roll the first thin egg layer'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'roll the first thin egg layer'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 계란물을 얇게 붓고 반쯤 익었을 때 젓가락으로 살살 말아주기",
        missionEn: "Snap Mission! 'I\'ll roll the first thin egg layer gently with flat spatulas.' Snap!",
        keyVocab: 'roll the first thin egg layer',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'roll the first thin egg layer', pron: 'roll the first thin egg layer' },
          { role: 'db', en: 'gently with flat spatulas.', pron: 'gently with flat spatulas.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll roll the first thin egg layer.', fullPron: 'I\'ll roll the first thin egg layer', ko: 'roll the first thin egg layer 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna roll the first thin egg layer.', fullPron: 'I\'m gonna roll the first thin egg layer', ko: 'roll the first thin egg layer 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to roll the first thin egg layer?', fullPron: 'You have to roll the first thin egg layer?', ko: 'roll the first thin egg layer 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['roll the first thin egg layer', 'oil the pan', 'pour remaining egg']
        },
        fullEn: "I\'ll roll the first thin egg layer gently with flat spatulas.",
        fullPron: 'I\'ll + roll the first thin egg layer + gently with flat spatulas.',
        fullKo: '계란물을 얇게 붓고 반쯤 익었을 때 젓가락으로 살살 말아주기'
      },
      {
        stepTitle: 'SCENE 6 · Push Rolled Log and Pour More Egg',
        visualEmojis: '🔄 🍳 🟡',
        imagePath: '/images/kfood/ep44-thumb.jpg',
        actionNote: '말아둔 계란을 한쪽으로 밀고 빈자리에 계란물을 이어 붓기',
        coachKo: "코어 블록은 'pour remaining egg in thin sheets'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'pour remaining egg in thin sheets'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 말아둔 계란을 한쪽으로 밀고 빈자리에 계란물을 이어 붓기",
        missionEn: "Snap Mission! 'We\'re gonna pour remaining egg in thin sheets connecting seamlessly to the roll.' Snap!",
        keyVocab: 'pour remaining egg in thin sheets',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'pour remaining egg in thin sheets', pron: 'pour remaining egg in thin sheets' },
          { role: 'db', en: 'connecting seamlessly to the roll.', pron: 'connecting seamlessly to the roll.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna pour remaining egg in thin sheets.', fullPron: 'We\'re gonna pour remaining egg in thin sheets', ko: 'pour remaining egg in thin sheets 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna pour remaining egg in thin sheets.', fullPron: 'I\'m gonna pour remaining egg in thin sheets', ko: 'pour remaining egg in thin sheets 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to pour remaining egg in thin sheets?', fullPron: 'You have to pour remaining egg in thin sheets?', ko: 'pour remaining egg in thin sheets 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['pour remaining egg in thin sheets', 'whisk five eggs', 'slice into thick rounds']
        },
        fullEn: "We\'re gonna pour remaining egg in thin sheets connecting seamlessly to the roll.",
        fullPron: 'We\'re gonna + pour remaining egg in thin sheets + connecting seamlessly to the roll.',
        fullKo: '말아둔 계란을 한쪽으로 밀고 빈자리에 계란물을 이어 붓기'
      },
      {
        stepTitle: 'SCENE 7 · Slice into Thick Elegant Rounds',
        visualEmojis: '🔪 🟡 ✨',
        imagePath: '/images/kfood/ep44-thumb.jpg',
        actionNote: '한 김 식힌 뒤 칼로 도톰하게 썰어 노란색 단면 예쁘게 드러내기',
        coachKo: "코어 블록은 'slice into thick elegant rounds'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slice into thick elegant rounds'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 한 김 식힌 뒤 칼로 도톰하게 썰어 노란색 단면 예쁘게 드러내기",
        missionEn: "Snap Mission! 'You have to slice into thick elegant rounds after cooling down slightly.' Snap!",
        keyVocab: 'slice into thick elegant rounds',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'slice into thick elegant rounds', pron: 'slice into thick elegant rounds' },
          { role: 'db', en: 'after cooling down slightly.', pron: 'after cooling down slightly.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to slice into thick elegant rounds.', fullPron: 'You have to slice into thick elegant rounds', ko: 'slice into thick elegant rounds 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slice into thick elegant rounds.', fullPron: 'I\'m gonna slice into thick elegant rounds', ko: 'slice into thick elegant rounds 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll slice into thick elegant rounds?', fullPron: 'I\'ll slice into thick elegant rounds?', ko: 'slice into thick elegant rounds 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['slice into thick elegant rounds', 'roll thin layers', 'lightly oil pan']
        },
        fullEn: "You have to slice into thick elegant rounds after cooling down slightly.",
        fullPron: 'You have to + slice into thick elegant rounds + after cooling down slightly.',
        fullKo: '한 김 식힌 뒤 칼로 도톰하게 썰어 노란색 단면 예쁘게 드러내기'
      },
      {
        stepTitle: 'SCENE 8 · Velvety Tender & Delicately Savory',
        visualEmojis: '😋 🍳 💛',
        imagePath: '/images/kfood/ep44-thumb.jpg',
        actionNote: '한입 베어 물면 폭신폭신 부드럽고 밥반찬으로 최고인 계란말이',
        coachKo: "코어 블록은 'velvety tender and delicately savory'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'velvety tender and delicately savory'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 한입 베어 물면 폭신폭신 부드럽고 밥반찬으로 최고인 계란말이",
        missionEn: "Snap Mission! 'It\'s so velvety tender and delicately savory with beautiful mosaic layers!' Snap!",
        keyVocab: 'velvety tender and delicately savory',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'velvety tender and delicately savory', pron: 'velvety tender and delicately savory' },
          { role: 'db', en: 'with beautiful mosaic layers!', pron: 'with beautiful mosaic layers!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so velvety tender and delicately savory.', fullPron: 'It\'s so velvety tender and delicately savory', ko: 'velvety tender and delicately savory 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to velvety tender and delicately savory.', fullPron: 'You have to velvety tender and delicately savory', ko: 'velvety tender and delicately savory 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you velvety tender and delicately savory?', fullPron: 'Can you velvety tender and delicately savory?', ko: 'velvety tender and delicately savory 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['velvety tender and delicately savory', 'mince carrots', 'slice into thick rounds']
        },
        fullEn: "It\'s so velvety tender and delicately savory with beautiful mosaic layers!",
        fullPron: 'It\'s so + velvety tender and delicately savory + with beautiful mosaic layers!',
        fullKo: '한입 베어 물면 폭신폭신 부드럽고 밥반찬으로 최고인 계란말이'
      }
    ]
  },
  // ==========================================
  // EP.45. 🍚 5-Min Butter Egg Rice
  // ==========================================
  {
    id: 'ganjang-gyeran-bap',
    epNumber: 'EP.45',
    emoji: '🍚',
    shortTitle: '🍚 5-Min Butter Egg Rice',
    title: 'How to Make 5-Minute Korean Comfort Butter Soy Sauce Egg Rice',
    ytTitle: 'How to Make 5-Minute Korean Butter Soy Egg Rice in Easy English 🍚 | SoundBlock K-Cooking EP.45',
    thumbnailText: '5-Min Butter Egg Rice! [I\'m gonna] + [mix sunny-side-up eggs with melting butter and soy sauce]',
    thumbnailImage: '/images/kfood/ep45-thumb.jpg',
    introNarrationKo: "Welcome to SoundBlock K-Cooking! Today, let\'s make Korea\'s ultimate 5-minute comfort food: piping hot rice with crispy fried eggs, melting butter, and seasoned soy sauce, using simple sound blocks. Let\'s get cooking!",
    outroNarrationKo: "Mission complete! You\'ve mastered all the sound blocks for quick comfort Butter Egg Rice! Subscribe and like for more delicious K-food. See you in the next video!",
    scenes: [
      {
        stepTitle: 'SCENE 1 · Scoop Steaming Hot Rice into Bowl',
        visualEmojis: '🍚 🥣 💨',
        imagePath: '/images/kfood/ep45-thumb.jpg',
        actionNote: '갓 지어 김이 모락모락 나는 따뜻한 흰쌀밥을 볼에 담기',
        coachKo: "코어 블록은 'scoop steaming hot white rice'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'scoop steaming hot white rice'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 갓 지어 김이 모락모락 나는 따뜻한 흰쌀밥을 볼에 담기",
        missionEn: "Snap Mission! 'You have to scoop steaming hot white rice right into a wide bowl.' Snap!",
        keyVocab: 'scoop steaming hot white rice',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'scoop steaming hot white rice', pron: 'scoop steaming hot white rice' },
          { role: 'db', en: 'right into a wide bowl.', pron: 'right into a wide bowl.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to scoop steaming hot white rice.', fullPron: 'You have to scoop steaming hot white rice', ko: 'scoop steaming hot white rice 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna scoop steaming hot white rice.', fullPron: 'I\'m gonna scoop steaming hot white rice', ko: 'scoop steaming hot white rice 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll scoop steaming hot white rice?', fullPron: 'I\'ll scoop steaming hot white rice?', ko: 'scoop steaming hot white rice 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['scoop steaming hot white rice', 'drop creamy butter', 'fry two eggs']
        },
        fullEn: "You have to scoop steaming hot white rice right into a wide bowl.",
        fullPron: 'You have to + scoop steaming hot white rice + right into a wide bowl.',
        fullKo: '갓 지어 김이 모락모락 나는 따뜻한 흰쌀밥을 볼에 담기'
      },
      {
        stepTitle: 'SCENE 2 · Drop Creamy Butter at Center of Rice',
        visualEmojis: '🧈 🍚 💛',
        imagePath: '/images/kfood/ep45-thumb.jpg',
        actionNote: '따뜻한 밥 한가운데에 고소한 버터 한 조각 쏙 묻어 녹이기',
        coachKo: "코어 블록은 'drop creamy butter into warm rice'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'drop creamy butter into warm rice'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 따뜻한 밥 한가운데에 고소한 버터 한 조각 쏙 묻어 녹이기",
        missionEn: "Snap Mission! 'I\'m gonna drop creamy butter into warm rice letting it melt inside.' Snap!",
        keyVocab: 'drop creamy butter into warm rice',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'m gonna", pron: 'I\'m gonna' },
          { role: 'core', en: 'drop creamy butter into warm rice', pron: 'drop creamy butter into warm rice' },
          { role: 'db', en: 'letting it melt inside.', pron: 'letting it melt inside.' }
        ],
        combos: [
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna drop creamy butter into warm rice.', fullPron: 'I\'m gonna drop creamy butter into warm rice', ko: 'drop creamy butter into warm rice 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to drop creamy butter into warm rice.', fullPron: 'You have to drop creamy butter into warm rice', ko: 'drop creamy butter into warm rice 해야 해요.' },
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna drop creamy butter into warm rice?', fullPron: 'We\'re gonna drop creamy butter into warm rice?', ko: 'drop creamy butter into warm rice 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'m gonna", "You have to", "We\'re gonna"],
          coreCandidates: ['drop creamy butter into warm rice', 'scoop hot rice', 'fry eggs crispy']
        },
        fullEn: "I\'m gonna drop creamy butter into warm rice letting it melt inside.",
        fullPron: 'I\'m gonna + drop creamy butter into warm rice + letting it melt inside.',
        fullKo: '따뜻한 밥 한가운데에 고소한 버터 한 조각 쏙 묻어 녹이기'
      },
      {
        stepTitle: 'SCENE 3 · Fry Two Eggs Sunny-Side Up with Crispy Edges',
        visualEmojis: '🍳 🥚 🥓',
        imagePath: '/images/kfood/ep45-thumb.jpg',
        actionNote: '기름 두른 팬에 달걀 2개를 가장자리가 바삭하게 반숙으로 부치기',
        coachKo: "코어 블록은 'fry two sunny-side-up eggs'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'fry two sunny-side-up eggs'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 기름 두른 팬에 달걀 2개를 가장자리가 바삭하게 반숙으로 부치기",
        missionEn: "Snap Mission! 'We\'re gonna fry two sunny-side-up eggs with crispy golden frills.' Snap!",
        keyVocab: 'fry two sunny-side-up eggs',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'fry two sunny-side-up eggs', pron: 'fry two sunny-side-up eggs' },
          { role: 'db', en: 'with crispy golden frills.', pron: 'with crispy golden frills.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna fry two sunny-side-up eggs.', fullPron: 'We\'re gonna fry two sunny-side-up eggs', ko: 'fry two sunny-side-up eggs 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna fry two sunny-side-up eggs.', fullPron: 'I\'m gonna fry two sunny-side-up eggs', ko: 'fry two sunny-side-up eggs 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to fry two sunny-side-up eggs?', fullPron: 'You have to fry two sunny-side-up eggs?', ko: 'fry two sunny-side-up eggs 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['fry two sunny-side-up eggs', 'scoop hot rice', 'drizzle seasoned soy sauce']
        },
        fullEn: "We\'re gonna fry two sunny-side-up eggs with crispy golden frills.",
        fullPron: 'We\'re gonna + fry two sunny-side-up eggs + with crispy golden frills.',
        fullKo: '기름 두른 팬에 달걀 2개를 가장자리가 바삭하게 반숙으로 부치기'
      },
      {
        stepTitle: 'SCENE 4 · Slide Runny Eggs Over Melting Butter',
        visualEmojis: '🍳 ➡️ 🍚',
        imagePath: '/images/kfood/ep45-thumb.jpg',
        actionNote: '노른자가 탱글탱글 살아있는 반숙 계란을 밥 위에 사뿐히 얹기',
        coachKo: "코어 블록은 'slide runny eggs over rice'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'slide runny eggs over rice'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 노른자가 탱글탱글 살아있는 반숙 계란을 밥 위에 사뿐히 얹기",
        missionEn: "Snap Mission! 'You have to slide runny eggs over rice keeping the yolks intact.' Snap!",
        keyVocab: 'slide runny eggs over rice',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'slide runny eggs over rice', pron: 'slide runny eggs over rice' },
          { role: 'db', en: 'keeping the yolks intact.', pron: 'keeping the yolks intact.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to slide runny eggs over rice.', fullPron: 'You have to slide runny eggs over rice', ko: 'slide runny eggs over rice 할 거예요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll slide runny eggs over rice.', fullPron: 'I\'ll slide runny eggs over rice', ko: 'slide runny eggs over rice 해야 해요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna slide runny eggs over rice?', fullPron: 'I\'m gonna slide runny eggs over rice?', ko: 'slide runny eggs over rice 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'ll", "I\'m gonna"],
          coreCandidates: ['slide runny eggs over rice', 'drop creamy butter', 'drizzle soy sauce']
        },
        fullEn: "You have to slide runny eggs over rice keeping the yolks intact.",
        fullPron: 'You have to + slide runny eggs over rice + keeping the yolks intact.',
        fullKo: '노른자가 탱글탱글 살아있는 반숙 계란을 밥 위에 사뿐히 얹기'
      },
      {
        stepTitle: 'SCENE 5 · Drizzle Seasoned Soy Sauce & Sesame Oil',
        visualEmojis: '🫙 🧂 🌰',
        imagePath: '/images/kfood/ep45-thumb.jpg',
        actionNote: '진간장 한 스푼과 고소한 참기름을 밥 둘레로 휘리릭 두르기',
        coachKo: "코어 블록은 'drizzle seasoned soy sauce'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'drizzle seasoned soy sauce'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 진간장 한 스푼과 고소한 참기름을 밥 둘레로 휘리릭 두르기",
        missionEn: "Snap Mission! 'I\'ll drizzle seasoned soy sauce and fragrant toasted sesame oil.' Snap!",
        keyVocab: 'drizzle seasoned soy sauce',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "I\'ll", pron: 'I\'ll' },
          { role: 'core', en: 'drizzle seasoned soy sauce', pron: 'drizzle seasoned soy sauce' },
          { role: 'db', en: 'and fragrant toasted sesame oil.', pron: 'and fragrant toasted sesame oil.' }
        ],
        combos: [
          { bbEn: 'I\'ll', fullEn: 'I\'ll drizzle seasoned soy sauce.', fullPron: 'I\'ll drizzle seasoned soy sauce', ko: 'drizzle seasoned soy sauce 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna drizzle seasoned soy sauce.', fullPron: 'I\'m gonna drizzle seasoned soy sauce', ko: 'drizzle seasoned soy sauce 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to drizzle seasoned soy sauce?', fullPron: 'You have to drizzle seasoned soy sauce?', ko: 'drizzle seasoned soy sauce 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["I\'ll", "I\'m gonna", "You have to"],
          coreCandidates: ['drizzle seasoned soy sauce', 'fry sunny-side eggs', 'break the runny yolks']
        },
        fullEn: "I\'ll drizzle seasoned soy sauce and fragrant toasted sesame oil.",
        fullPron: 'I\'ll + drizzle seasoned soy sauce + and fragrant toasted sesame oil.',
        fullKo: '진간장 한 스푼과 고소한 참기름을 밥 둘레로 휘리릭 두르기'
      },
      {
        stepTitle: 'SCENE 6 · Sprinkle Crushed Seaweed & Toasted Seeds',
        visualEmojis: '🌿 🌰 ✨',
        imagePath: '/images/kfood/ep45-thumb.jpg',
        actionNote: '바삭한 조미김을 손으로 부수어 통깨와 함께 소복이 뿌리기',
        coachKo: "코어 블록은 'sprinkle crushed roasted seaweed'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'sprinkle crushed roasted seaweed'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 바삭한 조미김을 손으로 부수어 통깨와 함께 소복이 뿌리기",
        missionEn: "Snap Mission! 'We\'re gonna sprinkle crushed roasted seaweed and lots of nutty sesame.' Snap!",
        keyVocab: 'sprinkle crushed roasted seaweed',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "We\'re gonna", pron: 'We\'re gonna' },
          { role: 'core', en: 'sprinkle crushed roasted seaweed', pron: 'sprinkle crushed roasted seaweed' },
          { role: 'db', en: 'and lots of nutty sesame.', pron: 'and lots of nutty sesame.' }
        ],
        combos: [
          { bbEn: 'We\'re gonna', fullEn: 'We\'re gonna sprinkle crushed roasted seaweed.', fullPron: 'We\'re gonna sprinkle crushed roasted seaweed', ko: 'sprinkle crushed roasted seaweed 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna sprinkle crushed roasted seaweed.', fullPron: 'I\'m gonna sprinkle crushed roasted seaweed', ko: 'sprinkle crushed roasted seaweed 해야 해요.' },
          { bbEn: 'You have to', fullEn: 'You have to sprinkle crushed roasted seaweed?', fullPron: 'You have to sprinkle crushed roasted seaweed?', ko: 'sprinkle crushed roasted seaweed 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["We\'re gonna", "I\'m gonna", "You have to"],
          coreCandidates: ['sprinkle crushed roasted seaweed', 'drop creamy butter', 'break runny yolks']
        },
        fullEn: "We\'re gonna sprinkle crushed roasted seaweed and lots of nutty sesame.",
        fullPron: 'We\'re gonna + sprinkle crushed roasted seaweed + and lots of nutty sesame.',
        fullKo: '바삭한 조미김을 손으로 부수어 통깨와 함께 소복이 뿌리기'
      },
      {
        stepTitle: 'SCENE 7 · Break Runny Yolks and Mix Thoroughly',
        visualEmojis: '🥄 🟡 💥',
        imagePath: '/images/kfood/ep45-thumb.jpg',
        actionNote: '숟가락으로 노른자를 톡 터뜨려 버터, 간장과 골고루 비비기',
        coachKo: "코어 블록은 'break the golden runny yolks'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'break the golden runny yolks'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 숟가락으로 노른자를 톡 터뜨려 버터, 간장과 골고루 비비기",
        missionEn: "Snap Mission! 'You have to break the golden runny yolks and mix with creamy butter.' Snap!",
        keyVocab: 'break the golden runny yolks',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "You have to", pron: 'You have to' },
          { role: 'core', en: 'break the golden runny yolks', pron: 'break the golden runny yolks' },
          { role: 'db', en: 'and mix with creamy butter.', pron: 'and mix with creamy butter.' }
        ],
        combos: [
          { bbEn: 'You have to', fullEn: 'You have to break the golden runny yolks.', fullPron: 'You have to break the golden runny yolks', ko: 'break the golden runny yolks 할 거예요.' },
          { bbEn: 'I\'m gonna', fullEn: 'I\'m gonna break the golden runny yolks.', fullPron: 'I\'m gonna break the golden runny yolks', ko: 'break the golden runny yolks 해야 해요.' },
          { bbEn: 'I\'ll', fullEn: 'I\'ll break the golden runny yolks?', fullPron: 'I\'ll break the golden runny yolks?', ko: 'break the golden runny yolks 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["You have to", "I\'m gonna", "I\'ll"],
          coreCandidates: ['break the golden runny yolks', 'scoop hot rice', 'fry sunny eggs']
        },
        fullEn: "You have to break the golden runny yolks and mix with creamy butter.",
        fullPron: 'You have to + break the golden runny yolks + and mix with creamy butter.',
        fullKo: '숟가락으로 노른자를 톡 터뜨려 버터, 간장과 골고루 비비기'
      },
      {
        stepTitle: 'SCENE 8 · Silky Savory & Nostalgic Comfort',
        visualEmojis: '😋 🍚 🧈',
        imagePath: '/images/kfood/ep45-thumb.jpg',
        actionNote: '한 입 가득 퍼지는 버터의 고소함과 짭조름한 계란밥의 힐링 한 숟갈',
        coachKo: "코어 블록은 'silky savory and nostalgic comfort'입니다. 시작 블록을 바꿔 볼까요?",
        coachEn: "Our core action is 'silky savory and nostalgic comfort'. Let's swap the starter block!",
        missionKo: "실전 조립 미션! 한 입 가득 퍼지는 버터의 고소함과 짭조름한 계란밥의 힐링 한 숟갈",
        missionEn: "Snap Mission! 'It\'s so silky savory and nostalgic comfort curing any late-night hunger!' Snap!",
        keyVocab: 'silky savory and nostalgic comfort',
        bgGradient: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        blocks: [
          { role: 'bb', en: "It\'s so", pron: 'It\'s so' },
          { role: 'core', en: 'silky savory and nostalgic comfort', pron: 'silky savory and nostalgic comfort' },
          { role: 'db', en: 'curing any late-night hunger!', pron: 'curing any late-night hunger!' }
        ],
        combos: [
          { bbEn: 'It\'s so', fullEn: 'It\'s so silky savory and nostalgic comfort.', fullPron: 'It\'s so silky savory and nostalgic comfort', ko: 'silky savory and nostalgic comfort 할 거예요.' },
          { bbEn: 'You have to', fullEn: 'You have to silky savory and nostalgic comfort.', fullPron: 'You have to silky savory and nostalgic comfort', ko: 'silky savory and nostalgic comfort 해야 해요.' },
          { bbEn: 'Can you', fullEn: 'Can you silky savory and nostalgic comfort?', fullPron: 'Can you silky savory and nostalgic comfort?', ko: 'silky savory and nostalgic comfort 해 줄래요?' }
        ],
        quizPool: {
          bbCandidates: ["It\'s so", "You have to", "Can you"],
          coreCandidates: ['silky savory and nostalgic comfort', 'drop creamy butter', 'break runny yolks']
        },
        fullEn: "It\'s so silky savory and nostalgic comfort curing any late-night hunger!",
        fullPron: 'It\'s so + silky savory and nostalgic comfort + curing any late-night hunger!',
        fullKo: '한 입 가득 퍼지는 버터의 고소함과 짭조름한 계란밥의 힐링 한 숟갈'
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

const currentCoachText = computed(() => {
  if (activeStage.value === 'quiz') return currentScene.value.missionEn || currentScene.value.missionKo
  return currentScene.value.coachEn || currentScene.value.coachKo
})

const activeSceneImage = computed(() => {
  if (customMediaMap.value[sceneKey.value]) {
    return customMediaMap.value[sceneKey.value]
  }
  if (currentScene.value.imagePath) {
    return withBase(currentScene.value.imagePath)
  }
  return ''
})

function getComboCorePart(combo: SwapCombo): string {
  if (combo.fullEn.startsWith(combo.bbEn)) {
    return combo.fullEn.slice(combo.bbEn.length).trim()
  }
  return combo.fullEn
}

function getComboCoreBlock(combo: SwapCombo): string {
  const scene = currentScene.value
  const coreEn = scene?.blocks?.[1]?.en
  if (coreEn) return coreEn
  if (combo.fullEn.startsWith(combo.bbEn)) {
    return combo.fullEn.slice(combo.bbEn.length).trim()
  }
  return combo.fullEn
}

function getComboDetailBlock(combo: SwapCombo): string {
  const scene = currentScene.value
  return scene?.blocks?.[2]?.en || ''
}

// 🌟 Step 2 자석 결합 퀴즈 후보 블록 랜덤 셔플 (정답이 항상 1번에 위치하는 현상 해결)
function shuffleArray<T>(items: T[]): T[] {
  if (!items || items.length <= 1) return items ? [...items] : []
  const arr = [...items]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

const currentQuizBbCandidates = ref<string[]>([])
const currentQuizCoreCandidates = ref<string[]>([])

function refreshQuizPool() {
  const pool = currentScene.value?.quizPool
  if (!pool) return
  currentQuizBbCandidates.value = shuffleArray(pool.bbCandidates)
  currentQuizCoreCandidates.value = shuffleArray(pool.coreCandidates)
}

watch(
  [currentEpId, safeSceneIndex],
  () => {
    refreshQuizPool()
  },
  { immediate: true }
)

function setStage(stage: 'swap' | 'quiz' | 'sentence') {
  activeStage.value = stage
  if (stage === 'quiz') {
    isSnapped.value = false
    pickedBb.value = null
    pickedCore.value = null
    refreshQuizPool()
  }
}

// ---------------------------------------------------------
// Web Audio API 방송용 효과음 합성기 (자석 철컥, 딩동, 전환음)
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
  playTone(523.25, 160, 'triangle', 0.06, 0)
  playTone(659.25, 220, 'triangle', 0.06, 90)
}

function playBlockPop(idx: number) {
  const freqs = [440, 554.37, 659.25]
  playTone(freqs[idx % 3], 110, 'sine', 0.05, 0)
}

function playDingDongYourTurn() {
  playTone(783.99, 220, 'sine', 0.09, 0)
  playTone(659.25, 380, 'sine', 0.09, 180)
}

function playMagnetSnapSound() {
  // 자석이 "철컥!" 달라붙는 묵직하고 경쾌한 클릭 사운드
  if (!enableSoundEffects.value) return
  const ctx = getAudioContext()
  if (!ctx) return
  playTone(280, 70, 'square', 0.08, 0)
  playTone(880, 140, 'triangle', 0.09, 40)
  playTone(1320, 220, 'sine', 0.06, 80)
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

async function speakCoreBlock() {
  const coreBlk = currentScene.value.blocks[1]
  if (coreBlk) {
    await speakSingleBlock(coreBlk.en, 1)
  }
}

async function playComboCard(cIdx: number) {
  activeComboIdx.value = cIdx
  playBlockPop(cIdx)
  const epId = currentEpId.value
  const sIdx = safeSceneIndex.value
  const mp3Url = `/audio/kfood/${epId}-s${sIdx}-c${cIdx}.mp3`
  const ok = await playMp3Async(mp3Url, 0.96)
  if (!ok) {
    const combo = currentScene.value.combos[cIdx]
    if (combo) await speakAsync(combo.fullEn, 'en-US', 0.95)
  }
}

async function playMissionAudio() {
  const epId = currentEpId.value
  const sIdx = safeSceneIndex.value
  const mp3Url = `/audio/kfood/${epId}-s${sIdx}-mission.mp3`
  const ok = await playMp3Async(mp3Url, 1.0)
  if (!ok) {
    await speakAsync(currentScene.value.missionEn || currentScene.value.missionKo || '', 'en-US', 1.0)
  }
}

function clearPicked(role: 'bb' | 'core') {
  if (role === 'bb') pickedBb.value = null
  if (role === 'core') pickedCore.value = null
  isSnapped.value = false
}

async function triggerSnapAnimation() {
  playMagnetSnapSound()
  isSnapped.value = true
  pickedBb.value = currentScene.value.blocks[0].en
  pickedCore.value = currentScene.value.blocks[1].en
}

async function onPickCandidate(role: 'bb' | 'core', optText: string) {
  if (role === 'bb') {
    pickedBb.value = optText
    playBlockPop(0)
    await speakAsync(optText, 'en-US', 0.95)
  } else {
    pickedCore.value = optText
    playBlockPop(1)
    await speakAsync(optText, 'en-US', 0.95)
  }

  // 두 슬롯이 모두 선택되었을 때 정답 검증
  if (pickedBb.value && pickedCore.value) {
    const isCorrectBb = pickedBb.value === currentScene.value.blocks[0].en
    const isCorrectCore = pickedCore.value === currentScene.value.blocks[1].en
    if (isCorrectBb && isCorrectCore) {
      await triggerSnapAnimation()
      playSuccessBell()
      await speakSceneSentence(1.0)
    } else {
      // 오답일 경우 경쾌한 재시도 톤
      playTone(330, 160, 'triangle', 0.08, 0)
    }
  }
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
  activeComboIdx.value = null
  isShadowingTurn.value = false
  shadowingProgress.value = 0
  pickedBb.value = null
  pickedCore.value = null
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

  // 1) 인트로 슬라이드일 때 (intro-ko.mp3 안에 이미 'Let's get cooking!'이 포함되어 있으므로 단 1회만 재생)
  if (slideCursor.value === -1) {
    if (enableKoreanCoachVoice.value) {
      const ok = await playMp3Async(`/audio/kfood/${epId}-intro-ko.mp3`, 1.0)
      if (!ok) await speakAsync(currentEpisode.value.introNarrationEn || "Welcome to SoundBlock K-Cooking! Today, let's cook authentic Korean food using easy sound blocks. Let's get cooking!", 'en-US', 1.0)
      if (myToken !== sequenceToken) return false
    }
    return myToken === sequenceToken
  }

  // 2) 아웃트로 슬라이드일 때
  if (slideCursor.value >= currentEpisode.value.scenes.length) {
    if (enableKoreanCoachVoice.value) {
      const ok = await playMp3Async(`/audio/kfood/${epId}-outro-ko.mp3`, 1.0)
      if (!ok) await speakAsync(currentEpisode.value.outroNarrationEn || 'Mission complete! See you next time!', 'en-US', 1.0)
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

  // [STAGE 1] 시작 블록 3단 교체 훈련
  activeStage.value = 'swap'
  activeComboIdx.value = null

  if (enableKoreanCoachVoice.value && sc.coachKo) {
    const okCoach = await playMp3Async(`/audio/kfood/${epId}-s${sIdx}-coach.mp3`, 1.0)
    if (!okCoach) await speakAsync(sc.coachEn || sc.coachKo || '', 'en-US', 1.0)
    if (myToken !== sequenceToken) return false
    if (!(await waitMs(300, myToken))) return false
  }

  // Combos 0, 1, 2 순차 시연
  for (let c = 0; c < sc.combos.length; c++) {
    if (myToken !== sequenceToken) return false
    activeComboIdx.value = c
    playBlockPop(c)
    const okCombo = await playMp3Async(`/audio/kfood/${epId}-s${sIdx}-c${c}.mp3`, 0.95)
    if (!okCombo) await speakAsync(sc.combos[c].fullEn, 'en-US', 0.95)
    if (!(await waitMs(280, myToken))) return false
  }

  activeComboIdx.value = null
  if (!(await waitMs(400, myToken))) return false

  // [STAGE 2] 실전 자석 합체 미션
  activeStage.value = 'quiz'
  isSnapped.value = false
  pickedBb.value = null
  pickedCore.value = null
  refreshQuizPool()

  if (enableKoreanCoachVoice.value && sc.missionKo) {
    const okMission = await playMp3Async(`/audio/kfood/${epId}-s${sIdx}-mission.mp3`, 1.0)
    if (!okMission) await speakAsync(sc.missionEn || sc.missionKo || '', 'en-US', 1.0)
    if (myToken !== sequenceToken) return false
    if (!(await waitMs(400, myToken))) return false
  }

  // 1초 뒤 자석이 철컥 달라붙는 연출
  if (!(await waitMs(900, myToken))) return false
  await triggerSnapAnimation()
  if (myToken !== sequenceToken) return false
  if (!(await waitMs(300, myToken))) return false

  // 합체된 완성 문장 재생
  const okFull = await playMp3Async(`/audio/kfood/${epId}-s${sIdx}-full.mp3`, 1.0)
  if (!okFull) await speakAsync(sc.fullEn, 'en-US', 1.0)
  if (myToken !== sequenceToken) return false

  // [STAGE 3] 따라 말하기 (YOUR TURN) 4초
  activeStage.value = 'sentence'
  if (includeShadowingPause.value) {
    if (!(await waitMs(300, myToken))) return false
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
  if (slideCursor.value >= currentEpisode.value.scenes.length) {
    slideCursor.value = -1
  }

  while (isAutoPlaying.value && slideCursor.value <= currentEpisode.value.scenes.length) {
    const completed = await playCurrentSlideSequence()
    if (!completed || !isAutoPlaying.value) break

    const myToken = sequenceToken
    const ok = await waitMs(750, myToken)
    if (!ok || !isAutoPlaying.value) break

    if (slideCursor.value < currentEpisode.value.scenes.length) {
      slideCursor.value++
    } else {
      isAutoPlaying.value = false
      break
    }
  }

  // 🌟 에피소드 전체(Intro ~ Outro) 방송이 완료되었을 때 녹화 중이라면 1.8초 뒤 자동으로 녹화 종료 & 저장
  if (slideCursor.value >= currentEpisode.value.scenes.length && isScreenRecording.value) {
    await new Promise((resolve) => setTimeout(resolve, 1800))
    if (isScreenRecording.value) {
      stopScreenRecording()
      // 전체화면 모드였다면 자연스럽게 복원
      if (typeof document !== 'undefined' && document.fullscreenElement) {
        document.exitFullscreen().catch(() => {})
      }
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
  slideCursor.value = -1
  activeStage.value = 'swap'
}

function goToSlide(idx: number) {
  stopAutoShow()
  slideCursor.value = idx
  activeStage.value = 'swap'
}

function prevSlide() {
  stopAutoShow()
  if (slideCursor.value > -1) {
    slideCursor.value--
  } else {
    slideCursor.value = currentEpisode.value.scenes.length
  }
  activeStage.value = 'swap'
}

function nextSlide() {
  stopAutoShow()
  if (slideCursor.value < currentEpisode.value.scenes.length) {
    slideCursor.value++
  } else {
    slideCursor.value = -1
  }
  activeStage.value = 'swap'
}

// ---------------------------------------------------------
// 1080p 전체화면 방송 모드 & 마우스 자동 숨김
// ---------------------------------------------------------
async function enterFullscreen() {
  isFullscreenMode.value = true
  if (typeof document !== 'undefined') {
    document.body.classList.add('kf-theater-body')
  }
  if (studioRoot.value && studioRoot.value.requestFullscreen) {
    try {
      if (!document.fullscreenElement) {
        await studioRoot.value.requestFullscreen()
      }
    } catch {
      // CSS fullscreen fallback
    }
  }
}

async function toggleFullscreenBroadcast() {
  if (isFullscreenMode.value) {
    await exitFullscreen()
    return
  }
  await enterFullscreen()
}

async function exitFullscreen() {
  isFullscreenMode.value = false
  if (typeof document !== 'undefined') {
    document.body.classList.remove('kf-theater-body')
    if (document.fullscreenElement) {
      try {
        await document.exitFullscreen()
      } catch {
        // ignore
      }
    }
  }
}

function onFullscreenChange() {
  if (typeof document !== 'undefined' && !document.fullscreenElement) {
    // 🚨 녹화 중이거나 녹화 준비 카운트다운 중일 때는
    // 브라우저 탭 공유 다이얼로그 때문에 네이티브 풀스크린이 일시 해제되더라도
    // CSS 극장 모드(Theater Fullscreen)를 철통 유지하여 창모드로 튕기는 현상을 원천 방지합니다!
    if (isScreenRecording.value || countdownToRecord.value !== null) {
      return
    }
    isFullscreenMode.value = false
    document.body.classList.remove('kf-theater-body')
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

function getEpisodeTags(ep: CookingEpisode): string {
  const dish = ep.shortTitle.replace(/^[^\s]+\s*/, '')
  const specificTagsMap: Record<string, string[]> = {
    'kimchi-stew': ['kimchi stew', 'how to make kimchi stew', 'authentic kimchi stew recipe', 'kimchi jjigae recipe', 'kimchi soup in english'],
    'kimchi-fried-rice': ['kimchi fried rice', 'easy kimchi fried rice', 'how to make kimchi fried rice', '5 minute kimchi fried rice', 'bokkeumbap recipe'],
    'korean-ramen': ['korean ramen', 'korean ramyeon', 'how to cook korean ramen', 'how to cook shin ramen', 'k-ramen recipe'],
    'bulgogi-bbq': ['korean bulgogi', 'bulgogi beef recipe', 'korean bbq beef', 'how to make bulgogi', 'ssam lettuce wrap'],
    'tteokbokki': ['tteokbokki recipe', 'how to make tteokbokki', 'spicy tteokbokki', 'cheese tteokbokki', 'korean rice cakes in english'],
    'korean-pancake': ['korean pancake recipe', 'crispy pajeon', 'haemul pajeon recipe', 'how to make korean pancake', 'kimchijeon recipe'],
    'japchae': ['japchae recipe', 'how to make japchae', 'korean glass noodles recipe', 'traditional japchae', 'sweet potato noodles'],
    'korean-fried-chicken': ['korean fried chicken', 'yangnyeom chicken', 'how to make korean fried chicken', 'crispy korean chicken', 'dakgangjeong recipe'],
    'bibimbap': ['bibimbap recipe', 'how to make bibimbap', 'dolsot bibimbap', 'sizzling bibimbap', 'korean rice bowl recipe'],
    'kimbap': ['kimbap recipe', 'how to make kimbap', 'korean seaweed rice rolls', 'easy kimbap recipe', 'gimbap recipe'],
    'doenjang-jjigae': ['doenjang jjigae', 'soybean paste stew', 'how to make doenjang jjigae', 'korean stew', 'tofu stew recipe'],
    'budae-jjigae': ['budae jjigae', 'army stew', 'army base stew', 'how to make budae jjigae', 'korean army stew recipe'],
    'samgyetang': ['samgyetang', 'ginseng chicken soup', 'how to make samgyetang', 'korean chicken soup', 'korean healthy soup'],
    'miyeok-guk': ['miyeok guk', 'beef seaweed soup', 'how to make miyeok guk', 'korean seaweed soup', 'korean birthday soup'],
    'jeyuk-bokkeum': ['jeyuk bokkeum', 'spicy pork stir fry', 'korean spicy pork', 'how to make jeyuk bokkeum', 'dwaejigogi bokkeum'],
    'beef-bulgogi': ['beef bulgogi', 'bulgogi bokkeum', 'korean bulgogi recipe', 'how to make bulgogi', 'sweet soy beef'],
    'buchujeon': ['buchujeon', 'chive pancake', 'crispy chive pancake', 'how to make buchujeon', 'korean vegetable pancake'],
    'gamjajeon': ['gamjajeon', 'potato pancake', 'chewy potato pancake', 'how to make gamjajeon', 'korean potato pancake'],
    'mul-kimchi': ['mul kimchi', 'water kimchi', 'dongchimi recipe', 'how to make water kimchi', 'nabak kimchi'],
    'chonggak-kimchi': ['chonggak kimchi', 'ponytail radish kimchi', 'altari kimchi', 'how to make chonggak kimchi', 'bachelor radish kimchi'],
    'geotjeori': ['geotjeori', 'fresh kimchi', 'quick kimchi recipe', 'how to make geotjeori', 'napa cabbage fresh kimchi'],
    'sundubu-jjigae': ["sundubu jjigae", "soft tofu stew", "how to make soft tofu stew", "korean spicy tofu stew", "soondubu recipe"],
    'samgyeopsal-bbq': ["samgyeopsal", "korean pork belly bbq", "how to grill samgyeopsal", "korean bbq ssam", "kfood pork belly"],
    'galbitang': ["galbitang", "beef short rib soup", "how to make galbitang", "korean beef soup", "clear short rib soup"],
    'seolleongtang': ["seolleongtang", "ox bone soup", "korean beef bone soup", "milky bone broth", "how to make seolleongtang"],
    'gamjatang': ["gamjatang", "pork backbone stew", "how to make gamjatang", "korean potato stew", "spicy pork stew"],
    'beef-radish-soup': ["beef radish soup", "korean beef soup", "how to make beef radish soup", "muguk recipe", "korean home cooking"],
    'kongnamul-gukbap': ["kongnamul gukbap", "bean sprout soup", "korean hangover soup", "how to make kongnamul gukbap", "korean rice soup"],
    'jjajangmyeon': ["jjajangmyeon", "black bean noodles", "how to make jjajangmyeon", "korean chinese noodles", "chunjang recipe"],
    'jjamppong': ["jjamppong", "spicy seafood noodles", "how to make jjamppong", "korean spicy noodles", "seafood noodle soup"],
    'bajirak-kalguksu': ["bajirak kalguksu", "clam kalguksu", "korean knife cut noodles", "how to make kalguksu", "clam noodle soup"],
    'janchi-guksu': ["janchi guksu", "banquet noodles", "warm anchovy noodles", "how to make janchi guksu", "korean somen noodles"],
    'bibim-guksu': ["bibim guksu", "spicy mixed noodles", "korean cold noodles", "how to make bibim guksu", "spicy somen recipe"],
    'mul-naengmyeon': ["mul naengmyeon", "korean cold noodles", "chilled buckwheat noodles", "how to make naengmyeon", "dongchimi cold noodles"],
    'dakbokkeumtang': ["dakbokkeumtang", "spicy braised chicken", "korean chicken stew", "how to make dakbokkeumtang", "dakdoritang recipe"],
    'osam-bulgogi': ["osam bulgogi", "squid and pork belly", "spicy squid stir fry", "how to make osam bulgogi", "korean spicy pork"],
    'dwaeji-galbi': ["dwaeji galbi", "marinated pork ribs", "korean pork ribs", "how to make dwaeji galbi", "korean bbq ribs"],
    'sundae-twigim': ["korean sundae", "korean tempura", "twigim", "korean blood sausage", "korean street food snack"],
    'street-toast': ["korean street toast", "korean cabbage toast", "how to make street toast", "isaac toast style", "korean breakfast toast"],
    'crispy-mandu': ["gun mandu", "korean dumplings", "fried dumplings", "how to fry mandu", "crispy dumplings"],
    'eomuk-tang': ["eomuk tang", "fish cake soup", "korean street fish cakes", "how to make eomuk tang", "fish cake skewers"],
    'hotteok-bungeoppang': ["hotteok", "bungeoppang", "korean street snacks", "sweet korean pancake", "fish shaped pastry"],
    'gyeran-jjim': ["gyeran jjim", "korean steamed egg", "volcanic steamed egg", "how to make gyeran jjim", "fluffy steamed egg"],
    'gyeran-mari': ["gyeran mari", "korean rolled omelet", "rolled egg omelet", "how to make gyeran mari", "korean lunchbox egg"],
    'ganjang-gyeran-bap': ["ganjang gyeran bap", "egg rice", "butter soy sauce rice", "korean comfort food", "5 minute quick meal"],
  }
  const dishSpecific = specificTagsMap[ep.id] || [dish.toLowerCase(), `how to cook ${dish.toLowerCase()}`, `${dish.toLowerCase()} recipe`]
  const globalTags = [
    'soundblock k-cooking',
    'soundblock',
    'sound blocks english',
    'learn english speaking',
    'english speaking practice',
    'comprehensible input english',
    'easy english conversation',
    'beginner english speaking',
    'speak english out loud',
    'korean cooking in english',
    'k-food recipe in english',
    'cooking english expressions',
    'daily english speaking',
    'korean food',
    'kfood'
  ]
  return [...dishSpecific, ...globalTags].join(', ')
}

const copiedField = ref<string>('')

async function copySingleItem(field: string, text: string) {
  try {
    await navigator.clipboard.writeText(text)
    copiedField.value = field
    setTimeout(() => {
      if (copiedField.value === field) copiedField.value = ''
    }, 2000)
  } catch (err) {
    console.error('Failed to copy', err)
  }
}

const currentPinnedComment = computed(() => {
  const ep = currentEpisode.value
  const scene1 = ep.scenes[0]
  const sampleBlocks = scene1 ? scene1.blocks.map((b) => `[${b.en}]`).join(' + ') : ''
  const dishName = ep.shortTitle.replace(/^[^\s]+\s*/, '')
  return [
    `${ep.emoji} SoundBlock K-Cooking Challenge!`,
    `Can you speak today's sentence out loud in one breath?`,
    sampleBlocks ? `👉 ${sampleBlocks}` : `👉 "${scene1?.fullEn || ''}"`,
    '',
    `💬 Which step was your favorite in cooking ${dishName}?`,
    `Or tell us what Korean food you want to cook next in easy English! 👇`
  ].join('\n')
})

const currentDescriptionText = computed(() => {
  const ep = currentEpisode.value
  const dishName = ep.shortTitle.replace(/^[^\s]+\s*/, '')
  return [
    `Welcome to SoundBlock K-Cooking! ${ep.emoji}`,
    `Learn how to cook authentic Korean ${dishName} while mastering real-life English speaking using simple 3-part sound blocks!`,
    '',
    `💡 What are Sound Blocks?`,
    `① 1st Block: Starter rhythm (e.g. "I'm gonna", "You have to", "I'll")`,
    `② Core Action: Natural cooking action (e.g. "${ep.scenes[0]?.blocks[1]?.en || 'action'}")`,
    `③ Detail Block: Completes the scene with clarity (e.g. "${ep.scenes[0]?.blocks[2]?.en || 'detail'}")`,
    '',
    `--- ⏱️ Timestamps ---`,
    `00:00 Intro · Let's get cooking!`,
    ...ep.scenes.map((s, i) => {
      const totalSec = (i + 1) * 32
      const mm = String(Math.floor(totalSec / 60)).padStart(2, '0')
      const ss = String(totalSec % 60).padStart(2, '0')
      return `${mm}:${ss} ${s.stepTitle}
- Full Sentence: "${s.fullEn}"
- Blocks: ${s.blocks.map((b) => `[${b.en}]`).join(' + ')}
- Swap 1st Block: ${s.combos.map((c) => c.fullEn).join(' / ')}`
    }),
    `${String(Math.floor((32 + ep.scenes.length * 32) / 60)).padStart(2, '0')}:${String((32 + ep.scenes.length * 32) % 60).padStart(2, '0')} Full Review · Master all sound blocks!`,
    '',
    `🔔 Subscribe & Like to cook more delicious K-food in easy English!`,
    `Official Channel · YouTube @SoundBlockKCooking`,
    '',
    `#SoundBlockKCooking #KFood #${dishName.replace(/\s+/g, '')} #LearnEnglish #EnglishSpeaking #EasyEnglish #KoreanCooking #CookingEnglish`
  ].join('\n')
})

async function copyEpisodeScript() {
  const ep = currentEpisode.value
  const lines = [
    `=== 1. VIDEO TITLE ===`,
    ep.ytTitle,
    '',
    `=== 2. THUMBNAIL TEXT ===`,
    ep.thumbnailText,
    '',
    `=== 3. PINNED COMMENT (Copy & Pin in YouTube comments) ===`,
    currentPinnedComment.value,
    '',
    `=== 4. DESCRIPTION & TIMESTAMPS ===`,
    currentDescriptionText.value,
    '',
    `=== 5. YOUTUBE VIDEO TAGS (Copy & Paste into YouTube Studio 'Tags' box) ===`,
    getEpisodeTags(ep)
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
  if (typeof window !== 'undefined') {
    try {
      const saved = localStorage.getItem('soundblock_font_scale')
      if (saved === 'normal' || saved === 'large' || saved === 'huge') {
        fontScale.value = saved
      }
    } catch {}
  }
  if (typeof document !== 'undefined') {
    document.addEventListener('fullscreenchange', onFullscreenChange)
    window.addEventListener('keydown', onKeyDown)
  }
})

onBeforeUnmount(() => {
  stopAutoShow()
  stopScreenRecording()
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
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 999999 !important;
  margin: 0 !important;
  border-radius: 0 !important;
  border: none !important;
  background: #000 !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
}

body.kf-theater-body {
  overflow: hidden !important;
}

body.kf-theater-body .VPNav,
body.kf-theater-body .VPSidebar,
body.kf-theater-body .VPFooter,
body.kf-theater-body .VPLocalNav,
body.kf-theater-body header,
body.kf-theater-body nav {
  display: none !important;
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
.kf-aspect-toggle,
.kf-font-toggle {
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

.kf-font-btn {
  background: rgba(250, 204, 21, 0.12);
  border-color: rgba(250, 204, 21, 0.45);
  color: var(--vp-c-text-1);
}

.kf-font-btn strong {
  color: #d97706;
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
  width: 100vw;
}

.theater-fullscreen .screen-wide {
  width: 100vw !important;
  height: 100vh !important;
  max-height: 100vh !important;
  border-radius: 0 !important;
  box-shadow: none !important;
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
  height: 720px;
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

/* 방송용 다크 스크림 그라데이션 */
.kf-scrim-gradient {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(
    to bottom,
    rgba(9, 13, 24, 0.78) 0%,
    rgba(9, 13, 24, 0.15) 20%,
    rgba(9, 13, 24, 0.35) 45%,
    rgba(9, 13, 24, 0.92) 75%,
    rgba(9, 13, 24, 0.98) 100%
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
  padding: 0.8rem 1.2rem 0.25rem;
  gap: 0.75rem;
}

.kf-hud-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: rgba(15, 23, 42, 0.82);
  backdrop-filter: blur(8px);
  padding: 0.35rem 0.85rem 0.35rem 0.45rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.kf-hud-logo {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.kf-hud-brand {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.hud-ch-name {
  font-size: 0.85rem;
  font-weight: 800;
  color: #facc15;
}

.hud-ep-step {
  font-size: 1.15rem;
  font-weight: 900;
  color: #fff;
}

.kf-hud-vocab {
  background: rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(10px);
  padding: 0.5rem 1.15rem;
  border-radius: 14px;
  border: 1.5px solid rgba(56, 189, 248, 0.75);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  color: #fff;
}

.vocab-tag {
  font-size: 0.78rem;
  font-weight: 900;
  color: #38bdf8;
  letter-spacing: 0.05em;
}

.kf-hud-vocab strong {
  font-size: 1.25rem;
  font-weight: 900;
  color: #fff;
}

.kf-hud-progress {
  position: relative;
  z-index: 10;
  display: flex;
  gap: 0.35rem;
  padding: 0 1.2rem;
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

/* 훈련 단계 탭 (상단 배너 바로 아래) */
.kf-stage-tabs {
  position: relative;
  z-index: 12;
  display: flex;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.45rem 1rem 0;
}

.stage-tab-btn {
  padding: 0.45rem 1.15rem;
  font-size: 0.95rem;
  font-weight: 900;
  border-radius: 999px;
  border: 1.5px solid rgba(255, 255, 255, 0.28);
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(10px);
  color: #e2e8f0;
  cursor: pointer;
  transition: all 0.18s ease;
}

.stage-tab-btn.active {
  background: #facc15;
  color: #0f172a;
  border-color: #facc15;
  box-shadow: 0 4px 14px rgba(250, 204, 21, 0.35);
}

/* 중앙 코칭 배너 & YOUR TURN 모달 */
.kf-coach-banner {
  position: relative;
  z-index: 10;
  align-self: center;
  max-width: 92%;
  margin: auto 1rem 0.55rem;
  background: rgba(10, 15, 30, 0.96);
  backdrop-filter: blur(14px);
  border: 2px solid rgba(250, 204, 21, 0.85);
  border-radius: 999px;
  padding: 0.55rem 1.45rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #ffffff;
  box-shadow: 0 10px 32px rgba(0, 0, 0, 0.65);
}

.coach-icon {
  font-size: 0.95rem;
  font-weight: 900;
  padding: 0.28rem 0.85rem;
  border-radius: 999px;
  background: #facc15;
  color: #0f172a;
  white-space: nowrap;
  letter-spacing: -0.01em;
}

.coach-text {
  font-size: 1.25rem;
  font-weight: 800;
  line-height: 1.45;
  color: #ffffff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9);
}

.kf-center-turn-modal {
  position: relative;
  z-index: 14;
  align-self: center;
  width: min(88%, 580px);
  margin: auto 1rem 0.5rem;
  background: linear-gradient(135deg, rgba(5, 150, 105, 0.96), rgba(16, 185, 129, 0.96));
  border: 2px solid #fde047;
  border-radius: 16px;
  padding: 0.85rem 1.25rem;
  color: #fff;
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55);
}

.turn-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.45rem;
}

.turn-mic-icon {
  font-size: 1.6rem;
}

.turn-texts {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.turn-texts strong {
  font-size: 1.05rem;
  color: #fef08a;
}

.turn-texts span {
  font-size: 0.84rem;
  opacity: 0.95;
}

.turn-sec-badge {
  font-size: 0.95rem;
  font-weight: 900;
  padding: 0.25rem 0.65rem;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.35);
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
   하단 방송 자막 독 (Broadcast Lower-Third)
   =================================================== */
.kf-lower-third {
  position: relative;
  z-index: 10;
  padding: 0.6rem 1.2rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

/* ---------------------------------------------------
   STAGE 1 · 시작 블록 3단 교체 스타일
   --------------------------------------------------- */
.kf-core-anchor-bar {
  display: inline-flex;
  align-items: center;
  align-self: center;
  gap: 0.65rem;
  background: rgba(5, 150, 105, 0.38);
  backdrop-filter: blur(12px);
  border: 1.5px solid rgba(52, 211, 153, 0.85);
  border-radius: 999px;
  padding: 0.35rem 1.15rem;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
  margin-bottom: 0.25rem;
  transition: transform 0.18s ease;
}

.kf-core-anchor-bar:hover {
  transform: scale(1.02);
}

.kf-core-anchor-bar .anchor-badge {
  font-size: 0.78rem;
  font-weight: 800;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: #059669;
  color: #fff;
}

.kf-core-anchor-bar .anchor-en {
  font-size: 1.35rem;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
}

.kf-core-anchor-bar .anchor-hint {
  font-size: 0.74rem;
  color: #a7f3d0;
}

.kf-combo-grid {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  width: 100%;
}

.kf-combo-card {
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(12px);
  border: 2px solid rgba(255, 255, 255, 0.16);
  border-radius: 16px;
  padding: 0.85rem 1.35rem;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
}

.kf-combo-card.active {
  background: rgba(30, 58, 138, 0.6);
  border-color: #fde047;
  transform: scale(1.02);
  box-shadow: 0 0 0 3px #fde047, 0 12px 32px rgba(0, 0, 0, 0.6);
}

.combo-sentence {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.combo-block-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.32rem 0.85rem;
  border-radius: 10px;
  font-size: 1.45rem;
  font-weight: 900;
  color: #fff;
  letter-spacing: -0.01em;
  text-shadow: 0 2px 5px rgba(0, 0, 0, 0.85);
  transition: all 0.18s ease;
}

.combo-block-pill.c-bb {
  background: rgba(37, 99, 235, 0.45);
  border: 2px solid rgba(96, 165, 250, 0.9);
  box-shadow: 0 2px 10px rgba(37, 99, 235, 0.35);
}

.combo-block-pill.c-core {
  background: rgba(5, 150, 105, 0.45);
  border: 2px solid rgba(52, 211, 153, 0.9);
  box-shadow: 0 2px 10px rgba(5, 150, 105, 0.35);
}

.combo-block-pill.c-db {
  background: rgba(147, 51, 234, 0.45);
  border: 2px solid rgba(192, 132, 252, 0.9);
  box-shadow: 0 2px 10px rgba(147, 51, 234, 0.35);
}

.font-large .combo-block-pill {
  font-size: 1.75rem;
  padding: 0.38rem 1rem;
}

.font-huge .combo-block-pill {
  font-size: 2.15rem;
  padding: 0.48rem 1.15rem;
}

.combo-en {
  font-size: 1.25rem;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
}

.combo-pron {
  font-size: 0.88rem;
  font-weight: 700;
  color: #38bdf8;
}

.combo-ko {
  font-size: 0.86rem;
  font-weight: 700;
  color: #e2e8f0;
}

/* ---------------------------------------------------
   STAGE 2 · 실전 자석 합체 미션 스타일
   --------------------------------------------------- */
.kf-mission-banner {
  background: rgba(220, 38, 38, 0.25);
  backdrop-filter: blur(10px);
  border: 1.5px solid rgba(239, 68, 68, 0.7);
  border-radius: 12px;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  color: #fff;
  cursor: pointer;
}

.m-badge {
  font-size: 0.74rem;
  font-weight: 900;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  background: #ef4444;
}

.m-text {
  font-size: 1.05rem;
  font-weight: 800;
  flex: 1;
}

.m-listen {
  font-size: 0.72rem;
  color: #fde047;
}

.kf-snap-target-row {
  display: flex;
  align-items: stretch;
  gap: 0.75rem;
  padding: 0.75rem 1.1rem;
  background: rgba(15, 23, 42, 0.75);
  border-radius: 18px;
  border: 2px dashed rgba(255, 255, 255, 0.25);
  transition: all 0.3s ease;
}

.kf-snap-target-row.snapped {
  border-style: solid;
  border-color: #fde047;
  background: rgba(15, 23, 42, 0.92);
  box-shadow: 0 0 25px rgba(250, 204, 21, 0.45);
}

/* 🌟 회색 대신 선명한 블루 / 그린 / 오렌지 고유 레고 블록 색상 탑재 */
.snap-slot {
  flex: 1;
  min-height: 90px;
  padding: 0.75rem 0.95rem;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  text-align: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
}

.slot-bb {
  background: rgba(29, 78, 216, 0.5) !important;
  border: 2.5px dashed #60a5fa !important;
}
.slot-bb .slot-badge {
  color: #bfdbfe !important;
}
.slot-bb.is-filled {
  background: #2563eb !important;
  border: 2.5px solid #93c5fd !important;
  box-shadow: 0 0 22px rgba(37, 99, 235, 0.75) !important;
}

.slot-core {
  background: rgba(4, 120, 87, 0.5) !important;
  border: 2.5px dashed #34d399 !important;
}
.slot-core .slot-badge {
  color: #a7f3d0 !important;
}
.slot-core.is-filled {
  background: #059669 !important;
  border: 2.5px solid #6ee7b7 !important;
  box-shadow: 0 0 22px rgba(5, 150, 105, 0.75) !important;
}

.slot-db {
  background: rgba(180, 83, 9, 0.55) !important;
  border: 2.5px solid #fbbf24 !important;
}
.slot-db .slot-badge {
  color: #fde68a !important;
}
.slot-db.is-filled {
  background: #d97706 !important;
  border: 2.5px solid #fde047 !important;
  box-shadow: 0 0 22px rgba(217, 119, 6, 0.75) !important;
}

.slot-badge {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.slot-word {
  font-size: 1.65rem;
  font-weight: 900;
  color: #fff;
  line-height: 1.25;
  text-align: center;
  word-break: keep-all;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.7);
}

.slot-word.is-qmark {
  font-size: 2.1rem;
  color: #ffffff;
  font-weight: 900;
}

.snap-plus {
  display: flex;
  align-items: center;
  font-weight: 900;
  color: #fde047;
  font-size: 1.55rem;
}

/* 🌟 후보 블록 풀: 라벨과 버튼이 여유 있게 떨어지도록 간격 대폭 확대 */
.kf-candidate-pool {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  width: 100%;
  margin-top: 0.4rem;
}

.cand-row {
  display: flex;
  align-items: center;
  gap: 1.25rem; /* 라벨과 버튼 사이 시원하고 넉넉한 간격 */
  padding: 0.65rem 1.05rem;
  border-radius: 16px;
  backdrop-filter: blur(14px);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4);
}

.cand-row.row-bb {
  background: rgba(30, 58, 138, 0.45);
  border: 2px solid rgba(96, 165, 250, 0.45);
}

.cand-row.row-core {
  background: rgba(6, 78, 59, 0.45);
  border: 2px solid rgba(52, 211, 153, 0.45);
}

.cand-badge-col {
  flex-shrink: 0;
}

.cand-sec-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.65rem 1.35rem;
  border-radius: 12px;
  font-size: 1.25rem;
  font-weight: 900;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.cand-sec-badge.badge-bb {
  background: #1d4ed8;
  border: 2px solid #93c5fd;
  color: #ffffff;
  box-shadow: 0 0 14px rgba(37, 99, 235, 0.6);
}

.cand-sec-badge.badge-core {
  background: #047857;
  border: 2px solid #6ee7b7;
  color: #ffffff;
  box-shadow: 0 0 14px rgba(5, 150, 105, 0.6);
}

.cand-items {
  display: flex;
  gap: 0.85rem;
  flex: 1;
}

/* 🌟 후보 버튼: 회색 대신 선명한 블루 / 그린 레고 블록 */
.cand-btn {
  flex: 1;
  padding: 0.75rem 1.25rem;
  border-radius: 14px;
  font-size: 1.65rem;
  font-weight: 900;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
  text-align: center;
  white-space: nowrap;
}

.cand-btn.cand-bb {
  background: rgba(30, 64, 175, 0.65);
  border: 2.5px solid #60a5fa;
  color: #ffffff;
}
.cand-btn.cand-bb:hover {
  background: #2563eb;
  border-color: #93c5fd;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.7);
}

.cand-btn.cand-core {
  background: rgba(6, 95, 70, 0.65);
  border: 2.5px solid #34d399;
  color: #ffffff;
}
.cand-btn.cand-core:hover {
  background: #059669;
  border-color: #6ee7b7;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(5, 150, 105, 0.7);
}

.cand-btn.selected {
  transform: translateY(-2px) scale(1.02);
}

.cand-bb.selected {
  background: #1d4ed8 !important;
  border-color: #fde047 !important;
  color: #fff !important;
  box-shadow: 0 0 24px rgba(250, 204, 21, 0.75) !important;
}

.cand-core.selected {
  background: #047857 !important;
  border-color: #fde047 !important;
  color: #fff !important;
  box-shadow: 0 0 24px rgba(250, 204, 21, 0.75) !important;
}

.cand-btn.correct {
  border-color: #fde047 !important;
  background: #eab308 !important;
  color: #0f172a !important;
  box-shadow: 0 0 26px rgba(250, 204, 21, 0.95);
  transform: scale(1.04);
}

/* ---------------------------------------------------
   STAGE 3 · 완성 문장 & 소리 블록 표준 스타일 (Step 2와 통일된 겹침 없는 레고 블록)
   --------------------------------------------------- */
.kf-blocks-row {
  display: flex;
  align-items: stretch;
  gap: 0.75rem;
  width: 100%;
}

.kf-glass-block {
  flex: 1;
  min-height: 90px;
  padding: 0.75rem 1rem;
  border-radius: 14px;
  backdrop-filter: blur(14px);
  cursor: pointer;
  border: 2.5px solid transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  text-align: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s ease, border-color 0.2s ease;
}

.kf-glass-block.bb {
  background: rgba(29, 78, 216, 0.75);
  border-color: #60a5fa;
}

.kf-glass-block.core {
  background: rgba(4, 120, 87, 0.75);
  border-color: #34d399;
}

.kf-glass-block.db {
  background: rgba(180, 83, 9, 0.75);
  border-color: #fbbf24;
}

.kf-glass-block.active {
  transform: translateY(-3px) scale(1.02);
  border-color: #fde047 !important;
  box-shadow: 0 0 25px rgba(250, 204, 21, 0.8), 0 8px 24px rgba(0, 0, 0, 0.5);
}

.gblk-top {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
}

.gblk-badge {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.kf-glass-block.bb .gblk-badge {
  color: #bfdbfe;
}

.kf-glass-block.core .gblk-badge {
  color: #a7f3d0;
}

.kf-glass-block.db .gblk-badge {
  color: #fde68a;
}

.gblk-en {
  font-size: 1.65rem;
  font-weight: 900;
  color: #ffffff;
  line-height: 1.25;
  text-align: center;
  word-break: keep-all;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
}

.kf-sentence-banner {
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 0.65rem 1.05rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.kf-main-en {
  font-size: 1.45rem;
  font-weight: 900;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.85);
}

.play-hint-icon {
  font-size: 1.1rem;
}

.kf-sub-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.94rem;
}

.kf-meta-pron {
  color: #38bdf8;
  font-weight: 800;
}

.kf-meta-ko {
  color: #f8fafc;
  font-weight: 800;
}

/* ===================================================
   🔠 글자 대폭 확대 (한글 발음 제거로 확보된 공간 전면 활용)
   =================================================== */
.anchor-en {
  font-size: 1.5rem;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.85);
}

.combo-en {
  font-size: 1.5rem;
  font-weight: 900;
  color: #fff;
  line-height: 1.3;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
}

.combo-ko {
  font-size: 1.15rem;
  font-weight: 800;
  color: #fde047;
  letter-spacing: -0.01em;
}

.gblk-en {
  font-size: 1.55rem;
  font-weight: 900;
  color: #fff;
  letter-spacing: -0.01em;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
}

.kf-main-en {
  font-size: 1.85rem;
  font-weight: 900;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  line-height: 1.3;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.95);
}

.kf-meta-ko {
  font-size: 1.25rem;
  color: #fde047;
  font-weight: 800;
}

.font-large .kf-main-en {
  font-size: 2.25rem;
}
.font-large .gblk-en {
  font-size: 1.85rem;
}
.font-large .combo-en {
  font-size: 1.8rem;
}
.font-large .anchor-en {
  font-size: 1.8rem;
}
.font-large .combo-ko {
  font-size: 1.28rem;
}
.font-large .kf-meta-ko {
  font-size: 1.38rem;
}
.font-large .m-text {
  font-size: 1.3rem;
}
.font-large .slot-word {
  font-size: 1.55rem;
}

.font-huge .kf-main-en {
  font-size: 2.75rem;
}
.font-huge .gblk-en {
  font-size: 2.25rem;
}
.font-huge .combo-en {
  font-size: 2.15rem;
}
.font-huge .anchor-en {
  font-size: 2.15rem;
}
.font-huge .combo-ko {
  font-size: 1.45rem;
}
.font-huge .kf-meta-ko {
  font-size: 1.55rem;
}
.font-huge .m-text {
  font-size: 1.45rem;
}
.font-huge .slot-word {
  font-size: 1.8rem;
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

.kf-intro-content {
  position: relative;
  z-index: 10;
  margin: auto;
  padding: 1.5rem;
  text-align: center;
  color: #fff;
  width: min(92%, 840px);
}

/* 🌟 아웃트로: 760px 제한을 풀고 16:9 와이드 화면에 맞춰 넓고 시원하게 전면 배치 */
.kf-outro-content {
  position: relative;
  z-index: 10;
  margin: auto;
  padding: 1rem 2rem;
  text-align: center;
  color: #fff;
  width: min(96%, 1440px);
  max-height: 96%;
  display: flex;
  flex-direction: column;
  justify-content: center;
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

/* 아웃트로 복습 그리드: 4열 x 2행 와이드 배치로 8개 문장 전체가 짤림 없이 한 화면에 쏙 */
.outro-badge {
  display: inline-block;
  font-size: 1.2rem;
  font-weight: 800;
  color: #34d399;
  letter-spacing: 0.06em;
  margin-bottom: 0.35rem;
}

.outro-title {
  margin: 0.35rem 0 1.2rem !important;
  font-size: 2.35rem !important;
  font-weight: 900;
  color: #fff !important;
  line-height: 1.35 !important; /* 🌟 2줄로 개행되어도 위아래 글자가 겹치거나 붙지 않는 충분한 줄간격 */
  border: none !important;
  text-shadow: 0 3px 12px rgba(0, 0, 0, 0.85);
}

.kf-review-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 4열 x 2행으로 8개 전체가 한눈에 쏙 들어옴! */
  gap: 0.85rem;
  text-align: left;
  margin-bottom: 1.2rem;
  width: 100%;
}

.kf-review-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.95rem;
  border-radius: 14px;
  background: rgba(30, 41, 59, 0.92);
  border: 2px solid rgba(255, 255, 255, 0.22);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
}

.kf-review-item:hover {
  border-color: #38bdf8;
  background: rgba(14, 165, 233, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(56, 189, 248, 0.4);
}

.rev-num {
  font-size: 1.2rem;
  font-weight: 900;
  color: #38bdf8;
  min-width: 1.8rem;
  flex-shrink: 0;
}

.rev-body {
  flex: 1;
}

.rev-en {
  font-size: 1.15rem;
  font-weight: 800;
  color: #fff;
  line-height: 1.3;
  word-break: keep-all;
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
  flex-direction: column;
  align-items: stretch;
  gap: 0.35rem;
  padding: 0.45rem 0;
  border-bottom: 1px dashed var(--vp-c-divider);
}

.kf-meta-row:last-child {
  border-bottom: none;
}

.kf-meta-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.kf-copy-mini-btn {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  border: 1px solid var(--vp-c-brand-2);
  border-radius: 6px;
  padding: 0.2rem 0.55rem;
  font-size: 0.76rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.kf-copy-mini-btn:hover {
  background: var(--vp-c-brand-1);
  color: #fff;
}

.kf-code-block {
  background: var(--vp-c-bg-alt);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  font-family: inherit;
  font-size: 0.8rem;
  line-height: 1.45;
  white-space: pre-wrap;
  margin: 0;
  color: var(--vp-c-text-1);
}

.kf-desc-textarea {
  width: 100%;
  background: var(--vp-c-bg-alt);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.78rem;
  line-height: 1.45;
  color: var(--vp-c-text-1);
  resize: vertical;
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

/* ===================================================
   모바일 화면 전용 미디어 쿼리 (@media max-width: 768px)
   스마트폰에서 글자가 작아서 안 보이는 현상 완벽 해결!
   =================================================== */
@media (max-width: 1100px) and (min-width: 769px) {
  .kf-review-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* ===================================================
   📱 스마트폰 세로 모드(Portrait) 전용 완벽 대응
   화면 겹침/잘림 방지 및 모바일 앱(쇼츠/릴스) 스타일 레이아웃
   =================================================== */
@media (max-width: 768px) {
  .kf-studio-v2 {
    margin: 0.8rem 0 1.5rem;
    border-radius: 14px;
  }

  .kf-topbar {
    padding: 0.55rem 0.75rem;
    gap: 0.4rem;
  }

  .kf-studio-badge {
    font-size: 0.68rem;
    padding: 0.2rem 0.5rem;
  }

  .kf-ep-btn,
  .kf-mode-btn {
    padding: 0.28rem 0.55rem;
    font-size: 0.72rem;
  }

  /* 세로 화면에서는 고정 높이 대신 스마트폰 화면에 맞게 유연하게 확장 */
  .kf-broadcast-screen.screen-wide {
    aspect-ratio: auto;
    min-height: 580px;
    height: auto;
    display: flex;
    flex-direction: column;
  }

  .kf-main-scene,
  .kf-special-slide {
    position: relative;
    inset: auto;
    width: 100%;
    min-height: 580px;
    height: auto;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: visible;
  }

  .kf-bg-full {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .kf-scrim-gradient {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      to bottom,
      rgba(9, 13, 24, 0.82) 0%,
      rgba(9, 13, 24, 0.25) 20%,
      rgba(9, 13, 24, 0.65) 55%,
      rgba(9, 13, 24, 0.96) 80%,
      rgba(9, 13, 24, 1) 100%
    );
  }

  /* 상단 모바일 컴팩트 HUD */
  .kf-hud-top {
    padding: 0.65rem 0.85rem 0.25rem;
    gap: 0.5rem;
  }

  .kf-hud-logo {
    width: 28px;
    height: 28px;
  }

  .hud-ch-name {
    display: none;
  }

  .hud-ep-step {
    font-size: 0.82rem;
  }

  .kf-hud-vocab {
    padding: 0.25rem 0.65rem;
  }

  .vocab-tag {
    font-size: 0.58rem;
  }

  .kf-hud-vocab strong {
    font-size: 0.85rem;
  }

  .kf-hud-progress {
    padding: 0 0.85rem;
  }

  /* 모바일 단계 선택 탭 */
  .kf-stage-tabs {
    flex-wrap: wrap;
    gap: 0.3rem;
    padding: 0.4rem 0.65rem 0;
  }

  .stage-tab-btn {
    font-size: 0.74rem;
    padding: 0.28rem 0.65rem;
  }

  /* 중앙 코칭 배너 */
  .kf-coach-banner {
    max-width: 94%;
    margin: 0.5rem auto 0.4rem;
    padding: 0.4rem 0.85rem;
    gap: 0.45rem;
  }

  .coach-icon {
    font-size: 0.72rem;
    padding: 0.2rem 0.55rem;
  }

  .coach-text {
    font-size: 0.95rem;
    line-height: 1.35;
  }

  /* 하단 자막 & 인터랙션 독 */
  .kf-lower-third {
    padding: 0.5rem 0.75rem 1rem;
    gap: 0.55rem;
  }

  /* STAGE 1: 모바일 세로 콤보 카드 */
  .kf-core-anchor-bar {
    padding: 0.3rem 0.85rem;
    gap: 0.45rem;
    margin-bottom: 0.2rem;
  }

  .kf-core-anchor-bar .anchor-badge {
    font-size: 0.68rem;
    padding: 0.12rem 0.45rem;
  }

  .kf-core-anchor-bar .anchor-en {
    font-size: 1.15rem;
  }

  .kf-core-anchor-bar .anchor-hint {
    font-size: 0.68rem;
  }

  .kf-combo-grid {
    gap: 0.45rem;
  }

  .kf-combo-card {
    padding: 0.55rem 0.75rem;
    border-radius: 12px;
  }

  .combo-sentence {
    gap: 0.35rem;
  }

  .combo-block-pill {
    font-size: 1.25rem !important;
    padding: 0.25rem 0.65rem !important;
    border-radius: 8px;
  }

  /* STAGE 2: 모바일 실전 자석 합체 */
  .kf-mission-banner {
    padding: 0.45rem 0.75rem;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  .m-badge {
    font-size: 0.68rem;
  }

  .m-text {
    font-size: 0.95rem;
  }

  .m-listen {
    display: none;
  }

  .kf-snap-target-row {
    padding: 0.45rem 0.6rem;
    gap: 0.35rem;
  }

  .snap-slot {
    padding: 0.4rem 0.5rem;
  }

  .slot-badge {
    font-size: 0.62rem;
  }

  .slot-word {
    font-size: 1.1rem;
  }

  .cand-row {
    flex-direction: column;
    align-items: stretch;
    gap: 0.55rem;
    padding: 0.55rem;
  }

  .cand-sec-badge {
    font-size: 0.95rem;
    padding: 0.35rem 0.75rem;
  }

  .cand-items {
    width: 100%;
    gap: 0.45rem;
  }

  .cand-btn {
    font-size: 1.15rem;
    padding: 0.45rem 0.75rem;
  }

  .qc-en {
    font-size: 1.05rem;
  }

  /* STAGE 3: 모바일 완성 문장 */
  .kf-blocks-row {
    flex-direction: column;
    gap: 0.35rem;
  }

  .kf-glass-block {
    padding: 0.45rem 0.75rem;
  }

  .gblk-badge {
    font-size: 0.68rem;
  }

  .gblk-en {
    font-size: 1.35rem;
  }

  .kf-sentence-banner {
    padding: 0.55rem 0.85rem;
  }

  .kf-main-en {
    font-size: 1.35rem;
  }

  .kf-meta-ko {
    font-size: 1.05rem;
  }

  /* 인트로 / 아웃트로 모바일 대응 */
  .kf-intro-content,
  .kf-outro-content {
    padding: 1rem 0.85rem;
  }

  .kf-intro-title {
    font-size: 1.4rem !important;
  }

  .kf-intro-sub {
    font-size: 0.85rem;
  }

  .kf-intro-formula {
    gap: 0.3rem;
  }

  .f-pill {
    font-size: 0.72rem;
    padding: 0.35rem 0.6rem;
  }

  .kf-review-grid {
    grid-template-columns: 1fr;
    max-height: 280px;
    overflow-y: auto;
  }

  .kf-controls-panel {
    padding: 0.75rem 0.85rem;
  }

  .kf-nav-group {
    justify-content: center;
  }

  .kf-ctrl-btn {
    font-size: 0.74rem;
    padding: 0.32rem 0.6rem;
  }
}

/* ===================================================
   🖥️ 1080p 풀스크린 방송 모드 전용 방송국급 대왕 글씨
   유튜브 녹화 시 TV 방송 자막처럼 시원시원하고 굵직하게 출력
   =================================================== */
.theater-fullscreen .kf-hud-top {
  padding: 1.4rem 2.5rem 0.5rem;
}

.theater-fullscreen .kf-hud-logo {
  width: 52px;
  height: 52px;
}

.theater-fullscreen .hud-ch-name {
  font-size: 1.15rem;
}

.theater-fullscreen .hud-ep-step {
  font-size: 1.65rem;
}

.theater-fullscreen .vocab-tag {
  font-size: 1rem;
}

.theater-fullscreen .kf-hud-vocab strong {
  font-size: 1.75rem;
}

.theater-fullscreen .kf-stage-tabs {
  padding: 0.85rem 2.5rem 0;
  gap: 1rem;
}

.theater-fullscreen .stage-tab-btn {
  font-size: 1.35rem;
  padding: 0.65rem 1.75rem;
}

.theater-fullscreen .kf-coach-banner {
  padding: 0.85rem 2.2rem;
  margin-bottom: 0.85rem;
  border-width: 2.5px;
}

.theater-fullscreen .coach-icon {
  font-size: 1.25rem;
  padding: 0.45rem 1.2rem;
}

.theater-fullscreen .coach-text {
  font-size: 1.75rem;
  line-height: 1.45;
}

.theater-fullscreen .kf-center-turn-modal {
  width: min(85%, 840px);
  padding: 1.2rem 1.85rem;
  border-radius: 20px;
}

.theater-fullscreen .turn-mic-icon {
  font-size: 2.6rem;
}

.theater-fullscreen .turn-texts strong {
  font-size: 1.6rem;
}

.theater-fullscreen .turn-texts span {
  font-size: 1.15rem;
}

.theater-fullscreen .turn-sec-badge {
  font-size: 1.35rem;
  padding: 0.35rem 0.85rem;
}

/* 풀스크린 하단 자막 독 */
.theater-fullscreen .kf-lower-third {
  padding: 0.85rem 2.5rem 1.85rem;
  gap: 0.85rem;
}

/* STAGE 1: 시작 블록 3단 교체 대왕 폰트 */
.theater-fullscreen .kf-core-anchor {
  padding: 0.75rem 1.55rem;
  border-radius: 16px;
}

.theater-fullscreen .anchor-label {
  font-size: 1.1rem;
}

.theater-fullscreen .anchor-en {
  font-size: 2.15rem;
}

.theater-fullscreen .anchor-hint {
  font-size: 1rem;
}

.theater-fullscreen .kf-combo-card {
  padding: 0.75rem 1.35rem;
  border-radius: 16px;
  gap: 0.35rem;
}

.theater-fullscreen .kf-core-anchor-bar {
  padding: 0.55rem 1.65rem;
}
.theater-fullscreen .kf-core-anchor-bar .anchor-badge {
  font-size: 1rem;
  padding: 0.25rem 0.75rem;
}
.theater-fullscreen .kf-core-anchor-bar .anchor-en {
  font-size: 1.85rem;
}

.theater-fullscreen .kf-intro-content {
  width: min(95%, 1350px);
  padding: 3rem 2rem;
}

.theater-fullscreen .kf-intro-top-pill {
  font-size: 1.55rem;
  padding: 0.65rem 1.85rem 0.65rem 0.85rem;
  margin-bottom: 1.6rem;
}

.theater-fullscreen .kf-mini-logo {
  width: 48px;
  height: 48px;
}

.theater-fullscreen .kf-intro-ep-badge {
  font-size: 1.75rem;
  margin-bottom: 0.85rem;
}

.theater-fullscreen .kf-intro-title {
  font-size: 4.25rem !important;
  margin-bottom: 1.25rem !important;
  line-height: 1.2;
}

.theater-fullscreen .kf-intro-sub {
  font-size: 1.85rem;
  max-width: 1100px;
  margin-bottom: 2.2rem !important;
}

.theater-fullscreen .kf-intro-formula {
  gap: 1.1rem;
  margin-bottom: 2.6rem;
}

.theater-fullscreen .f-pill {
  padding: 1.05rem 2.15rem;
  border-radius: 18px;
  font-size: 1.85rem;
}

.theater-fullscreen .f-plus {
  font-size: 2.25rem;
}

.theater-fullscreen .kf-intro-cta {
  padding: 1.25rem 3.25rem;
  font-size: 2.15rem;
  border-radius: 999px;
}

.theater-fullscreen .kf-combo-grid {
  gap: 0.85rem;
}

.theater-fullscreen .kf-combo-card {
  padding: 1.15rem 2rem;
  border-radius: 20px;
}

.theater-fullscreen .combo-sentence {
  gap: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

.theater-fullscreen .combo-block-pill {
  font-size: 2.05rem;
  padding: 0.48rem 1.35rem;
  border-radius: 16px;
  border-width: 3px;
  max-width: 100%;
  word-break: keep-all;
  text-align: center;
  white-space: nowrap;
}

.theater-fullscreen .combo-ko {
  font-size: 1.55rem;
  padding-left: 0.35rem;
}

/* STAGE 2: 실전 자석 합체 대왕 폰트 */
.theater-fullscreen .kf-mission-banner {
  padding: 0.85rem 1.65rem;
  border-radius: 16px;
}

.theater-fullscreen .m-badge {
  font-size: 1.1rem;
  padding: 0.35rem 0.85rem;
}

.theater-fullscreen .m-text {
  font-size: 1.85rem;
}

.theater-fullscreen .m-listen {
  font-size: 1.05rem;
}

.theater-fullscreen .snap-slot {
  padding: 0.85rem 1.25rem;
  border-radius: 14px;
}

.theater-fullscreen .m-text {
  font-size: 1.65rem;
}

.theater-fullscreen .m-puzzle {
  font-size: 1.85rem;
}

.theater-fullscreen .m-clue {
  font-size: 1.55rem;
}

.theater-fullscreen .snap-slot {
  min-height: 120px;
  padding: 0.95rem 1.25rem;
  border-radius: 18px;
  gap: 0.65rem;
}

.theater-fullscreen .slot-badge {
  font-size: 1.55rem;
}

.theater-fullscreen .slot-word {
  font-size: 2.35rem;
  line-height: 1.25;
}

.theater-fullscreen .slot-word.is-qmark {
  font-size: 2.85rem;
}

.theater-fullscreen .cand-row {
  padding: 0.75rem 1.25rem;
  border-radius: 18px;
  gap: 1.25rem;
}

.theater-fullscreen .cand-sec-badge {
  font-size: 1.65rem;
  padding: 0.75rem 1.65rem;
  border-radius: 14px;
}

.theater-fullscreen .cand-btn {
  font-size: 2.25rem;
  padding: 0.95rem 1.6rem;
  border-radius: 16px;
}

/* STAGE 3: 완성 문장 & 소리 블록 대왕 폰트 */
.theater-fullscreen .kf-glass-block {
  min-height: 120px;
  padding: 0.95rem 1.6rem;
  border-radius: 18px;
  gap: 0.6rem;
}

.theater-fullscreen .gblk-badge {
  font-size: 1.45rem;
}

.theater-fullscreen .gblk-en {
  font-size: 2.35rem;
  line-height: 1.25;
}

.theater-fullscreen .kf-sentence-banner {
  padding: 1.2rem 2.5rem;
  border-radius: 20px;
}

.theater-fullscreen .kf-main-en {
  font-size: 3.35rem;
  gap: 0.9rem;
}

.theater-fullscreen .play-hint-icon {
  font-size: 2.1rem;
}

.theater-fullscreen .kf-meta-ko {
  font-size: 1.65rem;
}

/* 아웃트로 복습 그리드 대형화 (와이드 4열 x 2행 전면 배치) */
.theater-fullscreen .kf-outro-content {
  width: min(96%, 1720px);
  padding: 1.2rem 2.5rem;
}

.theater-fullscreen .outro-badge {
  font-size: 1.55rem;
  margin-bottom: 0.5rem;
}

.theater-fullscreen .outro-title {
  font-size: 2.85rem !important;
  line-height: 1.35 !important;
  margin: 0.4rem 0 1.4rem !important;
}

.theater-fullscreen .kf-review-grid {
  gap: 1.1rem;
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 1.6rem;
}

.theater-fullscreen .kf-review-item {
  padding: 1rem 1.35rem;
  border-radius: 16px;
}

.theater-fullscreen .rev-num {
  font-size: 1.45rem;
  min-width: 2.2rem;
}

.theater-fullscreen .rev-en {
  font-size: 1.45rem;
  line-height: 1.32;
}

.theater-fullscreen .rev-ko {
  font-size: 1.15rem;
}


.kf-mic-chk {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--vp-c-text-1);
  display: flex;
  align-items: center;
  gap: 0.3rem;
  cursor: pointer;
  background: var(--vp-c-bg-soft);
  padding: 0.35rem 0.65rem;
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
}

.srec-options {
  width: 100%;
  margin-top: 0.35rem;
}

.kf-rec-mic-label {
  font-size: 0.84rem;
  color: var(--vp-c-text-1);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
}

/* ===================================================
   🔴 스튜디오 원클릭 자체 비디오 녹화기 스타일
   =================================================== */
.kf-rec-toggle-btn {
  background: #ef4444;
  border-color: #ef4444;
  color: #fff !important;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.kf-rec-toggle-btn.is-rec-active {
  background: #b91c1c;
  animation: recPulse 1.2s infinite;
}

.rem-btn.rem-rec {
  background: #ef4444;
}

.rem-btn.rem-rec.recording {
  background: #b91c1c;
  animation: recPulse 1.2s infinite;
}

.kf-record-countdown-overlay {
  position: absolute;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(10px);
}
.rc-box {
  text-align: center;
}
.rc-badge {
  display: inline-block;
  padding: 0.5rem 1.4rem;
  border-radius: 9999px;
  background: rgba(239, 68, 68, 0.25);
  border: 1px solid rgba(239, 68, 68, 0.6);
  color: #fca5a5;
  font-size: 1.1rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  margin-bottom: 1.25rem;
}
.rc-number {
  font-size: 9rem;
  font-weight: 900;
  color: #ffffff;
  line-height: 1;
  text-shadow: 0 0 50px rgba(239, 68, 68, 0.8);
  animation: kfPop 0.4s ease-out;
}
.rc-sub {
  margin-top: 1.25rem;
  font-size: 1.35rem;
  font-weight: 600;
  color: #cbd5e1;
}

.kf-rec-status-badge {
  position: absolute;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  background: rgba(220, 38, 38, 0.95);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 900;
  padding: 0.35rem 1rem;
  border-radius: 999px;
  box-shadow: 0 4px 18px rgba(220, 38, 38, 0.6);
  pointer-events: none;
}

.rec-pulsing-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
  animation: recDotBlink 1s infinite alternate;
}

@keyframes recDotBlink {
  from { opacity: 0.3; transform: scale(0.85); }
  to { opacity: 1; transform: scale(1.2); }
}

@keyframes recPulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.kf-studio-recorder-box {
  background: rgba(239, 68, 68, 0.08);
  border: 1.5px solid rgba(239, 68, 68, 0.35);
  border-radius: 14px;
  padding: 0.85rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.srec-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1 1 300px;
}

.srec-title {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.95rem;
  color: #ef4444;
}

.srec-desc {
  margin: 0 !important;
  font-size: 0.8rem;
  color: var(--vp-c-text-2);
  line-height: 1.4;
}

.kf-btn-studio-rec {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border: none;
  color: #fff !important;
  font-size: 0.92rem;
  font-weight: 800;
  padding: 0.65rem 1.35rem;
  border-radius: 10px;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(239, 68, 68, 0.35);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.kf-btn-studio-rec:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.5);
}

.kf-btn-studio-rec.is-rec-active {
  background: #b91c1c;
  animation: recPulse 1.2s infinite;
}

</style>
