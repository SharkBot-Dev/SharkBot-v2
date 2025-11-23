from discord.ext import commands
import discord
from discord import app_commands
import re

from models import command_disable

class ModLogSettingView(discord.ui.View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)
        self.channel = None

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], max_values=1, min_values=1, placeholder="ModLogを送信するチャンネルを選択してください。")
    async def modlog_setting(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.channel = select.values[0]
        await interaction.response.send_message(ephemeral=True, content=f"{select.values[0].mention} を選択しました。")

    @discord.ui.button(label="設定する", style=discord.ButtonStyle.green)
    async def modlog_set(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.channel is None:
            return await interaction.response.send_message(ephemeral=True, content="先にチャンネルを選択してください。")

        db = interaction.client.async_db["MainTwo"].AutoModLog
        await db.update_one(
            {"Guild": interaction.guild.id},
            {'$set': {"Guild": interaction.guild.id, 'Channel': self.channel.id}},
            upsert=True,
        )
        await interaction.response.send_message(ephemeral=True, content=f"設定しました。\n次からAutoModのログを {self.channel.mention} に送信します。")

    @discord.ui.button(label="無効化する", style=discord.ButtonStyle.red)
    async def modlog_disable(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = interaction.client.async_db["MainTwo"].AutoModLog
        await db.delete_one(
            {"Guild": interaction.guild.id}
        )
        await interaction.response.send_message(ephemeral=True, content="無効化しました。")

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
        db_automod = self.bot.async_db["Main"].AutoModDetecter
        await db_automod.update_one(
            {"Guild": interaction.guild.id}, 
            {'$set': {"Guild": interaction.guild.id}}, 
            upsert=True
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
            await dbs.update_one(
                {"Guild": interaction.guild.id},
                {'$set': {"Guild": interaction.guild.id}},
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
            await dbs.update_one(
                {"Guild": interaction.guild.id},
                {'$set': {"Guild": interaction.guild.id}},
                upsert=True,
            )
        elif タイプ.value == "slashspam":
            dbs = self.bot.async_db["Main"].UserApplicationSpamBlock
            await dbs.update_one(
                {"Guild": interaction.guild.id},
                {'$set': {"Guild": interaction.guild.id}},
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
            app_commands.Choice(name="カスタムワード", value="customword"),
        ]
    )
    async def automod_delete(
        self, interaction: discord.Interaction, タイプ: app_commands.Choice[str]
    ):
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

        elif タイプ.value == "customword":
            rules = await guild.fetch_automod_rules()
            for r in rules:
                if r.name == "カスタムワード対策":
                    await r.delete()

        await interaction.followup.send(
            ephemeral=True, content=f"AutoModの「{タイプ.name}」を削除しました。"
        )

    @automod.command(name="customword", description="カスタムワードのAutoModを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_customword(
        self, interaction: discord.Interaction
    ):
        db_automod = self.bot.async_db["Main"].AutoModDetecter
        await db_automod.update_one(
            {"Guild": interaction.guild.id}, 
            {'$set': {"Guild": interaction.guild.id}}, 
            upsert=True
        )

        class AddCustomWordModal(discord.ui.Modal, title='カスタムワード追加'): 
            wordinput = discord.ui.TextInput(
                label='カスタムワードの入力',
                placeholder='test, hello, world',
                style=discord.TextStyle.long,
                required=False
            )

            regixinput = discord.ui.TextInput(
                label='正規表現の入力',
                placeholder='discord.gg',
                style=discord.TextStyle.long,
                required=False
            )

            async def on_submit(self, interaction_modal: discord.Interaction):
                try:
                    await interaction_modal.response.defer(ephemeral=True)
                    if self.regixinput.value:
                        await interaction_modal.guild.create_automod_rule(
                            name="カスタム正規表現対策",
                            event_type=discord.AutoModRuleEventType.message_send,
                            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword, regex_patterns=self.regixinput.value.split(", ")),
                            actions=[
                                discord.AutoModRuleAction(
                                    type=discord.AutoModRuleActionType.block_message
                                )
                            ],
                            enabled=True
                        )
                    if self.wordinput.value:
                        await interaction_modal.guild.create_automod_rule(
                            name="カスタムワード対策",
                            event_type=discord.AutoModRuleEventType.message_send,
                            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.keyword, keyword_filter=self.wordinput.value.split(", ")),
                            actions=[
                                discord.AutoModRuleAction(
                                    type=discord.AutoModRuleActionType.block_message
                                )
                            ],
                            enabled=True
                        )
                    await interaction_modal.followup.send(ephemeral=True, content="カスタムワードを追加しました。")
                except:
                    return await interaction_modal.followup.send(ephemeral=True, content="追加に失敗しました。")

        await interaction.response.send_modal(AddCustomWordModal())

    @automod.command(name="modlog", description="AutoModにより処罰された際に発生するログを送信するチャンネルを設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True, manage_channels=True)
    async def automod_moglog(
        self, interaction: discord.Interaction
    ):
        await interaction.response.send_message(ephemeral=True, content="以下のボタンとチャンネル選択バーを使って設定してください。", view=ModLogSettingView())

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModCog(bot))
