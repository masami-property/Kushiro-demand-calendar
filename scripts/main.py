import sys
import os
import json

# 親ディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'data_processing'))

from tourism_trends_processor import process_tourism_trends
from combine_csv import run_combine_csv
from calendar_generator import generate_calendar_data

def main():
    print("データ処理を開始します...\n")

    # 1. 観光トレンドデータの処理
    raw_data_file = 'data/raw/tourism_trends_raw_data.txt'
    output_json_file = 'data/processed/monthly_tourism_trends.json'
    monthly_tourism_trends = process_tourism_trends(raw_data_file)
    if monthly_tourism_trends:
        with open(output_json_file, 'w', encoding='utf-8') as f:
            json.dump(monthly_tourism_trends, f, ensure_ascii=False, indent=4)
        print(f"✅ 月ごとの観光トレンドデータを {output_json_file} に保存しました。\n")
    else:
        print("❌ 月ごとの観光トレンドデータを取得できませんでした。\n")
        return

    # 2. イベントデータの結合
    run_combine_csv()
    print("\n")

    # 3. カレンダーデータの生成
    events_csv = 'data/processed/combined_events.csv'
    start_year = 2025
    end_year = 2026
    output_calendar_json_file = 'data/processed/calendar_data.json'
    calendar_output = generate_calendar_data(events_csv, start_year, end_year)
    with open(output_calendar_json_file, 'w', encoding='utf-8') as f:
        json.dump(calendar_output, f, ensure_ascii=False, indent=4)
    print(f"✅ カレンダーデータを {output_calendar_json_file} に生成しました。\n")

    print("データ処理が完了しました。")

if __name__ == "__main__":
    main()
