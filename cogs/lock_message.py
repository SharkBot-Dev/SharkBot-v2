from discord.ext import commands
import discord
import time
import asyncio

from datetime import datetime, timezone

SERVICE_NAME = {
    "disboard": "Disboard",
    "dissoku": "Dissoku",
    "discafe": "DISCafé",
    "discadia": "Discadia",
    "dicoall": "Dicoall",
    "distopia": "Distopia",
    "sabachan": "SabaChannel",
}

class LockMessageEditModal(discord.ui.Modal):
    def __init__(self, msgid: discord.Message):
        super().__init__(title="固定メッセージの修正")
        self.msgid = msgid

        self.title_ = discord.ui.Label(
            text="タイトルを入力",
            description="タイトルを入力してください。",
            component=discord.ui.TextInput(
                style=discord.TextStyle.long,
                required=True,
                default=self.msgid.embeds[0].title,
            ),
        )
        self.add_item(self.title_)

        self.desc = discord.ui.Label(
            text="説明を入力",
            description="説明を入力してください。",
            component=discord.ui.TextInput(
                style=discord.TextStyle.long,
                required=True,
                default=self.msgid.embeds[0].description,
            ),
        )
        self.add_item(self.desc)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        assert isinstance(self.title_.component, discord.ui.TextInput)
        assert isinstance(self.desc.component, discord.ui.TextInput)

        db = interaction.client.async_db["Main"].LockMessage
        try:
            dbfind = await db.find_one(
                {"Channel": interaction.channel.id}, {"_id": False}
            )
        except Exception:
            return

        if dbfind is None:
            return

        await db.update_one(
            {"Channel": interaction.channel.id, "Guild": interaction.guild.id},
            {
                "$set": {
                    "Channel": interaction.channel.id,
                    "Guild": interaction.guild.id,
                    "Title": self.title_.component.value,
                    "Desc": self.desc.component.value,
                    "MessageID": self.msgid.id,
                }
            },
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

    async def get_bump_status_embed(self, message: discord.Message):
        now = datetime.now()
        db_main = self.bot.async_db["Main"]
        db_maintwo = self.bot.async_db["MainTwo"]

        services = {
            "Dicoall": "dicoall",
            "Distopia": "distopia",
            "SabaChannel": "sabachan",
            "DissokuChannel": "dissoku",
            "DisboardChannel": "disboard",
            "DiscafeChannel": "discafe",
            "DisCadiaChannel": "discadia",
            "SharkBotChannel": "sharkbot"
        }

        services_to_slash = {
            "dicoall": "</up:935190259111706754>",
            "distopia": "</bump:1309070135360749620>",
            "sabachan": "</vote:1233256792507682860>",
            "dissoku": "</up:1363739182672904354>",
            "disboard": "</bump:947088344167366698>",
            "discafe": "</up:980136954169536525>",
            "discadia": "</bump:1225075208394768496>",
            "sharkbot": "</global up:1408658655532023855>"
        }

        services_name = {
            "dicoall": "Dicoall",
            "distopia": "Distopia",
            "sabachan": "鯖チャンネル",
            "dissoku": "ディス速",
            "disboard": "ディスボード",
            "discafe": "DCafe",
            "discadia": "Discadia",
            "sharkbot": "SharkBot"
        }

        alert_db = db_main["AlertQueue"]

        async def find_channel(collection):
            try:
                data = await collection.find_one(
                    {"Channel": message.channel.id},
                    {"_id": False}
                )
                return data or False
            except Exception:
                return False

        possible = []      # Bump可能
        cooldown = []      # クールタイム中
        disabled = []      # 未設定

        for db_name, service_id in services.items():
            collection = db_main[db_name]
            config = await find_channel(collection)

            if not config:
                disabled.append(service_id)
                continue

            exists = await alert_db.find_one({
                "Channel": message.channel.id,
                "ID": service_id,
                "NotifyAt": {"$gt": now}
            })

            if exists:
                remaining = exists["NotifyAt"] - now
                minutes = remaining.seconds // 60
                seconds = remaining.seconds % 60
                cooldown.append(f"{services_name.get(service_id)} （あと {minutes}分{seconds}秒）")
            else:
                possible.append(f"{services_name.get(service_id)} {services_to_slash.get(service_id, 'スラッシュコマンド取得失敗')}")

        collection = db_maintwo["SharkBotChannel"]
        config = await find_channel(collection)
        if config:
                

            exists = await alert_db.find_one({
                "Channel": message.channel.id,
                "ID": "sharkbot",
                "NotifyAt": {"$gt": now}
            })

            if exists:
                remaining = exists["NotifyAt"] - now
                minutes = remaining.seconds // 60
                seconds = remaining.seconds % 60
                cooldown.append(f"Sharkbot （あと {minutes}分{seconds}秒）")
            else:
                possible.append(f"Sharkbot {services_to_slash.get('sharkbot', 'スラッシュコマンド取得失敗')}")

        embed = discord.Embed(
            title="Bump 状況一覧",
            description="🟢 Bump可能:\n{}\n\n🟡 クールダウン中:\n{}".format("\n".join(possible) if possible else "なし", "\n".join(cooldown) if cooldown else "なし"),
            color=discord.Color.green()
        )

        return embed

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
                        return await interaction.response.send_message(
                            ephemeral=True,
                            content="固定メッセージを削除するにはチャンネルの管理権限が必要です。",
                        )
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
                        return await interaction.response.send_message(
                            ephemeral=True,
                            content="固定メッセージを編集するにはチャンネルの管理権限が必要です。",
                        )
                    await interaction.response.send_modal(
                        LockMessageEditModal(interaction.message)
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

            service = dbfind.get('Service')

            if service is None:

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
                    {
                        "$set": {
                            "Channel": message.channel.id,
                            "Guild": message.guild.id,
                            "Title": dbfind.get("Title", ""),
                            "Desc": dbfind.get("Desc", ""),
                            "MessageID": msg.id,
                        }
                    },
                    upsert=True,
                )
            elif service == "bump_pin":
                em = await self.get_bump_status_embed(message)
                msg = await message.channel.send(embed=em, view=view)

                await db.update_one(
                    {"Channel": message.channel.id, "Guild": message.guild.id},
                    {
                        "$set": {
                            "Channel": message.channel.id,
                            "Guild": message.guild.id,
                            "Title": em.title,
                            "Desc": em.description,
                            "MessageID": msg.id,
                        }
                    },
                    upsert=True,
                )

        finally:
            self.working.remove(message.channel.id)


async def setup(bot):
    await bot.add_cog(LockMessageCog(bot))
