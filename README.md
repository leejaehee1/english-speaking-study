# English Speaking Study

2개월 동안 평일 영어회화를 연습하고, 필요한 표현과 숙제를 기록하는 VitePress 학습 사이트입니다.

## 학습 목표

**외국, 특히 밴쿠버에서 일상생활의 쉬운 대화를 편하게 주고받기.**

- 카페·식당에서 주문하고 원하는 것을 요청하기
- 장을 보며 물건 위치와 가격 묻기
- 길·버스·교통편을 묻고 들은 내용 확인하기
- 이웃과 날씨·주말·취미에 관해 이야기하기
- 못 알아들으면 다시 묻고, 다른 표현으로 대화 이어가기

확인 기준은 익숙한 상황에서 노트를 보지 않고 질문·답변·추가 질문을 3–5번 주고받는 것입니다.

## 바로 보기

- [학습 안내](docs/index.md)
- [Daily · 2026-10-12](docs/daily/2026-10-12.md)
- [영어 일기](docs/diary/index.md)
- [원어민 참조 자료](docs/references/index.md)
- [자주 쓰는 표현](docs/patterns/useful-expressions.md)
- [Week 1 Review](docs/review/week-01.md)
- [JoyTalk](https://projects-joytalk.vercel.app/)

## 숙제 방식

### 녹음 · 당일 자정까지 카카오톡 제출

노트 한 페이지 정도를 원어민 음성의 발음·강세·리듬에 최대한 가깝게 연습하고 녹음해 제출합니다.

Daily에는 참조 스크립트, 원어민 음성 출처·구간, 연습 범위, 제출 여부, 다음에 고칠 발음 1개를 남깁니다. 녹음 파일은 사이트나 저장소에 따로 보관하지 않습니다.

### 필사 · 공책에 작성

기본 흐름은 **영어 일기 작성 → 문장 교정 → 교정된 일기를 공책에 필사**입니다. 참조 스크립트나 다른 글을 필사해도 됩니다.

Daily에는 필사 내용, 해당하는 경우 일기 링크, 공책 페이지, 완료 여부를 남깁니다. 녹음과 필사는 같은 내용으로 진행해도 되고 서로 달라도 됩니다.

### 기록하는 곳

- **사이트**: 일기, 참조 자료, 표현집, 숙제 체크와 복습 기록
- **공책**: 손으로 쓰는 필사
- **카카오톡**: 녹음 숙제 제출

## 평일 학습 루틴

기본 연습은 하루 25분, 기록은 5분 이내로 간단하게 유지합니다. 녹음·필사 숙제에 필요한 시간은 분량에 맞춰 별도로 확보합니다.

1. 어제 표현 3개를 보지 않고 말하기 · 5분
2. 오늘 패턴으로 내 문장 3개 만들기 · 10분
3. 원어민 음성을 짧게 따라 말하기 · 5분
4. Daily 기록과 교정 · 5분

다음 날 짧게 복습하고, 금요일에는 노트를 가리고 말하며 숙제와 반복 실수를 돌아봅니다. 주말은 선택 복습입니다.

## 2개월 학습 방향

- **1–2주**: 자기소개·인사·카페 주문, GET / MAKE / HAVE / LET
- **3–4주**: 장보기·길 묻기·버스 이용, 들은 내용 확인하기
- **5–6주**: 날씨·주말·취미 대화, 간단한 예약과 요청하기
- **7–8주**: 밴쿠버 생활 상황 역할극, 추가 질문으로 대화 이어가기, 반복 실수 복습

매주 한 상황을 정해 두 역할을 번갈아 연습합니다. 원어민 스크립트를 따라 읽는 연습과 함께, 문장 없이 직접 답하는 연습도 합니다.

## 문서 구조

```text
english-speaking-study/
├── docs/
│   ├── index.md                      # 학습 안내와 링크
│   ├── daily/2026-10-12.md            # 하루 기록과 숙제 체크
│   ├── diary/                        # 직접 쓴 일기와 교정본
│   │   ├── index.md
│   │   └── 2026-10-12.md              # 첫 일기 작성 양식
│   ├── references/                   # 원어민 스크립트·음성 출처
│   │   ├── index.md
│   │   └── script-template.md         # 참조 자료 작성 양식
│   ├── patterns/
│   │   ├── get.md
│   │   ├── make.md
│   │   ├── have.md
│   │   ├── let.md
│   │   ├── question-patterns.md
│   │   └── useful-expressions.md
│   ├── pronunciation/pronunciation-notes.md
│   ├── mistakes/common-mistakes.md
│   ├── review/week-01.md
│   └── .vitepress/config.mts          # 메뉴·사이드바·검색 설정
├── package.json
└── package-lock.json
```

**매일 기록은 Daily에, 다시 쓸 표현은 patterns에, 반복 오류는 mistakes에 모읍니다.** 일기와 참조 자료는 따로 관리하고 Daily에서 연결합니다.

## 새 기록 추가하기

1. [Daily 양식](docs/daily/2026-10-12.md)을 참고해 새 날짜 파일을 만듭니다. 첫날 표현은 그날 배운 내용으로 바꿉니다.
2. [일기 양식](docs/diary/2026-10-12.md)과 [참조 자료 양식](docs/references/script-template.md)을 필요에 따라 복사해 작성합니다.
3. 홈, 일기·참조 자료 목록, `docs/.vitepress/config.mts`의 해당 메뉴와 사이드바에 새 페이지 링크를 추가합니다. Daily 메뉴가 새 날짜를 가리키도록 바꿉니다.
4. Daily에서 숙제에 사용한 자료를 연결하고, 카카오톡 제출과 공책 필사 완료를 각각 기록합니다.
5. 금요일에 [주간 복습 양식](docs/review/week-01.md)을 참고해 새 주차 파일을 만들고 홈·복습 메뉴·사이드바에 연결합니다.
6. `npm run docs:build`로 빌드와 문서 링크 오류를 확인합니다.

일기와 참조 자료의 초기 페이지는 작성 양식입니다. 실제 경험, 원어민 음성 출처, 숙제 완료 여부는 직접 채웁니다.

## 로컬 실행

Node.js 20 이상과 npm을 사용합니다.

```sh
npm ci
npm run docs:dev
```

실행 후 표시되는 주소의 `/english-speaking-study/` 경로로 접속합니다.

빌드와 결과 미리보기:

```sh
npm run docs:build
npm run docs:preview
```

빌드 결과는 `docs/.vitepress/dist/`에 생성됩니다. VitePress 기본 테마의 상단 메뉴, 사이드바, 로컬 검색을 사용합니다.

## 배포 경로

`docs/.vitepress/config.mts`의 `base`는 GitHub Pages 저장소 경로인 `/english-speaking-study/`로 설정되어 있습니다. 루트 도메인에 배포할 경우 `/`로 변경합니다.

`.github/workflows/deploy.yml`이 `main` 브랜치에 올라온 변경 사항을 빌드하고 GitHub Pages에 배포합니다. 저장소 Settings → Pages → Source는 **GitHub Actions**로 설정합니다.

- [학습 사이트](https://leejaehee1.github.io/english-speaking-study/)
- [배포 상태](https://github.com/leejaehee1/english-speaking-study/actions)
