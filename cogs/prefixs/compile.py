from discord.ext import commands
import discord
from consts import settings
from discord import app_commands
from models import command_disable, make_embed
import aiohttp

class Prefixs_CompileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> Prefixs_CompileCog")

    @commands.command(name="python", aliases=['py'], description="Pythonを実行します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    async def compile_python(self, ctx: commands.Context, *, program: str):
        if not await command_disable.command_enabled_check_by_cmdname("shell compile", ctx.guild):
            return

        headers = {
            "accept": "*/*",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "authorization": "Bearer undefined",
            "content-type": "application/json",
            "origin": "https://onecompiler.com",
            "priority": "u=1, i",
            "referer": "https://onecompiler.com/python",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        }

        json_data = {
            "name": "Python",
            "title": "Python Hello World",
            "version": "3.6",
            "mode": "python",
            "description": None,
            "extension": "py",
            "concurrentJobs": 10,
            "languageType": "programming",
            "active": True,
            "properties": {
                "language": "python",
                "docs": True,
                "tutorials": True,
                "cheatsheets": True,
                "filesEditable": True,
                "filesDeletable": True,
                "files": [
                    {
                        "name": "main.py",
                        "content": program.removeprefix('```').removesuffix('```'),
                    },
                ],
                "newFileOptions": [
                    {
                        "helpText": "New Python file",
                        "name": "script${i}.py",
                        "content": "# In main file\n# import script${i}\n# print(script${i}.sum(1, 3))\n\ndef sum(a, b):\n    return a + b",
                    },
                ],
            },
            "visibility": "public",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://onecompiler.com/api/code/exec", headers=headers, json=json_data
            ) as response:
                data = await response.json()
                await ctx.reply(
                    embed=make_embed.success_embed(
                        title="Pythonの実行結果",
                        description=f"```{data.get('stdout', '')}```"
                    )
                )

    @commands.command(name="nodejs", aliases=['njs'], description="Nodejsを実行します。")
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    async def compile_nodejs(self, ctx: commands.Context, *, program: str):
        if not await command_disable.command_enabled_check_by_cmdname("shell compile", ctx.guild):
            return

        headers = {
            "accept": "*/*",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "authorization": "Bearer undefined",
            "content-type": "application/json",
            "origin": "https://onecompiler.com",
            "priority": "u=1, i",
            "referer": "https://onecompiler.com/nodejs",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

        json_data = {
            "name": "NodeJS",
            "title": "NodeJS Hello World",
            "version": "12.13",
            "mode": "javascript",
            "description": None,
            "extension": "js",
            "languageType": "programming",
            "active": True,
            "properties": {
                "language": "nodejs",
                "docs": True,
                "tutorials": True,
                "cheatsheets": True,
                "filesEditable": True,
                "filesDeletable": True,
                "files": [
                    {
                        "name": "index.js",
                        "content": program.removeprefix('```').removesuffix('```'),
                    },
                ],
                "newFileOptions": [
                    {
                        "helpText": "New JS file",
                        "name": "script${i}.js",
                        "content": "/**\n *  In main file\n *  let script${i} = require('./script${i}');\n *  console.log(script${i}.sum(1, 2));\n */\n\nfunction sum(a, b) {\n    return a + b;\n}\n\nmodule.exports = { sum };",
                    },
                    {
                        "helpText": "Add Dependencies",
                        "name": "package.json",
                        "content": '{\n  "name": "main_app",\n  "version": "1.0.0",\n  "description": "",\n  "main": "HelloWorld.js",\n  "dependencies": {\n    "lodash": "^4.17.21"\n  }\n}',
                    },
                ],
            },
            "visibility": "public",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://onecompiler.com/api/code/exec", headers=headers, json=json_data
            ) as response:
                data = await response.json()
                await ctx.reply(
                    embed=make_embed.success_embed(
                        title="Nodejsの実行結果",
                        description=f"```{data.get('stdout', '')}```"
                    )
                )

async def setup(bot):
    await bot.add_cog(Prefixs_CompileCog(bot))
