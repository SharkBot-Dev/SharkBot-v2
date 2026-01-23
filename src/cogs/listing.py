from discord.ext import commands
import discord
import io
import datetime
import aiohttp
from discord import app_commands

from models import make_embed, pages


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


class ListingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> ListingCog")

    listing = app_commands.Group(
        name="listing", description="メンバーをリスト化します。"
    )

    @listing.command(name="member", description="メンバーをリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def listing_member(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        member_list = interaction.guild.members
        split_size = 20
        chunked_members = [
            member_list[i : i + split_size] for i in range(0, len(member_list), split_size)
        ]

        embeds = []
        total_pages = len(chunked_members)
        
        for i, members in enumerate(chunked_members):
            embed = discord.Embed(
                title=f"メンバーリスト ({len(member_list)}人)",
                color=discord.Color.blue(),
                description="\n".join([f"{m.name} (`{m.id}`)" for m in members])
            )
            embed.set_footer(text=f"Page {i + 1} / {total_pages}")
            embeds.append(embed)

        view = pages.Pages(embeds=embeds, now_page=0)

        msg = await interaction.followup.send(embed=embeds[0], view=view)

    @listing.command(name="role-member", description="ロールとそのメンバー数をリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def listing_role_member(self, interaction: discord.Interaction):
        await interaction.response.defer()

        raw = self.bot.raw(bot=self.bot)
        roles = await raw.get_guild_role_member_counts(guildId=str(interaction.guild_id))

        if not isinstance(roles, dict):
            return await interaction.followup.send("データの取得に失敗しました。")

        r = [f"<@&{r_id}> .. {count}人" for r_id, count in roles.items()]

        if len(r) == 0:
            return await interaction.followup.send(
                embed=make_embed.error_embed(title="ロールが見つかりません。")
            )

        split_size = 20
        spliting_roles_list = [
            r[i : i + split_size] for i in range(0, len(r), split_size)
        ]

        embeds = []
        total_pages = len(spliting_roles_list)
        for i, role_chunk in enumerate(spliting_roles_list):
            embed = discord.Embed(
                title=f"ロールメンバー数一覧 ({len(r)}種類)",
                description="\n".join(role_chunk),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {i + 1} / {total_pages}")
            embeds.append(embed)

        view = pages.Pages(embeds=embeds, now_page=0)

        msg = await interaction.followup.send(
            embed=embeds[0], 
            view=view, 
            allowed_mentions=discord.AllowedMentions.none()
        )

    @listing.command(name="role", description="ロールをリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def listing_role(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        role_list = list(reversed(interaction.guild.roles))

        if not role_list:
            return await interaction.followup.send("ロールが見つかりませんでした。")

        split_size = 20
        chunked_roles = [
            role_list[i : i + split_size] for i in range(0, len(role_list), split_size)
        ]

        embeds = []
        total_pages = len(chunked_roles)
        for i, roles in enumerate(chunked_roles):
            description = "\n".join([f"{r.mention} (`{r.id}`)" for r in roles])
            
            embed = discord.Embed(
                title=f"ロールリスト ({len(role_list)}個)",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {i + 1} / {total_pages}")
            embeds.append(embed)

        view = pages.Pages(embeds=embeds, now_page=0)

        msg = await interaction.followup.send(
            embed=embeds[0], 
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @listing.command(name="emoji", description="サーバー内絵文字をリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def listing_emoji(self, interaction: discord.Interaction):
        await interaction.response.defer()
        emoji_list = interaction.guild.emojis

        if len(emoji_list) == 0:
            return await interaction.followup.send("絵文字がありません。")

        chunked_emojis = [
            emoji_list[i : i + 20] for i in range(0, len(emoji_list), 20)
        ]

        embeds = []
        total_pages = len(chunked_emojis)
        for i, emojis in enumerate(chunked_emojis):
            description = "\n".join([f"{r.__str__()} (`{r.id}`)" for r in emojis])
            
            embed = discord.Embed(
                title=f"絵文字リスト ({len(emoji_list)}個)",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {i + 1} / {total_pages}")
            embeds.append(embed)

        view = pages.Pages(embeds=embeds, now_page=0)

        msg = await interaction.followup.send(
            embed=embeds[0], 
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @listing.command(
        name="invite", description="サーバー内招待リンクをリスト化します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def listing_invite(self, interaction: discord.Interaction):
        await interaction.response.defer()
        invite_list = await interaction.guild.invites()

        if len(invite_list) == 0:
            return await interaction.followup.send("招待リンクがありません。")

        sp_invite_list = [
            invite_list[i : i + 20] for i in range(0, len(invite_list), 20)
        ]

        embeds = []
        total_pages = len(sp_invite_list)
        for i, invite in enumerate(sp_invite_list):
            description = "\n".join([f"{i.inviter.mention} {i.url}" for i in invite])
            
            embed = discord.Embed(
                title=f"招待リンクリスト ({len(invite_list)}個)",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {i + 1} / {total_pages}")
            embeds.append(embed)

        view = pages.Pages(embeds=embeds, now_page=0)

        msg = await interaction.followup.send(
            embed=embeds[0], 
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @listing.command(name="inviter", description="招待回数をリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def listing_invite(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        invite_list = await interaction.guild.invites()

        if not invite_list:
            return await interaction.followup.send("有効な招待リンクがありません。")

        ranking = {}
        for invite in invite_list:
            inviter = invite.inviter.mention if invite.inviter else "不明"
            ranking[inviter] = ranking.get(inviter, 0) + invite.uses

        sorted_ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

        split_size = 20
        split_ranking_chunks = [
            sorted_ranking[i : i + split_size] for i in range(0, len(sorted_ranking), split_size)
        ]

        embeds = []
        total_pages = len(split_ranking_chunks)
        
        for i, chunk in enumerate(split_ranking_chunks):
            description = "\n".join([f"{inviter} ： **{count}** 回" for inviter, count in chunk])
            
            embed = discord.Embed(
                title=f"招待ランキング (合計 {len(sorted_ranking)}名)",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {i + 1} / {total_pages}")
            embeds.append(embed)

        view = pages.Pages(embeds=embeds, now_page=0)

        msg = await interaction.followup.send(
            embed=embeds[0], 
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @listing.command(name="ban", description="Banしたメンバーをリスト化します.")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(ban_members=True)
    async def listing_ban(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        bans = [b async for b in interaction.guild.bans()]
        
        if not bans:
            return await interaction.followup.send("Banされているメンバーはいません。")

        split_size = 20
        chunked_bans = [bans[i : i + split_size] for i in range(0, len(bans), split_size)]

        embeds = []
        total_pages = len(chunked_bans)
        for i, chunk in enumerate(chunked_bans):
            description = "\n".join([f"{entry.user.name} (`{entry.user.id}`)" for entry in chunk])
            embed = discord.Embed(
                title=f"BANリスト ({len(bans)}人)",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {i + 1} / {total_pages}")
            embeds.append(embed)

        view = pages.Pages(embeds=embeds, now_page=0)
        msg = await interaction.followup.send(embed=embeds[0], view=view)

    @listing.command(
        name="guild-ban",
        description="認証時に検知する危険なサーバーリストを取得します。",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(ban_members=True)
    async def listing_guild_ban(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        db = self.bot.async_db["Main"].GuildBAN
        guild_ban_list = [b async for b in db.find({"Guild": str(interaction.guild.id)})]
        
        if not guild_ban_list:
            return await interaction.followup.send("Banされているサーバーはありません。")

        split_size = 20
        chunked_guilds = [guild_ban_list[i : i + split_size] for i in range(0, len(guild_ban_list), split_size)]

        embeds = []
        total_pages = len(chunked_guilds)
        for i, chunk in enumerate(chunked_guilds):
            description = "\n".join([f"`{item['BANGuild']}`" for item in chunk])
            embed = discord.Embed(
                title=f"BANサーバーリスト ({len(guild_ban_list)}サーバー)",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {i + 1} / {total_pages}")
            embeds.append(embed)

        view = pages.Pages(embeds=embeds, now_page=0)
        msg = await interaction.followup.send(embed=embeds[0], view=view)
        view.message = msg

    @listing.command(name="analysis", description="サーバーを解析します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        内容=[
            app_commands.Choice(name="メンバーとBotの比率", value="mb"),
            app_commands.Choice(
                name="1ヶ月間の1日ごとのメンバー参加数", value="one_mem"
            ),
            app_commands.Choice(name="メンバーの機種の割合", value="pc_sm"),
            app_commands.Choice(name="メンバーのステータスの割合", value="mem_status"),
            app_commands.Choice(name="グローバルなユーザーとBotの比率", value="gl_mb"),
        ]
    )
    async def analysis_guild_or_user(
        self, interaction: discord.Interaction, 内容: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        if 内容.value == "mb":
            member_list = len(interaction.guild.members)
            bot_list = len([m for m in interaction.guild.members if m.bot])
            human_list = len([m for m in interaction.guild.members if not m.bot])
            json_data = {
                "labels": [
                    f"Members ({human_list})",
                    f"Bots ({bot_list})",
                ],
                "values": [human_list / member_list, bot_list / member_list],
                "title": f"Member and Bot Ratio ({member_list})",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:3067/piechart", json=json_data
                ) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(
                        file=discord.File(io_, filename="piechart.png")
                    )
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
                    member
                    for member in member_list
                    if member.joined_at and abs((member.joined_at - d).days) == 0
                ]
                count_.append(len(matched_members))

            json_data = {
                "xvalues": time_[::-1],
                "yvalues": count_[::-1],
                "title": "Number of members participating",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:3067/plot", json=json_data
                ) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(
                        file=discord.File(io_, filename="join_chart.png")
                    )
                    io_.close()
        elif 内容.value == "gl_mb":
            member_list = len(self.bot.users)
            bot_list = len([m for m in self.bot.users if m.bot])
            human_list = len([m for m in self.bot.users if not m.bot])
            json_data = {
                "labels": [
                    f"Users ({human_list})",
                    f"Bots ({bot_list})",
                ],
                "values": [human_list / member_list, bot_list / member_list],
                "title": f"User and Bot Ratio ({member_list})",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:3067/piechart", json=json_data
                ) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(
                        file=discord.File(io_, filename="piechart.png")
                    )
                    io_.close()
        elif 内容.value == "pc_sm":
            member_list = len(interaction.guild.members)
            browser = len([m for m in interaction.guild.members if m.client_status.web])
            phone = len(
                [m for m in interaction.guild.members if m.client_status.mobile]
            )
            desktop = len(
                [m for m in interaction.guild.members if m.client_status.desktop]
            )
            json_data = {
                "labels": [
                    f"Borwser ({browser})",
                    f"Phone ({phone})",
                    f"Desktop ({desktop})",
                ],
                "values": [browser, phone, desktop],
                "title": f"Percentage of members' devices ({member_list})",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:3067/piechart", json=json_data
                ) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(
                        file=discord.File(io_, filename="piechart.png")
                    )
                    io_.close()
        elif 内容.value == "mem_status":
            member_list = len(interaction.guild.members)
            online = len(
                [
                    m
                    for m in interaction.guild.members
                    if m.status == discord.Status.online
                ]
            )
            idle = len(
                [
                    m
                    for m in interaction.guild.members
                    if m.status == discord.Status.idle
                ]
            )
            dnd = len(
                [m for m in interaction.guild.members if m.status == discord.Status.dnd]
            )
            ofline = len(
                [
                    m
                    for m in interaction.guild.members
                    if m.status == discord.Status.offline
                ]
            )
            json_data = {
                "labels": [
                    f"Online ({online})",
                    f"Idle ({idle})",
                    f"Dnd ({dnd})",
                    f"Ofline ({ofline})",
                ],
                "values": [online, idle, dnd, ofline],
                "title": f"Member Status Percentage ({member_list})",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:3067/piechart", json=json_data
                ) as response:
                    io_ = io.BytesIO(await response.read())
                    await interaction.followup.send(
                        file=discord.File(io_, filename="piechart.png")
                    )
                    io_.close()

    @listing.command(name="graph", description="グラフを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def graph_make(
        self,
        interaction: discord.Interaction,
        数式: str
    ):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:3067/formula", json={
                    'formula': 数式
                }
            ) as response:
                if response.status != 200:
                    e = await response.json()
                    return await interaction.followup.send(embed=make_embed.error_embed(title="グラフの作成に失敗しました。", description=f"```{e.get('error', 'エラーの取得失敗')}```"))
                
                i = io.BytesIO(await response.read())
                file = discord.File(i, filename="graph.png")

                await interaction.followup.send(file=file, embed=make_embed.success_embed(title="グラフを作成しました。", description=f"数式: `{数式}`"))
                i.close()

async def setup(bot):
    await bot.add_cog(ListingCog(bot))
