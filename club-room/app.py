from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ----------------------
# MongoDB接続
# ----------------------
MONGO_URL = os.environ.get("MONGO_URL")

print("MONGO_URL =", MONGO_URL)

if not MONGO_URL:
    print("⚠ MONGO_URL が設定されていません")

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')

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

WEEKDAYS = ["月","火","水","木","金","土","日"]

# ----------------------
# メイン画面
# ----------------------
@app.route("/")
def index():

    if collection is None:
        return "データベースに接続できていません"

    # ✅ 7日前のデータ削除
    try:
        limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        collection.delete_many({"date": {"$lt": limit_date}})
    except Exception as e:
        print("削除エラー:", e)

    # ✅ 日付取得（フォーマット統一）
    selected_date = request.args.get("date")

    if not selected_date:
        selected_date = datetime.now().strftime("%Y-%m-%d")
    else:
        selected_date = selected_date.replace("/", "-").strip()

    # ✅ 曜日
    dt = datetime.strptime(selected_date, "%Y-%m-%d")
    selected_day = WEEKDAYS[dt.weekday()]

    # ✅ 予約取得
    try:
        reservations = list(collection.find(
            {"date": selected_date},
            {"_id": 0}
        ))

        # ✅ 時間順ソート
        reservations.sort(
            key=lambda x: datetime.strptime(
                x["slot"].split("-")[0], "%H:%M"
            )
        )

    except Exception as e:
        print("DB取得エラー:", e)
        reservations = []

    # ======================
    # ✅ ✅ ✅ リアルタイム使用判定（完全版）
    # ======================
    in_use = False
    current_user = ""

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    now_time = now.time()

    for r in reservations:

        # ✅ 同じ日だけ判定
        if r["date"] != today_str:
            continue

        try:
            start_str, end_str = r["slot"].split("-")

            start_time = datetime.strptime(start_str.strip(), "%H:%M").time()
            end_time = datetime.strptime(end_str.strip(), "%H:%M").time()

            if start_time <= now_time < end_time:
                in_use = True
                current_user = r["name"]
                break

        except Exception as e:
            print("時間処理エラー:", e)

    # ======================

    return render_template(
        "index.html",
        reservations=reservations,
        slots=SLOTS,
        selected_date=selected_date,
        selected_day=selected_day,
        in_use=in_use,
        current_user=current_user,
        today=today_str
    )

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

    # ✅ 日付統一
    date = date.replace("/", "-")

    try:
        # ✅ 重複チェック
        exists = collection.find_one({
            "date": date,
            "slot": slot
        })

        if exists:
            return "その時間はすでに予約されています"

        collection.insert_one({
            "id": str(datetime.now().timestamp()),
            "name": name,
            "date": date,
            "slot": slot
        })

    except Exception as e:
        print("追加エラー:", e)

    return redirect("/?date=" + date)

# ----------------------
# 予約削除
# ----------------------
@app.route("/delete", methods=["POST"])
def delete():

    if collection is None:
        return redirect("/")

    date = request.form.get("date").replace("/", "-")
    slot = request.form.get("slot")
    name = request.form.get("name")

    try:
        collection.delete_one({
            "date": date,
            "slot": slot,
            "name": name
        })
    except Exception as e:
        print("削除エラー:", e)

    return redirect("/?date=" + date)

# ----------------------
# ヘルスチェック
# ----------------------
@app.route("/health")
def health():
    return "OK"

# ----------------------
# 起動
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
``
