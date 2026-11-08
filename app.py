import os, re, sqlite3, secrets
from datetime import datetime, date
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
UPLOAD_DIR = BASE / "uploads"
GENERATED_DIR = BASE / "generated"
DB = BASE / "skillsprint.db"
ALLOWED = {"pdf", "docx", "txt"}

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
            created_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            title TEXT NOT NULL, due_date TEXT, done INTEGER DEFAULT 0)""")
        con.execute("""CREATE TABLE IF NOT EXISTS progress(
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            item TEXT NOT NULL, completed INTEGER DEFAULT 0,
            UNIQUE(user_id,item))""")

init_db()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password with at least 8 characters.", "danger")
        else:
            try:
                with db() as con:
                    con.execute("INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)",
                                (name,email,generate_password_hash(password),datetime.now().isoformat()))
                flash("Account created. Please sign in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That email is already registered.", "danger")
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    with db() as con:
        tasks = con.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY due_date LIMIT 4",(session["user_id"],)).fetchall()
        total = con.execute("SELECT COUNT(*) n FROM progress WHERE user_id=?",(session["user_id"],)).fetchone()["n"]
        completed = con.execute("SELECT COUNT(*) n FROM progress WHERE user_id=? AND completed=1",(session["user_id"],)).fetchone()["n"]
    percent = round(completed/total*100) if total else 0
    return render_template("dashboard.html", tasks=tasks, percent=percent, completed=completed, total=total)

@app.route("/learning")
@login_required
def learning():
    paths = [
      ("Python Full Stack Developer","Python, HTML, CSS, JavaScript, Flask, SQL, APIs and deployment","python"),
      ("Data Structures & Algorithms","Complexity, arrays, strings, linked lists, stacks, queues, trees, graphs and DP","dsa"),
      ("AI & Machine Learning","Python data stack, preprocessing, supervised learning, evaluation and projects","ai")
    ]
    return render_template("learning.html", paths=paths)

SYLLABI = {
"python": ("Python Full Stack Developer", [
"Python fundamentals: variables, data types, conditions, loops, functions",
"Object-oriented programming: classes, inheritance, encapsulation, polymorphism",
"HTML5, CSS3, responsive layouts and accessibility",
"JavaScript: DOM, events, fetch API, async/await",
"Backend development with Flask: routes, templates, forms, sessions",
"Databases: SQL, SQLite, joins, CRUD, normalization",
"REST APIs, JSON, authentication, validation and security basics",
"Git/GitHub, testing, debugging and deployment"
]),
"dsa": ("Data Structures & Algorithms", [
"Algorithm analysis: Big-O, time and space complexity",
"Arrays, strings, searching and sorting",
"Hash maps, sets, two pointers and sliding window",
"Linked lists, stacks, queues and recursion",
"Trees, binary search trees, heaps and tries",
"Graphs: BFS, DFS, shortest paths and topological sorting",
"Greedy algorithms, backtracking and dynamic programming",
"Practice: problem solving, dry runs and interview patterns"
]),
"ai": ("AI & Machine Learning", [
"Python, NumPy, pandas, Matplotlib and data cleaning",
"Exploratory data analysis and feature engineering",
"Supervised learning: regression, decision trees, SVM and ensembles",
"Unsupervised learning: clustering and dimensionality reduction",
"Model evaluation: train/test split, cross-validation and metrics",
"Neural network fundamentals and deep learning overview",
"Model deployment with Flask APIs",
"Capstone project, documentation and responsible AI"
])}

@app.route("/syllabus/<track>")
@login_required
def syllabus(track):
    if track not in SYLLABI: return redirect(url_for("learning"))
    title, topics = SYLLABI[track]
    return render_template("syllabus.html", title=title, topics=topics, track=track)

@app.route("/download/syllabus/<track>")
@login_required
def download_syllabus(track):
    if track not in SYLLABI: return redirect(url_for("learning"))
    title, topics = SYLLABI[track]
    safe = re.sub(r"[^A-Za-z0-9]+","_",title).strip("_")
    path = BASE / "static" / "downloads" / f"{safe}_syllabus.txt"
    path.write_text(title + "\n\n" + "\n".join(f"{i+1}. {t}" for i,t in enumerate(topics)), encoding="utf-8")
    return send_from_directory(path.parent, path.name, as_attachment=True)

@app.route("/videos")
@login_required
def videos():
    items = [
      ("Python Full Course","https://www.youtube.com/results?search_query=python+full+course+beginner+to+advanced"),
      ("Full Stack Development with Flask","https://www.youtube.com/results?search_query=flask+full+stack+project+tutorial"),
      ("DSA in Python","https://www.youtube.com/results?search_query=data+structures+algorithms+python+course"),
      ("SQL for Developers","https://www.youtube.com/results?search_query=sql+full+course+for+beginners"),
      ("Technical Interview Preparation","https://www.youtube.com/results?search_query=technical+interview+preparation+computer+science")
    ]
    return render_template("videos.html", items=items)

@app.route("/planner", methods=["GET","POST"])
@login_required
def planner():
    if request.method == "POST":
        title = request.form.get("title","").strip()
        due = request.form.get("due_date","")
        if title:
            with db() as con:
                con.execute("INSERT INTO tasks(user_id,title,due_date) VALUES(?,?,?)",(session["user_id"],title,due))
            flash("Planner task added.", "success")
        return redirect(url_for("planner"))
    with db() as con:
        tasks = con.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY done,due_date",(session["user_id"],)).fetchall()
    return render_template("planner.html", tasks=tasks)

@app.route("/planner/toggle/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):
    with db() as con:
        con.execute("UPDATE tasks SET done=1-done WHERE id=? AND user_id=?",(task_id,session["user_id"]))
    return redirect(url_for("planner"))

@app.route("/planner/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    with db() as con:
        con.execute("DELETE FROM tasks WHERE id=? AND user_id=?",(task_id,session["user_id"]))
    return redirect(url_for("planner"))

@app.route("/communication")
@login_required
def communication():
    questions = ["Tell me about yourself.","Why did you choose Computer Science Engineering?","What are your key technical skills?","Describe a challenging project you worked on.","What are your strengths and an area you are improving?","Where do you see yourself in five years?"]
    return render_template("communication.html", questions=questions)

def extract_text(path, ext):
    if ext == "txt": return path.read_text(encoding="utf-8", errors="ignore")
    if ext == "docx":
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    if ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return ""

@app.route("/resume", methods=["GET","POST"])
@login_required
def resume():
    result = None
    if request.method == "POST":
        f = request.files.get("resume")
        if not f or not f.filename:
            flash("Choose a PDF, DOCX or TXT resume.", "danger")
        else:
            ext = f.filename.rsplit(".",1)[-1].lower() if "." in f.filename else ""
            if ext not in ALLOWED:
                flash("Supported formats: PDF, DOCX and TXT.", "danger")
            else:
                filename = secrets.token_hex(8) + "." + ext
                path = UPLOAD_DIR / filename
                f.save(path)
                content = extract_text(path, ext)
                result = score_resume(content)
                result["filename"] = secure_filename(f.filename)
    return render_template("resume.html", result=result)

def score_resume(text):
    t = text.lower()
    checks = {
      "Contact details": any(x in t for x in ["@", "linkedin", "github"]),
      "Professional summary": any(x in t for x in ["summary","objective","profile"]),
      "Education": any(x in t for x in ["education","b.tech","bachelor","degree"]),
      "Technical skills": any(x in t for x in ["skills","python","java","sql","javascript"]),
      "Projects": "project" in t,
      "Experience / internships": any(x in t for x in ["experience","internship","intern"]),
      "Achievements / certifications": any(x in t for x in ["certification","certificate","achievement"]),
      "Action-oriented impact": any(x in t for x in ["developed","built","implemented","improved","designed"])
    }
    score = round(sum(checks.values()) / len(checks) * 100)
    advice = {
      "Contact details":"Add a professional email, phone number, LinkedIn and GitHub links." ,
      "Professional summary":"Add a short role-focused summary if it helps explain your target role.",
      "Education":"Show your degree, institution and expected graduation date.",
      "Technical skills":"Group relevant skills by category and match them to the target job.",
      "Projects":"Add 2–3 relevant projects with your contribution and technologies.",
      "Experience / internships":"Include internships, volunteering or practical experience where relevant.",
      "Achievements / certifications":"Add credible certifications, awards or measurable achievements.",
      "Action-oriented impact":"Start bullets with strong verbs and quantify outcomes where truthful."
    }
    return {"score":score,"checks":checks,"advice":[advice[k] for k,v in checks.items() if not v],
            "note":"This is a basic keyword/structure estimate, not an official ATS score. Results vary by employer and job description."}

@app.route("/ppt", methods=["GET","POST"])
@login_required
def ppt():
    link = None
    if request.method == "POST":
        title = request.form.get("title","My Presentation").strip() or "My Presentation"
        topic = request.form.get("topic","").strip()
        points = [x.strip() for x in request.form.get("points","").splitlines() if x.strip()]
        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt
            prs = Presentation()
            slide = prs.slides.add_slide(prs.slide_layouts[0])
            slide.shapes.title.text = title
            slide.placeholders[1].text = topic or "Created with SkillSprint AI"
            chunks = [points[i:i+5] for i in range(0,len(points),5)] or [["Introduction","Key concepts","Applications","Conclusion"]]
            for n, chunk in enumerate(chunks,1):
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                slide.shapes.title.text = f"{topic or title} – Part {n}"
                tf = slide.placeholders[1].text_frame
                tf.text = chunk[0]
                for p in chunk[1:]:
                    para = tf.add_paragraph(); para.text = p; para.level = 0
            out = GENERATED_DIR / f"presentation_{secrets.token_hex(4)}.pptx"
            prs.save(out)
            link = url_for("generated_file", filename=out.name)
        except Exception as e:
            flash("PPT generation needs python-pptx. Run: pip install python-pptx. " + str(e), "danger")
    return render_template("ppt.html", link=link)

@app.route("/generated/<filename>")
@login_required
def generated_file(filename):
    return send_from_directory(GENERATED_DIR, filename, as_attachment=True)

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")

@app.route("/api/chat", methods=["POST"])
@login_required
def chat_api():
    msg = request.json.get("message","").strip()
    if not msg: return jsonify(reply="Please type a question.")
    # General-purpose offline helper responses. Replace/extend with a hosted LLM API for generative answers.
    low = msg.lower()
    if any(w in low for w in ["python","code","error","program"]):
        reply = "Let's solve it step by step. Share the code, exact error message, and expected output. I can explain the logic, identify likely bugs, and suggest a corrected version."
    elif any(w in low for w in ["resume","ats","job","internship"]):
        reply = "For career help, start with the target role and job description. Tailor your skills and project bullets to relevant requirements, use clear headings, and quantify genuine results. You can also upload your resume in the ATS Resume Checker."
    elif any(w in low for w in ["interview","speak","communication"]):
        reply = "Try this structure: answer the question directly, give one specific example, explain your action, and finish with the result or lesson. Practise aloud in the Communication Lab."
    elif any(w in low for w in ["study","plan","schedule","time"]):
        reply = "Break the goal into 30–45 minute sessions, choose one measurable outcome per session, and schedule short revision blocks. Add your tasks in the Study Planner."
    else:
        reply = "I can help with programming, debugging, DSA, Python full stack, AI/ML, project ideas, presentations, study planning, resumes, internships and interview preparation. Tell me your goal and any constraints, and I'll work through a solution with you."
    return jsonify(reply=reply)

@app.route("/profile")
@login_required
def profile():
    with db() as con:
        user = con.execute("SELECT name,email,created_at FROM users WHERE id=?",(session["user_id"],)).fetchone()
    return render_template("profile.html", user=user)

@app.errorhandler(413)
def too_large(e):
    flash("File is too large. Maximum upload size is 8 MB.", "danger")
    return redirect(url_for("resume"))

if __name__ == "__main__":
    app.run(debug=True)
