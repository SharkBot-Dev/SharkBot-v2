# Cog 開発ガイド

このドキュメントでは SharkBot-v2 で Cog (拡張機能) を開発する方法を説明します。

## 目次

- [Cog とは](#cog-とは)
- [基本的な Cog の作成](#基本的な-cog-の作成)
- [コマンドの種類](#コマンドの種類)
- [データベースの使用](#データベースの使用)
- [エラーハンドリング](#エラーハンドリング)
- [権限チェック](#権限チェック)
- [翻訳対応](#翻訳対応)
- [ベストプラクティス](#ベストプラクティス)
- [実例](#実例)

## Cog とは

Cog は Discord Bot の機能を論理的に分割して管理するための仕組みです。SharkBot-v2 では、各機能を個別の Cog として実装し、`src/cogs/` ディレクトリに配置します。

### Cog の利点

- **モジュール性**: 機能ごとに分離して開発・テスト可能
- **再利用性**: 他のプロジェクトでも使用可能
- **保守性**: コードが整理され、バグ修正が容易
- **ホットリロード**: Bot を再起動せずに Cog をリロード可能

## 基本的な Cog の作成

### 最小限の Cog

```python
from discord.ext import commands
import discord
from discord import app_commands

class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> MyCog")

    @app_commands.command(name="hello", description="挨拶します")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("こんにちは！")

async def setup(bot: commands.Bot):
    await bot.add_cog(MyCog(bot))
```

### ファイルの配置

1. `src/cogs/mycog.py` として保存
2. Bot を再起動すると自動的にロードされます

### Cog のリロード

開発中に Cog を変更した場合:

```
/admin cogs 操作の種類:リロード cog名:mycog
```

または Jishaku を使用:

```
!jsk reload cogs.mycog
```

## コマンドの種類

### スラッシュコマンド (推奨)

```python
@app_commands.command(name="test", description="テストコマンド")
async def test(self, interaction: discord.Interaction):
    await interaction.response.send_message("テスト成功！")
```

### サブコマンド

```python
# グループの作成
admin = app_commands.Group(
    name="admin",
    description="管理者コマンド"
)

# サブコマンドの追加
@admin.command(name="kick", description="ユーザーをキック")
async def admin_kick(
    self,
    interaction: discord.Interaction,
    user: discord.Member
):
    await user.kick()
    await interaction.response.send_message(f"{user.name} をキックしました。")
```

### 選択肢付きコマンド

```python
@app_commands.command(name="choose", description="選択肢から選ぶ")
@app_commands.choices(
    option=[
        app_commands.Choice(name="オプション1", value="opt1"),
        app_commands.Choice(name="オプション2", value="opt2"),
        app_commands.Choice(name="オプション3", value="opt3"),
    ]
)
async def choose(
    self,
    interaction: discord.Interaction,
    option: app_commands.Choice[str]
):
    await interaction.response.send_message(f"選択: {option.name}")
```

### コンテキストメニュー

```python
@app_commands.context_menu(name="ユーザー情報")
async def user_info(self, interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        f"ユーザー名: {user.name}\nID: {user.id}"
    )
```

## データベースの使用

### MongoDB へのアクセス

```python
class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.async_db["DashboardBot"]  # データベース
        self.collection = self.db["MyCollection"]  # コレクション

    @app_commands.command(name="save", description="データを保存")
    async def save_data(self, interaction: discord.Interaction, text: str):
        # データの挿入
        await self.collection.insert_one({
            "Guild": interaction.guild.id,
            "User": interaction.user.id,
            "Text": text
        })
        await interaction.response.send_message("保存しました！")

    @app_commands.command(name="load", description="データを読み込み")
    async def load_data(self, interaction: discord.Interaction):
        # データの取得
        data = await self.collection.find_one({
            "Guild": interaction.guild.id,
            "User": interaction.user.id
        })
        
        if data:
            await interaction.response.send_message(f"保存されたテキスト: {data['Text']}")
        else:
            await interaction.response.send_message("データが見つかりません。")
```

### データの操作

```python
# 挿入
await collection.insert_one({"key": "value"})

# 検索
data = await collection.find_one({"key": "value"})

# 更新
await collection.update_one(
    {"key": "value"},
    {"$set": {"new_key": "new_value"}}
)

# 削除
await collection.delete_one({"key": "value"})

# 複数取得
cursor = collection.find({"Guild": guild_id})
data_list = await cursor.to_list(length=100)
```

## エラーハンドリング

### エラー応答の表示

```python
from models import make_embed

@app_commands.command(name="test", description="テスト")
async def test(self, interaction: discord.Interaction):
    try:
        # 何か処理
        result = await some_operation()
        await interaction.response.send_message("成功！")
    except Exception as e:
        # エラー応答
        await interaction.response.send_message(
            embed=make_embed.error_embed(
                title="エラーが発生しました",
                description=str(e)
            ),
            ephemeral=True
        )
```

### カスタムエラーハンドラ

```python
class MyCog(commands.Cog):
    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="権限エラー",
                    description="このコマンドを実行する権限がありません。"
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="エラー",
                    description=str(error)
                ),
                ephemeral=True
            )
```

## 権限チェック

### Discord の権限チェック

```python
from discord import app_commands

@app_commands.command(name="kick", description="ユーザーをキック")
@app_commands.default_permissions(kick_members=True)
async def kick(
    self,
    interaction: discord.Interaction,
    user: discord.Member
):
    # kick_members 権限が必要
    await user.kick()
    await interaction.response.send_message(f"{user.name} をキックしました。")
```

### カスタム権限チェック

```python
async def is_admin(interaction: discord.Interaction) -> bool:
    """Bot 管理者かチェック"""
    db = interaction.client.async_db["Main"]
    collection = db["BotAdmins"]
    data = await collection.find_one({"User": interaction.user.id})
    return data is not None

@app_commands.command(name="admin_only", description="管理者専用")
async def admin_only(self, interaction: discord.Interaction):
    if not await is_admin(interaction):
        await interaction.response.send_message(
            embed=make_embed.error_embed(
                title="権限エラー",
                description="このコマンドはBot管理者のみ実行できます。"
            ),
            ephemeral=True
        )
        return
    
    await interaction.response.send_message("管理者コマンド実行！")
```

## 翻訳対応

### 翻訳システムの使用

```python
@app_commands.command(name="hello", description="挨拶します")
async def hello(self, interaction: discord.Interaction):
    # 言語設定を取得 (CustomTree で自動設定)
    lang = interaction.extras.get("lang", "ja")
    
    # 翻訳データから取得
    messages = {
        "ja": "こんにちは！",
        "en": "Hello!"
    }
    
    message = messages.get(lang, messages["ja"])
    await interaction.response.send_message(message)
```

### translate モジュールの使用

```python
from models import translate

@app_commands.command(name="greet", description="挨拶します")
async def greet(self, interaction: discord.Interaction):
    lang = interaction.extras.get("lang", "ja")
    
    # 翻訳キーから取得
    greeting = await translate.get_text("greeting", lang)
    
    await interaction.response.send_message(greeting)
```

## ベストプラクティス

### 1. Embed を使用した見やすい応答

```python
from models import make_embed

@app_commands.command(name="info", description="情報を表示")
async def info(self, interaction: discord.Interaction):
    embed = discord.Embed(
        title="情報",
        description="これは情報です",
        color=discord.Color.blue()
    )
    embed.add_field(name="フィールド1", value="値1", inline=False)
    embed.add_field(name="フィールド2", value="値2", inline=False)
    embed.set_footer(text="SharkBot")
    
    await interaction.response.send_message(embed=embed)
```

### 2. 遅延応答の使用

長時間かかる処理の場合:

```python
@app_commands.command(name="heavy", description="重い処理")
async def heavy_task(self, interaction: discord.Interaction):
    # 遅延応答 (3秒以内に応答が必要なため)
    await interaction.response.defer()
    
    # 重い処理
    result = await some_heavy_operation()
    
    # フォローアップメッセージ
    await interaction.followup.send(f"結果: {result}")
```

### 3. Ephemeral メッセージ

他のユーザーに見せたくない情報:

```python
@app_commands.command(name="secret", description="秘密の情報")
async def secret(self, interaction: discord.Interaction):
    await interaction.response.send_message(
        "これは秘密の情報です",
        ephemeral=True  # 実行者のみに表示
    )
```

### 4. ビューとボタンの使用

```python
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__()
    
    @discord.ui.button(label="クリック", style=discord.ButtonStyle.primary)
    async def button_callback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message("ボタンがクリックされました！")

@app_commands.command(name="button", description="ボタンを表示")
async def button_test(self, interaction: discord.Interaction):
    view = MyView()
    await interaction.response.send_message("ボタンをクリックしてください", view=view)
```

### 5. オートコンプリート

```python
async def color_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    colors = ["赤", "青", "緑", "黄", "紫"]
    return [
        app_commands.Choice(name=color, value=color)
        for color in colors if current.lower() in color.lower()
    ]

@app_commands.command(name="color", description="色を選択")
@app_commands.autocomplete(color=color_autocomplete)
async def choose_color(self, interaction: discord.Interaction, color: str):
    await interaction.response.send_message(f"選択した色: {color}")
```

## 実例

### 簡単な投票 Cog

```python
from discord.ext import commands
import discord
from discord import app_commands
from models import make_embed

class PollCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> PollCog")
    
    @app_commands.command(name="poll", description="投票を作成")
    async def create_poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None
    ):
        # Embed を作成
        embed = discord.Embed(
            title="📊 投票",
            description=question,
            color=discord.Color.blue()
        )
        
        # オプションを追加
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        options = [option1, option2, option3, option4]
        
        for i, option in enumerate(options):
            if option:
                embed.add_field(
                    name=f"{emojis[i]} オプション {i+1}",
                    value=option,
                    inline=False
                )
        
        embed.set_footer(text=f"作成者: {interaction.user.name}")
        
        # メッセージを送信
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # リアクションを追加
        for i, option in enumerate(options):
            if option:
                await message.add_reaction(emojis[i])

async def setup(bot: commands.Bot):
    await bot.add_cog(PollCog(bot))
```

### データベースを使用した Todo Cog

```python
from discord.ext import commands
import discord
from discord import app_commands
from models import make_embed

class TodoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.async_db["DashboardBot"]
        self.collection = self.db["Todos"]
        print("init -> TodoCog")
    
    todo = app_commands.Group(name="todo", description="Todoリスト管理")
    
    @todo.command(name="add", description="Todoを追加")
    async def todo_add(self, interaction: discord.Interaction, task: str):
        await self.collection.insert_one({
            "Guild": interaction.guild.id,
            "User": interaction.user.id,
            "Task": task,
            "Done": False
        })
        
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="✅ Todo追加",
                description=f"「{task}」を追加しました。"
            )
        )
    
    @todo.command(name="list", description="Todoリストを表示")
    async def todo_list(self, interaction: discord.Interaction):
        cursor = self.collection.find({
            "Guild": interaction.guild.id,
            "User": interaction.user.id,
            "Done": False
        })
        todos = await cursor.to_list(length=100)
        
        if not todos:
            await interaction.response.send_message("Todoはありません。")
            return
        
        embed = discord.Embed(
            title="📝 Todoリスト",
            color=discord.Color.blue()
        )
        
        for i, todo in enumerate(todos, 1):
            embed.add_field(
                name=f"{i}. {todo['Task']}",
                value="未完了",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @todo.command(name="done", description="Todoを完了")
    async def todo_done(self, interaction: discord.Interaction, task: str):
        result = await self.collection.update_one(
            {
                "Guild": interaction.guild.id,
                "User": interaction.user.id,
                "Task": task,
                "Done": False
            },
            {"$set": {"Done": True}}
        )
        
        if result.modified_count > 0:
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="✅ 完了",
                    description=f"「{task}」を完了しました。"
                )
            )
        else:
            await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="エラー",
                    description="タスクが見つかりません。"
                ),
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(TodoCog(bot))
```

## デバッグのヒント

### ログの出力

```python
import logging

logger = logging.getLogger(__name__)

@app_commands.command(name="test", description="テスト")
async def test(self, interaction: discord.Interaction):
    logger.info(f"Test command executed by {interaction.user.name}")
    await interaction.response.send_message("テスト")
```

### プリントデバッグ

```python
@app_commands.command(name="debug", description="デバッグ")
async def debug(self, interaction: discord.Interaction):
    print(f"Guild: {interaction.guild.name}")
    print(f"User: {interaction.user.name}")
    print(f"Channel: {interaction.channel.name}")
    await interaction.response.send_message("デバッグ情報をコンソールに出力しました")
```

## 次のステップ

- [ARCHITECTURE.md](./ARCHITECTURE.md) でシステムの全体像を理解
- [API.md](./API.md) で API ドキュメントを確認
- 既存の Cog (`src/cogs/`) を参考にする
- [Discord.py ドキュメント](https://discordpy.readthedocs.io/) を読む
