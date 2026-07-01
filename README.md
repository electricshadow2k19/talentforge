# TalentForge — GenvenX Recruiter Productivity AI

**JD + Resume → ATS score, optimized resume, submission package, questions, emails — in one click.**

Product line under **GenvenX Technologies** (IT staffing pillar).

---

## Live app (cloud) — use this

| | URL |
|---|---|
| **App** | **https://talentforge-two.vercel.app** |
| **API health** | https://talentforge-two.vercel.app/api/health |

Open the app in any browser. No local install required.

### Login credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@genvenx.com` | `admin123` |
| **Recruiter** | `hira@genvenx.com` | `recruiter123` |

### What works in production

- Login, dashboard, candidate management
- Recruiter workspace — JD paste/upload, resume from database or ad hoc
- Full pipeline: ATS scoring, gap analysis, temporal review, optimized resume, submission package, emails
- Heuristic mode (no OpenAI key required); set `OPENAI_API_KEY` in Vercel for AI mode

### Architecture

**Vercel full-stack** — React SPA + FastAPI serverless API on the same domain (`talentforge-two.vercel.app`).

Data is bootstrapped automatically on first request (demo admin, recruiter, and sample candidate).

> **Note:** Current cloud deploy uses ephemeral `/tmp` SQLite on Vercel serverless. Data may reset on cold starts. For persistent production data, upgrade to PostgreSQL (see below).

### Optional: persistent PostgreSQL

For production-grade data persistence, choose one:

1. **Neon on Vercel** (recommended, free tier)
   - Vercel dashboard → Integrations → add **Neon** → accept terms
   - Sets `DATABASE_URL` automatically
   - Redeploy: `npx vercel --prod`

2. **Render API + Postgres** (separate API host)
   - [Deploy to Render](https://render.com/deploy?repo=https://github.com/electricshadow2k19/talentforge) (uses `render.yaml`)
   - Set `VITE_API_URL` in Vercel to your Render API URL
   - Redeploy frontend: `npx vercel --prod`

### Redeploy

```powershell
cd TalentForge
npx vercel --prod
```

---

## MVP scope

| Step | Output |
|------|--------|
| 1. JD analysis | Skills, tools, versions, responsibilities |
| 2. Resume analysis | Skills, certs, experience, work history |
| 3. ATS score | Weighted before/after scores |
| 4. Temporal review | Skill/version placement audit |
| 5. Resume optimization | JD-aligned rewrites (no fabrication) |
| 6. Submission package | Summary, strengths, risks |
| 7. Interview questions | Technical, scenario, behavioral |
| 8. Email drafts | Vendor, candidate, manager |

---

## Local development (optional)

For engineers only — end users should use the cloud URL above.

```powershell
.\start-local.ps1
```

Or with Docker:

```powershell
docker compose up
```

---

## API endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | No | Status + AI enabled |
| `/api/auth/login` | POST | No | JWT login |
| `/api/candidates` | GET/POST | Yes | Candidate CRUD |
| `/api/submissions/analyze` | POST | Yes | Full JD pipeline |
| `/api/generate-package` | POST | No | Legacy anonymous demo |

Interactive docs (local): http://localhost:8000/docs

---

## Project structure

```
TalentForge/
├── frontend/          React SPA (Vite + Tailwind)
├── backend/           FastAPI + SQLAlchemy + pipeline services
├── api/               Vercel serverless entrypoint
├── vercel.json        Cloud deployment config
├── render.yaml        Optional Render blueprint (API + Postgres)
├── docker-compose.yml Local dev stack
└── project_scope.txt  Full product spec
```

---

## License

Proprietary — GenvenX Technologies Pvt Ltd
