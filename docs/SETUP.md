# SETUP — public repo, phone se, step by step

Ye guide **phone se** follow ho sakti hai. Laptop ki zaroorat nahi — sab kuch GitHub Actions (free) pe chalega.

Total one-time kaam: **~1 ghanta**. Uske baad roz **5 minute** (video dekh ke Publish dabana).

> **Repo public hai.** Iska matlab code aur workflow logs sab dekh sakte hain. Isliye: **koi key, client secret
> ya refresh token kabhi code, commit, issue ya log me nahi.** Sab sirf GitHub **Secrets** me. (Isi wajah se
> token nikalne ka kaam Actions me nahi, Google ke apne OAuth Playground me hota hai — neeche Step 7.)

Credentials ka literal click-by-click (deep links, kya dabana hai, kya copy karna hai):
**[`docs/CREDENTIALS.md`](CREDENTIALS.md)**

---

## Part 1 — Free me exactly kya chalega

| Kaam | Kaun karta hai (free) | Limit |
|------|----------------------|-------|
| Video render (ffmpeg) | GitHub Actions ka free runner | **public repo = unlimited minutes** |
| Hindi voiceover | edge-tts (Microsoft ka free endpoint) | koi key nahi, calls unlimited (kabhi block ho sakta hai) |
| Captions (word-level) | edge-tts timings | free |
| Trending topic dhoondhna | YouTube Data API key | 10,000 units/din — ek run ~2,050 units |
| B-roll footage | Pexels free API (portrait clips) | 200 requests/hour |
| Music | tumhare `assets/music` me daale 1-2 free tracks | free |
| Script | channel profile ka line-bank (bina AI) | free (thoda repeat ho sakta hai) |
| YouTube upload | YouTube Data API (OAuth) | free, quota me ~4-5 upload/din |
| Roz auto-run (cron 08:00 IST) | GitHub Actions schedule | free |

**Paid sirf 2 cheezein (optional):** AI se naya script, aur apna server (jiski zaroorat nahi).

---

## Part 2 — Kya kya "lena" hai (checklist)

| # | Cheez | Kahan se | Zaroori? |
|---|-------|----------|----------|
| 1 | Google account | accounts.google.com | Haan (channel ke liye, alag account better) |
| 2 | YouTube channel | youtube.com → Create a channel | Haan |
| 3 | GitHub account + repo | github.com | Haan (repo ban gaya hai) |
| 4 | Google Cloud project + **YouTube Data API v3** enable | console.cloud.google.com | Haan |
| 5 | **API key** (`YOUTUBE_API_KEY`) | Cloud → Credentials → API key | Haan (trends ke liye) |
| 6 | **OAuth client** Web application + secret (`YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`) | Cloud → Credentials → OAuth client ID | Haan (upload ke liye) |
| 7 | **Refresh token** (`YOUTUBE_REFRESH_TOKEN`) | OAuth Playground (Step 7) | Haan (upload ke liye) |
| 8 | Pexels API key (`PEXELS_API_KEY`) | pexels.com/api | Optional (b-roll auto download) |
| 9 | Free LLM key (`OPENAI_API_KEY`) | console.groq.com ya aistudio.google.com | Optional (naye scripts) |
| 10 | 1-2 royalty-free music tracks | YouTube Audio Library / Pixabay | Optional |

---

## Part 3 — Step by step

### Step 1 — YouTube channel (20 min, ek baar)

1. Channel ke liye **alag Google account** banao (safe rehta hai).
2. `youtube.com` → us account se sign in → profile icon → **Create a channel**.
3. Naam **Roz Ek Junoon** (ya jo pasand ho), handle `@rozekjunoon` jaisa jo available ho.
4. **Customise channel → Branding** me DP + banner (Canva free app, 15 min). Optional par CTR me farq padta hai.
5. Yaad rakhna: OAuth usi account se karna hai jisse ye channel bana.

### Step 2 — GitHub repo (ho gaya)

Repo bana diya hai (public). Bas `github.com` pe sign in karke apna repo khol lo:
**Settings → Secrets and variables → Actions**.

### Step 3 — Google Cloud project + API enable (10 min)

`console.cloud.google.com` kholo:

1. Upar project dropdown → **New project** → naam `shorts-pipeline` → **Create**.
2. Project select hai ye confirm karo → **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.

### Step 4 — API key (2 min)

**APIs & Services → Credentials → + Create credentials → API key** → key copy karo.

👉 Ye **`YOUTUBE_API_KEY`** hai. (Trending/popular videos padhne ke liye. Isse upload nahi hota, isliye ye kam risk hai — par phir bhi sirf secret me rakho.)

### Step 5 — OAuth consent screen + client (10 min)

Google ne isko **"Google Auth Platform"** naam de diya hai (consent screen ke andar hi khulta hai).

1. **APIs & Services → OAuth consent screen**:
   - User type **External** → Create
   - App name: `Shorts Pipeline`; User support email + Developer contact: apna Gmail
   - **Save and continue** (Scopes skip karo) → **Test users** me apna Gmail add karo → Save.
2. **Credentials → + Create credentials → OAuth client ID**:
   - Application type: **Web application**
   - Name: `shorts-pipeline`
   - **Authorized redirect URIs → Add URI** → likho: `https://developers.google.com/oauthplayground`
   - **Create** → ab **Client ID** aur **Client secret** copy karo.

👉 Ye **`YOUTUBE_CLIENT_ID`** aur **`YOUTUBE_CLIENT_SECRET`** hain.
⚠️ Client secret ko screenshot/issue/commit me mat daalo — sirf Step 6 ke Secrets me.

> Laptop hai to type **"TVs and Limited Input devices"** bhi chun sakte ho aur `python tools/youtube_auth.py` se
> token le sakte ho. Phone-only ke liye **Web application** + Playground wala rasta use karo. Dono ka token same
> kaam karta hai.

### Step 6 — GitHub Secrets (5 min)

Repo → **Settings → Secrets and variables → Actions → Secrets → New repository secret**. Ek-ek karke add karo:

| Name | Value |
|------|-------|
| `YOUTUBE_API_KEY` | Step 4 ki API key |
| `YOUTUBE_CLIENT_ID` | Step 5 ka Client ID |
| `YOUTUBE_CLIENT_SECRET` | Step 5 ka Client secret |

Optional (jab use karna ho tab add karo):

| Name | Value |
|------|-------|
| `PEXELS_API_KEY` | pexels.com/api se free key |
| `OPENAI_API_KEY` | Groq/Gemini/OpenAI key (script AI se) |

Free LLM (Groq/Gemini) chahiye to **Variables** tab me do variables bhi banao:

| Variable | Value |
|----------|-------|
| `OPENAI_BASE_URL` | `https://api.groq.com/openai/v1` ya `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `SCRIPT_MODEL` | `llama-3.3-70b-versatile` ya `gemini-2.0-flash` |

### Step 7 — Refresh token (OAuth Playground, 5 min)

Ye step ek baar. Isse `YOUTUBE_REFRESH_TOKEN` milega — iske bina upload nahi hoga.

1. Phone browser me kholo: `https://developers.google.com/oauthplayground`
2. Top-right **gear ⚙️** dabao → **Use your own OAuth credentials** tick karo →
   apna **Client ID** aur **Client secret** (Step 5) paste karo → **Close**.
3. Left column (Step 1) me scopes ki list hai. Neeche input box me ye scope paste karo:
   `https://www.googleapis.com/auth/youtube.upload`
   → **Authorize APIs** dabao.
4. Google sign-in → **wahi account jisse channel bana hai** chuno → **Allow**
   (unverified app ka warning aaye to **Advanced → Go to Shorts Pipeline (unsafe)** — apna hi app hai).
5. Wapas Playground me **Step 2: Exchange authorization code for tokens** →
   **Exchange authorization code for tokens** dabao.
6. Response me **`refresh_token`** dikhega (lamba string). Copy karo — naya token dobara nahi dikhega.
7. Repo → Settings → Secrets → naya secret: **`YOUTUBE_REFRESH_TOKEN`** = wo value.

⚠️ Ye token tumhare channel ka password jaisa hai. Kahin paste mat karo (issue, chat, screenshot).
Galti se leak ho jaye to: Google Account → **Security → Third-party apps** me is app ka access **Remove** karo,
phir Step 7 dobara.

### Step 8 — Consent screen Publish karo (2 min, warna token 7 din me expire)

**APIs & Services → OAuth consent screen → Publish app** dabao.

Testing mode me Google refresh token **7 din** me expire kar deta hai → uske baad upload fail hoga.
Publish karne ke baad token chalta rehta hai (YouTube upload scope "sensitive" hai, isliye Google
"unverified app" warning dikha sakta hai — apne hi app me **Advanced → Go to…** se aage badhna).

### Step 9 — Pehla test run (5-10 min, upload ke bina)

1. Repo → **Actions** → left me **Daily short** → **Run workflow**:
   - channel: `motivation`
   - mode: `none` ← pehle upload band
   - idea: khaali chhod do
2. ~5-8 min me green tick. Run page ke neeche **Artifacts → video-and-report** download karo (zip milega).
3. Andar: `video.mp4`, `thumbnail.jpg`, `review.md`, `script.txt`. **Video dekho**:
   - Hindi voice saaf hai?
   - Captions screen pe theek jagah + padhne layak?
   - Thumbnail ka text clear?
4. Kuch bhi off lage to bata dena — `channels/motivation.json` me `voice_rate`, `caption_size`,
   `duration_target`, `line_bank` ek line se badalte hain.

### Step 10 — Upload on karo

1. Wahi workflow, mode: `private` → run.
2. YouTube Studio app → video (private) → title + thumbnail check → **Publish**.
3. Ab roz 08:00 IST pe cron khud chalega (private upload). Subah sirf **Publish** dabana hai.
4. 1-2 hafte baad, jab content consistent lage — `.github/workflows/daily.yml` me `default: "private"` ko
   `"public"` kar do, ya har roz manual run `public` mode me karo.

---

### Step 11 — Doosra channel ya doosra Google account?

**Short answer: haan, chalega — GitHub aur YouTube ka koi rishta nahi hota.**

- **GitHub account** aur uski email — sirf code aur actions chalane ke liye. Iska YouTube se koi connection nahi.
  Tumhare GitHub pe `a@gmail.com` ho aur YouTube `b@gmail.com` pe — bilkul theek hai.
- **YouTube channel** kis Google account pe hai, ye sirf 3 jagah matter karta hai:
  1. OAuth Playground me sign-in usi account se karo jisse channel bana hai (ya jise us channel pe upload
     permission hai).
  2. Cloud project ka consent screen me wo account **test user** ho (Testing mode me).
  3. API key kisi bhi Cloud project ki ho sakti hai — sirf public data padhti hai.

**Brand account ka dhyan:** agar channel kisi "brand account" pe hai to OAuth ke waqt Google poochta hai kaunsa
channel/brand account — **wahi chuno**, warna token galat channel pe chala jayega.

**Ek se zyada account (4 channels = 4 different Google accounts)?** Ek repo ka default token ek hi account ka hota hai.
Do raste:

**Raasta A — har channel ka apna repo (simple, recommended):**
Har account ke liye is repo ka fork/copy banao, us repo ke **Secrets me usi account ka** token daalo.
Fayda: har channel ka apna quota (10,000 units/din), alag history, kuch mix nahi hota.

**Raasta B — ek hi repo, per-channel secrets:**
Channel profile JSON me `credential_suffix` daalo:

```json
{ "name": "Rok Facts", "credential_suffix": "FACTS" }
```

Phir repo me ye secrets banao (jo na ho, wo default pe fallback karta hai):

| Channel | Client ID secret | Client secret | Refresh token secret |
|---------|------------------|---------------|----------------------|
| motivation (default) | `YOUTUBE_CLIENT_ID` | `YOUTUBE_CLIENT_SECRET` | `YOUTUBE_REFRESH_TOKEN` |
| facts (`"FACTS"`) | `YOUTUBE_CLIENT_ID_FACTS` | `YOUTUBE_CLIENT_SECRET_FACTS` | `YOUTUBE_REFRESH_TOKEN_FACTS` |

⚠️ Raasta B me **quota ek hi hai** (Cloud project ka 10,000 units/din — sab channels milkar ~4-5 uploads).
Isliye 3-4 channels ek saath chalane ho to **Raasta A** better hai.

---

## Part 4 — Roz ka tumhara kaam (5 min)


1. Subah: YouTube Studio → private video dekho → **Publish** (ya delete karke dobara run).
2. Hafte me ek baar `review.md` padho: kaunsa trend aaya, kaunsa idea chuna — isse pata chalega format chal raha hai ya nahi.
3. Mahine me ek baar repo me chhota commit ya manual run — 60 din inactivity pe GitHub cron khud band kar deta hai.

---

## Part 5 — Kuch break ho jaye to

| Dikh raha hai | Matlab | Fix |
|---------------|--------|-----|
| `credentials missing` | refresh token nahi/expire | Step 7 dobara, phir secret update |
| `invalid_grant` | token revoke/expire (Testing mode) | consent screen **Publish**, Step 7 dobara |
| `403 quota exceeded` | aaj ka YouTube quota khatam | agle din (reset ~10:30 IST) |
| `invalid_client` | client id/secret galat ya type mismatch | Step 5 dobara, secrets update |
| voice nahi, sirf captions | edge-tts block hua | run dobara; ya b-roll+music pe focus |
| flat colour background | koi b-roll nahi mila | `PEXELS_API_KEY` daalo ya `assets/broll` me clips upload karo |
| script repeat lag raha | LLM key nahi | Step 6 ka optional part (Groq/Gemini free) |
| workflow hi nahi dikh raha | workflow default branch pe nahi | `main` branch pe hona chahiye |
| cron band | 60 din no activity | ek commit/manual run |

---

## Part 6 — Public repo: 4 safety rules

1. Keys/tokens sirf **Settings → Secrets** me. `.env` **kabhi commit nahi** (`.gitignore` me hai).
2. `.env.example` me sirf khaali naam rehte hain, value nahi.
3. Screenshot/log share karte waqt client secret aur token blur karo.
4. Token leak ho jaye to: Google Account → Security → third-party access **Remove** → naya token → secret update.

---

## Progress checklist

- ✔ Repo (public) — code ready
- ⬜ Step 1: channel
- ⬜ Step 3-6: Cloud project, API key, OAuth client, secrets
- ⬜ Step 7-8: refresh token + publish app
- ⬜ Step 9-10: test run, phir private upload

Kisi step pe atak jao to wahi step number bata do — usi ke exact button bata dunga.
