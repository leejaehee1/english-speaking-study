<script setup>
import { computed, ref } from 'vue'
import { withBase } from 'vitepress'

const sources = import.meta.glob(['../../daily/*.md', '../../diary/*.md', '../../writing/*.md', '../../references/*.md'], { query: '?raw', import: 'default', eager: true })
const kinds = { daily: '수업', diary: '일기', writing: '영작', references: '자료' }
const records = Object.entries(sources).flatMap(([path, content]) => {
  const match = path.match(/\/([^/]+)\/(2026-\d{2}-\d{2})[^/]*\.md$/)
  if (!match) return []
  const [, category, date] = match
  const title = content.match(/^# (.+)$/m)?.[1] || date
  return [{ date, category, title, link: '/' + path.replace('../../', '').replace(/\.md$/, '') }]
}).sort((a, b) => a.link.localeCompare(b.link))
const selected = ref(records.some(r => r.date === '2026-10-13') ? '2026-10-13' : '')
const chosen = computed(() => records.filter(r => r.date === selected.value))
const weekdays = ['월', '화', '수', '목', '금', '토', '일']
const months = [10, 11].map(month => {
  const offset = (new Date(2026, month - 1, 1).getDay() + 6) % 7
  const count = new Date(2026, month, 0).getDate()
  const size = Math.ceil((offset + count) / 7) * 7
  return { month, cells: Array.from({ length: size }, (_, i) => {
    const day = i - offset + 1
    if (day < 1 || day > count) return null
    const date = `2026-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const entries = records.filter(r => r.date === date)
    return { day, date, entries, labels: [...new Set(entries.map(r => kinds[r.category]))] }
  }) }
})
</script>

<template>
  <div class="study-calendar">
    <p class="legend">날짜를 누르면 그날의 자료를 볼 수 있어요. 색이 있는 날짜에는 학습 기록이 있습니다.</p>
    <div class="months">
      <section v-for="month in months" :key="month.month" :aria-label="`2026년 ${month.month}월`">
        <h2>2026년 {{ month.month }}월</h2>
        <div class="calendar-grid">
          <span v-for="(weekday, i) in weekdays" :key="weekday" class="weekday" :class="{ weekend: i > 4 }">{{ weekday }}</span>
          <template v-for="(cell, i) in month.cells" :key="i">
            <button v-if="cell" type="button" class="day" :class="{ recorded: cell.entries.length, selected: selected === cell.date, weekend: i % 7 > 4 }" :aria-label="`${cell.date}: ${cell.labels.join(', ') || '기록 없음'}`" :aria-pressed="selected === cell.date" @click="selected = cell.date">
              <span class="date-number">{{ cell.day }}</span>
              <span v-if="cell.labels.length" class="day-labels">{{ cell.labels.join(' · ') }}</span>
            </button>
            <span v-else class="blank" aria-hidden="true"></span>
          </template>
        </div>
      </section>
    </div>
    <section class="day-detail" aria-live="polite" aria-atomic="true">
      <h2>{{ selected ? selected.replaceAll('-', '.') : '날짜를 선택하세요' }}</h2>
      <ul v-if="chosen.length" class="records">
        <li v-for="record in chosen" :key="record.link"><span class="kind">{{ kinds[record.category] }}</span><a :href="withBase(record.link)">{{ record.title }}</a></li>
      </ul>
      <p v-else>이 날짜에는 아직 등록된 학습 기록이 없습니다.</p>
    </section>
  </div>
</template>

<style scoped>
.legend { color: var(--vp-c-text-2); font-size: 14px; }
.months { display: grid; gap: 24px; }
h2 { margin: 16px 0; border: 0; padding: 0; font-size: 20px; }
.calendar-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px; }
.weekday { text-align: center; color: var(--vp-c-text-2); font-size: 13px; padding: 4px; }
.day, .blank { min-height: 72px; }
.day { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; padding: 8px; border: 1px solid var(--vp-c-divider); border-radius: 6px; background: var(--vp-c-bg); text-align: left; cursor: pointer; color: var(--vp-c-text-1); }
.weekend { color: var(--vp-c-text-3); }
.recorded { background: var(--vp-c-brand-soft); }
.selected { outline: 2px solid var(--vp-c-brand-1); outline-offset: -2px; }
.day:hover { border-color: var(--vp-c-brand-1); }
.day:focus-visible { outline: 3px solid var(--vp-c-brand-1); outline-offset: 2px; }
.date-number { font-size: 16px; font-weight: 600; line-height: 1.3; }
.day-labels { color: var(--vp-c-brand-1); font-size: 11px; line-height: 1.4; overflow-wrap: anywhere; }
.day-detail { margin-top: 28px; border-top: 1px solid var(--vp-c-divider); padding-top: 8px; }
.records { list-style: none; padding: 0; }
.records li { display: flex; gap: 12px; align-items: baseline; padding: 10px 0; }
.kind { color: var(--vp-c-text-2); font-size: 12px; min-width: 30px; }
@media (min-width: 1280px) { .months { grid-template-columns: 1fr 1fr; gap: 20px; } .day { padding: 6px; } }
@media (max-width: 420px) { .day { padding: 5px; min-height: 66px; } .calendar-grid { gap: 3px; } }
</style>
