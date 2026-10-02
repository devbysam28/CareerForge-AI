import os
import json
import re
from flask import Flask, render_template, request, jsonify, session
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "career-chooser-dev-secret")

MODEL = "gemini-3.5-flash-lite"
RESOURCE_LIBRARY = [
    {"name":"freeCodeCamp","url":"https://www.freecodecamp.org/","type":"Learning","tags":["python","javascript","web","data","sql","devops","ai","software","frontend","backend"]},
    {"name":"MDN Web Docs","url":"https://developer.mozilla.org/","type":"Documentation","tags":["javascript","web","html","css","frontend"]},
    {"name":"roadmap.sh","url":"https://roadmap.sh/","type":"Roadmap","tags":["web","backend","frontend","devops","python","javascript","ai","software","cybersecurity"]},
    {"name":"CS50 by Harvard","url":"https://cs50.harvard.edu/","type":"Course","tags":["programming","computer-science","python","web","sql","ai","software"]},
    {"name":"Kaggle Learn","url":"https://www.kaggle.com/learn","type":"Course","tags":["python","data","machine-learning","ai","sql","pandas","numpy"]},
    {"name":"Google Machine Learning Crash Course","url":"https://developers.google.com/machine-learning/crash-course","type":"Course","tags":["machine-learning","ai","python","data"]},
    {"name":"Google Cloud Skills Boost","url":"https://www.cloudskillsboost.google/","type":"Learning","tags":["cloud","devops","data","google-cloud"]},
    {"name":"Microsoft Learn","url":"https://learn.microsoft.com/training/","type":"Learning","tags":["cloud","azure","dotnet","devops","data","ai"]},
    {"name":"AWS Skill Builder","url":"https://skillbuilder.aws/","type":"Learning","tags":["aws","cloud","devops"]},
    {"name":"GitHub Skills","url":"https://skills.github.com/","type":"Hands-on","tags":["git","github","devops","programming","software"]},
    {"name":"Docker Get Started","url":"https://docs.docker.com/get-started/","type":"Documentation","tags":["docker","devops","cloud","deployment"]},
    {"name":"PostgreSQL Tutorial","url":"https://www.postgresql.org/docs/current/tutorial.html","type":"Documentation","tags":["sql","database","backend","data"]},
    {"name":"Python Docs","url":"https://docs.python.org/3/tutorial/","type":"Documentation","tags":["python","programming","backend","data","ai"]},
    {"name":"The Odin Project","url":"https://www.theodinproject.com/","type":"Course","tags":["web","javascript","frontend","backend","software"]},
    {"name":"MIT OpenCourseWare","url":"https://ocw.mit.edu/","type":"Course","tags":["computer-science","programming","math","ai","data"]},
    {"name":"NPTEL","url":"https://nptel.ac.in/","type":"Course","tags":["computer-science","programming","ai","data","cloud","software"]},
    {"name":"SQLBolt","url":"https://sqlbolt.com/","type":"Interactive","tags":["sql","database","data","backend"]},
    {"name":"Hugging Face Course","url":"https://huggingface.co/learn","type":"Course","tags":["ai","machine-learning","nlp","deep-learning","python"]},
    {"name":"Cisco Networking Academy","url":"https://www.netacad.com/","type":"Learning","tags":["networking","cybersecurity","linux"]},
    {"name":"Linux Journey","url":"https://linuxjourney.com/","type":"Interactive","tags":["linux","devops","cybersecurity","cloud"]},
    {"name":"OWASP Web Security Testing Guide","url":"https://owasp.org/www-project-web-security-testing-guide/","type":"Guide","tags":["cybersecurity","web","security"]},
    {"name":"Django Documentation","url":"https://docs.djangoproject.com/en/stable/","type":"Documentation","tags":["python","backend","web"]},
    {"name":"React Learn","url":"https://react.dev/learn","type":"Documentation","tags":["react","javascript","frontend","web"]},
    {"name":"Java Tutorials","url":"https://dev.java/learn/","type":"Learning","tags":["java","programming","backend","software"]},
]


SYSTEM_PROMPT = """You are CareerForge, an AI career-planning engine.
Your job is to transform a student's current profile and career goal into a realistic, actionable roadmap.

IMPORTANT:
- Do not act like a generic chatbot.
- Return ONLY valid JSON. No markdown fences and no commentary.
- Never promise a job or guaranteed salary.
- Respect the user's current education and experience.
- Prefer free learning resources.
- Identify the skills and gaps that should drive resource selection. Do not invent resource URLs; resource matching is handled by the backend.
- Build a practical progression from foundation -> skills -> projects -> proof of skill -> interview preparation.
- Include a 30/60/90-day plan.
- Identify a small set of high-impact missing skills instead of an enormous list.
- Explain why each skill matters for the target.
- Project ideas must produce portfolio evidence.
- If the goal is vague, make a reasonable interpretation and state it.

JSON schema:
{
  "headline": "short personalized headline",
  "career_summary": "2-3 sentence assessment",
  "fit_score": 0-100,
  "fit_label": "Starting Point|Building Momentum|Career Ready",
  "target_role": "role",
  "career_dna": [
    {"dimension":"Technical Foundation|Practical Skills|Portfolio Proof|Career Readiness|Consistency","score":0-100,"note":"short explanation"}
  ],
  "skill_gaps": [
    {"skill":"...", "priority":"High|Medium|Low", "reason":"...", "action":"..."}
  ],
  "roadmap": [
    {"phase":"Phase 1", "title":"...", "duration":"...", "goal":"...", "steps":["...","...","..."], "deliverable":"..."}
  ],
  "days_30_60_90": {
    "first_30":"...",
    "days_31_60":"...",
    "days_61_90":"..."
  },
  "projects": [
    {"title":"...", "difficulty":"Beginner|Intermediate|Advanced", "why":"...", "stack":"...", "outcome":"..."}
  ],
  "resources": [
    {"name":"exact resource name from library", "url":"exact supplied url", "type":"...", "why":"...", "priority":"Must Do|Useful"}
  ],
  "weekly_routine": [
    {"activity":"Learning|Building|Practice|Career", "hours":"...", "description":"..."}
  ],
  "next_7_days":["...","...","...","...","...","...","..."]
}
"""

def clean_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        text = match.group(0)
    return json.loads(text)

def fallback_plan(profile):
    goal = profile.get("goal", "your target career")
    return {
        "headline": f"Your starting roadmap for {goal}",
        "career_summary": "Start with fundamentals, then convert learning into portfolio evidence and interview-ready skills.",
        "fit_score": 35,
        "fit_label": "Starting Point",
        "target_role": goal,
        "career_dna": [
            {"dimension":"Technical Foundation","score":35,"note":"Build the core concepts required by the target role."},
            {"dimension":"Practical Skills","score":30,"note":"Prioritize hands-on exercises and small implementations."},
            {"dimension":"Portfolio Proof","score":20,"note":"Create 2-3 projects that demonstrate the target skills."},
            {"dimension":"Career Readiness","score":25,"note":"Add GitHub, resume evidence and interview practice."},
            {"dimension":"Consistency","score":40,"note":"A repeatable weekly routine will compound progress."}
        ],
        "skill_gaps": [
            {"skill":"Role fundamentals","priority":"High","reason":"Core knowledge is needed before advanced work.","action":"Study one focused topic daily and practice it."},
            {"skill":"Portfolio project","priority":"High","reason":"Employers need evidence of applied ability.","action":"Build one end-to-end project aligned with the target role."},
            {"skill":"Git & GitHub","priority":"Medium","reason":"Version control is standard in software teams.","action":"Publish projects with clean READMEs and commit history."}
        ],
        "roadmap": [
            {"phase":"Phase 1","title":"Foundation","duration":"Weeks 1-3","goal":"Learn the essential concepts.","steps":["Study the core concepts","Solve small practice tasks","Track weak areas"],"deliverable":"Foundation notes + practice repository"},
            {"phase":"Phase 2","title":"Build","duration":"Weeks 4-7","goal":"Turn knowledge into working skills.","steps":["Build a small project","Use Git/GitHub","Document decisions"],"deliverable":"First portfolio project"},
            {"phase":"Phase 3","title":"Proof","duration":"Weeks 8-12","goal":"Become demonstrably job-ready.","steps":["Build a stronger project","Practice interviews","Polish resume and GitHub"],"deliverable":"Portfolio-ready project + resume"}
        ],
        "days_30_60_90": {
            "first_30":"Finish fundamentals and publish one small project.",
            "days_31_60":"Build a stronger role-specific project and improve GitHub.",
            "days_61_90":"Practice interviews, polish your resume and apply your skills."
        },
        "projects": [
            {"title":"Role-focused starter project","difficulty":"Beginner","why":"Turns your first concepts into evidence.","stack":"Choose the simplest stack matching your goal.","outcome":"A GitHub repository with README and demo."},
            {"title":"End-to-end portfolio project","difficulty":"Intermediate","why":"Shows practical problem solving.","stack":"Role-specific stack","outcome":"A deployable project you can explain in interviews."}
        ],
        "resources": RESOURCE_LIBRARY[:6],
        "weekly_routine": [
            {"activity":"Learning","hours":"5 hrs","description":"Concepts and guided lessons"},
            {"activity":"Building","hours":"5 hrs","description":"Hands-on implementation"},
            {"activity":"Practice","hours":"3 hrs","description":"Problems, quizzes or interview questions"},
            {"activity":"Career","hours":"1 hr","description":"GitHub, resume and reflection"}
        ],
        "next_7_days":[
            "Choose one role-specific learning path.",
            "Set up a GitHub repository.",
            "Finish the first core module.",
            "Solve 5 practical exercises.",
            "Build one tiny feature.",
            "Write a short README.",
            "Review progress and adjust next week's plan."
        ]
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/assessment")
def assessment():
    return render_template("assessment.html")

@app.route("/resources")
def resources():
    return render_template("resources.html", resources=RESOURCE_LIBRARY)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/roadmap")
def roadmap():
    plan = session.get("plan")
    if not plan:
        return render_template("empty.html", title="No roadmap yet", message="Complete the Career Assessment first.")
    return render_template("roadmap.html", plan=plan)


# Deterministic resource matching: AI identifies the gaps, but the backend
# decides which validated free resources are shown to the user.
ROLE_KEYWORDS = {
    "ai": ["ai", "machine learning", "ml", "artificial intelligence", "deep learning", "nlp", "data scientist", "data science"],
    "web": ["web developer", "frontend", "front end", "backend", "full stack", "fullstack", "web development"],
    "software": ["software engineer", "software developer", "developer"],
    "data": ["data analyst", "data engineer", "data science", "analytics"],
    "cloud": ["cloud engineer", "cloud", "aws", "azure", "gcp", "devops", "site reliability", "sre"],
    "cybersecurity": ["cybersecurity", "cyber security", "security engineer", "ethical hacking", "penetration testing"],
    "java": ["java developer", "spring boot"],
}

def normalize_terms(text):
    return set(re.findall(r"[a-z0-9+#.]+", text.lower()))

def match_resources(profile, plan, limit=10):
    goal = profile.get("goal", "").lower()
    gaps_text = " ".join(
        f"{g.get('skill','')} {g.get('reason','')} {g.get('action','')}"
        for g in plan.get("skill_gaps", [])
    ).lower()
    combined = f"{goal} {gaps_text}"
    tokens = normalize_terms(combined)

    desired = set()
    for category, keywords in ROLE_KEYWORDS.items():
        if any(k in combined for k in keywords):
            desired.add(category)

    # Extract useful concepts from the AI's gaps.
    for term in ["python","javascript","sql","database","docker","git","github",
                 "machine-learning","machine learning","ai","data","pandas",
                 "numpy","cloud","aws","azure","linux","networking","cybersecurity",
                 "react","java","web","frontend","backend","deployment","nlp"]:
        if term in combined:
            desired.add(term.replace(" ", "-"))

    scored = []
    for resource in RESOURCE_LIBRARY:
        tags = set(resource["tags"])
        score = len(tags & desired)

        # Small extra boost for direct word overlap with the target goal.
        name_tokens = normalize_terms(resource["name"])
        score += len(name_tokens & tokens) * 2

        if score > 0:
            scored.append((score, resource))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Always give the student a useful foundation if matching is sparse.
    selected = [r for _, r in scored[:limit]]
    if len(selected) < 6:
        for r in RESOURCE_LIBRARY:
            if r not in selected:
                selected.append(r)
            if len(selected) >= 6:
                break

    # Turn the technical match into user-facing explanations.
    results = []
    high_gap = plan.get("skill_gaps", [])
    for i, resource in enumerate(selected[:limit]):
        overlap = list(set(resource["tags"]) & desired)
        related_gap = None
        for gap in high_gap:
            gap_text = f"{gap.get('skill','')} {gap.get('reason','')}".lower()
            if any(tag.replace("-", " ") in gap_text or tag in gap_text for tag in overlap):
                related_gap = gap.get("skill")
                break

        if related_gap:
            why = f"Matched to your skill gap: {related_gap}."
            priority = "Must Do" if i < 5 else "Useful"
        elif overlap:
            why = f"Relevant to your {profile.get('goal','career')} path through {', '.join(overlap[:3])}."
            priority = "Useful"
        else:
            why = "A useful foundation resource for your career path."
            priority = "Useful"

        results.append({
            "name": resource["name"],
            "url": resource["url"],
            "type": resource["type"],
            "tags": resource["tags"],
            "why": why,
            "priority": priority
        })
    return results

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    required = ["education", "experience", "skills", "goal"]
    if any(not str(data.get(k, "")).strip() for k in required):
        return jsonify({"error":"Please complete all required fields."}), 400

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error":"GEMINI_API_KEY is not configured. Add it to your local .env or Render Environment Variables."}), 500

    profile = {
        "name": str(data.get("name","")).strip(),
        "education": str(data.get("education","")).strip(),
        "experience": str(data.get("experience","")).strip(),
        "skills": str(data.get("skills","")).strip(),
        "interests": str(data.get("interests","")).strip(),
        "goal": str(data.get("goal","")).strip(),
        "weekly_hours": str(data.get("weekly_hours","8")).strip(),
        "location": str(data.get("location","India")).strip(),
    }

    library_text = json.dumps(RESOURCE_LIBRARY, ensure_ascii=False)
    prompt = f"""{SYSTEM_PROMPT}

STUDENT PROFILE:
{json.dumps(profile, ensure_ascii=False, indent=2)}

RESOURCE_LIBRARY:
{library_text}

Create a personalized plan. Select 6-10 resources that directly match the user's goal. Make the roadmap achievable within the stated weekly hours.
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=MODEL, contents=prompt)
        plan = clean_json(response.text)

        # Resource Engine: use the AI's skill-gap analysis + the user's goal
        # to deterministically match only validated free resources.
        plan["resources"] = match_resources(profile, plan, limit=10)
        plan["resource_engine_note"] = (
            "Resources were matched from CareerForge's validated free-resource "
            "library using your target role and identified skill gaps."
        )

        session["plan"] = plan
        return jsonify(plan)
    except Exception as exc:
        print("AI generation error:", repr(exc))
        return jsonify({"error":"The AI service could not generate the roadmap right now. Check your API key/model and try again."}), 502

@app.route("/api/health")
def health():
    return jsonify({"status":"ok", "ai_configured": bool(os.environ.get("GEMINI_API_KEY"))})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
