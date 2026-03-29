import os
from flask import Flask, render_template

app = Flask(__name__)

SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")


@app.route("/")
def dashboard():
    return render_template("dashboard.html", server_url=SERVER_URL)


if __name__ == "__main__":
    port = int(os.environ.get("PARENT_PORT", 5001))
    app.run(debug=True, port=port)
