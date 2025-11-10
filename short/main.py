from flask import Flask, request, jsonify, redirect, render_template
import sqlite3
import string
import random

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            original_url TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/shorten", methods=["GET"])
def shorten():
    try:
        data = request.args
        if not data or "url" not in data:
            return jsonify({"error": "URLが指定されていません"}), 400

        original_url = data["url"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("SELECT code FROM urls WHERE original_url = ?", (original_url,))
        row = cur.fetchone()
        if row:
            code = row[0]
        else:
            code = generate_code()
            cur.execute("INSERT INTO urls (code, original_url) VALUES (?, ?)", (code, original_url))
            conn.commit()

        conn.close()
        short_url = request.host_url + "s/" + code
        return jsonify({"short_url": short_url})
    except Exception as e:
        return jsonify({"error": f"予期しないエラー: {e}"}), 500

@app.route("/s/<code>")
def redirect_to_original(code):
    try:
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT original_url FROM urls WHERE code = ?", (code,))
        row = cur.fetchone()
        conn.close()

        if row:
            return redirect(row[0])
        else:
            return jsonify({"error": "指定されたURLは存在しません"}), 404
    except:
        return jsonify({"error": "予期しないエラーが発生しました"}), 500

if __name__ == "__main__":
    app.run(debug=False, port=3116, host="0.0.0.0")