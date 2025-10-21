from discord.ext import commands
import discord
import time
import asyncio

class LockMessageEditModal(discord.ui.Modal):
    def __init__(self, msgid: discord.Message):
        super().__init__(title="固定メッセージの修正")
        self.msgid = msgid

        self.title_ = discord.ui.Label(
            text="タイトルを入力",
            description="タイトルを入力してください。",
            component=discord.ui.TextInput(
                style=discord.TextStyle.long, required=True, default=self.msgid.embeds[0].title
            ),
        )
        self.add_item(self.title_)

        self.desc = discord.ui.Label(
            text="説明を入力",
            description="説明を入力してください。",
            component=discord.ui.TextInput(
                style=discord.TextStyle.long, required=True, default=self.msgid.embeds[0].description
            ),
        )
        self.add_item(self.desc)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        assert isinstance(self.title_.component, discord.ui.TextInput)
        assert isinstance(self.desc.component, discord.ui.TextInput)
        
        db = interaction.client.async_db["Main"].LockMessage
        try:
            dbfind = await db.find_one({"Channel": interaction.channel.id}, {"_id": False})
        except Exception:
            return

        if dbfind is None:
            return

        await db.update_one(
                {"Channel": interaction.channel.id, "Guild": interaction.guild.id},
                {"$set": {
                    "Channel": interaction.channel.id,
                    "Guild": interaction.guild.id,
                    "Title": self.title_.component.value,
                    "Desc": self.desc.component.value,
                    "MessageID": self.msgid.id,
                }},
                upsert=True,
            )

        embed = discord.Embed(
            title=self.title_.component.value,
            description=self.desc.component.value,
            color=discord.Color.random(),
        )
        
        await self.msgid.edit(embed=embed)

class LockMessageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.working = set()
        print("init -> LockMessageCog")

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_panel(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if "lockmessage_delete+" == custom_id:
                    if not interaction.user.guild_permissions.manage_channels:
                        return await interaction.response.send_message(ephemeral=True, content="固定メッセージを削除するにはチャンネルの管理権限が必要です。")
                    await interaction.response.defer(ephemeral=True)
                    db = interaction.client.async_db["Main"].LockMessage
                    result = await db.delete_one(
                        {
                            "Channel": interaction.channel.id,
                        }
                    )
                    await interaction.message.delete()
                    await interaction.followup.send(
                        "固定メッセージを削除しました。", ephemeral=True
                    )
                elif "lockmessage_edit+" == custom_id:
                    if not interaction.user.guild_permissions.manage_channels:
                        return await interaction.response.send_message(ephemeral=True, content="固定メッセージを編集するにはチャンネルの管理権限が必要です。")
                    await interaction.response.send_modal(LockMessageEditModal(interaction.message))
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
        except Exception:
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
            view.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.blurple,
                    label="編集",
                    custom_id="lockmessage_edit+",
                )
            )

            embed = discord.Embed(
                title=dbfind.get("Title", "固定メッセージ"),
                description=dbfind.get("Desc", ""),
                color=discord.Color.random(),
            )
            msg = await message.channel.send(embed=embed, view=view)

            await db.update_one(
                {"Channel": message.channel.id, "Guild": message.guild.id},
                {"$set": {
                    "Channel": message.channel.id,
                    "Guild": message.guild.id,
                    "Title": dbfind.get("Title", ""),
                    "Desc": dbfind.get("Desc", ""),
                    "MessageID": msg.id,
                }},
                upsert=True,
            )

        finally:
            self.working.remove(message.channel.id)


async def setup(bot):
    await bot.add_cog(LockMessageCog(bot))
