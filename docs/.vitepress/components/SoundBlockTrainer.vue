<template>
  <div class="sb-trainer" @click.stop>
    <!-- 상단 헤더 & 모드 전환 탭 -->
    <div class="sb-header">
      <div class="sb-header-top">
        <span class="sb-badge">INTERACTIVE SOUND BLOCK TRAINER</span>
        <h3 class="sb-title">🧱 소리 블록(Sound Block) 0.1초 조립 &amp; 스피킹 훈련기</h3>
        <p class="sb-subtitle">
          단어 하나씩 조합하지 마세요! <strong>① 시작 블록(Day 1~5)</strong> + <strong>② 코어 블록(Day 6~10: do·make·get·take·have)</strong> + <strong>③ 디테일 블록</strong>을 레고처럼 조립해 입으로 뱉는 연습을 해 보세요.
        </p>
      </div>

      <div class="sb-tabs">
        <button
          type="button"
          class="sb-tab"
          :class="{ active: activeTab === 'builder' }"
          @click="activeTab = 'builder'"
        >
          🧱 1. 레고 블록 자유 조립기
        </button>
        <button
          type="button"
          class="sb-tab"
          :class="{ active: activeTab === 'puzzle' }"
          @click="activeTab = 'puzzle'"
        >
          🧩 2. 블록 조립 퀴즈 ({{ puzzleIndex + 1 }}/{{ filteredDrills.length }})
        </button>
        <button
          type="button"
          class="sb-tab"
          :class="{ active: activeTab === 'reflex' }"
          @click="activeTab = 'reflex'"
        >
          ⚡ 3. 0.1초 순발력 입트임 드릴
        </button>
      </div>
    </div>

    <!-- =====================================================
         TAB 1: 레고 블록 자유 조립기 (Block Lego Builder)
         ===================================================== -->
    <div v-if="activeTab === 'builder'" class="sb-body">
      <!-- 조립 결과 전광판 -->
      <div class="sb-stage">
        <div class="sb-stage-top">
          <span class="sb-stage-label">현재 조립된 소리 블록 ({{ activeChunkCount }} Chunks)</span>
          <div class="sb-stage-actions">
            <button type="button" class="sb-btn sb-btn-random" @click="randomizeBuilder">
              🎲 랜덤 조합 뽑기
            </button>
          </div>
        </div>

        <!-- 시각적 블록 체인 -->
        <div class="sb-lego-chain">
          <div class="sb-lego-piece bb" @click="speakText(selectedBB.en, 0.95)">
            <span class="piece-tag">① 시작 블록 ({{ selectedBB.day }})</span>
            <strong class="piece-en">{{ selectedBB.en }}</strong>
            <span class="piece-pron">[{{ selectedBB.pron }}]</span>
            <span class="piece-ko">{{ selectedBB.ko }}</span>
          </div>

          <span class="sb-plus">+</span>

          <div class="sb-lego-piece core" @click="speakText(adaptedCore.en, 0.95)">
            <span class="piece-tag">② 코어 블록 ({{ selectedCore.category }})</span>
            <strong class="piece-en">{{ adaptedCore.en }}</strong>
            <span class="piece-pron">[{{ adaptedCore.pron }}]</span>
            <span class="piece-ko">{{ adaptedCore.ko }}</span>
          </div>

          <template v-if="selectedDB.id !== 'none'">
            <span class="sb-plus">+</span>
            <div class="sb-lego-piece db" @click="speakText(adaptedDB.en, 0.95)">
              <span class="piece-tag">③ 디테일 블록</span>
              <strong class="piece-en">{{ adaptedDB.en }}</strong>
              <span class="piece-pron">[{{ adaptedDB.pron }}]</span>
              <span class="piece-ko">{{ adaptedDB.ko }}</span>
            </div>
          </template>
        </div>

        <!-- 완성 문장 & 발음 가이드 -->
        <div class="sb-assembled-box">
          <div class="sb-assembled-en">
            {{ assembledSentence.en }}
          </div>
          <div class="sb-assembled-pron">
            🗣️ 소리 블록 리듬: <strong>{{ assembledSentence.pron }}</strong>
          </div>
          <div class="sb-assembled-ko">
            💡 자연스러운 뜻: <strong>{{ assembledSentence.ko }}</strong>
          </div>

          <!-- 오디오 컨트롤 바 -->
          <div class="sb-audio-bar">
            <button type="button" class="sb-btn sb-btn-primary" @click="speakText(assembledSentence.en, 1.0)">
              🔊 정상 속도 듣기 (1.0x)
            </button>
            <button type="button" class="sb-btn" @click="speakText(assembledSentence.en, 0.78)">
              🐢 천천히 듣기 (0.8x)
            </button>
            <button type="button" class="sb-btn" @click="speakText(assembledSentence.en, 1.15)">
              ⚡ 빠르게 듣기 (1.15x)
            </button>
            <button type="button" class="sb-btn sb-btn-step" @click="speakStepByStep">
              🔁 블록별 끊어→이어 듣기
            </button>
          </div>
        </div>

        <!-- 소리 튜닝 핵심 코칭 -->
        <div class="sb-coaching-grid">
          <div class="sb-coaching-item">
            <span class="coach-badge bb-badge">{{ selectedBB.day }} 시작 블록 포인트</span>
            <p>{{ selectedBB.tip }}</p>
          </div>
          <div class="sb-coaching-item">
            <span class="coach-badge core-badge">{{ selectedCore.category }} 코어 블록 포인트</span>
            <p>{{ selectedCore.tip }}</p>
          </div>
        </div>
      </div>

      <!-- 블록 선택 팔레트 -->
      <div class="sb-palette-section">
        <!-- 1. 시작 블록 선택 -->
        <div class="sb-palette-box">
          <div class="sb-palette-header">
            <h4>① 시작 블록 (Beginning Block · Day 1~5) 선택</h4>
            <div class="sb-filter-pills">
              <button
                v-for="f in bbFilters"
                :key="f.id"
                type="button"
                class="sb-pill"
                :class="{ active: bbFilter === f.id }"
                @click="bbFilter = f.id"
              >
                {{ f.label }}
              </button>
            </div>
          </div>
          <div class="sb-chip-grid">
            <button
              v-for="bb in filteredBBs"
              :key="bb.id"
              type="button"
              class="sb-chip bb-chip"
              :class="{ selected: selectedBB.id === bb.id }"
              @click="selectBB(bb)"
            >
              <span class="chip-en">{{ bb.en }}</span>
              <span class="chip-sub">{{ bb.ko }} · <em>{{ bb.pron }}</em></span>
            </button>
          </div>
        </div>

        <!-- 2. 코어 블록 선택 -->
        <div class="sb-palette-box">
          <div class="sb-palette-header">
            <h4>② 코어 블록 (Core Block · Day 6~10 5대 동사 &amp; 필수 표현) 선택</h4>
            <div class="sb-filter-pills">
              <button
                v-for="f in coreFilters"
                :key="f.id"
                type="button"
                class="sb-pill"
                :class="{ active: coreFilter === f.id }"
                @click="coreFilter = f.id"
              >
                {{ f.label }}
              </button>
            </div>
          </div>
          <div class="sb-chip-grid">
            <button
              v-for="core in filteredCores"
              :key="core.id"
              type="button"
              class="sb-chip core-chip"
              :class="{ selected: selectedCore.id === core.id }"
              @click="selectCore(core)"
            >
              <span class="chip-verb-tag">{{ core.verb }}</span>
              <span class="chip-en">{{ core.en }}</span>
              <span class="chip-sub">{{ core.ko }}</span>
            </button>
          </div>
        </div>

        <!-- 3. 디테일 블록 선택 -->
        <div class="sb-palette-box">
          <div class="sb-palette-header">
            <h4>③ 디테일 블록 (Detail Block · 선택 부착)</h4>
          </div>
          <div class="sb-chip-grid db-grid">
            <button
              v-for="db in detailBlocks"
              :key="db.id"
              type="button"
              class="sb-chip db-chip"
              :class="{ selected: selectedDB.id === db.id }"
              @click="selectDB(db)"
            >
              <span class="chip-en">{{ db.id === 'none' ? '(붙이지 않음)' : db.en }}</span>
              <span v-if="db.id !== 'none'" class="chip-sub">{{ db.ko }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- =====================================================
         TAB 2: 실전 블록 조립 퀴즈 (Block Assembly Puzzle)
         ===================================================== -->
    <div v-else-if="activeTab === 'puzzle'" class="sb-body">
      <div class="sb-drill-toolbar">
        <div class="sb-filter-pills">
          <button
            v-for="f in drillFilters"
            :key="f.id"
            type="button"
            class="sb-pill"
            :class="{ active: drillFilter === f.id }"
            @click="setDrillFilter(f.id)"
          >
            {{ f.label }}
          </button>
        </div>
        <div class="sb-drill-nav">
          <button type="button" class="sb-btn-sm" @click="shuffleDrills">🔀 순서 섞기</button>
          <span class="sb-score-badge">정답 완료: {{ solvedCount }} / {{ filteredDrills.length }}</span>
        </div>
      </div>

      <div v-if="currentPuzzle" class="sb-puzzle-card">
        <div class="sb-puzzle-meta">
          <span class="sb-day-tag">{{ currentPuzzle.dayLabel }}</span>
          <span class="sb-chunk-tag">{{ currentPuzzle.chunks.length }}개 소리 블록 조립</span>
        </div>

        <div class="sb-prompt-ko">
          “{{ currentPuzzle.ko }}”
        </div>
        <p class="sb-prompt-guide">
          아래 블록 조각들을 <strong>순서대로 클릭</strong>해서 위 한국어 문장을 영어로 조립해 보세요!
        </p>

        <!-- 사용자가 조립 중인 슬롯 -->
        <div class="sb-answer-slots">
          <div
            v-for="(targetChunk, idx) in currentPuzzle.chunks"
            :key="idx"
            class="sb-slot"
            :class="{
              filled: Boolean(userSelectedChunks[idx]),
              correct: puzzleSolved,
              wrong: puzzleWrong
            }"
            @click="removeChunkAt(idx)"
          >
            <span class="slot-num">블록 {{ idx + 1 }}</span>
            <strong v-if="userSelectedChunks[idx]" class="slot-text">
              {{ userSelectedChunks[idx] }}
            </strong>
            <span v-else class="slot-placeholder">여기에 {{ idx + 1 }}번째 블록 선택</span>
          </div>
        </div>

        <!-- 선택 가능한 블록 풀 -->
        <div class="sb-options-pool">
          <button
            v-for="(opt, idx) in puzzleOptions"
            :key="idx + '-' + opt"
            type="button"
            class="sb-option-chip"
            :disabled="userSelectedChunks.includes(opt) || puzzleSolved"
            @click="pickPuzzleOption(opt)"
          >
            {{ opt }}
          </button>
        </div>

        <!-- 피드백 영역 -->
        <div v-if="puzzleWrong" class="sb-feedback wrong">
          ❌ 블록 순서나 표현이 다릅니다! 슬롯을 클릭해 취소하거나 <strong>다시 놓기</strong>를 눌러 보세요.
          <button type="button" class="sb-btn-sm" @click="resetCurrentPuzzle">↺ 다시 놓기</button>
        </div>

        <div v-if="puzzleSolved" class="sb-feedback correct">
          <div class="sb-solved-title">🎉 정답입니다! 소리 블록 하나로 이어서 읽어 보세요:</div>
          <div class="sb-solved-en">{{ currentPuzzle.en }}</div>
          <div class="sb-solved-pron">🗣️ 발음·리듬: <strong>{{ currentPuzzle.pron }}</strong></div>
          <div class="sb-solved-tip">💡 {{ currentPuzzle.tip }}</div>
          <div class="sb-audio-bar">
            <button type="button" class="sb-btn sb-btn-primary" @click="speakText(currentPuzzle.en, 1.0)">
              🔊 다시 듣기 (1.0x)
            </button>
            <button type="button" class="sb-btn" @click="speakText(currentPuzzle.en, 0.8)">
              🐢 천천히 (0.8x)
            </button>
            <button type="button" class="sb-btn sb-btn-step" @click="nextPuzzle">
              다음 문제로 이동 →
            </button>
          </div>
        </div>

        <!-- 하단 네비게이션 -->
        <div class="sb-card-footer">
          <button type="button" class="sb-btn" @click="prevPuzzle">← 이전 문장</button>
          <button type="button" class="sb-btn" @click="revealPuzzleAnswer">💡 정답 바로 보기</button>
          <button type="button" class="sb-btn" @click="nextPuzzle">다음 문장 →</button>
        </div>
      </div>
    </div>

    <!-- =====================================================
         TAB 3: 0.1초 순발력 스피킹 드릴 (Reflex Drill)
         ===================================================== -->
    <div v-else-if="activeTab === 'reflex'" class="sb-body">
      <div class="sb-drill-toolbar">
        <div class="sb-filter-pills">
          <button
            v-for="f in drillFilters"
            :key="f.id"
            type="button"
            class="sb-pill"
            :class="{ active: drillFilter === f.id }"
            @click="setDrillFilter(f.id)"
          >
            {{ f.label }}
          </button>
        </div>
        <div class="sb-reflex-settings">
          <label class="sb-toggle-label">
            <input v-model="autoPlayTTS" type="checkbox" />
            정답 공개 시 음성 자동 재생
          </label>
          <span class="sb-score-badge">마스터: {{ masteredIds.length }} / {{ drills.length }}</span>
        </div>
      </div>

      <div v-if="currentReflex" class="sb-reflex-card">
        <div class="sb-puzzle-meta">
          <span class="sb-day-tag">{{ currentReflex.dayLabel }}</span>
          <span v-if="masteredIds.includes(currentReflex.id)" class="sb-mastered-tag">✅ 마스터 완료</span>
        </div>

        <div class="sb-prompt-ko">
          “{{ currentReflex.ko }}”
        </div>

        <!-- 타이머 게이지 -->
        <div class="sb-timer-wrap">
          <div class="sb-timer-bar">
            <div
              class="sb-timer-fill"
              :style="{ width: reflexProgress + '%' }"
              :class="{ urgent: reflexProgress > 70 }"
            ></div>
          </div>
          <div class="sb-timer-actions">
            <button type="button" class="sb-btn sb-btn-random" @click="startThreeSecChallenge">
              ⏱️ 3초 순발력 타이머 시작!
            </button>
            <button
              type="button"
              class="sb-btn"
              @click="showBBHint = !showBBHint"
            >
              {{ showBBHint ? '🙈 힌트 숨기기' : '💡 1단계: 시작 블록만 힌트 보기 (0.1초 발사!)' }}
            </button>
          </div>
        </div>

        <!-- 1단계: 시작 블록 힌트 -->
        <div v-if="showBBHint && !showReflexAnswer" class="sb-bb-hint-box">
          🔥 일단 입 밖으로 먼저 뱉으세요:
          <strong>{{ currentReflex.chunks[0] }} ...</strong>
        </div>

        <!-- 정답 공개 버튼 or 공개된 카드 -->
        <div v-if="!showReflexAnswer" class="sb-reveal-zone">
          <button type="button" class="sb-btn sb-btn-primary sb-btn-large" @click="revealReflex">
            👀 소리 블록 정답 확인 &amp; 원어민 음성 듣기
          </button>
        </div>

        <div v-else class="sb-reflex-answer">
          <!-- 블록 분해 표시 -->
          <div class="sb-reflex-chunks">
            <div
              v-for="(chunk, idx) in currentReflex.chunks"
              :key="idx"
              class="sb-reflex-chunk"
              :class="idx === 0 ? 'bb' : idx === 1 ? 'core' : 'db'"
              @click="speakText(chunk, 0.95)"
            >
              <span class="chunk-role">
                {{ idx === 0 ? '① 시작 블록' : idx === 1 ? '② 코어 블록' : '③ 디테일 블록' }}
              </span>
              <strong>{{ chunk }}</strong>
            </div>
          </div>

          <div class="sb-solved-en">{{ currentReflex.en }}</div>
          <div class="sb-solved-pron">🗣️ 소리 블록 발음: <strong>{{ currentReflex.pron }}</strong></div>
          <div class="sb-solved-tip">💡 {{ currentReflex.tip }}</div>

          <div class="sb-audio-bar">
            <button type="button" class="sb-btn sb-btn-primary" @click="speakText(currentReflex.en, 1.0)">
              🔊 정상 속도 (1.0x)
            </button>
            <button type="button" class="sb-btn" @click="speakText(currentReflex.en, 0.8)">
              🐢 천천히 (0.8x)
            </button>
            <button type="button" class="sb-btn" @click="speakText(currentReflex.en, 1.15)">
              ⚡ 빠르게 (1.15x)
            </button>
            <button
              type="button"
              class="sb-btn"
              :class="{ 'sb-btn-mastered': masteredIds.includes(currentReflex.id) }"
              @click="toggleMastered(currentReflex.id)"
            >
              {{ masteredIds.includes(currentReflex.id) ? '✅ 마스터됨 (해제)' : '⭐ 입에 붙었음 체크!' }}
            </button>
          </div>
        </div>

        <div class="sb-card-footer">
          <button type="button" class="sb-btn" @click="prevReflex">← 이전 문장</button>
          <button type="button" class="sb-btn" @click="randomReflex">🎲 랜덤 문제</button>
          <button type="button" class="sb-btn sb-btn-step" @click="nextReflex">다음 문장 →</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'

interface BeginningBlock {
  id: string
  day: string
  dayGroup: string
  en: string
  ko: string
  pron: string
  subject: 'I' | 'you' | 'we'
  isQuestion: boolean
  tip: string
}

interface CoreBlock {
  id: string
  verb: string
  category: string
  en: string
  ko: string
  pron: string
  tip: string
}

interface DetailBlock {
  id: string
  en: string
  ko: string
  pron: string
}

interface DrillItem {
  id: string
  dayGroup: string
  dayLabel: string
  ko: string
  en: string
  chunks: string[]
  pron: string
  tip: string
}

const activeTab = ref<'builder' | 'puzzle' | 'reflex'>('builder')

// ---------------------------------------------------------
// 1. 시작 블록 데이터 (Day 1 ~ Day 5)
// ---------------------------------------------------------
const bbFilters = [
  { id: 'all', label: '전체 (Day 1~5)' },
  { id: 'day1', label: 'Day 1 · wanna' },
  { id: 'day2', label: 'Day 2 · gonna' },
  { id: 'day3', label: 'Day 3 · have to' },
  { id: 'day4', label: 'Day 4 · I\'ll / won\'t' },
  { id: 'day5', label: 'Day 5 · 과거·습관' }
]
const bbFilter = ref('all')

const beginningBlocks: BeginningBlock[] = [
  // Day 1
  {
    id: 'i-wanna',
    day: 'Day 1',
    dayGroup: 'day1',
    en: 'I wanna',
    ko: '나는 ~하고 싶어',
    pron: '아이 워너',
    subject: 'I',
    isQuestion: false,
    tip: '세 단어(I want to)가 아니라 banana(다-다-다) 리듬의 한 단어(I-wan-na)로 발음하세요!'
  },
  {
    id: 'i-just-wanna',
    day: 'Day 1',
    dayGroup: 'day1',
    en: 'I just wanna',
    ko: '난 그냥 ~하고 싶어',
    pron: '아이 저스 워너',
    subject: 'I',
    isQuestion: false,
    tip: 'just의 t는 받침으로 삼키고 부드럽게 wanna로 연결해 한 덩어리로 뱉습니다.'
  },
  {
    id: 'i-dont-wanna',
    day: 'Day 1',
    dayGroup: 'day1',
    en: "I don't wanna",
    ko: '나는 ~하고 싶지 않아',
    pron: '아러워너 / 아론워너',
    subject: 'I',
    isQuestion: false,
    tip: "don't의 t를 강하게 터뜨리지 않고 모음 사이에서 'ㄹ/ㄴ'처럼 부드럽게 흘려보냅니다."
  },
  {
    id: 'do-you-wanna',
    day: 'Day 1',
    dayGroup: 'day1',
    en: 'Do you wanna',
    ko: '너 ~하고 싶어? / ~할래?',
    pron: '두유워너',
    subject: 'you',
    isQuestion: true,
    tip: 'Do you는 기능어라 힘을 완전히 빼고 wan-에만 강세를 줘서 4음절 한 단어처럼 질문하세요.'
  },
  // Day 2
  {
    id: 'im-gonna',
    day: 'Day 2',
    dayGroup: 'day2',
    en: "I'm gonna",
    ko: '나는 ~할 거야',
    pron: '암거너 / 아머너',
    subject: 'I',
    isQuestion: false,
    tip: 'I am going to에 힘을 빼고 암거너(또는 아머너)로 가볍게 던지며 뒤의 코어 동사를 생각할 시간을 법니다.'
  },
  {
    id: 'im-not-gonna',
    day: 'Day 2',
    dayGroup: 'day2',
    en: "I'm not gonna",
    ko: '나는 ~안 할 거야',
    pron: '암낫거너',
    subject: 'I',
    isQuestion: false,
    tip: '부정어 not의 모음을 살려 강세를 주고 gonna는 약하게 처리합니다.'
  },
  {
    id: 'youre-gonna',
    day: 'Day 2',
    dayGroup: 'day2',
    en: "You're gonna",
    ko: '너는 ~하게 될 거야',
    pron: '유어거너 / 여거너',
    subject: 'you',
    isQuestion: false,
    tip: "You're는 소유격 your와 소리가 똑같습니다. 힘을 빼고 여거너처럼 발음하세요."
  },
  {
    id: 'are-you-gonna',
    day: 'Day 2',
    dayGroup: 'day2',
    en: 'Are you gonna',
    ko: '너 ~할 거야?',
    pron: '아유거너 / 어유거너',
    subject: 'you',
    isQuestion: true,
    tip: 'Are you gonna 전체에 힘을 빼고 뒤에 오는 핵심 동사와 명사를 올려 질문합니다.'
  },
  {
    id: 'were-gonna',
    day: 'Day 2',
    dayGroup: 'day2',
    en: "We're gonna",
    ko: '우리는 ~할 거야',
    pron: '워거너',
    subject: 'we',
    isQuestion: false,
    tip: "We're는 위어(2음절)가 아니라 과거형 동사 were(/wər/)처럼 '워' 한 음절로 발음하면 원어민 소리가 납니다."
  },
  // Day 3
  {
    id: 'i-have-to',
    day: 'Day 3',
    dayGroup: 'day3',
    en: 'I have to',
    ko: '나 ~해야 돼',
    pron: '아이 해프터',
    subject: 'I',
    isQuestion: false,
    tip: '해-브-투(3음절) 금지! have to는 sister와 똑같은 2음절 리듬(해프터)으로, 전체는 banana 리듬을 탑니다.'
  },
  {
    id: 'i-dont-have-to',
    day: 'Day 3',
    dayGroup: 'day3',
    en: "I don't have to",
    ko: '나 굳이 ~할 필요 없어',
    pron: '아러해프터',
    subject: 'I',
    isQuestion: false,
    tip: "'~하면 안 된다'가 아니라 '굳이 ~안 해도 된다(불필요)'는 뜻입니다! don't를 플랩화해 아러해프터로 연결하세요."
  },
  {
    id: 'you-have-to',
    day: 'Day 3',
    dayGroup: 'day3',
    en: 'You have to',
    ko: '너 ~해야 돼',
    pron: '유 해프터',
    subject: 'you',
    isQuestion: false,
    tip: '가운데 have에만 강세를 주어 유-해프-터(banana 리듬)로 발음합니다.'
  },
  {
    id: 'you-dont-have-to',
    day: 'Day 3',
    dayGroup: 'day3',
    en: "You don't have to",
    ko: '너 ~할 필요 없어 (안 해도 돼)',
    pron: '유론해프터 / 유러해프터',
    subject: 'you',
    isQuestion: false,
    tip: "상대방의 부담을 덜어줄 때 0.1초 만에 나오는 필수 블록입니다. don't have to를 론해프터처럼 묶어 주세요."
  },
  // Day 4
  {
    id: 'ill',
    day: 'Day 4',
    dayGroup: 'day4',
    en: "I'll",
    ko: '내가 (지금) ~할게',
    pron: '아을 / 올',
    subject: 'I',
    isQuestion: false,
    tip: '아-일(2음절)이 아니라 혀끝을 천장에 붙인 채 어두운 소리만 내는 Dark L(아을/올) 1음절로 연결합니다.'
  },
  {
    id: 'i-wont',
    day: 'Day 4',
    dayGroup: 'day4',
    en: "I won't",
    ko: '난 절대 ~안 할 거야',
    pron: '아이 워운트',
    subject: 'I',
    isQuestion: false,
    tip: 'want(원트)와 구별하기 위해 입술을 동그랗게 모아 w로 시작하고 오우(oʊ) 이중모음을 확실히 넣어 워운트로 발음합니다!'
  },
  {
    id: 'youll',
    day: 'Day 4',
    dayGroup: 'day4',
    en: "You'll",
    ko: '넌 ~하게 될 거야',
    pron: '열 (/jəl/)',
    subject: 'you',
    isQuestion: false,
    tip: "유-울(2음절) 대신 모음을 툭 떨어뜨리고 Dark L을 붙여 한국어 '열'에 가깝게 한 음절로 지나갑니다."
  },
  // Day 5
  {
    id: 'did-you',
    day: 'Day 5',
    dayGroup: 'day5',
    en: 'Did you',
    ko: '너 ~했어?',
    pron: '디쥬',
    subject: 'you',
    isQuestion: true,
    tip: 'd + y가 만나 구개음화(디쥬)가 일어나며, 기능어이므로 힘을 빼고 뒤 동사원형에 강세를 줍니다.'
  },
  {
    id: 'i-didnt',
    day: 'Day 5',
    dayGroup: 'day5',
    en: "I didn't",
    ko: '나 ~안 했어',
    pron: '아이 디든(트)',
    subject: 'I',
    isQuestion: false,
    tip: "didn't를 정박으로 또박또박 읽지 않고 살짝 엇박으로 디든~ 하고 튕기듯 뒤에 동사원형을 붙입니다."
  },
  {
    id: 'i-used-to',
    day: 'Day 5',
    dayGroup: 'day5',
    en: 'I used to',
    ko: '나 예전엔 ~하곤 했었지',
    pron: '아이 유스터',
    subject: 'I',
    isQuestion: false,
    tip: '사용하다(유즈드)가 아니라 무성음 s 소리(유스터)로 발음하며, I wanna와 똑같은 banana 리듬(다-다-다)입니다!'
  }
]

// ---------------------------------------------------------
// 2. 코어 블록 데이터 (Day 6 ~ Day 10 + 기초 동사)
// ---------------------------------------------------------
const coreFilters = [
  { id: 'all', label: '전체' },
  { id: 'DO', label: 'Day 6 · DO' },
  { id: 'MAKE', label: 'Day 7 · MAKE' },
  { id: 'GET', label: 'Day 8 · GET' },
  { id: 'TAKE', label: 'Day 9 · TAKE' },
  { id: 'HAVE', label: 'Day 10 · HAVE' },
  { id: 'BASIC', label: '일상 기초 동사' }
]
const coreFilter = ref('all')

const coreBlocks: CoreBlock[] = [
  // Day 6: DO
  {
    id: 'do-my-work',
    verb: 'DO',
    category: 'Day 6 · DO',
    en: 'do my work',
    ko: '내 일을 하다',
    pron: '두 마이 워크',
    tip: '정해진 업무·과제를 수행할 때는 do를 씁니다 (상대방이 주어일 때는 do your work / do my work 모두 응용 가능).'
  },
  {
    id: 'do-the-laundry',
    verb: 'DO',
    category: 'Day 6 · DO',
    en: 'do the laundry',
    ko: '빨래를 하다',
    pron: '두 더 런쥬리',
    tip: 'laundry는 라운드리가 아니라 런쥬리! dr이 만나 쥬/츄 소리로 변합니다.'
  },
  {
    id: 'do-the-dishes',
    verb: 'DO',
    category: 'Day 6 · DO',
    en: 'do the dishes',
    ko: '설거지를 하다',
    pron: '두 더 디쉬즈',
    tip: '반복적인 집안일(가사 노동)은 모두 do + the + 집안일 명사 콜로케이션을 씁니다.'
  },
  {
    id: 'do-pilates',
    verb: 'DO',
    category: 'Day 6 · DO',
    en: 'do Pilates',
    ko: '필라테스를 하다',
    pron: '두 펄라리즈',
    tip: 'Pilates는 필라테스가 아니라 2음절에 강세가 오는 펄라리즈(/pɪˈlɑː.tiz/, t 플랩화)로 발음해야 원어민이 알아듣습니다!'
  },
  {
    id: 'do-my-hair',
    verb: 'DO',
    category: 'Day 6 · DO',
    en: 'do my hair',
    ko: '머리를 손질하다(세팅하다)',
    pron: '두 마이 헤어',
    tip: '머리·화장·손톱 등 외모를 깔끔하게 단장하는 행동은 모두 do(do my hair / do my makeup / do my nails)를 씁니다.'
  },
  {
    id: 'do-my-makeup',
    verb: 'DO',
    category: 'Day 6 · DO',
    en: 'do my makeup',
    ko: '화장을 하다',
    pron: '두 마이 메이컵',
    tip: '화장하는 행위 자체를 수행하므로 make가 아니라 do my makeup을 씁니다.'
  },
  // Day 7: MAKE
  {
    id: 'make-my-bed',
    verb: 'MAKE',
    category: 'Day 7 · MAKE',
    en: 'make my bed',
    ko: '이불(침대) 정리를 하다',
    pron: '메익 마이 베드',
    tip: '침대를 제작하는 게 아니라 어질러진 침구를 정돈된 결과물 상태로 만들어 놓는 것이라 make를 씁니다!'
  },
  {
    id: 'make-coffee',
    verb: 'MAKE',
    category: 'Day 7 · MAKE',
    en: 'make some coffee',
    ko: '커피를 타다(내리다)',
    pron: '메익 썸 커피',
    tip: '음식이나 음료를 만들어 결과물을 내는 모든 행동은 make를 씁니다.'
  },
  {
    id: 'make-a-mistake',
    verb: 'MAKE',
    category: 'Day 7 · MAKE',
    en: 'make a mistake',
    ko: '실수를 하다',
    pron: '메이커 미스테이크',
    tip: '내가 행동을 해서 실수라는 결과물이 생겨난 것이므로 do가 아니라 make a mistake를 씁니다.'
  },
  {
    id: 'make-a-decision',
    verb: 'MAKE',
    category: 'Day 7 · MAKE',
    en: 'make a decision',
    ko: '결정을 내리다',
    pron: '메이커 디시젼',
    tip: 'decide 1단어보다 원어민은 make a decision 소리 블록을 훨씬 더 즐겨 씁니다.'
  },
  {
    id: 'make-an-exception',
    verb: 'MAKE',
    category: 'Day 7 · MAKE',
    en: 'make an exception',
    ko: '예외를 두다 (봐주다)',
    pron: '메이컨 익셉션',
    tip: "make + an + exception이 연음되어 '메이컨 익셉션'처럼 한 호흡에 이어집니다."
  },
  {
    id: 'make-a-reservation',
    verb: 'MAKE',
    category: 'Day 7 · MAKE',
    en: 'make a reservation',
    ko: '(식당·호텔) 예약을 하다',
    pron: '메이커 레저베이션',
    tip: '공간/자리를 잡아 두는 예약은 reservation, 병원·미용실 등 사람과 시간을 잡는 약속은 make an appointment!'
  },
  {
    id: 'make-an-appointment',
    verb: 'MAKE',
    category: 'Day 7 · MAKE',
    en: 'make an appointment',
    ko: '(병원·미용실 등) 예약을 잡다',
    pron: '메이컨 어포인먼(트)',
    tip: '의사 선생님 등 사람을 만나는 예약은 appointment를 씁니다.'
  },
  // Day 8: GET
  {
    id: 'get-a-job',
    verb: 'GET',
    category: 'Day 8 · GET',
    en: 'get a job',
    ko: '취직하다 (일자리를 얻다)',
    pron: '게러 좝',
    tip: 'get + a가 만나면 t가 플랩화되어 게러(get a)로 부드럽게 연결됩니다.'
  },
  {
    id: 'get-some-sleep',
    verb: 'GET',
    category: 'Day 8 · GET',
    en: 'get some sleep',
    ko: '잠을 좀 자다 (수면을 취하다)',
    pron: '겟 썸 슬립',
    tip: '단순히 sleep이라고 하기보다 잠이 부족한 상태에서 수면을 얻는 느낌으로 get some sleep / get some rest를 자주 씁니다.'
  },
  {
    id: 'get-a-refund',
    verb: 'GET',
    category: 'Day 8 · GET',
    en: 'get a refund',
    ko: '환불을 받다',
    pron: '게러 리펀드',
    tip: '내 수중에 없던 환불금을 다시 돌려받아 획득하는 것이므로 get a refund(게러 리펀드)!'
  },
  {
    id: 'get-home-safe',
    verb: 'GET',
    category: 'Day 8 · GET',
    en: 'get home safe',
    ko: '집에 안전하게 도착하다',
    pron: '겟 홈 세이프',
    tip: 'get + 장소 = 그 장소에 도달(도착)하다! Did you get home safe?로 가장 많이 쓰입니다.'
  },
  {
    id: 'get-a-drink',
    verb: 'GET',
    category: 'Day 8 · GET',
    en: 'go get a drink',
    ko: '가서 마실 것 좀 가져오다(마시다)',
    pron: '고 게러 드링크',
    tip: 'go와 get a drink를 묶어 하나의 코어 블록처럼 쓰면 원어민다운 리듬이 살아납니다.'
  },
  // Day 9: TAKE
  {
    id: 'take-you-home',
    verb: 'TAKE',
    category: 'Day 9 · TAKE',
    en: 'take you home',
    ko: '너를 집에 데려다주다',
    pron: '테이큐 홈',
    tip: 'take + 사람 + 장소 = 데려다주다! take와 you가 연음되어 테이큐 홈처럼 소리 납니다.'
  },
  {
    id: 'take-my-medicine',
    verb: 'TAKE',
    category: 'Day 9 · TAKE',
    en: 'take my medicine',
    ko: '약을 챙겨 먹다',
    pron: '테익 마이 메디슨',
    tip: '약은 배불리 씹어 먹는(eat) 음식이 아니라 복용 의도를 가지고 내 몸에 취하는 것이므로 반드시 take를 씁니다!'
  },
  {
    id: 'take-a-shower',
    verb: 'TAKE',
    category: 'Day 9 · TAKE',
    en: 'take a shower',
    ko: '샤워를 하다',
    pron: '테이커 샤워',
    tip: 'take + a가 연음되어 테이커 샤워! take a walk(산책하다), take a break(쉬다)도 같은 패턴입니다.'
  },
  {
    id: 'take-a-bite',
    verb: 'TAKE',
    category: 'Day 9 · TAKE',
    en: 'take a bite',
    ko: '한 입 먹어보다',
    pron: '테이커 바이트',
    tip: '음료 한 모금 마셔보는 건 take a sip(테이커 씹), 음식 한 입 베어 무는 건 take a bite!'
  },
  {
    id: 'take-an-english-class',
    verb: 'TAKE',
    category: 'Day 9 · TAKE',
    en: 'take an English class',
    ko: '영어 수업을 듣다',
    pron: '테이컨 잉글리쉬 클래스',
    tip: '수업은 귀로만 듣는(listen) 게 아니라 내가 참여해 지식을 내 것으로 취하는 것이므로 take a class!'
  },
  // Day 10: HAVE
  {
    id: 'have-a-plan',
    verb: 'HAVE',
    category: 'Day 10 · HAVE',
    en: 'have a plan',
    ko: '계획(방안)을 가지고 있다',
    pron: '해버 플랜',
    tip: 'have + a가 연음되어 해버 플랜! 단수 a plan은 문제를 해결할 구체적 방안·작전이라는 뜻입니다.'
  },
  {
    id: 'have-plans',
    verb: 'HAVE',
    category: 'Day 10 · HAVE',
    en: 'have plans',
    ko: '(선약 등) 일정·약속이 있다',
    pron: '해브 플랜즈',
    tip: '복수형 plans를 쓰면 친구들과 밥 먹거나 만나는 일상적인 약속·일정이 있다는 뜻이 됩니다!'
  },
  {
    id: 'have-lunch',
    verb: 'HAVE',
    category: 'Day 10 · HAVE',
    en: 'have lunch',
    ko: '점심을 먹다 (식사 시간을 보내다)',
    pron: '해브 런치',
    tip: 'eat보다 식사 자리와 시간을 온전히 누리고 경험한다는 뉘앙스로 have breakfast/lunch/dinner를 많이 씁니다.'
  },
  {
    id: 'have-a-good-time',
    verb: 'HAVE',
    category: 'Day 10 · HAVE',
    en: 'have a good time',
    ko: '좋은 시간을 보내다',
    pron: '해버 굿 타임',
    tip: '경험을 온전히 누릴 때도 have를 씁니다 (have fun, have a good time).'
  },
  // 일상 기초 동사 (Day 1~5 복습용)
  {
    id: 'go-home',
    verb: 'BASIC',
    category: '일상 기초 동사',
    en: 'go home',
    ko: '집에 가다',
    pron: '고 홈',
    tip: 'home은 부사이므로 to 없이 바로 go home으로 붙입니다.'
  },
  {
    id: 'wash-my-face',
    verb: 'BASIC',
    category: '일상 기초 동사',
    en: 'wash my face',
    ko: '세수하다',
    pron: '워시 마이 페이스',
    tip: 'Day 5 일상 루틴 필수 블록: get up → wash my face → brush my teeth → leave the house!'
  },
  {
    id: 'brush-my-teeth',
    verb: 'BASIC',
    category: '일상 기초 동사',
    en: 'brush my teeth',
    ko: '양치하다',
    pron: '브러쉬 마이 티쓰',
    tip: '치아 여러 개를 닦으므로 단수 tooth가 아니라 복수형 teeth를 씁니다.'
  },
  {
    id: 'work-late',
    verb: 'BASIC',
    category: '일상 기초 동사',
    en: 'work late',
    ko: '늦게까지 일하다(야근하다)',
    pron: '워크 레이트',
    tip: 'I have to + work late + tonight처럼 3단 블록으로 자주 쓰입니다.'
  }
]

// ---------------------------------------------------------
// 3. 디테일 블록 데이터 (선택 부착)
// ---------------------------------------------------------
const detailBlocks: DetailBlock[] = [
  { id: 'none', en: '', ko: '디테일 없음', pron: '' },
  { id: 'right-now', en: 'right now', ko: '지금 당장', pron: '롸잇 나우' },
  { id: 'tonight', en: 'tonight', ko: '오늘 밤에', pron: '투나잇' },
  { id: 'this-time', en: 'this time', ko: '이번에는', pron: '디스 타임' },
  { id: 'for-me', en: 'for me', ko: '날 위해서(대신해서)', pron: '포 미' },
  { id: 'for-you', en: 'for you', ko: '널 위해서', pron: '포 유' },
  { id: 'every-day', en: 'every day', ko: '매일', pron: '에브리 데이' },
  { id: 'tomorrow', en: 'tomorrow', ko: '내일', pron: '투모로우' },
  { id: 'with-my-friends', en: 'with my friends', ko: '내 친구들과 함께', pron: '위드 마이 프렌즈' },
  { id: 'in-the-morning', en: 'in the morning', ko: '아침에', pron: '인 더 모닝' }
]

const selectedBB = ref<BeginningBlock>(beginningBlocks[0])
const selectedCore = ref<CoreBlock>(coreBlocks[1]) // do the laundry
const selectedDB = ref<DetailBlock>(detailBlocks[1]) // right now

const filteredBBs = computed(() => {
  if (bbFilter.value === 'all') return beginningBlocks
  return beginningBlocks.filter((b) => b.dayGroup === bbFilter.value)
})

const filteredCores = computed(() => {
  if (coreFilter.value === 'all') return coreBlocks
  return coreBlocks.filter((c) => c.verb === coreFilter.value)
})

const activeChunkCount = computed(() => (selectedDB.value.id === 'none' ? 2 : 3))

// 주어(I / you / we)에 맞춰 소유격·목적격 자동 보정 (자연스러운 문장 생성)
const adaptedCore = computed(() => {
  const subj = selectedBB.value.subject
  let en = selectedCore.value.en
  let ko = selectedCore.value.ko
  let pron = selectedCore.value.pron

  if (subj === 'you') {
    if (en === 'take you home') {
      en = 'take me home'
      ko = '나를 집에 데려다주다'
      pron = '테익 미 홈'
    } else if (en.includes('my ')) {
      en = en.replace('my ', 'your ')
      ko = ko.replace('내 ', '네 ')
      pron = pron.replace('마이 ', '유어 ')
    }
  } else if (subj === 'we') {
    if (en.includes('my ')) {
      en = en.replace('my ', 'our ')
      ko = ko.replace('내 ', '우리 ')
      pron = pron.replace('마이 ', '아워 ')
    }
  }
  return { en, ko, pron }
})

const adaptedDB = computed(() => {
  const subj = selectedBB.value.subject
  let en = selectedDB.value.en
  let ko = selectedDB.value.ko
  let pron = selectedDB.value.pron

  if (subj === 'I' && en === 'for me') {
    en = 'for you'
    ko = '널 위해서'
    pron = '포 유'
  } else if (subj === 'you' && en === 'with my friends') {
    en = 'with your friends'
    ko = '네 친구들과 함께'
    pron = '위드 유어 프렌즈'
  }
  return { en, ko, pron }
})

const assembledSentence = computed(() => {
  const bb = selectedBB.value
  const core = adaptedCore.value
  const db = adaptedDB.value

  const parts = [bb.en, core.en]
  const pronParts = [bb.pron, core.pron]
  if (selectedDB.value.id !== 'none' && db.en) {
    parts.push(db.en)
    pronParts.push(db.pron)
  }

  const punct = bb.isQuestion ? '?' : '.'
  const en = parts.join(' ') + punct
  const pron = pronParts.join(' + ')

  const dbKoPrefix = selectedDB.value.id !== 'none' && db.ko ? `${db.ko} ` : ''
  const ko = `${dbKoPrefix}${core.ko} → (${bb.ko})`

  return { en, pron, ko }
})

function selectBB(bb: BeginningBlock) {
  selectedBB.value = bb
}
function selectCore(core: CoreBlock) {
  selectedCore.value = core
}
function selectDB(db: DetailBlock) {
  selectedDB.value = db
}

function randomizeBuilder() {
  const randBB = beginningBlocks[Math.floor(Math.random() * beginningBlocks.length)]
  const randCore = coreBlocks[Math.floor(Math.random() * coreBlocks.length)]
  const randDB = detailBlocks[Math.floor(Math.random() * detailBlocks.length)]
  selectedBB.value = randBB
  selectedCore.value = randCore
  selectedDB.value = randDB
  speakText(assembledSentence.value.en, 1.0)
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

let stepTimers: number[] = []
function clearStepTimers() {
  stepTimers.forEach((id) => window.clearTimeout(id))
  stepTimers = []
}

function speakStepByStep() {
  clearStepTimers()
  const chunks = [selectedBB.value.en, adaptedCore.value.en]
  if (selectedDB.value.id !== 'none' && adaptedDB.value.en) {
    chunks.push(adaptedDB.value.en)
  }
  chunks.push(assembledSentence.value.en)

  let delay = 0
  chunks.forEach((chunk, idx) => {
    const isFull = idx === chunks.length - 1
    const t = window.setTimeout(() => {
      speakText(chunk, isFull ? 1.0 : 0.9)
    }, delay)
    stepTimers.push(t)
    delay += isFull ? 1800 : 1250
  })
}

// ---------------------------------------------------------
// TAB 2 & TAB 3 공통: 1~10일차 핵심 실전 조합 문장 데이터
// ---------------------------------------------------------
const drillFilters = [
  { id: 'all', label: '전체 (1~10일차)' },
  { id: 'day1-5', label: 'Day 1~5 · 시작 블록 집중' },
  { id: 'do-make', label: 'Day 6~7 · DO & MAKE' },
  { id: 'get-take-have', label: 'Day 8~10 · GET · TAKE · HAVE' }
]
const drillFilter = ref('all')

const drills = ref<DrillItem[]>([
  // Day 1~5
  {
    id: 'd1',
    dayGroup: 'day1-5',
    dayLabel: 'Day 1 · wanna',
    ko: '나 그냥 그거 먹고 싶어.',
    en: 'I just wanna eat it.',
    chunks: ['I just wanna', 'eat it'],
    pron: '아이 저스 워너 + 이릿',
    tip: 'eat it이 연음·플랩화되어 이릿으로 소리 납니다. 2개의 블록으로 가볍게 던지세요!'
  },
  {
    id: 'd2',
    dayGroup: 'day1-5',
    dayLabel: 'Day 1 · don\'t wanna',
    ko: '너를 화나게 하고 싶지 않아.',
    en: "I don't wanna make you mad.",
    chunks: ["I don't wanna", 'make you mad'],
    pron: '아러워너 + 메이큐 매드',
    tip: "뒤의 make you mad가 바로 안 떠올라도 일단 입에서 I don't wanna(아러워너)부터 먼저 뱉는 게 핵심!"
  },
  {
    id: 'd3',
    dayGroup: 'day1-5',
    dayLabel: 'Day 1 · Do you wanna',
    ko: '너 이거 진짜 하고 싶어?',
    en: 'Do you really wanna do this?',
    chunks: ['Do you really wanna', 'do this?'],
    pron: '두유 뤼얼리 워너 + 두 디스?',
    tip: 'Do you는 힘을 빼고 really와 wan-에 리듬을 실어 질문합니다.'
  },
  {
    id: 'd4',
    dayGroup: 'day1-5',
    dayLabel: 'Day 2 · I\'m gonna',
    ko: '나 가서 마실 것 좀 가져올게.',
    en: "I'm gonna go get a drink.",
    chunks: ["I'm gonna", 'go get a drink'],
    pron: '암거너 + 고 게러 드링크',
    tip: '총 7단어지만 뇌는 [암거너] + [고 게러 드링크] 단 2블록으로 처리합니다!'
  },
  {
    id: 'd5',
    dayGroup: 'day1-5',
    dayLabel: 'Day 2 · We\'re gonna',
    ko: '우리가 해결할게요 (알아낼게요).',
    en: "We're gonna figure it out.",
    chunks: ["We're gonna", 'figure it out'],
    pron: '워거너 + 피겨릿 아웃',
    tip: "We're는 were(워)처럼 발음해 '워거너', figure it out은 연음해 '피겨릿 아웃'!"
  },
  {
    id: 'd6',
    dayGroup: 'day1-5',
    dayLabel: 'Day 3 · have to',
    ko: '나 오늘 밤 늦게까지 일해야 돼.',
    en: 'I have to work late tonight.',
    chunks: ['I have to', 'work late', 'tonight'],
    pron: '아이 해프터 + 워크 레이트 + 투나잇',
    tip: 'have to는 해브투(3음절)가 아니라 sister와 같은 2음절 리듬(해프터)!'
  },
  {
    id: 'd7',
    dayGroup: 'day1-5',
    dayLabel: 'Day 3 + Day 1 합체',
    ko: '원하지 않으면 너 여기 안 있어도 돼.',
    en: "You don't have to stay here if you don't wanna.",
    chunks: ["You don't have to", 'stay here', "if you don't wanna"],
    pron: '유론해프터 + 스테이 히어 + 이프 유 론워너',
    tip: 'Day 3 블록(You don\'t have to)과 Day 1 블록(don\'t wanna)을 레고처럼 합체한 문장입니다!'
  },
  {
    id: 'd8',
    dayGroup: 'day1-5',
    dayLabel: 'Day 4 · I\'ll / won\'t',
    ko: '내가 저 사람들한테 말할게.',
    en: "I'll talk to them.",
    chunks: ["I'll", 'talk to them'],
    pron: '아을(올) + 턱 투 뎀',
    tip: "I'll은 아-일(2음절)이 아니라 Dark L을 써서 '아을/올' 1음절로 바로 동사에 붙입니다."
  },
  {
    id: 'd9',
    dayGroup: 'day1-5',
    dayLabel: 'Day 5 · 일상 루틴 & 과거',
    ko: '너 오늘 아침에 세수했어?',
    en: 'Did you wash your face this morning?',
    chunks: ['Did you', 'wash your face', 'this morning?'],
    pron: '디쥬 + 워시 유어 페이스 + 디스 모닝?',
    tip: '과거 의문문은 동사 과거형을 고민할 필요 없이 무조건 [디쥬 + 동사원형 블록]!'
  },
  // Day 6~7: DO & MAKE
  {
    id: 'd10',
    dayGroup: 'do-make',
    dayLabel: 'Day 6 · DO + Day 3',
    ko: '너 내 일을 대신해 줄 필요 없어.',
    en: "You don't have to do my work for me.",
    chunks: ["You don't have to", 'do my work', 'for me'],
    pron: '유론해프터 + 두 마이 워크 + 포 미',
    tip: '9단어 문장이지만 3개의 소리 블록만 조립하면 0.1초 만에 입에서 나옵니다!'
  },
  {
    id: 'd11',
    dayGroup: 'do-make',
    dayLabel: 'Day 6 · DO (운동)',
    ko: '나는 필라테스만 해.',
    en: 'I just do Pilates.',
    chunks: ['I just', 'do Pilates'],
    pron: '아이 저스 + 두 펄라리즈',
    tip: '요가·필라테스·태권도 같은 개인 수련 운동은 do! 발음은 필라테스가 아니라 펄라리즈!'
  },
  {
    id: 'd12',
    dayGroup: 'do-make',
    dayLabel: 'Day 6 · DO (집안일)',
    ko: '내가 빨래할게.',
    en: "I'll do the laundry.",
    chunks: ["I'll", 'do the laundry'],
    pron: '아을 + 두 더 런쥬리',
    tip: 'laundry는 라운드리가 아니라 런쥬리! 집안일은 do the laundry / do the dishes.'
  },
  {
    id: 'd13',
    dayGroup: 'do-make',
    dayLabel: 'Day 6 · DO + Day 5',
    ko: '내가 옛날에 네 머리 해 주곤 했었는데.',
    en: 'I used to do your hair.',
    chunks: ['I used to', 'do your hair'],
    pron: '아이 유스터 + 두 유어 헤어',
    tip: 'Day 5 습관 블록(I used to) + Day 6 단장 블록(do your hair)의 완벽한 콜라보!'
  },
  {
    id: 'd14',
    dayGroup: 'do-make',
    dayLabel: 'Day 7 · MAKE (침대 정리)',
    ko: '너 침대(이불) 정리해야지.',
    en: 'You have to make your bed.',
    chunks: ['You have to', 'make your bed'],
    pron: '유 해프터 + 메익 유어 베드',
    tip: '침구를 깔끔히 정돈된 결과물 상태로 만들어 놓는 것이라 make your bed를 씁니다.'
  },
  {
    id: 'd15',
    dayGroup: 'do-make',
    dayLabel: 'Day 7 · MAKE + Day 4',
    ko: '이번에는 제가 예외로 할게요 (특별히 봐드릴게요).',
    en: "I'll make an exception this time.",
    chunks: ["I'll", 'make an exception', 'this time'],
    pron: '아을 + 메이컨 익셉션 + 디스 타임',
    tip: "make an exception이 연음되어 '메이컨 익셉션' 한 블록으로 착 붙습니다."
  },
  {
    id: 'd16',
    dayGroup: 'do-make',
    dayLabel: 'Day 7 · MAKE (예약)',
    ko: '저 예약 안 했는데요.',
    en: "I didn't make a reservation.",
    chunks: ["I didn't", 'make a reservation'],
    pron: '아이 디든 + 메이커 레저베이션',
    tip: '식당·호텔처럼 공간/자리를 예약할 때는 make a reservation!'
  },
  // Day 8~10: GET, TAKE, HAVE
  {
    id: 'd17',
    dayGroup: 'get-take-have',
    dayLabel: 'Day 8 · GET (취업)',
    ko: '나 취직해야 돼 (일자리 구해야 돼).',
    en: 'I have to get a job.',
    chunks: ['I have to', 'get a job'],
    pron: '아이 해프터 + 게러 좝',
    tip: '없던 직업을 내 손에 얻는 것이므로 get a job(게러 좝)!'
  },
  {
    id: 'd18',
    dayGroup: 'get-take-have',
    dayLabel: 'Day 8 · GET (잠·휴식)',
    ko: '너 잠 좀 자야겠다.',
    en: 'You have to get some sleep.',
    chunks: ['You have to', 'get some sleep'],
    pron: '유 해프터 + 겟 썸 슬립',
    tip: '부족한 수면이나 휴식을 취할 때는 get some sleep / get some rest 블록을 씁니다.'
  },
  {
    id: 'd19',
    dayGroup: 'get-take-have',
    dayLabel: 'Day 8 · GET (도착)',
    ko: '너 집에 안전하게 도착했어?',
    en: 'Did you get home safe?',
    chunks: ['Did you', 'get home safe?'],
    pron: '디쥬 + 겟 홈 세이프?',
    tip: '친구와 헤어지고 집에 잘 들어갔는지 물어볼 때 0.1초 만에 나와야 하는 필수 문장!'
  },
  {
    id: 'd20',
    dayGroup: 'get-take-have',
    dayLabel: 'Day 9 · TAKE (데려다주다)',
    ko: '내가 너 집에 데려다줄게.',
    en: "I'll take you home.",
    chunks: ["I'll", 'take you home'],
    pron: '아을 + 테이큐 홈',
    tip: 'take + 사람 + 장소 = 데려다주다! take you가 연음되어 테이큐 홈!'
  },
  {
    id: 'd21',
    dayGroup: 'get-take-have',
    dayLabel: 'Day 9 · TAKE (복용)',
    ko: '나 약 먹어야 돼.',
    en: 'I have to take my medicine.',
    chunks: ['I have to', 'take my medicine'],
    pron: '아이 해프터 + 테익 마이 메디슨',
    tip: '약은 eat이 아니라 복용 의도를 갖고 내 몸에 취하는 것이므로 take my medicine!'
  },
  {
    id: 'd22',
    dayGroup: 'get-take-have',
    dayLabel: 'Day 9 · TAKE (한 입)',
    ko: '한 입 먹어볼래?',
    en: 'Do you wanna take a bite?',
    chunks: ['Do you wanna', 'take a bite?'],
    pron: '두유워너 + 테이커 바이트?',
    tip: '한 입 베어 물기는 take a bite, 음료 한 모금 마셔보기는 take a sip!'
  },
  {
    id: 'd23',
    dayGroup: 'get-take-have',
    dayLabel: 'Day 10 · HAVE (출산)',
    ko: '우리 곧 아기가 태어나요 (출산할 거예요).',
    en: "We're having a baby.",
    chunks: ["We're", 'having a baby'],
    pron: '워 + 해빙 어 베이비',
    tip: "새 생명을 맞이하는 진행형은 We're having a baby라고 표현합니다."
  },
  {
    id: 'd24',
    dayGroup: 'get-take-have',
    dayLabel: 'Day 10 · HAVE (선약·약속)',
    ko: '나 내일 친구들이랑 약속(일정) 있어.',
    en: 'I have plans with my friends tomorrow.',
    chunks: ['I have plans', 'with my friends', 'tomorrow'],
    pron: '아이 해브 플랜즈 + 위드 마이 프렌즈 + 투모로우',
    tip: '단수 a plan은 해결 방안/작전, 복수 plans는 사람들과 만나는 약속/일정입니다!'
  }
])

const filteredDrills = computed(() => {
  if (drillFilter.value === 'all') return drills.value
  return drills.value.filter((d) => d.dayGroup === drillFilter.value)
})

// ---------------------------------------------------------
// TAB 2: 퍼즐 상태 관리
// ---------------------------------------------------------
const puzzleIndex = ref(0)
const userSelectedChunks = ref<string[]>([])
const puzzleSolved = ref(false)
const puzzleWrong = ref(false)
const solvedIds = ref<string[]>([])

const currentPuzzle = computed(() => filteredDrills.value[puzzleIndex.value] || filteredDrills.value[0])
const solvedCount = computed(() =>
  filteredDrills.value.filter((d) => solvedIds.value.includes(d.id)).length
)

const puzzleOptions = computed(() => {
  if (!currentPuzzle.value) return []
  const answerChunks = [...currentPuzzle.value.chunks]
  const distractorsPool = [
    'I wanna',
    "I'm gonna",
    "You don't have to",
    'Did you',
    'make my work',
    'eat my medicine',
    'do a mistake',
    'right now',
    'for you'
  ].filter((item) => !answerChunks.includes(item))

  // 오답 조각 2~3개 섞기
  const extra = distractorsPool.slice(0, 3)
  const combined = [...answerChunks, ...extra]
  return combined.sort((a, b) => a.localeCompare(b))
})

function resetCurrentPuzzle() {
  userSelectedChunks.value = []
  puzzleSolved.value = false
  puzzleWrong.value = false
}

watch(currentPuzzle, () => {
  resetCurrentPuzzle()
})

function setDrillFilter(id: string) {
  drillFilter.value = id
  puzzleIndex.value = 0
  reflexIndex.value = 0
  resetCurrentPuzzle()
  resetReflexState()
}

function shuffleDrills() {
  drills.value = [...drills.value].sort(() => Math.random() - 0.5)
  puzzleIndex.value = 0
  resetCurrentPuzzle()
}

function pickPuzzleOption(opt: string) {
  if (!currentPuzzle.value || puzzleSolved.value) return
  if (userSelectedChunks.value.length >= currentPuzzle.value.chunks.length) return

  userSelectedChunks.value.push(opt)
  puzzleWrong.value = false

  if (userSelectedChunks.value.length === currentPuzzle.value.chunks.length) {
    const isCorrect = userSelectedChunks.value.every(
      (val, idx) => val === currentPuzzle.value.chunks[idx]
    )
    if (isCorrect) {
      puzzleSolved.value = true
      if (!solvedIds.value.includes(currentPuzzle.value.id)) {
        solvedIds.value.push(currentPuzzle.value.id)
      }
      speakText(currentPuzzle.value.en, 1.0)
    } else {
      puzzleWrong.value = true
    }
  }
}

function removeChunkAt(idx: number) {
  if (puzzleSolved.value) return
  if (userSelectedChunks.value[idx]) {
    userSelectedChunks.value.splice(idx, 1)
    puzzleWrong.value = false
  }
}

function revealPuzzleAnswer() {
  if (!currentPuzzle.value) return
  userSelectedChunks.value = [...currentPuzzle.value.chunks]
  puzzleWrong.value = false
  puzzleSolved.value = true
  speakText(currentPuzzle.value.en, 1.0)
}

function prevPuzzle() {
  if (puzzleIndex.value > 0) {
    puzzleIndex.value--
  } else {
    puzzleIndex.value = filteredDrills.value.length - 1
  }
}

function nextPuzzle() {
  if (puzzleIndex.value < filteredDrills.value.length - 1) {
    puzzleIndex.value++
  } else {
    puzzleIndex.value = 0
  }
}

// ---------------------------------------------------------
// TAB 3: 0.1초 순발력 스피킹 드릴 상태 관리
// ---------------------------------------------------------
const reflexIndex = ref(0)
const showBBHint = ref(false)
const showReflexAnswer = ref(false)
const autoPlayTTS = ref(true)
const masteredIds = ref<string[]>([])
const reflexProgress = ref(0)
let reflexTimer: number | null = null

const currentReflex = computed(() => filteredDrills.value[reflexIndex.value] || filteredDrills.value[0])

function clearReflexTimer() {
  if (reflexTimer !== null) {
    window.clearInterval(reflexTimer)
    reflexTimer = null
  }
}

function resetReflexState() {
  clearReflexTimer()
  showBBHint.value = false
  showReflexAnswer.value = false
  reflexProgress.value = 0
}

function startThreeSecChallenge() {
  resetReflexState()
  const start = Date.now()
  const duration = 3000
  reflexTimer = window.setInterval(() => {
    const elapsed = Date.now() - start
    reflexProgress.value = Math.min(100, Math.round((elapsed / duration) * 100))
    if (elapsed >= duration) {
      clearReflexTimer()
      revealReflex()
    }
  }, 50)
}

function revealReflex() {
  clearReflexTimer()
  reflexProgress.value = 100
  showReflexAnswer.value = true
  if (autoPlayTTS.value && currentReflex.value) {
    speakText(currentReflex.value.en, 1.0)
  }
}

function toggleMastered(id: string) {
  const idx = masteredIds.value.indexOf(id)
  if (idx === -1) {
    masteredIds.value.push(id)
  } else {
    masteredIds.value.splice(idx, 1)
  }
}

function prevReflex() {
  resetReflexState()
  if (reflexIndex.value > 0) {
    reflexIndex.value--
  } else {
    reflexIndex.value = filteredDrills.value.length - 1
  }
}

function nextReflex() {
  resetReflexState()
  if (reflexIndex.value < filteredDrills.value.length - 1) {
    reflexIndex.value++
  } else {
    reflexIndex.value = 0
  }
}

function randomReflex() {
  resetReflexState()
  if (filteredDrills.value.length <= 1) return
  let next = reflexIndex.value
  while (next === reflexIndex.value) {
    next = Math.floor(Math.random() * filteredDrills.value.length)
  }
  reflexIndex.value = next
}

onBeforeUnmount(() => {
  clearStepTimers()
  clearReflexTimer()
})
</script>

<style scoped>
.sb-trainer {
  margin: 1.5rem 0 2.2rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 16px;
  background: var(--vp-c-bg-soft);
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
}

.sb-header {
  padding: 1.25rem 1.5rem 0;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.09), rgba(16, 185, 129, 0.08));
  border-bottom: 1px solid var(--vp-c-divider);
}

.sb-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  margin-bottom: 0.45rem;
}

.sb-title {
  margin: 0 0 0.35rem !important;
  font-size: 1.25rem !important;
  font-weight: 800;
  color: var(--vp-c-text-1);
}

.sb-subtitle {
  margin: 0 0 1rem !important;
  font-size: 0.9rem;
  color: var(--vp-c-text-2);
  line-height: 1.55;
}

.sb-tabs {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.sb-tab {
  padding: 0.65rem 1.05rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--vp-c-text-2);
  background: transparent;
  border: 1px solid transparent;
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  cursor: pointer;
  transition: all 0.18s ease;
}

.sb-tab:hover {
  color: var(--vp-c-text-1);
  background: rgba(255, 255, 255, 0.4);
}

.sb-tab.active {
  color: var(--vp-c-brand-1);
  background: var(--vp-c-bg);
  border-color: var(--vp-c-divider);
}

.sb-body {
  padding: 1.35rem 1.5rem;
  background: var(--vp-c-bg);
}

/* 전광판 스테이지 */
.sb-stage {
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  padding: 1.15rem 1.25rem;
  background: var(--vp-c-bg-soft);
  margin-bottom: 1.35rem;
}

.sb-stage-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.9rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.sb-stage-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--vp-c-text-2);
  text-transform: uppercase;
}

.sb-lego-chain {
  display: flex;
  align-items: stretch;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.sb-lego-piece {
  flex: 1 1 180px;
  display: flex;
  flex-direction: column;
  padding: 0.8rem 0.95rem;
  border-radius: 12px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.sb-lego-piece:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.sb-lego-piece.bb {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.35);
}

.sb-lego-piece.core {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.38);
}

.sb-lego-piece.db {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.38);
}

.piece-tag {
  font-size: 0.72rem;
  font-weight: 700;
  opacity: 0.8;
  margin-bottom: 0.2rem;
}

.piece-en {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--vp-c-text-1);
}

.piece-pron {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--vp-c-brand-1);
  margin-top: 0.15rem;
}

.piece-ko {
  font-size: 0.8rem;
  color: var(--vp-c-text-2);
  margin-top: 0.15rem;
}

.sb-plus {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--vp-c-text-3);
  padding: 0 0.15rem;
}

.sb-assembled-box {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 1rem 1.15rem;
  margin-bottom: 0.9rem;
}

.sb-assembled-en {
  font-size: 1.45rem;
  font-weight: 800;
  color: var(--vp-c-text-1);
  margin-bottom: 0.35rem;
  letter-spacing: -0.01em;
}

.sb-assembled-pron {
  font-size: 0.95rem;
  color: var(--vp-c-brand-1);
  margin-bottom: 0.25rem;
}

.sb-assembled-ko {
  font-size: 0.9rem;
  color: var(--vp-c-text-2);
  margin-bottom: 0.85rem;
}

.sb-audio-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.sb-btn {
  padding: 0.45rem 0.85rem;
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.sb-btn:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.sb-btn-primary {
  background: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  color: #fff !important;
}

.sb-btn-primary:hover {
  opacity: 0.92;
}

.sb-btn-step {
  background: rgba(16, 185, 129, 0.14);
  border-color: rgba(16, 185, 129, 0.4);
  color: var(--vp-c-text-1);
}

.sb-btn-random {
  background: rgba(139, 92, 246, 0.14);
  border-color: rgba(139, 92, 246, 0.4);
}

.sb-btn-mastered {
  background: rgba(16, 185, 129, 0.2);
  border-color: rgba(16, 185, 129, 0.55);
}

.sb-btn-large {
  padding: 0.75rem 1.35rem;
  font-size: 0.98rem;
}

.sb-btn-sm {
  padding: 0.3rem 0.65rem;
  font-size: 0.78rem;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  cursor: pointer;
}

.sb-coaching-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.65rem;
}

.sb-coaching-item {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  padding: 0.7rem 0.9rem;
  font-size: 0.83rem;
}

.sb-coaching-item p {
  margin: 0.3rem 0 0 !important;
  line-height: 1.45;
  color: var(--vp-c-text-2);
}

.coach-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.12rem 0.5rem;
  border-radius: 6px;
}

.bb-badge {
  background: rgba(59, 130, 246, 0.15);
  color: #2563eb;
}

.core-badge {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}

/* 팔레트 영역 */
.sb-palette-section {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.sb-palette-box {
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 0.95rem 1.1rem;
  background: var(--vp-c-bg-soft);
}

.sb-palette-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.sb-palette-header h4 {
  margin: 0 !important;
  font-size: 0.95rem !important;
  font-weight: 700;
}

.sb-filter-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.sb-pill {
  padding: 0.25rem 0.65rem;
  font-size: 0.76rem;
  font-weight: 600;
  border-radius: 999px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  color: var(--vp-c-text-2);
  cursor: pointer;
}

.sb-pill.active {
  background: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  color: #fff;
}

.sb-chip-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
  gap: 0.45rem;
}

.sb-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  padding: 0.55rem 0.75rem;
  border-radius: 9px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  cursor: pointer;
  transition: all 0.14s ease;
}

.sb-chip:hover {
  border-color: var(--vp-c-brand-1);
}

.sb-chip.bb-chip.selected {
  border-width: 2px;
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.sb-chip.core-chip.selected {
  border-width: 2px;
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.sb-chip.db-chip.selected {
  border-width: 2px;
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

.chip-verb-tag {
  font-size: 0.66rem;
  font-weight: 800;
  padding: 0.08rem 0.4rem;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.16);
  color: #059669;
  margin-bottom: 0.2rem;
}

.chip-en {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--vp-c-text-1);
}

.chip-sub {
  font-size: 0.75rem;
  color: var(--vp-c-text-2);
  margin-top: 0.12rem;
}

/* 퍼즐 & 드릴 공통 */
.sb-drill-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-bottom: 1rem;
}

.sb-drill-nav,
.sb-reflex-settings {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.sb-score-badge {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
}

.sb-puzzle-card,
.sb-reflex-card {
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  padding: 1.25rem;
  background: var(--vp-c-bg-soft);
}

.sb-puzzle-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.65rem;
}

.sb-day-tag {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.18rem 0.6rem;
  border-radius: 6px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
}

.sb-chunk-tag,
.sb-mastered-tag {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.18rem 0.55rem;
  border-radius: 6px;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
}

.sb-prompt-ko {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--vp-c-text-1);
  margin-bottom: 0.35rem;
}

.sb-prompt-guide {
  font-size: 0.85rem;
  color: var(--vp-c-text-2);
  margin: 0 0 1rem !important;
}

.sb-answer-slots {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 1rem;
}

.sb-slot {
  flex: 1 1 160px;
  min-height: 64px;
  border: 2px dashed var(--vp-c-divider);
  border-radius: 10px;
  padding: 0.6rem 0.85rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: var(--vp-c-bg);
  cursor: pointer;
}

.sb-slot.filled {
  border-style: solid;
  border-color: var(--vp-c-brand-1);
}

.sb-slot.correct {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.08);
}

.sb-slot.wrong {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
}

.slot-num {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--vp-c-text-3);
}

.slot-text {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--vp-c-text-1);
}

.slot-placeholder {
  font-size: 0.82rem;
  color: var(--vp-c-text-3);
}

.sb-options-pool {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.sb-option-chip {
  padding: 0.55rem 0.95rem;
  border-radius: 9px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--vp-c-text-1);
  cursor: pointer;
  transition: all 0.14s ease;
}

.sb-option-chip:hover:not(:disabled) {
  border-color: var(--vp-c-brand-1);
  transform: translateY(-1px);
}

.sb-option-chip:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.sb-feedback {
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.sb-feedback.wrong {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.35);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  flex-wrap: wrap;
  font-size: 0.9rem;
}

.sb-feedback.correct {
  background: var(--vp-c-bg);
  border: 1px solid rgba(16, 185, 129, 0.45);
}

.sb-solved-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: #059669;
  margin-bottom: 0.3rem;
}

.sb-solved-en {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--vp-c-text-1);
  margin-bottom: 0.25rem;
}

.sb-solved-pron {
  font-size: 0.92rem;
  color: var(--vp-c-brand-1);
  margin-bottom: 0.25rem;
}

.sb-solved-tip {
  font-size: 0.85rem;
  color: var(--vp-c-text-2);
  margin-bottom: 0.8rem;
}

.sb-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--vp-c-divider);
}

/* TAB 3: 순발력 타이머 */
.sb-timer-wrap {
  margin: 0.8rem 0 1rem;
}

.sb-timer-bar {
  height: 8px;
  border-radius: 999px;
  background: var(--vp-c-bg);
  overflow: hidden;
  border: 1px solid var(--vp-c-divider);
  margin-bottom: 0.65rem;
}

.sb-timer-fill {
  height: 100%;
  background: #10b981;
  transition: width 0.06s linear;
}

.sb-timer-fill.urgent {
  background: #f59e0b;
}

.sb-timer-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.sb-bb-hint-box {
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.35);
  margin-bottom: 1rem;
  font-size: 0.95rem;
}

.sb-reveal-zone {
  display: flex;
  justify-content: center;
  padding: 1.2rem 0;
}

.sb-reflex-answer {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 1rem 1.15rem;
  margin-bottom: 1rem;
}

.sb-reflex-chunks {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.85rem;
}

.sb-reflex-chunk {
  padding: 0.5rem 0.85rem;
  border-radius: 9px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.sb-reflex-chunk.bb {
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.35);
}

.sb-reflex-chunk.core {
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
}

.sb-reflex-chunk.db {
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.chunk-role {
  font-size: 0.68rem;
  font-weight: 700;
  opacity: 0.75;
}

.sb-toggle-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
  color: var(--vp-c-text-2);
  cursor: pointer;
}
</style>
