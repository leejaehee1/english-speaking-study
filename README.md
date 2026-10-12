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
