import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'ko-KR',
  srcExclude: ['public/downloads/**/*.md'],
  title: 'English Speaking Study',
  description: '2개월 평일 영어회화 학습 기록과 나만의 표현집',
  base: '/english-speaking-study/',
  themeConfig: {
    nav: [
      { text: '홈', link: '/' },
      { text: '학습 달력', link: '/calendar' },
      { text: '영화 자막', link: '/movies/' },
      { text: '오늘의 기록', link: '/daily/2026-10-16' },
      { text: 'JoyTalk', link: 'https://projects-joytalk.vercel.app/', target: '_blank', rel: 'noopener noreferrer' }
    ],
    sidebar: [
      { text: '학습 가이드', collapsed: true, items: [
        { text: '영어 수준과 학습 시간', link: '/guides/cefr-levels' },
        { text: '외국어 학습법 · 소리와 표현 쌓기', link: '/guides/language-learning-method' }
      ] },
      { text: '수업 기록', collapsed: true, items: [
        { text: '10월 16일 · 감사·인물과 프로그램 소개', link: '/daily/2026-10-16' },
        { text: '10월 15일 · 시제·생활 표현과 직업', link: '/daily/2026-10-15' },
        { text: '10월 14일 · 질문 패턴과 음식 표현', link: '/daily/2026-10-14' },
        { text: '10월 13일 · 여행과 표현', link: '/daily/2026-10-13' },
        { text: '10월 12일', link: '/daily/2026-10-12' }
      ] },
      { text: '녹음 숙제', collapsed: true, items: [
        { text: '10월 16일 · Learning English 녹음', link: '/references/2026-10-16-english-learning-reading' },
        { text: '10월 15일 · Feelings 녹음', link: '/references/2026-10-15-feelings-reading' },
        { text: '10월 14일 · 세 토픽 읽기 녹음', link: '/references/2026-10-14-travel-food-reading' },
        { text: '10월 13일 · 습관 대화', link: '/references/2026-10-13-daily-habits' },
        { text: '10월 12일 · 아침 대화', link: '/references/2026-10-12-morning-conversation' }
      ] },
      { text: '영어 일기', collapsed: true, items: [
        { text: '10월 16일 · 멋진 하루와 말하기 연습', link: '/diary/2026-10-16' },
        { text: '10월 15일 · 바쁘지만 행복한 하루', link: '/diary/2026-10-15' },
        { text: '10월 14일 · 스터디룸과 듣기 전략', link: '/diary/2026-10-14' },
        { text: '10월 13일 · 비 오는 날', link: '/diary/2026-10-13' },
        { text: '10월 12일 · 공부 시작', link: '/diary/2026-10-12' }
      ] },
      { text: '영작 숙제', collapsed: true, items: [
        { text: '10월 13일 · go through', link: '/writing/2026-10-13-go-through' },
        { text: '10월 12일 · Think', link: '/writing/2026-10-12-think' }
      ] },
      { text: '수업 자료', collapsed: true, items: [
        { text: '10월 19일 · 한국의 술 문화', link: '/patterns/korean-drinking-culture' },
        { text: '10월 19일 · 유튜브 A2-B2 스크립트', link: '/references/everyday-english-full-script' },
        { text: '10월 19일 · 수업 준비', link: '/references/2026-10-19-class-preparation' },
        { text: '10월 12일 · 코스트코 읽기', link: '/references/2026-10-12-costco-reading' }
      ] },
      { text: '주간 복습', collapsed: true, items: [
        { text: '1주차 · 10월 12–16일', link: '/review/week-01' }
      ] },
      { text: '표현집', collapsed: true, items: [
        { text: '자주 쓰는 표현', link: '/patterns/useful-expressions' },
        { text: 'Someone I Admire · 존경하는 사람', link: '/patterns/someone-i-admire' },
        { text: 'Feelings & Emotions · 감정 표현', link: '/patterns/feelings-and-emotions' },
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
        { text: '음소 학습 시리즈 · 소리튠영어', link: '/pronunciation/pronunciation-notes#phoneme-series' },
        { text: '모음 음소 · 여덟 가지 소리', link: '/pronunciation/vowel-phonemes' },
        { text: '자음 음소 · B/P, D/T, G/K, V/F, S/Z, J/CH', link: '/pronunciation/consonant-phonemes' },
        { text: '아침 회화 전 · 5분 발음 연습', link: '/pronunciation/morning-practice' },
        { text: '단어 추출 · 발음 연습', link: '/pronunciation/word-practice' }
      ] },
      { text: '영화 자막', collapsed: true, items: [
        { text: '영화별 목록', link: '/movies/' },
        { text: 'Greenland 2 · 시청용', link: '/movies/greenland-2' },
        { text: 'Greenland 2 · 상세 복습', link: '/movies/greenland-2-review' },
        { text: '날짜별 학습 양식', link: '/movies/study-template' }
      ] },
    ],
    search: { provider: 'local' },
    outline: { label: '이 페이지', level: [2, 3] },
    docFooter: { prev: '이전', next: '다음' },
    socialLinks: [{ icon: 'github', link: 'https://github.com/leejaehee1/english-speaking-study' }]
  }
})
