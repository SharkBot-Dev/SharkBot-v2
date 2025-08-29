from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import io
import time
import asyncio
import re
import datetime
from functools import partial
import aiohttp
import time
import matplotlib.pyplot as plt
from discord import app_commands


class Paginator(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current = 0

    async def update_message(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.embeds[self.current], view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = (self.current - 1) % len(self.embeds)
        await self.update_message(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = (self.current + 1) % len(self.embeds)
        await self.update_message(interaction)


class ListingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ListingCog")

    listing = app_commands.Group(name="listing", description="メンバーをリスト化します。")

    @listing.command(name="member", description="メンバーをリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def listing_member(self,  interaction: discord.Interaction):
        await interaction.response.defer()
        member_list = interaction.guild.members
        spliting_member_list = [member_list[i: i+20]
                                for i in range(0, len(member_list), 20)]

        def return_memberinfos(page: int):
            return "\n".join([f"{sm.name}({sm.id})" for sm in spliting_member_list[page-1]])

        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(
                    label="ページ番号", placeholder="数字を入力", style=discord.TextStyle.short, required=True)
                self.add_item(self.page)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    test = int(self.page.value)
                    await interaction.message.edit(embed=discord.Embed(title=f"メンバーリスト ({len(member_list)}人)", description=return_memberinfos(int(self.page.value)), color=discord.Color.blue()).set_footer(text=f"{self.page.value}/{len(spliting_member_list)}"))
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")

        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send())

        await interaction.followup.send(embed=discord.Embed(title=f"メンバーリスト ({len(member_list)}人)", description=return_memberinfos(1), color=discord.Color.blue()).set_footer(text=f"1/{len(spliting_member_list)}"), view=SendModal())

    @listing.command(name="role", description="ロールをリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def listing_role(self, interaction: discord.Interaction):
        await interaction.response.defer()
        member_list = interaction.guild.roles

        if len(member_list) == 0:
            return await interaction.followup.send("ロールがありません。")

        spliting_member_list = [member_list[i: i + 20]
                                for i in range(0, len(member_list), 20)]

        def return_memberinfos(page: int):
            return "\n".join([f"{sm.name.replace('@', '')} ({sm.id})" for sm in spliting_member_list[page - 1]])

        class send(discord.ui.Modal):
            def __init__(self, view: discord.ui.View):
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(
                    label="ページ番号", placeholder="数字を入力", style=discord.TextStyle.short, required=True)
                self.add_item(self.page)
                self.view_ref = view

            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    page_number = int(self.page.value)
                    if not (1 <= page_number <= len(spliting_member_list)):
                        return await interaction.response.send_message(
                            "そのページは存在しません。", ephemeral=True
                        )
                    self.view_ref.current_page = page_number
                    embed = discord.Embed(
                        title=f"ロールリスト ({len(member_list)}個)",
                        description=return_memberinfos(page_number),
                        color=discord.Color.blue()
                    ).set_footer(text=f"{page_number}/{len(spliting_member_list)}")

                    await interaction.response.edit_message(embed=embed, view=self.view_ref)

                except ValueError:
                    await interaction.response.send_message("数字以外を入れないでください。", ephemeral=True)

        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.current_page = 1

            async def update_embed(self, interaction: discord.Interaction):
                self.previous.disabled = self.current_page <= 1
                self.next.disabled = self.current_page >= len(
                    spliting_member_list)

                embed = discord.Embed(
                    title=f"ロールリスト ({len(member_list)}個)",
                    description=return_memberinfos(self.current_page),
                    color=discord.Color.blue()
                ).set_footer(text=f"{self.current_page}/{len(spliting_member_list)}")
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.green, disabled=True)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page -= 1
                await self.update_embed(interaction)

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.green)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page += 1
                await self.update_embed(interaction)

            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send(self))

        view = SendModal()
        view.previous.disabled = True
        view.next.disabled = len(spliting_member_list) <= 1

        embed = discord.Embed(
            title=f"ロールリスト ({len(member_list)}個)",
            description=return_memberinfos(1),
            color=discord.Color.blue()
        ).set_footer(text=f"1/{len(spliting_member_list)}")

        await interaction.followup.send(embed=embed, view=view)

    @listing.command(name="emoji", description="サーバー内絵文字をリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def listing_emoji(self,  interaction: discord.Interaction):
        await interaction.response.defer()
        emoji_list = interaction.guild.emojis

        if len(emoji_list) == 0:
            return await interaction.followup.send("絵文字がありません。")

        spliting_member_list = [emoji_list[i: i + 20]
                                for i in range(0, len(emoji_list), 20)]

        def return_memberinfos(page: int):
            return "\n".join([f"{sm} `{sm}`" for sm in spliting_member_list[page - 1]])

        class send(discord.ui.Modal):
            def __init__(self, view: discord.ui.View):
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(
                    label="ページ番号", placeholder="数字を入力", style=discord.TextStyle.short, required=True)
                self.add_item(self.page)
                self.view_ref = view

            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    page_number = int(self.page.value)
                    if not (1 <= page_number <= len(spliting_member_list)):
                        return await interaction.followup.send(ephemeral=True, content="そのページは存在しません。")
                    self.view_ref.current_page = page_number
                    await self.view_ref.update_embed(interaction)
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")

        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.current_page = 1

            async def update_embed(self, interaction: discord.Interaction):
                self.previous.disabled = self.current_page <= 1
                self.next.disabled = self.current_page >= len(
                    spliting_member_list)

                embed = discord.Embed(
                    title=f"絵文字リスト ({len(emoji_list)}個)",
                    description=return_memberinfos(self.current_page),
                    color=discord.Color.blue()
                ).set_footer(text=f"{self.current_page}/{len(spliting_member_list)}")
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.green, disabled=True)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page -= 1
                await self.update_embed(interaction)

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.green)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page += 1
                await self.update_embed(interaction)

            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send(self))

        view = SendModal()
        view.previous.disabled = True
        view.next.disabled = len(spliting_member_list) <= 1

        embed = discord.Embed(
            title=f"絵文字リスト ({len(emoji_list)}個)",
            description=return_memberinfos(1),
            color=discord.Color.blue()
        ).set_footer(text=f"1/{len(spliting_member_list)}")

        await interaction.followup.send(embed=embed, view=view)

    @listing.command(name="invite", description="サーバー内招待リンクをリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def listing_invite(self,  interaction: discord.Interaction):
        await interaction.response.defer()
        invite_list = await interaction.guild.invites()

        if len(invite_list) == 0:
            return await interaction.followup.send("招待リンクがありません。")

        spliting_member_list = [invite_list[i: i + 20]
                                for i in range(0, len(invite_list), 20)]

        def return_memberinfos(page: int):
            return "\n".join([f"{sm.inviter.mention} {sm.url}" for sm in spliting_member_list[page - 1]])

        class send(discord.ui.Modal):
            def __init__(self, view: discord.ui.View):
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(
                    label="ページ番号", placeholder="数字を入力", style=discord.TextStyle.short, required=True)
                self.add_item(self.page)
                self.view_ref = view

            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    page_number = int(self.page.value)
                    if not (1 <= page_number <= len(spliting_member_list)):
                        return await interaction.followup.send(ephemeral=True, content="そのページは存在しません。")
                    self.view_ref.current_page = page_number
                    await self.view_ref.update_embed(interaction)
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")

        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.current_page = 1

            async def update_embed(self, interaction: discord.Interaction):
                self.previous.disabled = self.current_page <= 1
                self.next.disabled = self.current_page >= len(
                    spliting_member_list)

                embed = discord.Embed(
                    title=f"招待リスト ({len(invite_list)}個)",
                    description=return_memberinfos(self.current_page),
                    color=discord.Color.blue()
                ).set_footer(text=f"{self.current_page}/{len(spliting_member_list)}")
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.green, disabled=True)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page -= 1
                await self.update_embed(interaction)

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.green)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page += 1
                await self.update_embed(interaction)

            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send(self))

        view = SendModal()
        view.previous.disabled = True
        view.next.disabled = len(spliting_member_list) <= 1

        embed = discord.Embed(
            title=f"招待リスト ({len(invite_list)}個)",
            description=return_memberinfos(1),
            color=discord.Color.blue()
        ).set_footer(text=f"1/{len(spliting_member_list)}")

        await interaction.followup.send(embed=embed, view=view)

    @listing.command(name="inviter", description="招待回数をリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def listing_invite(self,  interaction: discord.Interaction):
        await interaction.response.defer()
        invite_list = await interaction.guild.invites()

        if len(invite_list) == 0:
            return await interaction.followup.send("招待リンクがありません。")

        ranking = {}
        for invite in invite_list:
            inviter = invite.inviter.mention if invite.inviter else "不明"
            ranking[inviter] = ranking.get(inviter, 0) + invite.uses

        sorted_ranking = sorted(
            ranking.items(), key=lambda x: x[1], reverse=True)

        split_ranking = [sorted_ranking[i:i + 20]
                         for i in range(0, len(sorted_ranking), 20)]

        def return_rankinginfos(page: int):
            start_rank = (page - 1) * 20
            lines = []
            for idx, (mention, uses) in enumerate(split_ranking[page - 1], start=start_rank + 1):
                lines.append(f"{idx}位: {mention} — {uses}人招待")
            return "\n".join(lines)

        class send(discord.ui.Modal):
            def __init__(self, view: discord.ui.View):
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(
                    label="ページ番号", placeholder="数字を入力",
                    style=discord.TextStyle.short, required=True
                )
                self.add_item(self.page)
                self.view_ref = view

            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    page_number = int(self.page.value)
                    if not (1 <= page_number <= len(split_ranking)):
                        return await interaction.followup.send(ephemeral=True, content="そのページは存在しません。")
                    self.view_ref.current_page = page_number
                    await self.view_ref.update_embed(interaction)
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")

        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.current_page = 1

            async def update_embed(self, interaction: discord.Interaction):
                self.previous.disabled = self.current_page <= 1
                self.next.disabled = self.current_page >= len(split_ranking)

                embed = discord.Embed(
                    title=f"招待回数ランキング",
                    description=return_rankinginfos(self.current_page),
                    color=discord.Color.blue()
                ).set_footer(text=f"{self.current_page}/{len(split_ranking)}")
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.green, disabled=True)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page -= 1
                await self.update_embed(interaction)

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.green)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page += 1
                await self.update_embed(interaction)

            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send(self))

        view = SendModal()
        view.previous.disabled = True
        view.next.disabled = len(split_ranking) <= 1

        embed = discord.Embed(
            title=f"招待回数ランキング",
            description=return_rankinginfos(1),
            color=discord.Color.blue()
        ).set_footer(text=f"1/{len(split_ranking)}")

        await interaction.followup.send(embed=embed, view=view)

    @listing.command(name="ban", description="Banしたメンバーをリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(ban_members=True)
    async def listing_ban(self, interaction: discord.Interaction):
        await interaction.response.defer()
        member_list = [b async for b in interaction.guild.bans()]
        if len(member_list) == 0:
            return await interaction.followup.send("Banされているメンバーはいません。")
        spliting_member_list = [member_list[i: i+20]
                                for i in range(0, len(member_list), 20)]

        def return_memberinfos(page: int):
            return "\n".join([f"{sm.user.name}({sm.user.id})" for sm in spliting_member_list[page-1]])

        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(
                    label="ページ番号", placeholder="数字を入力", style=discord.TextStyle.short, required=True)
                self.add_item(self.page)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    test = int(self.page.value)
                    await interaction.message.edit(embed=discord.Embed(title=f"BANリスト ({len(member_list)}人)", description=return_memberinfos(int(self.page.value)), color=discord.Color.blue()).set_footer(text=f"{self.page.value}/{len(spliting_member_list)}"))
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")

        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send())

        await interaction.followup.send(embed=discord.Embed(title=f"BANリスト ({len(member_list)}人)", description=return_memberinfos(1), color=discord.Color.blue()).set_footer(text=f"1/{len(spliting_member_list)}"), view=SendModal())

    @listing.command(name="guild-ban", description="認証時に検知する危険なサーバーリストを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(ban_members=True)
    async def listing_guild_ban(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].GuildBAN
        member_list = [b async for b in db.find({"Guild": str(interaction.guild.id)})]
        if len(member_list) == 0:
            return await interaction.followup.send("Banされているサーバーはありません。")
        spliting_member_list = [member_list[i: i+20]
                                for i in range(0, len(member_list), 20)]

        def return_memberinfos(page: int):
            return "\n".join([f"{sm["BANGuild"]}" for sm in spliting_member_list[page-1]])

        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="ページの移動", timeout=None)
                self.page = discord.ui.TextInput(
                    label="ページ番号", placeholder="数字を入力", style=discord.TextStyle.short, required=True)
                self.add_item(self.page)

            async def on_submit(self, interaction: discord.Interaction) -> None:
                try:
                    await interaction.response.defer(ephemeral=True)
                    test = int(self.page.value)
                    await interaction.message.edit(embed=discord.Embed(title=f"BANサーバーリスト ({len(member_list)}サーバー)", description=return_memberinfos(int(self.page.value)), color=discord.Color.blue()).set_footer(text=f"{self.page.value}/{len(spliting_member_list)}"))
                except:
                    return await interaction.followup.send(ephemeral=True, content="数字以外を入れないでください。")

        class SendModal(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(label="ページ移動", style=discord.ButtonStyle.blurple)
            async def page_move(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(send())

        await interaction.followup.send(embed=discord.Embed(title=f"BANサーバーリスト ({len(member_list)}サーバー)", description=return_memberinfos(1), color=discord.Color.blue()).set_footer(text=f"1/{len(spliting_member_list)}"), view=SendModal())

    @listing.command(name="analysis", description="サーバーを解析します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(内容=[
        app_commands.Choice(name='メンバーとBotの比率', value="mb"),
        app_commands.Choice(name='1ヶ月間の1日ごとのメンバー参加数', value="one_mem"),
        app_commands.Choice(name='メンバーの機種の割合', value="pc_sm"),
        app_commands.Choice(name='メンバーのステータスの割合', value="mem_status"),
        app_commands.Choice(name='グローバルなユーザーとBotの比率', value="gl_mb"),
    ])
    async def analysis_guild_or_user(self, interaction: discord.Interaction, 内容: app_commands.Choice[str]):
        await interaction.response.defer()
        if 内容.value == "mb":
            member_list = len(interaction.guild.members)
            bot_list = len([m for m in interaction.guild.members if m.bot])
            human_list = len(
                [m for m in interaction.guild.members if not m.bot])
            json_data = {
                'labels': [
                    f'Members ({human_list})',
                    f'Bots ({bot_list})',
                ],
                'values': [
                    human_list / member_list,
                    bot_list / member_list
                ],
                'title': f'Member and Bot Ratio ({member_list})'
            }
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:3067/piechart", json=json_data) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(file=discord.File(io_, filename="piechart.png"))
                    io_.close()
        elif 内容.value == "one_mem":
            time_ = []
            count_ = []
            member_list = interaction.guild.members
            now = datetime.datetime.now(datetime.timezone.utc)

            for i in range(30):
                d = now - datetime.timedelta(days=i)
                label = i
                time_.append(label)

                matched_members = [
                    member for member in member_list
                    if member.joined_at and abs((member.joined_at - d).days) == 0
                ]
                count_.append(len(matched_members))

            json_data = {
                'xvalues': time_[::-1],
                'yvalues': count_[::-1],
                'title': "Number of members participating"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:3067/plot", json=json_data) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(file=discord.File(io_, filename="join_chart.png"))
                    io_.close()
        elif 内容.value == "gl_mb":
            member_list = len(self.bot.users)
            bot_list = len([m for m in self.bot.users if m.bot])
            human_list = len([m for m in self.bot.users if not m.bot])
            json_data = {
                'labels': [
                    f'Users ({human_list})',
                    f'Bots ({bot_list})',
                ],
                'values': [
                    human_list / member_list,
                    bot_list / member_list
                ],
                'title': f'User and Bot Ratio ({member_list})'
            }
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:3067/piechart", json=json_data) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(file=discord.File(io_, filename="piechart.png"))
                    io_.close()
        elif 内容.value == "pc_sm":
            member_list = len(interaction.guild.members)
            browser = len(
                [m for m in interaction.guild.members if m.client_status.web])
            phone = len(
                [m for m in interaction.guild.members if m.client_status.mobile])
            desktop = len(
                [m for m in interaction.guild.members if m.client_status.desktop])
            json_data = {
                'labels': [
                    f'Borwser ({browser})',
                    f'Phone ({phone})',
                    f"Desktop ({desktop})"
                ],
                'values': [
                    browser,
                    phone,
                    desktop
                ],
                'title': f"Percentage of members' devices ({member_list})"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:3067/piechart", json=json_data) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(file=discord.File(io_, filename="piechart.png"))
                    io_.close()
        elif 内容.value == "mem_status":
            member_list = len(interaction.guild.members)
            online = len(
                [m for m in interaction.guild.members if m.status == discord.Status.online])
            idle = len(
                [m for m in interaction.guild.members if m.status == discord.Status.idle])
            dnd = len(
                [m for m in interaction.guild.members if m.status == discord.Status.dnd])
            ofline = len(
                [m for m in interaction.guild.members if m.status == discord.Status.offline])
            json_data = {
                'labels': [
                    f'Online ({online})',
                    f'Idle ({idle})',
                    f"Dnd ({dnd})",
                    f"Ofline ({ofline})"
                ],
                'values': [
                    online,
                    idle,
                    dnd,
                    ofline
                ],
                'title': f"Member Status Percentage ({member_list})"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:3067/piechart", json=json_data) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(file=discord.File(io_, filename="piechart.png"))
                    io_.close()

    @listing.command(name="graph", description="グラフを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(内容=[
        app_commands.Choice(name='円グラフ', value="pie"),
        app_commands.Choice(name='折れ線グラフ', value="line"),
    ])
    async def graph_make(self, interaction_: discord.Interaction, 内容: app_commands.Choice[str], タイトル: str = "Graph"):
        if 内容.value == "pie":
            class send(discord.ui.Modal):
                def __init__(self) -> None:
                    super().__init__(title="円グラフの設定", timeout=None)
                    self.datas = discord.ui.TextInput(
                        label="データ (「ラベル|データ」 と入力)", placeholder="タイトルを入力", style=discord.TextStyle.long, required=True)
                    self.add_item(self.datas)

                async def on_submit(self, interaction: discord.Interaction) -> None:
                    await interaction.response.defer(ephemeral=True)
                    try:
                        data = self.datas.value.split("\n")
                        labels = []
                        values = []
                        for d in data:
                            label, value = d.split("|")
                            labels.append(label)
                            values.append(int(value))
                        if len(labels) != len(values):
                            raise ValueError("ラベルとデータの数が一致しません。")
                    except Exception as e:
                        return await interaction.followup.send(ephemeral=True, content="エラーが発生しました。")
                    json_data = {
                        'labels': labels,
                        'values': values,
                        'title': タイトル
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post("http://localhost:3067/piechart", json=json_data) as response:
                            io_ = io.BytesIO(await response.read())
                            await interaction.followup.send(file=discord.File(io_, filename="piechart.png"))
                            io_.close()
            await interaction_.response.send_modal(send())
        elif 内容.value == "line":
            class send(discord.ui.Modal):
                def __init__(self) -> None:
                    super().__init__(title="折れ線グラフの設定", timeout=None)
                    self.xdatas = discord.ui.TextInput(
                        label="Xのデータ (,で区切る)", placeholder="1,2,3", style=discord.TextStyle.long, required=True)
                    self.add_item(self.xdatas)
                    self.ydatas = discord.ui.TextInput(
                        label="Yのデータ (,で区切る)", placeholder="1,2,3", style=discord.TextStyle.long, required=True)
                    self.add_item(self.ydatas)

                async def on_submit(self, interaction: discord.Interaction) -> None:
                    await interaction.response.defer(ephemeral=True)
                    try:
                        x = []
                        y = []
                        xdata = self.xdatas.value.split(",")
                        for d in xdata:
                            if not d.isdigit():
                                return await interaction.followup.send(ephemeral=True, content="Xのデータは数字でなければなりません。")
                            x.append(int(d))
                        ydata = self.ydatas.value.split(",")
                        for d in ydata:
                            if not d.isdigit():
                                return await interaction.followup.send(ephemeral=True, content="Yのデータは数字でなければなりません。")
                            y.append(int(d))
                        if len(x) != len(y):
                            return await interaction.followup.send(ephemeral=True, content="XとYのデータの数が一致しません。")
                    except Exception as e:
                        return await interaction.followup.send(ephemeral=True, content="エラーが発生しました。")
                    json_data = {
                        'xvalues': x,
                        'yvalues': y,
                        'title': タイトル
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post("http://localhost:3067/plot", json=json_data) as response:
                            io_ = io.BytesIO(await response.read())
                            await interaction.followup.send(file=discord.File(io_, filename="plot.png"))
                            io_.close()
            await interaction_.response.send_modal(send())


async def setup(bot):
    await bot.add_cog(ListingCog(bot))
