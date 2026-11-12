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
                  <span class="combo-block-pill c-core">{{ getComboCorePart(combo) }}</span>
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
            <strong>Video Title:</strong>
            <code>{{ currentEpisode.ytTitle }}</code>
          </div>
          <div class="kf-meta-row">
            <strong>Thumbnail Text:</strong>
            <code>{{ currentEpisode.thumbnailText }}</code>
          </div>
          <div class="kf-meta-row">
            <strong>Thumbnail Image:</strong>
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
          <div class="kf-meta-row">
            <strong>Pinned Comment:</strong>
            <code>🍲 SoundBlock K-Cooking Challenge! Which step was your favorite? Let us know below! 👇</code>
          </div>
          <div class="kf-meta-row">
            <strong>Video Tags (500 chars):</strong>
            <code>{{ getEpisodeTags(currentEpisode) }}</code>
          </div>
          <div class="kf-meta-row">
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

  try {
    // 1) 화면 및 탭 내부 오디오 캡처 (Chrome 최신 preferCurrentTab 옵션 탑재)
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
    countdownToRecord.value = null

    // 💡 3) 풀스크린이 완벽히 안착된 상태에서 실제 레코더 시작! (어색한 창선택 화면 0% 녹화)
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

function getEpisodeTags(ep: CookingEpisode): string {
  const dish = ep.shortTitle.replace(/^[^\s]+\s*/, '')
  const specificTagsMap: Record<string, string[]> = {
    'kimchi-stew': ['kimchi stew', 'how to make kimchi stew', 'authentic kimchi stew recipe', 'kimchi jjigae recipe', 'kimchi soup in english'],
    'kimchi-fried-rice': ['kimchi fried rice', 'easy kimchi fried rice', 'how to make kimchi fried rice', '5 minute kimchi fried rice', 'bokkeumbap recipe'],
    'korean-ramen': ['korean ramen', 'korean ramyeon', 'how to cook korean ramen', 'how to cook shin ramen', 'k-ramen recipe'],
    'bulgogi-bbq': ['korean bulgogi', 'bulgogi beef recipe', 'korean bbq beef', 'how to make bulgogi', 'ssam lettuce wrap'],
    'tteokbokki': ['tteokbokki recipe', 'how to make tteokbokki', 'spicy tteokbokki', 'cheese tteokbokki', 'korean rice cakes in english'],
    'korean-pancake': ['korean pancake recipe', 'crispy pajeon', 'haemul pajeon recipe', 'how to make korean pancake', 'kimchijeon recipe'],
    'japchae': ['japchae recipe', 'how to make japchae', 'korean glass noodles recipe', 'traditional japchae', 'sweet potato noodles']
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

async function copyEpisodeScript() {
  const ep = currentEpisode.value
  const dishName = ep.shortTitle.replace(/^[^\s]+\s*/, '')
  const lines = [
    `=== 1. VIDEO TITLE ===`,
    ep.ytTitle,
    '',
    `=== 2. THUMBNAIL TEXT ===`,
    ep.thumbnailText,
    '',
    `=== 3. PINNED COMMENT (Copy & Pin in YouTube comments) ===`,
    `🍲 SoundBlock K-Cooking Challenge!`,
    `Which step was your favorite? Try speaking the full sentence out loud in one breath!`,
    `👇 Share your favorite sound block in the comments below!`,
    '',
    `=== 4. DESCRIPTION & TIMESTAMPS ===`,
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
    `04:15 Full Review · Master all sound blocks!`,
    '',
    `🔔 Subscribe & Like to cook more delicious K-food in easy English!`,
    `Official Channel · YouTube @SoundBlockKCooking`,
    '',
    `#SoundBlockKCooking #KFood #${dishName.replace(/\s+/g, '')} #LearnEnglish #EnglishSpeaking #EasyEnglish #KoreanCooking #CookingEnglish`,
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
  gap: 1.6rem;
}

.theater-fullscreen .combo-block-pill {
  font-size: 2.85rem;
  padding: 0.75rem 2rem;
  border-radius: 18px;
  border-width: 3px;
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
