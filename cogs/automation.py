import time
from deep_translator import GoogleTranslator
from discord.ext import commands
import discord
from discord import app_commands
import aiohttp
import asyncio

from models import make_embed

cooldown_automation = {}


class AutoMationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AutoMationCog")

    async def run_automation(self, action: str, guild_id: int, ctx: dict):
        db = self.bot.async_db["MainTwo"].AutoMation
        try:
            data = await db.find_one({"Guild": guild_id}, {"_id": False})
        except:
            return

        if not data or not data.get("AutoMations"):
            return

        for rule in data["AutoMations"]:
            if rule.get("Action") != action:
                continue

            act = rule.get("Action")

            if_type = rule.get("If")
            if_value = rule.get("IfValue")
            run = rule.get("Run")
            run_value = rule.get("RunValue")

            message = ctx.get("message")
            content = ctx.get("content")

            if if_type == "in":
                if not content or if_value not in content:
                    continue

            elif if_type == "equal":
                if not content or content != if_value:
                    continue

            elif if_type == "channel":
                channel = ctx.get("channel")
                if not channel or channel.id != if_value:
                    continue

            elif if_type == "emoji":
                emoji = ctx.get("emoji")
                if not emoji or str(emoji) != if_value:
                    continue

            elif if_type == "threadname":
                name = ctx.get("name")
                if not name or name != if_value:
                    continue

            if not ctx.get("author") is None:
                ath = ctx.get("author")
                if isinstance(ath, discord.Member):
                    try:
                        run_value = run_value.replace("{user}", ath.name)
                        run_value = run_value.replace("{user.mention}", ath.mention)
                        run_value = run_value.replace("{user.id}", str(ath.id))
                    except:
                        pass

            if run == "send" and "channel" in ctx:
                current_time = time.time()
                last_message_time = cooldown_automation.get(ctx["channel"].guild.id, 0)
                if current_time - last_message_time < 3:
                    return
                cooldown_automation[ctx["channel"].guild.id] = current_time

                try:
                    await ctx["channel"].send(
                        run_value
                        + "\n-# このメッセージは自動化機能によるメッセージです。"
                    )
                except:
                    pass

            if run == "reply" and "message" in ctx:
                current_time = time.time()
                last_message_time = cooldown_automation.get(ctx["channel"].guild.id, 0)
                if current_time - last_message_time < 3:
                    return
                cooldown_automation[ctx["channel"].guild.id] = current_time

                try:
                    if not ctx["message"] is None:
                        await ctx["message"].reply(
                            run_value
                            + "\n-# このメッセージは自動化機能によるメッセージです。"
                        )
                except:
                    pass

            if run == "delete" and "message" in ctx:
                current_time = time.time()
                last_message_time = cooldown_automation.get(ctx["channel"].guild.id, 0)
                if current_time - last_message_time < 3:
                    return
                cooldown_automation[ctx["channel"].guild.id] = current_time

                try:
                    await ctx["message"].delete()
                except:
                    pass

            if run == "reaction" and "message" in ctx:
                current_time = time.time()
                last_message_time = cooldown_automation.get(ctx["channel"].guild.id, 0)
                if current_time - last_message_time < 3:
                    return
                cooldown_automation[ctx["channel"].guild.id] = current_time

                try:
                    await ctx["message"].add_reaction(run_value)
                except:
                    pass

            if run == "threadcreate" and "channel" in ctx:
                current_time = time.time()
                last_message_time = cooldown_automation.get(ctx["channel"].guild.id, 0)
                if current_time - last_message_time < 3:
                    return
                cooldown_automation[ctx["channel"].guild.id] = current_time

                if act == "send":
                    try:
                        await ctx["message"].create_thread(name=run_value)
                    except:
                        pass
                elif act == "reaction":
                    try:
                        await ctx["message"].create_thread(name=run_value)
                    except:
                        pass
                else:
                    try:
                        await ctx["channel"].create_thread(name=run_value)
                    except:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        await self.run_automation(
            "send",
            message.guild.id,
            {
                "message": message,
                "channel": message.channel,
                "content": message.content,
                "author": message.author,
            },
        )

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild:
            return

        await self.run_automation(
            "delete",
            message.guild.id,
            {
                "message": message,
                "channel": message.channel,
                "content": message.content,
                "author": message.author,
            },
        )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return
        if not reaction.message.guild:
            return

        await self.run_automation(
            "reaction",
            reaction.message.guild.id,
            {
                "message": reaction.message,
                "channel": reaction.message.channel,
                "emoji": str(reaction.emoji),
                "user": user,
                "content": reaction.message.content,
            },
        )

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if not thread.guild:
            return

        await self.run_automation(
            "threadcreate",
            thread.guild.id,
            {
                "thread": thread,
                "channel": thread.parent,
                "name": thread.name,
                "message": thread.starter_message,
            },
        )

    automation = app_commands.Group(
        name="automation",
        description="サーバー内での行動に対して自動的に実行する内容を設定します。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
    )

    @automation.command(name="create", description="自動化ルールを作成します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        アクション=[
            app_commands.Choice(name="メッセージを送信したら", value="send"),
            app_commands.Choice(name="メッセージを削除したら", value="delete"),
            app_commands.Choice(name="リアクションをしたら", value="reaction"),
            app_commands.Choice(name="スレッドを作成したら", value="threadcreate"),
        ]
    )
    @app_commands.choices(
        条件=[
            app_commands.Choice(name="含まれていたら", value="in"),
            app_commands.Choice(name="同じだったら", value="equal"),
            app_commands.Choice(name="チャンネルだったら", value="channel"),
        ]
    )
    @app_commands.choices(
        行動=[
            app_commands.Choice(name="を送信する", value="send"),
            app_commands.Choice(name="を返信する", value="reply"),
            app_commands.Choice(name="メッセージを削除する", value="delete"),
            app_commands.Choice(name="をリアクションする", value="reaction"),
            app_commands.Choice(
                name="という名前のスレッドを作成する", value="threadcreate"
            ),
        ]
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automation_create(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        アクション: app_commands.Choice[str],
        条件: app_commands.Choice[str],
        行動: app_commands.Choice[str],
        条件のチャンネル: discord.TextChannel = None,
        条件のテキストや絵文字: str = None,
        行動のテキストや絵文字: str = None,
    ):
        if 条件.value == "channel":
            if not 条件のチャンネル:
                return await interaction.response.send_message(
                    ephemeral=True, content="条件のチャンネルを指定する必要があります。"
                )
            if_value = 条件のチャンネル.id
            if_value_display = f"<#{if_value}>"
        else:
            if not 条件のテキストや絵文字:
                return await interaction.response.send_message(
                    ephemeral=True,
                    content="条件のテキストや絵文字を指定する必要があります。",
                )
            if_value = 条件のテキストや絵文字
            if_value_display = if_value

        if 行動.value == "delete":
            run_value = None
            run_value_display = "(削除)"
        else:
            run_value = 行動のテキストや絵文字
            run_value_display = run_value

        db = interaction.client.async_db["MainTwo"].AutoMation

        data = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        automations = data.get("AutoMations", []) if data else []

        if len(automations) >= 20:
            return await interaction.response.send_message(
                ephemeral=True, content="自動化は **25個まで** しか作成できません。"
            )

        for a in automations:
            if a.get("Title") == タイトル:
                return await interaction.response.send_message(
                    ephemeral=True,
                    content=f"自動化「{タイトル}」は既に存在します。別の名前を使ってください。",
                )

        await db.update_one(
            {"Guild": interaction.guild.id},
            {
                "$addToSet": {
                    "AutoMations": {
                        "Title": タイトル,
                        "Action": アクション.value,
                        "If": 条件.value,
                        "IfValue": if_value,
                        "Run": 行動.value,
                        "RunValue": run_value,
                    }
                }
            },
            upsert=True,
        )

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"自動化「{タイトル}」を作成しました。",
                description=f"""
**アクション**：{アクション.name}  
**条件**：{if_value_display} が {条件.name}  
**行動**：{run_value_display} を {行動.name}
""",
            )
        )

    @automation.command(name="delete", description="既存の自動化ルールを削除します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automation_delete(self, interaction: discord.Interaction):
        db = interaction.client.async_db["MainTwo"].AutoMation

        data = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        if not data or not data.get("AutoMations"):
            return await interaction.response.send_message(
                ephemeral=True, content="削除できる自動化がありません。"
            )

        automations = data["AutoMations"]

        class AutoDeletionView(discord.ui.View):
            def __init__(self, items):
                super().__init__(timeout=60)
                select = discord.ui.Select(
                    placeholder="削除する自動化を選択してください",
                    min_values=1,
                    max_values=1,
                    options=[
                        discord.SelectOption(
                            label=a.get("Title", "名称なし"),
                            description=f"{a['Action']} / {a['If']} / {a['Run']}",
                        )
                        for a in items
                    ],
                )
                select.callback = self.select_callback
                self.select = select
                self.add_item(select)
                self.value = None

            async def select_callback(self, interaction2: discord.Interaction):
                self.value = self.select.values[0]
                await interaction2.response.defer()
                self.stop()

        view = AutoDeletionView(automations)

        await interaction.response.send_message(
            content="削除する自動化ルールを選んでください：", ephemeral=True, view=view
        )

        await view.wait()

        if view.value is None:
            return

        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$pull": {"AutoMations": {"Title": view.value}}},
        )

        await interaction.followup.send(
            ephemeral=True, content=f"自動化「{view.value}」を削除しました。"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMationCog(bot))
