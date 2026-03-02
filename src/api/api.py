from flask import (
    Flask,
    render_template,
    request,
    redirect,
    make_response,
    send_file,
    jsonify,
)
from pymongo import MongoClient
from discord import SyncWebhook
from uvicorn.middleware.wsgi import WSGIMiddleware
import dotenv
import os
from flask_cors import CORS

dotenv.load_dotenv()

app = Flask(__name__, static_folder="./static/", template_folder="./Templates/")
CORS(app)

client = MongoClient("mongodb://localhost:27017/")

# サーバーごとの経済情報取得
@app.get("/economy/<guildid>")
def economy_getinfo(guildid: str):
    data = {}
    db = client["Main"].ServerMoneyCurrency
    _id = f"{guildid}"
    dbfind = db.find_one({"_id": _id}, {"_id": False})
    if not dbfind:
        data["currency"] = "コイン"
        return jsonify(data)
    data["currency"] = dbfind.get("Name", "コイン")
    return jsonify(data)

# そのユーザーが持っているお金を取得
@app.get("/economy/<guildid>/<userid>")
def economy_getmoney(guildid: str, userid: str):
    data = {}
    db = client["Main"].ServerMoney
    user_data = db.find_one({"_id": f"{guildid}-{userid}"}, {"_id": False})
    if not user_data:
        data["money"] = 0
        data["bank"] = 0
        return jsonify(data)
    data["money"] = user_data.get('count', 0)
    data["bank"] = user_data.get('bank', 0)
    return jsonify(data)

# お金をアップデート
# ※APIKey必要
@app.patch("/economy/<guildid>/<userid>")
def economy_patchmoney(guildid: str, userid: str):
    api_key = request.headers.get('Authorization')
    if not api_key:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        g_id = int(guildid)
    except ValueError:
        return jsonify({"error": "指定形式が正しくありません"}), 400

    apikey_db = client["SharkAPI"].APIKeys
    key = apikey_db.find_one({
        "guild_id": g_id
    })
    if not key:
        return jsonify({"error": "Unauthorized"}), 401

    if api_key != key.get('apikey'):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    db = client["Main"].ServerMoney
    update_fields = {}

    try:
        if 'money' in data:
            update_fields["count"] = int(data["money"])
        if 'bank' in data:
            update_fields["bank"] = int(data["bank"])
    except ValueError:
        return jsonify({"error": "数値形式が正しくありません"}), 400

    if not update_fields:
        return jsonify({"error": "更新する項目がありません"}), 400

    result = db.update_one(
        {"_id": f"{guildid}-{userid}"},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return jsonify({"error": "指定されたユーザーが見つかりません"}), 404

    return jsonify({"success": True})

def add_topgg(id_: str):
    db = client["Main"].TOPGGVote
    user_data = db.find_one({"_id": int(id_)})
    if user_data:
        db.update_one({"_id": int(id_)}, {"$inc": {"count": 1}})
        return True
    else:
        db.insert_one({"_id": int(id_), "count": 1})
        return True

@app.route("/topgg/webhook", methods=["GET", "POST"])
def topgg_vote_webhook():
    apikey = os.environ.get("APIKEY")
    auth = request.headers.get("Authorization")
    if auth != apikey:
        return "Unauthorized", 401
    data = request.json
    if not data:
        return "No data", 400
    try:
        add_topgg(data["user"])
        url = os.environ.get("WEBHOOK")
        web = SyncWebhook.from_url(url)
        web.send(content=f"<@{data['user']}> さんがVoteをしてくれました！")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        print(f"Vote Error: {e}")
        return "VoteError"

# ドキュメント
@app.get("/docs")
def docs():
    return render_template("docs.html")

@app.get("/")
def index():
    return redirect("/docs")

asgi_app = WSGIMiddleware(app)
