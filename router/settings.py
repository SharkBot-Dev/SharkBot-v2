import time
from fastapi import APIRouter, Depends, Form, Request
import httpx
from consts import settings, templates
from consts import mongodb
from models import command_disable
from fastapi.responses import RedirectResponse
import html

router = APIRouter(prefix="/settings")

req_cooldown = {}


async def check_owner(user, guild_id: str) -> bool:
    user_guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": user.get("id")}
    )
    guild = next(
        (g for g in user_guilds.get("Guilds", []) if g.get("id") == guild_id), None
    )
    if guild is None:
        return False

    if not guild.get("owner"):
        return False

    bot_joined = await mongodb.mongo["DashboardBot"].bot_joind_guild.find_one(
        {"Guild": int(guild_id)}
    )

    if bot_joined is None:
        return False

    return True


def rate_limiter(request: Request):
    return request.app.state.limiter.limit("1/2 seconds")


@router.get("/{guild_id}", dependencies=[Depends(rate_limiter)])
async def settings_page(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)

    if guild is None:
        return RedirectResponse("/login/guilds")

    guilds = await mongodb.mongo["DashboardBot"].bot_joind_guild.find_one(
        {"Guild": int(guild_id)}
    )

    if guilds == None:
        return RedirectResponse(
            "https://discord.com/oauth2/authorize?client_id=1322100616369147924"
        )

    if not guild.get("owner"):
        return RedirectResponse("/login/guilds")

    prefix_doc = await mongodb.mongo["DashboardBot"].CustomPrefixBot.find_one(
        {"Guild": int(guild_id)}
    )
    prefix = prefix_doc.get("Prefix") if prefix_doc else "!"

    return templates.templates.TemplateResponse(
        "main_settings.html",
        {"request": request, "guild": guild, "settings": {"prefix": prefix}},
    )


@router.post("/{guild_id}/update_prefix", dependencies=[Depends(rate_limiter)])
async def update_prefix(request: Request, guild_id: str, prefix: str = Form(...)):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    await mongodb.mongo["DashboardBot"].CustomPrefixBot.replace_one(
        {"Guild": int(guild_id)},
        {"Guild": int(guild_id), "Prefix": prefix},
        upsert=True,
    )

    return RedirectResponse(f"/settings/{guild_id}", status_code=303)


@router.get("/{guild_id}/create_embed", dependencies=[Depends(rate_limiter)])
async def create_embed(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one(
        {"Guild": int(guild_id)}
    )

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [
            {"id": str(int(ch["id"])), "name": ch["name"]}
            for ch in channel_doc["Channels"]
        ]

    return templates.templates.TemplateResponse(
        "make_embed.html", {"request": request, "guild": guild, "channels": channels}
    )


@router.post(
    "/{guild_id}/send_embed", name="send_embed", dependencies=[Depends(rate_limiter)]
)
async def send_embed(
    request: Request,
    guild_id: str,
    title: str = Form(...),
    desc: str = Form(...),
    channel: str = Form(...),
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    safe_title = html.escape(title)
    safe_desc = html.escape(desc)

    try:
        await mongodb.mongo["DashboardBot"].SendEmbedQueue.replace_one(
            {"Guild": int(guild_id)},
            {
                "Guild": int(guild_id),
                "Title": safe_title,
                "Description": safe_desc,
                "User": int(u.get("id")),
                "Channel": int(channel),
            },
            upsert=True,
        )
    except:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/create_embed", status_code=303)


@router.get("/{guild_id}/pin_message", dependencies=[Depends(rate_limiter)])
async def pin_message(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one(
        {"Guild": int(guild_id)}
    )

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [
            {"id": str(int(ch["id"])), "name": ch["name"]}
            for ch in channel_doc["Channels"]
        ]

    return templates.templates.TemplateResponse(
        "lock_message.html", {"request": request, "guild": guild, "channels": channels}
    )


@router.post("/{guild_id}/pin_message_create", dependencies=[Depends(rate_limiter)])
async def send_embed(
    request: Request,
    guild_id: str,
    title: str = Form(...),
    desc: str = Form(...),
    channel: str = Form(...),
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    safe_title = html.escape(title)
    safe_desc = html.escape(desc)

    try:
        db = mongodb.mongo["Main"].LockMessage
        await db.replace_one(
            {"Channel": int(channel), "Guild": int(guild_id)},
            {
                "Channel": int(channel),
                "Guild": int(guild_id),
                "Title": safe_title,
                "Desc": safe_desc,
                "MessageID": 0,
            },
            upsert=True,
        )
    except Exception:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/pin_message", status_code=303)


# よろしくメッセージ


@router.get("/{guild_id}/welcome", dependencies=[Depends(rate_limiter)])
async def welcome(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one(
        {"Guild": int(guild_id)}
    )

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [
            {"id": str(int(ch["id"])), "name": ch["name"]}
            for ch in channel_doc["Channels"]
        ]

    msg = await mongodb.mongo["Main"].WelcomeMessage.find_one({"Guild": int(guild_id)})

    def rep_name(msg: str):
        return (
            msg.replace("<name>", "[name]")
            .replace("<count>", "[count]")
            .replace("<guild>", "[guild]")
            .replace("<createdat>", "[createdat]")
        )

    if not msg:
        return templates.templates.TemplateResponse(
            "welcome_settings.html",
            {
                "request": request,
                "guild": guild,
                "channels": channels,
                "title": "[name] さん、よろしく！",
                "description": "あなたは [count] 人目のメンバーです！\n\nアカウント作成日: [createdat]",
            },
        )

    return templates.templates.TemplateResponse(
        "welcome_settings.html",
        {
            "request": request,
            "guild": guild,
            "channels": channels,
            "title": rep_name(msg.get("Title", "[name] さん、よろしく！")),
            "description": rep_name(msg.get(
                "Description",
                "あなたは [count] 人目のメンバーです！\n\nアカウント作成日: [createdat]",
            )),
        },
    )


@router.post("/{guild_id}/welcome_set", dependencies=[Depends(rate_limiter)])
async def welcome_send(
    request: Request,
    guild_id: str,
    title: str = Form(...),
    desc: str = Form(...),
    channel: str = Form(...),
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    safe_title = html.escape(title)
    safe_desc = html.escape(desc)

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one(
        {"Guild": int(guild_id)}
    )

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [str(int(ch["id"])) for ch in channel_doc["Channels"]]

    if channel not in channels:
        return templates.templates.TemplateResponse(
            "message.html",
            {
                "request": request,
                "url": f"/settings/{guild_id}/welcome",
                "message": "不正なチャンネルが指定されました。",
            },
        )

    try:
        def rep_name(msg: str):
            return (
                msg.replace("[name]", "<name>")
                .replace("[count]", "<count>")
                .replace("[guild]", "<guild>")
                .replace("[createdat]", "<createdat>")
            )

        db = mongodb.mongo["Main"].WelcomeMessage
        if title == "delete_welcome":
            await db.delete_one({"Guild": int(guild_id)})
        else:
            await db.replace_one(
                {"Guild": int(guild_id)},
                {
                    "Channel": int(channel),
                    "Guild": int(guild_id),
                    "Title": rep_name(safe_title),
                    "Description": rep_name(safe_desc),
                },
                upsert=True,
            )
    except Exception:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/welcome", status_code=303)


# メッセージ展開


@router.get("/{guild_id}/expand", dependencies=[Depends(rate_limiter)])
async def expand(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    return templates.templates.TemplateResponse(
        "expand_settings.html", {"request": request, "guild": guild}
    )


@router.post("/{guild_id}/expand_set", dependencies=[Depends(rate_limiter)])
async def expand_set(request: Request, guild_id: str, setting: str = Form(...)):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    try:
        if setting == "delete_expand":
            await mongodb.mongo["Main"].ExpandSettings.delete_one(
                {"Guild": int(guild_id)}
            )
        else:
            await mongodb.mongo["Main"].ExpandSettings.replace_one(
                {"Guild": int(guild_id)}, {"Guild": int(guild_id)}, upsert=True
            )

    except Exception:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/expand", status_code=303)


# ロールパネル


@router.get("/{guild_id}/rolepanel", dependencies=[Depends(rate_limiter)])
async def rolepanel(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    return templates.templates.TemplateResponse(
        "rolepanel.html", {"request": request, "guild": guild}
    )


# ログ設定


@router.get("/{guild_id}/logging", dependencies=[Depends(rate_limiter)])
async def logging(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one(
        {"Guild": int(guild_id)}
    )

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [
            {"id": str(int(ch["id"])), "name": ch["name"]}
            for ch in channel_doc["Channels"]
        ]

    return templates.templates.TemplateResponse(
        "logging_setting.html",
        {"request": request, "guild": guild, "channels": channels},
    )


@router.post("/{guild_id}/logging_set", dependencies=[Depends(rate_limiter)])
async def logging_set(request: Request, guild_id: str, channel: str = Form(None)):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    if not channel:
        return RedirectResponse(f"/settings/{guild_id}/logging")

    # --- クールダウン ---
    current_time = time.time()
    last_message_time = req_cooldown.get(guild_id, 0)
    if current_time - last_message_time < 30:
        return templates.templates.TemplateResponse(
            "message.html",
            {
                "request": request,
                "url": f"/settings/{guild_id}/logging",
                "message": "クールダウンです。30秒後に再度お試しください。",
            },
        )
    req_cooldown[guild_id] = current_time

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one(
        {"Guild": int(guild_id)}
    )

    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [str(int(ch["id"])) for ch in channel_doc["Channels"]]

    if channel not in channels:
        return templates.templates.TemplateResponse(
            "message.html",
            {
                "request": request,
                "url": f"/settings/{guild_id}/logging",
                "message": "不正なチャンネルが指定されました。",
            },
        )

    try:
        async with httpx.AsyncClient() as client:
            webhook = await client.post(
                f"{settings.DISCORD_API}/channels/{channel}/webhooks",
                json={"name": "SharkBot-Log"},
                headers={"Authorization": f"Bot {settings.TOKEN}"},
            )

        resp = webhook.json()

        webhook_id = resp.get("id")
        webhook_token = resp.get("token")

        if not webhook_id or not webhook_token:
            return templates.templates.TemplateResponse(
                "message.html",
                {
                    "request": request,
                    "url": f"/settings/{guild_id}/logging",
                    "message": "エラーが発生しました。",
                },
            )

        await mongodb.mongo["Main"].EventLoggingChannel.replace_one(
            {"Guild": int(guild_id)},
            {
                "Guild": int(guild_id),
                "Channel": int(channel),
                "Webhook": f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}",
            },
            upsert=True,
        )

        return templates.templates.TemplateResponse(
            "message.html",
            {
                "request": request,
                "url": f"/settings/{guild_id}/logging",
                "message": "ログチャンネルが指定されました。",
            },
        )
    except:
        return RedirectResponse(f"/{guild_id}/logging", status_code=303)


# コマンドの有効化・無効化


@router.get("/{guild_id}/commands", dependencies=[Depends(rate_limiter)])
async def command_disable_(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
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
            "disabled_commands": disabled,
        },
    )


@router.post("/{guild_id}/command_disable", dependencies=[Depends(rate_limiter)])
async def command_disable_set(
    request: Request, guild_id: str, enabled_commands: list[str] = Form(default=[])
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
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


# レベル


@router.get("/{guild_id}/leveling", dependencies=[Depends(rate_limiter)])
async def leveling(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    channel_doc = await mongodb.mongo["DashboardBot"].guild_channels.find_one(
        {"Guild": int(guild_id)}
    )
    channels = []
    if channel_doc and "Channels" in channel_doc:
        channels = [
            {"id": str(int(ch["id"])), "name": ch["name"]}
            for ch in channel_doc["Channels"]
        ]

    l_t_doc = await mongodb.mongo["Main"].LevelingUpTiming.find_one(
        {"Guild": int(guild_id)}
    )
    l_t = l_t_doc.get("Timing", 60) if l_t_doc else 60

    level_doc = await mongodb.mongo["Main"].LevelingSetting.find_one(
        {"Guild": int(guild_id)}
    )
    level_check = "checked" if level_doc else ""

    return templates.templates.TemplateResponse(
        "level.html",
        {
            "request": request,
            "guild": guild,
            "channels": channels,
            "timing": l_t,
            "check": level_check,
        },
    )


@router.post("/{guild_id}/leveling_set", dependencies=[Depends(rate_limiter)])
async def leveling_set(
    request: Request,
    guild_id: str,
    enabled: str = Form(None),
    timing: int = Form(60),
    channel: str = Form(None),
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    if not enabled:
        await mongodb.mongo["Main"].LevelingSetting.delete_one({"Guild": int(guild_id)})
        return RedirectResponse(f"/settings/{guild_id}/leveling")

    await mongodb.mongo["Main"].LevelingSetting.replace_one(
        {"Guild": int(guild_id)}, {"Guild": int(guild_id)}, upsert=True
    )

    await mongodb.mongo["Main"].LevelingUpTiming.replace_one(
        {"Guild": int(guild_id)},
        {"Guild": int(guild_id), "Timing": timing},
        upsert=True,
    )

    if channel:
        channel = html.escape(channel)
        await mongodb.mongo["Main"].LevelingUpAlertChannel.replace_one(
            {"Guild": int(guild_id)},
            {"Guild": int(guild_id), "Channel": int(channel)},
            upsert=True,
        )
    elif channel == "0":
        await mongodb.mongo["Main"].LevelingUpAlertChannel.delete_one(
            {"Guild": int(guild_id)}
        )
    else:
        await mongodb.mongo["Main"].LevelingUpAlertChannel.delete_one(
            {"Guild": int(guild_id)}
        )

    return RedirectResponse(f"/settings/{guild_id}/leveling", status_code=303)


# AutoMod作成


@router.get("/{guild_id}/automod", dependencies=[Depends(rate_limiter)])
async def automod(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    return templates.templates.TemplateResponse(
        "automod.html", {"request": request, "guild": guild}
    )


@router.post("/{guild_id}/automod_create", dependencies=[Depends(rate_limiter)])
async def automod_create(request: Request, guild_id: str, name: str = Form(None)):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    if name is None:
        return RedirectResponse(f"/settings/{guild_id}/automod", status_code=303)

    safe_name = html.escape(name)

    try:
        await mongodb.mongo["DashboardBot"].CreateAutoModQueue.replace_one(
            {"Guild": int(guild_id)},
            {"Guild": int(guild_id), "Name": safe_name},
            upsert=True,
        )
    except:
        return {"message": "不正な値が入力されました。"}

    return RedirectResponse(f"/settings/{guild_id}/automod", status_code=303)


# 自動返信


@router.get("/{guild_id}/autoreply", dependencies=[Depends(rate_limiter)])
async def autoreply(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    db = mongodb.mongo["Main"].AutoReply
    word_list = [b async for b in db.find({"Guild": int(guild_id)})]

    return templates.templates.TemplateResponse(
        "autoreply.html", {"request": request, "guild": guild, "autos": word_list}
    )


@router.post("/{guild_id}/autoreply_set", dependencies=[Depends(rate_limiter)])
async def autoreply_set(
    request: Request, guild_id: str, tri: str = Form(...), reply: str = Form(...)
):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    if not tri:
        return RedirectResponse(f"/settings/{guild_id}/autoreply", status_code=303)

    if not reply:
        return RedirectResponse(f"/settings/{guild_id}/autoreply", status_code=303)

    safe_trigger = html.escape(tri)
    safe_replyword = html.escape(reply)

    db = mongodb.mongo["Main"].AutoReply
    await db.replace_one(
        {"Guild": int(guild_id), "Word": safe_trigger},
        {"Guild": int(guild_id), "Word": safe_trigger, "ReplyWord": safe_replyword},
        upsert=True,
    )

    return RedirectResponse(f"/settings/{guild_id}/autoreply", status_code=303)


@router.post("/{guild_id}/autoreply_delete", dependencies=[Depends(rate_limiter)])
async def autoreply_delete(request: Request, guild_id: str, tri: str = Form(...)):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    if not tri:
        return RedirectResponse(f"/settings/{guild_id}/autoreply", status_code=303)

    safe_trigger = html.escape(tri)

    db = mongodb.mongo["Main"].AutoReply
    await db.delete_one({"Word": safe_trigger, "Guild": int(guild_id)})

    return RedirectResponse(f"/settings/{guild_id}/autoreply", status_code=303)
