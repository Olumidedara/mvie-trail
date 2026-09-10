# Movie StoryBot

Fully automated, 100% free pipeline that generates **short storytelling videos with AI voiceover** from **public-domain / royalty-free film sources**, then publishes them to GitHub Releases so you can review and post them to YouTube Shorts, TikTok, and Instagram Reels.

```
Source (Internet Archive + Pexels)
   → Analyze (Groq Whisper transcription)
   → Script (Llama 3.3 70B writes the narration)
   → Voiceover (edge-tts neural voices)
   → Assemble (ffmpeg, Ken Burns + burned captions)
   → Export vertical 9:16 + landscape 16:9
   → Publish (GitHub Releases + manifest)
   → Dashboard (Vercel: review, download, schedule)
```

## Repository layout

| Path | Purpose |
|---|---|
| `pipeline/` | Python generation pipeline |
| `dashboard/` | Next.js dashboard (deployed on Vercel) |
| `.github/workflows/pipeline.yml` | GitHub Actions runner (free compute) |
| `config.json` | Shared configuration (sources, voice, sizes) |
| `output/manifest.json` | Latest videos + metadata (committed each run) |

## Two free halves

| Half | Where it runs | Why |
|---|---|---|
| Dashboard (review/download/schedule) | **Vercel free (Hobby)** | Lightweight, serverless-friendly |
| Heavy pipeline (download, TTS, ffmpeg) | **GitHub Actions free runner** (2 vCPU / 7 GB RAM / 14 GB disk, ffmpeg preinstalled) | Only free option with enough resources |

Free Vercel/Render tiers cannot run the heavy pipeline (memory + duration limits), so the compute lives on GitHub Actions and the dashboard just triggers it via the GitHub API. **You do all social media posting manually** — no ToS-risky botting.

## Quick start

1. Follow **SETUP.md** to wire up secrets and first deployment.
2. From the dashboard Home, click **Run now** (or let the schedule fire).
3. GitHub Actions runs `pipeline/pipeline.py`, renders videos, uploads them to GitHub Releases.
4. Download the vertical/landscape MP4s from the dashboard **Library** and post them yourself.

### Local development

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r pipeline/requirements.txt
ffmpeg -version                  # install ffmpeg first

# Generate one video locally (uses Pexels + edge-tts; Groq optional)
$env:PEXELS_API_KEY="..."        # free key from pexels.com/api
python pipeline/pipeline.py run --genre "vintage science fiction" --count 1 --no-upload
```

## Legal note

`config.json` has `source.use_studio_trailers`. Keep it `false` (default). It only uses public-domain (Internet Archive) and royalty-free (Pexels) material, so your derived videos can be monetized. Flipping it to `true` downloads real studio trailers — those are copyrighted: expect Content ID claims, zero ad revenue, and takedown risk.

## Free-tier limits

- GitHub Actions: 2,000 minutes/month on a **public repo** → ~3–6 runs/day.
- Groq free: rate-limited Whisper + LLM → keep `max_videos_per_run` modest.
- Vercel Hobby: cron + function invocations are fine for a solo dashboard.
- GitHub Releases: permanent video storage, 2 GB/file limit.