import time
import discord
from discord.ext import commands
from discord import app_commands
# import TagScriptEngine as tse
from consts import badword
import io

from models import make_embed

cooldown_tags = {}


class TagsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> TagsCog")

    def replace_tag(self, text: str, args: str, author: discord.Member):
        return text.replace('{args}', args).replace('{author}', author.name).replace('{author_id}', str(author.id))

    tag = app_commands.Group(
        name="tag", description="タグスクリプトを設定します。"
    )

    # ---------- タグ作成 ----------
    @tag.command(name="create", description="tagを作成します。")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tag_create(
        self,
        interaction: discord.Interaction,
        名前: str
    ):

        class TagCreateModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Tagを作成する。", timeout=180)

            code = discord.ui.Label(
                text="コードを入力",
                description="コードを入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.long, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                assert isinstance(self.code.component, discord.ui.TextInput)
                lower_script = self.code.component.value.lower()
                for word in badword.badwords:
                    if word.lower() in lower_script:
                        embed = make_embed.error_embed(title="Tag作成に失敗しました。")
                        return await interaction_.response.send_message(embed=embed)

                db = interaction.client.async_db["Main"].Tags
                await db.update_one(
                    {"command": 名前, "guild_id": interaction_.guild.id},
                    {"$set": {"tagscript": self.code.component.value}},
                    upsert=True
                )
                embed = make_embed.success_embed(title="Tagを作成しました。")
                await interaction_.response.send_message(
                    embed=embed
                )

        await interaction.response.send_modal(TagCreateModal())

    # ---------- タグ削除 ----------
    @tag.command(name="delete", description="tagを削除します。")
    @app_commands.checks.has_permissions(manage_messages=True)
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
            embed = make_embed.error_embed(title="そのTagは存在しません。")
            return await interaction.response.send_message(
                embed=embed
            )

        await db.delete_one({"guild_id": interaction.guild.id, "command": 名前})

        embed = make_embed.success_embed(title="Tagを削除しました。")

        await interaction.response.send_message(
            embed=embed
        )

    @tag.command(name="tags", description="タグリストを表示します。")
    @app_commands.checks.has_permissions(manage_messages=True)
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

    @tag.command(name="use", description="tagを使用します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tags_use(
        self,
        interaction: discord.Interaction,
        コマンド名: str,
        引数: str = "No Args."
    ):
        await interaction.response.defer()
        db_tags = self.bot.async_db["Main"].Tags
        doc = await db_tags.find_one({"guild_id": interaction.guild.id, "command": コマンド名})
        if doc:
            try:
                ts_script = doc["tagscript"]
                await interaction.followup.send(self.replace_tag(ts_script, 引数, interaction.user) + "\n-# これはタグスクリプトからのメッセージです。")
            except Exception as e:
                return await interaction.followup.send("エラーが発生しました。")
        else:
            await interaction.followup.send(embed=make_embed.error_embed(title="Tagが見つかりません。", description=f"`/tag create`で作成できます。"))

    @tag.command(name="export", description="タグをエクスポートします。")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tags_export(
        self,
        interaction: discord.Interaction,
        名前: str
    ):
        db_tags = self.bot.async_db["Main"].Tags
        doc = await db_tags.find_one({"guild_id": interaction.guild.id, "command": 名前})
        if doc:
            i = io.StringIO(str(doc.get('tagscript', 'None')))
            await interaction.response.send_message(file=discord.File(i, filename="tag.txt"))
            i.close()
        else:
            await interaction.response.send_message(content="そのタグが見つかりません。", ephemeral=True)

    # ---------- メッセージ監視でカスタムタグ実行 ----------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild:
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
            try:
                current_time = time.time()
                last_message_time = cooldown_tags.get(message.guild.id, 0)
                if current_time - last_message_time < 3:
                    return
                cooldown_tags[message.guild.id] = current_time

                ts_script = doc["tagscript"]
                await message.channel.send(self.replace_tag(ts_script, args, message.author) + "\n-# これはタグスクリプトからのメッセージです。")
            except Exception as e:
                return await message.channel.send("エラーが発生しました。")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            a = None
            return a

async def setup(bot):
    await bot.add_cog(TagsCog(bot))
