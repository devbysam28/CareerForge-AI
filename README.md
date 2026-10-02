# CareerForge — AI Career Chooser

CareerForge is an AI-powered career planning platform. A user enters their education, experience, current skills and target goal. The platform generates:

- Career DNA / readiness snapshot
- Skill-gap analysis
- Phased learning roadmap
- 30/60/90-day action plan
- Portfolio project ideas
- Curated free learning resources
- Weekly routine
- Next 7-day action checklist

## Tech Stack

- Python + Flask
- HTML5/CSS3/JavaScript
- Google Gemini API
- Gunicorn
- Render
- GitHub

## AI differentiation

Unlike a generic chatbot, CareerForge uses a structured career-planning pipeline. The model must return a fixed schema, and resource links are validated against a curated resource library before being shown.

## Run locally

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Set your Gemini key:

Windows PowerShell:
```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
```

macOS/Linux:
```bash
export GEMINI_API_KEY="YOUR_KEY"
```

Run:
```bash
python app.py
```

Open http://127.0.0.1:5000

## Render

Build Command:
`pip install -r requirements.txt`

Start Command:
`gunicorn app:app`

Environment Variables:
- `GEMINI_API_KEY` = your Gemini API key
- `SECRET_KEY` = any long random string
- `GEMINI_MODEL` = `gemini-2.5-flash-lite`

Do not put the API key in GitHub.
