from discord.ext import commands
import discord
import traceback
import sys
import logging
import time
import asyncio


class LockMessageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.working = set()
        print(f"init -> LockMessageCog")

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_panel(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if "lockmessage_delete+" in custom_id:
                    await interaction.response.defer(ephemeral=True)
                    if not interaction.user.guild_permissions.manage_channels:
                        return
                    db = interaction.client.async_db["Main"].LockMessage
                    result = await db.delete_one(
                        {
                            "Channel": interaction.channel.id,
                        }
                    )
                    await interaction.message.delete()
                    await interaction.followup.send(
                        "LockMessageを削除しました。", ephemeral=True
                    )
        except:
            return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if "!." in message.content:
            return

        user_id = message.author.id
        db = self.bot.async_db["Main"].LockMessage
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except Exception as e:
            return

        if dbfind is None:
            return
        if message.channel.id in self.working:
            return

        self.working.add(message.channel.id)

        try:
            if (
                time.time()
                - discord.Object(id=dbfind["MessageID"]).created_at.timestamp()
                < 10
            ):
                return
            await asyncio.sleep(5)

            try:
                await discord.PartialMessage(
                    channel=message.channel, id=dbfind["MessageID"]
                ).delete()
            except discord.NotFound:
                pass

            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.red,
                    label="削除",
                    custom_id="lockmessage_delete+",
                )
            )

            embed = discord.Embed(
                title=dbfind.get("Title", "固定メッセージ"),
                description=dbfind.get("Desc", ""),
                color=discord.Color.random(),
            )
            msg = await message.channel.send(embed=embed, view=view)

            await db.replace_one(
                {"Channel": message.channel.id, "Guild": message.guild.id},
                {
                    "Channel": message.channel.id,
                    "Guild": message.guild.id,
                    "Title": dbfind.get("Title", ""),
                    "Desc": dbfind.get("Desc", ""),
                    "MessageID": msg.id,
                },
                upsert=True,
            )

        finally:
            self.working.remove(message.channel.id)


async def setup(bot):
    await bot.add_cog(LockMessageCog(bot))
