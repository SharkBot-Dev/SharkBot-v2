# API ドキュメント

このドキュメントでは SharkBot-v2 の Web API とダッシュボードについて説明します。

## 目次

- [概要](#概要)
- [認証](#認証)
- [エンドポイント](#エンドポイント)
- [ダッシュボード](#ダッシュボード)
- [API の拡張](#api-の拡張)

## 概要

SharkBot-v2 は FastAPI を使用して Web ダッシュボードと API を提供します。

### 技術スタック

- **FastAPI**: Web フレームワーク
- **Uvicorn**: ASGI サーバー
- **Jinja2**: テンプレートエンジン
- **SlowAPI**: レート制限
- **MongoDB**: データストレージ

### アーキテクチャ

```
api.py (FastAPI アプリケーション)
├── SessionMiddleware: セッション管理
├── Limiter: レート制限
├── StaticFiles: 静的ファイル配信 (/static)
└── Routers:
    ├── mainpage: メインページ
    └── settings: 設定ページ
```

## 認証

### Discord OAuth2 認証

SharkBot-v2 は Discord OAuth2 を使用してユーザー認証を行います。

#### 認証フロー

```
1. ユーザーが /login にアクセス
   ↓
2. Discord 認証ページにリダイレクト
   ↓
3. ユーザーが認証を許可
   ↓
4. /login/callback にリダイレクト
   ↓
5. アクセストークンを取得
   ↓
6. ユーザー情報を取得してセッションに保存
   ↓
7. ダッシュボードにリダイレクト
```

#### エンドポイント

##### `GET /login`

Discord OAuth2 認証を開始します。

**レスポンス**: Discord 認証ページへのリダイレクト

**実装例**:
```python
@app.get("/login")
async def login():
    url = (
        f"{settings.DISCORD_API}/oauth2/authorize"
        f"?client_id={settings.CLIENT_ID}"
        f"&redirect_uri={settings.REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return RedirectResponse(url)
```

##### `GET /login/callback`

OAuth2 コールバックを処理します。

**パラメータ**:
- `code` (string): 認証コード

**レート制限**: 1回/分

**レスポンス**: ダッシュボードへのリダイレクト

**実装例**:
```python
@app.get("/login/callback")
@limiter.limit("1/minute")
async def callback(request: Request, code: str):
    # アクセストークンを取得
    token_response = await client.post(
        f"{settings.DISCORD_API}/oauth2/token",
        data={
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.REDIRECT_URI,
        }
    )
    
    # ユーザー情報を取得
    access_token = token_response.json()["access_token"]
    user_response = await client.get(
        f"{settings.DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # セッションに保存
    request.session["user"] = user_response.json()
    request.session["access_token"] = access_token
    
    return RedirectResponse("/dashboard")
```

### セッション管理

セッションは `SessionMiddleware` で管理されます。

```python
app.add_middleware(SessionMiddleware, secret_key=settings.SESSINKEY)
```

セッションデータ:
- `user`: ユーザー情報 (ID, username, avatar など)
- `access_token`: Discord アクセストークン

## エンドポイント

### メインページ

#### `GET /`

ホームページを表示します。

**レスポンス**: HTML (index.html)

### ダッシュボード

#### `GET /dashboard`

ダッシュボードのメインページを表示します。

**認証**: 必須

**レスポンス**: HTML (guilds.html) - ユーザーが参加しているサーバー一覧

#### `GET /dashboard/{guild_id}`

特定のサーバーの設定ページを表示します。

**認証**: 必須

**パラメータ**:
- `guild_id` (int): サーバー ID

**レスポンス**: HTML (main_settings.html)

### 設定 API

#### `GET /settings/{guild_id}/commands`

サーバーのコマンド設定を表示します。

**認証**: 必須

**パラメータ**:
- `guild_id` (int): サーバー ID

**レスポンス**: HTML (commands_settings.html)

#### `POST /settings/{guild_id}/commands`

コマンド設定を更新します。

**認証**: 必須

**パラメータ**:
- `guild_id` (int): サーバー ID

**リクエストボディ**:
```json
{
  "command": "コマンド名",
  "enabled": true/false
}
```

**レスポンス**: 
```json
{
  "success": true,
  "message": "設定を更新しました"
}
```

#### `GET /settings/{guild_id}/automod`

自動モデレーション設定を表示します。

**認証**: 必須

**パラメータ**:
- `guild_id` (int): サーバー ID

**レスポンス**: HTML (automod.html)

#### `POST /settings/{guild_id}/automod`

自動モデレーション設定を更新します。

**認証**: 必須

**パラメータ**:
- `guild_id` (int): サーバー ID

**リクエストボディ**:
```json
{
  "enabled": true/false,
  "spam_limit": 5,
  "mention_limit": 10
}
```

### 経済システム API

#### `GET /economy/{guild_id}/{user_id}`

ユーザーの経済データを取得します。

**認証**: 必須

**パラメータ**:
- `guild_id` (int): サーバー ID
- `user_id` (int): ユーザー ID

**レスポンス**:
```json
{
  "user_id": 123456789,
  "balance": 1000,
  "bank": 5000
}
```

## ダッシュボード

### テンプレート構造

```
templates/
├── layout.html              # ベースレイアウト
├── index.html              # ホームページ
├── guilds.html             # サーバー一覧
├── main_settings.html      # メイン設定
├── commands_settings.html  # コマンド設定
├── automod.html           # 自動モデレーション設定
├── autoreply.html         # 自動応答設定
├── welcome_settings.html  # ウェルカム設定
├── level.html             # レベルシステム設定
├── economy.html           # 経済システム設定
├── logging_setting.html   # ログ設定
├── rolepanel.html         # ロールパネル設定
├── tags.html              # タグ設定
└── make_embed.html        # Embed作成
```

### テンプレートの使用

```python
from consts import templates

@router.get("/dashboard/{guild_id}")
async def dashboard(request: Request, guild_id: int):
    # セッションからユーザー情報を取得
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    
    # サーバー情報を取得
    guild = await get_guild_info(guild_id)
    
    # テンプレートをレンダリング
    return templates.TemplateResponse(
        "main_settings.html",
        {
            "request": request,
            "user": user,
            "guild": guild
        }
    )
```

### 静的ファイル

静的ファイル (CSS, JavaScript, 画像) は `/static` ディレクトリに配置します。

```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```

テンプレートでの使用:
```html
<link rel="stylesheet" href="/static/css/style.css">
<script src="/static/js/main.js"></script>
<img src="/static/images/logo.png">
```

## API の拡張

### 新しいルーターの作成

1. `src/router/` に新しいファイルを作成

```python
# src/router/myrouter.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/api/myendpoint")
async def my_endpoint(request: Request):
    return JSONResponse({
        "message": "Hello from my endpoint!"
    })

@router.post("/api/myendpoint")
async def my_endpoint_post(request: Request):
    data = await request.json()
    # データを処理
    return JSONResponse({
        "success": True,
        "data": data
    })
```

2. `api.py` でルーターをインクルード

```python
from router import myrouter

app.include_router(myrouter.router)
```

### MongoDB へのアクセス

```python
from consts import mongodb

@router.get("/api/data/{guild_id}")
async def get_data(guild_id: int):
    # MongoDB にアクセス
    db = mongodb.client["DashboardBot"]
    collection = db["MyCollection"]
    
    # データを取得
    data = await collection.find_one({"Guild": guild_id})
    
    if data:
        return JSONResponse(data)
    else:
        return JSONResponse(
            {"error": "Data not found"},
            status_code=404
        )
```

### レート制限の設定

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/limited")
@limiter.limit("5/minute")  # 5回/分に制限
async def limited_endpoint(request: Request):
    return JSONResponse({"message": "Rate limited endpoint"})
```

### エラーハンドリング

```python
from fastapi import HTTPException

@router.get("/api/data/{item_id}")
async def get_item(item_id: int):
    # データを取得
    item = await get_item_from_db(item_id)
    
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )
    
    return JSONResponse(item)
```

### ミドルウェアの追加

```python
from starlette.middleware.base import BaseHTTPMiddleware

class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # リクエスト前の処理
        print(f"Request: {request.url}")
        
        # リクエストを処理
        response = await call_next(request)
        
        # レスポンス後の処理
        print(f"Response: {response.status_code}")
        
        return response

# ミドルウェアを追加
app.add_middleware(MyMiddleware)
```

## セキュリティ

### 認証チェック

```python
from fastapi import Depends, HTTPException

async def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    return user

@router.get("/api/protected")
async def protected_endpoint(user: dict = Depends(get_current_user)):
    return JSONResponse({
        "message": f"Hello, {user['username']}!"
    })
```

### CORS 設定

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 入力バリデーション

```python
from pydantic import BaseModel, Field

class SettingsUpdate(BaseModel):
    enabled: bool
    limit: int = Field(ge=1, le=100)  # 1-100の範囲

@router.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    # バリデーション済みのデータを使用
    return JSONResponse({
        "enabled": settings.enabled,
        "limit": settings.limit
    })
```

## 開発とテスト

### ローカル開発

```bash
cd src
uvicorn api:app --reload --port 8000
```

### API テスト

```bash
# cURL でテスト
curl http://localhost:8000/api/myendpoint

# Python でテスト
import requests
response = requests.get("http://localhost:8000/api/myendpoint")
print(response.json())
```

### ログの確認

```python
import logging

logger = logging.getLogger(__name__)

@router.get("/api/debug")
async def debug_endpoint(request: Request):
    logger.info("Debug endpoint called")
    logger.debug(f"Request headers: {request.headers}")
    return JSONResponse({"status": "ok"})
```

## 次のステップ

- [ARCHITECTURE.md](./ARCHITECTURE.md) でシステムアーキテクチャを理解
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/) を読む
- 既存のルーター (`src/router/`) を参考にする
