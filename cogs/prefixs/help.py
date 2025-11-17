import io
from discord.ext import commands
import discord
from consts import settings
from discord import app_commands
from models import command_disable, make_embed
import aiohttp

HELP_TREE = {
    "管理機能": {
        "モデレーション": [
            {"name": "moderation kick", "description": "メンバーをキックします。"},
            {"name": "moderation ban ban", "description": "ユーザーをBanします。"},
            {"name": "moderation ban unban", "description": "ユーザーのBanを解除します。"},
            {"name": "moderation ban massban", "description": "複数人を一斉にbanします。"},
            {"name": "moderation ban softban", "description": "Ban機能を利用してメッセージを一斉削除します。"},
            {"name": "moderation timeout", "description": "メンバーをタイムアウトします。"},
            {"name": "moderation untimeout", "description": "タイムアウトを解除します。"},
            {"name": "moderation max-timeout", "description": "タイムアウトができる最大までタイムアウトします。"},
            {"name": "moderation clear", "description": "メッセージを削除します。"},
            {"name": "moderation warn", "description": "メンバーを警告します。"},
            {"name": "moderation warns", "description": "メンバーの警告回数を確認します。"},
            {"name": "moderation remake", "description": "チャンネルを再生成します。"},
            {"name": "moderation lock", "description": "チャンネルで話せなくします。"},
            {"name": "moderation unlock", "description": "チャンネルを開放します。"},
            {"name": "moderation report", "description": "通報チャンネルをセットアップします。"},
            {"name": "moderation serverban", "description": "web認証時に指定したサーバーに入っていると認証できなくします。"},
            {"name": "moderation serverunban", "description": "web認証時に指定したサーバーに入っていても認証できるようにします。"},
            {"name": "moderation auditlog", "description": "監査ログをダンプします。"},
            {"name": "moderation lottery", "description": "抽選をします。"},
        ],
        "DM・招待停止": [
            {"name": "moderation pause invite", "description": "招待を一時停止します。"},
            {"name": "moderation pause dm", "description": "DMを一時停止します。"},
            {"name": "moderation pause both", "description": "DMと招待を一時停止します。"},
        ],
        "自動管理": [
            {"name": "automod create", "description": "AutoModを作成します。"},
            {"name": "automod delete", "description": "AutoModを削除します。"},
            {"name": "automod customword", "description": "カスタムワードを禁止するAutoModを作成します。"},
        ],
        "自動返信": [
            {"name": "autoreply create", "description": "自動返信を作成します。"},
            {"name": "autoreply delete", "description": "自動返信を削除します。"},
            {"name": "autoreply list", "description": "自動返信リストを表示します。"},
            {"name": "autoreply templates", "description": "自動返信をテンプレートから作成します。"},
            {"name": "autoreply export", "description": "自動返信ををエクスポートします。"},
            {"name": "autoreply import", "description": "自動返信ををインポートします。"},
        ],
        "自動リアクション": [
            {"name": "autoreact channel", "description": "自動リアクションをチャンネルを条件にして作成します。"},
            {"name": "autoreact word", "description": "自動リアクションをワードを条件にして作成します。"},
            {"name": "autoreact remove", "description": "自動リアクションを削除します。"},
            {"name": "autoreact list", "description": "自動リアクションをリスト化します。"}
        ],
        "自動GIF・GIF検索": [
            {"name": "gif search", "description": "GIFを検索します。"},
            {"name": "gif autogif-channel add", "description": "自動gif返信のチャンネルを追加します。"},
            {"name": "gif autogif-channel remove", "description": "自動gif返信チャンネルを削除します。"},
        ],
        "オフライン検知": [
            {"name": "autodown settings", "description": "オフライン検知の設定を確認します。"},
            {"name": "autodown vc-kick", "description": "オフラインになるとVCからキックするように設定します。"},
        ],
        "ロール管理": [
            {"name": "role add", "description": "ロールを追加します。"},
            {"name": "role remove", "description": "ロールを剝奪します。"},
            {"name": "role color-role", "description": "色ロールを作成します。"},
            {"name": "role can-bot", "description": "そのロールをBotが扱えるかをチェックします。"},
        ],
        "ニックネーム管理": [
            {"name": "nick edit", "description": "ニックネームを編集します。"},
            {"name": "role reset", "description": "ニックネームをリセットします。"},
        ],
        "様々なパネル": {
            "ロールパネル": [
                {"name": "panel role", "description": "ロールパネルを作成します。"},
                {"name": "panel role-edit", "description": "ロールパネルを編集します。"},
                {"name": "panel newgui-rolepanel", "description": "新しいロールパネルを作成します。"},
                {"name": "panel newgui-rolepanel-edit", "description": "新しいロールパネルを編集します。"},
                {"name": "panel select-rolepanel", "description": "セレクトボックス式ロールパネルを作成します。"},
                {"name": "panel random", "description": "ランダムなロールが付与されるロールパネルを作成します。"},
            ],
            "アンケート・メンバー募集": [
                {"name": "panel poll", "description": "投票ををします。"},
                {"name": "panel enquete", "description": "アンケートを取ります。"},
                {"name": "panel party", "description": "募集パネルを作成します。"},
            ],
            "チケット": [
                {"name": "panel ticket", "description": "チケットパネルを作成します。"},
            ],
            "認証": [
                {"name": "panel auth abs-auth", "description": "絶対値を入力させる認証パネルを作成します。"},
                {"name": "panel auth arror-auth", "description": "矢印の向きを入力させるパネルを作成します。"},
                {"name": "panel auth auth", "description": "ワンクリック認証パネルを作成します。"},
                {"name": "panel auth-plus", "description": "認証したらロールが外れた後にロールが付くパネルを作ります。"},
                {"name": "panel auth webauth", "description": "Web認証パネルを作成します。"},
                {"name": "panel auth image", "description": "画像認証パネルを作成します。"},
                {"name": "panel auth guideline", "description": "ルールに同意させるパネルを作成します。"},
                {"name": "panel auth auth-reqrole", "description": "認証パネルに必要なロールを設定します。"},
            ]
        },
        "その他設定": [
            {"name": "settings lock-message", "description": "固定メッセージをセットアップします。"},
            {"name": "settings prefix", "description": "頭文字を設定します。"},
            {"name": "settings score", "description": "処罰スコアを設定します。"},
            {"name": "settings warn-setting", "description": "AutoModでの警告時に実行する内容を設定します。"},
            {"name": "settings expand", "description": "メッセージ展開をセットアップします。"},
            {"name": "settings auto-publish", "description": "自動アナウンス公開をセットアップします。"},
            {"name": "settings file-deletor", "description": "自動的に削除するファイル拡張子を設定します。"},
            {"name": "settings auto-translate", "description": "自動翻訳を設定します。"},
            {"name": "settings good-morning", "description": "Botが挨拶をするチャンネルをセットアップします。"},
            {"name": "settings auto-thread", "description": "自動スレッド作成をセットアップします。"},
            {"name": "settings lang", "description": "Change the bot's language. (Beta)"},
        ]
    },
    "便利機能": {
        "ネットワークツール": [
            {"name": "tools network iplookup", "description": "IPを検索します。"},
            {"name": "tools network nslookup", "description": "DNS情報を取得します。"},
            {"name": "tools network meta", "description": "サイトのメタデータを取得します。"},
            {"name": "tools network ping", "description": "ドメインにPingを送信します。"},
            {"name": "tools network whois", "description": "Whois検索をします。"},
        ],
        "計算機能": [
            {"name": "tools calc size-converter", "description": "サイズの計算をします。"},
            {"name": "tools calc calculator", "description": "電卓を使用します。"},
        ],
        "OCR機能": [
            {"name": "tools ocr ocr", "description": "OCRをします・"},
        ],
        "Twitter系の機能": [
            {"name": "tools twitter info", "description": "ツイート情報を取得します。"},
        ],
        "その他便利機能": [
            {"name": "tools embed", "description": "埋め込みを作成します。"},
            {"name": "tools button", "description": "ボタンを作成します。"},
            {"name": "tools choise", "description": "Botが選びます。"},
            {"name": "tools timestamp", "description": "timestampを作成します。"},
            {"name": "tools todo", "description": "TODOを作成します。"},
            {"name": "tools invite", "description": "招待リンクを作成します。"},
            {"name": "tools uuid", "description": "UUIDを作成します。"},
            {"name": "tools short", "description": "短縮URLを作成します。"},
            {"name": "tools afk", "description": "留守番をしてもらいます。"},
            {"name": "tools timer", "description": "タイマーをセットします。"},
            {"name": "tools qr", "description": "QRコードを作成&読み取りします。"},
            {"name": "tools weather", "description": "天気を取得します。"},
            {"name": "tools reminder", "description": "リマインダーを作成します。"},
            {"name": "tools calendar", "description": "カレンダーをダウンロードします。"},
            {"name": "tools download", "description": "いろいろダウンロードします。"},
        ]
    },
    "検索機能": {
        "Discord上の検索": [
            {"name": "search multi", "description": "一斉に検索します。"},
            {"name": "search tag", "description": "サーバータグを何人がつけているかを検索します。"},
            {"name": "search user", "description": "ユーザーを検索します。"},
            {"name": "search server", "description": "サーバーを検索します。"},
            {"name": "search channel", "description": "チャンネルを検索します。"},
            {"name": "search ban", "description": "ユーザーBanを検索します。"},
            {"name": "search bot", "description": "サーバーに入れたBotを検索します。"},
            {"name": "search invite", "description": "招待リンクを検索します。"},
            {"name": "search avatar", "description": "ユーザーのアバターを検索します。"},
            {"name": "search banner", "description": "ユーザーのバナーを検索します。"},
            {"name": "search emoji", "description": "絵文字を検索します。"},
            {"name": "search spotify", "description": "ユーザーの聞いている曲を検索します。"},
            {"name": "search snowflake", "description": "Snowflakeを検索します。"},
        ],
        "Web上の検索": [
            {"name": "search web translate", "description": "翻訳をします。"},
            {"name": "search web news", "description": "ニュースを取得します。"},
            {"name": "search web wikipedia", "description": "Wikipediaを取得します。"},
            {"name": "search web safeweb", "description": "SafeWebでURLの安全性をチェックします。"},
            {"name": "search web anime", "description": "アニメを検索します。"},
        ]
    }
}

class Paginator(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current = 0

    async def update_message(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.embeds[self.current], view=self
        )

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current = (self.current - 1) % len(self.embeds)
        await self.update_message(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = (self.current + 1) % len(self.embeds)
        await self.update_message(interaction)

class CategoryView(discord.ui.View):
    def __init__(self, tree: dict, path: list):
        super().__init__(timeout=180)
        self.add_item(CategorySelect(tree, path))

        if len(path) > 1:
            self.add_item(BackButton(path))

class BackButton(discord.ui.Button):
    def __init__(self, path: list):
        super().__init__(label="← 戻る", style=discord.ButtonStyle.secondary)
        self.path = path

    async def callback(self, interaction: discord.Interaction):
        if len(self.path) <= 1:
            return

        tree = HELP_TREE
        for p in self.path[1:-1]:
            tree = tree[p]

        new_path = self.path[:-1]

        await interaction.response.edit_message(
            content=f"**{' > '.join(new_path)}** に戻りました",
            view=CategoryView(tree, new_path),
            embed=None
        )

class BackOnlyView(discord.ui.View):
    def __init__(self, path: list):
        super().__init__(timeout=180)
        self.add_item(BackButton(path))

class CategorySelect(discord.ui.Select):
    def __init__(self, tree: dict, path: list):
        """
        tree: 今の階層（dict または list）
        path: 現在の階層 ["親", "子", ...]
        """

        self.tree = tree
        self.path = path

        options = [
            discord.SelectOption(label=str(key))
            for key in tree.keys()
        ]

        super().__init__(
            placeholder=" > ".join(path) + " のカテゴリを選択",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]

        next_tree = self.tree[selected]
        new_path = self.path + [selected]

        if isinstance(next_tree, dict):
            await interaction.response.edit_message(
                content=f"**{' > '.join(new_path)} を選択中...**",
                view=CategoryView(next_tree, new_path),
                embed=None
            )
        else:
            embed = make_embed.success_embed(
                title="ヘルプ : " + " > ".join(new_path)
            )

            for cmd in next_tree:
                embed.add_field(
                    name=f"/{cmd['name']}",
                    value=cmd["description"],
                    inline=False
                )

            await interaction.response.edit_message(embed=embed, view=BackOnlyView(self.path), content="")

class Prefixs_HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> Prefixs_HelpCog")

    @commands.command(name="help_beta", aliases=["hb"], description="スラッシュコマンド用のヘルプを表示します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def help_beta_slash(self, ctx: commands.Context):
        await ctx.reply(
            content="**カテゴリを選択してください**",
            view=CategoryView(HELP_TREE, ["ヘルプ"])
        )

    @commands.command(name="help", aliases=["h"], description="頭文字用ヘルプを表示します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def help_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname("help", ctx.guild):
            return
        
        ems = []

        for start in range(0, len(list(self.bot.commands)), 10):
            embed = make_embed.success_embed(title="SharkBotのヘルプ (頭文字バージョン)", description="頭文字バージョンです。\nスラッシュコマンド用ヘルプは、\n`/help`を使用してください。\n\nちなみに、頭文字コマンドは、\n`[頭文字]コマンド名`と送信することで機能します。\n\n標準頭文字: `!.`")
            
            embed.add_field(name="コマンド一覧", value="以下がコマンド一覧です。\n下のボタンでページを切り替えられます。", inline=False)
            
            for cmd in list(self.bot.commands)[start : start + 10]:
                if "load" in cmd.name:
                    continue
                if "jishaku" in cmd.name:
                    continue
                if "sync_slash" == cmd.name:
                    continue
                if "save" == cmd.name:
                    continue
                if "task" == cmd.name:
                    continue
                if "send" == cmd.name:
                    continue

                al = ', '.join(cmd.aliases)

                al = al if al else "なし"

                embed.add_field(name=cmd.name, value=cmd.description + f"\n別名: " + al, inline=False)

            ems.append(embed)

        c = 1
        for e in ems:
            if type(e) != discord.Embed:
                continue
            e.set_footer(text=f"{c} / {len(ems)}")
            c += 1

        await ctx.reply(embed=ems[0], view=Paginator(ems))

    @commands.command(name="dashboard", aliases=["d"], description="ダッシュボードの案内を表示します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def dashboard_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname("dashboard", ctx.guild):
            return
        
        await ctx.reply(f"現在はダッシュボードにアクセスできません。")

    @commands.command(name="source", aliases=["so"], description="Botのソースコードを表示します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def source_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname("help", ctx.guild):
            return
        
        base_url = "https://github.com/SharkBot-Dev/SharkBot-v2"

        await ctx.reply(base_url)

    @commands.command(name="aliases", aliases=["a"], description="頭文字コマンドの別名からコマンドを検索します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def aliases_prefix(self, ctx: commands.Context, aliases: str):
        if not await command_disable.command_enabled_check_by_cmdname("help", ctx.guild):
            return
        
        command = self.bot.commands
        for c in command:
            if aliases in list(c.aliases):
                return await ctx.reply(embed=make_embed.success_embed(title=f"{c.name} を発見しました。")
                                       .add_field(name="コマンド名", value=c.name, inline=False)
                                       .add_field(name="説明", value=c.description, inline=False)
                                       .add_field(name="ほかの別名", value=", ".join(list(c.aliases))))
            
        await ctx.reply(embed=make_embed.error_embed(title="コマンドが見つかりませんでした。", description="ヘルプコマンドで正しい別名を確認してください。"))

async def setup(bot):
    await bot.add_cog(Prefixs_HelpCog(bot))
