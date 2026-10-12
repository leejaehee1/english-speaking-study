import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'ko-KR',
  title: 'English Speaking Study',
  description: '2개월 평일 영어회화 학습 기록과 나만의 표현집',
  base: '/english-speaking-study/',
  themeConfig: {
    nav: [
      { text: '홈', link: '/' },
      { text: '오늘의 기록', link: '/daily/2026-10-12' },
      { text: 'JoyTalk', link: 'https://projects-joytalk.vercel.app/', target: '_blank', rel: 'noopener noreferrer' }
    ],
    sidebar: [
      { text: '매일 기록', items: [
        { text: '오늘의 기록', link: '/daily/2026-10-12' },
        { text: '영어 일기', link: '/diary/' },
        { text: '참조 자료', link: '/references/' },
        { text: '10월 12일 녹음 숙제 · 아침 일상 대화', link: '/references/2026-10-12-morning-conversation' },
        { text: '주간 복습', link: '/review/week-01' }
      ] },
      { text: '표현집', collapsed: true, items: [
        { text: '자주 쓰는 표현', link: '/patterns/useful-expressions' },
        { text: '질문 패턴', link: '/patterns/question-patterns' },
        { text: 'GET', link: '/patterns/get' },
        { text: 'MAKE', link: '/patterns/make' },
        { text: 'HAVE', link: '/patterns/have' },
        { text: 'LET', link: '/patterns/let' }
      ] },
      { text: '발음과 교정', collapsed: true, items: [
        { text: '발음 노트', link: '/pronunciation/pronunciation-notes' },
        { text: '자주 하는 실수', link: '/mistakes/common-mistakes' }
      ] }
    ],
    search: { provider: 'local' },
    outline: { label: '이 페이지', level: [2, 3] },
    docFooter: { prev: '이전', next: '다음' },
    socialLinks: [{ icon: 'github', link: 'https://github.com/leejaehee1/english-speaking-study' }]
  }
})
