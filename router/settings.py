from fastapi import APIRouter, Form, Request
from consts import templates
from consts import mongodb
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

    prefix_doc = await mongodb.mongo["DashboardBot"].CustomPrefixBot.find_one({"Guild": guild_id})
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