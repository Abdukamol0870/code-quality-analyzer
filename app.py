from flask import Flask, render_template, request
from analyzer import analyze_python

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    code, result, error = "", None, None
    if request.method == "POST":
        code = request.form.get("code", "")
        uploaded = request.files.get("file")
        if uploaded and uploaded.filename:
            if not uploaded.filename.lower().endswith(".py"):
                error = "Faqat .py fayl yuklash mumkin."
            else:
                code = uploaded.read().decode("utf-8", errors="replace")
        if not error:
            if not code.strip():
                error = "Tahlil uchun kod kiriting yoki .py fayl yuklang."
            else:
                result = analyze_python(code)
    return render_template("index.html", code=code, result=result, error=error)

if __name__ == "__main__":
    app.run(debug=True)
