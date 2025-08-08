# 釧路宿泊需要予測カレンダー

## プロジェクト概要
本プロジェクトは、釧路市における宿泊施設のダイナミックプライシングシステム構築を目的とした需要予測カレンダーです。様々な公開データを統合・分析し、各日の宿泊需要の傾向を視覚的に把握できるようにしています。

## 機能概要
- イベント情報（大会、クルーズ客船、コンサート）の収集と統合
- 日本の祝日データの統合
- 釧路市観光統計データに基づく季節トレンドの反映
- 曜日効果の考慮
- 各日の需要スコア算出と影響度レベル（High/Medium/Low）の判定
- 年間カレンダー形式での視覚化（HTML/CSS/JavaScript）
- マウスホバーによる詳細情報表示

## データソース
本プロジェクトで利用しているデータは全て公開情報源に基づいています。
- **大会・イベント情報**: [釧路観光コンベンション協会](https://ja.kushiro-lakeakan.com/news/20980/)
- **クルーズ客船入港情報**: [釧路市ホームページ](https://www.city.kushiro.lg.jp/sangyou/umisora/1006541/1006592/1006593.html)
- **コンサート・ライブ情報**: [L-Tike](https://l-tike.com/search/?vnu=釧路&pref=01) (手動コピー＆ペースト)
- **日本の祝日情報**: [内閣府](https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv)
- **観光トレンド情報**: [釧路市観光統計](https://www.city.kushiro.lg.jp/sangyou/kankou/1006252/1006253.html) (手動コピー＆ペースト)

## セットアップ方法
1. リポジトリをクローンします。
   ```bash
   git clone https://github.com/masami-property/Kushiro-demand-calendar.git
   cd Kushiro-demand-calendar
   ```
2. 必要なPythonライブラリをインストールします。
   ```bash
   pip install -r requirements.txt
   ```

## 実行方法
本プロジェクトは、以下のスクリプトを順番に実行することで、需要予測カレンダーのデータを生成します。

1. **生データの前処理 (必要に応じて手動で `data/raw/` にデータを配置後)**
   - `scripts/data_collection/event2csv.py`: イベント情報PDFをCSVに変換
   - `scripts/data_collection/cruise_scraper.py`: クルーズ客船情報をスクレイピング
   - `scripts/data_collection/concert_processor.py`: コンサート情報を処理

2. **データ統合とトレンド生成**
   - `scripts/data_processing/tourism_trends_processor.py`: 観光トレンドデータを処理
   - `scripts/data_processing/combine_csv.py`: 全てのイベントデータを統合
   - `scripts/data_processing/calendar_generator.py`: 統合データと祝日、トレンド情報からカレンダーデータを生成

   各スクリプトは、プロジェクトのルートディレクトリから以下のように実行します。
   ```bash
   python scripts/data_collection/event2csv.py [PDFのURL]
   python scripts/data_collection/cruise_scraper.py
   python scripts/data_collection/concert_processor.py
   python scripts/data_processing/tourism_trends_processor.py
   python scripts/data_processing/combine_csv.py
   python scripts/data_processing/calendar_generator.py
   ```

## GitHub Pagesでの閲覧方法
本カレンダーはGitHub Pagesで公開されています。

[カレンダーを見る](https://masami-property.github.io/Kushiro-demand-calendar/)

または、ローカルでウェブサーバーを起動して閲覧することも可能です。
プロジェクトのルートディレクトリで以下のコマンドを実行し、ブラウザで `http://localhost:8000/web/index.html` にアクセスしてください。
```bash
python -m http.server 8000
```
