from discord.ext import commands, tasks
import discord
import datetime
import random

from models import save_commands


class BatchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> BatchCog")

    async def reset_db(self):
        await self.bot.async_db.Main.TTSCheckBeta.delete_many({})
        print("読み上げをリセットしました。")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.reset_db()
        for cmd in self.bot.tree.get_commands():
            await save_commands.save_command(cmd)
        await self.bot.get_channel(1349646266379927594).send(
            embed=discord.Embed(
                title="Botが起動しました。", color=discord.Color.green()
            )
            .set_footer(text="SharkBot", icon_url=self.bot.user.avatar.url)
            .add_field(name="導入サーバー数", value=f"{len(self.bot.guilds)}サーバー")
        )
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
