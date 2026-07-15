# AI 추천 챗봇 — 배포 가이드 (Cloudflare Worker)

브라우저에 API 키를 노출하지 않기 위해, 키를 숨겨주는 작은 서버(Cloudflare Worker)를 하나 띄웁니다. 무료이고 10분이면 됩니다.

## 준비물
1. **Anthropic API 키** — https://console.anthropic.com → API Keys → Create Key (`sk-ant-...`)
   - 결제수단 등록 필요. 이 용도는 매우 저렴합니다(추천 1회 ≈ 수 원).
2. **Cloudflare 계정** — https://dash.cloudflare.com (무료 가입)

## 1) Worker 만들기
1. Cloudflare 대시보드 → **Compute (Workers)** → **Create** → **Create Worker**
2. 이름 예: `event-ai` → **Deploy** (기본 코드 그대로 일단 배포)
3. **Edit code** 클릭 → 편집기 내용을 전부 지우고, 이 폴더의 [worker.js](worker.js) 내용을 붙여넣기 → **Deploy**

## 2) 비밀값(환경변수) 등록
Worker 페이지 → **Settings** → **Variables and Secrets** → **Add** 로 두 개 등록 (Type: **Secret**):
- `ANTHROPIC_API_KEY` = 위에서 만든 `sk-ant-...`
- `APP_PASS` = 원하는 접속 암호 (예: `design2026`) — 동기 2명에게 알려줄 값

저장 후 다시 **Deploy**.

## 3) 사이트에 주소 연결
- Worker 주소를 복사 (예: `https://event-ai.내계정.workers.dev`)
- `index.html`에서 `const AI_ENDPOINT = "";` 를 찾아 그 주소로 바꾸기:
  ```js
  const AI_ENDPOINT = "https://event-ai.내계정.workers.dev";
  ```
- 커밋 → push → GitHub Pages 반영

## 4) 사용
- 사이트 우하단 **🤖 AI 추천** 버튼 클릭
- 처음 한 번 **접속 암호**(`APP_PASS`) 입력 → 브라우저에 저장됨
- "그래픽 전공 대학생인데 상금 큰 대회 추천해줘" 처럼 물어보면, 목록에서 골라 링크로 추천

## 다 쓰고 나면
- 테스트가 끝나면 Cloudflare에서 Worker를 **Delete**, Anthropic 콘솔에서 **API 키 폐기**하면 깔끔하게 정리됩니다.

## 참고 / 안전
- 암호(`APP_PASS`)는 코드에 저장되지 않고 사용자가 입력하므로 저장소에 노출되지 않습니다.
- Worker는 모델을 `claude-haiku-4-5`로 고정하고 응답 토큰을 상한 걸어, 암호가 유출돼도 피해가 제한됩니다.
- 그래도 암호는 신뢰하는 사람에게만 알려주세요.
