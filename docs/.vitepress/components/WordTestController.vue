<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute } from 'vitepress'

const route = useRoute()
const isTestMode = ref(false)
const revealedCount = ref(0)
const totalTargets = ref(0)
const allTargets = ref([])

function isEnglishTestText(text) {
  const cleaned = (text || '').trim().replace(/\s*✅\s*$/, '')
  if (!cleaned) return false
  // 영어 알파벳이 포함되어 있어야 함
  if (!/[a-zA-Z]/.test(cleaned)) return false
  // 한글이 포함되어 있으면 설명문이므로 제외
  if (/[가-힣]/.test(cleaned)) return false
  return true
}

function scanTargets() {
  if (typeof document === 'undefined') return []
  const container = document.querySelector('.vp-doc')
  if (!container) return []

  const found = []
  const seen = new Set()

  // 1. 표의 2번째 열(형용사 단어) 및 4번째 열(실전 예문)
  const rows = container.querySelectorAll('table tbody tr')
  rows.forEach(row => {
    const c2 = row.querySelector('td:nth-child(2) strong')
    if (c2 && isEnglishTestText(c2.textContent) && !seen.has(c2)) {
      seen.add(c2)
      found.push({ el: c2, type: 'word' })
    }
    const c4 = row.querySelector('td:nth-child(4) strong')
    if (c4 && isEnglishTestText(c4.textContent) && !seen.has(c4)) {
      seen.add(c4)
      found.push({ el: c4, type: 'sentence' })
    }
  })

  // 2. 리스트 항목 (Section 5 핵심 구문 및 Section 6 예문)
  const listStrongs = container.querySelectorAll('ul li > strong')
  listStrongs.forEach(strong => {
    if (strong.closest('.word-test-container')) return
    if (isEnglishTestText(strong.textContent) && !seen.has(strong)) {
      seen.add(strong)
      found.push({ el: strong, type: 'phrase' })
    }
  })

  // 3. 소제목 내 굵은 글씨 (Section 6 단어 제목)
  const h4Strongs = container.querySelectorAll('h4 strong')
  h4Strongs.forEach(strong => {
    if (isEnglishTestText(strong.textContent) && !seen.has(strong)) {
      seen.add(strong)
      found.push({ el: strong, type: 'word' })
    }
  })

  return found
}

function updateCounts() {
  if (typeof document === 'undefined') return
  const revealed = document.querySelectorAll('.word-test-target.is-revealed')
  revealedCount.value = revealed.length
}

function activateTestMode() {
  if (typeof document === 'undefined') return
  const container = document.querySelector('.vp-doc')
  if (container) {
    container.classList.add('word-test-active')
  }

  const targets = scanTargets()
  allTargets.value = targets
  totalTargets.value = targets.length
  revealedCount.value = 0

  targets.forEach(({ el, type }) => {
    el.classList.add('word-test-target', 'is-hidden')
    el.classList.remove('is-revealed')
    el.setAttribute('data-test-type', type)
    el.setAttribute('title', '클릭하여 정답 및 발음 확인')
  })
}

function deactivateTestMode() {
  if (typeof document === 'undefined') return
  const container = document.querySelector('.vp-doc')
  if (container) {
    container.classList.remove('word-test-active')
  }

  const targets = allTargets.value.length ? allTargets.value : scanTargets()
  targets.forEach(({ el }) => {
    el.classList.remove('word-test-target', 'is-hidden', 'is-revealed')
    el.removeAttribute('data-test-type')
    el.removeAttribute('title')
  })

  revealedCount.value = 0
}

function toggleMode() {
  isTestMode.value = !isTestMode.value
  if (isTestMode.value) {
    activateTestMode()
  } else {
    deactivateTestMode()
  }
}

function hideAll() {
  if (!isTestMode.value || typeof document === 'undefined') return
  allTargets.value.forEach(({ el }) => {
    el.classList.add('is-hidden')
    el.classList.remove('is-revealed')
  })
  revealedCount.value = 0
}

function showAll() {
  if (!isTestMode.value || typeof document === 'undefined') return
  allTargets.value.forEach(({ el }) => {
    el.classList.remove('is-hidden')
    el.classList.add('is-revealed')
  })
  revealedCount.value = totalTargets.value
}

function handleDocClick(event) {
  if (!isTestMode.value) return
  if (event.target.closest('.word-test-container')) return

  let target = event.target.closest('.word-test-target')
  if (!target) {
    const td = event.target.closest('td')
    if (td) {
      target = td.querySelector('.word-test-target.is-hidden')
    }
  }
  if (!target) {
    const li = event.target.closest('li')
    if (li) {
      target = li.querySelector('.word-test-target.is-hidden')
    }
  }

  if (target && target.classList.contains('is-hidden')) {
    target.classList.remove('is-hidden')
    target.classList.add('is-revealed')
    updateCounts()
  }
}

onMounted(() => {
  nextTick(() => {
    const targets = scanTargets()
    allTargets.value = targets
    totalTargets.value = targets.length
    document.addEventListener('click', handleDocClick)
  })
})

onBeforeUnmount(() => {
  deactivateTestMode()
  if (typeof document !== 'undefined') {
    document.removeEventListener('click', handleDocClick)
  }
})

watch(() => route.path, () => {
  if (isTestMode.value) {
    isTestMode.value = false
    deactivateTestMode()
  }
  nextTick(() => {
    const targets = scanTargets()
    allTargets.value = targets
    totalTargets.value = targets.length
  })
})
</script>

<template>
  <div class="word-test-container" aria-label="단어 테스트 모드 컨트롤러">
    <div class="word-test-bar" :class="{ 'is-active': isTestMode }">
      <!-- 상단 단일 라디오 버튼 컨트롤 -->
      <label
        class="radio-label"
        tabindex="0"
        role="radio"
        :aria-checked="isTestMode"
        @click.prevent="toggleMode"
        @keydown.space.prevent="toggleMode"
        @keydown.enter.prevent="toggleMode"
        title="클릭하여 단어 테스트 모드를 켜거나 끕니다"
      >
        <span class="custom-radio" :class="{ checked: isTestMode }">
          <span class="radio-dot" v-if="isTestMode"></span>
        </span>
        <input
          type="radio"
          name="word-test-mode-radio"
          :checked="isTestMode"
          class="hidden-radio-input"
          aria-hidden="true"
          tabindex="-1"
        />
        <span class="radio-label-text">단어 테스트 모드 (영어 가리기)</span>
      </label>

      <!-- 테스트 활성화 시 우측 상태 & 조작 버튼 -->
      <div v-if="isTestMode" class="active-controls">
        <span class="status-counter">
          🎯 <strong>{{ revealedCount }}</strong> / {{ totalTargets }} 확인됨
        </span>
        <button
          type="button"
          class="btn-action"
          @click="hideAll"
          title="모든 단어를 다시 가립니다"
        >
          🔄 다시 가리기
        </button>
        <button
          type="button"
          class="btn-action outline"
          @click="showAll"
          title="모든 정답을 확인합니다"
        >
          👁️ 모두 보기
        </button>
      </div>
      <div v-else class="inactive-hint">
        <span class="badge-normal">학습 모드 (영어 전체 표시)</span>
      </div>
    </div>

    <!-- 테스트 안내 가이드 -->
    <div v-if="isTestMode" class="test-guide-box">
      <div class="guide-icon">💡</div>
      <div class="guide-text">
        <strong>단어 테스트 진행 중:</strong> 한국어 의미를 확인하고 알맞은 영어 단어나 문장을 마음속으로 떠올려 보세요. 가려진 빈칸(<code>❓ 클릭하여 확인</code>)을 누르면 정답이 나타나며 원어민 발음이 재생됩니다. 테스트를 종료하려면 상단의 라디오 버튼을 다시 누르세요.
      </div>
    </div>
  </div>
</template>

<style scoped>
.word-test-container {
  margin: 16px 0 24px;
  font-family: inherit;
}

.word-test-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 18px;
  background: var(--vp-c-bg-soft);
  border: 1.5px solid var(--vp-c-divider);
  border-radius: 12px;
  transition: all 0.25s ease;
}

.word-test-bar.is-active {
  background: var(--vp-c-brand-soft);
  border-color: var(--vp-c-brand-1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.radio-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  padding: 4px 0;
}

.radio-label:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 4px;
  border-radius: 6px;
}

.hidden-radio-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

.custom-radio {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--vp-c-text-3);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--vp-c-bg);
  box-sizing: border-box;
  flex-shrink: 0;
}

.custom-radio.checked {
  border-color: var(--vp-c-brand-1);
  border-width: 2px;
}

.radio-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--vp-c-brand-1);
  animation: dotPop 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes dotPop {
  0% { transform: scale(0); }
  100% { transform: scale(1); }
}

.radio-label-text {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--vp-c-text-1);
}

.active-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-counter {
  font-size: 13px;
  color: var(--vp-c-brand-1);
  font-weight: 600;
  background: var(--vp-c-bg);
  padding: 4px 10px;
  border-radius: 20px;
  border: 1px solid var(--vp-c-brand-1);
}

.inactive-hint .badge-normal {
  font-size: 12px;
  color: var(--vp-c-text-2);
  background: var(--vp-c-bg-mute);
  padding: 4px 10px;
  border-radius: 20px;
}

.btn-action {
  padding: 5px 12px;
  font-size: 12.5px;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid var(--vp-c-brand-1);
  background: var(--vp-c-brand-1);
  color: #fff;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-action:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-action.outline {
  background: var(--vp-c-bg);
  color: var(--vp-c-brand-1);
}

.btn-action.outline:hover {
  background: var(--vp-c-brand-soft);
}

.test-guide-box {
  margin-top: 10px;
  padding: 10px 14px;
  background: var(--vp-c-bg-mute);
  border-left: 4px solid var(--vp-c-brand-1);
  border-radius: 0 8px 8px 0;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: var(--vp-c-text-2);
  line-height: 1.5;
  animation: fadeIn 0.3s ease;
}

.guide-icon {
  font-size: 15px;
  flex-shrink: 0;
  margin-top: 1px;
}

.guide-text code {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--vp-c-bg);
  color: var(--vp-c-brand-1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
