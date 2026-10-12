# English Speaking Study

**밴쿠버에서 쉬운 일상 대화를 편하게 하기 위한 2개월 평일 영어회화 기록.**

[학습 사이트](https://leejaehee1.github.io/english-speaking-study/) · [JoyTalk](https://projects-joytalk.vercel.app/)

## 매일 할 일

1. 표현 3개를 내 상황으로 바꿔 말하기
2. 노트 한 페이지 정도를 원어민 음성처럼 녹음해 **자정까지 카카오톡 제출**
3. 영어 일기 작성 → 교정 → **공책에 필사**

녹음과 필사 내용은 달라도 됩니다. 녹음 파일은 따로 보관하지 않고 Daily에 제출·필사 완료 여부만 남깁니다.

## 기록 위치

- [Daily](docs/daily/2026-10-12.md): 숙제 체크와 짧은 메모
- [영작](docs/writing/index.md): 문제·내 답안·첨삭
- [일기](docs/diary/index.md): 내가 쓴 글과 교정본
- [참조 자료](docs/references/index.md): 원어민 스크립트·음성 출처
- [표현집](docs/patterns/useful-expressions.md): 다시 쓸 표현
- [주간 복습](docs/review/week-01.md): 금요일에 확인할 내용

새 기록은 기존 양식을 복사하고, 각 목록과 `docs/.vitepress/config.mts`에 링크를 추가합니다.

## 발음 듣기

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
