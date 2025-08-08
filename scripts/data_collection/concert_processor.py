import pandas as pd
import re
from datetime import datetime

def parse_date_str(date_str):
    """日付文字列を YYYY-MM-DD 形式に変換"""
    if not date_str:
        return ""
    
    # 例: 2025/9/20(土) -> 2025-09-20
    match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return f"{year}-{month:02d}-{day:02d}"
    return date_str

def estimate_attendees_from_venue(venue_name):
    """会場名から推定集客数を返す"""
    if "コーチャンフォー釧路文化ホール" in venue_name or "釧路市民文化会館" in venue_name:
        return 1500  # 大ホールを想定
    elif "北海道立釧路芸術館" in venue_name:
        return 100  # アートホールを想定
    else:
        return 0

def get_impact_level(attendees):
    """集客数から影響度レベルを判定する"""
    if attendees >= 1000:
        return "High"
    elif 300 <= attendees < 1000:
        return "Medium"
    else:
        return "Low"

def process_concert_data(raw_data_path):
    """手動でコピーしたコンサート情報を処理し、DataFrameを返す"""
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 各コンサート情報をブロックに分割
    # 「コンサート」または「演劇・ステージ・舞台」で始まる行を区切りとする
    concert_blocks = re.split(r'(コンサート|演劇・ステージ・舞台)\n', content)[1:]
    
    concerts = []
    for i in range(0, len(concert_blocks), 2):
        event_type_raw = concert_blocks[i].strip()
        block_content = concert_blocks[i+1].strip()

        subject_match = re.match(r'(.+?)\n公演日：', block_content, re.DOTALL)
        subject = subject_match.group(1).strip() if subject_match else ""

        date_match = re.search(r'公演日：\n(.+?)\n会場：', block_content, re.DOTALL)
        date_str = date_match.group(1).strip() if date_match else ""
        
        venue_match = re.search(r'会場：\n(.+?)\n販売方法', block_content, re.DOTALL)
        venue = venue_match.group(1).strip() if venue_match else ""

        start_date = parse_date_str(date_str.split('～')[0].strip())
        end_date = parse_date_str(date_str.split('～')[-1].strip()) if '～' in date_str else start_date

        estimated_attendees = estimate_attendees_from_venue(venue)
        impact_level = get_impact_level(estimated_attendees)

        concerts.append({
            'EventType': 'コンサート',
            'Subject': subject,
            'StartDate': start_date,
            'EndDate': end_date,
            'EstimatedAttendees': estimated_attendees,
            'Location': venue,
            'ImpactLevel': impact_level,
            'DataSource': 'l-tike.com',
            'LastUpdated': datetime.now().strftime("%Y-%m-%d")
        })
    return pd.DataFrame(concerts)

if __name__ == "__main__":
    raw_data_file = 'data/raw/concert_raw_data.txt'
    output_csv_file = 'data/processed/r7-concert_converted.csv'

    # ダミーデータを作成（ユーザーが手動で作成するファイルを想定）
    dummy_content = """
コンサート
世界旅行音楽団　つきのさんぽ　釧路公演　音楽で世界旅行！！
公演日：
2025/9/20(土)
会場：
北海道立釧路芸術館　アートホール（北海道）
販売方法
先着
一般発売
受付期間
発売前
2025/8/8(金) 10:00 ～ 2025/9/20(土) 13:30
申込/詳細
詳細はこちら
コンサート
吉幾三
公演日：
2025/9/27(土)
会場：
コーチャンフォー釧路文化ホール（釧路市民文化会館）（北海道）
販売方法
先着
一般発売
受付期間
発売中
2025/5/31(土) 10:00 ～ 2025/9/27(土) 23:59
申込/詳細
お申し込みはこちら
コンサート
絢香
公演日：
2025/10/11(土)
会場：
コーチャンフォー釧路文化ホール（釧路市民文化会館）（北海道）
販売方法
先着
一般発売
受付期間
発売中
2025/7/26(土) 10:00 ～ 2025/9/24(水) 22:00
申込/詳細
お申し込みはこちら
演劇・ステージ・舞台
ＤＲＵＭ　ＴＡＯ　ＬＩＶＥ　２０２５
公演日：
2025/10/19(日)
会場：
コーチャンフォー釧路文化ホール（釧路市民文化会館）（北海道）
販売方法
先着
一般発売
受付期間
発売中
2025/7/10(木) 10:00 ～ 2025/10/17(金) 23:59
申込/詳細
お申し込みはこちら
"""
    with open(raw_data_file, 'w', encoding='utf-8') as f:
        f.write(dummy_content)

    df_concert = process_concert_data(raw_data_file)
    df_concert.to_csv(output_csv_file, index=False, encoding='utf-8-sig')

    print(f"✅ コンサート情報を処理し、{output_csv_file} を作成しました。")
