import pandas as pd
import re
from datetime import datetime

def process_event_data(df, event_type, data_source):
    processed_rows = []
    for index, row in df.iterrows():
        subject = row.get('Subject', '')
        start_date = row.get('Start Date', '')
        end_date = row.get('End Date', '')
        location = row.get('Location', '')
        high_attendance_flag = row.get('HighAttendanceFlag', '')
        description = row.get('Description', '')

        # EstimatedAttendeesの抽出
        estimated_attendees = 0
        attendees_match = re.search(r'参集人員: (?:最新: |\d{4}: )?(\d+)(?:人)?', description)
        if attendees_match:
            try:
                estimated_attendees = int(attendees_match.group(1))
            except ValueError:
                pass

        # ImpactLevelの決定
        impact_level = "Low"
        if high_attendance_flag == "Yes":
            impact_level = "High"
        elif 300 <= estimated_attendees < 1000: # HighAttendanceFlagがNoでも300人以上ならMedium
            impact_level = "Medium"

        # 阿寒地域のイベントを除外
        if isinstance(location, str) and "阿寒" in location:
            continue

        processed_rows.append({
            'EventType': event_type,
            'Subject': subject,
            'StartDate': start_date,
            'EndDate': end_date,
            'EstimatedAttendees': estimated_attendees,
            'Location': location,
            'ImpactLevel': impact_level,
            'DataSource': data_source,
            'LastUpdated': datetime.now().strftime("%Y-%m-%d")
        })
    return pd.DataFrame(processed_rows)

def run_combine_csv():
    # ファイルパス
    cruise_file = 'data/processed/r7-cruise_converted.csv'
    con_file = 'data/processed/r7-con_converted.csv'
    ev_file = 'data/processed/r7-ev_converted.csv'
    concert_file = 'data/processed/r7-concert_converted.csv'
    output_file = 'data/processed/combined_events.csv'

    # クルーズデータを読み込み
    df_cruise = pd.read_csv(cruise_file)

    # 大会データを読み込み、処理
    df_con_raw = pd.read_csv(con_file)
    df_con = process_event_data(df_con_raw, '大会', 'kushiro-lakeakan.com')

    # イベントデータを読み込み、処理
    df_ev_raw = pd.read_csv(ev_file)
    df_ev = process_event_data(df_ev_raw, 'イベント', 'kushiro-lakeakan.com')

    # コンサートデータを読み込み (process_event_dataは不要、既に整形済みのため)
    df_concert = pd.read_csv(concert_file)

    # 全てのDataFrameを結合
    combined_df = pd.concat([df_cruise, df_con, df_ev, df_concert], ignore_index=True)

    # CSVとして出力
    combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"✅ 全てのCSVファイルを結合し、{output_file} を作成しました。")

if __name__ == "__main__":
    run_combine_csv()
