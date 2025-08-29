import discord
from discord.ext import commands
from consts import mongodb
from discord import app_commands

async def save_command(cmd: app_commands.Command, parent: str = None):
    full_name = f"{parent} {cmd.name}" if parent else cmd.name

    if isinstance(cmd, app_commands.Group):
        for sub in cmd.commands:
            await save_command(sub, parent=full_name)
    else:

        if not isinstance(cmd, app_commands.ContextMenu):

            doc = {
                "name": full_name,
                "description": cmd.description or "",
            }
            await mongodb.mongo["DashboardBot"].Commands.replace_one(
                {"name": full_name},
                doc,
                upsert=True
            )

async def get_commands(guild_id: int) -> list[str]:
    cmds = await mongodb.mongo["DashboardBot"].Commands.find_one(
        {"Guild": guild_id}
    )
    return cmds.get("commands", []) if cmds else []

async def clear_commands() -> list[str]:
    cmds = await mongodb.mongo["DashboardBot"].Commands.delete_many({})
    return