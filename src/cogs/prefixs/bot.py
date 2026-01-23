from discord.ext import commands
import discord
from models import command_disable, make_embed


class Prefixs_BotCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> Prefixs_BotCog")

    @commands.command(name="ping", description="Pingを測定します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def ping_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname(
            "bot ping", ctx.guild
        ):
            return

        embed = make_embed.success_embed(
            title="Pingを測定しました。",
            description=f"DiscordAPI: {round(self.bot.latency * 1000)}ms",
        )
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Prefixs_BotCog(bot))
