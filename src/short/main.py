import sqlite3
import string
import random
import os
from flask import Flask, request, jsonify, redirect, render_template
from urllib.parse import urlparse
from uvicorn.middleware.wsgi import WSGIMiddleware

app = Flask(__name__, static_folder="static")
DATABASE = "database.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by_ip TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_code TEXT NOT NULL,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (url_code) REFERENCES urls (code)
            )
        """)
    print("Database initialized.")

init_db()

def get_client_ip():
    return request.headers.get('CF-Connecting-IP', request.remote_addr)

def generate_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/shorten", methods=["GET"])
def shorten():
    original_url = request.args.get("url")
    ip_address = get_client_ip()
    
    if not original_url:
        return jsonify({"error": "URLが指定されていません"}), 400

    if not original_url.startswith(("http://", "https://")):
        return jsonify({"error": "有効なURLを入力してください"}), 400

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT code FROM urls WHERE original_url = ?", (original_url,))
            row = cur.fetchone()
            
            if row:
                code = row["code"]
            else:
                while True:
                    code = generate_code()
                    cur.execute("SELECT 1 FROM urls WHERE code = ?", (code,))
                    if not cur.fetchone():
                        break
                
                cur.execute(
                    "INSERT INTO urls (code, original_url, created_by_ip) VALUES (?, ?, ?)",
                    (code, original_url, ip_address)
                )
                conn.commit()

        host_url = request.host_url.replace("http://", "https://") if not request.is_secure else request.host_url
        short_url = f"{host_url}s/{code}"
        return jsonify({"short_url": short_url})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "サーバー内部でエラーが発生しました"}), 500

@app.route("/s/<code>")
def redirect_to_original(code):
    ip_address = get_client_ip()
    user_agent = request.headers.get('User-Agent')

    if code == "sharkbot":
        return redirect("https://discord.com/oauth2/authorize?client_id=1322100616369147924&permissions=8&integration_type=0&scope=bot+applications.commands")

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT original_url FROM urls WHERE code = ?", (code,))
            row = cur.fetchone()

            if row:
                cur.execute(
                    "INSERT INTO access_logs (url_code, ip_address, user_agent) VALUES (?, ?, ?)",
                    (code, ip_address, user_agent)
                )
                conn.commit()
                return redirect(row["original_url"])
            else:
                return "指定された短縮URLは見つかりませんでした。", 404

    except Exception as e:
        return jsonify({"error": "エラーが発生しました"}), 500

@app.route("/info")
def info():
    return render_template("info.html")

asgi_app = WSGIMiddleware(app)