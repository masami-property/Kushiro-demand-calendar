import pandas as pd
import re
import json
from datetime import datetime

def process_tourism_trends(raw_data_path):
    """手動でコピーした観光トレンドデータを処理し、月ごとのスコアを返す"""
    monthly_data = {}
    try:
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 各月のデータを正規表現で抽出
        # 例: "4月: 123,456" の形式に対応
        matches = re.findall(r'(\d{1,2})月:\s*([\d,]+)', content)
        for month_str, value_str in matches:
            month = int(month_str)
            value = int(value_str.replace(',', ''))
            monthly_data[month] = value

    except FileNotFoundError:
        print(f"Error: Raw data file not found at {raw_data_path}")
        return {}
    except Exception as e:
        print(f"Error processing raw data: {e}")
        return {}

    if not monthly_data:
        print("No monthly data extracted. Please check the raw data format.")
        return {}

    # 月ごとのデータをDataFrameに変換
    df = pd.Series(monthly_data).sort_index()

    # 正規化（最大値を100とする）
    max_value = df.max()
    if max_value > 0:
        normalized_scores = (df / max_value) * 100
    else:
        normalized_scores = df * 0 # 全て0の場合

    # JSON形式で保存するために、キーを文字列の月（例: "01", "02"）に変換
    # calendar_generator.pyで使うために、YYYY-MM形式のキーにする
    # ただし、ここでは年が不明なので、仮に2025年として扱う
    # calendar_generator.pyで使う際に、該当月のスコアを適用する
    output_scores = {}
    current_year = datetime.now().year # スクリプト実行時の年を仮定
    for month, score in normalized_scores.items():
        # 4月から翌年3月までのデータとして扱う
        year_for_key = current_year if month >= 4 else current_year + 1
        month_key = f"{year_for_key}-{month:02d}"
        output_scores[month_key] = score

    return output_scores

if __name__ == "__main__":
    raw_data_file = 'data/raw/tourism_trends_raw_data.txt'
    output_json_file = 'data/processed/monthly_tourism_trends.json'

    monthly_tourism_trends = process_tourism_trends(raw_data_file)

    if monthly_tourism_trends:
        with open(output_json_file, 'w', encoding='utf-8') as f:
            json.dump(monthly_tourism_trends, f, ensure_ascii=False, indent=4)
        print(f"✅ 月ごとの観光トレンドデータを {output_json_file} に保存しました。")
    else:
        print("❌ 月ごとの観光トレンドデータを取得できませんでした。")
