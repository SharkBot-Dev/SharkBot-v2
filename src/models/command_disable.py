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
    このギルドでコマンドが有効か、および実行ロール権限があるかをチェックする
    """
    if interaction.guild is None:
        return True

    cmdname = extract_command_name(interaction)
    
    config = await mongodb.mongo["DashboardBot"].CommandDisabled.find_one(
        {"Guild": interaction.guild.id}
    )

    if not config:
        return True

    disabled_list = config.get("commands", [])
    if cmdname in disabled_list:
        return False

    role_restrictions = config.get("roleRestrictions", {})
    allowed_role_id = role_restrictions.get(cmdname)

    if allowed_role_id:
        user_has_role = any(r.id == int(allowed_role_id) for r in interaction.user.roles)
        if not user_has_role:
            return False

    return True


async def command_enabled_check_by_cmdname(cmdname: str, guild: discord.Guild) -> bool:
    """
    (互換性維持用) コマンド名のみでのチェック
    ※この関数は interaction がないため、ロール制限の判定はスキップされます
    """
    config = await mongodb.mongo["DashboardBot"].CommandDisabled.find_one(
        {"Guild": guild.id}
    )

    if not config:
        return True
    
    if cmdname in config.get("commands", []):
        return False
        
    return True


async def set_command_config(guild_id: int, commands: list[str], role_restrictions: dict[str, str]) -> bool:
    """
    無効コマンドとロール制限をセットで更新
    """
    await mongodb.mongo["DashboardBot"].CommandDisabled.update_one(
        {"Guild": guild_id},
        {
            "$set": {
                "commands": commands,
                "roleRestrictions": role_restrictions
            }
        },
        upsert=True
    )
    return True

async def get_command_config(guild_id: int) -> tuple[list[str], dict[str, str]]:
    """
    設定をまるごと取得 (disabled_commands, role_restrictions)
    """
    config = await mongodb.mongo["DashboardBot"].CommandDisabled.find_one(
        {"Guild": guild_id}
    )
    if not config:
        return [], {}
    return config.get("commands", []), config.get("roleRestrictions", {})

async def disable_single_command(guild_id: int, cmdname: str) -> bool:
    """
    特定のコマンドを一つだけ無効化リストに追加する
    """
    await mongodb.mongo["DashboardBot"].CommandDisabled.update_one(
        {"Guild": guild_id},
        {"$addToSet": {"commands": cmdname}},
        upsert=True
    )
    return True

async def enable_single_command(guild_id: int, cmdname: str) -> bool:
    """
    特定のコマンドを一つだけ無効化リストから削除（有効化）する
    """
    await mongodb.mongo["DashboardBot"].CommandDisabled.update_one(
        {"Guild": guild_id},
        {"$pull": {"commands": cmdname}}
    )
    return True

async def set_single_role_restriction(guild_id: int, cmdname: str, role_id: int) -> bool:
    """
    特定のコマンドにロール制限を設定する
    """
    await mongodb.mongo["DashboardBot"].CommandDisabled.update_one(
        {"Guild": guild_id},
        {"$set": {f"roleRestrictions.{cmdname}": str(role_id)}},
        upsert=True
    )
    return True

async def remove_single_role_restriction(guild_id: int, cmdname: str) -> bool:
    """
    特定のコマンドのロール制限を解除する
    """
    await mongodb.mongo["DashboardBot"].CommandDisabled.update_one(
        {"Guild": guild_id},
        {"$unset": {f"roleRestrictions.{cmdname}": ""}}
    )
    return True