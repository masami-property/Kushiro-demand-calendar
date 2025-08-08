import pandas as pd
import requests
from io import StringIO
from datetime import datetime

class HolidayParser:
    def __init__(self, url="https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv"):
        self.url = url
        self.holidays = self._fetch_holidays()

    def _fetch_holidays(self):
        """内閣府の祝日CSVをダウンロードし、DataFrameとして読み込む"""
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # HTTPエラーがあれば例外を発生させる
            # Shift-JISでデコード
            csv_data = response.content.decode('shift_jis')
            df = pd.read_csv(StringIO(csv_data), header=None, names=['Date', 'Name'], skiprows=1)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except requests.exceptions.RequestException as e:
            print(f"祝日データのダウンロード中にエラーが発生しました: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"祝日データの解析中にエラーが発生しました: {e}")
            return pd.DataFrame()

    def is_holiday(self, date_obj):
        """指定された日付が祝日かどうかを判定する"""
        if self.holidays.empty:
            return False
        return date_obj in self.holidays['Date'].dt.date.values

    def get_holiday_name(self, date_obj):
        """指定された日付の祝日名を取得する"""
        if self.holidays.empty:
            return None
        holiday_row = self.holidays[self.holidays['Date'].dt.date == date_obj]
        if not holiday_row.empty:
            return holiday_row.iloc[0]['Name']
        return None

    def get_holidays_in_range(self, start_date, end_date):
        """指定された期間内の祝日リストを取得する"""
        if self.holidays.empty:
            return []
        mask = (self.holidays['Date'] >= pd.to_datetime(start_date)) & (self.holidays['Date'] <= pd.to_datetime(end_date))
        return self.holidays[mask].to_dict('records')

if __name__ == "__main__":
    holiday_parser = HolidayParser()

    # 例: 今日の日付が祝日かどうかを確認
    today = datetime.now().date()
    if holiday_parser.is_holiday(today):
        print(f"{today} は祝日です: {holiday_parser.get_holiday_name(today)}")
    else:
        print(f"{today} は祝日ではありません。")

    # 例: 2025年1月1日が祝日かどうかを確認
    new_year = datetime(2025, 1, 1).date()
    if holiday_parser.is_holiday(new_year):
        print(f"{new_year} は祝日です: {holiday_parser.get_holiday_name(new_year)}")

    # 例: 2025年1月中の祝日リストを取得
    holidays_jan_2025 = holiday_parser.get_holidays_in_range('2025-01-01', '2025-01-31')
    print("\n2025年1月中の祝日:")
    for h in holidays_jan_2025:
        print(f"  {h['Date'].strftime('%Y-%m-%d')}: {h['Name']}")
