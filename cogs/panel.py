import asyncio
import random
import string
import time
from discord.ext import commands
import discord
from discord import app_commands

from models import command_disable
import sys
from PIL import Image, ImageDraw, ImageFont
import io


class AuthModal_keisan(discord.ui.Modal, title="認証をする"):
    def __init__(self, role: discord.Role):
        super().__init__()

        a = random.randint(-999, 999)
        self.kekka = str(abs(a))
        self.r = role

        self.name = discord.ui.TextInput(label=f"{a}の絶対値は？")
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.kekka == self.name.value:
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.add_roles(self.r)
                await interaction.followup.send("認証に成功しました。", ephemeral=True)
            except:
                await interaction.followup.send("認証に失敗しました。", ephemeral=True)
        else:
            await interaction.response.send_message(
                "認証に失敗しました。", ephemeral=True
            )


class PlusAuthModal_keisan(discord.ui.Modal, title="認証をする"):
    def __init__(self, role: discord.Role, drole: discord.Role):
        super().__init__()

        a = random.randint(-999, 999)
        self.kekka = str(abs(a))
        self.r = role
        self.dr = drole

        self.name = discord.ui.TextInput(label=f"{a}の絶対値は？")
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.kekka == self.name.value:
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.remove_roles(self.dr)
                await interaction.user.add_roles(self.r)
                await interaction.followup.send("認証に成功しました。", ephemeral=True)
            except:
                await interaction.followup.send("認証に失敗しました。", ephemeral=True)
        else:
            await interaction.response.send_message(
                "認証に失敗しました。", ephemeral=True
            )


tku_cooldown = {}


class AuthGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="auth", description="認証系のコマンドです。")

    @app_commands.command(
        name="abs-auth", description="絶対値を使った認証パネルを作ります。"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_authbutton(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        説明: str,
        ロール: discord.Role,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.channel.send(
            embed=discord.Embed(
                title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()
            ),
            view=discord.ui.View().add_item(
                discord.ui.Button(label="認証", custom_id=f"authpanel_v1+{ロール.id}")
            ),
        )
        await interaction.response.send_message(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @app_commands.command(name="auth", description="ワンクリック認証パネルを作ります。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_authbutton_onclick(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        説明: str,
        ロール: discord.Role,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.channel.send(
            embed=discord.Embed(
                title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()
            ),
            view=discord.ui.View().add_item(
                discord.ui.Button(label="認証", custom_id=f"authpanel_v2+{ロール.id}")
            ),
        )
        await interaction.response.send_message(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @app_commands.command(
        name="auth-plus",
        description="認証したらロールが外れた後にロールが付くパネルを作ります。",
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_authbutton_plus(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        説明: str,
        ロール: discord.Role,
        外すロール: discord.Role,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.channel.send(
            embed=discord.Embed(
                title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()
            ),
            view=discord.ui.View().add_item(
                discord.ui.Button(
                    label="認証",
                    custom_id=f"authpanel_plus_v1+{ロール.id}+{外すロール.id}",
                )
            ),
        )
        await interaction.followup.send(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @app_commands.command(name="webauth", description="Web認証パネルを作ります。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_authboost(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        説明: str,
        ロール: discord.Role,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.channel.send(
            embed=discord.Embed(
                title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()
            ),
            view=discord.ui.View().add_item(
                discord.ui.Button(label="認証", custom_id=f"boostauth+{ロール.id}")
            ),
        )
        await interaction.followup.send(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @app_commands.command(name="image", description="画像認証パネルを作ります。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_imageauth(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        説明: str,
        ロール: discord.Role,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.channel.send(
            embed=discord.Embed(
                title=タイトル, description=説明, color=discord.Color.green()
            ),
            view=discord.ui.View().add_item(
                discord.ui.Button(label="認証", custom_id=f"imageauth+{ロール.id}")
            ),
        )
        await interaction.response.send_message(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @app_commands.command(name="guideline", description="画像認証パネルを作ります。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def paneL_guideline(
        self, interaction: discord.Interaction, ロール: discord.Role
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        class RuleMake(discord.ui.Modal, title="ルールを入力してください。"):
            def __init__(self):
                super().__init__()

                self.rule = discord.ui.TextInput(
                    label="ルール", style=discord.TextStyle.long
                )
                self.add_item(self.rule)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                await interaction.response.defer(thinking=True)
                await interaction.channel.send(
                    embed=discord.Embed(
                        title="このサーバーのルールに同意する必要があります。",
                        description=self.rule.value,
                        color=discord.Color.green(),
                    )
                    .set_thumbnail(url=interaction.client.user.avatar.url)
                    .set_footer(
                        text="Discord コミュニティガイドライン も忘れないようにして下さい。"
                    ),
                    view=discord.ui.View().add_item(
                        discord.ui.Button(
                            label="同意します",
                            custom_id=f"authpanel_v2+{ロール.id}",
                            style=discord.ButtonStyle.green,
                        )
                    ),
                )
                await asyncio.sleep(1)
                await interaction.delete_original_response()

        await interaction.response.send_modal(RuleMake())

    async def message_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        try:
            messages = []
            async for m in interaction.channel.history(limit=50):
                messages.append(m)
            choices = []

            for message in messages:
                if not message.embeds:
                    continue
                if current.lower() in message.embeds[0].title.lower():
                    choices.append(
                        discord.app_commands.Choice(
                            name=message.embeds[0].title[:100], value=str(message.id)
                        )
                    )

                if len(choices) >= 25:
                    break

            return choices
        except:
            return [discord.app_commands.Choice(name="エラーが発生しました", value="0")]

    @app_commands.command(
        name="auth-reqrole", description="認証パネルに必要なロールを設定します。"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @discord.app_commands.autocomplete(認証パネルのid=message_autocomplete)
    async def panel_auth_reqrole(
        self,
        interaction: discord.Interaction,
        認証パネルのid: str,
        必要なロール: discord.Role = None,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            認証パネルのid_ = await interaction.channel.fetch_message(
                int(認証パネルのid)
            )
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="メッセージが見つかりません", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        if 必要なロール:
            db = self.bot.async_db["Main"].AuthReqRole
            await db.replace_one(
                {"Message": 認証パネルのid_.id},
                {"Message": 認証パネルのid_.id, "Role": 必要なロール.id},
                upsert=True,
            )
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="必要なロールを設定しました。", color=discord.Color.green()
                )
            )
        else:
            db = self.bot.async_db["Main"].AuthReqRole
            await db.delete_one({"Message": 認証パネルのid_.id})
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="必要なロールを無効化しました。", color=discord.Color.green()
                )
            )


class PanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> PanelCog")

    async def check_ticket_cat(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].TicketCategory
        try:
            dbfind = await db.find_one(
                {"Message": interaction.message.id}, {"_id": False}
            )
        except:
            return None
        if dbfind is not None:
            return dbfind["Channel"]
        return None

    async def check_ticket_alert(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].TicketAlert
        try:
            dbfind = await db.find_one(
                {"Message": interaction.message.id}, {"_id": False}
            )
        except:
            return None
        if dbfind is not None:
            return self.bot.get_channel(dbfind["Channel"])
        return None

    async def check_guild_bed(self, int_: discord.Interaction):
        db = self.bot.async_db["Main"].RestoreBed
        try:
            dbfind = await db.find_one(
                {"Guild": int_.guild.id, "User": int_.user.id}, {"_id": False}
            )
        except:
            return False
        if dbfind is not None:
            return True
        return False

    async def check_ticket_progress_channel(self, int_: discord.Interaction):
        db = self.bot.async_db["Main"].TicketProgress
        try:
            dbfind = await db.find_one({"Message": int_.message.id}, {"_id": False})
        except:
            return None
        if dbfind is not None:
            try:
                return self.bot.get_channel(dbfind.get("Channel"))
            except:
                return None
        return None

    async def check_ticket_progress_channel_end(self, int_: discord.Interaction):
        db = self.bot.async_db["Main"].TicketProgressTemp
        try:
            dbfind = await db.find_one({"Message": int_.message.id}, {"_id": False})
            await db.delete_many({"Author": dbfind.get("Author")})
        except:
            return None, None
        if dbfind is not None:
            try:
                return self.bot.get_channel(dbfind.get("Channel")), self.bot.get_user(
                    dbfind.get("Author")
                )
            except:
                return None, None
        return None, None

    async def get_ticket_mention(self, message: discord.Message):
        db = self.bot.async_db["Main"].TicketRole
        try:
            dbfind = await db.find_one({"Message": message.id}, {"_id": False})
        except:
            return None
        if dbfind is not None:
            try:
                return message.guild.get_role(dbfind.get("Role")).mention
            except:
                return
        return None

    async def get_auth_reqrole(self, message: discord.Message):
        db = self.bot.async_db["Main"].AuthReqRole
        try:
            dbfind = await db.find_one({"Message": message.id}, {"_id": False})
        except:
            return None
        if dbfind is not None:
            try:
                return message.guild.get_role(dbfind.get("Role"))
            except:
                return None
        return None

    def randstring(self, n):
        randlst = [
            random.choice(string.ascii_letters + string.digits) for i in range(n)
        ]
        return "".join(randlst)

    async def create_authimage(
        self, role: discord.Role, interaction: discord.Interaction
    ):
        img = Image.new(mode="RGB", size=(300, 100), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        bfnt = ImageFont.truetype("data/DiscordFont.ttf", 40)
        text = random.randint(100000, 999999)
        draw.text((20, 20), str(text), "white", font=bfnt)
        tmpio = io.BytesIO()
        img.save(tmpio, format="png")
        tmpio.seek(0)
        try:
            await interaction.user.send(
                file=discord.File(fp=tmpio, filename="auth.png"),
                content="画像に書いてある文字を入力をしてください。",
            )
        except:
            return
        tmpio.close()
        try:
            msg = await self.bot.wait_for(
                "message",
                check=lambda m: m.guild is None and m.author.id == interaction.user.id,
                timeout=30,
            )

            if msg.content == str(text):
                try:
                    await interaction.user.add_roles(interaction.guild.get_role(role))
                    await interaction.followup.send(
                        ephemeral=True,
                        content=f"{interaction.user.mention} 認証が完了しました。",
                    )
                except discord.Forbidden:
                    await interaction.followup.send(
                        "付与したいロールの位置がSharkBotのロールよりも上にあるため付与できませんでした。\n"
                        "https://i.imgur.com/fGcWslT.gif",
                        ephemeral=True,
                    )
            else:
                await interaction.user.send("入力された数字が間違っています。")
        except:
            return await interaction.followup.send(
                content=f"{interaction.user.mention} 認証がタイムアウトしました。",
                ephemeral=True,
            )
        return

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_panel(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if "rolepanel_v1+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if (
                            interaction.guild.get_role(int(custom_id.split("+")[1]))
                            not in interaction.user.roles
                        ):
                            await interaction.user.add_roles(
                                interaction.guild.get_role(int(custom_id.split("+")[1]))
                            )
                            await interaction.followup.send(
                                "ロールを追加しました。", ephemeral=True
                            )
                        else:
                            await interaction.user.remove_roles(
                                interaction.guild.get_role(int(custom_id.split("+")[1]))
                            )
                            await interaction.followup.send(
                                "ロールを剥奪しました。", ephemeral=True
                            )
                    except discord.Forbidden:
                        await interaction.followup.send(
                            "付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif",
                            ephemeral=True,
                        )
                    except:
                        await interaction.followup.send(
                            "追加に失敗しました。", ephemeral=True
                        )
                elif "authpanel_v1+" in custom_id:
                    try:
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if r not in interaction.user.roles:
                                return await interaction.response.send_message(
                                    "あなたは指定されたロールを持っていないため、認証できません。",
                                    ephemeral=True,
                                )
                        if (
                            interaction.guild.get_role(int(custom_id.split("+")[1]))
                            in interaction.user.roles
                        ):
                            return await interaction.response.send_message(
                                "あなたはすでに認証しています。", ephemeral=True
                            )
                        await interaction.response.send_modal(
                            AuthModal_keisan(
                                interaction.guild.get_role(int(custom_id.split("+")[1]))
                            )
                        )
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            "付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif",
                            ephemeral=True,
                        )
                    except:
                        await interaction.response.send_message(
                            "認証に失敗しました。", ephemeral=True
                        )
                elif "authpanel_v2+" in custom_id:
                    try:
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if r not in interaction.user.roles:
                                return await interaction.response.send_message(
                                    "あなたは指定されたロールを持っていないため、認証できません。",
                                    ephemeral=True,
                                )
                        if (
                            interaction.guild.get_role(int(custom_id.split("+")[1]))
                            in interaction.user.roles
                        ):
                            return await interaction.response.send_message(
                                "あなたはすでに認証しています。", ephemeral=True
                            )
                        await interaction.response.defer(ephemeral=True)
                        await interaction.user.add_roles(
                            interaction.guild.get_role(int(custom_id.split("+")[1]))
                        )
                        await interaction.followup.send(
                            "認証が完了しました。", ephemeral=True
                        )
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            "付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif",
                            ephemeral=True,
                        )
                    except:
                        await interaction.response.send_message(
                            "認証に失敗しました。", ephemeral=True
                        )
                elif "imageauth+" in custom_id:
                    try:
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if r not in interaction.user.roles:
                                return await interaction.response.send_message(
                                    "あなたは指定されたロールを持っていないため、認証できません。",
                                    ephemeral=True,
                                )
                        if (
                            interaction.guild.get_role(int(custom_id.split("+")[1]))
                            in interaction.user.roles
                        ):
                            return await interaction.response.send_message(
                                "あなたはすでに認証しています。", ephemeral=True
                            )
                        await interaction.response.defer(ephemeral=True)
                        await interaction.followup.send(
                            "DMをみてください。\nDMに何も届かない場合は、DMを受け取れるか確認してください。",
                            ephemeral=True,
                        )
                        await self.create_authimage(
                            int(custom_id.split("+")[1]), interaction
                        )
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            "付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif",
                            ephemeral=True,
                        )
                    except:
                        await interaction.response.send_message(
                            "認証に失敗しました。", ephemeral=True
                        )
                elif "authpanel_plus_v1+" in custom_id:
                    try:
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if r not in interaction.user.roles:
                                return await interaction.response.send_message(
                                    "あなたは指定されたロールを持っていないため、認証できません。",
                                    ephemeral=True,
                                )
                        if (
                            interaction.guild.get_role(int(custom_id.split("+")[1]))
                            in interaction.user.roles
                        ):
                            return await interaction.response.send_message(
                                "あなたはすでに認証しています。", ephemeral=True
                            )
                        await interaction.response.send_modal(
                            PlusAuthModal_keisan(
                                interaction.guild.get_role(
                                    int(custom_id.split("+")[1])
                                ),
                                interaction.guild.get_role(
                                    int(custom_id.split("+")[2])
                                ),
                            )
                        )
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            "付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif",
                            ephemeral=True,
                        )
                    except:
                        await interaction.response.send_message(
                            f"認証に失敗しました。\n{sys.exc_info()}", ephemeral=True
                        )
                elif "poll+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        des = interaction.message.embeds[0].description.split("\n")
                        text = ""
                        for d in des:
                            if d.split(": ")[0] == custom_id.split("+")[1]:
                                ct = int(d.split(": ")[1]) + 1
                                text += f"{d.split(': ')[0]}: {ct}\n"
                                continue
                            text += f"{d}\n"
                        await interaction.message.edit(
                            embed=discord.Embed(
                                title=f"{interaction.message.embeds[0].title}",
                                description=f"{text}",
                                color=discord.Color.green(),
                            )
                        )
                        await interaction.followup.send(
                            content="投票しました。", ephemeral=True
                        )
                    except:
                        await interaction.followup.send(
                            f"投票に失敗しました。\n{sys.exc_info()}", ephemeral=True
                        )
                elif "poll_done" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if custom_id.split("+")[1] == f"{interaction.user.id}":
                            await interaction.message.edit(view=None)
                            await interaction.followup.send(
                                content="集計しました。", ephemeral=True
                            )
                        else:
                            await interaction.followup.send(
                                content="権限がありません。", ephemeral=True
                            )
                    except:
                        await interaction.followup.send(
                            f"集計に失敗しました。\n{sys.exc_info()}", ephemeral=True
                        )
                elif "ticket_v1" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        overwrites = {
                            interaction.guild.default_role: discord.PermissionOverwrite(
                                read_messages=False
                            ),
                            interaction.guild.me: discord.PermissionOverwrite(
                                read_messages=True
                            ),
                            interaction.user: discord.PermissionOverwrite(
                                read_messages=True, send_messages=True
                            ),
                        }
                        check_c = await self.check_ticket_cat(interaction)
                        current_time = time.time()
                        last_message_time = tku_cooldown.get(interaction.user.id, 0)
                        if current_time - last_message_time < 30:
                            return await interaction.followup.send(
                                "レートリミットです。", ephemeral=True
                            )
                        tku_cooldown[interaction.user.id] = current_time
                        db_progress = self.bot.async_db["Main"].TicketProgressTemp
                        ch = await self.check_ticket_progress_channel(interaction)
                        role_ment = await self.get_ticket_mention(interaction.message)
                        if not check_c:
                            if interaction.channel.category:
                                tkc = await interaction.channel.category.create_text_channel(
                                    name=f"{interaction.user.name}-ticket",
                                    overwrites=overwrites,
                                )
                                view = discord.ui.View()
                                view.add_item(
                                    discord.ui.Button(
                                        label="削除",
                                        custom_id="delete_ticket",
                                        style=discord.ButtonStyle.red,
                                    )
                                )
                                view.add_item(
                                    discord.ui.Button(
                                        label="閉じる",
                                        custom_id="close_ticket",
                                        style=discord.ButtonStyle.red,
                                    )
                                )
                                msg = await tkc.send(
                                    embed=discord.Embed(
                                        title=f"`{interaction.user.name}`のチケット",
                                        color=discord.Color.green(),
                                    ),
                                    view=view,
                                    content=role_ment
                                    if role_ment
                                    else f"{interaction.user.mention}",
                                )
                                if ch:
                                    await db_progress.replace_one(
                                        {
                                            "Channel": ch.id,
                                            "Message": msg.id,
                                            "Author": interaction.user.id,
                                        },
                                        {
                                            "Channel": ch.id,
                                            "Message": msg.id,
                                            "Author": interaction.user.id,
                                        },
                                        upsert=True,
                                    )
                                await interaction.followup.send(
                                    f"チケットを作成しました。\n{tkc.jump_url}",
                                    ephemeral=True,
                                )
                            else:
                                tkc = await interaction.guild.create_text_channel(
                                    name=f"{interaction.user.name}-ticket",
                                    overwrites=overwrites,
                                )
                                view = discord.ui.View()
                                view.add_item(
                                    discord.ui.Button(
                                        label="削除",
                                        custom_id="delete_ticket",
                                        style=discord.ButtonStyle.red,
                                    )
                                )
                                view.add_item(
                                    discord.ui.Button(
                                        label="閉じる",
                                        custom_id="close_ticket",
                                        style=discord.ButtonStyle.red,
                                    )
                                )
                                msg = await tkc.send(
                                    embed=discord.Embed(
                                        title=f"`{interaction.user.name}`のチケット",
                                        color=discord.Color.green(),
                                    ),
                                    view=view,
                                    content=role_ment
                                    if role_ment
                                    else f"{interaction.user.mention}",
                                )
                                if ch:
                                    await db_progress.replace_one(
                                        {
                                            "Channel": ch.id,
                                            "Message": msg.id,
                                            "Author": interaction.user.id,
                                        },
                                        {
                                            "Channel": ch.id,
                                            "Message": msg.id,
                                            "Author": interaction.user.id,
                                        },
                                        upsert=True,
                                    )
                                await interaction.followup.send(
                                    f"チケットを作成しました。\n{tkc.jump_url}",
                                    ephemeral=True,
                                )
                        else:
                            if self.bot.get_channel(check_c):
                                tkc = await self.bot.get_channel(
                                    check_c
                                ).create_text_channel(
                                    name=f"{interaction.user.name}-ticket",
                                    overwrites=overwrites,
                                )
                                view = discord.ui.View()
                                view.add_item(
                                    discord.ui.Button(
                                        label="削除",
                                        custom_id="delete_ticket",
                                        style=discord.ButtonStyle.red,
                                    )
                                )
                                view.add_item(
                                    discord.ui.Button(
                                        label="閉じる",
                                        custom_id="close_ticket",
                                        style=discord.ButtonStyle.red,
                                    )
                                )
                                msg = await tkc.send(
                                    embed=discord.Embed(
                                        title=f"`{interaction.user.name}`のチケット",
                                        color=discord.Color.green(),
                                    ),
                                    view=view,
                                    content=role_ment
                                    if role_ment
                                    else f"{interaction.user.mention}",
                                )
                                if ch:
                                    await db_progress.replace_one(
                                        {
                                            "Channel": ch.id,
                                            "Message": msg.id,
                                            "Author": interaction.user.id,
                                        },
                                        {
                                            "Channel": ch.id,
                                            "Message": msg.id,
                                            "Author": interaction.user.id,
                                        },
                                        upsert=True,
                                    )
                                await interaction.followup.send(
                                    f"チケットを作成しました。\n{tkc.jump_url}",
                                    ephemeral=True,
                                )
                            else:
                                await interaction.followup.send(
                                    "エラーが発生しました。\n指定されたカテゴリが見つかりません。",
                                    ephemeral=True,
                                )
                    except discord.Forbidden:
                        await interaction.followup.send(
                            f"チケット作成に必要な権限がありません。\n再度権限を確認してください。",
                            ephemeral=True,
                        )
                    except:
                        await interaction.followup.send(
                            f"チケット作成に失敗しました。\n{sys.exc_info()}",
                            ephemeral=True,
                        )
                elif "delete_ticket" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        ch, user = await self.check_ticket_progress_channel_end(
                            interaction
                        )
                        try:
                            h = []
                            async for his in interaction.channel.history(
                                limit=100, oldest_first=True
                            ):
                                h.append(
                                    "{}: {}".format(
                                        his.author.name,
                                        his.content.replace("\n", "\\n"),
                                    )
                                )
                            kaiwa_io = io.StringIO("\n".join(h))
                            if not user:
                                await ch.send(
                                    embed=discord.Embed(
                                        title="チケットの実績が記録されました",
                                        color=discord.Color.green(),
                                    )
                                    .add_field(name="チケットを開いた人", value="不明")
                                    .set_thumbnail(
                                        url=self.bot.user.default_avatar.url
                                    ),
                                    file=discord.File(kaiwa_io, "hist.txt"),
                                )
                            else:
                                await ch.send(
                                    embed=discord.Embed(
                                        title="チケットの実績が記録されました",
                                        color=discord.Color.green(),
                                    )
                                    .add_field(
                                        name="チケットを開いた人",
                                        value=f"{user.mention}\n({user.id})",
                                    )
                                    .set_thumbnail(
                                        url=user.avatar.url
                                        if user.avatar
                                        else user.default_avatar.url
                                    ),
                                    file=discord.File(kaiwa_io, "hist.txt"),
                                )
                            kaiwa_io.close()
                        except:
                            pass
                        await interaction.channel.delete()
                    except discord.Forbidden:
                        await interaction.followup.send(
                            f"チケット削除に必要な権限がありません。\n再度権限を確認してください。",
                            ephemeral=True,
                        )
                    except:
                        await interaction.followup.send(
                            f"チケット削除に失敗しました。\n{sys.exc_info()}",
                            ephemeral=True,
                        )
                elif "close_ticket" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        overwrites = {
                            interaction.guild.default_role: discord.PermissionOverwrite(
                                read_messages=False
                            ),
                            interaction.guild.me: discord.PermissionOverwrite(
                                read_messages=True
                            ),
                            interaction.user: discord.PermissionOverwrite(
                                read_messages=False, send_messages=False
                            ),
                        }

                        ch, user = await self.check_ticket_progress_channel_end(
                            interaction
                        )
                        try:
                            h = []
                            async for his in interaction.channel.history(
                                limit=100, oldest_first=True
                            ):
                                h.append(
                                    "{}: {}".format(
                                        his.author.name,
                                        his.content.replace("\n", "\\n"),
                                    )
                                )
                            kaiwa_io = io.StringIO("\n".join(h))
                            if not user:
                                await ch.send(
                                    embed=discord.Embed(
                                        title="チケットの実績が記録されました",
                                        color=discord.Color.green(),
                                    )
                                    .add_field(name="チケットを開いた人", value="不明")
                                    .set_thumbnail(
                                        url=self.bot.user.default_avatar.url
                                    ),
                                    file=discord.File(kaiwa_io, "hist.txt"),
                                )
                            else:
                                await ch.send(
                                    embed=discord.Embed(
                                        title="チケットの実績が記録されました",
                                        color=discord.Color.green(),
                                    )
                                    .add_field(
                                        name="チケットを開いた人",
                                        value=f"{user.mention}\n({user.id})",
                                    )
                                    .set_thumbnail(
                                        url=user.avatar.url
                                        if user.avatar
                                        else user.default_avatar.url
                                    ),
                                    file=discord.File(kaiwa_io, "hist.txt"),
                                )
                            kaiwa_io.close()
                        except:
                            pass
                        await interaction.channel.edit(
                            overwrites=overwrites,
                            name=interaction.channel.name.replace("ticket", "close"),
                        )
                        await interaction.channel.send(
                            embed=discord.Embed(
                                title="チケットが閉じられました。",
                                color=discord.Color.red(),
                            )
                        )
                        view = discord.ui.View()
                        view.add_item(
                            discord.ui.Button(
                                label="削除",
                                custom_id="delete_ticket",
                                style=discord.ButtonStyle.red,
                            )
                        )
                        await interaction.message.edit(view=view)
                    except:
                        await interaction.followup.send(
                            f"チケットクローズに失敗しました。\n{sys.exc_info()}",
                            ephemeral=True,
                        )
                elif "boostauth+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        r = await self.get_auth_reqrole(interaction.message)
                        if r:
                            if r not in interaction.user.roles:
                                return await interaction.followup.send(
                                    "あなたは指定されたロールを持っていないため、認証できません。",
                                    ephemeral=True,
                                )
                        role = custom_id.split("+")[1]
                        code = self.randstring(30)
                        db = self.bot.async_db["Main"].MemberAddAuthRole
                        await db.replace_one(
                            {"Guild": str(interaction.guild.id), "Code": code},
                            {
                                "Guild": str(interaction.guild.id),
                                "Code": code,
                                "Role": role,
                            },
                            upsert=True,
                        )
                        await interaction.followup.send(
                            "この認証パネルは、Webにアクセスする必要があります。\n以下のボタンからアクセスして認証してください。\n\n追記: あなたの参加しているサーバーが取得されます。\nそれらの情報は、Botの動作向上のために使用されます。",
                            ephemeral=True,
                            view=discord.ui.View().add_item(
                                discord.ui.Button(
                                    label="認証する",
                                    url=f"https://discord.com/oauth2/authorize?client_id=1322100616369147924&response_type=code&redirect_uri=https%3A%2F%2Fwww.sharkbot.xyz%2Finvite_auth&scope=identify+guilds+connections&state={code}",
                                )
                            ),
                        )
                    except:
                        await interaction.followup.send(
                            f"認証に失敗しました。\n{sys.exc_info()}",
                            ephemeral=True,
                        )
                elif "postauth+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        role = custom_id.split("+")[1]
                        code = self.randstring(30)
                        db = self.bot.async_db["Main"].PostAuth
                        await db.replace_one(
                            {"Guild": str(interaction.guild.id), "Code": code},
                            {
                                "Guild": str(interaction.guild.id),
                                "Code": code,
                                "Role": role,
                                "User": str(interaction.user.id),
                            },
                            upsert=True,
                        )
                        await interaction.followup.send(
                            "認証をするには、\n```{'code': 'code_', 'guild': 'guild_'}```\nを`https://www.sharkbot.xyz/postauth`\nにPostしてください。".replace(
                                "code_", code
                            ).replace("guild_", str(interaction.guild.id)),
                            ephemeral=True,
                        )
                    except:
                        await interaction.followup.send(
                            f"認証に失敗しました。\n{sys.exc_info()}", ephemeral=True
                        )
                elif "obj_ok+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        gid = custom_id.split("+")[1]
                        uid = custom_id.split("+")[2]
                        guild = self.bot.get_guild(int(gid))
                        db = self.bot.async_db["Main"].ObjReq
                        await db.delete_one({"Guild": guild.id, "User": int(uid)})
                        await self.bot.get_user(int(uid)).send(
                            f"「{guild.name}」の異議申し立てが受諾されました。"
                        )
                        await interaction.followup.send(
                            ephemeral=True, content="異議申し立てに返信しました。"
                        )
                    except:
                        await interaction.followup.send(
                            f"異議申し立てに失敗しました。\n{sys.exc_info()}",
                            ephemeral=True,
                        )
                elif "obj_no+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        gid = custom_id.split("+")[1]
                        uid = custom_id.split("+")[2]
                        guild = self.bot.get_guild(int(gid))
                        db = self.bot.async_db["Main"].ObjReq
                        await db.delete_one({"Guild": guild.id, "User": int(uid)})
                        await self.bot.get_user(int(uid)).send(
                            f"「{guild.name}」の異議申し立てが拒否されました。"
                        )
                        await interaction.followup.send(
                            ephemeral=True, content="異議申し立てに返信しました。"
                        )
                    except:
                        await interaction.followup.send(
                            f"異議申し立てに失敗しました。\n{sys.exc_info()}",
                            ephemeral=True,
                        )
                elif "botban+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        type_ = interaction.message.embeds[0].fields[0].value
                        if type_ == "ユーザー":
                            target = self.bot.get_user(
                                int(interaction.message.embeds[0].footer.text)
                            )
                            db = self.bot.async_db["Main"].BlockUser
                            await db.replace_one(
                                {"User": target.id}, {"User": target.id}, upsert=True
                            )
                        elif type_ == "サーバー":
                            target = self.bot.get_guild(
                                int(interaction.message.embeds[0].footer.text)
                            )
                            db = self.bot.async_db["Main"].BlockGuild
                            await db.replace_one(
                                {"Guild": target.id}, {"Guild": target.id}, upsert=True
                            )
                        await interaction.message.reply("BotからBANしました。")
                        await interaction.followup.send(
                            ephemeral=True,
                            content=f"BotからBANしました。\nID: {target.id}\nタイプ: {type_}",
                        )
                    except:
                        await interaction.followup.send(
                            "BotからのBANに失敗しました。", ephemeral=True
                        )
                elif "botwarn+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        type_ = interaction.message.embeds[0].fields[0].value
                        if type_ == "ユーザー":
                            target = self.bot.get_user(
                                int(interaction.message.embeds[0].footer.text)
                            )
                            reason = interaction.message.embeds[0].fields[2].value
                            await target.send(
                                embed=discord.Embed(
                                    title="SharkBotからあなたは警告されました。",
                                    color=discord.Color.yellow(),
                                ).add_field(name="理由", value=reason)
                            )
                        elif type_ == "サーバー":
                            target = self.bot.get_guild(
                                int(interaction.message.embeds[0].footer.text)
                            )
                            reason = interaction.message.embeds[0].fields[2].value
                            await target.owner.send(
                                embed=discord.Embed(
                                    title="SharkBotからあなたは警告されました。",
                                    color=discord.Color.yellow(),
                                ).add_field(name="理由", value=reason)
                            )
                        await interaction.message.reply("警告しました。")
                        await interaction.followup.send(
                            ephemeral=True,
                            content=f"Botから警告しました。\nID: {target.id}\nタイプ: {type_}",
                        )
                    except:
                        await interaction.followup.send(
                            "Botからの警告に失敗しました。", ephemeral=True
                        )
                elif "botdelete+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        await interaction.message.edit(view=None)
                        await interaction.message.reply("破棄しました。")
                        await interaction.followup.send(
                            ephemeral=True, content="破棄しました。"
                        )
                    except:
                        await interaction.followup.send(
                            "破棄に失敗しました。", ephemeral=True
                        )
                elif "join_party+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if (
                            f"{interaction.user.id}"
                            in interaction.message.embeds[0].fields[3].value
                        ):
                            return
                        max_memb = int(
                            interaction.message.embeds[0]
                            .fields[1]
                            .value.replace("人", "")
                        )
                        memb = int(
                            interaction.message.embeds[0]
                            .fields[2]
                            .value.replace("人", "")
                        )
                        emb = interaction.message.embeds[0].copy()
                        emb.set_field_at(
                            2, name="現在の参加人数", value=f"{memb + 1}人", inline=True
                        )
                        if (
                            interaction.message.embeds[0].fields[3].value
                            == "まだいません。"
                        ):
                            emb.set_field_at(
                                3,
                                name="参加者",
                                value=f"{interaction.user.display_name} ({interaction.user.id})",
                                inline=False,
                            )
                        else:
                            emb.set_field_at(
                                3,
                                name="参加者",
                                value=f"{interaction.message.embeds[0].fields[3].value}\n{interaction.user.display_name} ({interaction.user.id})",
                                inline=False,
                            )
                        if (
                            int(
                                interaction.message.embeds[0]
                                .fields[2]
                                .value.replace("人", "")
                            )
                            == max_memb
                        ):
                            await interaction.message.edit(
                                embeds=[
                                    emb,
                                    discord.Embed(
                                        title="募集が完了しました。",
                                        color=discord.Color.red(),
                                    ),
                                ],
                                view=None,
                            )
                        else:
                            await interaction.message.edit(embed=emb)
                        await interaction.followup.send(
                            ephemeral=True, content="参加しました。"
                        )
                    except Exception as e:
                        await interaction.message.edit(
                            embed=discord.Embed(
                                title="エラーが発生したため、強制終了しました。",
                                color=discord.Color.red(),
                            )
                        )
                        await interaction.followup.send(
                            f"参加に失敗しました。\nエラーコード: {e}", ephemeral=True
                        )
                elif "viproom+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        role = custom_id.split("+")[1]
                        if not self.bot.get_guild(1343124570131009579).get_member(
                            interaction.user.id
                        ):
                            return await interaction.followup.send(
                                ephemeral=True,
                                content="VIPルームに参加する権限がありません。\nSharkBotサポートサーバーに参加して下さい。",
                            )
                        if (
                            self.bot.get_guild(1343124570131009579).get_role(
                                1359843498395959437
                            )
                            in self.bot.get_guild(1343124570131009579)
                            .get_member(interaction.user.id)
                            .roles
                        ):
                            await interaction.user.add_roles(
                                interaction.guild.get_role(int(role))
                            )
                        else:
                            return await interaction.followup.send(
                                ephemeral=True,
                                content="VIPルームに参加する権限がありません。\nVIPルーム権限を購入して下さい。",
                            )
                        await interaction.followup.send(
                            ephemeral=True, content="VIPルームに参加しました。"
                        )
                    except:
                        await interaction.followup.send(
                            "VIPルームに参加できませんでした。", ephemeral=True
                        )
                elif "enquete_answer+" in custom_id:
                    embed = interaction.message.embeds[0].fields
                    class Modal_Qneuete(discord.ui.Modal):
                        def __init__(self, embed_fields, message: discord.Message):
                            super().__init__(title="アンケートに回答する", timeout=180)
                            self.message = message

                            for e in embed_fields[:5]:
                                self.add_item(
                                    discord.ui.TextInput(
                                        label=e.name,
                                        placeholder=f"{e.name}について回答してください",
                                        style=discord.TextStyle.short,
                                        required=True,
                                        max_length=30
                                    )
                                )

                        async def on_submit(self, interaction: discord.Interaction):
                            embed = self.message.embeds[0]
                            new_embed = discord.Embed(title=embed.title, color=embed.color)
                            new_embed.set_footer(text="SharkBot Enquete")

                            for i, field in enumerate(embed.fields):
                                if i < len(self.children):
                                    answer = self.children[i].value
                                    user = interaction.user.name

                                    old_value = "" if field.value == "未回答" else field.value

                                    new_value = f"{old_value}\n{user}: {answer}" if old_value else f"{user}: {answer}"

                                    new_embed.add_field(name=field.name, value=new_value, inline=False)
                                else:
                                    new_embed.add_field(name=field.name, value=field.value, inline=False)

                            await self.message.edit(embed=new_embed)
                            await interaction.response.send_message("回答を記録しました", ephemeral=True)
                    await interaction.response.send_modal(Modal_Qneuete(embed, interaction.message))
                elif "templates_answer+" in custom_id:
                    embed_fields = interaction.message.embeds[0].fields

                    class Modal_Qneuete(discord.ui.Modal):
                        def __init__(self, embed_fields, message: discord.Message):
                            super().__init__(title=f"{message.embeds[0].title}", timeout=180)
                            self.message = message
                            self.embed_fields = embed_fields

                            for e in embed_fields[:5]:
                                self.add_item(
                                    discord.ui.TextInput(
                                        label=e.value,
                                        placeholder=f"{e.value}について回答してください",
                                        style=discord.TextStyle.short,
                                        required=True,
                                        max_length=30
                                    )
                                )

                        async def on_submit(self, interaction: discord.Interaction):
                            answer_embed = discord.Embed(color=discord.Color.blue())
                            for i, field in enumerate(self.embed_fields[:len(self.children)]):
                                answer = self.children[i].value
                                answer_embed.add_field(name=field.value, value=answer, inline=False)

                            answer_embed.set_author(
                                name=f"{interaction.user.name} / {interaction.user.id}",
                                icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
                            )

                            await interaction.channel.send(embed=answer_embed)

                            question_embed = discord.Embed(
                                title=self.message.embeds[0].title,
                                color=discord.Color.green()
                            )
                            for i, q in enumerate(self.embed_fields):
                                question_embed.add_field(name=f"Q.{i+1}", value=q.value, inline=False)

                            question_embed.set_footer(text="SharkBot Templates")

                            view = discord.ui.View()
                            view.add_item(discord.ui.Button(label="発言する", custom_id="templates_answer+"))

                            await interaction.channel.send(embed=question_embed, view=view)

                            await interaction.response.send_message("回答を送信しました", ephemeral=True)

                            await asyncio.sleep(2)

                            await interaction.message.delete()

                    await interaction.response.send_modal(Modal_Qneuete(embed_fields, interaction.message))

                elif "globalchat_agree+" in custom_id:
                    db = self.bot.async_db["Main"].GlobalChatRuleAgreeUser
                    await db.replace_one(
                        {"User": interaction.user.id},
                        {
                            "User": interaction.user.id,
                            "UserName": interaction.user.name
                        },
                        upsert=True,
                    )
                    await interaction.response.send_message(ephemeral=True, content="グローバルチャットのルールに同意しました。")
        except:
            return

    panel = app_commands.Group(name="panel", description="パネル系のコマンドです。")

    panel.add_command(AuthGroup())

    @panel.command(name="role", description="ロールパネルを作成します。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_role(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        説明: str,
        メンションを表示するか: bool,
        ロール1: discord.Role,
        ロール2: discord.Role = None,
        ロール3: discord.Role = None,
        ロール4: discord.Role = None,
        ロール5: discord.Role = None,
        ロール6: discord.Role = None,
        ロール7: discord.Role = None,
        ロール8: discord.Role = None,
        ロール9: discord.Role = None,
        ロール10: discord.Role = None,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        view = discord.ui.View()
        ls = []
        view.add_item(
            discord.ui.Button(
                label=f"{ロール1.name}", custom_id=f"rolepanel_v1+{ロール1.id}"
            )
        )
        ls.append(f"{ロール1.mention}")
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール2.name}", custom_id=f"rolepanel_v1+{ロール2.id}"
                )
            )
            ls.append(f"{ロール2.mention}")
        except:
            pass
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール3.name}", custom_id=f"rolepanel_v1+{ロール3.id}"
                )
            )
            ls.append(f"{ロール3.mention}")
        except:
            pass
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール4.name}", custom_id=f"rolepanel_v1+{ロール4.id}"
                )
            )
            ls.append(f"{ロール4.mention}")
        except:
            pass
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール5.name}", custom_id=f"rolepanel_v1+{ロール5.id}"
                )
            )
            ls.append(f"{ロール5.mention}")
        except:
            pass
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール6.name}", custom_id=f"rolepanel_v1+{ロール6.id}"
                )
            )
            ls.append(f"{ロール6.mention}")
        except:
            pass
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール7.name}", custom_id=f"rolepanel_v1+{ロール7.id}"
                )
            )
            ls.append(f"{ロール7.mention}")
        except:
            pass
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール8.name}", custom_id=f"rolepanel_v1+{ロール8.id}"
                )
            )
            ls.append(f"{ロール8.mention}")
        except:
            pass
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール9.name}", custom_id=f"rolepanel_v1+{ロール9.id}"
                )
            )
            ls.append(f"{ロール9.mention}")
        except:
            pass
        try:
            view.add_item(
                discord.ui.Button(
                    label=f"{ロール10.name}", custom_id=f"rolepanel_v1+{ロール10.id}"
                )
            )
            ls.append(f"{ロール10.mention}")
        except:
            pass
        embed = discord.Embed(
            title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()
        )
        if メンションを表示するか:
            embed.add_field(name="ロール一覧", value="\n".join(ls))
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    async def message_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        try:
            choices = []

            async for message in interaction.channel.history(limit=50):
                if not message.embeds:
                    continue

                embed = message.embeds[0]
                if not embed.title:
                    continue

                if current.lower() in embed.title.lower():
                    choices.append(
                        app_commands.Choice(
                            name=embed.title[:100], value=str(message.id)
                        )
                    )

                if len(choices) >= 25:
                    break

            return choices
        except:
            return [discord.app_commands.Choice(name="エラーが発生しました", value="0")]

    @panel.command(name="role-edit", description="ロールパネルを編集します。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @discord.app_commands.autocomplete(ロールパネルのid=message_autocomplete)
    @discord.app_commands.choices(
        削除か追加か=[
            discord.app_commands.Choice(name="追加", value="add"),
            discord.app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def panel_rolepanel_edit(
        self,
        interaction: discord.Interaction,
        ロールパネルのid: str,
        ロール: discord.Role,
        削除か追加か: discord.app_commands.Choice[str],
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer(ephemeral=True)
        try:
            ロールパネルのid_ = await interaction.channel.fetch_message(
                int(ロールパネルのid)
            )
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="メッセージが見つかりません", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        view = discord.ui.View()
        for action_row in ロールパネルのid_.components:
            for v in action_row.children:
                if isinstance(v, discord.Button):
                    view.add_item(
                        discord.ui.Button(label=v.label, custom_id=v.custom_id)
                    )

        if 削除か追加か.name == "追加":
            view.add_item(
                discord.ui.Button(
                    label=ロール.name, custom_id=f"rolepanel_v1+{ロール.id}"
                )
            )

        else:
            view = discord.ui.View()
            for action_row in ロールパネルのid_.components:
                for v in action_row.children:
                    if isinstance(v, discord.Button):
                        if not v.label == ロール.name:
                            view.add_item(
                                discord.ui.Button(label=v.label, custom_id=v.custom_id)
                            )
        embed = ロールパネルのid_.embeds[0]

        if embed.fields:
            field_value = embed.fields[0].value or ""

            if 削除か追加か.name == "追加":
                field_value += f"\n{ロール.mention}"
            elif 削除か追加か.name == "削除":
                field_value = (
                    field_value.replace(f"\n{ロール.mention}", "")
                    .replace(f"{ロール.mention}\n", "")
                    .replace(f"{ロール.mention}", "")
                )

            new_embed = embed.copy()
            new_embed.set_field_at(
                0,
                name=embed.fields[0].name,
                value=field_value,
                inline=embed.fields[0].inline,
            )

            await ロールパネルのid_.edit(view=view, embeds=[new_embed])

            await interaction.followup.send(
                embed=discord.Embed(
                    title="編集しました。", color=discord.Color.green()
                ),
                ephemeral=True,
            )
            return
        else:
            pass
        await ロールパネルのid_.edit(view=view)
        await interaction.followup.send(
            embed=discord.Embed(title="編集しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @panel.command(
        description="新しいGUIのロールパネルを作成します。", name="newgui-rolepanel"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_newgui_rolepanel(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        ロール1: discord.Role,
        ロール2: discord.Role = None,
        ロール3: discord.Role = None,
        ロール4: discord.Role = None,
        ロール5: discord.Role = None,
        説明: str = None,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        cont = self.bot.container(self.bot)
        cont.add_view(cont.text(f"# {タイトル}"))
        if 説明:
            cont.add_view(cont.text(f"{説明}"))
        b1 = cont.labeled_customid_button(
            button_label="取得", custom_id=f"rolepanel_v1+{ロール1.id}", style=1
        )
        cont.add_view(cont.labeled_button(f"{ロール1.name} ({ロール1.id})", b1))
        if ロール2:
            b2 = cont.labeled_customid_button(
                button_label="取得", custom_id=f"rolepanel_v1+{ロール2.id}", style=1
            )
            cont.add_view(cont.labeled_button(f"{ロール2.name} ({ロール2.id})", b2))
        if ロール3:
            b3 = cont.labeled_customid_button(
                button_label="取得", custom_id=f"rolepanel_v1+{ロール3.id}", style=1
            )
            cont.add_view(cont.labeled_button(f"{ロール3.name} ({ロール3.id})", b3))
        if ロール4:
            b4 = cont.labeled_customid_button(
                button_label="取得", custom_id=f"rolepanel_v1+{ロール4.id}", style=1
            )
            cont.add_view(cont.labeled_button(f"{ロール4.name} ({ロール4.id})", b4))
        if ロール5:
            b5 = cont.labeled_customid_button(
                button_label="取得", custom_id=f"rolepanel_v1+{ロール5.id}", style=1
            )
            cont.add_view(cont.labeled_button(f"{ロール5.name} ({ロール5.id})", b5))
        await cont.send(0, interaction.channel.id)
        await interaction.delete_original_response()

    @panel.command(
        name="newgui-rolepanel-edit",
        description="新しいGuiのロールパネルを編集します。",
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @discord.app_commands.choices(
        削除か追加か=[
            discord.app_commands.Choice(name="追加", value="add"),
            discord.app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def panel_new_gui_rolepanel_edit(
        self,
        interaction: discord.Interaction,
        メッセージ: str,
        ロール: discord.Role,
        削除か追加か: discord.app_commands.Choice[str],
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()

        try:
            メッセージ = await interaction.channel.fetch_message(int(メッセージ))
        except:
            await interaction.delete_original_response()
            return

        cont = self.bot.container(self.bot)
        con = await cont.fetch(メッセージ, interaction.channel.id)
        cont.comp = con[0].get("components", [])
        if 削除か追加か.name == "デバッグ":
            if not interaction.user.id == 1335428061541437531:
                return await interaction.followup.send("オーナーのみ実行可能です。")
            await interaction.followup.send(f"{cont.comp}")
        elif 削除か追加か.name == "追加":
            b1 = cont.labeled_customid_button(
                button_label="取得", custom_id=f"rolepanel_v1+{ロール.id}", style=1
            )
            cont.add_view(cont.labeled_button(f"{ロール.name} ({ロール.id})", b1))
            await cont.edit(メッセージ, interaction.channel.id)
        elif 削除か追加か.name == "削除":
            ls = []
            b1 = cont.labeled_customid_button(
                button_label="取得", custom_id=f"rolepanel_v1+{ロール.id}", style=1
            )
            for c in cont.comp:
                if c.get("components", {}) == {}:
                    ls.append(c)
                    continue
                if c.get("type", 0) == 9:
                    if (
                        c.get("components", {})[0].get("content", None)
                        == f"{ロール.name} ({ロール.id})"
                    ):
                        continue
                    ls.append(c)
            cont.comp = ls
            await cont.edit(メッセージ, interaction.channel.id)

        await interaction.delete_original_response()

    @panel.command(
        name="select-rolepanel",
        description="セレクト式ロールパネルを作成します。現在は編集不可です。",
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_select_role(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        ロール1: discord.Role,
        ロール2: discord.Role = None,
        ロール3: discord.Role = None,
        ロール4: discord.Role = None,
        ロール5: discord.Role = None,
        説明: str = "セレクトボックスからロールを入手できます。",
    ):
        await interaction.response.defer()
        roles = [ロール1, ロール2, ロール3, ロール4, ロール5]
        roles = [r for r in roles if r is not None]
        options = [
            discord.SelectOption(
                label=role.name,
                description=f"{role.name}のロールを付与",
                value=f"select_role+{role.id}",
            )
            for role in roles
            if role is not None
        ]
        view = discord.ui.View()
        view.add_item(
            discord.ui.Select(
                placeholder="ロールを選んでください",
                options=options,
                max_values=len(options),
                custom_id="select_role",
            )
        )
        await interaction.channel.send(
            embed=discord.Embed(
                title=タイトル, description=説明, color=discord.Color.green()
            ).add_field(
                name="ロール一覧",
                value="\n".join([role.mention for role in roles if role is not None]),
            ),
            view=view,
        )
        await interaction.delete_original_response()

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_select(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 3:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id == "select_role":
                    try:
                        add = []
                        remove = []
                        await interaction.response.defer(ephemeral=True)
                        for r in interaction.data["values"]:
                            roleid = r.removeprefix("select_role+")
                            role = interaction.guild.get_role(int(roleid))
                            if role not in interaction.user.roles:
                                await interaction.user.add_roles(role)
                                add.append(role.mention)
                            if role in interaction.user.roles:
                                await interaction.user.remove_roles(role)
                                remove.append(role.mention)
                            await asyncio.sleep(1)
                        await interaction.followup.send(
                            ephemeral=True,
                            embed=discord.Embed(
                                color=discord.Color.green(),
                                title="ロールの追加・剥奪が完了しました。",
                                description="追加されたロール:\n{}\n剥奪されたロール:\n{}".format(
                                    "\n".join(add), "\n".join(remove)
                                ),
                            ),
                        )
                    except discord.Forbidden as f:
                        await interaction.followup.send(
                            "付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif",
                            ephemeral=True,
                        )
                    except:
                        await interaction.followup.send(
                            "追加に失敗しました。", ephemeral=True
                        )
        except Exception as e:
            return

    @panel.command(name="poll", description="アンケート作成をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_poll(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        選択肢1: str,
        選択肢2: str = None,
        選択肢3: str = None,
        選択肢4: str = None,
        選択肢5: str = None,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer(ephemeral=True)
        if not 選択肢2 and not 選択肢3 and not 選択肢4 and not 選択肢5:
            msg_ = await interaction.channel.send(
                embed=discord.Embed(
                    title=タイトル, description=選択肢1, color=discord.Color.blue()
                )
            )
            await msg_.add_reaction("👍")
            await msg_.add_reaction("👎")
            await interaction.followup.send(
                embed=discord.Embed(
                    title="作成しました。", color=discord.Color.green()
                ),
                ephemeral=True,
            )
            return
        if not 選択肢3 and not 選択肢4 and not 選択肢5:
            msg_ = await interaction.channel.send(
                embed=discord.Embed(
                    title=タイトル,
                    description="🇦 " + 選択肢1 + f"\n🇧 {選択肢2}",
                    color=discord.Color.blue(),
                )
            )
            await msg_.add_reaction("🇦")
            await msg_.add_reaction("🇧")
            await interaction.followup.send(
                embed=discord.Embed(
                    title="作成しました。", color=discord.Color.green()
                ),
                ephemeral=True,
            )
            return
        text = ""
        # view = discord.ui.View()
        # view.add_item(discord.ui.Button(label=f"{選択肢1}", custom_id=f"poll+{選択肢1}"))
        text += f"1️⃣ {選択肢1}\n"
        try:
            if 選択肢2 != None:
                # view.add_item(discord.ui.Button(label=f"{選択肢2}", custom_id=f"poll+{選択肢2}"))
                text += f"2️⃣ {選択肢2}\n"
        except:
            pass
        try:
            if 選択肢3 != None:
                # view.add_item(discord.ui.Button(label=f"{選択肢3}", custom_id=f"poll+{選択肢3}"))
                text += f"3️⃣ {選択肢3}\n"
        except:
            pass
        try:
            if 選択肢4 != None:
                # view.add_item(discord.ui.Button(label=f"{選択肢4}", custom_id=f"poll+{選択肢4}"))
                text += f"4️⃣ {選択肢4}\n"
        except:
            pass
        try:
            if 選択肢5 != None:
                # view.add_item(discord.ui.Button(label=f"{選択肢5}", custom_id=f"poll+{選択肢5}"))
                text += f"5️⃣ {選択肢5}"
        except:
            pass
        # view.add_item(discord.ui.Button(label=f"集計", custom_id=f"poll_done+{ctx.author.id}"))
        # await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{text}", color=discord.Color.green()), view=view)
        msg_ = await interaction.channel.send(
            embed=discord.Embed(
                title=f"{タイトル}", description=f"{text}", color=discord.Color.blue()
            )
        )
        await msg_.add_reaction("1️⃣")
        if 選択肢2 != None:
            await msg_.add_reaction("2️⃣")
        await asyncio.sleep(1)
        if 選択肢3 != None:
            await msg_.add_reaction("3️⃣")
        if 選択肢4 != None:
            await msg_.add_reaction("4️⃣")
        if 選択肢5 != None:
            await msg_.add_reaction("5️⃣")
        await interaction.followup.send(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @panel.command(name="ticket", description="チケットパネルを作成します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_ticket(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        説明: str,
        カテゴリ: discord.CategoryChannel = None,
        実績チャンネル: discord.TextChannel = None,
        メンションするロール: discord.Role = None,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )
        msg = await interaction.channel.send(
            embed=discord.Embed(
                title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()
            ),
            view=discord.ui.View().add_item(
                discord.ui.Button(label="チケットを作成", custom_id="ticket_v1")
            ),
        )
        if カテゴリ:
            db = self.bot.async_db["Main"].TicketCategory
            await db.replace_one(
                {"Channel": カテゴリ.id, "Message": msg.id},
                {"Channel": カテゴリ.id, "Message": msg.id},
                upsert=True,
            )
        if 実績チャンネル:
            db = self.bot.async_db["Main"].TicketProgress
            await db.replace_one(
                {"Channel": 実績チャンネル.id, "Message": msg.id},
                {"Channel": 実績チャンネル.id, "Message": msg.id},
                upsert=True,
            )
        if メンションするロール:
            db = self.bot.async_db["Main"].TicketRole
            await db.replace_one(
                {"Role": メンションするロール.id, "Message": msg.id},
                {"Role": メンションするロール.id, "Message": msg.id},
                upsert=True,
            )
        await interaction.response.send_message(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @panel.command(name="party", description="様々な募集をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_party(
        self, interaction: discord.Interaction, 内容: str, 最大人数: int
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if 最大人数 > 16:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="15人まで可能です。", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        await interaction.channel.send(
            embed=discord.Embed(title="募集", color=discord.Color.blue())
            .add_field(name="内容", value=内容, inline=False)
            .add_field(name="最大人数", value=f"{最大人数}人")
            .add_field(name="現在の参加人数", value="0人")
            .add_field(name="参加者", value="まだいません。", inline=False),
            view=discord.ui.View().add_item(
                discord.ui.Button(label="参加する", custom_id="join_party+")
            ),
        )
        await interaction.response.send_message(
            embed=discord.Embed(title="作成しました。", color=discord.Color.green()),
            ephemeral=True,
        )

    @panel.command(name="enquete", description="アンケートを取ります。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_enquete(
        self, interaction: discord.Interaction, タイトル: str, 質問1: str, 質問2: str=None, 質問3: str=None, 質問4: str=None, 質問5: str=None
    ):
        await interaction.response.defer()
        q_s = [質問1, 質問2, 質問3, 質問4, 質問5]
        q_s = [q for q in q_s if q is not None]
        embed=discord.Embed(title=タイトル, color=discord.Color.green())
        for q in q_s:
            embed.add_field(name=q, inline=False, value="未回答")
        embed.set_footer(text="SharkBot Enquete")
        await interaction.channel.send(embed=embed, view=discord.ui.View().add_item(discord.ui.Button(label="回答する", custom_id="enquete_answer+")))
        await interaction.delete_original_response()

    @panel.command(name="templates", description="テンプレートに沿って話してもらうパネルを作成します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_templates(
        self, interaction: discord.Interaction, タイトル: str, 質問1: str, 質問2: str=None, 質問3: str=None, 質問4: str=None, 質問5: str=None
    ):
        await interaction.response.defer()
        q_s = [質問1, 質問2, 質問3, 質問4, 質問5]
        q_s = [q for q in q_s if q is not None]
        embed=discord.Embed(title=タイトル, color=discord.Color.green())
        for i, q in enumerate(q_s):
            embed.add_field(name=f"Q.{i+1}", inline=False, value=f"{q}")
        embed.set_footer(text="SharkBot Templates")
        await interaction.channel.send(embed=embed, view=discord.ui.View().add_item(discord.ui.Button(label="発言する", custom_id="templates_answer+")))
        await interaction.delete_original_response()

    @panel.command(name="top", description="一コメを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def top(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async for top in interaction.channel.history(limit=1, oldest_first=True):
            await interaction.followup.send(
                embed=discord.Embed(
                    title="最初のコメント (一コメ)",
                    color=discord.Color.green(),
                    description=top.content,
                ),
                view=discord.ui.View().add_item(
                    discord.ui.Button(label="アクセスする", url=top.jump_url)
                ),
            )
            return

    @panel.command(name="free-channel", description="フリーチャンネルを作成します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def panel_free_channel(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        説明: str,
        カテゴリ: discord.CategoryChannel = None,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )
        msg = await interaction.channel.send(
            embed=discord.Embed(
                title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()
            ),
            view=discord.ui.View().add_item(
                discord.ui.Button(label="チャンネルを作成", custom_id="freechannel_")
            ),
        )
        if カテゴリ:
            db = self.bot.async_db["Main"].FreeChannelCategory
            await db.replace_one(
                {"Channel": カテゴリ.id, "Message": msg.id},
                {"Channel": カテゴリ.id, "Message": msg.id},
                upsert=True,
            )
        await interaction.response.send_message(
            ephemeral=True, content="フリーチャンネルパネルを作成しました。"
        )


async def setup(bot):
    await bot.add_cog(PanelCog(bot))
