# 일본 디자인 공모전 (한국어 정리판)

koubo.jp · 登竜門(compe.japandesign.ne.jp)의 일본 디자인 공모전을 모아 한국어로 보여주는 개인용 정적 사이트.

## 구성
- `index.html` — 사이트 (검색·카테고리·출처·관심 대회·학생전용 숨기기·페이지네이션)
- `data.js` — 공모전 데이터 (자동 생성)
- `update.py` — 스크래핑·가공 스크립트 (파이썬 표준 라이브러리만 사용)
- `translations.json` — 제목 한국어 번역 캐시
- `font/` — LINE Seed KR/JP 웹폰트

## 자동 갱신
`.github/workflows/update.yml` 이 매일 09:00(KST) GitHub Actions에서 `update.py`를 실행해
`data.js`를 갱신·커밋합니다. GitHub Pages가 자동 반영합니다.

수동 실행: 로컬에서 `python3 update.py`, 또는 Actions 탭에서 "Run workflow".

## 배포
GitHub Pages — Settings → Pages → Deploy from a branch → `main` / `(root)`.
