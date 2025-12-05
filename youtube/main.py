import hashlib
import hmac
from flask import Flask, request, Response
import xml.etree.ElementTree as ET
from mongo import channels
import requests

from uvicorn.middleware.wsgi import WSGIMiddleware

import settings

app = Flask(__name__)

HMAC_SECRET = settings.HMAC_SECRET.encode()

@app.get("/youtube/callback")
def verify():
    challenge = request.args.get("hub.challenge")
    return Response(challenge, 200)

@app.post("/youtube/callback")
def notification():
    signature = request.headers.get("X-Hub-Signature")
    body = request.data

    if signature:
        algo, received_hash = signature.split("=")

        calc = hmac.new(HMAC_SECRET, body, hashlib.sha1).hexdigest()

        if calc != received_hash:
            return "Invalid signature", 403
    else:
        return "Invalid signature", 403

    xml = request.data.decode("utf-8")
    root = ET.fromstring(xml)

    ns = {
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "atom": "http://www.w3.org/2005/Atom"
    }

    entry = root.find("atom:entry", ns)
    if entry is None:
        return "OK"

    channel_id = entry.find("yt:channelId", ns).text
    video_id = entry.find("yt:videoId", ns).text
    title = entry.find("atom:title", ns).text

    url = f"https://www.youtube.com/watch?v={video_id}"

    cursor = channels.find({"channel_id": channel_id})

    for item in cursor:
        webhook = item.get("webhook_url")
        if webhook:
            requests.post(webhook, json={
                "content": item.get('message', f"{title}\n\n{url}"), "username": "SharkBot Youtube", "avatar_url": "https://yt3.googleusercontent.com/vE6aoNnj0dvL-8sPUMwJ5hQOwsjGhP6q3_MmuwyAc36Jous6GSWVgPnOqKN2KoGsaES8pBKrKA=s900-c-k-c0x00ffffff-no-rj"
            })

    return "OK"

asgi_app = WSGIMiddleware(app)