import os
import shutil
import threading
import time
import datetime
from flask import Flask

STATIC_DIR = "static"


def clean_static():
    if os.path.exists(STATIC_DIR):
        shutil.rmtree(STATIC_DIR)
    os.makedirs(STATIC_DIR, exist_ok=True)
    print("[INFO] static フォルダを再生成しました")


def daily_cleaner():
    last_day = datetime.date.today()
    while True:
        time.sleep(60)
        now = datetime.date.today()
        if now != last_day:
            clean_static()
            last_day = now


clean_static()

thread = threading.Thread(target=daily_cleaner, daemon=True)
thread.start()

app = Flask(__name__, static_folder=STATIC_DIR)


@app.get("/")
def index():
    return "これはBotのファイルサーバーです。<br>ほかには何もありません。"


if __name__ == "__main__":
    app.run("0.0.0.0", port=5110, debug=False)
