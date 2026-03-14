from discord.ext import commands
import discord
from discord import app_commands
import random
import asyncio

from models import make_embed

class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_user_leveling(self, guild_id: int, user_id: int):
        db = self.bot.async_db["Main"].Leveling
        data = await db.find_one({"Guild": guild_id, "User": user_id})
        return (data.get("Level", 0), data.get("XP", 0)) if data else (0, 0)

    async def update_user_leveling(self, guild_id: int, user_id: int, level: int, xp: int):
        db = self.bot.async_db["Main"].Leveling
        await db.update_one({"Guild": guild_id, "User": user_id}, {"$set": {"Level": level, "XP": xp}}, upsert=True)

    async def add_server_money(self, guild_id: int, user_id: int, coin: int):
        db = self.bot.async_db["Main"].ServerMoney
        await db.update_one({"_id": f"{guild_id}-{user_id}"}, {"$inc": {"count": coin}, "$set": {"Guild": guild_id, "User": user_id}}, upsert=True)

    async def add_server_item(self, guild_id: int, user_id: int, itemname: str, count: int):
        db = self.bot.async_db["Main"].ServerMoneyItem
        _id = f"{guild_id}-{user_id}-{itemname}"
        await db.update_one({"_id": _id}, {"$inc": {"count": count}, "$set": {"Guild": guild_id, "User": user_id, "ItemName": itemname}}, upsert=True)

    async def giveaway_select_winner(self, interaction: discord.Interaction, data: dict, is_reroll: bool = False):
        members = data.get("Members", [])
        prize_text = data.get('Item', '不明')
        guild = interaction.guild

        if not members:
            return await interaction.followup.send("参加者がいないため、抽選できませんでした。", ephemeral=True)

        winner_id = random.choice(members)
        try:
            winner = guild.get_member(winner_id) or await guild.fetch_member(winner_id)
        except:
            winner = None

        if not winner:
            return await interaction.followup.send(f"当選者（ID: {winner_id}）がサーバーに見つかりませんでした。再度お試しください。", ephemeral=True)

        if data.get("XP", 0) > 0:
            lv, current_xp = await self.get_user_leveling(guild.id, winner.id)
            await self.update_user_leveling(guild.id, winner.id, lv, current_xp + data["XP"])
        
        if data.get("Coin", 0) > 0:
            await self.add_server_money(guild.id, winner.id, data["Coin"])
        
        if data.get("Itemname") != "0":
            await self.add_server_item(guild.id, winner.id, data["Itemname"], data.get("Count", 1))

        prefix = "【再抽選】" if is_reroll else ""
        content = f"{prefix}{winner.name} さん、おめでとうございます！"
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="再抽選", custom_id=f"giveaway_reroll_{interaction.message.id}", style=discord.ButtonStyle.gray))
        
        await interaction.channel.send(view=view, embed=make_embed.success_embed(title=content, description=f"**{prize_text}** に当選しました！"), content=winner.mention)

    async def giveaway_create(self, interaction: discord.Interaction, title: str, prize: str, xp: int, coin: int, itemname: str, count: int):
        embed = discord.Embed(title=title, description=f"**景品:** `{prize}`\nボタンを押して参加！", color=discord.Color.gold())
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="参加する", custom_id="giveaway_join", style=discord.ButtonStyle.blurple))
        view.add_item(discord.ui.Button(label="終了する", custom_id="giveaway_end", style=discord.ButtonStyle.red))

        await interaction.response.send_message("Giveawayを作成しました。", ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=view)

        db = self.bot.async_db["Main"].Giveaway
        await db.update_one(
            {"Guild": interaction.guild.id, "Message": msg.id},
            {"$set": {"Item": prize, "Members": [], "XP": xp, "Coin": coin, "Itemname": itemname, "Count": count, "Active": True}},
            upsert=True
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id: return

        db = self.bot.async_db["Main"].Giveaway

        if custom_id == "giveaway_join":
            res = await db.update_one(
                {"Guild": interaction.guild.id, "Message": interaction.message.id, "Active": True},
                {"$addToSet": {"Members": interaction.user.id}}
            )
            msg = "参加しました！" if res.modified_count > 0 else "既に参加しているか、終了しています。"
            await interaction.response.send_message(msg, ephemeral=True)

        elif custom_id == "giveaway_end":
            if not interaction.user.guild_permissions.manage_guild:
                return await interaction.response.send_message("権限がありません。", ephemeral=True)
            
            data = await db.find_one_and_update(
                {"Guild": interaction.guild.id, "Message": interaction.message.id, "Active": True},
                {"$set": {"Active": False}}
            )
            if not data:
                return await interaction.response.send_message("既に終了しているか、データがありません。", ephemeral=True)
            
            await interaction.response.defer(ephemeral=True)
            await interaction.message.edit(view=None)
            await self.giveaway_select_winner(interaction, data)

        elif custom_id.startswith("giveaway_reroll_"):
            if not interaction.user.guild_permissions.manage_guild:
                return await interaction.response.send_message("権限がありません。", ephemeral=True)
            
            original_msg_id = int(custom_id.replace("giveaway_reroll_", ""))
            data = await db.find_one({"Message": original_msg_id})
            
            if not data:
                return await interaction.response.send_message("抽選データが見つかりません。", ephemeral=True)
            
            await interaction.response.defer(ephemeral=True)
            await self.giveaway_select_winner(interaction, data, is_reroll=True)

    giveaway = app_commands.Group(name="giveaway", description="サーバー内プレゼント企画")

    @giveaway.command(name="create", description="プレゼント企画を開始")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_create_cmd(self, interaction: discord.Interaction, タイトル: str, 景品名: str, xp: int = 0, コイン: int = 0, アイテム名: str = "0", 個数: int = 1):
        await self.giveaway_create(interaction, タイトル, 景品名, xp, コイン, アイテム名, 個数)

async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))