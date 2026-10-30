# SmartHire Local

One offline browser workspace for role setup, resume screening, aptitude and coding tests, a structured interview, face comparison, and recruiter reports. The active app binds to `127.0.0.1` and makes no paid API calls.

## Start

Double-click [START_SMARTHIRE.cmd](START_SMARTHIRE.cmd), then open `http://127.0.0.1:5000`. Python and the packages in [app/requirements.txt](app/requirements.txt) must be installed once. For development:

```powershell
cd app
python -m pip install -r requirements.txt
python main.py
```

The local question banks, face models, and Whisper model are bundled in `app/`; runtime use does not download models. A clean-machine `.exe` installer is still planned.

## Walkthrough

1. Pick a predefined role template or enter a role. Set Phase 1 weights and choose **Beginner**, **Intermediate**, or **Advanced** for aptitude, coding, and interview. Advanced coding uses a weighted shortest-path problem.
2. Add a candidate using a PDF or text. The three [fictitious example resumes](examples/resumes) can fill the form and are also downloadable as PDFs.
3. Review the weighted resume match, complete the tests, and answer interview questions by typing or locally transcribed speech. The interviewer has motion graphics and can attempt spoken questions through a local Windows voice. Interview answers receive no automatic quality percentage; a recruiter rates each answer on a 0–4 rubric in the dashboard.
4. With candidate consent, add a reference photo and start the camera. The app draws a face box and displays an **uncalibrated cosine similarity score**. A three-frame capture returns **match**, **no match**, or **inconclusive** automatically. The camera check is separate from the hiring score.
5. In the dashboard, choose **View analysis** for a candidate. This opens an inline four-phase score breakdown, the points each phase contributed to the overall score, a five-point evidence summary, and expandable resume and interview details. Download the PDF report there if needed.

## Project layout

```text
app/                 Active Flask app, web UI, tests, local banks and models
examples/resumes/    Fictitious sample PDFs
docs/plans/          Architecture and verification notes
docs/presentations/  Earlier presentations
archive/             Original prototype, standalone face app and old environments
START_SMARTHIRE.cmd  One-command development launcher
```

The active SQLite database is `app/unified/smarthire.sqlite3`; it contains candidate information. The archive retains a historical database copy from before the reorganization. Keep both private.

## Current limits

- This is a local demo, not a release-ready HR product. The coding runner is not isolated from the host; use only trusted submissions. There is no recruiter authentication yet.
- Face comparison uses OpenCV SFace and MediaPipe with a simple motion check. The displayed score is **similarity, not a probability of identity**. Motion alone can be spoofed; thresholds need validation on the intended cameras and population before real identity decisions. No face images or embeddings are persisted by the active app, and an inconclusive result can be retried. Model redistribution rights still need review.
- The interview uses structured questions and local Whisper transcription, not a conversational local LLM. Windows voice playback depends on the installed voice; this development machine currently falls back to written questions.
- Earlier interview percentages came from answer length and question-word overlap and could reward irrelevant responses. They are retained only as `legacy_heuristic_score` in the database, excluded from active interview and overall scores, and replaced by the recruiter rubric. The pre-migration database backup is `app/unified/backups/smarthire-pre-rubric-2026-10-07.sqlite3`.
- Resume extraction needs machine-readable PDFs. Scores support HR review and are not automatic hiring decisions.

Run checks from `app/` with `python -m unittest unified.test_app -v`. See [the architecture](docs/plans/PRODUCT_ARCHITECTURE_PLAN.md) and [release verification](docs/plans/PLAN_VERIFICATION.md) for remaining gates.
