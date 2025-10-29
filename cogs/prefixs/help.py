import io
from discord.ext import commands
import discord
from consts import settings
from discord import app_commands
from models import command_disable, make_embed
import aiohttp

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
        
class Prefixs_HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> Prefixs_HelpCog")

    @commands.command(name="help", aliases=["h"], description="頭文字用ヘルプを表示します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def help_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname("help", ctx.guild):
            return
        
        ems = []

        for start in range(0, len(list(self.bot.commands)), 10):
            embed = make_embed.success_embed(title="SharkBotのヘルプ (頭文字バージョン)", description="頭文字バージョンです。\nスラッシュコマンド用ヘルプは、\n`/help`を使用してください。\n\nちなみに、頭文字コマンドは、\n`[頭文字]コマンド名`と送信することで機能します。\n\n標準頭文字: `!.`")
            
            embed.add_field(name="コマンド一覧", value="以下がコマンド一覧です。\n下のボタンでページを切り替えられます。", inline=False)
            
            for cmd in list(self.bot.commands)[start : start + 10]:
                if "load" in cmd.name:
                    continue
                if "jishaku" in cmd.name:
                    continue
                if "sync_slash" == cmd.name:
                    continue
                if "save" == cmd.name:
                    continue

                al = ', '.join(cmd.aliases)
                embed.add_field(name=cmd.name, value=cmd.description + f"\n別名: " + al if al else "なし", inline=False)

            ems.append(embed)

        c = 1
        for e in ems:
            if type(e) != discord.Embed:
                continue
            e.set_footer(text=f"{c} / {len(ems)}")
            c += 1

        await ctx.reply(embed=ems[0], view=Paginator(ems))

    @commands.command(name="dashboard", aliases=["d"], description="ダッシュボードの案内を表示します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def dashboard_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname("dashboard", ctx.guild):
            return
        
        await ctx.reply(f"現在はダッシュボードにアクセスできません。")

    @commands.command(name="source", aliases=["so"], description="Botのソースコードを表示します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def source_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname("help", ctx.guild):
            return
        
        base_url = "https://github.com/SharkBot-Dev/SharkBot-v2"

        await ctx.reply(base_url)

    @commands.command(name="aliases", aliases=["a"], description="頭文字コマンドの別名からコマンドを検索します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def aliases_prefix(self, ctx: commands.Context, aliases: str):
        if not await command_disable.command_enabled_check_by_cmdname("help", ctx.guild):
            return
        
        command = self.bot.commands
        for c in command:
            if aliases in list(c.aliases):
                return await ctx.reply(embed=make_embed.success_embed(title=f"{c.name} を発見しました。")
                                       .add_field(name="コマンド名", value=c.name, inline=False)
                                       .add_field(name="説明", value=c.description, inline=False)
                                       .add_field(name="ほかの別名", value=", ".join(list(c.aliases))))
            
        await ctx.reply(embed=make_embed.error_embed(title="コマンドが見つかりませんでした。", description="ヘルプコマンドで正しい別名を確認してください。"))

async def setup(bot):
    await bot.add_cog(Prefixs_HelpCog(bot))
