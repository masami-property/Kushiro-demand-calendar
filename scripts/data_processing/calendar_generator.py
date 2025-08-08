import pandas as pd
from datetime import datetime, timedelta
from holiday_parser import HolidayParser
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def generate_calendar_data(events_csv_path, start_year, end_year):
    # イベントデータを読み込む
    df_events = pd.read_csv(events_csv_path)
    # 日付カラムをdatetimeに変換。エラーはNaTに変換する
    df_events["StartDate"] = pd.to_datetime(df_events["StartDate"], errors="coerce")
    df_events["EndDate"] = pd.to_datetime(df_events["EndDate"], errors="coerce")

    # 無効な日付を持つ行を削除
    df_events.dropna(subset=["StartDate", "EndDate"], inplace=True)

    # 祝日パーサーを初期化
    holiday_parser = HolidayParser()

    # 月ごとのトレンドデータを読み込む
    monthly_trends_path = "data/processed/monthly_tourism_trends.json"
    monthly_trends = {}
    try:
        with open(monthly_trends_path, "r", encoding="utf-8") as f:
            monthly_trends = json.load(f)
    except FileNotFoundError:
        print(
            f"Warning: {monthly_trends_path} not found. Monthly tourism trends will not be applied."
        )

    # イベントタイプごとのデフォルトスコア（参加者数0の場合）
    default_scores = {
        "大会": 200,
        "クルーズ": 50,
        "コンサート": 100,
        "イベント": 300,  # 霧フェスのような大規模イベント向け
    }

    calendar_data = {}
    current_date = datetime(start_year, 1, 1).date()
    end_date = datetime(end_year, 12, 31).date()

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        daily_data = {
            "date": date_str,
            "is_holiday": False,
            "holiday_name": None,
            "events": [],
            "demand_score": 0,
            "monthly_trend_score": 0,
            "impact_level": "Low",
        }

        # 祝日情報を追加
        if holiday_parser.is_holiday(current_date):
            daily_data["is_holiday"] = True
            daily_data["holiday_name"] = holiday_parser.get_holiday_name(current_date)
            daily_data["demand_score"] += 50  # 祝日は固定で50点

        # 月ごとのトレンドスコアを加算
        month_key = current_date.strftime("%Y-%m")
        if month_key in monthly_trends:
            daily_data["monthly_trend_score"] = monthly_trends[month_key]
            daily_data["demand_score"] += daily_data["monthly_trend_score"] * 2

        # イベント情報を追加
        for _, event in df_events.iterrows():
            if event["StartDate"].date() <= current_date <= event["EndDate"].date():
                subject_with_emoji = event["Subject"]
                if event["EventType"] == "大会":
                    subject_with_emoji = "🏆 " + subject_with_emoji
                elif event["EventType"] == "クルーズ":
                    subject_with_emoji = "🚢 " + subject_with_emoji
                elif event["EventType"] == "イベント":
                    subject_with_emoji = "🎉 " + subject_with_emoji
                elif event["EventType"] == "コンサート":
                    subject_with_emoji = "🎤 " + subject_with_emoji

                daily_data["events"].append(
                    {
                        "subject": subject_with_emoji,
                        "event_type": event["EventType"],
                        "estimated_attendees": event["EstimatedAttendees"],
                        "location": event["Location"],
                        "impact_level": event["ImpactLevel"],
                    }
                )

                # イベントの推定参加者数に基づいてスコアを加算
                duration = (
                    event["EndDate"].date() - event["StartDate"].date()
                ).days + 1
                score_to_add = 0
                if event["EstimatedAttendees"] > 0:
                    score_to_add = (event["EstimatedAttendees"] / duration) / 5
                else:
                    score_to_add = (
                        default_scores.get(event["EventType"], 100) / duration
                    )

                if event["EventType"] == "クルーズ":
                    score_to_add /= 5  # クルーズ船のウェイトを1/5に

                if event["EventType"] == "大会":
                    if duration > 1:
                        score_to_add += (event["EstimatedAttendees"] / 10) * (
                            duration - 1
                        )
                    if "全国" in event["Subject"] or event["EstimatedAttendees"] >= 500:
                        score_to_add += 50 / duration

                # 霧フェス専用のボーナス点
                if (
                    "霧フェス" in event["Subject"]
                    or "KUSHIRO KIRI FESTIVAL" in event["Subject"]
                ):
                    score_to_add += 200 / duration  # 霧フェスは特別に200点を日割り加算

                daily_data["demand_score"] += score_to_add

        # 曜日効果
        if current_date.weekday() >= 5:  # 土日
            daily_data["demand_score"] += 20

        # スコア計算のログ出力
        event_scores = [
            f"{e['subject']}({score_to_add:.2f})" for e in daily_data["events"]
        ]
        print(
            f"{date_str}: DemandScore={daily_data['demand_score']:.2f}, Holiday={50 if daily_data['is_holiday'] else 0}, Weekend={20 if current_date.weekday() >= 5 else 0}, Trend={daily_data['monthly_trend_score'] * 2}, Events={event_scores}"
        )

        calendar_data[date_str] = daily_data
        current_date += timedelta(days=1)

    # スコアを0～100に正規化
    max_score = max(
        [data["demand_score"] for data in calendar_data.values()], default=1
    )
    for date, data in calendar_data.items():
        data["demand_score"] = (
            (data["demand_score"] / max_score) * 100 if max_score > 0 else 0
        )
        # 正規化後の影響度判定（30点で黄色、50点で赤）
        data["impact_level"] = (
            "High"
            if data["demand_score"] >= 50
            else "Medium" if data["demand_score"] >= 30 else "Low"
        )

    return calendar_data


if __name__ == "__main__":
    events_csv = "data/processed/combined_events.csv"
    start_year = 2025
    end_year = 2026
    output_json_file = "data/processed/calendar_data.json"

    calendar_output = generate_calendar_data(events_csv, start_year, end_year)

    with open(output_json_file, "w", encoding="utf-8") as f:
        json.dump(calendar_output, f, ensure_ascii=False, indent=4)

    print(f"✅ カレンダーデータを {output_json_file} に生成しました。")
