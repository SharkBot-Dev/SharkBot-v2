from discord.ext import commands
import discord
from discord import app_commands


class CountCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> CountCog")

    async def get_counting_setting(self, message: discord.Message):
        db_settings = self.bot.async_db["Main"].CountingSettings
        try:
            dbfind = await db_settings.find_one(
                {"Channel": message.channel.id}, {"_id": False}
            )
        except:
            return {"Reset": False}
        if dbfind is None:
            return {"Reset": False}
        if dbfind.get("Reset", "no") == "yes":
            return {"Reset": True}
        else:
            return {"Reset": False}

    @commands.Cog.listener("on_message")
    async def on_message_count(self, message: discord.Message):
        if message.author.bot:
            return

        db = self.bot.async_db["Main"].Counting
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        try:
            if dbfind.get("Now", 0) + 1 != int(message.content):
                reset = await self.get_counting_setting(message)
                if reset.get("Reset") == False:
                    if not dbfind.get("Now", 0) + 1 == 1:
                        await message.reply(
                            embed=discord.Embed(
                                title="カウントに失敗しました・・",
                                description="1から数えなおそう！",
                                color=discord.Color.red(),
                            )
                        )
                    await db.update_one(
                        {"Guild": message.guild.id, "Channel": message.channel.id},
                        {
                            "$set": {
                                "Guild": message.guild.id,
                                "Channel": message.channel.id,
                                "Now": 0,
                            }
                        },
                        upsert=True,
                    )
                    return
                else:
                    await message.reply(
                        embed=discord.Embed(
                            title="カウントに失敗しました・・",
                            description="気にしないで！\n続きから数えよう！",
                            color=discord.Color.red(),
                        )
                    )
                    return

            await db.update_one(
                {"Channel": message.channel.id}, {"$inc": {"Now": 1}}, upsert=True
            )

            await message.add_reaction("✅")
        except:
            return

    count = app_commands.Group(
        name="count", description="カウントゲーム関連のコマンドです。"
    )

    @count.command(name="setup", description="カウントゲームをセットアップします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def count_setup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        db = self.bot.async_db["Main"].Counting
        await db.update_one(
            {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "Now": 0,
                }
            },
            upsert=True,
        )
        await interaction.channel.send(
            embed=discord.Embed(
                title="カウントをセットアップしました。",
                description="1から数えてみよう！",
                color=discord.Color.green(),
            )
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="カウントをセットアップしました。", color=discord.Color.green()
            )
        )

    @count.command(name="disable", description="カウントゲームを終了します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def count_disable(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        db = self.bot.async_db["Main"].Counting
        result = await db.delete_one({"Channel": interaction.channel.id})
        if result.deleted_count == 0:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="このチャンネルではカウントは有効ではありません。",
                    color=discord.Color.red(),
                )
            )
        return await interaction.followup.send(
            embed=discord.Embed(
                title="カウントを無効化しました。", color=discord.Color.red()
            )
        )

    @count.command(name="skip", description="カウントゲームの現在の数字を設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def count_skip(self, interaction: discord.Interaction, 数字: int):
        await interaction.followup.defer()
        db = self.bot.async_db["Main"].Counting
        try:
            dbfind = await db.find_one(
                {"Channel": interaction.channel.id}, {"_id": False}
            )
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="このチャンネルではカウントは有効ではありません。",
                    color=discord.Color.red(),
                )
            )
        if dbfind is None:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="このチャンネルではカウントは有効ではありません。",
                    color=discord.Color.red(),
                )
            )
        await db.update_one(
            {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "Now": 数字,
                }
            },
            upsert=True,
        )
        return await interaction.followup.send(
            embed=discord.Embed(
                title="カウントゲームの現在の数字を変更しました。",
                description=f"次は{数字 + 1}からカウントしましょう！",
                color=discord.Color.green(),
            )
        )

    @count.command(name="reset", description="カウントゲームをリセットします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def count_reset(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].Counting
        try:
            dbfind = await db.find_one(
                {"Channel": interaction.channel.id}, {"_id": False}
            )
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="このチャンネルではカウントは有効ではありません。",
                    color=discord.Color.red(),
                )
            )
        if dbfind is None:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="このチャンネルではカウントは有効ではありません。",
                    color=discord.Color.red(),
                )
            )
        await db.update_one(
            {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "Now": 0,
                }
            },
            upsert=True,
        )
        return await interaction.followup.send(
            embed=discord.Embed(
                title="カウントゲームの現在の数字をリセットしました。",
                description="次は1からカウントしましょう！",
                color=discord.Color.green(),
            )
        )


async def setup(bot):
    await bot.add_cog(CountCog(bot))
