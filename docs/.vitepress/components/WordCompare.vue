<script setup>
import { ref, onMounted } from 'vue'

const query = ref('glove, globe')
const rate = ref(0.85)
const useDictAudio = ref(true)
const items = ref([])
const activeWord = ref('')
const sequencePlaying = ref(false)

const PRESETS = [
  { label: 'glove vs. globe (글러브/지구본)', words: 'glove, globe' },
  { label: 'phase vs. phrase (단계/구문)', words: 'phase, phrase' },
  { label: 'chill vs. chilly (식히다/쌀쌀한)', words: 'chill, chilly' },
  { label: 'bad vs. bed (나쁜/침대)', words: 'bad, bed' },
  { label: 'cap vs. cup (모자/컵)', words: 'cap, cup' },
  { label: 'work vs. walk (일하다/걷다)', words: 'work, walk' },
  { label: 'sheet vs. sit (시트/앉다)', words: 'sheet, sit' },
  { label: 'fool vs. full (바보/가득 찬)', words: 'fool, full' },
  { label: 'desert vs. dessert (사막/디저트)', words: 'desert, dessert' },
  { label: 'though vs. thought vs. through', words: 'though, thought, through' }
]

const POS_KO = {
  noun: '명', verb: '동', adjective: '형', adverb: '부',
  pronoun: '대', preposition: '전', conjunction: '접', interjection: '감'
}

const audioMap = {}
const cacheMap = {}

function extractIpa(data) {
  if (!Array.isArray(data)) return ''
  for (const entry of data) {
    if (Array.isArray(entry.phonetics)) {
      const us = entry.phonetics.find(p => p.text && /-us\.mp3$/i.test(p.audio || ''))
      if (us?.text) return us.text
      const anyText = entry.phonetics.find(p => p.text)
      if (anyText?.text) return anyText.text
    }
    if (entry.phonetic) return entry.phonetic
  }
  return ''
}

function speakTts(word) {
  return new Promise(resolve => {
    if (!('speechSynthesis' in window)) return resolve()
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(word)
    const voices = window.speechSynthesis.getVoices()
    const voice =
      voices.find(v => v.lang === 'en-US' && /Samantha|Google US|Ava|Alex/i.test(v.name)) ||
      voices.find(v => v.lang === 'en-US') ||
      voices.find(v => v.lang.startsWith('en'))
    if (voice) u.voice = voice
    u.lang = voice?.lang || 'en-US'
    u.rate = Number(rate.value)
    u.onend = () => resolve()
    u.onerror = () => resolve()
    window.speechSynthesis.speak(u)
  })
}

async function playSingle(word) {
  activeWord.value = word
  const key = word.toLowerCase()
  const a = audioMap[key]
  if (useDictAudio.value && a && Number(rate.value) === 1) {
    window.speechSynthesis?.cancel()
    try {
      a.currentTime = 0
      await a.play()
      await new Promise(res => {
        a.onended = res
        a.onerror = res
      })
      activeWord.value = ''
      return
    } catch {
      // fallback to TTS
    }
  }
  await speakTts(word)
  activeWord.value = ''
}

async function playSequence() {
  if (!items.value.length || sequencePlaying.value) return
  sequencePlaying.value = true
  for (const item of items.value) {
    if (!sequencePlaying.value) break
    await playSingle(item.word)
    await new Promise(r => setTimeout(r, 420))
  }
  sequencePlaying.value = false
  activeWord.value = ''
}

async function fetchWordDetails(item) {
  const key = item.word.toLowerCase()
  if (cacheMap[key]) {
    Object.assign(item, cacheMap[key])
    return
  }
  // 1. Dictionary API (IPA + audio + English def)
  const dictPromise = (async () => {
    try {
      const res = await fetch('https://api.dictionaryapi.dev/api/v2/entries/en/' + encodeURIComponent(key))
      if (!res.ok) return
      const data = await res.json()
      const ipa = extractIpa(data)
      if (ipa) item.ipa = ipa
      const phonetics = Array.isArray(data) ? data.flatMap(d => d.phonetics || []) : []
      const pick = phonetics.find(p => p.audio && /-us\.mp3$/i.test(p.audio)) || phonetics.find(p => p.audio)
      if (pick?.audio) {
        const audio = new Audio(pick.audio)
        audio.preload = 'auto'
        audioMap[key] = audio
        item.hasAudio = true
      }
      const m = Array.isArray(data) && data[0]?.meanings?.[0]
      const def = m?.definitions?.[0]?.definition
      if (def) item.enDef = `(${m.partOfSpeech}) ${def}`
    } catch {
      // ignore
    }
  })()

  // 2. Korean meaning
  const koPromise = (async () => {
    try {
      const res = await fetch(
        'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ko&dt=t&dt=bd&q=' +
          encodeURIComponent(key)
      )
      if (!res.ok) return
      const d = await res.json()
      const dict = d[1] || []
      if (dict.length) {
        item.ko = dict
          .map(e => `[${POS_KO[e[0]] || e[0]}] ${e[1].slice(0, 4).join(', ')}`)
          .join(' · ')
      } else if (d[0]) {
        item.ko = d[0].map(x => x[0]).join('')
      }
    } catch {
      item.ko = ''
    }
  })()

  await Promise.all([dictPromise, koPromise])
  if (!item.ipa) item.ipa = '(발음기호 조회 없음)'
  item.loading = false
  cacheMap[key] = {
    ipa: item.ipa,
    ko: item.ko,
    enDef: item.enDef,
    hasAudio: item.hasAudio,
    loading: false
  }
}

function compareWords() {
  const tokens =
    query.value
      .split(/[\s,/·|]+/)
      .map(w => w.trim().replace(/^[^A-Za-z]+|[^A-Za-z'’-]+$/g, ''))
      .filter(Boolean) || []

  const unique = []
  const seen = new Set()
  for (const t of tokens) {
    const low = t.toLowerCase()
    if (!seen.has(low)) {
      seen.add(low)
      unique.push(t)
    }
  }

  items.value = unique.map(w => ({
    word: w,
    ipa: '…',
    ko: '뜻 불러오는 중…',
    enDef: '',
    hasAudio: false,
    loading: true
  }))

  items.value.forEach(item => fetchWordDetails(item))
}

function selectPreset(presetWords) {
  query.value = presetWords
  compareWords()
  setTimeout(() => playSequence(), 250)
}

onMounted(() => {
  compareWords()
})
</script>

<template>
  <section class="compare-box" aria-label="단어 발음·발음기호 직접 비교">
    <div class="compare-header">
      <div>
        <h3 class="compare-title">🔤 비교하고 싶은 단어 직접 입력 · 발음 &amp; 발음기호(IPA) 비교</h3>
        <p class="compare-sub">
          비교할 영어 단어들을 쉼표(`,`)나 공백으로 구분해 입력하면 <strong>발음 기호(IPA)</strong>와 <strong>한국어 뜻</strong>을 나란히 보여주고 연속으로 발음을 비교해 줍니다.
        </p>
      </div>
    </div>

    <div class="input-row">
      <input
        v-model="query"
        type="text"
        class="word-input"
        placeholder="예: glove, globe 또는 bad, bed 또는 rotisserie, charcuterie"
        @keydown.enter.prevent="compareWords"
      />
      <button type="button" class="primary-btn" @click="compareWords">발음기호 비교</button>
      <button
        v-if="items.length > 1"
        type="button"
        class="seq-btn"
        :disabled="sequencePlaying"
        @click="playSequence"
      >
        {{ sequencePlaying ? '🔊 연속 재생 중…' : '▶️ 연속 비교 듣기 (A → B)' }}
      </button>
      <label class="rate-label">
        속도
        <select v-model="rate">
          <option :value="0.7">느리게 (0.7x)</option>
          <option :value="0.85">조금 느리게 (0.85x)</option>
          <option :value="1">보통 (1.0x)</option>
        </select>
      </label>
    </div>

    <div class="preset-row">
      <span class="preset-label">추천 비교 세트:</span>
      <button
        v-for="p in PRESETS"
        :key="p.words"
        type="button"
        class="preset-chip"
        @click="selectPreset(p.words)"
      >
        {{ p.label }}
      </button>
    </div>

    <div v-if="items.length" class="cards-grid">
      <div
        v-for="item in items"
        :key="item.word"
        class="word-card"
        :class="{ active: activeWord.toLowerCase() === item.word.toLowerCase() }"
        @click="playSingle(item.word)"
      >
        <div class="card-top">
          <span class="card-word">{{ item.word }}</span>
          <button type="button" class="speak-btn" @click.stop="playSingle(item.word)">
            🔊 듣기
          </button>
        </div>
        <div class="card-ipa">{{ item.ipa }}</div>
        <div v-if="item.ko" class="card-ko">{{ item.ko }}</div>
        <div v-if="item.enDef" class="card-en">{{ item.enDef }}</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.compare-box {
  margin: 18px 0 28px;
  padding: 18px 20px;
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
}
.compare-title {
  margin: 0 0 4px !important;
  font-size: 18px;
  font-weight: 700;
}
.compare-sub {
  margin: 0 0 14px !important;
  font-size: 13.5px;
  color: var(--vp-c-text-2);
}
.input-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}
.word-input {
  flex: 1 1 240px;
  padding: 8px 12px;
  font-size: 15px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
}
.word-input:focus {
  outline: 2px solid var(--vp-c-brand-1);
}
.primary-btn,
.seq-btn {
  padding: 8px 14px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid var(--vp-c-brand-1);
}
.primary-btn {
  background: var(--vp-c-brand-1);
  color: #fff;
}
.seq-btn {
  background: var(--vp-c-bg);
  color: var(--vp-c-brand-1);
}
.rate-label {
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--vp-c-text-2);
}
.rate-label select {
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
}
.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 16px;
}
.preset-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--vp-c-text-2);
}
.preset-chip {
  padding: 3px 9px;
  font-size: 12px;
  border-radius: 999px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  cursor: pointer;
  transition: all 0.15s;
}
.preset-chip:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 12px;
}
.word-card {
  padding: 14px 16px;
  border-radius: 10px;
  background: var(--vp-c-bg);
  border: 1.5px solid var(--vp-c-divider);
  cursor: pointer;
  transition: transform 0.12s, border-color 0.15s, box-shadow 0.15s;
}
.word-card:hover {
  border-color: var(--vp-c-brand-1);
}
.word-card.active {
  border-color: var(--vp-c-brand-1);
  box-shadow: 0 0 0 3px var(--vp-c-brand-soft);
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.card-word {
  font-size: 22px;
  font-weight: 800;
  color: var(--vp-c-text-1);
}
.speak-btn {
  padding: 4px 10px;
  font-size: 12.5px;
  font-weight: 600;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  cursor: pointer;
}
.card-ipa {
  margin-top: 4px;
  font-size: 17px;
  font-weight: 700;
  color: var(--vp-c-brand-1);
  font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
}
.card-ko {
  margin-top: 8px;
  font-size: 13.5px;
  color: var(--vp-c-text-1);
  line-height: 1.45;
}
.card-en {
  margin-top: 4px;
  font-size: 12px;
  color: var(--vp-c-text-2);
  line-height: 1.4;
}
</style>
