<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useData } from 'vitepress'
const { frontmatter, page } = useData()
const supported = ref(false)
const text = ref('')
const rate = ref(0.85)
const speaking = ref(false)
const message = ref('')
let utterance
let revision = 0
const isEnglish = value => /[a-z]/i.test(value) && !/[^\x00-\x7F\u00A0\u00B7\u2010-\u201F\u2026]/.test(value) && value.length <= 600
function capture() {
  if (!frontmatter.value.listen || !supported.value) return
  const selection = window.getSelection()
  if (!selection || selection.isCollapsed || !selection.rangeCount) return
  const root = document.querySelector('.vp-doc')
  const range = selection.getRangeAt(0)
  if (!root?.contains(range.startContainer) || !root.contains(range.endContainer)) return
  const chosen = selection.toString().trim().replace(/\s+/g, ' ')
  if (isEnglish(chosen)) { text.value = chosen; message.value = '' } else { close() }
}
function clickPhrase(event) {
  if (!frontmatter.value.listen || !supported.value || !window.getSelection()?.isCollapsed) return
  const strong = event.target.closest?.('.vp-doc strong')
  if (!strong || strong.closest('a, button')) return
  const chosen = strong.textContent.replace(/\s*✅\s*$/, '').trim()
  if (isEnglish(chosen)) { text.value = chosen; speak() }
}
function stop() {
  revision++
  if (supported.value) window.speechSynthesis.cancel()
  speaking.value = false
  utterance = undefined
}
function speak() {
  if (!text.value || !supported.value) return
  stop()
  const current = revision
  utterance = new SpeechSynthesisUtterance(text.value.replace(/\s*·\s*/g, ', '))
  const voices = window.speechSynthesis.getVoices()
  const preferredLang = frontmatter.value.listeningLang || 'en-CA'
  const voice = voices.find(v => v.lang === preferredLang) || voices.find(v => v.lang === 'en-US') || voices.find(v => v.lang.startsWith('en'))
  utterance.lang = voice?.lang || 'en-US'
  if (voice) utterance.voice = voice
  utterance.rate = Number(rate.value)
  utterance.onend = () => { if (current === revision) speaking.value = false }
  utterance.onerror = event => {
    if (current !== revision) return
    speaking.value = false
    if (!['canceled', 'interrupted'].includes(event.error)) message.value = '음성 재생이 지원되지 않거나 영어 음성이 없습니다. 원본 영상 링크를 이용해주세요.'
  }
  message.value = ''
  speaking.value = true
  window.speechSynthesis.speak(utterance)
}
function close() { stop(); text.value = ''; message.value = '' }
onMounted(() => {
  supported.value = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window
  document.addEventListener('selectionchange', capture)
  document.addEventListener('click', clickPhrase)
})
watch(() => page.value.relativePath, close)
onBeforeUnmount(() => {
  stop()
  document.removeEventListener('selectionchange', capture)
  document.removeEventListener('click', clickPhrase)
})
</script>

<template>
  <div v-if="frontmatter.listen" class="listening-hint">
    <span v-if="supported">굵은 영어 표현을 누르거나, 영어 단어·문장을 선택한 뒤 듣기를 누르세요.</span>
    <span v-else>음성 읽기는 지원되는 브라우저에서 사용할 수 있습니다.</span>
  </div>
  <aside v-if="frontmatter.listen && supported && text" class="listening-panel" aria-label="영어 발음 듣기">
    <p class="selected-text">{{ text }}</p>
    <div class="controls">
      <button type="button" @click="speak">{{ speaking ? '다시 듣기' : '🔊 듣기' }}</button>
      <label>속도
        <select v-model="rate" @change="stop">
          <option :value="0.7">느리게</option><option :value="0.85">조금 느리게</option><option :value="1">보통</option>
        </select>
      </label>
      <button type="button" @click="stop">멈추기</button>
      <button type="button" @click="close" aria-label="발음 듣기 닫기">닫기</button>
    </div>
    <p v-if="message" role="status">{{ message }}</p>
    <small>기기의 영어 음성 · 원본 화자와 다를 수 있어요.</small>
  </aside>
</template>

<style scoped>
.listening-hint { margin: 16px 0; font-size: 13px; color: var(--vp-c-text-2); }
.listening-panel { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 100; width: min(560px, calc(100vw - 24px)); max-height: 40vh; overflow: auto; padding: 14px 16px; background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 12px; box-shadow: 0 6px 24px #0002; }
.selected-text { margin: 0 0 10px; font-size: 15px; max-height: 72px; overflow: auto; }
.controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 13px; }
button, select { padding: 4px 8px; border: 1px solid var(--vp-c-divider); border-radius: 6px; cursor: pointer; background: var(--vp-c-bg-soft); }
button:focus-visible, select:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px; }
small { display: block; margin-top: 8px; color: var(--vp-c-text-2); font-size: 11px; }
</style>
