from discord.ext import commands
import discord
from discord import app_commands

from models import make_embed

from models import command_disable, translate

import asyncio
import psutil

import io
import aiohttp

class BotCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> BotCog")

    bot = app_commands.Group(name="bot", description="Bot系のコマンドです。", allowed_installs=app_commands.AppInstallationType(guild=True, user=True))

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
        embed = make_embed.success_embed(title=translate.get(interaction.extras["lang"], 'bot', 'Pingを測定しました。'), description=f"DiscordAPI: {round(self.bot.latency * 1000)}ms")

        await interaction.response.send_message(
            embed=embed
        )

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

            embed = make_embed.success_embed(title=f"{botのid}の招待リンクを作成しました。", description=f"""# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)
# [🖊️権限を選んで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands)
# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)""")

            await interaction.followup.send(embed=embed)
            return

        await interaction.response.defer()

        gu = interaction.guild.default_role
        mem_kengen = discord.utils.oauth_url(botのid.id, permissions=gu.permissions)

        embed = make_embed.success_embed(title=f"{botのid}の招待リンクを作成しました。", description=f"""# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)
# [🖊️権限を選んで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands)
# [✅メンバーの権限で招待]({mem_kengen})
# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)""")

        await interaction.followup.send(embed=embed)

    @bot.command(name="faq", description="よくある質問を閲覧します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bot_faq(self, interaction: discord.Interaction):
        class FaqLayout(discord.ui.LayoutView):
            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    f"### よくある質問",
                ),
                discord.ui.Separator(),
                discord.ui.TextDisplay(
                    f"例えば、このBotはどんなことができるの？\n・グローバルチャット、グローバル宣伝でサーバー外との交流を深める\n・なんでも検索をする\n・レベル、実績システムの構築\n・様々な画像、動画、音声の作成、加工\n・ルール違反者のモデレーション\nなどなど",
                ),
                discord.ui.Separator(),
                discord.ui.TextDisplay(
                    f"Botはどうやって使うの？\nすべてスラッシュコマンド (/) で使用できます。",
                ),
                discord.ui.Separator(),
                discord.ui.TextDisplay(
                    f"その他の質問をしたいんだけど、どうすればいいの？\n以下のURLのサーバーで質問をすることができます。\nhttps://discord.com/invite/mUyByHYMGk",
                ),
                accent_colour=discord.Colour.green(),
            )

        await interaction.response.send_message(view=FaqLayout())

    @bot.command(name="custom", description="Botのアバターなどをカスタマイズします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    async def bot_customize(self, interaction: discord.Interaction, アバター: discord.Attachment = None, バナー: discord.Attachment = None, 名前: str = None):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(ephemeral=True, embed=make_embed.error_embed(title="このコマンドは使用できません。", description="サーバーにBotをインストールして使用してください。"))

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
            av_check = av_check.get('safe', False)
            if not av_check:
                return await interaction.followup.send(content="不適切なアバターなため、設定できません。")
            avatar = await raw.image_to_data_uri(io_=av_io)
            av_io.close()
        else:
            avatar = None
        if バナー:
            bn_io = io.BytesIO(await バナー.read())
            ba_check = await check_nsfw(bn_io)
            ba_check = ba_check.get('safe', False)
            if not ba_check:
                return await interaction.followup.send(content="不適切なバナーなため、設定できません。")
            banner = await raw.image_to_data_uri(io_=bn_io)
            bn_io.close()
        else:
            banner = None
        try:
            await raw.modify_current_member(str(interaction.guild.id), avatarUri=avatar, bannerUri=banner, nick=名前)
        except Exception as e:
            return await interaction.followup.send(embed=make_embed.error_embed(title="レートリミットです。", description=f"何分かお待ちください。\n\nエラーコード\n```{e}```"))
        await interaction.followup.send(embed=make_embed.success_embed(title="Botのアバターなどをカスタマイズしました。"))

async def setup(bot):
    await bot.add_cog(BotCog(bot))
