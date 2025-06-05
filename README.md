# 334Ranker

## 概要
**334Ranker**は、特定の時間（3時34分）にTwitter上で「334」というキーワードを含むツイートを収集し、その投稿時刻に基づいてランキングを生成・公開するTwitterBotです。

## 機能
1. **ツイート収集**:
   - 毎日3時34分（`TIME334` 変更可能）に投稿された「334」というキーワードのツイートを収集。
   - Twitter API（`unofficial_twitter_client`）を使用して、タイムラインや検索結果からデータを取得。

2. **ランキング生成**:
   - ツイート時刻を基に、当日のランキング（トップ30）を生成。
   - 過去の記録からユーザーのポイントを計算し、級位や世界ランキングを決定。
   - 月間ランキングも生成（毎月1日に実行）。

3. **自動返信**:
   - メンションされたツイートに対して、ユーザーのランキング情報（級位、ポイント、順位など）や当日の結果を返信。
   - フォローリクエストにも対応し、条件を満たす場合にフォロー返しを行う。

4. **画像生成**:
   - 当日および月間ランキングをHTMLページ（`HTML_URL`, `HTML_URL2`）を利用して画像化。
   - 生成した画像をTwitterに投稿。

5. **データ管理**:
   - PHPサーバー（`PHP_URL`）と連携し、ユーザーデータやランキング情報を保存・取得。
   - 過去の記録を基にポイントや順位を計算。

## 必要環境
当BotはGitHub Actionsで動作するよう設計されています。

- **Python 3.x**
- **ライブラリ**:
  - `chromedriver_binary`
  - `selenium`
  - `seleniumwire`
  - `requests`
  - `unofficial_twitter_client`
  - その他標準ライブラリ
- **外部サービス**:
  - PHPサーバー（データ保存・取得用）
  - Chromeブラウザ（画像生成用）
- **環境変数**:
  - `PHP_URL`: PHPスクリプトが設置されているディレクトリ
  - `MAIN_TOKENS`: 主アカウントの認証情報（`name$token$secret`）
  - `REP_TOKENS`: 返信用アカウントの認証情報（`name1$token1$secret1|name2$token2$secret2...`）
  - `HTML_URL`: デイリーランキング画像生成ページのURL
  - `HTML_URL2`: 月間ランキング画像生成ページのURL

## 設定方法
1. **環境変数の設定**:
   ```bash
   export PHP_URL="http://your-php-server.com/"
   export MAIN_TOKENS="main_account_name$oauth_token$oauth_secret"
   export REP_TOKENS="rep_account1$token1$secret1|rep_account2$token2$secret2"
   export HTML_URL="http://your-html-server.com/daily"
   export HTML_URL2="http://your-html-server.com/monthly"

2. **依存ライブラリのインストール**:
   ```bash
   pip install -r requirements.txt

3. **PHPサーバーの設置**:
  - `get.php`, `get_rank.php`, `add.php`, `add_rank.php`を`PHP_URL`直下に設置。
  - `HTML_URL`, `HTML_URL2`に画像生成用HTMLを設置（Macのシステムフォントを使いたかった & CSSに慣れていたのでこのような実装にしています）

## 実行方法
`TIME334`で指定した時刻の20分前の時刻を基準に、4時間おきに起動してください（GitHub Actionsの6時間以内で動かすため）

## ライセンス

MIT