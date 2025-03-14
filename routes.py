from main import app
from flask import render_template
@app.route("/upload", methods=['POST'])
def homepage():
    return render_template("homepage.html")

