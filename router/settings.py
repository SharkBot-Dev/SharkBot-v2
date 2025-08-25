from fastapi import APIRouter, Form, Request
from consts import templates
from consts import mongodb
from models import command_disable
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/settings")

async def check_owner(user, guild_id: str):
    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": user.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return False

    if not guild.get("owner"):
        return False

    guilds = await mongodb.mongo["DashboardBot"].bot_joind_guild.find_one({
        "Guild": int(guild_id)
    })

    if guilds == None:
        return 
    
    return True

@router.get("/{guild_id}")
async def settings_page(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)

    if guild is None:
        return RedirectResponse("/login/guilds")

    guilds = await mongodb.mongo["DashboardBot"].bot_joind_guild.find_one({
        "Guild": int(guild_id)
    })

    if guilds == None:
        return RedirectResponse("https://discord.com/oauth2/authorize?client_id=1322100616369147924")

    if not guild.get("owner"):
        return RedirectResponse("/login/guilds")

    prefix_doc = await mongodb.mongo["DashboardBot"].CustomPrefixBot.find_one({"Guild": int(guild_id)})
    prefix = prefix_doc.get("Prefix") if prefix_doc else "!"

    return templates.templates.TemplateResponse("main_settings.html", {
        "request": request,
        "guild": guild,
        "settings": {
            "prefix": prefix
        }
    })


@router.post("/{guild_id}/update_prefix")
async def update_prefix(request: Request, guild_id: str, prefix: str = Form(...)):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    await mongodb.mongo["DashboardBot"].CustomPrefixBot.replace_one(
        {"Guild": int(guild_id)}, 
        {"Guild": int(guild_id), "Prefix": prefix}, 
        upsert=True
    )

    return RedirectResponse(f"/settings/{guild_id}", status_code=303)

@router.get("/{guild_id}/create_embed")
async def create_embed(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one({"Guild": int(guild_id)})

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [
            {
                "id": str(int(ch["id"])),
                "name": ch["name"]
            }
            for ch in channel_doc["Channels"]
        ]

    return templates.templates.TemplateResponse(
        "make_embed.html",
        {
            "request": request,
            "guild": guild,
            "channels": channels
        }
    )

@router.post("/{guild_id}/send_embed", name="send_embed")
async def send_embed(
    request: Request,
    guild_id: str,
    title: str = Form(...),
    desc: str = Form(...),
    channel: str = Form(...)
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    try:

        await mongodb.mongo["DashboardBot"].SendEmbedQueue.replace_one(
            {"Guild": int(guild_id)},
            {
                "Guild": int(guild_id),
                "Title": title,
                "Description": desc,
                "User": int(u.get("id")),
                "Channel": int(channel)
            },
            upsert=True
        )
    except:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/create_embed", status_code=303)

@router.get("/{guild_id}/pin_message")
async def pin_message(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one({"Guild": int(guild_id)})

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [
            {
                "id": str(int(ch["id"])),
                "name": ch["name"]
            }
            for ch in channel_doc["Channels"]
        ]

    return templates.templates.TemplateResponse(
        "lock_message.html",
        {
            "request": request,
            "guild": guild,
            "channels": channels
        }
    )

@router.post("/{guild_id}/pin_message_create", name="send_embed")
async def send_embed(
    request: Request,
    guild_id: str,
    title: str = Form(...),
    desc: str = Form(...),
    channel: str = Form(...)
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    try:

        db = mongodb.mongo["Main"].LockMessage
        await db.replace_one(
            {"Channel": int(channel), "Guild": int(guild_id)}, 
            {"Channel": int(channel), "Guild": int(guild_id), "Title": title, "Desc": desc, "MessageID": 0}, 
            upsert=True
        )
    except Exception as e:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/pin_message", status_code=303)

# よろしくメッセージ
@router.get("/{guild_id}/welcome")
async def welcome(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one({"Guild": int(guild_id)})

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [
            {
                "id": str(int(ch["id"])),
                "name": ch["name"]
            }
            for ch in channel_doc["Channels"]
        ]

    msg = await mongodb.mongo["Main"].WelcomeMessage.find_one({"Guild": int(guild_id)})

    if not msg:
        return templates.templates.TemplateResponse(
            "welcome_settings.html",
            {
                "request": request,
                "guild": guild,
                "channels": channels,
                "title": "<name> さん、よろしく！",
                "description": "あなたは <count> 人目のメンバーです！\n\nアカウント作成日: <createdat>"
            }
        )

    return templates.templates.TemplateResponse(
        "welcome_settings.html",
        {
            "request": request,
            "guild": guild,
            "channels": channels,
            "title": msg.get("Title", "<name> さん、よろしく！"),
            "description": msg.get("Description", "あなたは <count> 人目のメンバーです！\n\nアカウント作成日: <createdat>")
        }
    )

@router.post("/{guild_id}/welcome_set")
async def welcome_send(
    request: Request,
    guild_id: str,
    title: str = Form(...),
    desc: str = Form(...),
    channel: str = Form(...)
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    try:

        db = mongodb.mongo["Main"].WelcomeMessage
        if title == "delete_welcome":
            await db.delete_one({
                "Guild": int(guild_id)
            })
        else:

            await db.replace_one(
                {"Guild": int(guild_id)}, 
                {"Channel": int(channel), "Guild": int(guild_id), "Title": title, "Description": desc}, 
                upsert=True
            )
    except Exception as e:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/welcome", status_code=303)

# メッセージ展開
@router.get("/{guild_id}/expand")
async def expand(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    return templates.templates.TemplateResponse(
        "expand_settings.html",
        {
            "request": request,
            "guild": guild
        }
    )

@router.post("/{guild_id}/expand_set")
async def expand_set(
    request: Request,
    guild_id: str,
    setting: str = Form(...)
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    try:
        if setting == "delete_expand":
            await mongodb.mongo["Main"].ExpandSettings.delete_one({
                "Guild": int(guild_id)
            })
        else:

            await mongodb.mongo["Main"].ExpandSettings.replace_one(
                {"Guild": int(guild_id)}, 
                {"Guild": int(guild_id)}, 
                upsert=True
            )

    except Exception as e:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/expand", status_code=303)

# ロールパネル
@router.get("/{guild_id}/rolepanel")
async def rolepanel(
    request: Request,
    guild_id: str
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    return templates.templates.TemplateResponse(
        "rolepanel.html",
        {
            "request": request,
            "guild": guild
        }
    )

# コマンドの有効化・無効化
@router.get("/{guild_id}/commands")
async def command_disable_(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    cmds = await mongodb.mongo["DashboardBot"].Commands.find().to_list(None)

    disabled = await command_disable.get_disabled_commands(int(guild_id))

    return templates.templates.TemplateResponse(
        "commands_settings.html",
        {
            "request": request,
            "guild": guild,
            "commands": cmds,
            "disabled_commands": disabled
        }
    )


@router.post("/{guild_id}/command_disable")
async def command_disable_set(
    request: Request,
    guild_id: str,
    enabled_commands: list[str] = Form(default=[])
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one({"User": u.get("id")})
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    cmds = await mongodb.mongo["DashboardBot"].Commands.find().to_list(None)
    all_cmd_names = [c["name"] for c in cmds]

    to_disable = [c for c in all_cmd_names if c not in enabled_commands]

    await command_disable.set_disabled_commands(int(guild_id), to_disable)

    return RedirectResponse(f"/settings/{guild_id}/commands", status_code=303)