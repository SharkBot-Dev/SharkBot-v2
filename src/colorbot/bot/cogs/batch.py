from discord.ext import commands, tasks
import discord


class BatchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> BatchCog")

    async def reset_db(self):
        await self.bot.async_db.TTSCheckBeta.delete_many({})
        print("読み上げをリセットしました。")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.reset_db()
        self.loop_pres.start()

    @tasks.loop(seconds=10)
    async def loop_pres(self):
        try:
            await self.bot.change_presence(
                activity=discord.CustomActivity(
                    name=f"/help | {len(self.bot.guilds)}鯖 | {self.bot.shard_count}Shard | {round(self.bot.latency * 1000)}ms"
                )
            )
        except:
            pass


async def setup(bot):
    await bot.add_cog(BatchCog(bot))
