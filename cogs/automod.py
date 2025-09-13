from discord.ext import commands
import discord
from discord import app_commands
import re

from models import command_disable


class AutoModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AutoModCog")

    automod = app_commands.Group(
        name="automod", description="AutoMod管理のコマンドです。"
    )

    @automod.command(name="create", description="AutoModを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(
        タイプ=[
            app_commands.Choice(name="招待リンク", value="invite"),
            app_commands.Choice(name="Token", value="token"),
            app_commands.Choice(name="Everyoneとhere", value="everyone"),
            app_commands.Choice(name="メールアドレス", value="mail"),
            app_commands.Choice(name="メッセージスパム", value="spam"),
            app_commands.Choice(name="スラッシュコマンドスパム", value="slashspam"),
        ]
    )
    async def automod_create(
        self, interaction: discord.Interaction, タイプ: app_commands.Choice[str]
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer(ephemeral=True)
        if タイプ.value == "invite":
            await interaction.guild.create_automod_rule(
                name="招待リンク対策",
                event_type=discord.AutoModRuleEventType.message_send,
                trigger=discord.AutoModTrigger(
                    type=discord.AutoModRuleTriggerType.keyword,
                    regex_patterns=[
                        r"(discord\.(gg|com/invite|app\.com/invite)[/\\][\w-]+)",
                        r"\b\<(\n*)?h(\n*)?t(\n*)?t(\n*)?p(\n*)?s?(\n*)?:(\n*)?\/(\n*)?\/(\n*)?(([dｄⓓᵈᴰⅮ𝒹ⅾⅮ𝔻𝕕%％𝓓]{1,}|[^\p{sc=latin}]*)(\n*)([iｉⓘsｓⓢ𝖎𝖘ɪꜱᴵⁱˢ𝓘𝓢\n]{1,}|[\p{sc=latin}\n]*)([\p{sc=latin}\nº]*|[^\p{sc=latin}\n]*)[\/\\](\n*)[^\s]*)+\b",
                    ],
                ),
                actions=[
                    discord.AutoModRuleAction(
                        type=discord.AutoModRuleActionType.block_message
                    )
                ],
                enabled=True,
            )
        elif タイプ.value == "token":
            dbs = self.bot.async_db["Main"].TokenBlock
            await dbs.replace_one(
                {"Guild": interaction.guild.id},
                {"Guild": interaction.guild.id},
                upsert=True,
            )
        elif タイプ.value == "everyone":
            await interaction.guild.create_automod_rule(
                name="Everyone対策",
                event_type=discord.AutoModRuleEventType.message_send,
                trigger=discord.AutoModTrigger(
                    type=discord.AutoModRuleTriggerType.keyword,
                    regex_patterns=[r"@everyone", r"@here"],
                ),
                actions=[
                    discord.AutoModRuleAction(
                        type=discord.AutoModRuleActionType.block_message
                    )
                ],
                enabled=True,
            )
        elif タイプ.value == "mail":
            await interaction.guild.create_automod_rule(
                name="メールアドレス対策",
                event_type=discord.AutoModRuleEventType.message_send,
                trigger=discord.AutoModTrigger(
                    type=discord.AutoModRuleTriggerType.keyword,
                    regex_patterns=[
                        r"^[a-zA-Z0-9_+-]+(.[a-zA-Z0-9_+-]+)*@([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.)+[a-zA-Z]{2,}$"
                    ],
                ),
                actions=[
                    discord.AutoModRuleAction(
                        type=discord.AutoModRuleActionType.block_message
                    )
                ],
                enabled=True,
            )
        elif タイプ.value == "spam":
            dbs = self.bot.async_db["Main"].SpamBlock
            await dbs.replace_one(
                {"Guild": interaction.guild.id},
                {"Guild": interaction.guild.id},
                upsert=True,
            )
        elif タイプ.value == "slashspam":
            dbs = self.bot.async_db["Main"].UserApplicationSpamBlock
            await dbs.replace_one(
                {"Guild": interaction.guild.id},
                {"Guild": interaction.guild.id},
                upsert=True,
            )
        await interaction.followup.send(
            ephemeral=True, content=f"AutoModの「{タイプ.name}」を作成しました。"
        )

    @automod.command(name="delete", description="Automodを削除します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(
        タイプ=[
            app_commands.Choice(name="招待リンク", value="invite"),
            app_commands.Choice(name="Token", value="token"),
            app_commands.Choice(name="Everyoneとhere", value="everyone"),
            app_commands.Choice(name="メールアドレス", value="mail"),
            app_commands.Choice(name="メッセージスパム", value="spam"),
            app_commands.Choice(name="スラッシュコマンドスパム", value="slashspam"),
        ]
    )
    async def automod_delete(
        self, interaction: discord.Interaction, タイプ: app_commands.Choice[str]
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        db = self.bot.async_db["Main"]

        if タイプ.value == "invite":
            await db.InviteBlock.delete_one({"Guild": guild.id})
            rules = await guild.fetch_automod_rules()
            for r in rules:
                if r.name == "招待リンク対策":
                    await r.delete()

        elif タイプ.value == "token":
            await db.TokenBlock.delete_one({"Guild": guild.id})

        elif タイプ.value == "everyone":
            rules = await guild.fetch_automod_rules()
            for r in rules:
                if r.name == "Everyone対策":
                    await r.delete()

        elif タイプ.value == "mail":
            rules = await guild.fetch_automod_rules()
            for r in rules:
                if r.name == "メールアドレス対策":
                    await r.delete()

        elif タイプ.value == "spam":
            await db.SpamBlock.delete_one({"Guild": guild.id})

        elif タイプ.value == "slashspam":
            await db.UserApplicationSpamBlock.delete_one({"Guild": guild.id})

        await interaction.followup.send(
            ephemeral=True, content=f"AutoModの「{タイプ.name}」を削除しました。"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModCog(bot))
