import pdfplumber
import pandas as pd
import sys
import os
import requests
from io import BytesIO
import re
from datetime import datetime

# 日付文字列を可能な限り YYYY-MM-DD に変換（和暦Rを西暦に変換）
def parse_date_str(date_str, start_date=None):
    if not date_str or not isinstance(date_str, str):
        return date_str

    date_str = date_str.strip()

    # すでに yyyy-mm-dd 形式ならそのまま返す
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    # 和暦Rを西暦に変換（例: R7→2025）
    date_str = re.sub(r'令和\s*(\d+)', lambda m: str(2018 + int(m.group(1))), date_str)
    date_str = re.sub(r'R\s*(\d+)', lambda m: str(2018 + int(m.group(1))), date_str)

    # 曖昧表現はそのまま
    if re.search(r'(上旬|中旬|下旬|頃|未定)', date_str):
        return date_str

    # 「(予定)」を削除
    date_str = date_str.replace("(予定)", "").strip()

    # 「2025年7月12日（土）」などのフォーマットを YYYY-MM-DD に変換
    m = re.match(r'(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日', date_str)
    if m:
        y, m_, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            dt = datetime(y, m_, d)
            return dt.strftime("%Y-%m-%d")
        except:
            return f"{y}-{m_:02d}-{d:02d}"
    
    # 「2025年13日（日）」のような形式（月が抜けている場合）
    # start_dateから月を推測
    m = re.match(r'(\d{4})年\s*(\d{1,2})日', date_str)
    if m and start_date:
        y, d = int(m.group(1)), int(m.group(2))
        # start_dateから月を抽出
        if isinstance(start_date, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", start_date):
            start_month = int(start_date[5:7])
            try:
                dt = datetime(y, start_month, d)
                return dt.strftime("%Y-%m-%d")
            except:
                return f"{y}-{start_month:02d}-{d:02d}"
    
    # yyyy/mm/dd, yyyy.mm.dd に対応
    for fmt in ("%Y/%m/%d", "%Y.%m.%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            continue

    # 月日だけのフォーマットがあれば今年の西暦に
    m = re.match(r'(\d{1,2})[月/-](\d{1,2})日?', date_str)
    if m:
        m_, d = int(m.group(1)), int(m.group(2))
        y = datetime.now().year
        try:
            dt = datetime(y, m_, d)
            return dt.strftime("%Y-%m-%d")
        except:
            return date_str

    return date_str


# PDFからテーブル抽出（ヘッダー重複除去）
def extract_tables_from_pdf(pdf_stream):
    all_rows = []
    header = None

    with pdfplumber.open(pdf_stream) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                if header is None:
                    header = table[0]
                data_rows = table[1:] if table[0] == header else table
                all_rows.extend(data_rows)

    if not header:
        raise ValueError("⚠️ ヘッダーが見つかりませんでした。")

    df = pd.DataFrame(all_rows, columns=header)
    df = df[~(df == pd.Series(header, index=df.columns)).all(axis=1)]
    df = df.drop_duplicates()
    return df

# 大会 or イベント判定
def detect_format(df):
    headers = [h.strip() for h in df.columns]
    if any("大会等の名称" in h for h in headers):
        return "大会"
    elif any("行事催事名" in h for h in headers):
        return "イベント"
    else:
        return "不明"

# カレンダー変換
def convert_to_calendar(df, fmt_type):
    calendar_rows = []

    if fmt_type == "イベント":
        for _, row in df.iterrows():
            subject = row.get("行事催事名", "")
            is_scheduled = False
            if "(予定)" in subject:
                subject = subject.replace("(予定)", "").strip()
                is_scheduled = True

            start = row.get("開催期間", "")
            end = ""
            if isinstance(start, str) and any(s in start for s in ["～", "〜", "-"]):
                parts = re.split(r"[～〜\-]", start)
                start_raw, end_raw = parts[0].strip(), parts[-1].strip()
            else:
                start_raw, end_raw = start, ""

            start_parsed = parse_date_str(start_raw)
            end_parsed = parse_date_str(end_raw, start_parsed) if end_raw else ""

            # 参集人員解析
            attendance_raw = str(row.get("参集人員", "")).strip()
            attendance_summary = []
            high_attendance_flag = "No"
            for line in attendance_raw.splitlines():
                m = re.match(r'(\d+)\s+([\d,]+|-)', line)
                if m:
                    year_jp = int(m.group(1))
                    count_str = m.group(2).replace(',', '')
                    if count_str == '-':
                        continue
                    count = int(count_str)
                    year_ad = 2018 + year_jp
                    attendance_summary.append(f"{year_ad}: {count}人")
                    if count >= 1000:
                        high_attendance_flag = "Yes"
            attendance_text = ", ".join(attendance_summary)

            desc_parts = [
                str(row.get("行事内容", "")).strip(),
                str(row.get("主催者名", "")).strip(),
                str(row.get("問い合わせ先", "")).strip(),
                f"参集人員: {attendance_text}" if attendance_text else ""
            ]
            if is_scheduled:
                desc_parts.append("(日程は予定)")
            description = "\n".join([p for p in desc_parts if p])

            location = row.get("開催場所", "")
            calendar_rows.append([subject, start_parsed, end_parsed, description, location, high_attendance_flag])

    elif fmt_type == "大会":
        for _, row in df.iterrows():
            subject = row.get("大会等の名称", "")
            is_scheduled = False
            if "(予定)" in subject:
                subject = subject.replace("(予定)", "").strip()
                is_scheduled = True

            start = row.get("開催日", "")
            end = ""
            if isinstance(start, str) and any(s in start for s in ["～", "〜", "-"]):
                parts = re.split(r"[～〜\-]", start)
                start_raw, end_raw = parts[0].strip(), parts[-1].strip()
            else:
                start_raw, end_raw = start, ""

            start_parsed = parse_date_str(start_raw)
            end_parsed = parse_date_str(end_raw, start_parsed) if end_raw else ""

            # 参集人員（con形式は単年度人数）
            attendance_raw = str(row.get("参集\n人員", "")).strip()
            if not attendance_raw:
                attendance_raw = str(row.get("参集人員", "")).strip()

            attendance_summary = []
            high_attendance_flag = "No"
            if attendance_raw:
                count_str = attendance_raw.replace(',', '')
                try:
                    count = int(count_str)
                    attendance_summary.append(f"最新: {count}人")
                    if count >= 1000:
                        high_attendance_flag = "Yes"
                except ValueError:
                    pass
            attendance_text = ", ".join(attendance_summary)

            desc1 = row.get('大会\n区分', '')
            desc2 = row.get('種類\n区分', '')
            desc = (desc1 + " " + desc2).strip()

            desc_parts = [
                desc,
                str(row.get("主催者", "")).strip(),
                str(row.get("連絡先", "")).strip(),
                f"参集人員: {attendance_text}" if attendance_text else ""
            ]
            if is_scheduled:
                desc_parts.append("(日程は予定)")
            description = "\n".join([p for p in desc_parts if p])
            location = row.get("会場", "")

            calendar_rows.append([subject, start_parsed, end_parsed, description, location, high_attendance_flag])

    calendar_df = pd.DataFrame(calendar_rows, columns=["Subject", "Start Date", "End Date", "Description", "Location", "HighAttendanceFlag"])
    return calendar_df

def download_pdf(url):
    r = requests.get(url)
    r.raise_for_status()
    return BytesIO(r.content)

# 既存のCSVファイルを修正する関数
def fix_existing_csv(csv_file):
    df = pd.read_csv(csv_file)
    
    for index, row in df.iterrows():
        start_date = row['Start Date']
        end_date = row['End Date']
        
        # Start Dateを修正
        fixed_start = parse_date_str(start_date)
        
        # End Dateを修正（Start Dateの情報を使用）
        if pd.notna(end_date) and end_date != "":
            fixed_end = parse_date_str(end_date, fixed_start)
        else:
            fixed_end = end_date
            
        df.at[index, 'Start Date'] = fixed_start
        df.at[index, 'End Date'] = fixed_end
    
    # 修正されたCSVを保存
    output_file = csv_file.replace('.csv', '_fixed.csv')
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 修正完了: {output_file}")
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python main.py <PDFのURL または CSVファイル>")
        sys.exit(1)

    input_path = sys.argv[1]
    
    # CSVファイルの場合は修正処理
    if input_path.endswith('.csv'):
        fix_existing_csv(input_path)
    else:
        # PDFの場合は従来の処理
        pdf_stream = download_pdf(input_path)
        df = extract_tables_from_pdf(pdf_stream)
        fmt_type = detect_format(df)
        print(f"📄 判定: {fmt_type}")

        cal_df = convert_to_calendar(df, fmt_type)

        base = os.path.splitext(os.path.basename(input_path))[0]
        output_csv = f"data/processed/{base}_converted.csv"
        cal_df.to_csv(output_csv, index=False, encoding="utf-8-sig")

        print(f"✅ 変換完了: {output_csv}")