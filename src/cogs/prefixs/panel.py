from discord.ext import commands
import discord
from models import command_disable, make_embed


class Prefixs_PanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> Prefixs_PanelCog")

    @commands.group(name="rolepanel", description="ロールパネル関連のコマンドです。", aliases=["rp", "rr"])
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_panel(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            await ctx.reply(
                embed=make_embed.success_embed(
                    title="ロールパネルのヘルプ"
                ).add_field(
                    name="!.rp create",
                    value="ロールパネルを作成します。",
                    inline=False,
                ).add_field(
                    name="!.rp add",
                    value="ロールパネルからロールを追加します。",
                    inline=False,
                ).add_field(
                    name="!.rp remove",
                    value="ロールパネルからロールを削除します。",
                    inline=False,
                )
            )
        return

    @role_panel.command(name="create", description="ロールパネルを作成します。", aliases=["c"])
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def rp_create(self, ctx: commands.Context, role: discord.Role, title: str = "役職パネル", *, description: str = "以下のボタンを押してロールを取得します。", show_role: bool = True):
        if not await command_disable.command_enabled_check_by_cmdname(
            "panel role", ctx.guild
        ):
            return

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label=role.name, custom_id=f"rolepanel_v1+{role.id}"
            )
        )

        embed = discord.Embed(
            title=title, description=description, color=discord.Color.green()
        )
        if show_role:
            embed.add_field(name="ロール一覧", value=role.mention)
        await ctx.channel.send(embed=embed, view=view)
        await ctx.message.add_reaction("✅")

    @role_panel.command(name="add", description="ロールパネルにロールを追加します。", aliases=["a"])
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def rp_add(self, ctx: commands.Context, msgid: str, role: discord.Role):
        if not await command_disable.command_enabled_check_by_cmdname(
            "panel role-edit", ctx.guild
        ):
            return
        try:
            msgid = int(msgid)
        except ValueError:
            return await ctx.reply(embed=make_embed.error_embed(title="メッセージidが不明です。", description="正しいメッセージidを指定してください。"))
        try:
            msg = await ctx.channel.fetch_message(
                msgid
            )
        except:
            return await ctx.reply(embed=make_embed.error_embed(title="メッセージが見つかりません。", description="正しいメッセージidを指定してください。"))
        
        view = discord.ui.View()
        for action_row in msg.components:
            for v in action_row.children:
                if isinstance(v, discord.Button):
                    view.add_item(
                        discord.ui.Button(label=v.label, custom_id=v.custom_id)
                    )

        view.add_item(
            discord.ui.Button(
                label=role.name, custom_id=f"rolepanel_v1+{role.id}"
            )
        )

        embed = msg.embeds[0]

        if embed.fields:
            field_value = embed.fields[0].value or ""

            field_value += f"\n{role.mention}"
            new_embed = embed.copy()
            new_embed.set_field_at(
                0,
                name=embed.fields[0].name,
                value=field_value,
                inline=embed.fields[0].inline,
            )

            await msg.edit(view=view, embeds=[new_embed])
        else:
            pass

        await ctx.message.add_reaction("✅")

    @role_panel.command(name="remove", description="ロールパネルからロールを削除します。", aliases=["r"])
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def rp_remove(self, ctx: commands.Context, msgid: str, role: discord.Role):
        if not await command_disable.command_enabled_check_by_cmdname(
            "panel role-edit", ctx.guild
        ):
            return
        try:
            msgid = int(msgid)
        except ValueError:
            return await ctx.reply(embed=make_embed.error_embed(title="メッセージidが不明です。", description="正しいメッセージidを指定してください。"))
        try:
            msg = await ctx.channel.fetch_message(
                msgid
            )
        except:
            return await ctx.reply(embed=make_embed.error_embed(title="メッセージが見つかりません。", description="正しいメッセージidを指定してください。"))
        
        view = discord.ui.View()
        for action_row in msg.components:
            for v in action_row.children:
                if isinstance(v, discord.Button):
                    view.add_item(
                        discord.ui.Button(label=v.label, custom_id=v.custom_id)
                    )

        view = discord.ui.View()
        for action_row in msg.components:
            for v in action_row.children:
                if isinstance(v, discord.Button):
                    if not v.label == role.name:
                        view.add_item(
                            discord.ui.Button(label=v.label, custom_id=v.custom_id)
                        )

        embed = msg.embeds[0]

        if embed.fields:
            field_value = embed.fields[0].value or ""

            field_value = (
                field_value.replace(f"\n{role.mention}", "")
                .replace(f"{role.mention}\n", "")
                .replace(f"{role.mention}", "")
            )

            new_embed = embed.copy()
            new_embed.set_field_at(
                0,
                name=embed.fields[0].name,
                value=field_value,
                inline=embed.fields[0].inline,
            )

            await msg.edit(view=view, embeds=[new_embed])
        else:
            pass
        await ctx.message.add_reaction("✅")

async def setup(bot):
    await bot.add_cog(Prefixs_PanelCog(bot))
