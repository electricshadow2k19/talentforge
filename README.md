# TalentForge — GenvenX Recruiter Productivity AI

**JD + Resume → ATS score, optimized resume, submission package, questions, emails — in one click.**

Product line under **GenvenX Technologies** (IT staffing pillar).

---

## MVP scope (v0.1)

| Step | Output |
|------|--------|
| 1. JD analysis | Mandatory/nice skills, experience, visa, location, remote/hybrid |
| 2. Resume analysis | Skills, certs, experience, contact, visa |
| 3. ATS score | Section scores + overall + missing keywords |
| 4. Resume optimization | JD-aligned rewrites (no false claims) |
| 5. Submission package | Summary, strengths, risks |
| 6. Interview questions | Technical, scenario, client, recruiter screen |
| 7. Email drafts | Vendor, candidate, manager |

**Cut from v1:** Job boards, CRM, payroll, multi-tenant billing, bench search, vendor intelligence.

**Success metric:** ~60 min → under 5 min per submission; 5 paying recruiters in 90 days.

---

## Live deployment (Vercel + Render)

| Service | Host | URL |
|---------|------|-----|
| **Web UI** | Vercel | https://talentforge.vercel.app |
| **API** | Render | https://talentforge-api.onrender.com |

### One-click backend (Render)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/electricshadow2k19/talentforge)

After deploy, set `OPENAI_API_KEY` in Render dashboard (optional).

### Frontend (Vercel)

1. Import repo https://github.com/electricshadow2k19/talentforge
2. **Root directory:** `frontend`
3. **Environment variable:** `VITE_API_URL` = `https://talentforge-api.onrender.com`
4. Deploy

Or CLI: `cd frontend && npx vercel --prod`

---

## Quick start (local)

### Backend (port 8000)

```bash
cd TalentForge/backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env            # add OPENAI_API_KEY for AI mode
uvicorn app.main:app --reload --port 8000
```

### Frontend (port 5173)

```bash
cd TalentForge/frontend
npm install
npm run dev
```

Open **http://localhost:5173** → click **Load sample** → **Generate submission package**.

---

## Modes

| Mode | When | Quality |
|------|------|---------|
| **AI** | `OPENAI_API_KEY` set in `.env` | Best — GPT-4o-mini structured JSON |
| **Heuristic** | No API key | Good for demo — keyword/skill matching |

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Status + AI enabled |
| `/api/generate-package` | POST | Multipart: `job_description`, `resume`, or `jd_file`, `resume_file` |
| `/api/generate-package/json` | POST | JSON body `{ job_description, resume }` |

Docs: http://localhost:8000/docs

---

## Project structure

```
TalentForge/
├── README.md
├── PRODUCT.md              # Vision, pricing, roadmap
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── services/pipeline.py
│   │   └── parsers/document.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.tsx
        └── components/ResultsPanel.tsx
```

---

## Roadmap

### Phase 2 (weeks 6–8)
- DOCX resume export (formatted)
- Submission history (SQLite)
- RTR package template

### Phase 3 (months 3–4)
- Multi-tenant auth
- Stripe billing ($49 / $199 / $499)
- Candidate ranking (batch upload)

### Phase 4
- Bench database search
- Vendor intelligence

---

## GenvenX fit

TalentForge automates the **daily workflow** recruiters already do manually — directly supports GenvenX staffing revenue, not generic Q&A.

**Positioning:** *Workflow automation, not another ChatGPT tab.*

---

## License

Proprietary — GenvenX Technologies Pvt Ltd
