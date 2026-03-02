from discord.ext import commands
import discord
from discord import app_commands

from models import make_embed

from models import command_disable, translate

import asyncio
import psutil

import io
import aiohttp

FEEDBACK_CHANNEL = 1437397034213703762


class FeedBackModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="フィードバックを送信する。")
        self.text = discord.ui.TextInput(label=f"内容", style=discord.TextStyle.long)
        self.add_item(self.text)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await asyncio.sleep(1)
        await interaction.client.get_channel(FEEDBACK_CHANNEL).send(
            embed=discord.Embed(
                title=f"フィードバック: {interaction.user.id}",
                color=discord.Color.green(),
                description=self.text.value,
            )
            .add_field(
                name="ユーザー",
                value=f"{interaction.user.display_name}({interaction.user.id})",
            )
            .set_author(
                name=f"{interaction.user.display_name}({interaction.user.id})",
                icon_url=interaction.user.avatar.url
                if interaction.user.avatar
                else interaction.user.default_avatar.url,
            )
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="フィードバックを送信しました！",
                description="ご意見ありがとうございます。",
            )
        )


class BotCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> BotCog")

    bot = app_commands.Group(
        name="bot",
        description="Bot系のコマンドです。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    @bot.command(
        name="follow", description="Botのアナウンスチャンネルをフォローします。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def follow_bot(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        await interaction.response.defer()
        guild = self.bot.get_guild(1343124570131009579)
        await guild.get_channel(1419883503365128212).follow(
            destination=interaction.channel, reason="Botのアナウンスをフォロー"
        )
        await asyncio.sleep(1)
        await guild.get_channel(1347451795978453052).follow(
            destination=interaction.channel, reason="Botのアナウンスをフォロー"
        )
        await asyncio.sleep(1)
        await guild.get_channel(1361173338763956284).follow(
            destination=interaction.channel, reason="Botのアナウンスをフォロー"
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="アナウンスチャンネルを追加しました。",
                description="このチャンネルでBOTをお知らせを受け取ることができます。",
            )
        )

    @bot.command(name="about", description="Botの情報を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def about_bot(self, interaction: discord.Interaction):
        await interaction.response.defer()

        command = self.bot.tree.get_commands()

        cmd_count = 0

        for cmd in command:
            if isinstance(cmd, discord.app_commands.Group):
                cmd_count += 1
                for sub in cmd.commands:
                    if isinstance(sub, discord.app_commands.Group):
                        cmd_count += 1
                        cmd_count += len(sub.commands)
                    else:
                        cmd_count += 1
            else:
                cmd_count += 1

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="招待リンク",
                url="https://discord.com/oauth2/authorize?client_id=1322100616369147924&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands",
            )
        )
        view.add_item(
            discord.ui.Button(
                label="サポートサーバー", url="https://discord.gg/mUyByHYMGk"
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Botアイコンの製作者様のサイト", url="https://hiyokoyarou.com/same/"
            )
        )
        em = discord.Embed(title="SharkBotの情報", color=discord.Color.green())
        em.add_field(
            name="サーバー数", value=f"{len(self.bot.guilds)}サーバー"
        ).add_field(name="ユーザー数", value=f"{len(self.bot.users)}人")
        em.add_field(name="サブ管理者", value="3人")
        em.add_field(name="モデレーター", value="8人")
        em.add_field(name="コマンド数", value=f"{cmd_count}個")

        em.set_thumbnail(url=self.bot.user.avatar.url)

        await interaction.followup.send(embeds=[em], view=view)

    @bot.command(name="ping", description="Pingを見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ping_bot(self, interaction: discord.Interaction):
        embed = make_embed.success_embed(
            title=translate.get(
                interaction.extras["lang"], "bot", "Pingを測定しました。"
            ),
            description=f"DiscordAPI: {round(self.bot.latency * 1000)}ms",
        )

        await interaction.response.send_message(embed=embed)

    def create_bar(self, percentage, length=20):
        filled = int(percentage / 100 * length)
        return "⬛" * filled + "⬜" * (length - filled)

    async def get_system_status(self):
        loop = asyncio.get_running_loop()

        cpu_usage = await loop.run_in_executor(None, psutil.cpu_percent, 1)
        memory = await loop.run_in_executor(None, psutil.virtual_memory)
        disk = await loop.run_in_executor(None, psutil.disk_usage, "/")

        return cpu_usage, memory, disk

    async def globalchat_joined_guilds(self):
        db = self.bot.async_db["Main"].NewGlobalChat
        return await db.count_documents({})

    async def globalads_joined_guilds(self):
        db = self.bot.async_db["Main"].NewGlobalAds
        return await db.count_documents({})

    async def sharkaccount_user(self):
        db = self.bot.async_db["Main"].LoginData
        return await db.count_documents({})

    @bot.command(name="debug", description="システム情報を確認します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def debug_bot(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cpu_usage, memory, disk = await self.get_system_status()

        embed = discord.Embed(
            title="サーバーのシステムステータス", color=discord.Color.blue()
        )
        embed.add_field(
            name="CPU 使用率",
            value=f"{cpu_usage}%\n{self.create_bar(cpu_usage)}",
            inline=False,
        )
        memory_usage = memory.percent
        embed.add_field(
            name="メモリ 使用率",
            value=f"{memory.percent}% ({memory.used // (1024**2)}MB / {memory.total // (1024**2)}MB)\n{self.create_bar(memory_usage)}",
            inline=False,
        )
        disk_usage = disk.percent
        embed.add_field(
            name="ディスク 使用率",
            value=f"{disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)\n{self.create_bar(disk_usage)}",
            inline=False,
        )

        globalchat_joined = await self.globalchat_joined_guilds()
        globalads_joined = await self.globalads_joined_guilds()
        embed.add_field(
            name="機能を使用しているサーバー数",
            value=f"""
グローバルチャット: {globalchat_joined}サーバー
グローバル宣伝: {globalads_joined}サーバー
""",
            inline=False,
        )

        sharkaccount_count = await self.sharkaccount_user()
        embed.add_field(
            name="機能を使用しているユーザー数",
            value=f"""
Sharkアカウント: {sharkaccount_count}人
""",
            inline=False,
        )

        await interaction.followup.send(embed=embed)

    @bot.command(name="invite", description="Botの招待リンクを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def invite_bot(self, interaction: discord.Interaction, botのid: discord.User):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            await interaction.response.defer()

            embed = make_embed.success_embed(
                title=f"{botのid}の招待リンクを作成しました。",
                description=f"""# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)
# [🖊️権限を選んで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands)
# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)""",
            )

            await interaction.followup.send(embed=embed)
            return

        await interaction.response.defer()

        gu = interaction.guild.default_role
        mem_kengen = discord.utils.oauth_url(botのid.id, permissions=gu.permissions)

        embed = make_embed.success_embed(
            title=f"{botのid}の招待リンクを作成しました。",
            description=f"""# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)
# [🖊️権限を選んで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands)
# [✅メンバーの権限で招待]({mem_kengen})
# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)""",
        )

        await interaction.followup.send(embed=embed)

    @bot.command(name="faq", description="よくある質問を閲覧します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bot_faq(self, interaction: discord.Interaction):
        embed = make_embed.success_embed(title="よくある質問")

        embed.add_field(name="Botの使い方", value="スラッシュコマンド (/) と、\nコンテキストコマンド (メッセージ/メンバー右クリック -> アプリ)\nで使用できます。", inline=False)
        embed.add_field(name="各種IDのコピーボタンを表示する方法", value="Discord設定 > 詳細 >\n開発者モード > 有効にする", inline=False)

        await interaction.response.send_message(
            embed=embed,
            view=discord.ui.View().add_item(discord.ui.Button(label="サポートサーバー", url="https://discord.com/invite/mUyByHYMGk"))
        )

    @bot.command(name="feedback", description="Botに意見を送信します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bot_feedback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FeedBackModal())

    @bot.command(name="uptime", description="Botの起動した時刻を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bot_uptime(self, interaction: discord.Interaction):
        uptime = self.bot.extensions.get("jishaku").Feature.load_time.timestamp()
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="Botの起動した時刻を取得しました。",
                description=f"<t:{uptime:.0f}:R>",
            )
        )

    @bot.command(name="vote", description="SharkBotに投票する方法を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bot_vote(self, interaction: discord.Interaction):
        await interaction.response.send_message(ephemeral=True, embed=make_embed.success_embed(title="以下から投票できます！", description="24時間に一回投票できます。"), view=discord.ui.View().add_item(discord.ui.Button(label="今すぐ投票する！", url="https://top.gg/ja/bot/1322100616369147924/vote")))

    @bot.command(name="custom", description="Botのアバターなどをカスタマイズします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    async def bot_customize(
        self,
        interaction: discord.Interaction,
        アバター: discord.Attachment = None,
        バナー: discord.Attachment = None,
        名前: str = None,
    ):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        return await interaction.response.send_message(
            ephemeral=True,
            embed=make_embed.error_embed(
                title="現在メンテナンス中です。",
                description="ご迷惑をおかけし申し訳ございません。",
            ),
        )

        await interaction.response.defer()

        async def check_nsfw(image_bytes):
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field(
                    "image",
                    image_bytes,
                    filename="image.jpg",
                    content_type="image/jpeg",
                )

                async with session.post(
                    "http://localhost:3000/analyze", data=data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result
                    else:
                        return {"safe": False}

        raw = self.bot.raw(bot=self.bot)
        if アバター:
            av_io = io.BytesIO(await アバター.read())
            av_check = await check_nsfw(av_io)
            av_check = av_check.get("safe", False)
            if not av_check:
                return await interaction.followup.send(
                    content="不適切なアバターなため、設定できません。"
                )
            avatar = await raw.image_to_data_uri(io_=av_io)
            av_io.close()
        else:
            avatar = None
        if バナー:
            bn_io = io.BytesIO(await バナー.read())
            ba_check = await check_nsfw(bn_io)
            ba_check = ba_check.get("safe", False)
            if not ba_check:
                return await interaction.followup.send(
                    content="不適切なバナーなため、設定できません。"
                )
            banner = await raw.image_to_data_uri(io_=bn_io)
            bn_io.close()
        else:
            banner = None
        try:
            await raw.modify_current_member(
                str(interaction.guild.id), avatarUri=avatar, bannerUri=banner, nick=名前
            )
        except Exception as e:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="レートリミットです。",
                    description=f"何分かお待ちください。\n\nエラーコード\n```{e}```",
                )
            )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="Botのアバターなどをカスタマイズしました。"
            )
        )


async def setup(bot):
    await bot.add_cog(BotCog(bot))
