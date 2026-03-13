from discord.ext import commands
import discord
from models import command_disable, make_embed
import time
import aiohttp

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
        
        discord_api_start_time = time.perf_counter()
        msg = await ctx.reply(embed=make_embed.loading_embed("計測しています..."))
        discord_api_end_time = time.perf_counter()

        discord_latency_ms = (discord_api_end_time - discord_api_start_time) * 1000
        ws_latency_ms = self.bot.latency * 1000

        embed = make_embed.success_embed(
            title="Pingを測定しました。",
            description=(
                f"**Discord API:** {discord_latency_ms:.2f}ms\n"
                f"**Discord WS:** {ws_latency_ms:.2f}ms"
            ),
        )
        await msg.edit(embed=embed)


async def setup(bot):
    await bot.add_cog(Prefixs_BotCog(bot))
