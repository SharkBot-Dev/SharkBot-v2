# システムアーキテクチャ

このドキュメントでは SharkBot-v2 のシステムアーキテクチャについて説明します。

## 目次

- [全体構成](#全体構成)
- [Bot アーキテクチャ](#bot-アーキテクチャ)
- [データベース設計](#データベース設計)
- [Web ダッシュボード](#web-ダッシュボード)
- [マイクロサービス](#マイクロサービス)
- [フロー図](#フロー図)

## 全体構成

SharkBot-v2 は以下のコンポーネントで構成されています:

```
┌─────────────────┐
│   Discord API   │
└────────┬────────┘
         │
┌────────▼────────────────────────────┐
│   Discord Bot (bot.py)              │
│   - AutoShardedBot                  │
│   - Cog システム                     │
│   - CustomTree (コマンド処理)        │
└────────┬────────────────────────────┘
         │
         ├──────────┬──────────┬──────────┐
         │          │          │          │
┌────────▼──────┐  │  ┌───────▼──────┐  │
│   MongoDB     │  │  │ FastAPI      │  │
│   Database    │  │  │ Dashboard    │  │
└───────────────┘  │  └──────────────┘  │
                   │                     │
         ┌─────────▼──────────┐  ┌──────▼──────┐
         │ Graph Service      │  │ AI Module   │
         │ (matplotlib)       │  │             │
         └────────────────────┘  └─────────────┘
```

## Bot アーキテクチャ

### Bot クラス階層

```python
commands.AutoShardedBot
    └── NewSharkBot
        ├── async_db: AsyncIOMotorClient (MongoDB 非同期)
        ├── sync_db: MongoClient (MongoDB 同期)
        └── tree: CustomTree (カスタムコマンドツリー)
```

### Bot 起動フロー

1. **bot.py 実行**
   - `NewSharkBot` インスタンスを作成
   - MongoDB クライアントを初期化
   - カスタムプレフィックス機能を設定

2. **setup_hook()**
   - 翻訳データをロード (`translate.load()`)
   - Cog を自動的にロード (`load_cogs()`)
   - コマンドツリーを同期 (`bot.tree.sync()`)

3. **on_ready()**
   - Jishaku 拡張をロード
   - Bot のプレゼンスを設定
   - ログ情報を表示

### Cog システム

Cog は Discord Bot の機能を分割して管理するための仕組みです。

#### Cog の自動ロード

```python
async def load_cogs(bot: commands.Bot, base_folder="cogs"):
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                # cogs/admin.py → cogs.admin
                # cogs/autotext/autotext.py → cogs.autotext.autotext
                module = f"{base_folder}.{relative_path}"
                await bot.load_extension(module)
```

### CustomTree - コマンド実行前処理

`CustomTree` は `discord.app_commands.CommandTree` を継承し、すべてのスラッシュコマンド実行前に以下のチェックを行います:

1. **DM チェック**: DMではコマンドを実行できない
2. **コマンド無効化チェック**: サーバー管理者によって無効化されていないか
3. **チャンネル無効化チェック**: チャンネルでコマンドが許可されているか
4. **ユーザーBanチェック**: ユーザーがBotからBanされていないか
5. **サーバーBanチェック**: サーバーがBotからBanされていないか
6. **言語設定の読み込み**: サーバーの言語設定を `interaction.extras["lang"]` に設定

### イベントシステム

Bot は Discord のイベントを処理します:

- `on_ready`: Bot が起動したときに実行
- `on_message`: メッセージが送信されたとき (現在は無効化)
- `on_member_join`: メンバーが参加したとき (welcome Cog で処理)
- `on_member_remove`: メンバーが退出したとき
- `on_guild_join`: Bot がサーバーに追加されたとき
- など

## データベース設計

### MongoDB コレクション構成

SharkBot-v2 は MongoDB を使用してデータを保存します。主なデータベースとコレクション:

#### Main データベース
- `BotAdmins`: Bot 管理者リスト
- `GuildSettings`: サーバー設定
- `UserData`: ユーザーデータ

#### DashboardBot データベース
- `CustomPrefixBot`: カスタムプレフィックス設定
- `CommandDisable`: 無効化されたコマンド
- `ChannelDisable`: コマンド無効化チャンネル
- `Levels`: レベルシステムデータ
- `Economy`: 経済システムデータ
- `AutoMod`: 自動モデレーション設定
- `AutoReply`: 自動応答設定
- `WelcomeSettings`: ウェルカムメッセージ設定
- `RolePanels`: ロールパネル設定
- `Tags`: カスタムタグ
- `Reminders`: リマインダー
- `Loops`: ループタスク

### データアクセスパターン

#### 非同期アクセス (推奨)
```python
db = self.bot.async_db["DashboardBot"]
collection = db["CommandDisable"]
data = await collection.find_one({"Guild": guild_id})
```

#### 同期アクセス (特定の場合のみ)
```python
db = self.bot.sync_db["DashboardBot"]
collection = db["CustomPrefixBot"]
data = collection.find_one({"Guild": guild_id})
```

## Web ダッシュボード

### FastAPI アーキテクチャ

```
FastAPI Application (api.py)
├── SessionMiddleware: セッション管理
├── Limiter: レート制限
├── StaticFiles: 静的ファイル配信
└── Routers:
    ├── mainpage: メインページ
    └── settings: 設定ページ
```

### 認証フロー

1. ユーザーが `/login` にアクセス
2. Discord OAuth2 認証ページにリダイレクト
3. 認証後、`/login/callback` にリダイレクト
4. アクセストークンを取得してセッションに保存
5. ユーザー情報とギルド情報を取得
6. ダッシュボードにリダイレクト

### テンプレートシステム

Jinja2 テンプレートエンジンを使用:

- `templates/layout.html`: ベースレイアウト
- `templates/index.html`: ホームページ
- `templates/guilds.html`: サーバー一覧
- `templates/main_settings.html`: メイン設定
- など

## マイクロサービス

SharkBot-v2 は複数のマイクロサービスで構成されています:

### Graph Service
- **場所**: `src/Graph/`
- **機能**: matplotlib を使用してグラフを生成
- **使用例**: サーバー統計、レベルランキングなど

### AI Module
- **場所**: `src/aimod/`
- **機能**: AI チャット機能
- **モデル**: Google Gen AI

### URL短縮サービス
- **場所**: `src/short/`
- **機能**: URL を短縮

### YouTube統合
- **場所**: `src/youtube/`
- **機能**: YouTube 動画情報の取得

### ColorBot
- **場所**: `src/colorbot/`
- **機能**: カラー管理 Bot (サブモジュール)

## フロー図

### コマンド実行フロー

```
Discord ユーザー
    │
    │ スラッシュコマンド実行
    ▼
CustomTree._from_interaction()
    │
    ├─► DMチェック → NG → エラー応答
    ├─► コマンド無効化チェック → NG → エラー応答
    ├─► チャンネル無効化チェック → NG → エラー応答
    ├─► ユーザーBanチェック → NG → エラー応答
    ├─► サーバーBanチェック → NG → エラー応答
    │
    ▼ OK
言語設定読み込み
    │
    ▼
Cog コマンド実行
    │
    ├─► MongoDB アクセス
    ├─► 外部API呼び出し
    ├─► 画像生成
    │
    ▼
Discord に応答
```

### Bot起動フロー

```
bot.py 実行
    │
    ▼
NewSharkBot 初期化
    │
    ├─► MongoDB接続
    └─► CustomTree設定
    │
    ▼
setup_hook()
    │
    ├─► 翻訳データロード
    ├─► Cog自動ロード
    └─► コマンド同期
    │
    ▼
on_ready()
    │
    ├─► Jishaku ロード
    ├─► プレゼンス設定
    └─► ログ表示
    │
    ▼
Bot 稼働中
```

### ダッシュボードアクセスフロー

```
ユーザー
    │
    ▼
/login アクセス
    │
    ▼
Discord OAuth2 認証
    │
    ▼
/login/callback
    │
    ├─► アクセストークン取得
    ├─► ユーザー情報取得
    └─► ギルド情報取得
    │
    ▼
ダッシュボード
    │
    ├─► サーバー選択
    ├─► 設定変更
    │   │
    │   ▼
    │   MongoDB更新
    │
    ▼
Bot に反映
```

## パフォーマンス最適化

### シャーディング

`AutoShardedBot` を使用して複数のシャードに分散:
- Discord が推奨するシャード数を自動計算
- 各シャードが独立して動作
- 負荷分散とスケーラビリティの向上

### データベースキャッシュ

頻繁にアクセスされるデータはメモリにキャッシュ:
- 翻訳データ
- 設定データ
- コマンド無効化リスト

### 非同期処理

すべての I/O 操作は非同期で実行:
- MongoDB アクセス
- HTTP リクエスト
- Discord API 呼び出し

## セキュリティ

### 認証と認可

1. **Bot管理者チェック**: 特定のコマンドは Bot 管理者のみ実行可能
2. **サーバー権限チェック**: Discord の権限システムを使用
3. **コマンド無効化**: サーバー管理者がコマンドを無効化可能
4. **ユーザー/サーバーBan**: 不正利用者を Ban

### データ保護

1. **環境変数**: 機密情報は環境変数で管理
2. **セッション管理**: FastAPI の SessionMiddleware
3. **レート制限**: slowapi を使用した API レート制限

## 拡張性

### 新しい Cog の追加

1. `src/cogs/` に新しい `.py` ファイルを作成
2. `commands.Cog` を継承したクラスを実装
3. `async def setup(bot)` 関数を定義
4. Bot 再起動で自動的にロードされる

### 新しい API エンドポイントの追加

1. `src/router/` に新しいルーターを作成
2. `api.py` でルーターをインクルード
3. FastAPI が自動的にルーティング

### 新しい言語の追加

1. `src/translate/` に新しい言語の JSON ファイルを追加
2. `translate.py` で言語をサポート
3. すべてのコマンドで自動的に翻訳が適用される
