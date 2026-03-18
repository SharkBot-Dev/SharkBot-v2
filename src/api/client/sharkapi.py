import aiohttp

class Economy:
    def __init__(self, json: dict):
        self.data = json
        self.currency = json.get('currency')

class EconomyMember:
    def __init__(self, json: dict):
        self.data = json
        self.money = json.get('money', 0)
        self.bank = json.get('bank', 0)

class AccountInfo:
    def __init__(self, json: dict):
        self.data = json
        self.money = json.get('money', 0)
        self.user_id = json.get('user_id', 0)
        self.user_name = json.get('user_name', 0)
        self.avatar_url = json.get('avatar_url', 0)

class BotStatus:
    def __init__(self, json: dict):
        self.data = json
        self.bot_ping = int(json.get('bot_ping', "0"))
        self.users_count = int(json.get('users_count', "0"))
        self.guilds_count = int(json.get('guilds_count', "0"))
        self.shards_count = int(json.get('shards_count', "0"))

class APIKeyInfo:
    def __init__(self, json: dict):
        self.data = json
        self.guild_id = int(json.get('guild_id', "0"))
        self.user_id = int(json.get('user_id', "0"))
        self.name = json.get('name', "0")
        self.apikey = json.get('apikey', "0")

class SharkBot:
    def __init__(self, apikey: str = None):
        self.BASE_URL = "https://api.sharkbot.xyz"
        self.APIKEY = apikey

    # ==== アカウント関連 ====
    async def fetchAccount(self, userId: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL + f'/account/{userId}') as resp:
                json = await resp.json()
                return AccountInfo(json)
            
    # ==== API関連 ====
    async def fetchAPIKeyInfo(self, guildId: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL + f'/api/{guildId}', headers={
                "Authorization": self.APIKEY
            }) as resp:
                json = await resp.json()
                return APIKeyInfo(json)

    # ==== 検索関連 ====
    async def fetchNews(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL + f'/search/news') as resp:
                json = await resp.json()
                return json.get('news_url')

    # ==== 経済関連 ====
    async def fetchEconomy(self, guildId: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL + f'/economy/{guildId}') as resp:
                json = await resp.json()
                return Economy(json)

    async def fetchEconomyLeaderboard(self, guildId: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL + f'/economy/{guildId}/leaderboard') as resp:
                json = await resp.json()
                return [EconomyMember(j) for j in json]

    async def fetchEconomyMember(self, guildId: str, userId: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL + f'/economy/{guildId}/{userId}') as resp:
                json = await resp.json()
                return EconomyMember(json)
            
    async def editEconomyMember(self, guildId: str, userId: str, money: int = None, bank: int = None):
        json = {}
        if money:
            json["money"] = money
        if bank:
            json["bank"] = bank

        async with aiohttp.ClientSession() as session:
            async with session.patch(self.BASE_URL + f'/economy/{guildId}/{userId}', json=json, headers={
                "Authorization": self.APIKEY
            }) as resp:
                resp.raise_for_status()
                return True

    # ==== Botのステータス ====
    async def fetchBotStatus(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL + "/status") as resp:
                json = await resp.json()
                return BotStatus(json)
            
    async def fetchBotPing(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL + "/status") as resp:
                json = await resp.json()
                return json["bot_ping"]