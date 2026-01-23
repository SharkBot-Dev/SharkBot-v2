from discord.ext import commands
import discord
from discord import app_commands
from models import make_embed, help_views

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> HelpCog")

    @app_commands.command(name="help", description="ヘルプを表示します")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def help(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.defer()
        view = help_views.HelpView(self.bot, user_=interaction.user)
        await interaction.followup.send(view=view, embed=await view.build_embed())

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
