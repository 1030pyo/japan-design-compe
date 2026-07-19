#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
일본 디자인 공모전 자동 업데이트 스크립트
 - koubo.jp (디자인 카테고리 c=7) + 登竜門(디자인 7장르) 스크래핑
 - 중복 제거·마감/상금/학생전용 판별
 - 번역은 translations.json 캐시 재사용 (새 공모전은 일본어로 남김)
 - data.js 를 새로 생성
사용: python3 update.py   (cron/launchd 로 매일 자동 실행)
"""
import re, json, os, sys, time, html, unicodedata
import urllib.request, concurrent.futures
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

def log(*a): print(*a, file=sys.stderr)

def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == tries-1: return ""
            time.sleep(1.0)
    return ""

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s).replace('　', ' ')
    return re.sub(r'\s+', ' ', s).strip()

# ---------------- koubo ----------------
KOUBO = "https://koubo.jp"
def koubo_collect_ids():
    order, seen = [], set()
    p, empty = 1, 0
    while empty < 2 and p <= 60:
        h = fetch(f"{KOUBO}/contest/list?c=7&p={p}")
        toks = re.findall(r'gray-600\\?"[^}]*?children\\?":\\?"([^"\\]{2,40})\\?"|\\?"contest\\?":\{\\?"id\\?":(\d+)', h)
        cur, added = "", 0
        for cat, cid in toks:
            if cat: cur = cat
            elif cid and cid not in seen:
                seen.add(cid); order.append((cid, cur)); added += 1
        if added == 0: empty += 1
        p += 1
    return order

def koubo_detail(cid):
    h = fetch(f"{KOUBO}/contest/{cid}")
    if not h: return None
    def og(p):
        m = re.search(r'<meta property="%s" content="([^"]*)"' % p, h); return m.group(1) if m else ""
    title = re.sub(r'\s*\|\s*公募.*$', '', og("og:title")).strip()
    img = og("og:image");  img = "" if "ogp_koubo" in img else img
    fields = {clean(k): clean(v) for k, v in re.findall(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>', h, re.S)}
    def pick(*keys):
        for k in fields:
            if any(w in k for w in keys): return fields[k]
        return ""
    return {"id": cid, "title_jp": title, "image": img,
            "deadline_jp": pick("締切"), "org_jp": pick("主催"),
            "prize_jp": pick("賞"), "qual_jp": pick("資格")}

def scrape_koubo():
    order = koubo_collect_ids()
    cat = {cid: c for cid, c in order}
    ids = [cid for cid, _ in order]
    log(f"koubo ids: {len(ids)}")
    out = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for cid, r in zip(ids, ex.map(koubo_detail, ids)):
            if r: r["cat_jp"] = cat.get(cid, ""); out[cid] = r
    return [out[c] for c in ids if c in out]

# ---------------- 登竜門 ----------------
TORYU = "https://compe.japandesign.ne.jp"
TORYU_CATS = [("graphic","그래픽·포스터"),("product","프로덕트"),("space","공간·건축"),
              ("craft","공예"),("digital-media","CG·디지털"),("character","캐릭터"),("idea","아이디어")]
def toryu_cards(h):
    out = []
    for c in re.findall(r'<li class="contest-list-item">(.*?)</li>', h, re.S):
        ms = re.search(r'href="https://compe\.japandesign\.ne\.jp/([a-z0-9-]+)/"', c)
        mt = re.search(r'<h3>(.*?)</h3>', c, re.S)
        if not ms or not mt: continue
        def dl(lbl):
            m = re.search(r'<dt>%s</dt>\s*<dd>(.*?)</dd>' % lbl, c, re.S); return clean(m.group(1)) if m else ""
        out.append({"slug": ms.group(1), "title_jp": clean(mt.group(1)),
                    "prize_jp": dl("賞"), "org_jp": dl("主催"), "deadline_jp": dl("締切")})
    return out

def toryu_detail(slug):
    h = fetch(f"{TORYU}/{slug}/")
    mi = re.search(r'<meta property="og:image" content="([^"]*)"', h)
    img = mi.group(1) if mi else ""
    if not img or 'trm_logo' in img or 'banner' in img or '/plugins/' in img: img = ""
    mq = re.search(r'<dt>参加資格</dt>\s*<dd>(.*?)</dd>', h, re.S) or re.search(r'<dt>応募資格</dt>\s*<dd>(.*?)</dd>', h, re.S)
    qual = clean(mq.group(1)) if mq else ""
    return slug, img, qual

def scrape_toryu():
    items = {}
    for slug_cat, ko in TORYU_CATS:
        p = 1
        while p <= 12:
            url = f"{TORYU}/category/{slug_cat}/" if p == 1 else f"{TORYU}/category/{slug_cat}/page/{p}/"
            cards = toryu_cards(fetch(url))
            if not cards: break
            for c in cards:
                if c["slug"] not in items:
                    c["cat_ko"] = ko; items[c["slug"]] = c
            if len(cards) < 30: break
            p += 1
    items = list(items.values())
    log(f"toryu unique(pre-dedup): {len(items)}")
    slugs = [x["slug"] for x in items]
    res = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for slug, img, qual in ex.map(lambda s: toryu_detail(s), slugs):
            res[slug] = (img, qual)
    for x in items:
        img, qual = res.get(x["slug"], ("", ""))
        x["image"], x["qual_jp"] = img, qual
    return items

# ---------------- 공통 가공 ----------------
CAT_K = {"チラシ・表紙・ポスターデザイン":"전단·표지·포스터","その他デザイン・デザインコンペ":"기타·컴페",
  "建築・設計・景観デザイン":"건축·설계·조경","ジュエリー・アパレル・ファッションデザイン":"주얼리·패션",
  "ロゴマーク":"로고마크","プロダクトデザイン":"프로덕트","写真・フォトコン":"사진·포토콘",
  "シンボルマーク":"심볼마크","CG・デジタル":"CG·디지털","ラベル・パッケージデザイン":"라벨·패키지",
  "アイデア":"아이디어","フラワーデザイン・ガーデニング":"플라워·가드닝","企画・ビジネスプラン":"기획·비즈니스",
  "プログラミング・ゲーム・アプリ":"프로그래밍·게임·앱","映像・映画・ショートフィルム":"영상·영화","その他":"기타",
  "金券・Amazonギフトカード・図書カード":"상품권·기프트","ナンバープレート":"넘버플레이트","スピーチ・弁論":"스피치·변론",
  "観光写真":"관광사진","動画・ビデオ・ショート動画":"동영상·숏폼","漫画・コミック":"만화·코믹","作詞":"작사","短文・大喜利・漢字":"단문·오오기리"}
STU_WORDS = ['学生','高校生','中学生','小学生','児童','生徒','大学生','専門学校','高専','園児','幼児','高等学校','中学校','小学校','中等教育','特別支援']
GEN_WORDS = ['一般','不問','どなた','問わ','制限なし','以上','限りません','どちら','市民','県民','国民','企業','団体','法人','社会人','プロ','アマ','在住','在勤','年齢','個人']
STU_MARKER = re.compile(r'《[^》]*(学生|高校生|中学生|小学生|児童|生徒|幼)[^》]*限定[^》]*》')
def is_student_only(qual, title=""):
    if title and STU_MARKER.search(title): return True
    if not qual: return False
    return any(w in qual for w in STU_WORDS) and not any(w in qual for w in GEN_WORDS)

def parse_dl(s):
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', s)
    if m: return int(m.group(1)), int(m.group(2)), int(m.group(3))
    m = re.search(r'(\d{1,2})月(\d{1,2})日', s)
    if m: return None, int(m.group(1)), int(m.group(2))
    return None, None, None

def prize_short(s):
    if not s: return ""
    a = [int(m.group(1).replace(',','')) for m in re.finditer(r'([0-9][0-9,]*)\s*万円', s)]
    if a: return f"상금 {max(a)}만엔"
    y = [int(m.group(1).replace(',','')) for m in re.finditer(r'([0-9][0-9,]*)\s*円', s)]
    if y: return f"상금 {max(y):,}엔"
    for kw, ko in [("図書カード","도서카드"),("Amazonギフト","아마존기프트"),("QUOカード","쿠오카드"),("ギフト","기프트"),
                   ("商品券","상품권"),("採用","작품 채용"),("賞状","상장"),("表彰状","표창장"),("記念品","기념품"),("トロフィー","트로피"),("完成品","완제품")]:
        if kw in s: return ko
    return "상세 참조"

def norm(s):
    s = html.unescape(s); s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'(第[0-9]+回|20[0-9]{2}年度?|20[0-9]{2}|令和[0-9]+年度?|《[^》]*》|\([^)]*限定[^)]*\))', '', s)
    return re.sub(r'[\s・「」『』（）()【】\[\]、,。.!！?？~〜\-—–/／＆&:：;；\'\"’”“×＋+]+', '', s).lower()

def main():
    koubo = scrape_koubo()
    toryu = scrape_toryu()
    if len(koubo) < 100:
        log(f"koubo 수집 실패({len(koubo)}건) → data.js 갱신 중단"); sys.exit(1)

    # dedup toryu vs koubo
    kn = [(norm(k['title_jp']), k) for k in koubo]
    def is_dup(t):
        nt = norm(t['title_jp'])
        for nk, k in kn:
            if not nk: continue
            r = SequenceMatcher(None, nt, nk).ratio()
            if nk in nt or nt in nk: r = max(r, 0.9)
            if r >= 0.70: return k['id']
        return None
    dup_koubo_ids = set()
    toryu_uniq = []
    for t in toryu:
        d = is_dup(t)
        if d: dup_koubo_ids.add(d)
        else: toryu_uniq.append(t)
    log(f"toryu 고유: {len(toryu_uniq)} (중복 {len(toryu)-len(toryu_uniq)})")

    # 번역 캐시
    cache_path = os.path.join(HERE, "translations.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}

    out = []
    for x in koubo:
        y, mo, d = parse_dl(x["deadline_jp"])
        iid = "k" + x["id"]
        ko = cache.get(iid, x["title_jp"])
        out.append({"id": iid, "ko": ko, "jp": x["title_jp"],
            "cat": CAT_K.get(x["cat_jp"], x["cat_jp"] or "기타"), "y": y, "m": mo, "d": d,
            "prize": prize_short(x["prize_jp"]), "org": x["org_jp"], "img": x["image"],
            "url": f"{KOUBO}/contest/{x['id']}",
            "src": "koubo·登竜門" if x["id"] in dup_koubo_ids else "koubo",
            "sortid": int(x["id"]) if x["id"].isdigit() else 0,
            "stu": is_student_only(x.get("qual_jp",""), x["title_jp"]),
            "utl": iid not in cache})
    seq = 900000
    for x in toryu_uniq:
        y, mo, d = parse_dl(x["deadline_jp"]); seq += 1
        iid = "t_" + x["slug"]
        ko = cache.get(iid, x["title_jp"])
        out.append({"id": iid, "ko": ko, "jp": x["title_jp"], "cat": x["cat_ko"],
            "y": y, "m": mo, "d": d, "prize": prize_short(x["prize_jp"]),
            "org": x["org_jp"], "img": x.get("image",""),
            "url": f"{TORYU}/{x['slug']}/", "src": "登竜門", "sortid": seq,
            "stu": is_student_only(x.get("qual_jp",""), x["title_jp"]),
            "utl": iid not in cache})

    js = ('window.DATA_UPDATED = "' + time.strftime("%Y.%m.%d") + '";\n'
          + "window.DATA = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    open(os.path.join(HERE, "data.js"), "w", encoding="utf-8").write(js)
    untranslated = sum(1 for o in out if o["utl"])
    log(f"✅ data.js 갱신: {len(out)}건 (koubo {len(koubo)} + 登竜門 {len(toryu_uniq)}), 미번역 {untranslated}건")
    # 업데이트 시각 기록
    open(os.path.join(HERE, "last_update.txt"), "w").write(time.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()
