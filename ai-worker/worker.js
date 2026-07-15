// Cloudflare Worker — 사이트의 AI 추천 챗봇용 프록시
// API 키를 브라우저에 노출하지 않고, 암호(APP_PASS)를 아는 사람만 쓰게 합니다.
//
// 필요한 환경변수(Settings → Variables and Secrets):
//   ANTHROPIC_API_KEY  (Secret) — Anthropic API 키
//   APP_PASS           (Secret) — 접속 암호 (동기들에게 알려줄 값)

export default {
  async fetch(request, env) {
    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-App-Pass",
    };
    const json = (obj, status = 200) =>
      new Response(JSON.stringify(obj), { status, headers: { ...cors, "Content-Type": "application/json" } });

    if (request.method === "OPTIONS") return new Response(null, { headers: cors });
    if (request.method !== "POST") return json({ error: "POST only" }, 405);

    // 암호 확인
    if (request.headers.get("X-App-Pass") !== env.APP_PASS) {
      return json({ error: "unauthorized" }, 401);
    }

    // 본문 파싱 + 안전장치(모델 고정, 토큰 상한)
    let payload;
    try { payload = await request.json(); } catch { return json({ error: "bad json" }, 400); }
    payload.model = "claude-haiku-4-5";
    payload.max_tokens = Math.min(payload.max_tokens || 1024, 1500);

    // Anthropic 호출 (키는 여기서만 붙는다 → 브라우저엔 노출 안 됨)
    const resp = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify(payload),
    });

    const text = await resp.text();
    return new Response(text, { status: resp.status, headers: { ...cors, "Content-Type": "application/json" } });
  },
};
