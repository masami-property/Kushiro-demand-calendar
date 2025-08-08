
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

def estimate_attendees(tonnage_str):
    """トン数から乗客数を推定する"""
    if not tonnage_str or not isinstance(tonnage_str, str):
        return 0
    
    tonnage_match = re.search(r'([\d,]+)t', tonnage_str)
    if not tonnage_match:
        return 0
        
    tonnage = int(tonnage_match.group(1).replace(',', ''))
    
    # 乗客数の推定ロジック（乗客スペース比を35と仮定）
    # これはあくまで概算です
    estimated_pax = int(tonnage / 35)
    return estimated_pax

def get_impact_level(attendees):
    """乗客数から影響度レベルを判定する"""
    if attendees >= 1000:
        return "High"
    elif 300 <= attendees < 1000:
        return "Medium"
    else:
        return "Low"

def parse_cruise_schedule(url):
    """クルーズ客船の入港予定ページをスクレイピングしてCSVに変換する"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # ページのタイトルから年を取得
    title_tag = soup.find('h1')
    year_match = re.search(r'(\d{4})年度', title_tag.text if title_tag else '')
    if not year_match:
        print("Error: Could not determine the year from the page title.")
        return
    
    fiscal_year_start = int(year_match.group(1))

    table = soup.find('table', class_='w100')
    if not table:
        print("Error: Could not find the schedule table.")
        return

    rows = table.find('tbody').find_all('tr')
    
    cruise_data = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 8:
            continue

        # 中止された寄港はスキップ
        if '寄港中止' in cols[3].text or 'CANCELLED' in cols[3].text:
            continue

        # 1. 日付と時刻の解析
        arrival_text = cols[1].text.strip()
        departure_text = cols[2].text.strip()

        arrival_date_match = re.search(r'(\d+)月(\d+)日', arrival_text)
        departure_date_match = re.search(r'(\d+)月(\d+)日', departure_text)

        if not arrival_date_match:
            continue

        month = int(arrival_date_match.group(1))
        day = int(arrival_date_match.group(2))
        
        # 年度に基づいて年を決定 (4月始まり)
        year = fiscal_year_start if month >= 4 else fiscal_year_start + 1
        
        start_date = f"{year}-{month:02d}-{day:02d}"
        end_date = start_date # クルーズ船は同日出港が基本

        # 2. 船名とトン数の抽出
        ship_info = cols[3].text.strip()
        ship_name_match = re.match(r'([^\(]+)', ship_info)
        ship_name = ship_name_match.group(1).strip() if ship_name_match else ""
        
        tonnage_str = ""
        tonnage_match = re.search(r'\((.*t)\)', ship_info)
        if tonnage_match:
            tonnage_str = tonnage_match.group(1)

        # 3. その他の情報
        last_port = cols[4].text.strip().replace('\n', ' ')
        next_port = cols[5].text.strip().replace('\n', ' ')
        berth = cols[6].text.strip().replace('\n', ' ')
        notes = cols[7].text.strip().replace('\n', ' ')

        # 4. 乗客数と影響レベルの推定
        attendees = estimate_attendees(tonnage_str)
        impact_level = get_impact_level(attendees)

        # 5. 統合データ作成
        description_parts = [
            f"トン数: {tonnage_str}" if tonnage_str else "",
            f"前港: {last_port}",
            f"次港: {next_port}",
            f"備考: {notes}" if notes else ""
        ]
        description = "\n".join(filter(None, description_parts))

        cruise_data.append({
            'EventType': 'クルーズ',
            'Subject': f"{ship_name}入港",
            'StartDate': start_date,
            'EndDate': end_date,
            'EstimatedAttendees': attendees,
            'Location': berth,
            'ImpactLevel': impact_level,
            'DataSource': 'city.kushiro.lg.jp',
            'LastUpdated': datetime.now().strftime("%Y-%m-%d"),
            'Description': description
        })

    if not cruise_data:
        print("No cruise data extracted.")
        return

    # DataFrameに変換
    df = pd.DataFrame(cruise_data)
    
    # 統合CSVのフォーマットに合わせる
    output_df = df[[ 
        'EventType', 'Subject', 'StartDate', 'EndDate', 
        'EstimatedAttendees', 'Location', 'ImpactLevel', 
        'DataSource', 'LastUpdated'
    ]]

    output_filename = 'data/processed/r7-cruise_converted.csv'
    output_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"✅ 変換完了: {output_filename}")


if __name__ == "__main__":
    target_url = "https://www.city.kushiro.lg.jp/sangyou/umisora/1006541/1006592/1006593.html"
    parse_cruise_schedule(target_url)
