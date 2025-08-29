import traceback
from discord.ext import commands, tasks
import discord
import datetime
import random
from models import permissions_text

class FreeChannelModal(discord.ui.Modal):
    def __init__(self, msgid: int):
        super().__init__(title='チャンネルを作成', timeout=180)
        self.msgid = msgid

    channelname = discord.ui.Label(
        text='チャンネル名を入力',
        description='チャンネル名を入力してください。',
        component=discord.ui.TextInput(
            style=discord.TextStyle.short,
            max_length=15,
            required=True
        ),
    )

    channeltype = discord.ui.Label(
        text='チャンネルタイプを選択',
        description='どのチャンネルを作成するかを選択してください。',
        component=discord.ui.Select(
            options=[
                discord.SelectOption(label='テキストチャンネル', value='text'),
                discord.SelectOption(label='NSFWテキストチャンネル', value='nsfwtext'),
            ],
            required=True,
            max_values=1
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        assert isinstance(self.channeltype.component, discord.ui.Select)
        assert isinstance(self.channelname.component, discord.ui.TextInput)

        db = interaction.client.async_db["Main"].FreeChannelCategory
        try:
            dbfind = await db.find_one({"Message": self.msgid}, {"_id": False})
        except:
            return
        nsfw = False if self.channeltype.component.values[0] == "text" else True
        if dbfind is None:
            if interaction.channel.category:
                    
                channel = await interaction.channel.category.create_text_channel(name=self.channelname.component.value, nsfw=nsfw)
            else:
                channel = await interaction.guild.create_text_channel(name=self.channelname.component.value, nsfw=nsfw)
        else:
            ch = interaction.guild.get_channel(dbfind.get("Channel", 0))
            if type(ch) == discord.CategoryChannel:
                channel = await ch.create_text_channel(name=self.channelname.component.value, nsfw=nsfw)
            else:
                return
        await channel.send(f"{interaction.user.mention}: フリーチャンネルを作成しました。")

class FreeChannelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_freechannel(self, interaction: discord.Interaction):
        try:
            if interaction.data['component_type'] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id.startswith("freechannel_"):
                    await interaction.response.send_modal(FreeChannelModal(interaction.message.id))
        except:
            return

async def setup(bot):
    await bot.add_cog(FreeChannelCog(bot))