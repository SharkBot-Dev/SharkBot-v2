from discord.ext import commands
import discord
from discord import app_commands
import random
import asyncio


class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def user_write(
        self, guild: discord.Guild, user: discord.User, level: int, xp: int
    ):
        try:
            db = self.bot.async_db["Main"].Leveling
            await db.replace_one(
                {"Guild": guild.id, "User": user.id},
                {"Guild": guild.id, "User": user.id, "Level": level, "XP": xp},
                upsert=True,
            )
        except:
            return

    async def get_level(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one(
                    {"Guild": guild.id, "User": user.id}, {"_id": False}
                )
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Level"]
        except:
            return

    async def get_xp(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one(
                    {"Guild": guild.id, "User": user.id}, {"_id": False}
                )
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["XP"]
        except:
            return

    async def add_server_money(
        self, guild: discord.Guild, author: discord.User, coin: int
    ):
        db = self.bot.async_db["Main"].ServerMoney
        user_data = await db.find_one({"_id": f"{guild.id}-{author.id}"})
        if user_data:
            await db.update_one(
                {"_id": f"{guild.id}-{author.id}"}, {"$inc": {"count": coin}}
            )
        else:
            await db.insert_one(
                {
                    "_id": f"{guild.id}-{author.id}",
                    "count": coin,
                    "Guild": guild.id,
                    "User": author.id,
                }
            )
        return True

    async def add_server_item(
        self, guild: discord.Guild, author: discord.User, itemname: str, count: int
    ):
        db = self.bot.async_db["Main"].ServerMoneyItem
        _id = f"{guild.id}-{author.id}-{itemname}"
        user_data = await db.find_one({"_id": _id})
        if user_data:
            await db.update_one({"_id": _id}, {"$inc": {"count": count}})
        else:
            await db.insert_one(
                {
                    "_id": _id,
                    "Guild": guild.id,
                    "User": author.id,
                    "ItemName": itemname,
                    "count": count,
                }
            )
        return True

    async def get_server_items(self, guild: discord.Guild, itemname: str):
        db = self.bot.async_db["Main"].ServerMoneyItems
        dbfind = await db.find_one(
            {"Guild": guild.id, "ItemName": itemname}, {"_id": False}
        )
        return dbfind

    async def giveaway_create(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        景品名: str,
        xp: int = 0,
        coin: int = 0,
        itemname: str = "0",
        count: int = 1,
    ):
        await interaction.response.send_message(
            ephemeral=True, content="Giveawayを作成しました。"
        )
        msg = await interaction.channel.send(
            embed=discord.Embed(
                title=タイトル,
                description=f"`{景品名}`がもらえるかも！？",
                color=discord.Color.gold(),
            ),
            view=discord.ui.View()
            .add_item(
                discord.ui.Button(
                    label="参加する",
                    custom_id="giveaway+",
                    style=discord.ButtonStyle.blurple,
                )
            )
            .add_item(
                discord.ui.Button(
                    label="終了する",
                    custom_id="giveaway_end+",
                    style=discord.ButtonStyle.red,
                )
            ),
        )
        db = self.bot.async_db["Main"].Giveaway
        await db.replace_one(
            {"Guild": interaction.guild.id, "Message": msg.id},
            {
                "Guild": interaction.guild.id,
                "Message": msg.id,
                "Item": 景品名,
                "Members": [],
                "XP": xp,
                "Coin": coin,
                "Itemname": itemname,
                "Count": count,
            },
            upsert=True,
        )

    async def giveaway_join(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        await interaction.response.send_message(
            ephemeral=True, content="Giveawayに参加しました。"
        )
        db = self.bot.async_db["Main"].Giveaway
        await db.update_one(
            {"Guild": interaction.guild.id, "Message": message.id},
            {"$addToSet": {"Members": interaction.user.id}},
            upsert=True,
        )

    async def giveaway_end(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        db = self.bot.async_db["Main"].Giveaway
        try:
            dbfind = await db.find_one(
                {"Guild": interaction.guild.id, "Message": message.id}, {"_id": False}
            )
        except:
            return
        if dbfind is None:
            return await interaction.response.send_message(
                ephemeral=True, content="現在Giveawayをしていません。"
            )
        if dbfind.get("Members", []) == []:
            await interaction.response.send_message(
                ephemeral=True, content="誰も参加していませんでした。"
            )
            await message.edit(view=None)
            return await db.delete_one(
                {"Guild": interaction.guild.id, "Message": message.id}
            )
        await interaction.response.send_message(
            ephemeral=True, content="Giveawayを終了させます。"
        )
        r = interaction.guild.get_member(random.choice(dbfind.get("Members", [0, 1])))
        await message.edit(view=None)
        await asyncio.sleep(1)
        await message.channel.send(
            content=f"{r.mention} さん、おめでとうございます！\n{dbfind.get('Item', '？')}に当選しました！"
        )
        if dbfind.get("XP", 0) != 0:
            xp = await self.get_xp(interaction.guild, r)
            lv = await self.get_level(interaction.guild, r)
            await self.user_write(interaction.guild, r, lv, xp + dbfind.get("XP", 0))
        if dbfind.get("Coin", 0) != 0:
            await self.add_server_money(interaction.guild, r, dbfind.get("Coin", 0))
        if dbfind.get("Itemname", "0") != "0":
            sm = await self.get_server_items(
                interaction.guild, dbfind.get("Itemname", "0")
            )
            if not sm:
                return await db.delete_one(
                    {"Guild": interaction.guild.id, "Message": message.id}
                )
            await self.add_server_item(
                interaction.guild, r, dbfind.get("Itemname", "0"), dbfind.get("Count")
            )
        await db.delete_one({"Guild": interaction.guild.id, "Message": message.id})

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_freechannel(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id.startswith("giveaway+"):
                    await self.giveaway_join(interaction, interaction.message)
                if custom_id.startswith("giveaway_end+"):
                    if not interaction.user.guild_permissions.manage_guild:
                        return
                    await self.giveaway_end(interaction, interaction.message)
        except:
            return

    giveaway = app_commands.Group(
        name="giveaway", description="サーバー内でのプレゼント企画系のコマンドです。"
    )

    @giveaway.command(
        name="create", description="サーバー内でのプレゼント企画を実施します。"
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_create_(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        景品名: str,
        xp: int = 0,
        コイン: int = 0,
        アイテム名: str = "0",
    ):
        await self.giveaway_create(
            interaction, タイトル, 景品名, xp, コイン, アイテム名
        )


async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))
