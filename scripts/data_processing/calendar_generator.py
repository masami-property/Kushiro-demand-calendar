import pandas as pd
from datetime import datetime, timedelta
from holiday_parser import HolidayParser
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def generate_calendar_data(events_csv_path, start_year, end_year):
    # イベントデータを読み込む
    df_events = pd.read_csv(events_csv_path)
    # 日付カラムをdatetimeに変換。エラーはNaTに変換する
    df_events['StartDate'] = pd.to_datetime(df_events['StartDate'], errors='coerce')
    df_events['EndDate'] = pd.to_datetime(df_events['EndDate'], errors='coerce')

    # 無効な日付を持つ行を削除
    df_events.dropna(subset=['StartDate', 'EndDate'], inplace=True)

    # 祝日パーサーを初期化
    holiday_parser = HolidayParser()

    # 月ごとのトレンドデータを読み込む (観光トレンドデータに変更)
    monthly_trends_path = 'data/processed/monthly_tourism_trends.json'
    monthly_trends = {}
    try:
        with open(monthly_trends_path, 'r', encoding='utf-8') as f:
            monthly_trends = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {monthly_trends_path} not found. Monthly tourism trends will not be applied.")

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
            "monthly_trend_score": 0, # 追加
            "impact_level": "Low" # 初期値
        }

        # 祝日情報を追加
        if holiday_parser.is_holiday(current_date):
            daily_data["is_holiday"] = True
            daily_data["holiday_name"] = holiday_parser.get_holiday_name(current_date)
            daily_data["demand_score"] += 50 # 祝日は固定でスコアを加算

        # 月ごとのトレンドスコアを加算
        month_key = current_date.strftime('%Y-%m')
        if month_key in monthly_trends:
            daily_data["monthly_trend_score"] = monthly_trends[month_key] # 追加
            daily_data["demand_score"] += daily_data["monthly_trend_score"] * 2 # トレンドスコアを2倍にして加算

        # イベント情報を追加
        # 複数日にわたるイベントも考慮
        for _, event in df_events.iterrows():
            if event['StartDate'].date() <= current_date <= event['EndDate'].date():
                subject_with_emoji = event['Subject']
                if event['EventType'] == '大会':
                    subject_with_emoji = "🏆 " + subject_with_emoji # 大会に絵文字を追加
                elif event['EventType'] == 'クルーズ':
                    subject_with_emoji = "🚢 " + subject_with_emoji # クルーズに絵文字を追加
                elif event['EventType'] == 'イベント':
                    subject_with_emoji = "🎉 " + subject_with_emoji # イベントに絵文字を追加
                elif event['EventType'] == 'コンサート':
                    subject_with_emoji = "🎤 " + subject_with_emoji # コンサートに絵文字を追加

                daily_data["events"].append({
                    "subject": subject_with_emoji,
                    "event_type": event['EventType'],
                    "estimated_attendees": event['EstimatedAttendees'],
                    "location": event['Location'],
                    "impact_level": event['ImpactLevel']
                })
                # イベントの推定参加者数に基づいてスコアを加算
                # 開催期間で日割り計算
                duration = (event['EndDate'].date() - event['StartDate'].date()).days + 1
                
                score_to_add = 0
                if event['EstimatedAttendees'] > 0:
                    # 基本の寄与度を上げるため、分母を小さくする（例: 10人あたり1点 -> 5人あたり1点）
                    score_to_add = (event['EstimatedAttendees'] / duration) / 5
                else:
                    # 人数不明の場合、固定で100点を日割り加算（以前の50点から増やす）
                    score_to_add = 100 / duration

                if event['EventType'] == 'クルーズ':
                    score_to_add /= 5 # クルーズ船のウェイトを1/5に減らす（変更なし）
                
                # 大会イベントの追加重み付け
                if event['EventType'] == '大会':
                    # 複数日にわたる大会の場合、宿泊需要を考慮してスコアを増幅
                    if duration > 1:
                        # 参加者数に応じて追加スコアを加算 (例: 参加者10人あたり1点)
                        score_to_add += (event['EstimatedAttendees'] / 10) * (duration - 1) 
                    
                    # 既存のボーナスロジック
                    if "全国" in event['Subject'] or event['EstimatedAttendees'] >= 500:
                        score_to_add += 50 / duration # 追加で50点を日割り加算

                daily_data["demand_score"] += score_to_add

        # 曜日効果 (例: 土日はスコアを加算)
        if current_date.weekday() >= 5: # 土曜日(5)または日曜日(6)
            daily_data["demand_score"] += 20

        # 最終的なImpactLevelの決定
        if daily_data["demand_score"] >= 1000:
            daily_data["impact_level"] = "High"
        elif daily_data["demand_score"] >= 300:
            daily_data["impact_level"] = "Medium"
        else:
            daily_data["impact_level"] = "Low"

        calendar_data[date_str] = daily_data
        current_date += timedelta(days=1)

    return calendar_data

if __name__ == "__main__":
    events_csv = 'data/processed/combined_events.csv'
    start_year = 2025
    end_year = 2026
    output_json_file = 'data/processed/calendar_data.json'

    calendar_output = generate_calendar_data(events_csv, start_year, end_year)

    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(calendar_output, f, ensure_ascii=False, indent=4)

    print(f"✅ カレンダーデータを {output_json_file} に生成しました。")
