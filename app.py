"""
app.py — Flask backend for the Agentic Career Counselling Companion.
Calls IBM Granite-4-h-small on watsonx.ai directly.

Run:
    pip install flask requests
    python app.py
"""
import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="frontend", static_url_path="")

# ── IBM watsonx.ai config ────────────────────────────────────────────────────
WX_URL     = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
MODEL_ID   = "ibm/granite-4-h-small"
PROJECT_ID = "96976d6c-b08d-4aa0-86e8-8c67fdb04468"
API_KEY    = os.environ.get("IBM_API_KEY", "JFgzcUApwzdyD9TWf1UfYhH2dqyfbIcd-ij6uRHVS392")

# ── Market data (embedded, no external calls) ────────────────────────────────
MARKET_DATA = {
    "artificial intelligence": {"demand":"Very High","growth":"38% / 5 yrs","salary":"$110K–$180K","skills":["Python","TensorFlow","MLOps","LLM Fine-tuning"],"sectors":["Tech","Healthcare","Finance"]},
    "data science":            {"demand":"Very High","growth":"35% / 5 yrs","salary":"$95K–$160K","skills":["Python","SQL","Statistics","Power BI"],"sectors":["Finance","E-commerce","Healthcare"]},
    "cybersecurity":           {"demand":"High",     "growth":"32% / 5 yrs","salary":"$85K–$155K","skills":["Ethical Hacking","SIEM","Zero Trust","Cloud Security"],"sectors":["Government","Finance","Defense"]},
    "cloud computing":         {"demand":"Very High","growth":"28% / 5 yrs","salary":"$90K–$150K","skills":["AWS","Kubernetes","Terraform","DevOps"],"sectors":["Tech","Retail","Startups"]},
    "healthcare":              {"demand":"High",     "growth":"15% / 5 yrs","salary":"$60K–$200K","skills":["Clinical Skills","EHR","Diagnostics"],"sectors":["Hospitals","Pharma","Telemedicine"]},
    "ux design":               {"demand":"High",     "growth":"18% / 5 yrs","salary":"$65K–$130K","skills":["Figma","User Research","Design Thinking"],"sectors":["Tech","E-commerce","Media"]},
    "finance":                 {"demand":"Moderate", "growth":"10% / 5 yrs","salary":"$70K–$200K","skills":["Financial Modelling","CFA","Risk Mgmt"],"sectors":["Banking","FinTech","Consulting"]},
    "renewable energy":        {"demand":"High",     "growth":"22% / 5 yrs","salary":"$70K–$130K","skills":["Solar PV","Wind Engineering","Grid Mgmt"],"sectors":["Energy","Government","Manufacturing"]},
}

SUBJECT_MAP = {
    "mathematics":["artificial intelligence","data science","finance"],
    "physics":["renewable energy","cloud computing","engineering"],
    "chemistry":["healthcare","renewable energy"],
    "biology":["healthcare"],
    "computer science":["artificial intelligence","cybersecurity","cloud computing","data science"],
    "statistics":["data science","artificial intelligence","finance"],
    "economics":["finance","data science"],
    "art":["ux design"],
    "design":["ux design"],
    "psychology":["ux design"],
    "business studies":["finance"],
}
INTEREST_MAP = {
    "coding":["artificial intelligence","cybersecurity","cloud computing","data science"],
    "design":["ux design"],
    "helping people":["healthcare"],
    "environment":["renewable energy"],
    "problem solving":["artificial intelligence","data science"],
    "numbers":["finance","data science"],
    "technology":["artificial intelligence","cloud computing","cybersecurity"],
    "creativity":["ux design"],
    "science":["healthcare"],
    "security":["cybersecurity"],
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_iam_token():
    r = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=" + API_KEY,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def call_granite(prompt: str, max_tokens: int = 600) -> str:
    try:
        token = get_iam_token()
        payload = {
            "model_id": MODEL_ID,
            "project_id": PROJECT_ID,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": max_tokens,
                "repetition_penalty": 1.05,
            },
        }
        r = requests.post(
            WX_URL,
            headers={"Accept":"application/json","Content-Type":"application/json",
                     "Authorization":"Bearer " + token},
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["results"][0]["generated_text"].strip()
    except Exception as e:
        return f"[IBM Granite unavailable: {str(e)}. Showing rule-based response.]"


def score_pathways(subjects: list, interests: list) -> list:
    scores = {}
    for s in subjects:
        key = s.get("subject", "").lower()
        w   = float(s.get("score", 0)) / 100.0
        for field in SUBJECT_MAP.get(key, []):
            scores[field] = scores.get(field, 0) + w * 2
    for i in interests:
        for field in INTEREST_MAP.get(i.lower(), []):
            scores[field] = scores.get(field, 0) + 1
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/api/assess", methods=["POST"])
def assess():
    data = request.get_json(force=True)
    name    = data.get("name", "Student")
    grade   = data.get("grade", "")
    age     = data.get("age", "")
    subjects= data.get("subjects", [])
    interests=data.get("interests", [])
    skills  = data.get("skills", "")
    style   = data.get("workStyle", "mixed")

    ranked = score_pathways(subjects, interests)
    top3   = ranked[:3]

    subj_str = ", ".join(f"{s['subject']} ({s['score']}%)" for s in subjects)
    int_str  = ", ".join(interests)
    top_str  = ", ".join(f"{f.title()}" for f, _ in top3)

    prompt = (
        f"You are an expert career counsellor. A student named {name}, age {age}, "
        f"in {grade} has these academic scores: {subj_str}. "
        f"Their interests are: {int_str}. Current skills: {skills}. "
        f"Work style preference: {style}. "
        f"Top matching career fields by analysis: {top_str}. "
        f"Write a personalised career counselling report with: "
        f"1) Overview of strengths, 2) Top 3 recommended career pathways with rationale, "
        f"3) Immediate next steps for the top recommendation, 4) Motivational closing. "
        f"Be specific, encouraging, and concise (under 400 words)."
    )
    advice = call_granite(prompt)

    pathways_out = []
    for field, score in top3:
        md = MARKET_DATA.get(field, {})
        pathways_out.append({
            "field":   field.title(),
            "score":   round(score, 1),
            "demand":  md.get("demand", "N/A"),
            "growth":  md.get("growth", "N/A"),
            "salary":  md.get("salary", "N/A"),
            "skills":  md.get("skills", []),
            "sectors": md.get("sectors", []),
        })

    return jsonify({"advice": advice, "pathways": pathways_out})


@app.route("/api/skillgap", methods=["POST"])
def skillgap():
    data   = request.get_json(force=True)
    name   = data.get("name", "Student")
    target = data.get("targetField", "").lower()
    have   = [s.strip().lower() for s in data.get("currentSkills", "").split(",") if s.strip()]
    months = data.get("months", 6)
    hours  = data.get("hours", 10)

    REQUIRED = {
        "artificial intelligence": ["Python","Statistics","Linear Algebra","Machine Learning","Deep Learning","SQL","Git","Cloud Basics"],
        "data science":            ["Python","SQL","Statistics","Data Visualisation","Excel","Machine Learning Basics","Communication"],
        "cybersecurity":           ["Networking","Linux","Python","Encryption","Risk Assessment","Ethical Hacking","Incident Response"],
        "cloud computing":         ["Linux","Networking","AWS/Azure/GCP","Docker","Kubernetes","CI/CD","Scripting","IaC"],
        "healthcare":              ["Biology","Chemistry","Physics","Communication","Medical Ethics","Anatomy","Clinical Decision Making"],
        "ux design":               ["Figma","User Research","Wireframing","Prototyping","Design Thinking","Typography","Usability Testing"],
        "finance":                 ["Accounting","Excel","Financial Modelling","Economics","Risk Analysis","Statistics","Communication"],
        "renewable energy":        ["Electrical Engineering","Physics","Mathematics","Energy Systems","AutoCAD","Project Management"],
    }
    required = REQUIRED.get(target, [])
    present  = [r for r in required if r.lower() in have]
    missing  = [r for r in required if r.lower() not in have]
    readiness = round(len(present)/len(required)*100, 1) if required else 0

    prompt = (
        f"You are a career coach. Student {name} wants to enter {target.title()}. "
        f"They have these skills: {', '.join(have) or 'none yet'}. "
        f"Skills still needed: {', '.join(missing)}. "
        f"Timeline: {months} months, {hours} hours/week available. "
        f"Create a practical month-by-month study roadmap. Include free resources. "
        f"Be specific and encouraging. Under 350 words."
    )
    roadmap = call_granite(prompt)

    return jsonify({
        "present":   present,
        "missing":   missing,
        "readiness": readiness,
        "roadmap":   roadmap,
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    data    = request.get_json(force=True)
    message = data.get("message", "")
    history = data.get("history", [])

    hist_str = ""
    for h in history[-6:]:
        hist_str += f"User: {h['user']}\nCounsellor: {h['bot']}\n"

    prompt = (
        "You are an empathetic AI career counsellor for students, powered by IBM Granite. "
        "You help students discover career paths, understand job markets, close skill gaps, "
        "and build confidence. Be warm, concise, and actionable.\n\n"
        + hist_str
        + f"User: {message}\nCounsellor:"
    )
    reply = call_granite(prompt, max_tokens=400)
    return jsonify({"reply": reply})


@app.route("/api/market", methods=["GET"])
def market():
    field = request.args.get("field", "").lower()
    if field in MARKET_DATA:
        return jsonify(MARKET_DATA[field])
    return jsonify({"fields": list(MARKET_DATA.keys())})


if __name__ == "__main__":
    os.makedirs("frontend", exist_ok=True)
    app.run(debug=True, port=5000)
