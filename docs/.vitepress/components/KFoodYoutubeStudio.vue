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
            :src="withBase('/images/kfood/ep1-thumb.jpg')"
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
            <!-- 1) 깔끔하게 통합된 단일 목표 문장 헤더 -->
            <div class="kf-mission-banner" @click="playMissionAudio">
              <span class="m-badge">🎯 MISSION</span>
              <span class="m-text">Assemble: <strong>"{{ currentScene.fullEn }}"</strong></span>
              <span class="m-listen">🔊 Listen</span>
            </div>

            <!-- 2) 자석 결합 타겟 슬롯 (도톰한 레고 마그넷 블록) -->
            <div class="kf-snap-target-row" :class="{ snapped: isSnapped }">
              <div
                class="snap-slot slot-bb"
                :class="{ 'is-filled': isSnapped || pickedBb }"
                title="Click to reset"
                @click="clearPicked('bb')"
              >
                <span class="slot-badge">① 1st Block</span>
                <span class="slot-word">{{ isSnapped ? currentScene.blocks[0].en : (pickedBb || '?') }}</span>
              </div>
              <span class="snap-plus">+</span>
              <div
                class="snap-slot slot-core"
                :class="{ 'is-filled': isSnapped || pickedCore }"
                title="Click to reset"
                @click="clearPicked('core')"
              >
                <span class="slot-badge">② Core Action</span>
                <span class="slot-word">{{ isSnapped ? currentScene.blocks[1].en : (pickedCore || '?') }}</span>
              </div>
              <span class="snap-plus">+</span>
              <div class="snap-slot slot-db" :class="{ 'is-filled': isSnapped }">
                <span class="slot-badge">③ Detail</span>
                <span class="slot-word">{{ isSnapped ? currentScene.blocks[2].en : '...' }}</span>
              </div>
            </div>

            <!-- 3) 후보 블록 풀 (카테고리별 시원하고 큼직한 레고 블록 선택 패널) -->
            <div class="kf-candidate-pool">
              <!-- 행 1: 1st Starter Block 후보 -->
              <div class="cand-row">
                <div class="cand-badge-col">
                  <span class="cand-sec-badge badge-bb">① 1st Block</span>
                </div>
                <div class="cand-items">
                  <button
                    v-for="(opt, oIdx) in currentScene.quizPool.bbCandidates"
                    :key="oIdx"
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
              <div class="cand-row">
                <div class="cand-badge-col">
                  <span class="cand-sec-badge badge-core">② Core Action</span>
                </div>
                <div class="cand-items">
                  <button
                    v-for="(opt, oIdx) in currentScene.quizPool.coreCandidates"
                    :key="oIdx"
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

            <!-- 4) 합체 완료 문장 배너 (겹침 0% · 시원하고 아름다운 완성 문장 단일 출력) -->
            <div v-if="isSnapped" class="kf-quiz-complete-bar" @click="speakSceneSentence(1.0)">
              <div class="qc-en">✨ PERFECT SNAP! 🧲 <strong>{{ currentScene.fullEn }}</strong></div>
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
          <span>📋 <strong>{{ currentEpisode.title }}</strong> · 유튜브 업로드용 제목·설명·태그·자막 패키지</span>
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
            <strong>Description &amp; Tags:</strong>
            <button type="button" class="kf-ctrl-btn-sm" @click="copyEpisodeScript">
              {{ copySuccess ? '✅ Copied!' : '📄 Copy Script & Tags' }}
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
  introNarrationKo: string
  outroNarrationKo: string
  scenes: CookingScene[]
}

const studioRoot = ref<HTMLElement | null>(null)
const aspectRatio = ref<'16:9' | '9:16'>('16:9')
const isCleanMode = ref(false)
const isFullscreenMode = ref(false)
const showFloatingControls = ref(true)

// 글자 크기 모드 (모바일 사용자 배려): 'large'를 기본으로 설정하여 스마트폰에서도 시원시원하게 보임
const fontScale = ref<'normal' | 'large' | 'huge'>('large')

const fontScaleLabel = computed(() => {
  if (fontScale.value === 'large') return '📱 대형(모바일 추천)'
  if (fontScale.value === 'huge') return '👑 초대형(왕글씨)'
  return '보통(PC)'
})

function cycleFontScale() {
  if (fontScale.value === 'large') fontScale.value = 'huge'
  else if (fontScale.value === 'huge') fontScale.value = 'normal'
  else fontScale.value = 'large'
}

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

    // 💡 2) 5초 카운트다운 (전체화면이 완전하게 자리잡고 사용자가 준비할 수 있는 여유 시간 제공)
    countdownToRecord.value = 5
    playTransitionChime()

    for (let c = 5; c >= 1; c--) {
      countdownToRecord.value = c
      playTone(440 + (5 - c) * 70, 120, 'sine', 0.12, 0)
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
const slideCursor = ref(0)

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
    ytTitle: '[소리블록 요리영어 #1] 중학교 단어로 김치찌개 끓이기 🍲 | How to Make Kimchi Stew in Easy English',
    thumbnailText: '"I\'m gonna make Kimchi stew!" → [I\'m gonna] + [make Kimchi stew]',
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
    title: '5분 완성 김치볶음밥 & 계란프라이 만들기 (Kimchi Fried Rice)',
    ytTitle: '[소리블록 요리영어 #2] 5분 완성 김치볶음밥 영어로 설명하기 🍳 | Kimchi Fried Rice in Easy English',
    thumbnailText: '"계란프라이 올릴게!" → [I\'ll] + [put a fried egg] + [on top]',
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
    shortTitle: '3화 · K-라면 끓이기',
    title: '영어로 K-라면 꼬들꼬들하게 끓이기 (Korean Instant Noodles)',
    ytTitle: '[소리블록 요리영어 #3] 외국인 친구에게 K-라면 끓이는 법 영어로 말하기 🍜 | How to Cook Korean Ramen',
    thumbnailText: '"스프부터 넣어야 해!" → [You have to] + [put the soup base first]',
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
    shortTitle: '4화 · 불고기 & 쌈',
    title: '영어로 불고기 재우기 & 상추쌈 싸 먹는 법 설명하기 (Bulgogi)',
    ytTitle: '[소리블록 요리영어 #4] 불고기 양념 재우기부터 상추쌈(Ssam)까지 영어로! 🥩 | Korean Bulgogi',
    thumbnailText: '"상추에 싸 드세요!" → [You have to] + [wrap it in lettuce]',
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

function setStage(stage: 'swap' | 'quiz' | 'sentence') {
  activeStage.value = stage
  if (stage === 'quiz') {
    isSnapped.value = false
    pickedBb.value = null
    pickedCore.value = null
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

  // 1) 인트로 슬라이드일 때
  if (slideCursor.value === -1) {
    if (enableKoreanCoachVoice.value) {
      const ok = await playMp3Async(`/audio/kfood/${epId}-intro-ko.mp3`, 1.0)
      if (!ok) await speakAsync(currentEpisode.value.introNarrationEn || 'Welcome to SoundBlock K-Cooking!', 'en-US', 1.0)
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
}

function startEpisodeFromBeginning() {
  slideCursor.value = -1
  toggleAutoShow()
}

function selectEpisode(id: string) {
  stopAutoShow()
  currentEpId.value = id
  slideCursor.value = 0
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

async function copyEpisodeScript() {
  const ep = currentEpisode.value
  const lines = [
    `[제목] ${ep.ytTitle}`,
    `[썸네일 문구] ${ep.thumbnailText}`,
    '',
    '--- [타임스탬프 & 소리 블록 대본] ---',
    ...ep.scenes.map(
      (s, i) =>
        `0${i}:00 ${s.stepTitle}
- EN: ${s.fullEn}
- 블록: ${s.blocks.map((b) => `[${b.en}]`).join(' + ')}
- 교체: ${s.combos.map((c) => c.fullEn).join(' / ')}
- 뜻: ${s.fullKo}
`
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
  align-items: center;
  gap: 0.55rem;
  padding: 0.6rem 0.8rem;
  background: rgba(15, 23, 42, 0.85);
  border-radius: 12px;
  border: 2px dashed rgba(255, 255, 255, 0.25);
  transition: all 0.3s ease;
}

.kf-snap-target-row.snapped {
  border-style: solid;
  border-color: #fde047;
  background: rgba(30, 41, 59, 0.95);
  box-shadow: 0 0 20px rgba(250, 204, 21, 0.35);
}

.snap-slot {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  transition: all 0.25s ease;
}

.slot-bb.is-filled {
  background: #2563eb;
}
.slot-core.is-filled {
  background: #059669;
}
.slot-db.is-filled {
  background: #d97706;
}

.slot-badge {
  font-size: 1.05rem;
  font-weight: 800;
  opacity: 0.95;
  letter-spacing: 0.05em;
}

.slot-word {
  font-size: 2.15rem;
  font-weight: 900;
  color: #fff;
  letter-spacing: -0.01em;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
}

.snap-plus {
  font-weight: 900;
  color: #fde047;
  font-size: 1.2rem;
}

.kf-candidate-pool {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.cand-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.cand-label {
  font-size: 1.25rem;
  font-weight: 900;
  color: #e2e8f0;
  min-width: 150px;
}

.cand-items {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.cand-btn {
  padding: 0.65rem 1.45rem;
  border-radius: 14px;
  font-size: 1.65rem;
  font-weight: 900;
  border: 2px solid rgba(255, 255, 255, 0.35);
  background: rgba(15, 23, 42, 0.92);
  color: #fff;
  cursor: pointer;
  transition: all 0.18s ease;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
}

.cand-bb:hover {
  border-color: #60a5fa;
  background: rgba(37, 99, 235, 0.3);
}

.cand-core:hover {
  border-color: #34d399;
  background: rgba(5, 150, 105, 0.3);
}

.cand-btn.selected {
  border-color: #fde047 !important;
  box-shadow: 0 0 14px rgba(250, 204, 21, 0.5);
  transform: translateY(-2px) scale(1.04);
}
.cand-bb.selected {
  background: #2563eb !important;
  color: #fff !important;
}
.cand-core.selected {
  background: #059669 !important;
  color: #fff !important;
}

.cand-btn.correct {
  border-color: #fde047 !important;
  background: #facc15 !important;
  color: #0f172a !important;
  transform: scale(1.05);
}

.kf-quiz-complete-bar {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.38) 0%, rgba(5, 150, 105, 0.48) 100%);
  backdrop-filter: blur(14px);
  border: 2px solid #34d399;
  border-radius: 14px;
  padding: 0.85rem 1.6rem;
  cursor: pointer;
  box-shadow: 0 0 25px rgba(52, 211, 153, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  animation: kfPop 0.3s ease-out;
}

.qc-en {
  font-size: 1.85rem;
  font-weight: 900;
  color: #fff;
  line-height: 1.35;
}

.qc-en strong {
  color: #fde047;
  text-shadow: 0 0 16px rgba(253, 224, 71, 0.6);
}

/* ---------------------------------------------------
   STAGE 3 · 완성 문장 & 소리 블록 표준 스타일
   --------------------------------------------------- */
.kf-blocks-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.kf-glass-block {
  flex: 1 1 140px;
  padding: 0.55rem 0.95rem;
  border-radius: 12px;
  backdrop-filter: blur(12px);
  cursor: pointer;
  border: 2px solid transparent;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.kf-glass-block.bb {
  background: rgba(37, 99, 235, 0.5);
  border-color: rgba(96, 165, 250, 0.8);
}

.kf-glass-block.core {
  background: rgba(5, 150, 105, 0.5);
  border-color: rgba(52, 211, 153, 0.8);
}

.kf-glass-block.db {
  background: rgba(217, 119, 6, 0.5);
  border-color: rgba(251, 191, 36, 0.8);
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
  font-size: 0.72rem;
  font-weight: 800;
  color: #e2e8f0;
}

.gblk-pron {
  font-size: 0.82rem;
  font-weight: 700;
  color: #fef08a;
}

.gblk-en {
  font-size: 1.25rem;
  font-weight: 900;
  color: #fff;
  letter-spacing: -0.01em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
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

.kf-intro-content,
.kf-outro-content {
  position: relative;
  z-index: 10;
  margin: auto;
  padding: 1.5rem;
  text-align: center;
  color: #fff;
  width: min(92%, 760px);
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
  font-size: 1.15rem;
  font-weight: 800;
  color: #34d399;
  letter-spacing: 0.06em;
}

.outro-title {
  margin: 0.35rem 0 1.25rem !important;
  font-size: 2.15rem !important;
  font-weight: 900;
  color: #fff !important;
  border: none !important;
}

.kf-review-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 0.75rem;
  text-align: left;
  margin-bottom: 1.25rem;
}

.kf-review-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.75rem 1.25rem;
  border-radius: 14px;
  background: rgba(30, 41, 59, 0.92);
  border: 2px solid rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.kf-review-item:hover {
  border-color: #38bdf8;
  background: rgba(14, 165, 233, 0.25);
  transform: translateY(-2px);
}

.rev-num {
  font-size: 1.25rem;
  font-weight: 900;
  color: #38bdf8;
  min-width: 2.4rem;
}

.rev-en {
  font-size: 1.45rem;
  font-weight: 900;
  color: #fff;
  line-height: 1.35;
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

  .cand-group {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .cand-label {
    font-size: 0.75rem;
    min-width: auto;
  }

  .cand-items {
    width: 100%;
    gap: 0.3rem;
  }

  .cand-btn {
    font-size: 0.88rem;
    padding: 0.3rem 0.65rem;
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

.theater-fullscreen .slot-badge {
  font-size: 1.35rem;
}

.theater-fullscreen .slot-word {
  font-size: 3.1rem;
}

.theater-fullscreen .cand-row {
  padding: 0.95rem 1.5rem;
  border-radius: 20px;
  gap: 1.5rem;
}

.theater-fullscreen .cand-sec-badge {
  font-size: 1.85rem;
  padding: 0.85rem 1.85rem;
  border-radius: 16px;
}

.theater-fullscreen .cand-btn {
  font-size: 2.65rem;
  padding: 1.15rem 2.0rem;
  border-radius: 18px;
}

.theater-fullscreen .qc-en {
  font-size: 3.15rem;
}

/* STAGE 3: 완성 문장 & 소리 블록 대왕 폰트 */
.theater-fullscreen .kf-glass-block {
  padding: 1rem 1.8rem;
  border-radius: 20px;
}

.theater-fullscreen .gblk-badge {
  font-size: 1.25rem;
}

.theater-fullscreen .gblk-en {
  font-size: 2.75rem;
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

/* 아웃트로 복습 그리드 대형화 */
.theater-fullscreen .outro-title {
  font-size: 2.2rem !important;
}

.theater-fullscreen .outro-badge {
  font-size: 1.65rem;
}

.theater-fullscreen .outro-title {
  font-size: 3.0rem !important;
}

.theater-fullscreen .kf-review-grid {
  gap: 1.1rem;
  grid-template-columns: repeat(2, 1fr);
  margin-bottom: 1.8rem;
}

.theater-fullscreen .kf-review-item {
  padding: 1.15rem 1.85rem;
  border-radius: 18px;
}

.theater-fullscreen .rev-num {
  font-size: 1.85rem;
  min-width: 3.2rem;
}

.theater-fullscreen .rev-en {
  font-size: 2.15rem;
  line-height: 1.3;
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
