from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import json
from unbelievaboat import Client
import asyncio
import aiohttp
from discord import Webhook
from discord import app_commands

cooldown_python_shell = {}

class RunPython(discord.ui.Modal, title='Pythonを実行'):
    code = discord.ui.TextInput(
        label='コードを入力',
        placeholder='print(1+1)',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/python',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        }
        
        json_data = {
            'name': 'Python',
            'title': 'Python Hello World',
            'version': '3.6',
            'mode': 'python',
            'description': None,
            'extension': 'py',
            'concurrentJobs': 10,
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'python',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'main.py',
                        'content': self.code.value,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New Python file',
                        'name': 'script${i}.py',
                        'content': '# In main file\n# import script${i}\n# print(script${i}.sum(1, 3))\n\ndef sum(a, b):\n    return a + b',
                    },
                ],
            },
            'visibility': 'public',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="Pythonの実行結果", description=f"```{data.get("stdout", "")}```", color=discord.Color.blue()))

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send('エラー。\nWhileなどは使用できません。')

class RunNodeJS(discord.ui.Modal, title='NodoJSを実行'):
    code = discord.ui.TextInput(
        label='コードを入力',
        placeholder='console.log(1+1);',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/nodejs',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        json_data = {
            'name': 'NodeJS',
            'title': 'NodeJS Hello World',
            'version': '12.13',
            'mode': 'javascript',
            'description': None,
            'extension': 'js',
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'nodejs',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'index.js',
                        'content': self.code.value,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New JS file',
                        'name': 'script${i}.js',
                        'content': "/**\n *  In main file\n *  let script${i} = require('./script${i}');\n *  console.log(script${i}.sum(1, 2));\n */\n\nfunction sum(a, b) {\n    return a + b;\n}\n\nmodule.exports = { sum };",
                    },
                    {
                        'helpText': 'Add Dependencies',
                        'name': 'package.json',
                        'content': '{\n  "name": "main_app",\n  "version": "1.0.0",\n  "description": "",\n  "main": "HelloWorld.js",\n  "dependencies": {\n    "lodash": "^4.17.21"\n  }\n}',
                    },
                ],
            },
            'visibility': 'public',
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="Nodejsの実行結果", description=f"```{data.get("stdout", "")}```", color=discord.Color.blue()))

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send('エラー。')

class RunCPlapla(discord.ui.Modal, title='C++を実行'):
    code = discord.ui.TextInput(
        label='コードを入力',
        placeholder='printf("aaa")',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/cpp',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        json_data = {
            'name': 'C++',
            'title': 'C++ Hello World',
            'version': 'latest',
            'mode': 'c_cpp',
            'description': None,
            'extension': 'cpp',
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'cpp',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'Main.cpp',
                        'content': self.code.value,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New C++ file',
                        'name': 'NewFile${i}.cpp',
                        'content': '#include <iostream>\n\n// Follow the steps below to use this file\n\n// 1. In main file add the following include \n// #include "NewFile${i}.cpp"\n\n// 2. Add the following in the code\n// sayHelloFromNewFile${i}();\n\nvoid sayHelloFromNewFile${i}() {\n    std::cout << "\\nHello from New File ${i}!\\n";\n}\n',
                    },
                    {
                        'helpText': 'New Text file',
                        'name': 'sample${i}.txt',
                        'content': 'Sample text file!',
                    },
                ],
            },
            'visibility': 'public',
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="C++の実行結果", description=f"```{data.get("stdout", "")}```", color=discord.Color.blue()))

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send(f'エラー。\n{sys.exc_info()}')

class RunCSharp(discord.ui.Modal, title='C#を実行'):
    code = discord.ui.TextInput(
        label='コードを入力',
        placeholder='Console.WriteLine("Hello world!");',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/csharp',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        json_data = {
            'name': 'C#',
            'title': 'C# Hello World!',
            'mode': 'csharp',
            'description': None,
            'extension': 'cs',
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'csharp',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'HelloWorld.cs',
                        'content': self.code.value,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New C# file',
                        'name': 'NewClass${i}.cs',
                        'content': 'using System;\n\nnamespace HelloWorld\n{\n\tpublic class NewClass${i}\n\t{\n\t\t// Follow the steps below to use this file\n\n\t\t// 1. In the main file (e.g., HelloWorld.cs), create an instance of this class:\n\t\t// NewClass${i} instance${i} = new NewClass${i}();\n\n\t\t// 2. Call the method to get the greeting message:\n\t\t// Console.WriteLine(instance${i}.SayHelloFromNewClass());\n\n\t\tpublic string SayHelloFromNewClass()\n\t\t{\n\t\t\treturn "Hello from New Class ${i}!";\n\t\t}\n\t}\n}',
                    },
                ],
            },
            'visibility': 'public',
        }
        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="C#の実行結果", description=f"```{data.get("stdout", "")}```", color=discord.Color.blue()))

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send('エラー。')

class ShellCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ShellCog")

    @commands.Cog.listener("on_message")
    async def on_message_python_shell(self, message: discord.Message):
        if message.author.bot:
            return
        
        db = self.bot.async_db["Main"].PythonShell
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_python_shell.get(message.channel.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_python_shell[message.channel.id] = current_time

        headers = {
            'accept': '*/*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'authorization': 'Bearer undefined',
            'content-type': 'application/json',
            'origin': 'https://onecompiler.com',
            'priority': 'u=1, i',
            'referer': 'https://onecompiler.com/python',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        }
        
        json_data = {
            'name': 'Python',
            'title': 'Python Hello World',
            'version': '3.6',
            'mode': 'python',
            'description': None,
            'extension': 'py',
            'concurrentJobs': 10,
            'languageType': 'programming',
            'active': True,
            'properties': {
                'language': 'python',
                'docs': True,
                'tutorials': True,
                'cheatsheets': True,
                'filesEditable': True,
                'filesDeletable': True,
                'files': [
                    {
                        'name': 'main.py',
                        'content': message.content,
                    },
                ],
                'newFileOptions': [
                    {
                        'helpText': 'New Python file',
                        'name': 'script${i}.py',
                        'content': '# In main file\n# import script${i}\n# print(script${i}.sum(1, 3))\n\ndef sum(a, b):\n    return a + b',
                    },
                ],
            },
            'visibility': 'public',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://onecompiler.com/api/code/exec', headers=headers, json=json_data) as response:
                data = await response.json()
                webhook_ = Webhook.from_url(dbfind.get("WebHook"), session=session)
                if data.get("exception", None):
                    return await webhook_.send(embed=discord.Embed(title="Python実行結果", description=f"```{data.get("exception", "出力なし")}```", color=discord.Color.red()), username="PythonShell", avatar_url="https://images.icon-icons.com/112/PNG/512/python_18894.png")
                await webhook_.send(embed=discord.Embed(title="Python実行結果", description=f"```{data.get("stdout", "出力なし")}```", color=discord.Color.blue()), username="PythonShell", avatar_url="https://images.icon-icons.com/112/PNG/512/python_18894.png")
                return

    shell = app_commands.Group(name="shell", description="プログラム系のコマンドです。")

    @shell.command(name="python", description="pythonシェルを使用します。")
    @app_commands.checks.cooldown(2, 10)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def python_shell(self, interaction: discord.Interaction, 有効化するか: bool):
        db = self.bot.async_db["Main"].PythonShell
        if 有効化するか:
            web = await interaction.channel.create_webhook(name="PythonShell")
            await db.replace_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}, 
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id, "WebHook": web.url}, 
                upsert=True
            )
            return await interaction.response.send_message(embed=discord.Embed(title="Pythonシェルを有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": interaction.guild.id, "Channel": interaction.channel.id})
            if result.deleted_count == 0:
                return await interaction.response.send_message(embed=discord.Embed(title="Pythonシェルは有効ではありません。", color=discord.Color.red()))
            return await interaction.response.send_message(embed=discord.Embed(title="Pythonシェルを無効化しました。", color=discord.Color.green()))
        
    @shell.command(name="compile", description="プログラムをコンパイルします。")
    @app_commands.checks.cooldown(2, 10)
    @app_commands.choices(言語=[
        app_commands.Choice(name='python',value="python"),
        app_commands.Choice(name='nodejs',value="nodejs"),
        app_commands.Choice(name='c++',value="cpp"),
        app_commands.Choice(name='c#',value="csharp"),
    ])
    async def compile_(self, interaction: discord.Interaction, 言語: app_commands.Choice[str]):
        if 言語.name == "python":
            await interaction.response.send_modal(RunPython())
        elif 言語.name == "nodejs":
            await interaction.response.send_modal(RunNodeJS())
        elif 言語.name == "c++":
            await interaction.response.send_modal(RunCPlapla())
        elif 言語.name == "c#":
            await interaction.response.send_modal(RunCSharp())

async def setup(bot):
    await bot.add_cog(ShellCog(bot))