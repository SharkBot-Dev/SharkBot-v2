import aiofiles
import json
from consts import mongodb

langs: dict[str, dict] = {}


async def load() -> None:
    for code in ("ja", "en"):
        try:
            async with aiofiles.open(
                f"translate/{code}.json", mode="r", encoding="utf-8"
            ) as f:
                data = await f.read()
                langs[code] = json.loads(data)
        except FileNotFoundError:
            print(f"[WARN] 翻訳ファイルが見つかりません: translate/{code}.json")
            langs[code] = {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] 翻訳ファイルの読み込みに失敗しました: {code}.json ({e})")
            langs[code] = {}


async def set_guild_lang(guild_id: int, lang: str) -> None:
    m = mongodb.mongo
    db = m.async_db["Main"].BotLang
    await db.update_one(
        {"Guild": guild_id},
        {"$set": {"Lang": lang}},
        upsert=True,
    )


async def get_guild_lang(guild_id: int) -> str:
    m = mongodb.mongo
    db = m.async_db["Main"].BotLang
    try:
        dbfind = await db.find_one({"Guild": guild_id}, {"_id": False})
    except Exception as e:
        return "ja"
    if not dbfind:
        return "ja"
    return dbfind.get("Lang", "ja")


def get(lang: str, category: str, key: str) -> str:
    if lang == "ja":
        return key

    data = langs.get(lang) or langs.get("ja", {})

    cat = data.get(category)
    if not cat:
        return key

    return cat.get(key, key)
