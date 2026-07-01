from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# --------------------------
# MongoDB
# --------------------------
MONGO_URL = os.environ.get("MONGO_URL")

try:
    client = MongoClient(
        MONGO_URL,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    db = client["clubroom"]
    collection = db["reservations"]

    print("✅ MongoDB接続成功")

except Exception as e:
    print("❌ MongoDB接続エラー:", e)
    collection = None

# --------------------------
# 時間帯
# --------------------------
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

WEEKDAYS = [
    "月", "火", "水",
    "木", "金", "土", "日"
]

# --------------------------
# メイン画面
# --------------------------
@app.route("/")
def index():

    if collection is None:
        return "データベースに接続できていません"

    # 日本時間
    now = datetime.utcnow() + timedelta(hours=9)

    # --------------------------
    # 7日前以前削除
    # --------------------------
    try:

        limit_date = (
            now - timedelta(days=7)
        ).strftime("%Y-%m-%d")

        collection.delete_many({
            "日付": {
                "$lt": limit_date
            }
        })

    except Exception as e:
        print("削除エラー:", e)

    # --------------------------
    # 日付取得
    # --------------------------
    selected_date = request.args.get("date")

    if not selected_date:
        selected_date = now.strftime("%Y-%m-%d")

    selected_date = (
        selected_date
        .replace("/", "-")
        .strip()
    )

    # --------------------------
    # 曜日
    # --------------------------
    dt = datetime.strptime(
        selected_date,
        "%Y-%m-%d"
    )

    selected_day = WEEKDAYS[
        dt.weekday()
    ]

    # --------------------------
    # 当日の予約取得
    # --------------------------
    try:

        reservations = list(
            collection.find(
                {"日付": selected_date},
                {"_id": 0}
            )
        )

        reservations.sort(
            key=lambda x:
            datetime.strptime(
                x["スロット"].split("-")[0],
                "%H:%M"
            )
        )

    except Exception as e:
        print("取得エラー:", e)
        reservations = []

    # --------------------------
    # リアルタイム使用状況
    # --------------------------
    in_use = False
    current_user = ""

    today_str = now.strftime("%Y-%m-%d")
    now_time = now.time()

    for r in reservations:

        try:

            db_date = (
                r["日付"]
                .replace("/", "-")
                .strip()
            )

            if db_date != today_str:
                continue

            start_str, end_str = (
                r["スロット"]
                .split("-")
            )

            start_time = datetime.strptime(
                start_str,
                "%H:%M"
            ).time()

            end_time = datetime.strptime(
                end_str,
                "%H:%M"
            ).time()

            if start_time <= now_time < end_time:

                in_use = True
                current_user = r["名称"]
                break

        except Exception as e:
            print("時間判定エラー:", e)

    # --------------------------
    # 表用データ作成
    # --------------------------
    slot_status = []

    for slot in SLOTS:

        reservation = next(
            (
                r
                for r in reservations
                if r["スロット"] == slot
            ),
            None
        )

        if reservation:

            slot_status.append({
                "slot": slot,
                "reserved": True,
                "name": reservation["名称"]
            })

        else:

            slot_status.append({
                "slot": slot,
                "reserved": False,
                "name": ""
            })

    return render_template(
        "index.html",
        slot_status=slot_status,
        selected_date=selected_date,
        selected_day=selected_day,
        in_use=in_use,
        current_user=current_user
    )

# --------------------------
# 予約追加
# --------------------------
@app.route("/add", methods=["POST"])
def add():

    if collection is None:
        return redirect("/")

    name = request.form.get("name")
    date = request.form.get("date")
    slot = request.form.get("slot")

    if not (
        name and
        date and
        slot
    ):
        return redirect("/")

    date = (
        date.replace("/", "-")
        .strip()
    )

    try:

        exists = collection.find_one({
            "日付": date,
            "スロット": slot
        })

        if exists:
            return "その時間帯は予約済みです"

        collection.insert_one({
            "id": str(
                datetime.now().timestamp()
            ),
            "名称": name,
            "日付": date,
            "スロット": slot
        })

    except Exception as e:
        print("追加エラー:", e)

    return redirect(
        "/?date=" + date
    )

# --------------------------
# 削除
# --------------------------
@app.route("/delete", methods=["POST"])
def delete():

    if collection is None:
        return redirect("/")

    date = request.form.get("date")
    slot = request.form.get("slot")
    name = request.form.get("name")

    try:

        collection.delete_one({
            "日付": date,
            "スロット": slot,
            "名称": name
        })

    except Exception as e:
        print("削除エラー:", e)

    return redirect(
        "/?date=" + date
    )

# --------------------------
# ヘルスチェック
# --------------------------
@app.route("/health")
def health():
    return "OK"

# --------------------------
# 起動
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)
