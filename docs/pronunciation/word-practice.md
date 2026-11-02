---
title: 단어 비교 · 문장에서 단어 추출 발음 연습
---

<script setup>
import { withBase } from 'vitepress'
</script>

# 단어 직접 비교 · 문장에서 단어 추출 발음 연습

헷갈리는 단어들을 직접 입력해 **발음 기호(IPA)와 원어민 발음을 나란히 비교** 하거나, 아래 추출기에 문장을 붙여 넣어 단어별로 연습할 수 있습니다.

<WordCompare />

---

## 문장에서 단어 일괄 추출기

일기·영작 교정본이나 녹음 대본을 붙여 넣고 **단어 추출** 을 누르세요. 추출된 단어를 누르면 발음 기호와 함께 발음을 들을 수 있습니다.

1. 중복을 제거하고 단어별로 듣고 따라 말합니다.
2. 어려운 단어는 세 번씩 반복합니다.
3. 마지막에는 원래 문장으로 돌아가 자연스럽게 이어 말합니다.

<a :href="withBase('/word.html')" target="_blank" rel="noopener noreferrer">단어 추출기를 새 창에서 크게 열기 ↗</a>

<iframe :src="withBase('/word.html')" title="영어 단어 추출과 발음 연습" style="width:100%; height:900px; border:1px solid var(--vp-c-divider); border-radius:8px; margin-top:16px;"></iframe>

[발음 노트](./pronunciation-notes.md) · [영작 숙제](../writing/index.md) · [영어 일기](../diary/index.md) · [녹음 자료](../references/index.md)
