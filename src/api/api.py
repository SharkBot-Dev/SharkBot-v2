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

dotenv.load_dotenv()

app = Flask(__name__, static_folder="./static/")

client = MongoClient("mongodb://localhost:27017/")

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


asgi_app = WSGIMiddleware(app)
