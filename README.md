# SkillSprint AI — SESD Project

A Flask + SQLite career-development starter application with:
- Register / login and per-user planner tasks
- Dashboard, learning tracks and downloadable syllabus text files
- YouTube topic-search links
- Interview speaking practice using browser Web Speech API where supported
- Resume structure/keyword estimate for PDF, DOCX and TXT
- Editable PowerPoint generation from a topic and outline
- General assistant chat endpoint with starter offline guidance
- Responsive animated dashboard UI

## Run on Windows (VS Code)

1. Extract this ZIP.
2. Open the extracted `SkillSprint_AI_SESD` folder in VS Code.
3. Open Terminal and run:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

If PowerShell blocks activation, run this in the same terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

4. Open http://127.0.0.1:5000
5. Register a new account.

## Important notes

- The resume score is a basic checklist/keyword estimate, not an official ATS score or a hiring prediction. For better job-specific review, compare the resume with a target job description.
- Browser speech recognition support varies. Use a supported browser, allow microphone access, and serve the app from localhost or HTTPS. Some browsers may send speech audio to a remote recognition service.
- The chat endpoint is an offline starter assistant, not a connected large language model. To get open-ended AI answers, integrate a model API on the backend and keep its API key in environment variables. Never put API keys in frontend JavaScript.
- SQLite is suitable for a local demo. Before public deployment, set a strong SECRET_KEY, use HTTPS, configure a production database, review upload security, and run with Gunicorn/a suitable hosting platform.
- This ZIP is a clean starter version. It does not overwrite your existing local project automatically. Back up your current folder before merging files.
