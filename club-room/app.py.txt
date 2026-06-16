from flask import Flask, render_template, request, redirect
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "data.json"

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

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
# データ読み込み
# ----------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []


# ----------------------
# データ保存
# ----------------------
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------
# メイン画面
# ----------------------
@app.route("/")
def index():

    reservations = load_data()

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # 選択された日付（指定がなければ今日）
    selected_date = request.args.get("date", today_str)

    # 曜日取得
    date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    selected_day = WEEKDAYS[date_obj.weekday()]

    # 選択した日の予約を時間順で取得
    selected_reservations = sorted(
        [r for r in reservations if r["date"] == selected_date],
        key=lambda x: x["slot"]
    )

    # ----------------------
    # 使用中判定
    # ----------------------
    in_use = False
    current_user = None

    now_time = now.time()

    for r in reservations:

        if r["date"] != today_str:
            continue

        start_str, end_str = r["slot"].split("-")

        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()

        if start_time <= now_time <= end_time:
            in_use = True
            current_user = r["name"]
            break

    return render_template(
        "index.html",
        today=today_str,
        selected_date=selected_date,
        selected_day=selected_day,
        reservations=selected_reservations,
        in_use=in_use,
        current_user=current_user,
        slots=SLOTS
    )


# ----------------------
# 予約追加
# ----------------------
@app.route("/add", methods=["POST"])
def add():

    name = request.form["name"]
    date = request.form["date"]
    slot = request.form["slot"]

    # 過去の日付は禁止
    if datetime.strptime(date, "%Y-%m-%d").date() < datetime.now().date():
        return "過去の日付は予約できません"

    reservations = load_data()

    # 重複チェック
    for r in reservations:
        if r["date"] == date and r["slot"] == slot:
            return "その時間帯は予約済みです"

    reservations.append({
        "name": name,
        "date": date,
        "slot": slot
    })

    # 日付→時間帯の順で並び替え
    reservations = sorted(
        reservations,
        key=lambda x: (x["date"], x["slot"])
    )

    save_data(reservations)

    return redirect("/?date=" + date)


# ----------------------
# 予約削除
# ----------------------
@app.route("/delete", methods=["POST"])
def delete():

    reservations = load_data()

    target_date = request.form["date"]
    target_slot = request.form["slot"]
    target_name = request.form["name"]

    reservations = [
        r for r in reservations
        if not (
            r["date"] == target_date
            and r["slot"] == target_slot
            and r["name"] == target_name
        )
    ]

    save_data(reservations)

    return redirect("/?date=" + target_date)


# ----------------------
# 起動
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)