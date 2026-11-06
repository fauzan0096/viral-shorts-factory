# Viral Shorts Factory

Ek roz ek short — roz ka pura kaam ek command me:

**trend catch -> idea -> script → voiceover → 1080x1920 video → thumbnail → YouTube upload**

Sab kuch Python + ffmpeg me hai. Koi paid runner nahi chahiye; GitHub Actions free tier bhi kaafi hai.

**Laptop nahi hai?** Poora setup phone se hota hai — step-by-step: [`docs/SETUP.md`](docs/SETUP.md)
(kya free hai, kya karna hai, kis order me, aur kya break hone pe kya karna hai).

---

## 1. Kaunse 4 channel banenge (ye maine chune hain)

Detailed plan: [`docs/CHANNEL-PLAN.md`](docs/CHANNEL-PLAN.md)

| # | Channel | Format | Kyun (viral logic) | Profile |
|---|---------|--------|--------------------|---------|
| 1 | **Roz Ek Junoon** (motivation) | 35-40s Hindi voiceover + cinematic b-roll | Evergreen, highest retention, roz naya topic easy, India me huge audience | `channels/motivation.json` |
| 2 | **Rok Facts** | 30-35s "did you know" facts | Sabse zyada CTR/thumbnail clicks, script banana fastest | `channels/facts.json` |
| 3 | **Theek Hai Bhai** (comedy) | 25-30s relatable POV one-liners | Shares + comments se viral loop, sabse sasta production | `channels/comedy.json` |
| 4 | **Chhoti Kahani** (story/moral) | 45-55s kahani + sabak | Sabse lamba watch-time, monetization ke liye strong | `channels/story.json` |

**Recommendation:** channel 1 (motivation) se start karo, 30 din daily. Retention aur voice pehle set ho jaye,
phir facts ko doosre channel ke roop me chalana — dono ke liye same pipeline, bas `--channel` badalna hai.

---

## 2. Pipeline kaise kaam karta hai

```
trends.py    -> YouTube trending + niche search, score = views/hour x engagement x freshness
ideas.py     -> trend keywords + channel ke seed ideas -> 3 best ORIGINAL topics (copy nahi)
script.py    -> LLM (agar key hai) ya curated line-bank se hook + body + CTA
voice.py     -> edge-tts neural Hindi voiceover + word-level captions (SRT)
assets.py    -> local b-roll / Pexels portrait clips + background music
render.py    -> ffmpeg: 1080x1920, 30fps, captions burned-in, voice + music mix
thumb.py     -> vertical thumbnail with big bold headline
metadata.py  -> title, description, tags, hashtags, thumbnail text
publish.py   -> YouTube resumable upload (private/scheduled default)
state.py     -> konsa topic already use ho chuka (repeat nahi hota)
review.py    -> work/<channel>/<date>/review.md — aaj ka pura decision trail
```

Har run me `review.md` banti hai: kaun se trends dikhe, kaunsa idea chuna aur kyun, script, title/tags.
Isse tum 30 second me check kar sakte ho ki video sahi hai ya nahi.

---

## 3. Quick start (laptop pe)

```bash
pip install -r requirements.txt      # optional: edge-tts (best quality voice)
# ffmpeg chahiye:  mac: brew install ffmpeg  |  ubuntu: sudo apt install ffmpeg

cp .env.example .env                 # keys baad me bharo, pehle kuch zaroori nahi

python run.py --channel motivation --dry-run     # sirf idea + script + package
python run.py --channel motivation --upload none # pura video, upload nahi
```

Output: `work/motivation/2025-01-05/video.mp4`, `thumbnail.jpg`, `review.md`.

### Commands

```bash
python run.py --channel motivation              # render + upload (privacy profile se)
python run.py --channel facts --upload private  # render + private upload
python run.py --channel comedy --idea "POV: Monday morning"   # apna topic force karo
python run.py --channel story --dry-run --shortlist 3         # sirf planning
```

---

## 4. Keys (jo chahiye, wo bharo — bina keys bhi chalta hai)

| Key | Kya milta hai | Bina iske |
|-----|---------------|-----------|
| `YOUTUBE_API_KEY` | Trending + niche videos ka real-time data | Seed ideas se offline chalega |
| `PEXELS_API_KEY` | Fresh stock b-roll auto download | Local `assets/broll` ya solid background |
| `OPENAI_API_KEY` (+ `OPENAI_BASE_URL`, `SCRIPT_MODEL`) | Naye scripts har roz | Curated line-bank se script |
| `YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN` | Auto upload | Video local render hoke ruk jayega |

YouTube upload setup (ek baar) — poora detail `docs/SETUP.md` me hai, short me:

1. Google Cloud Console -> new project -> **YouTube Data API v3** enable karo.
2. OAuth consent screen -> External -> khud ko **test user** add karo.
3. Credentials -> API key banao (`YOUTUBE_API_KEY`).
4. Credentials -> OAuth client ID, type **Web application**, redirect URI:
   `https://developers.google.com/oauthplayground` (`YOUTUBE_CLIENT_ID` + `YOUTUBE_CLIENT_SECRET`).
5. Refresh token: `https://developers.google.com/oauthplayground` -> gear ⚙️ -> *Use your own OAuth credentials*
   -> scope `https://www.googleapis.com/auth/youtube.upload` -> Authorize -> Exchange code for tokens ->
   `refresh_token` copy karo (`YOUTUBE_REFRESH_TOKEN`).
5b. Laptop hai to `python tools/youtube_auth.py` se bhi token le sakte ho (client type "TVs and Limited Input devices").
6. Consent screen pe **Publish app** dabao — warna refresh token 7 din me expire hota hai.

Agar channel brand new hai to OAuth token usi Google account ka ho jisse channel bana hai.
**Repo public hai — ye teen secrets kabhi code/issue/log me daalo mat, sirf Settings -> Secrets me.**

---

## 5. Roz automatic (GitHub Actions)

`.github/workflows/daily.yml` roz **08:00 IST** pe chalta hai:
ffmpeg + fonts install -> render -> private upload -> artifacts (video, thumbnail, review) 14 din ke liye.

Repo secrets me daalo: `YOUTUBE_API_KEY`, `PEXELS_API_KEY`, `YOUTUBE_CLIENT_ID`,
`YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`, (optional `OPENAI_API_KEY`).

Manual run: Actions -> *Daily short* -> Run workflow -> channel/mode choose karo.

**Default `private` rakha hai** — pehle 1-2 hafte khud dekh ke publish karo. Jab content consistent lage,
`--upload public` (ya workflow input) kar do.

---

## 6. B-roll aur music

- `assets/broll/*.mp4` — apne clips (vertical ya koi bhi, pipeline crop kar lega).
  Bina clips ke bhi video banta hai: solid background + captions (motivation/facts ke liye kaafi acceptable).
- `assets/music/*.mp3` — ek do royalty-free tracks. **Trending commercial songs mat lagao** — claim/strike.
- Free legal sources: Pexels, Pixabay, Mixkit, YouTube Audio Library.
- Better b-roll: apne phone se 10-15 clips shoot karo (chalti sadak, gym, chai, neon) — sabse "original" feel.

---

## 7. Rules (ye skip mat karo)

- Sirf **original** content: dusre ka video download karke re-upload = copyright strike + monetization gone.
  Pipeline sirf *topic/angle* trend se uthata hai, footage/audio nahi.
- Voice = TTS, footage = stock/apna. Music = licensed/free.
- Har run `review.md` padho — kuch bhi galat lage to video delete kar do, upload private hai.
- Roz same time upload karo (08:00-09:00 IST). Shorts me consistency hi algorithm ka best friend hai.

---

## 8. Structure

```
run.py                  CLI entry
channels/*.json         channel profiles (voice, prompts, line-bank, seed ideas)
pipeline/config.py      .env + profile loading
pipeline/trends.py      trend radar + viral scoring
pipeline/ideas.py       trend -> original idea shortlist
pipeline/script.py      LLM / template script writer
pipeline/voice.py       edge-tts + word-timed SRT
pipeline/captions.py    estimated SRT fallback
pipeline/assets.py      b-roll + music
pipeline/render.py      ffmpeg video builder
pipeline/thumb.py       thumbnail
pipeline/metadata.py    title/description/tags
pipeline/publish.py     YouTube upload
pipeline/state.py       used topics + history
pipeline/review.py      run report
tools/youtube_auth.py   one-time OAuth
.github/workflows/      daily cron
```

---

## 9. Naya channel add karna

`channels/facts.json` copy karke `channels/my-channel.json` banao, aur badlo:
`name`, `category_id`, `voice`, `topic_queries`, `broll_queries`, `hooks`, `line_bank`,
`idea_templates`, `seed_ideas`, `cta`, `hashtags`.

Phir: `python run.py --channel my-channel`.

**Channel ka YouTube account alag hai?** GitHub account/email aur YouTube account ka koi rishta nahi — koi bhi
combination chalega. Ek repo ka token ek account ka hota hai; per-channel account chahiye to profile me
`"credential_suffix": "FACTS"` daalo aur secrets `YOUTUBE_CLIENT_ID_FACTS`, `YOUTUBE_CLIENT_SECRET_FACTS`,
`YOUTUBE_REFRESH_TOKEN_FACTS` banao (details `docs/SETUP.md` Step 11).

---

## 10. Free hai ya nahi?

**Haan — ek channel roz chalane ka pura kharcha zero hai.** Sirf ye do cheezein optional paid hain:
LLM script likhwana, aur apna server.

| Cheez | Kitna free | Note |
|-------|-----------|------|
| Python + ffmpeg | unlimited | open source, local |
| edge-tts (Hindi voice) | unlimited calls | unofficial Microsoft endpoint, key nahi chahiye |
| YouTube Data API key | 10,000 units/din | search 100 units, trending 1, upload 1,600, thumbnail 50 — ek run ~2,050 units, matlab ~4-5 uploads/din |
| YouTube upload | free | channel + OAuth account ka hona chahiye |
| Pexels b-roll | 200 requests/hour | free key, credit optional |
| GitHub Actions | private repo 2,000 min/month; public repo unlimited | ek run ~5-8 min = 300+ runs/month free |
| LLM script (OpenAI) | paid | skip karo → curated line-bank se script banta hai |

Free LLM chahiye to koi OpenAI-compatible free tier lagao (`.env` me sirf base URL badalna hai):

- Google Gemini: `OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`
- Groq: `OPENAI_BASE_URL=https://api.groq.com/openai/v1`

### Free plan ke 3 real gotchas

1. **OAuth testing mode:** Google Cloud ka OAuth app "Testing" me ho to refresh token **7 din** me expire hota hai.
   Fix: app ko "Published" karo, ya har hafte `python tools/youtube_auth.py` dobara chalao.
   (Isliye pehle 1 hafte me token expire ho jaye to upload fail hoga — video render hoke padi rahegi.)
2. **GitHub cron**: 60 din repo me koi activity na ho to scheduled workflow khud band ho jata hai — mahine me ek commit/manual run kar dena.
3. **edge-tts** unofficial hai — kabhi block ho to voice ke bina (captions-only) video ban jayega. Tab `assets/broll` + music pe focus karo ya TTS provider badlo.

---

## 11. Limits (honest note)

- Render is device pe test nahi hua — pehla run khud dekh lena (`--dry-run` se start karo).
- YouTube Data API quota 10,000 units/din: 1 channel roz = ~2,050 units, aaram se fit.
- YPP (monetization) eligibility: 1,000 subscribers + 10M Shorts views/90 din, ya 4,000 watch hours/12 mahine. Policy badalti rehti hai — YouTube ke current page se confirm karo.

