<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
const supported = ref(false)
const message = ref('')
const sentences = [
  'How old do you think she is?',
  'Do you know how old she is?',
  'What do you think we should do?'
]
onMounted(() => { supported.value = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window })
function stop() { window.speechSynthesis.cancel() }
function speak(text) {
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'en-CA'
  const voices = window.speechSynthesis.getVoices()
  const voice = voices.find(v => v.lang === 'en-CA') || voices.find(v => v.lang.startsWith('en'))
  if (voice) utterance.voice = voice
  utterance.rate = 0.85
  utterance.onerror = () => { message.value = '음성을 재생할 수 없습니다. 위의 원본 영상 링크를 이용해주세요.' }
  message.value = ''
  window.speechSynthesis.speak(utterance)
}
onBeforeUnmount(() => { if (supported.value) window.speechSynthesis.cancel() })
</script>

<template>
  <div v-if="supported">
    <p v-for="sentence in sentences" :key="sentence">
      {{ sentence }} <button type="button" :aria-label="sentence + ' 듣기'" @click="speak(sentence)">듣기</button>
    </p>
    <button type="button" @click="stop">멈추기</button>
    <p v-if="message" role="status">{{ message }}</p>
  </div>
  <p v-else>이 브라우저에서는 음성 읽기를 사용할 수 없습니다. 위의 영상 링크로 들어보세요.</p>
</template>

<style scoped>
button { border: 1px solid var(--vp-c-divider); border-radius: 6px; padding: 2px 10px; color: var(--vp-c-brand-1); cursor: pointer; }
button:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px; }
</style>
