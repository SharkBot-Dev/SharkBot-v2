import discord
from consts import mongodb


def extract_command_name(interaction: discord.Interaction) -> str:
    data = interaction.data
    if not data:
        return ""

    name_parts = [data.get("name")]

    def recurse(options):
        if not options or not isinstance(options, list):
            return
        opt = options[0]

        if opt.get("type") in (1, 2):
            name_parts.append(opt["name"])
            recurse(opt.get("options", []))

    recurse(data.get("options", []))

    return " ".join(name_parts)


async def command_enabled_check(interaction: discord.Interaction) -> bool:
    """
    このギルドでコマンドが有効かをチェックする
    """
    if interaction.guild is None:
        return True

    cmdname = extract_command_name(interaction)

    cmds = await mongodb.mongo["DashboardBot"].CommandDisabled.find_one(
        {"Guild": interaction.guild.id}
    )

    if not cmds or cmdname not in cmds.get("commands", []):
        return True
    return False


async def add_disabled_command(guild_id: int, cmdname: str) -> bool:
    """
    ギルドに無効コマンドを追加
    """
    await mongodb.mongo["DashboardBot"].CommandDisabled.update_one(
        {"Guild": guild_id},
        {"$addToSet": {"commands": cmdname}},
        upsert=True
    )
    return True


async def remove_disabled_command(guild_id: int, cmdname: str) -> bool:
    """
    ギルドの無効コマンドから削除
    """
    await mongodb.mongo["DashboardBot"].CommandDisabled.update_one(
        {"Guild": guild_id},
        {"$pull": {"commands": cmdname}},
        upsert=True
    )
    return True

async def set_disabled_commands(guild_id: int, commands: list[str]) -> bool:
    """ギルドの無効化コマンド一覧を丸ごと置き換える"""
    await mongodb.mongo["DashboardBot"].CommandDisabled.update_one(
        {"Guild": guild_id},
        {"$set": {"commands": commands}},
        upsert=True
    )
    return True

async def get_disabled_commands(guild_id: int) -> list[str]:
    """
    ギルドで無効化されているコマンド一覧を取得
    """
    cmds = await mongodb.mongo["DashboardBot"].CommandDisabled.find_one(
        {"Guild": guild_id}
    )
    return cmds.get("commands", []) if cmds else []