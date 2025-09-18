import discord

async def quest_clear(interaction: discord.Interaction, qid: str) -> str:
    db = interaction.client.async_db["Main"].BotQuest

    dbfind = await db.find_one({"User": interaction.user.id, "Quest": qid}, {"_id": False})

    if dbfind is None:
        return False

    quest = dbfind.get("Quest")

    await db.delete_one({"User": interaction.user.id})

    await interaction.channel.send(embed=discord.Embed(title="クエストをクリアしました！", description=f"```{quest}```\nをクリアしたよ！", color=discord.Color.green()))

    return True