import io
from discord.ext import commands
import discord
from consts import settings
from discord import app_commands
from models import command_disable, make_embed, pages
import aiohttp


class Prefixs_HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> Prefixs_HelpCog")

    @commands.command(
        name="help", aliases=["h"], description="頭文字用ヘルプを表示します。"
    )
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def help_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname(
            "help", ctx.guild
        ):
            return

        ems = []

        for start in range(0, len(list(self.bot.commands)), 20):
            embed = make_embed.success_embed(
                title="SharkBotのヘルプ (頭文字バージョン)"
            )

            embed.add_field(
                name="コマンド一覧",
                value="以下がコマンド一覧です。\n下のボタンでページを切り替えられます。",
                inline=False,
            )

            for cmd in list(self.bot.commands)[start : start + 20]:
                if "load" in cmd.name:
                    continue
                if "jishaku" in cmd.name:
                    continue
                if "sync_slash" == cmd.name:
                    continue
                if "save" == cmd.name:
                    continue
                if "task" == cmd.name:
                    continue
                if "send" == cmd.name:
                    continue

                al = ", ".join(cmd.aliases)

                al = al if al else "なし"

                embed.add_field(name=cmd.name, value=cmd.description + f"\n別名: " + al)

            ems.append(embed)

        c = 1
        for e in ems:
            if type(e) != discord.Embed:
                continue
            e.set_footer(text=f"{c} / {len(ems)}")
            c += 1

        await ctx.reply(
            embed=ems[0],
            view=pages.Pages(embeds=ems, now_page=0, page_owner=ctx.author),
        )

    @commands.command(
        name="dashboard",
        aliases=["d"],
        description="ダッシュボードの案内を表示します。",
    )
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def dashboard_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname(
            "dashboard", ctx.guild
        ):
            return

        await ctx.reply(f"現在はダッシュボードにアクセスできません。")

    @commands.command(
        name="source", aliases=["so"], description="Botのソースコードを表示します。"
    )
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def source_prefix(self, ctx: commands.Context):
        if not await command_disable.command_enabled_check_by_cmdname(
            "help", ctx.guild
        ):
            return

        base_url = "https://github.com/SharkBot-Dev/SharkBot-v2"

        await ctx.reply(base_url)

    @commands.command(
        name="aliases",
        aliases=["a"],
        description="頭文字コマンドの別名からコマンドを検索します。",
    )
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    async def aliases_prefix(self, ctx: commands.Context, aliases: str):
        if not await command_disable.command_enabled_check_by_cmdname(
            "help", ctx.guild
        ):
            return

        command = self.bot.commands
        for c in command:
            if aliases in list(c.aliases):
                return await ctx.reply(
                    embed=make_embed.success_embed(title=f"{c.name} を発見しました。")
                    .add_field(name="コマンド名", value=c.name, inline=False)
                    .add_field(name="説明", value=c.description, inline=False)
                    .add_field(name="ほかの別名", value=", ".join(list(c.aliases)))
                )

        await ctx.reply(
            embed=make_embed.error_embed(
                title="コマンドが見つかりませんでした。",
                description="ヘルプコマンドで正しい別名を確認してください。",
            )
        )


async def setup(bot):
    await bot.add_cog(Prefixs_HelpCog(bot))
