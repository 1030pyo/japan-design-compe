# 배포 가이드 (GitHub Pages)

로컬 저장소는 이미 준비·커밋되어 있습니다. GitHub에 올리고 Pages만 켜면 끝.

## 방법 1 — GitHub Desktop (터미널 없이, 추천)
1. GitHub 계정 만들기 (없으면) → https://github.com/join
2. **GitHub Desktop** 설치 → https://desktop.github.com  (설치 후 GitHub 계정으로 로그인)
3. 상단 메뉴 **File → Add Local Repository** → 폴더 `~/event` (즉 `/Users/epyo/event`) 선택
4. 오른쪽 **Publish repository** 클릭
   - Name: 예) `japan-design-compe`
   - **"Keep this code private" 체크 해제** (공개로)
   - Publish
5. 브라우저에서 그 저장소 → **Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: **main** / **/(root)** → Save
6. 1~2분 뒤 접속 주소: `https://<내아이디>.github.io/japan-design-compe/`

## 방법 2 — 터미널 (git 익숙하면)
1. github.com 에서 New repository 생성 (public, README 없이 빈 저장소)
2. 아래 실행 (URL은 본인 것으로):
   ```
   cd ~/event
   git remote add origin https://github.com/<내아이디>/japan-design-compe.git
   git push -u origin main
   ```
   ※ 비밀번호 대신 Personal Access Token 필요 (github.com → Settings → Developer settings → Tokens)
3. Settings → Pages → Deploy from a branch → main /(root)

## 자동 갱신
올리고 나면 `.github/workflows/update.yml` 이 **매일 09:00(KST)** 자동 실행되어
`data.js`를 갱신·커밋 → Pages에 반영됩니다.
- 지금 바로 갱신: 저장소 **Actions 탭 → update-contests-data → Run workflow**
- (참고) GitHub는 저장소가 60일간 활동 없으면 예약 실행을 잠시 끄는데, 버튼으로 다시 켜집니다.
