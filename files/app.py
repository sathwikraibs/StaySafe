"""
StaySafe - Main Flask App
"""
from flask import Flask
from url_scanner import url_scanner_bp

app = Flask(__name__)
app.register_blueprint(url_scanner_bp)

@app.route("/")
def home():
    return {"status": "StaySafe API running"}

if __name__ == "__main__":
    app.run(debug=True, port=5000)
