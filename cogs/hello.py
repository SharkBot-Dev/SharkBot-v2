from discord.ext import commands, tasks
import discord
from datetime import datetime, time, timezone, timedelta

class HelloCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_goodmorning_alert.start()
        print("init -> HelloCog")

    async def get_mention(self, guild: discord.Guild, channel_id: int):
        db = self.bot.async_db["Main"].AlertMention
        try:
            dbfind = await db.find_one({"Channel": channel_id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return guild.get_role(dbfind.get("Role")).mention

    @tasks.loop(time=time(hour=8, minute=0, tzinfo=timezone(timedelta(hours=9))))
    async def check_goodmorning_alert(self):
        now = datetime.now().strftime('%Y年%m月%d日')

        news_db = self.bot.async_db["Main"].GoodMorningChannel
        async for n in news_db.find({}):
            guild = self.bot.get_guild(n.get('Guild', 0))
            if not guild:
                continue

            channel = guild.get_channel(n.get('Channel', 0))
            if not channel:
                continue

            embed = (
                discord.Embed(
                    title="おはようございます！",
                    description=f"今日は 「{now}」 です。",
                    color=discord.Color.green()
                )
                .add_field(name="今日のメンバー数", value=f"{guild.member_count}人", inline=False)
                .add_field(name="今日のチャンネル数", value=f"{len(guild.channels)}個", inline=False)
                .add_field(name="今日のロール数", value=f"{len(guild.roles)}個", inline=False)
            )

            mention = await self.get_mention(guild, channel.id)

            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            await channel.send(embed=embed, content=mention)

    async def cog_unload(self):
        self.check_goodmorning_alert.stop()

async def setup(bot):
    await bot.add_cog(HelloCog(bot))
