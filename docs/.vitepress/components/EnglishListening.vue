<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useData } from 'vitepress'
const { frontmatter, page } = useData()
const supported = ref(false)
const text = ref('')
const customInput = ref('')
const rate = ref(0.85)
const speaking = ref(false)
const message = ref('')
const wordIpaList = ref([])
const loadingIpa = ref(false)
let utterance
let revision = 0
let ipaRevision = 0

const BUILTIN_IPA = {
  a: '/ə/', an: '/æn/', the: '/ðə/', to: '/tuː/', of: '/ʌv/', in: '/ɪn/', on: '/ɑːn/', at: '/æt/',
  for: '/fɔːr/', with: '/wɪð/', from: '/frʌm/', by: '/baɪ/', about: '/əˈbaʊt/', as: '/æz/',
  into: '/ˈɪn.tuː/', like: '/laɪk/', through: '/θruː/', after: '/ˈæf.tər/', over: '/ˈoʊ.vər/',
  between: '/bɪˈtwiːn/', out: '/aʊt/', against: '/əˈɡenst/', during: '/ˈdʊr.ɪŋ/', without: '/wɪˈðaʊt/',
  before: '/bɪˈfɔːr/', under: '/ˈʌn.dər/', around: '/əˈraʊnd/', among: '/əˈmʌŋ/',
  i: '/aɪ/', you: '/juː/', he: '/hiː/', she: '/ʃiː/', it: '/ɪt/', we: '/wiː/', they: '/ðeɪ/',
  me: '/miː/', him: '/hɪm/', her: '/hɜːr/', us: '/ʌs/', them: '/ðem/',
  my: '/maɪ/', your: '/jʊr/', his: '/hɪz/', our: '/aʊər/', their: '/ðer/',
  this: '/ðɪs/', that: '/ðæt/', these: '/ðiːz/', those: '/ðoʊz/',
  is: '/ɪz/', am: '/æm/', are: '/ɑːr/', was: '/wʌz/', were: '/wɜːr/', be: '/biː/', been: '/bɪn/',
  have: '/hæv/', has: '/hæz/', had: '/hæd/', do: '/duː/', does: '/dʌz/', did: '/dɪd/',
  can: '/kæn/', could: '/kʊd/', will: '/wɪl/', would: '/wʊd/', should: '/ʃʊd/', may: '/meɪ/', might: '/maɪt/', must: '/mʌst/',
  not: '/nɑːt/', no: '/noʊ/', yes: '/jes/', so: '/soʊ/', but: '/bʌt/', and: '/ænd/', or: '/ɔːr/', if: '/ɪf/',
  because: '/bɪˈkɔːz/', while: '/waɪl/', unless: '/ənˈles/', until: '/ənˈtɪl/',
  what: '/wʌt/', where: '/wer/', when: '/wen/', why: '/waɪ/', how: '/haʊ/', who: '/huː/', which: '/wɪtʃ/',
  "i'm": '/aɪm/', "you're": '/jʊr/', "he's": '/hiːz/', "she's": '/ʃiːz/', "it's": '/ɪts/', "we're": '/wɪr/', "they're": '/ðer/',
  "don't": '/doʊnt/', "doesn't": '/ˈdʌz.ənt/', "didn't": '/ˈdɪd.ənt/', "can't": '/kænt/', "couldn't": '/ˈkʊd.ənt/',
  "won't": '/woʊnt/', "wouldn't": '/ˈwʊd.ənt/', "isn't": '/ˈɪz.ənt/', "aren't": '/ɑːrnt/', "wasn't": '/ˈwʌz.ənt/', "weren't": '/wɜːrnt/',
  "i'll": '/aɪl/', "you'll": '/juːl/', "we'll": '/wiːl/', "i've": '/aɪv/', "you've": '/juːv/', "you'd": '/juːd/',
  "here's": '/hɪrz/', "there's": '/ðerz/', "what's": '/wʌts/', "that's": '/ðæts/', "let's": '/lets/',
  costco: '/ˈkɑːst.koʊ/', "costco's": '/ˈkɑːst.koʊz/', kirkland: '/ˈkɜːr.klənd/', rotisserie: '/roʊˈtɪs.ər.i/',
  duracell: '/ˈdʊr.ə.sel/', charcuterie: '/ʃɑːrˌkuː.təˈriː/', ibuprofen: '/ˌaɪ.bjuːˈproʊ.fən/',
  oregano: '/əˈreɡ.ə.noʊ/', bogo: '/ˈboʊ.ɡoʊ/', condiments: '/ˈkɑːn.dɪ.mənts/', pesto: '/ˈpes.toʊ/',
  mayo: '/ˈmeɪ.oʊ/', veggies: '/ˈvedʒ.iz/', meds: '/medz/', evoo: '/ˌiː.viː.oʊˈoʊ/',
  dakgalbi: '/ˌdɑːk.ɡɑːlˈbiː/', soju: '/ˈsoʊ.dʒuː/', tiramisu: '/ˌtɪr.ə.mɪˈsuː/', risotto: '/rɪˈzɔː.toʊ/',
  parmesan: '/ˈpɑːr.mə.zɑːn/', cilantro: '/sɪˈlɑːn.troʊ/', coriander: '/ˈkɔːr.i.æn.dər/', durian: '/ˈdʊr.i.ən/'
}

const ipaCache = { ...BUILTIN_IPA }

function extractIpaFromApiData(data) {
  if (!Array.isArray(data)) return ''
  for (const entry of data) {
    if (entry.phonetic) return entry.phonetic
    if (Array.isArray(entry.phonetics)) {
      const us = entry.phonetics.find(p => p.text && /-us\.mp3$/i.test(p.audio || ''))
      if (us?.text) return us.text
      const anyText = entry.phonetics.find(p => p.text)
      if (anyText?.text) return anyText.text
    }
  }
  return ''
}

function getCandidateForms(word) {
  const w = word.toLowerCase().replace(/^['’]+|['’]+$/g, '')
  const candidates = [w]
  if (w.endsWith("'s") || w.endsWith("’s")) candidates.push(w.slice(0, -2))
  if (w.endsWith('ies') && w.length > 4) candidates.push(w.slice(0, -3) + 'y')
  if (w.endsWith('es') && w.length > 3) candidates.push(w.slice(0, -2), w.slice(0, -1))
  if (w.endsWith('s') && w.length > 3) candidates.push(w.slice(0, -1))
  if (w.endsWith('ing') && w.length > 5) {
    const stem = w.slice(0, -3)
    candidates.push(stem, stem + 'e')
    if (stem.length > 2 && stem[stem.length - 1] === stem[stem.length - 2]) {
      candidates.push(stem.slice(0, -1))
    }
  }
  if (w.endsWith('ed') && w.length > 4) {
    const stem = w.slice(0, -2)
    candidates.push(stem, w.slice(0, -1))
    if (stem.endsWith('i')) candidates.push(stem.slice(0, -1) + 'y')
  }
  return [...new Set(candidates)]
}

async function fetchWordIpa(rawWord) {
  const key = rawWord.toLowerCase().replace(/’/g, "'")
  if (key in ipaCache) return ipaCache[key]
  const candidates = getCandidateForms(key)
  for (const c of candidates) {
    if (c in ipaCache && ipaCache[c]) {
      ipaCache[key] = ipaCache[c]
      return ipaCache[key]
    }
  }
  for (const c of candidates) {
    try {
      const res = await fetch('https://api.dictionaryapi.dev/api/v2/entries/en/' + encodeURIComponent(c))
      if (!res.ok) continue
      const data = await res.json()
      const ipa = extractIpaFromApiData(data)
      if (ipa) {
        ipaCache[c] = ipa
        ipaCache[key] = ipa
        return ipa
      }
    } catch {
      // ignore network error
    }
  }
  ipaCache[key] = ''
  return ''
}

async function updatePhonetics(inputText) {
  const currentIpaRev = ++ipaRevision
  if (!inputText) {
    wordIpaList.value = []
    loadingIpa.value = false
    return
  }
  const tokens = inputText.match(/[A-Za-z]+(?:['’-][A-Za-z]+)*/g) || []
  // 최대 30단어까지 표시 (중복은 순서 유지하되 한 번만 표시)
  const seen = new Set()
  const uniqueTokens = []
  for (const t of tokens) {
    const lower = t.toLowerCase()
    if (!seen.has(lower)) {
      seen.add(lower)
      uniqueTokens.push(t)
    }
    if (uniqueTokens.length >= 30) break
  }
  wordIpaList.value = uniqueTokens.map(w => ({
    word: w,
    ipa: ipaCache[w.toLowerCase().replace(/’/g, "'")] || ''
  }))
  loadingIpa.value = true
  await Promise.all(
    wordIpaList.value.map(async (item, idx) => {
      if (item.ipa) return
      const ipa = await fetchWordIpa(item.word)
      if (currentIpaRev === ipaRevision && wordIpaList.value[idx]) {
        wordIpaList.value[idx].ipa = ipa
      }
    })
  )
  if (currentIpaRev === ipaRevision) {
    loadingIpa.value = false
  }
}

const isEnglish = value => /[a-z]/i.test(value) && !/[^\x00-\x7F\u00A0\u00B7\u00C0-\u00FF\u2010-\u201F\u2026]/.test(value) && value.length <= 600
function capture() {
  if (!frontmatter.value.listen || !supported.value) return
  const selection = window.getSelection()
  if (!selection || selection.isCollapsed || !selection.rangeCount) return
  const root = document.querySelector('.vp-doc')
  const range = selection.getRangeAt(0)
  if (!root?.contains(range.startContainer) || !root.contains(range.endContainer)) return
  const chosen = selection.toString().trim().replace(/\s+/g, ' ')
  if (isEnglish(chosen)) {
    text.value = chosen
    message.value = ''
    updatePhonetics(chosen)
  } else {
    close()
  }
}
function clickPhrase(event) {
  if (!frontmatter.value.listen || !supported.value || !window.getSelection()?.isCollapsed) return
  const strong = event.target.closest?.('.vp-doc strong') || event.target.closest?.('.vp-doc td')?.querySelector('strong')
  if (!strong || strong.closest('a, button')) return
  const chosen = strong.textContent.replace(/\s*✅\s*$/, '').trim()
  if (isEnglish(chosen)) {
    text.value = chosen
    updatePhonetics(chosen)
    speak()
  }
}
function stop() {
  revision++
  if (supported.value) window.speechSynthesis.cancel()
  speaking.value = false
  utterance = undefined
}
function speakCustom(targetText) {
  if (!targetText || !supported.value) return
  stop()
  const current = revision
  utterance = new SpeechSynthesisUtterance(targetText.replace(/\s*·\s*/g, ', '))
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
function speak() {
  speakCustom(text.value)
}
function submitCustomCompare() {
  const cleaned = customInput.value.trim().replace(/\s+/g, ' ')
  if (!cleaned) return
  text.value = cleaned
  message.value = ''
  updatePhonetics(cleaned)
  speakCustom(cleaned)
}
function close() {
  stop()
  text.value = ''
  wordIpaList.value = []
  message.value = ''
}
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
    <div v-if="supported" class="hint-bar">
      <span>굵은 영어 표현을 누르거나, 비교하고 싶은 단어를 직접 입력해 발음·발음기호(IPA)를 확인하세요.</span>
      <form class="quick-compare-form" @submit.prevent="submitCustomCompare">
        <input
          v-model="customInput"
          type="text"
          class="quick-compare-input"
          placeholder="비교할 단어 입력 (예: glove, globe)"
          aria-label="비교할 영어 단어 직접 입력"
        />
        <button type="submit" class="quick-compare-btn">🔊 발음·기호 비교</button>
      </form>
    </div>
    <span v-else>음성 읽기는 지원되는 브라우저에서 사용할 수 있습니다.</span>
  </div>
  <aside v-if="frontmatter.listen && supported && text" class="listening-panel" aria-label="영어 발음 듣기">
    <p class="selected-text">{{ text }}</p>
    <div v-if="wordIpaList.length" class="ipa-container" aria-label="단어별 발음 기호">
      <button
        v-for="item in wordIpaList"
        :key="item.word"
        type="button"
        class="ipa-chip"
        :title="`${item.word} 단어만 발음 듣기`"
        @click="speakCustom(item.word)"
      >
        <span class="ipa-word">{{ item.word }}</span>
        <span v-if="item.ipa" class="ipa-symbol">{{ item.ipa }}</span>
      </button>
    </div>
    <div class="controls">
      <button type="button" @click="speak">{{ speaking ? '다시 듣기' : '🔊 전체 듣기' }}</button>
      <label>속도
        <select v-model="rate" @change="stop">
          <option :value="0.7">느리게</option><option :value="0.85">조금 느리게</option><option :value="1">보통</option>
        </select>
      </label>
      <button type="button" @click="stop">멈추기</button>
      <button type="button" @click="close" aria-label="발음 듣기 닫기">닫기</button>
    </div>
    <p v-if="message" role="status">{{ message }}</p>
    <small>단어 칩을 누르면 해당 단어만 따로 들을 수 있어요 · 기기의 영어 음성</small>
  </aside>
</template>

<style scoped>
.listening-hint { margin: 16px 0; font-size: 13px; color: var(--vp-c-text-2); }
.hint-bar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 12px; background: var(--vp-c-bg-soft); border: 1px solid var(--vp-c-divider); border-radius: 8px; }
.quick-compare-form { display: flex; align-items: center; gap: 6px; flex: 1 1 260px; max-width: 380px; }
.quick-compare-input { flex: 1; min-width: 140px; padding: 4px 9px; font-size: 13px; border: 1px solid var(--vp-c-divider); border-radius: 6px; background: var(--vp-c-bg); color: var(--vp-c-text-1); }
.quick-compare-input:focus { outline: 2px solid var(--vp-c-brand-1); }
.quick-compare-btn { padding: 4px 10px; font-size: 12.5px; font-weight: 600; white-space: nowrap; background: var(--vp-c-brand-1); color: #fff; border: 1px solid var(--vp-c-brand-1); border-radius: 6px; cursor: pointer; }
.listening-panel { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 100; width: min(620px, calc(100vw - 24px)); max-height: 46vh; overflow: auto; padding: 14px 16px; background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 12px; box-shadow: 0 6px 24px #0002; }
.selected-text { margin: 0 0 8px; font-size: 15px; font-weight: 600; max-height: 68px; overflow: auto; }
.ipa-container { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; max-height: 110px; overflow-y: auto; padding: 6px 8px; background: var(--vp-c-bg-soft); border-radius: 8px; border: 1px solid var(--vp-c-divider); }
.ipa-chip { display: inline-flex; align-items: baseline; gap: 4px; padding: 2px 7px; font-size: 12px; border-radius: 6px; border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); cursor: pointer; transition: border-color 0.15s, background-color 0.15s; }
.ipa-chip:hover { border-color: var(--vp-c-brand-1); background: var(--vp-c-brand-soft); }
.ipa-word { font-weight: 600; color: var(--vp-c-text-1); }
.ipa-symbol { font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; color: var(--vp-c-brand-1); font-size: 12px; }
.controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 13px; }
button, select { padding: 4px 8px; border: 1px solid var(--vp-c-divider); border-radius: 6px; cursor: pointer; background: var(--vp-c-bg-soft); }
button:focus-visible, select:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px; }
small { display: block; margin-top: 8px; color: var(--vp-c-text-2); font-size: 11px; }
</style>
