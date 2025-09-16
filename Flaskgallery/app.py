from flask import Flask, render_template, request, redirect, url_for, session
import os, json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
GALLERY_JSON = "gallery.json"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(GALLERY_JSON):
    with open(GALLERY_JSON, "w") as f:
        json.dump([], f)

# Admin credentials
USERNAME = "admin"
PASSWORD = "1234"

# Helpers
def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

def load_gallery():
    with open(GALLERY_JSON) as f:
        return json.load(f)

def save_gallery(images):
    with open(GALLERY_JSON, "w") as f:
        json.dump(images, f, indent=2)

# ---------------- ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def index():
    images = load_gallery()

    # Handle new upload
    if request.method == "POST" and session.get("logged_in"):
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            # Add to gallery with temporary metadata
            images.append({
                "filename": filename,
                "title": "",
                "category": "",
                "date": datetime.now().isoformat()
            })
            save_gallery(images)
        return redirect(url_for("index"))

    # Categories for header buttons
    categories = sorted(set(img["category"] for img in images if img["category"]))
    return render_template("index.html", images=images, logged_in=session.get("logged_in"), categories=categories)

@app.route("/edit/<filename>", methods=["POST"])
def edit(filename):
    if not session.get("logged_in"):
        return redirect(url_for("index"))

    images = load_gallery()
    for img in images:
        if img["filename"] == filename:
            img["title"] = request.form.get("title", img["title"])
            img["category"] = request.form.get("category", img["category"])
            img["date"] = request.form.get("date", img["date"])
            break
    save_gallery(images)
    return redirect(url_for("index"))

@app.route("/delete/<filename>")
def delete(filename):
    if not session.get("logged_in"):
        return redirect(url_for("index"))

    images = load_gallery()
    images = [img for img in images if img["filename"] != filename]
    save_gallery(images)

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)

    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
