# SharkBot-v2 開発者ガイド

このドキュメントは SharkBot-v2 の開発者向けガイドです。

## 目次

- [プロジェクト概要](#プロジェクト概要)
- [技術スタック](#技術スタック)
- [プロジェクト構成](#プロジェクト構成)
- [開発環境のセットアップ](#開発環境のセットアップ)
- [コーディング規約](#コーディング規約)
- [関連ドキュメント](#関連ドキュメント)

## プロジェクト概要

SharkBot-v2 は Discord 用の多機能 Bot です。管理機能から楽しいコマンドまで、幅広いコマンドを提供します。

### 主な機能

- **モデレーション機能**: キック、Ban、タイムアウトなどの管理機能
- **自動化機能**: 自動応答、自動リアクション、自動テキストなど
- **エンターテイメント**: ゲーム、動物画像、音楽再生など
- **ユーティリティ**: リマインダー、タイマー、翻訳など
- **カスタマイズ**: プレフィックスのカスタマイズ、コマンド無効化など
- **ダッシュボード**: Web ベースの管理インターフェース
- **グローバルチャット**: サーバー間でのチャット機能
- **レベルシステム**: ユーザーアクティビティに基づくレベルアップ

## 技術スタック

### メインテクノロジー

- **Python 3.11+**: メインプログラミング言語
- **discord.py 2.6.4**: Discord Bot フレームワーク
- **MongoDB**: データベース (motor/pymongo)
- **FastAPI**: Web API とダッシュボード
- **Jinja2**: テンプレートエンジン

### 主要ライブラリ

- **discord.py**: Discord API ラッパー
- **motor**: MongoDB の非同期ドライバ
- **pymongo**: MongoDB の同期ドライバ
- **FastAPI**: 高速な Web フレームワーク
- **uvicorn**: ASGI サーバー
- **jishaku**: Bot デバッグツール
- **aiohttp**: 非同期 HTTP クライアント/サーバー
- **Pillow**: 画像処理
- **matplotlib**: グラフ生成
- **deep-translator**: 翻訳機能
- **OpenJTalk**: テキスト読み上げ (TTS)

### 開発ツール

- **autopep8**: コード自動整形
- **flake8**: リンター
- **ruff**: 高速リンター
- **pre-commit**: Git フック管理

## プロジェクト構成

```
SharkBot-v2/
├── docs/                    # ドキュメント
├── scripts/                 # 実行スクリプト
└── src/                     # ソースコード
    ├── bot.py              # Bot メインファイル
    ├── boot_bot.py         # Bot 起動スクリプト
    ├── api.py              # FastAPI サーバー
    ├── cogs/               # Bot コマンド (Cogs)
    ├── models/             # データモデルとヘルパー
    ├── consts/             # 定数と設定
    ├── templates/          # Web テンプレート
    ├── router/             # FastAPI ルーター
    ├── dashboard/          # ダッシュボード
    ├── Graph/              # グラフ生成サービス
    ├── aimod/              # AI モデル
    ├── colorbot/           # カラーBot サブモジュール
    ├── hiroyuki/           # ひろゆきモジュール
    ├── music/              # 音楽再生
    ├── short/              # URL 短縮サービス
    ├── sites/              # サイト関連
    ├── translate/          # 翻訳データ
    └── youtube/            # YouTube 統合
```

### 重要なディレクトリの説明

#### `src/cogs/`
Bot のコマンドを Cog (拡張機能) として実装します。各 Cog は特定の機能セットを提供します。

主な Cog:
- `admin.py`: Bot 管理者向けコマンド
- `mod.py`: モデレーションコマンド
- `help.py`: ヘルプシステム
- `music.py`: 音楽再生
- `level.py`: レベルシステム
- `welcome.py`: ウェルカムメッセージ
- `automod.py`: 自動モデレーション
- など多数

#### `src/models/`
データモデルとユーティリティ関数を提供します。

主なモジュール:
- `custom_tree.py`: カスタム CommandTree (権限チェック、翻訳など)
- `command_disable.py`: コマンド無効化システム
- `make_embed.py`: Embed 作成ヘルパー
- `translate.py`: 翻訳システム
- `permissions_text.py`: 権限テキスト生成

#### `src/consts/`
設定ファイルと定数を管理します。

- `settings.sample`: 設定ファイルのサンプル
- `mongodb.py`: MongoDB 接続設定
- `templates.py`: テンプレート設定

## 開発環境のセットアップ

詳細は [SETUP.md](./SETUP.md) を参照してください。

### クイックスタート

```bash
# リポジトリのクローン
git clone https://github.com/SharkBot-Dev/SharkBot-v2.git
cd SharkBot-v2/src

# 依存関係のインストール
pip install -r requirements.txt

# 設定ファイルのコピー
cp consts/settings.sample consts/settings.py

# settings.py を編集して Discord Token などを設定
# MongoDB を起動 (localhost:27017)

# Bot の起動
python bot.py
```

## コーディング規約

### Python スタイルガイド

- PEP 8 に準拠
- autopep8 でコードを整形
- flake8/ruff でコードをチェック

### Cog 開発のベストプラクティス

1. **Cog クラスの構造**
   ```python
   from discord.ext import commands
   import discord
   from discord import app_commands

   class MyCog(commands.Cog):
       def __init__(self, bot: commands.Bot):
           self.bot = bot
           print("init -> MyCog")

       # コマンドをここに実装
   
   async def setup(bot: commands.Bot):
       await bot.add_cog(MyCog(bot))
   ```

2. **エラーハンドリング**
   - 適切なエラーメッセージを表示
   - `make_embed.error_embed()` を使用

3. **データベースアクセス**
   - 非同期操作には `self.bot.async_db` を使用
   - 同期操作には `self.bot.sync_db` を使用

4. **翻訳対応**
   - `interaction.extras["lang"]` で言語を取得
   - `translate` モジュールを使用

### コミットメッセージ

- 日本語または英語で記述
- 変更内容を簡潔に説明
- 例: "Fix: ロールパネルの表示バグを修正", "Add: 新しい音楽コマンドを追加"

## 関連ドキュメント

- [ARCHITECTURE.md](./ARCHITECTURE.md) - システムアーキテクチャの詳細
- [SETUP.md](./SETUP.md) - 開発環境のセットアップ
- [COG_DEVELOPMENT.md](./COG_DEVELOPMENT.md) - Cog 開発ガイド
- [API.md](./API.md) - API ドキュメント
- [CONTRIBUTING.md](./CONTRIBUTING.md) - 貢献ガイドライン
- [DevHelp.md](./DevHelp.md) - 開発者向けヘルプ (既存)

## サポート

問題が発生した場合は、GitHub Issues で報告してください。
