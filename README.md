# English Speaking Study

**목표: 축적한 영어 지식과 회화 경험을 통합해 밴쿠버 일상에서 안정적으로 대화하고, 여행·음식·일·관심사에 대해 이유와 의견을 덧붙여 대화를 이어가기.**

2개월 동안 평일에 연습합니다. **B1 회화 능력을 안정화하고, 익숙한 주제에서 조건부 B2 수준의 수행**을 목표로 합니다. 핵심 패턴을 안정시킨 뒤 설명·이유·비교·의견으로 확장하며, 준비하지 않은 추가 질문에도 답하는 연습을 합니다. 현재 듣기·말하기를 확인하고 진행 중 점검 결과에 따라 목표 범위를 조정합니다.

[학습 사이트](https://leejaehee1.github.io/english-speaking-study/) · [JoyTalk](https://projects-joytalk.vercel.app/)

## 매일 할 일

1. 표현 3개를 내 상황으로 바꿔 말하기
2. 노트 한 페이지 정도를 원어민 음성처럼 녹음해 **자정까지 카카오톡 제출**
3. 영어 일기 작성 → 교정 → **공책에 필사**

녹음과 필사 내용은 달라도 됩니다. 녹음 파일은 따로 보관하지 않고 Daily에 제출·필사 완료 여부만 남깁니다.

## 기록 위치

- [영화 자막](docs/movies/index.md): 영화별 시청용 표현·상세 복습·시간 보정과 누적 학습

- [Daily](docs/daily/2026-10-16.md): 수업 내용과 이해를 돕는 예문
- [영작](docs/writing/index.md): 문제·내 답안·첨삭
- [일기](docs/diary/index.md): 내가 쓴 글과 교정본
- [녹음 숙제·수업 자료](docs/references/index.md): 녹음용 스크립트·음성 출처와 수업에 활용하는 읽기 자료
- [표현집](docs/patterns/useful-expressions.md): 다시 쓸 표현
- [주간 복습](docs/review/week-01.md): 금요일에 확인할 내용

수업 기록(`docs/daily/`)에는 실제 수업에서 다룬 내용과 이를 설명하는 예문만 정리합니다. 숙제 목록, 제출·필사 안내, 수행 여부, 별도 자가 학습·예습·영작 과제는 포함하지 않습니다. 일기·영작·녹음 숙제·수업 자료는 각 전용 문서에서 관리합니다.

새 기록은 기존 양식을 복사하고, 각 목록과 `docs/.vitepress/config.mts`에 링크를 추가합니다.

## 학습 가이드

- [Claude로 나만의 AI 영어 튜터 만들기](docs/guides/claude-ai-english-tutor.md)

- [외국어 학습법 · 소리와 표현 쌓기](docs/guides/language-learning-method.md)
- [영어 수준과 학습 시간 · CEFR](docs/guides/cefr-levels.md)

## 발음 듣기

**[음소 학습 시리즈 · 주아쌤_소리튠영어](https://www.youtube.com/watch?v=or7k3weRAtI&list=PLJv1Fpdyo3rbXoHAh_SiMdcKKZof0-Iow)** — 발음 연습의 기본 참고 영상·재생목록. [발음 노트](docs/pronunciation/pronunciation-notes.md#phoneme-series)에서 기존 모음·자음 자료와 함께 활용합니다.

표현집·영작·일기·녹음 대본 등에서 굵은 영어 표현을 누르면 발음을 듣습니다. 영어 단어·문장을 선택한 뒤 듣기도 가능합니다. 속도 조절과 멈추기를 지원하며, 기기의 영어 음성을 사용합니다.

새 학습 페이지에 적용하려면 Markdown 맨 위에 `listen: true`를 frontmatter로 추가합니다. 홈·목록·코스트코 읽기 자료에는 적용하지 않았습니다.

## 로컬 실행

Node.js 20 이상에서:

```sh
npm ci
npm run docs:dev
```

표시된 주소의 `/english-speaking-study/`에 접속합니다.

```sh
npm run docs:build
npm run docs:preview
```

## 배포

`main`에 푸시하면 GitHub Actions가 GitHub Pages에 자동 배포합니다.

[배포 상태 확인](https://github.com/leejaehee1/english-speaking-study/actions)
