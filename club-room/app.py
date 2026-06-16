from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# ----------------------
# MongoDB接続
# ----------------------
MONGO_URL = os.environ.get("MONGO_URL")

if not MONGO_URL:
    print("⚠ MONGO_URL が設定されていません")

try:
    client = MongoClient(MONGO_URL)
    db = client["clubroom"]
    collection = db["reservations"]
    print("✅ MongoDB接続成功")
except Exception as e:
    print("❌ MongoDB接続エラー:", e)
    collection = None

# ----------------------
# 時間帯
# ----------------------
SLOTS = [
    "09:00-10:30",
    "10:40-12:10",
    "12:10-13:00",
    "13:00-14:30",
    "14:40-16:10",
    "16:20-17:50",
    "18:00-19:30",
    "19:30-21:00"
]

# ----------------------
# メイン画面
# ----------------------
@app.route("/")
def index():
    if collection is None:
        return "データベースに接続できていません"

    try:
        data = list(collection.find({}, {"_id": 0}))
    except Exception as e:
        print("DB取得エラー:", e)
        data = []

    return render_template("index.html", reservations=data, slots=SLOTS)

# ----------------------
# 予約追加
# ----------------------
@app.route("/add", methods=["POST"])
def add():
    if collection is None:
        return "データベースエラー"

    name = request.form.get("name")
    date = request.form.get("date")
    slot = request.form.get("slot")

    if not (name and date and slot):
        return redirect("/")

    try:
        # 重複チェック
        exists = collection.find_one({
            "date": date,
            "slot": slot
        })

        if exists:
            return "その時間はすでに予約されています"

        # データ追加
        collection.insert_one({
            "id": str(datetime.now().timestamp()),
            "name": name,
            "date": date,
            "slot": slot
        })

    except Exception as e:
        print("追加エラー:", e)

    return redirect("/")

# ----------------------
# 予約削除
# ----------------------
@app.route("/delete", methods=["POST"])
def delete():
    if collection is None:
        return redirect("/")

    reservation_id = request.form.get("id")

    if reservation_id:
        try:
            collection.delete_one({
                "id": reservation_id
            })
        except Exception as e:
            print("削除エラー:", e)

    return redirect("/")

# ----------------------
# ヘルスチェック（Render用）
# ----------------------
@app.route("/health")
def health():
    return "OK"

# ----------------------
# 起動
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
