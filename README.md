# SmartHire — AI Recruitment Platform

A 3-phase AI-driven recruitment platform that automates resume filtering, online assessments, and AI video interviews.

---

## Quick Start

### 1. Install Dependencies
```cmd
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Phase 1: Resume Filtering (Standalone)
```cmd
# Run backend
python phase1_resume_filter/resume_filter_backend.py

# Or open frontend in browser
phase1_resume_filter/resume_filter_frontend.html
```

### 3. Phase 2 & 3: Start Backend Services
```cmd
python main.py
```

### 4. Open Frontends (Chrome/Edge)

| Phase | File |
|-------|------|
| **Phase 1** | `phase1_resume_filter/resume_filter_frontend.html` |
| **Phase 2** — Aptitude Test | `phase2_test_portal/aptitude_frontend/index.html` |
| **Phase 2** — Coding Test | `phase2_test_portal/coding_frontend/index.html` |
| **Phase 2** — Dashboard | `phase2_test_portal/dashboard/index.html` |
| **Phase 3** — AI Interview | `phase3_ai_interview/interview_frontend/index.html` |

---

## Architecture

```
SmartHire/
├── shared/                          # Shared utilities
│   ├── config.py                    # Configuration (MongoDB, APIs)
│   ├── database.py                  # MongoDB + in-memory fallback
│   └── memory_db.py                 # Demo mode storage
│
├── phase1_resume_filter/            # Phase 1: Resume Filtering
│   ├── resume_filter_backend.py     # NLP-based resume parser (spaCy + PyPDF2)
│   ├── resume_filter_frontend.html  # Web UI for resume upload & filtering
│   ├── key_terms_sample.txt         # Sample keywords for testing
│   ├── key_terms.txt                # Job role keywords
│   └── Example Resumes/             # 5 sample PDF resumes for testing
│
├── phase2_test_portal/              # Phase 2: Online Assessments
│   ├── aptitude_backend/            # Flask API (MCQ grading)
│   ├── aptitude_frontend/           # MCQ test UI
│   ├── coding_backend/              # Flask API (code execution)
│   ├── coding_frontend/             # Monaco Editor UI
│   ├── dashboard/                   # Recruiter leaderboard
│   ├── scoring_engine.py            # Composite scoring
│   └── report_generator.py          # PDF report generation
│
├── phase3_ai_interview/             # Phase 3: AI Video Interview
│   ├── interview_backend/           # Flask-SocketIO WebSocket server
│   ├── interview_frontend/          # WebRTC + Web Speech API UI
│   ├── report/                      # Scoring weights config
│   └── interview_questions.json     # HR question bank by role
│
├── main.py                          # Entry point (starts Phase 2 & 3 backends)
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

---

## Features

| Phase | Feature | Status |
|-------|---------|--------|
| **Phase 1** | Resume Filtering (spaCy NLP + PyPDF2 + keyword matching) | ✅ Completed |
| **Phase 2** | Aptitude Test (60+ MCQs, anti-cheat, timer) | ✅ Completed |
| **Phase 2** | Coding Test (Monaco Editor, local execution) | ✅ Completed |
| **Phase 2** | Recruiter Dashboard (composite scoring) | ✅ Completed |
| **Phase 3** | AI Video Interview (WebRTC + Speech API) | ✅ Completed |
| **Phase 3** | Real-time AI Follow-ups (Ollama or question bank) | ✅ Completed |

---

## Prerequisites

| Component | Required? | Purpose |
|-----------|-----------|---------|
| **Python 3.10+** | ✅ Required | Backend runtime |
| **Chrome/Edge** | ✅ Required | Speech recognition, WebRTC |
| **MongoDB** | ⚠️ Optional | Data persistence (demo mode works without it) |
| **Ollama** | ⚠️ Optional | AI interviewer LLM (question bank fallback available) |

---

## Ports

| Service | Port | Protocol |
|---------|------|----------|
| Aptitude Backend | 5001 | HTTP |
| Coding Backend | 5002 | HTTP |
| Interview Backend | 5003 | HTTP + WebSocket |

---

## Demo Mode

**No MongoDB?** No problem. The platform auto-detects MongoDB availability and falls back to in-memory storage. All features work identically — data is just lost when services stop.

See `README_DEMO_MODE.md` for full details.

---

## Troubleshooting

- **401 Error (Coding Test):** Fixed — now uses local code execution (no API key needed)
- **Interview chat not working:** Fixed — now uses browser Web Speech API
- **MongoDB connection failed:** Normal — demo mode activates automatically

For detailed troubleshooting, see `phase2_test_portal/TROUBLESHOOTING.md`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML + JS + Monaco Editor + WebRTC + Web Speech API |
| **Backend** | Python (Flask + Flask-SocketIO) |
| **Database** | MongoDB (optional) / In-memory fallback |
| **Code Execution** | Local subprocess (no API key) |
| **Speech Recognition** | Browser Web Speech API |
| **AI Interview** | Ollama (optional) / Question bank fallback |
| **TTS** | Browser SpeechSynthesis API |
| **PDF** | ReportLab |

---

**Version:** Prototype v3.0  
**Last Updated:** April 2026
