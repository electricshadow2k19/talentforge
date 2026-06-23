# TalentForge — Product Brief

## Problem

Recruiter workflow per candidate (~60 minutes):

1. Read JD (15 min)
2. Modify resume (20 min)
3. Format (10 min)
4. Write summary (10 min)
5. Prepare questions (10 min)
6. Emails + RTR (variable)

10 candidates/day = **10 hours** of repetitive work.

## Solution

**One workflow:** Upload JD + Resume → full submission package in **under 2 minutes**.

## Winning feature

Not resume rewriting alone.

**JD → Resume → ATS → Optimized Resume → Summary → Questions → Emails**

in one click.

## Revenue model (future)

| Tier | Price | Target |
|------|-------|--------|
| Solo recruiter | $49/mo | Independent |
| Small firm | $199/mo | 5–15 recruiters |
| Mid-size | $499/mo | 15–50 recruiters |
| Enterprise | Custom | Multi-office |

## Risks

1. Recruiters keep using ChatGPT manually
2. Keyword stuffing hurts quality → mitigate with "no false claims" policy + human review
3. ATS vendors add AI → differentiate on **staffing workflow + GenvenX integration**

## Rating (your assessment)

| Criteria | Score |
|----------|-------|
| Market size | 8/10 |
| Build difficulty | 6/10 |
| GenvenX fit | 10/10 |
| First revenue probability | 8/10 |
| **Overall** | **8.5/10** |

## MVP built (this repo)

- FastAPI backend + React UI
- PDF/DOCX/TXT parsing
- Heuristic + OpenAI pipeline
- All 7 workflow steps in UI tabs

## Next product decisions

1. Pilot with 3 GenvenX recruiters — measure time saved
2. Add DOCX download for optimized resume
3. Brand as **TalentForge by GenvenX**
