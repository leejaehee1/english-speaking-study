import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'ko-KR',
  title: 'English Speaking Study',
  description: '2개월 평일 영어회화 학습 기록과 나만의 표현집',
  base: '/english-speaking-study/',
  themeConfig: {
    nav: [
      { text: '홈', link: '/' },
      { text: '학습 달력', link: '/calendar' },
      { text: '오늘의 기록', link: '/daily/2026-10-15' },
      { text: 'JoyTalk', link: 'https://projects-joytalk.vercel.app/', target: '_blank', rel: 'noopener noreferrer' }
    ],
    sidebar: [
      { text: '학습 가이드', collapsed: true, items: [
        { text: '영어 수준과 학습 시간', link: '/guides/cefr-levels' }
      ] },
      { text: '수업 기록', collapsed: true, items: [
        { text: '10월 15일 · 시제·생활 표현과 직업', link: '/daily/2026-10-15' },
        { text: '10월 14일 · 질문 패턴과 음식 표현', link: '/daily/2026-10-14' },
        { text: '10월 13일 · 여행과 표현', link: '/daily/2026-10-13' },
        { text: '10월 12일', link: '/daily/2026-10-12' }
      ] },
      { text: '영어 일기', collapsed: true, items: [
        { text: '일기 목록', link: '/diary/' },
        { text: '10월 14일 · 스터디룸과 듣기 전략', link: '/diary/2026-10-14' },
        { text: '10월 13일 · 비 오는 날', link: '/diary/2026-10-13' },
        { text: '10월 12일 · 공부 시작', link: '/diary/2026-10-12' }
      ] },
      { text: '영작 숙제', collapsed: true, items: [
        { text: '영작 목록', link: '/writing/' },
        { text: '10월 13일 · go through', link: '/writing/2026-10-13-go-through' },
        { text: '10월 12일 · Think', link: '/writing/2026-10-12-think' }
      ] },
      { text: '녹음 숙제·수업 자료', collapsed: true, items: [
        { text: '자료 목록', link: '/references/' },
        { text: '10월 14일 · 세 토픽 읽기 녹음', link: '/references/2026-10-14-travel-food-reading' },
        { text: '10월 13일 · 습관 대화', link: '/references/2026-10-13-daily-habits' },
        { text: '10월 12일 · 아침 대화', link: '/references/2026-10-12-morning-conversation' },
        { text: '10월 12일 · 코스트코 읽기', link: '/references/2026-10-12-costco-reading' },
        { text: '스크립트 양식', link: '/references/script-template' }
      ] },
      { text: '주간 복습', collapsed: true, items: [
        { text: '1주차 · 10월 12–16일', link: '/review/week-01' }
      ] },
      { text: '표현집', collapsed: true, items: [
        { text: '자주 쓰는 표현', link: '/patterns/useful-expressions' },
        { text: '여행 형용사와 감탄 표현', link: '/patterns/travel-adjectives' },
        { text: '음식 형용사 · 맛과 식감', link: '/patterns/food-adjectives' },
        { text: '음식과 요리 · 재료와 조리', link: '/patterns/food-and-cooking' },
        { text: '질문 패턴', link: '/patterns/question-patterns' },
        { text: '숫자 읽기 · 1부터 1조', link: '/patterns/numbers' },
        { text: 'HAVE', link: '/patterns/have' },
        { text: 'GET', link: '/patterns/get' },
        { text: 'MAKE', link: '/patterns/make' },
        { text: 'TAKE', link: '/patterns/take' },
        { text: 'DO', link: '/patterns/do' },
        { text: 'LET', link: '/patterns/let' },
        { text: 'GIVE', link: '/patterns/give' },
        { text: 'WORK', link: '/patterns/work' },
        { text: 'KEEP', link: '/patterns/keep' },
        { text: 'GO', link: '/patterns/go' }
      ] },
      { text: '발음과 교정', collapsed: true, items: [
        { text: '발음 노트', link: '/pronunciation/pronunciation-notes' },
        { text: '모음 음소 · 여덟 가지 소리', link: '/pronunciation/vowel-phonemes' },
        { text: '자음 음소 · B/P, D/T, G/K, V/F, S/Z, J/CH', link: '/pronunciation/consonant-phonemes' },
        { text: '단어 추출 · 발음 연습', link: '/pronunciation/word-practice' },
        { text: '아침 회화 전 · 5분 발음 연습', link: '/pronunciation/morning-practice' },
        { text: '자주 하는 실수', link: '/mistakes/common-mistakes' }
      ] }
    ],
    search: { provider: 'local' },
    outline: { label: '이 페이지', level: [2, 3] },
    docFooter: { prev: '이전', next: '다음' },
    socialLinks: [{ icon: 'github', link: 'https://github.com/leejaehee1/english-speaking-study' }]
  }
})
