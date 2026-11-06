# Credentials — Client ID aur baaki sab, click by click

Ye file sirf ek kaam ke liye hai: **YouTube Data API key, OAuth Client ID, Client secret aur Refresh token**
nikalna. Phone se bhi ho jata hai — bas har screen pe kya dabana hai, wo neeche hai.

Note: Google ne "OAuth consent screen" ka naam badal ke **Google Auth Platform** kar diya hai. Steps me dono
naam likhe hain, screen pe jo dikhe wahi dabana.

---

## 0. Aakhir me tumhare paas ye 4 cheezein hongi

| Cheez | Kahan se milegi | GitHub secret ka naam | Kya karti hai |
|-------|-----------------|----------------------|---------------|
| API key | Step 3 | `YOUTUBE_API_KEY` | trending videos padhna |
| Client ID | Step 4 | `YOUTUBE_CLIENT_ID` | app ki pehchaan |
| Client secret | Step 4 (sirf ek baar dikhta hai) | `YOUTUBE_CLIENT_SECRET` | app ka password |
| Refresh token | Step 6 | `YOUTUBE_REFRESH_TOKEN` | bina dobara login, upload karna |

Sab kuch **ek hi Google Cloud project** me banega.

---

## Step 1 — Project banao (2 min)

1. Kholo: `https://console.cloud.google.com/projectcreate`
2. **Project name**: `shorts-pipeline` → **Create**
3. 20-30 second wait. Upar project selector me naam dikhne lage to aage badho.
4. **Zaroori:** poore setup me upar wahi project selected hona chahiye — warna sab kuch galat project me banega.

## Step 2 — YouTube Data API v3 enable karo (2 min)

1. Kholo: `https://console.cloud.google.com/apis/library/youtube.googleapis.com`
2. Upar project check karo → **Enable** dabao.
3. Page refresh karke "API Enabled" dikhe to done.

## Step 3 — API key (2 min)

1. Kholo: `https://console.cloud.google.com/apis/credentials`
2. Upar **+ Create credentials** → **API key**
3. Popup me key dikhegi (AIza... se shuru) → **copy** dabao.
4. **Optional but accha:** "Edit API key" → *API restrictions* → **Restrict key** → **YouTube Data API v3** → Save.
   (Isse key sirf ye API padh sakti hai.)
5. GitHub → repo → Settings → Secrets and variables → Actions → **New repository secret**:
   - Name: `YOUTUBE_API_KEY`
   - Secret: wo key paste karo → **Add secret**

## Step 4 — OAuth client ID + secret (5 min)

Pehle app "register" karna padta hai (naya console isko Google Auth Platform kehta hai).

### 4a. App register karo

1. Kholo: `https://console.cloud.google.com/auth/overview`
2. **Get started** dabao.
3. **App information**:
   - App name: `Shorts Pipeline`
   - User support email: apna Gmail
4. **Audience**: **External** chuno → Next
5. **Contact information**: apna Gmail → Next
6. **Agree to policy** tick → **Create**

### 4b. Test user add karo (Testing mode me zaroori)

1. Kholo: `https://console.cloud.google.com/auth/audience`
2. **Test users** → **Add users** → **YouTube channel wala Gmail** daalo → Save

Agar Cloud project kisi doosre account ka hai, to yahan **channel wala account** hona chahiye.

### 4c. Client banao

1. Kholo: `https://console.cloud.google.com/auth/clients`
2. **+ Create client** (ya "CREATE CLIENT")
3. **Application type**: **Web application**
4. **Name**: `shorts-pipeline`
5. **Authorized redirect URIs** → **+ Add URI** → paste karo:
   ```
   https://developers.google.com/oauthplayground
   ```
6. **Create** dabao.
7. Ab popup me **Client ID** aur **Client secret** dikhenge.
   ⚠️ **Client secret sirf isi waqt poora dikhta hai** — baad me sirf last 4 characters dikhte hain.
   Dono turant copy karo (ya "Download JSON" dabao).
8. GitHub secrets:
   - `YOUTUBE_CLIENT_ID` = Client ID
   - `YOUTUBE_CLIENT_SECRET` = Client secret

## Step 5 — Upload scope add karo (2 min)

1. Kholo: `https://console.cloud.google.com/auth/scopes`
2. **Add or remove scopes** → neeche "Manually add scopes" box me paste karo:
   ```
   https://www.googleapis.com/auth/youtube.upload
   ```
3. **Add to table** → **Update** → **Save**

Iske bina Playground "invalid_scope" error de sakta hai.

## Step 6 — Refresh token (5 min)

1. Phone browser me kholo: `https://developers.google.com/oauthplayground`
2. Top **right** gear ⚙️ dabao → **OAuth 2.0 Configuration** panel khulega:
   - **Use your own OAuth credentials** tick karo
   - **OAuth Client ID**: Step 4 ka Client ID
   - **OAuth Client secret**: Step 4 ka Client secret
   - **Close**
3. **Left column → Step 1** me scopes ki list hai. Upar input box me ye scope paste karo:
   ```
   https://www.googleapis.com/auth/youtube.upload
   ```
   → **Authorize APIs** dabao.
4. Google sign-in page:
   - **Channel wala account** chuno (ya Brand Account chuno agar channel usme hai)
   - "Google hasn't verified this app" aaye to **Advanced** → **Go to Shorts Pipeline (unsafe)** —
     apna hi app hai, safe hai
   - **Allow** / **Continue** dabao
5. Wapas Playground: **Step 2 → Exchange authorization code for tokens** dabao.
6. Response box me JSON aayega, usme **`"refresh_token": "1//..."`** hoga. Copy karo.
   (Ye dobara nahi dikhega — abhi copy karo.)
7. GitHub secret: `YOUTUBE_REFRESH_TOKEN` = wo value

**Agar `refresh_token` nahi dikha?** Pehle se authorize kar chuke ho to Google naya refresh token nahi deta.
Fix: Playground me Step 1 se dobara **Authorize APIs** karo (purana consent replace ho jayega), ya
`https://myaccount.google.com/permissions` se app ka access **Remove** karke phir se Step 6 karo.

## Step 7 — Consent screen Publish karo (2 min)

1. Kholo: `https://console.cloud.google.com/auth/audience`
2. **Publishing status: Testing** ke saamne **Publish app** dabao → confirm.

Kyun zaroori: Testing mode me Google refresh token ko **7 din** me expire kar deta hai. Publish karne ke baad
token chalta rehta hai. (Unverified app warning dikhegi — apna hi app hai, ignore karo.)

## Step 8 — Check karo ki sab sahi laga

Repo → **Settings → Secrets and variables → Actions** me ye 4 dikhne chahiye:

```
YOUTUBE_API_KEY
YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN
```

Optional: `PEXELS_API_KEY`, `OPENAI_API_KEY` (+ Variables me `OPENAI_BASE_URL`, `SCRIPT_MODEL`).

Ab pehla asli test: **Actions → Daily short → Run workflow** → channel `motivation`, mode `none`.
Log me dikhega:

- `[1/8] trend radar` — agar API key sahi hai to signals ka number aayega
- `[6/8] render` — video ban raha hai
- `[8/8] upload skipped` — mode `none` hai, sahi

Green tick + artifact `video-and-report` = sab set. Uske baad mode `private` se upload test karo.

---

## Errors ka matlab

| Error | Matlab | Fix |
|-------|--------|-----|
| `invalid_client` | client id/secret galat, ya secret copy nahi kiya tha | Step 4c dobara (naya secret banao), secret update karo |
| `redirect_uri_mismatch` | redirect URI add nahi kiya | Step 4c me `https://developers.google.com/oauthplayground` add karo |
| `invalid_scope` | scope Data Access me add nahi | Step 5 dobara |
| `access_denied` | Allow nahi dabaya / galat account | Step 6 dobara, channel wala account chuno |
| `invalid_grant` | refresh token expire/revoke | Step 6 dobara + Step 7 Publish |
| `403 quotaExceeded` | 10,000 units/din khatam | agle din (~10:30 IST reset) |
| `The request is missing a valid API key` | `YOUTUBE_API_KEY` secret nahi hai ya galat hai | Step 3 dobara |
| `No API key` / `API not enabled` | API enable nahi hua | Step 2 dobara |
| `app is not verified` (browser) | normal hai | **Advanced → Go to … (unsafe)** |

---

## 3 baatein jo bhoolni nahi

1. **Ye 4 values kabhi kisi ko na do** — refresh token se koi tumhari channel pe video upload/delete kar sakta hai.
2. Client secret **sirf ek baar** dikhta hai (naye clients me) — na dikhe to **Add secret** se naya banao, purana disable karo.
3. Repo public hai — values sirf GitHub **Secrets** me, kabhi commit/issue/screenshot me nahi.
