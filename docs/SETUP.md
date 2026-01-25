# 開発環境のセットアップ

このドキュメントでは SharkBot-v2 の開発環境をセットアップする手順を説明します。

## 目次

- [必要な環境](#必要な環境)
- [インストール手順](#インストール手順)
- [設定](#設定)
- [Bot の起動](#bot-の起動)
- [Web ダッシュボードの起動](#web-ダッシュボードの起動)
- [トラブルシューティング](#トラブルシューティング)

## 必要な環境

### システム要件

- **OS**: Linux (Ubuntu 20.04+ 推奨) / macOS / Windows (WSL2 推奨)
- **Python**: 3.11 以上
- **MongoDB**: 5.0 以上
- **メモリ**: 最低 2GB (推奨 4GB 以上)
- **ディスク**: 最低 5GB

### 必要なソフトウェア

1. **Python 3.11+**
2. **MongoDB**
3. **Git**
4. **OpenJTalk** (TTS 機能を使用する場合)

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/SharkBot-Dev/SharkBot-v2.git
cd SharkBot-v2
```

### 2. MongoDB のインストールと起動

#### Ubuntu/Debian
```bash
# MongoDB のインストール
sudo apt-get install mongodb

# MongoDB の起動
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

#### macOS (Homebrew)
```bash
# MongoDB のインストール
brew tap mongodb/brew
brew install mongodb-community

# MongoDB の起動
brew services start mongodb-community
```

#### Docker (推奨)
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. Python 依存関係のインストール

```bash
cd src

# venv の作成 (推奨)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

または `uv` を使用する場合:

```bash
# uv のインストール
pip install uv

# 依存関係のインストール
uv pip install -r requirements.txt
```

### 4. OpenJTalk のインストール (オプション)

TTS 機能を使用する場合のみ必要です。

#### Ubuntu/Debian
```bash
sudo apt-get install open-jtalk open-jtalk-mecab-naist-jdic
```

#### macOS
```bash
brew install open-jtalk
```

音声ファイル (htsvoice) を `src/htsvoice/` に配置してください。

## 設定

### 1. Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. "New Application" をクリック
3. Bot タブから Bot を作成
4. "Privileged Gateway Intents" をすべて有効化:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
5. Bot Token をコピー

### 2. OAuth2 設定

ダッシュボードを使用する場合:

1. OAuth2 タブを開く
2. "Redirects" に以下を追加:
   ```
   http://localhost:8000/login/callback
   ```
3. Client ID と Client Secret をコピー

### 3. 設定ファイルの作成

```bash
cd src/consts

# サンプルファイルをコピー
cp settings.sample settings.py

# settings.py を編集
nano settings.py  # または好きなエディタ
```

#### `settings.py` の内容

```python
# Discord Bot Token
TOKEN = "あなたのBotToken"

# OAuth2 設定 (ダッシュボード用)
CLIENT_ID = "あなたのClientID"
CLIENT_SECRET = "あなたのClientSecret"
REDIRECT_URI = "http://localhost:8000/login/callback"

# Discord API URL
DISCORD_API = "https://discord.com/api/v10"

# セッションキー (ランダムな文字列)
SESSINKEY = "ランダムな長い文字列"

# その他の設定...
```

### 4. 環境変数の設定 (オプション)

`.env` ファイルを作成することもできます:

```bash
cd src
nano .env
```

```env
Token=あなたのBotToken
CLIENT_ID=あなたのClientID
CLIENT_SECRET=あなたのClientSecret
```

## Bot の起動

### 方法1: 直接起動

```bash
cd src
python bot.py
```

### 方法2: boot_bot.py を使用 (自動再起動)

```bash
cd src
python boot_bot.py
```

`boot_bot.py` は以下の機能を提供します:
- Bot のクラッシュ時に自動再起動
- `reboot` ファイルを作成すると Bot を再起動
- `shutdown` ファイルを作成すると Bot を停止

### 方法3: スクリプトを使用

```bash
# Linux/macOS
./scripts/run.sh

# Windows
scripts\run_windows.bat
```

### 起動確認

Bot が正常に起動すると以下のようなログが表示されます:

```
InitDone
---[Logging]-------------------------------
BotName: SharkBot
Ready.
```

## Web ダッシュボードの起動

```bash
cd src
uvicorn api:app --reload --port 8000
```

ブラウザで `http://localhost:8000` にアクセスしてダッシュボードを確認できます。

## 開発ツールのセットアップ

### pre-commit フックのインストール

コミット前に自動的にコードをチェックします:

```bash
# pre-commit のインストール
pip install pre-commit

# フックのインストール
pre-commit install
```

### リンターとフォーマッターの実行

```bash
# autopep8 でコードを整形
autopep8 --in-place --recursive src/

# flake8 でコードをチェック
flake8 src/

# ruff でコードをチェック
ruff check src/
```

## 開発モードでの実行

### Jishaku デバッグツール

Bot には Jishaku が組み込まれています。Bot 起動後、Discord で以下のコマンドが使用できます:

- `!jsk py <code>`: Python コードを実行
- `!jsk sh <command>`: シェルコマンドを実行
- `!jsk load <extension>`: 拡張をロード
- `!jsk reload <extension>`: 拡張をリロード

### ホットリロード

Cog を変更した場合、Bot を再起動せずにリロードできます:

```
!jsk reload cogs.admin
```

または Admin コマンドを使用:

```
/admin cogs 操作の種類:リロード cog名:admin
```

## トラブルシューティング

### MongoDB 接続エラー

**エラー**: `ServerSelectionTimeoutError: localhost:27017`

**解決策**:
- MongoDB が起動しているか確認
  ```bash
  sudo systemctl status mongodb
  ```
- MongoDB のポートが 27017 であることを確認
- ファイアウォールが 27017 ポートをブロックしていないか確認

### Bot Token エラー

**エラー**: `discord.errors.LoginFailure: Improper token has been passed.`

**解決策**:
- `settings.py` の TOKEN が正しいか確認
- 環境変数 `Token` が設定されているか確認
- Discord Developer Portal で Token を再生成

### 権限エラー

**エラー**: Bot がサーバーで動作しない

**解決策**:
- Bot に必要な権限が付与されているか確認:
  - メッセージの送信
  - メッセージの管理
  - メンバーの管理
  - ロールの管理
  - など
- Privileged Gateway Intents が有効化されているか確認

### 依存関係のエラー

**エラー**: モジュールのインポートエラー

**解決策**:
```bash
# 依存関係を再インストール
pip install --upgrade -r requirements.txt

# または特定のパッケージを再インストール
pip install --upgrade discord.py
```

### Cog ロードエラー

**エラー**: `❌ Failed to load cogs.xxx`

**解決策**:
- Cog ファイルに構文エラーがないか確認
- 必要なモジュールがインポートされているか確認
- `async def setup(bot)` 関数が定義されているか確認

### OpenJTalk エラー (TTS)

**エラー**: TTS コマンドが動作しない

**解決策**:
- OpenJTalk がインストールされているか確認
  ```bash
  which open_jtalk
  ```
- htsvoice ファイルが `src/htsvoice/` に配置されているか確認

## 次のステップ

開発環境のセットアップが完了したら:

1. [DEVELOPER.md](./DEVELOPER.md) で開発の基本を学ぶ
2. [COG_DEVELOPMENT.md](./COG_DEVELOPMENT.md) で Cog の作成方法を学ぶ
3. [ARCHITECTURE.md](./ARCHITECTURE.md) でシステムアーキテクチャを理解する
4. [CONTRIBUTING.md](./CONTRIBUTING.md) で貢献方法を確認する

## サポート

問題が解決しない場合は、GitHub Issues で質問してください。
