import discord


async def quest_clear(interaction: discord.Interaction, qid: str) -> bool:
    db = interaction.client.async_db["Main"].BotQuest

    dbfind = await db.find_one({"User": interaction.user.id}, {"_id": False})
    if dbfind is None:
        return False

    quest = dbfind.get("Quest")
    if not quest:
        return False

    quest_text = quest.get(qid) if isinstance(quest, dict) else str(quest)

    await db.delete_one({"User": interaction.user.id})

    embed = discord.Embed(
        title="クエストをクリアしました！",
        description=f"```{quest_text}```\nをクリアしたよ！",
        color=discord.Color.green(),
    )
    await interaction.channel.send(embed=embed)

    return True
