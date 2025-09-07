import time
import discord
from discord.ext import commands
from discord import app_commands
import TagScriptEngine as tse
from consts import badword

cooldown_tags = {}

class TagsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.engine = tse.Interpreter([
            tse.MathBlock(),
            tse.RandomBlock(),
            tse.RangeBlock(),
            tse.AnyBlock(),
            tse.IfBlock(),
            tse.AllBlock(),
            tse.BreakBlock(),
            tse.StrfBlock(),
            tse.StopBlock(),
            tse.AssignmentBlock(),
            tse.FiftyFiftyBlock(),
            tse.ShortCutRedirectBlock("args"),
            tse.LooseVariableGetterBlock(),
            tse.SubstringBlock(),
            tse.EmbedBlock(),
            tse.ReplaceBlock(),
            tse.URLEncodeBlock(),
        ])
        print("init -> TagsCog")

    tag = app_commands.Group(
        name="tag", description="タグスクリプトを設定します。"
    )

    # ---------- タグ作成 ----------
    @tag.command(name="create", description="tagを作成します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tag_create(
        self,
        interaction: discord.Interaction,
        名前: str,
        スクリプト: str
    ):
        lower_script = スクリプト.lower()
        for word in badword.badwords:
            if word.lower() in lower_script:
                return await interaction.response.send_message(embed=discord.Embed(title="Tag作成に失敗しました。", color=discord.Color.red()))

        db = self.bot.async_db["Main"].Tags
        await db.update_one(
            {"command": 名前, "guild_id": interaction.guild.id},
            {"$set": {"tagscript": スクリプト}},
            upsert=True
        )
        await interaction.response.send_message(
            embed=discord.Embed(title="Tagを作成しました。", color=discord.Color.green())
        )

    # ---------- タグ削除 ----------
    @tag.command(name="delete", description="tagを削除します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tag_delete(
        self,
        interaction: discord.Interaction,
        名前: str
    ):
        db = self.bot.async_db["Main"].Tags
        doc = await db.find_one(
            {"guild_id": interaction.guild.id, "command": 名前}
        )
        if not doc:
            return await interaction.response.send_message(
                embed=discord.Embed(title="そのTagは存在しません。", color=discord.Color.red())
            )

        await db.delete_one({"guild_id": interaction.guild.id, "command": 名前})
        await interaction.response.send_message(
            embed=discord.Embed(title="Tagを削除しました。", color=discord.Color.green())
        )

    @tag.command(name="tags", description="タグリストを表示します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tags_list(
        self,
        interaction: discord.Interaction
    ):

        db_prefix = self.bot.async_db["DashboardBot"].CustomPrefixBot
        doc = await db_prefix.find_one({"Guild": interaction.guild.id})
        PREFIX = doc.get('Prefix', '!.') if doc else '!.'

        db_tags = self.bot.async_db["Main"].Tags
        cursor = db_tags.find({"guild_id": interaction.guild.id})
        tags = [PREFIX + doc["command"] async for doc in cursor]

        if not tags:
            return await interaction.response.send_message("このサーバーにはタグが登録されていません。")

        embed = discord.Embed(
            title=f"{interaction.guild.name} のタグ一覧",
            description="\n".join(tags),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    # ---------- メッセージ監視でカスタムタグ実行 ----------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        db_prefix = self.bot.async_db["DashboardBot"].CustomPrefixBot
        doc = await db_prefix.find_one({"Guild": message.guild.id})
        PREFIX = doc.get('Prefix', '!.') if doc else '!.'

        if not message.content.startswith(PREFIX):
            return

        parts = message.content[len(PREFIX):].split()
        if not parts:
            return
        cmd_name = parts[0]
        args = " ".join(parts[1:]) if len(parts) > 1 else ""

        db_tags = self.bot.async_db["Main"].Tags
        doc = await db_tags.find_one({"guild_id": message.guild.id, "command": cmd_name})
        if doc:
            current_time = time.time()
            last_message_time = cooldown_tags.get(message.guild.id, 0)
            if current_time - last_message_time < 3:
                return
            cooldown_tags[message.guild.id] = current_time

            ts_script = doc["tagscript"]
            response = self.engine.process(ts_script,     {
                "args": tse.StringAdapter(args),        # ユーザーが入力した引数
                "author": tse.StringAdapter(str(message.author)),  # 実行者の名前
                "author_id": tse.StringAdapter(str(message.author.id)),  # 実行者の名前
                "guild": tse.StringAdapter(str(message.guild.name)), # サーバーの名前
                "channel": tse.StringAdapter(str(message.channel.name)),  # チャンネルの名前
                "guild_id": tse.StringAdapter(str(message.guild.id)),  # サーバーの名前
                "channel_id": tse.StringAdapter(str(message.channel.id)),  # サーバーの名前
            })
            await message.channel.send(response.body)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            a = None
            return a

async def setup(bot):
    await bot.add_cog(TagsCog(bot))