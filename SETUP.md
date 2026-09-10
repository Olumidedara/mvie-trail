# Setup Guide

Everything is free. You need: GitHub (free), Vercel (free), two free API keys.

## 1. Create the GitHub repo

1. Create a new **public** repository (public = free Actions minutes).
2. Push this project to it. The repo must contain `pipeline/`, `.github/workflows/pipeline.yml`, `config.json`.

## 2. Free API keys

| Key | Where | What it powers |
|---|---|---|
| `PEXELS_API_KEY` | https://www.pexels.com/api/ (free, instant) | Stock video footage |
| `GROQ_API_KEY` | https://console.groq.com/keys (free tier) | Whisper transcription + Llama script writing |

Optional: skip Groq and the pipeline still works with built-in fallback scripts (no analysis/smart writing).

## 3. GitHub Actions secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

- `PEXELS_API_KEY`
- `GROQ_API_KEY`

Test it: **Actions → run-pipeline → Run workflow**. First run downloads enough to render a video.

## 4. GitHub PAT for triggering from the dashboard

The dashboard triggers runs via the GitHub API, so it needs a token:

1. GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. Repository access: **Only select repositories** → your repo.
3. Permissions → **Actions: Read and write** and **Contents: Read and write** (needed to commit `output/manifest.json`).
4. Copy the token (starts with `github_pat_...`). Save it as `GH_PAT` in Vercel (server-side only).

## 5. Deploy the dashboard on Vercel

1. vercel.com → **Add New → Project** → import your repo.
2. **Root Directory → `dashboard`** (it's a monorepo; the frontend lives there).
3. Framework preset: **Next.js** (auto-detected).
4. Environment variables (Project → Settings → Environment Variables):

   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_GITHUB_OWNER` | your GitHub username |
   | `NEXT_PUBLIC_GITHUB_REPO` | your repo name |
   | `GH_PAT` | the fine-grained token from step 4 |
   | `CRON_SECRET` | any random string (protects `/api/cron`) |

5. **Link a KV Store** (Storage → Create → KV → free) so your schedule persists. Vercel injects `KV_URL` automatically.
6. Deploy. The dashboard at `https://<your-app>.vercel.app` now has Home / Library / Settings.

## 6. Verify the schedule

The `dashboard/vercel.json` registers `/api/cron` every 15 minutes, which fires generations when your schedule says so. Check Settings → Schedule on the dashboard.

## Cost summary

- GitHub Actions free minutes (public repo) — $0
- Groq free tier — $0
- Pexels free API — $0
- edge-tts (Microsoft) — $0
- Vercel Hobby + KV — $0

## Troubleshooting

- **No videos in Library after a run** → open the Actions run logs; almost all errors are printed there.
- **Run now button error "Missing GH_PAT"** → set `GH_PAT` in Vercel env vars and redeploy.
- **Dispatch is 403** → the fine-grained token needs **Actions: Read and write**.
- **Manifest not updating** → check **Contents: Read and write** permission and that the workflow's `git push` step isn't rejected (`[skip ci]` is used to avoid re-triggering).
- **Groq rate limited** → lower `max_videos_per_run` in `config.json` or the dashboard schedule.