import html
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    make_response,
    send_file,
    jsonify,
    session,
    url_for,
    session,
)
from pymongo import MongoClient
import json
import settings

import requests

from uvicorn.middleware.wsgi import WSGIMiddleware

app = Flask(__name__, static_folder="./static/", template_folder="./Templates/")

client = MongoClient("mongodb://localhost:27017/")


@app.route("/", methods=["GET"])
def main():
    return render_template("index_3.html")


@app.route("/server/<server_id>", methods=["GET"])
def server_page(server_id):
    cp = client["MainTwo"].ServerPage

    try:
        guild = cp.find_one({"Guild": int(server_id)}, {"_id": False})
    except:
        return "サーバーIDは数字で指定してください。"

    if guild is None:
        return "そのサーバーは存在しません。"

    return render_template(
        "sites.html",
        name=guild.get("Name", "？？？"),
        text=guild.get("Text", "？？？"),
        invite=guild.get("Invite", "mUyByHYMGk"),
        icon=guild.get("Icon", "https://emojicdn.elk.sh/🐟"),
    )


@app.route("/server", methods=["GET"])
def server():
    cp = client["Main"].Register

    pipeline = [
        {
            "$addFields": {
                "has_created_at": {"$cond": [{"$ifNull": ["$Up", False]}, 1, 0]}
            }
        },
        {"$sort": {"has_created_at": -1, "Up": -1}},
    ]
    results_cursor = cp.aggregate(pipeline)

    servers = list(results_cursor)

    return render_template("server.html", server=servers, ct=len(servers))


def get_serverban(guilds, guild: str):
    try:
        db = client["Main"].GuildBAN
        for g in guilds:
            usermoney = db.find_one(
                {"BANGuild": g["id"], "Guild": guild}, {"_id": False}
            )
            if usermoney is None:
                continue
            else:
                return True
        return False
    except:
        return False


def add_role(token: str, user_id: str, guild_id: str, role_id: str):
    head = {"Authorization": "Bot " + token, "Content-Type": "application/json"}
    role = requests.put(
        "https://discord.com/api/guilds/"
        + guild_id
        + "/members/"
        + user_id
        + "/roles/"
        + role_id,
        headers=head,
    )
    return role.status_code


@app.route("/cookie", methods=["GET"])
def cookie():
    try:
        authorization_code = request.args.get("code")

        request_postdata = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": "https://www.sharkbot.xyz/cookie",
        }
        accesstoken_request = requests.post(
            "https://discord.com/api/oauth2/token", data=request_postdata
        )

        responce_json = accesstoken_request.json()

        access_token = responce_json["access_token"]

        user_info = requests.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()

        resp = make_response(redirect("/login"))
        resp.set_cookie("user_info", json.dumps(user_info))

        return resp
    except:
        return f"Error."


@app.route("/invite_auth", methods=["GET"])
def invite_auth_loading():
    code = request.args.get("code")
    state = request.args.get("state", "")
    return render_template("loading.html", code=code, state=state)


@app.route("/invite_auth_backend", methods=["POST"])
def invite_auth_backend():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "reason": "Jsonではないです。"}), 400

        authorization_code = data.get("code")
        state = data.get("state")
        turnstile_token = data.get("turnstile_token")

        if not authorization_code or not state:
            return jsonify({"status": "error", "reason": "不正なURLです。"}), 400

        if not turnstile_token:
            return jsonify(
                {"status": "error", "reason": "キャプチャが確認できません。"}
            ), 400

        db = client["Main"].MemberAddAuthRole
        usermoney = db.find_one({"Code": state}, {"_id": False})
        if usermoney is None:
            return jsonify(
                {"status": "error", "reason": "一度認証に使われたようです。"}
            ), 400

        ts_verify = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": settings.CAPTURE_KEY,
                "response": turnstile_token,
                "remoteip": request.remote_addr,
            },
            timeout=5,
        ).json()

        if not ts_verify.get("success"):
            return jsonify(
                {"status": "error", "reason": "キャプチャ認証に失敗しました。"}
            ), 403

        request_postdata = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": "https://www.sharkbot.xyz/invite_auth",
        }
        accesstoken_request = requests.post(
            "https://discord.com/api/oauth2/token", data=request_postdata
        )
        responce_json = accesstoken_request.json()

        if "access_token" not in responce_json:
            return jsonify(
                {"status": "error", "reason": "Discord OAuth token request failed"}
            ), 400

        access_token = responce_json["access_token"]

        user_info = requests.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()

        guilds = requests.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()

        db.delete_one({"Code": state})
        che = get_serverban(guilds, usermoney["Guild"])
        if che:
            return jsonify(
                {
                    "status": "error",
                    "reason": "サーバーオーナーが禁止しているサーバーに参加しています。",
                }
            ), 400

        add_role(settings.TOKEN, user_info["id"], usermoney["Guild"], usermoney["Role"])

        resp = make_response(
            jsonify(
                {
                    "status": "success",
                    "redirect": "/login",
                    "message": html.escape(
                        usermoney.get(
                            "Message", "このままページを閉じてもらって構いません。"
                        )
                    ),
                }
            )
        )
        resp.set_cookie("user_info", json.dumps(user_info))
        return resp

    except Exception as e:
        return jsonify({"status": "error"}), 500


@app.route("/autherrorpage", methods=["GET"])
def auth_error_page():
    return render_template("auth_error.html")


@app.route("/login", methods=["GET"])
def login():
    try:
        try:
            access_token = request.cookies.get("user_info")
        except:
            return render_template(
                "login.html",
                name=f"未ログイン",
                icon="https://www.sharkbot.xyz/static/LoginUser.png",
            )
        user = request.cookies.get("user_info")
        us = json.loads(user)
        return render_template(
            "login.html",
            name=us["username"],
            icon=f"https://cdn.discordapp.com/avatars/{us['id']}/{us['avatar']}",
        )
    except:
        return render_template(
            "login.html",
            name=f"未ログイン",
            icon="https://www.sharkbot.xyz/static/LoginUser.png",
        )


asgi_app = WSGIMiddleware(app)
