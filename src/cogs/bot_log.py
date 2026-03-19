import asyncio

from discord.ext import commands
import discord
from consts import mongodb
from models import make_embed


class BotLogCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> BotLogCog")

    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove_delete_data(self, guild: discord.Guild):
        # Prefixの削除
        db = self.bot.async_db["DashboardBot"].CustomPrefixBot
        await db.delete_many({"Guild": guild.id})

        # おはよう通知の削除
        db = self.bot.async_db["Main"].GoodMorningChannel
        await db.delete_many({"Guild": guild.id})

        # APIKeyの削除
        db = self.bot.async_db["SharkAPI"].APIKeys
        await db.delete_many({"guild_id": guild.id})

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_blockuser(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].BlockUser
        try:
            profile = await db.find_one({"User": guild.owner_id}, {"_id": False})
            if profile is None:
                return
            else:
                await guild.leave()
                await asyncio.sleep(1)
                await self.bot.get_channel(1359793645842206912).send(
                    embed=make_embed.success_embed(
                        title=f"ブロックされているサーバーから退出しました。"
                    )
                    .set_thumbnail(url=guild.icon.url if guild.icon else None)
                    .add_field(name=f"サーバー名", value=guild.name, inline=False)
                    .add_field(name=f"サーバーID", value=str(guild.id), inline=False)
                    .add_field(
                        name=f"理由", value=profile.get("Reason", "なし"), inline=False
                    )
                )
                return
        except:
            return

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_log(self, guild: discord.Guild):
        await self.bot.get_channel(1359793645842206912).send(
            embed=discord.Embed(
                title=f"サーバーに参加しました。",
                color=discord.Color.green(),
            )
            .set_thumbnail(url=guild.icon.url if guild.icon else None)
            .add_field(name=f"サーバー名", value=guild.name, inline=False)
            .add_field(name=f"サーバーID", value=str(guild.id), inline=False)
        )

        db = self.bot.async_db["Main"].BlockGuild

        try:
            profile = await db.find_one({"Guild": guild.id}, {"_id": False})
            if profile is None:
                return
            else:
                await guild.leave()
                await asyncio.sleep(1)
                await self.bot.get_channel(1359793645842206912).send(
                    embed=make_embed.success_embed(
                        title=f"ブロックされているサーバーから退出しました。"
                    )
                    .set_thumbnail(url=guild.icon.url if guild.icon else None)
                    .add_field(name=f"サーバー名", value=guild.name, inline=False)
                    .add_field(name=f"サーバーID", value=str(guild.id), inline=False)
                    .add_field(
                        name=f"理由", value=profile.get("Reason", "なし"), inline=False
                    )
                )
                return
        except:
            return

    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove_log(self, guild: discord.Guild):
        await self.bot.get_channel(1359793645842206912).send(
            embed=discord.Embed(
                title=f"サーバーから退出しました。", color=discord.Color.red()
            )
            .set_thumbnail(url=guild.icon.url if guild.icon else None)
            .add_field(name=f"サーバー名", value=guild.name, inline=False)
            .add_field(name=f"サーバーID", value=str(guild.id), inline=False)
        )

async def setup(bot):
    await bot.add_cog(BotLogCog(bot))
