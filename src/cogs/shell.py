from discord.ext import commands
import discord
import sys
import time
import aiohttp
from discord import Webhook
from discord import app_commands

from models import command_disable, make_embed

cooldown_python_shell = {}


class RunPython(discord.ui.Modal, title="Pythonを実行"):
    code = discord.ui.TextInput(
        label="コードを入力",
        placeholder="print(1+1)",
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
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
                        "content": self.code.value,
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
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="Pythonの実行結果",
                        description=f"```{data.get('stdout', '')}```",
                    )
                )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.followup.send("エラー。\nWhileなどは使用できません。")


class RunNodeJS(discord.ui.Modal, title="NodoJSを実行"):
    code = discord.ui.TextInput(
        label="コードを入力",
        placeholder="console.log(1+1);",
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
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
                        "content": self.code.value,
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
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="Nodejsの実行結果",
                        description=f"```{data.get('stdout', '')}```",
                    )
                )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.followup.send("エラー。")


class RunCPlapla(discord.ui.Modal, title="C++を実行"):
    code = discord.ui.TextInput(
        label="コードを入力",
        placeholder='printf("aaa")',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            "accept": "*/*",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "authorization": "Bearer undefined",
            "content-type": "application/json",
            "origin": "https://onecompiler.com",
            "priority": "u=1, i",
            "referer": "https://onecompiler.com/cpp",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

        json_data = {
            "name": "C++",
            "title": "C++ Hello World",
            "version": "latest",
            "mode": "c_cpp",
            "description": None,
            "extension": "cpp",
            "languageType": "programming",
            "active": True,
            "properties": {
                "language": "cpp",
                "docs": True,
                "tutorials": True,
                "cheatsheets": True,
                "filesEditable": True,
                "filesDeletable": True,
                "files": [
                    {
                        "name": "Main.cpp",
                        "content": self.code.value,
                    },
                ],
                "newFileOptions": [
                    {
                        "helpText": "New C++ file",
                        "name": "NewFile${i}.cpp",
                        "content": '#include <iostream>\n\n// Follow the steps below to use this file\n\n// 1. In main file add the following include \n// #include "NewFile${i}.cpp"\n\n// 2. Add the following in the code\n// sayHelloFromNewFile${i}();\n\nvoid sayHelloFromNewFile${i}() {\n    std::cout << "\\nHello from New File ${i}!\\n";\n}\n',
                    },
                    {
                        "helpText": "New Text file",
                        "name": "sample${i}.txt",
                        "content": "Sample text file!",
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
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="C++の実行結果",
                        description=f"```{data.get('stdout', '')}```",
                    )
                )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.followup.send(f"エラー。\n{sys.exc_info()}")


class RunCSharp(discord.ui.Modal, title="C#を実行"):
    code = discord.ui.TextInput(
        label="コードを入力",
        placeholder='Console.WriteLine("Hello world!");',
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        headers = {
            "accept": "*/*",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "authorization": "Bearer undefined",
            "content-type": "application/json",
            "origin": "https://onecompiler.com",
            "priority": "u=1, i",
            "referer": "https://onecompiler.com/csharp",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }

        json_data = {
            "name": "C#",
            "title": "C# Hello World!",
            "mode": "csharp",
            "description": None,
            "extension": "cs",
            "languageType": "programming",
            "active": True,
            "properties": {
                "language": "csharp",
                "docs": True,
                "tutorials": True,
                "cheatsheets": True,
                "filesEditable": True,
                "filesDeletable": True,
                "files": [
                    {
                        "name": "HelloWorld.cs",
                        "content": self.code.value,
                    },
                ],
                "newFileOptions": [
                    {
                        "helpText": "New C# file",
                        "name": "NewClass${i}.cs",
                        "content": 'using System;\n\nnamespace HelloWorld\n{\n\tpublic class NewClass${i}\n\t{\n\t\t// Follow the steps below to use this file\n\n\t\t// 1. In the main file (e.g., HelloWorld.cs), create an instance of this class:\n\t\t// NewClass${i} instance${i} = new NewClass${i}();\n\n\t\t// 2. Call the method to get the greeting message:\n\t\t// Console.WriteLine(instance${i}.SayHelloFromNewClass());\n\n\t\tpublic string SayHelloFromNewClass()\n\t\t{\n\t\t\treturn "Hello from New Class ${i}!";\n\t\t}\n\t}\n}',
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
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="C#の実行結果",
                        description=f"```{data.get('stdout', '')}```",
                    )
                )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.followup.send("エラー。")


class ShellCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shell_commands = {
            "ls": "ディレクトリの内容を一覧表示",
            "cd": "ディレクトリの移動",
            "pwd": "カレントディレクトリのパスを表示",
            "cp": "ファイルをコピー",
            "mv": "ファイルを移動または名前を変更",
            "rm": "ファイルを削除",
            "mkdir": "新しいディレクトリを作成",
            "rmdir": "空のディレクトリを削除",
            "touch": "空のファイルを作成またはタイムスタンプを変更",
            "cat": "ファイルの内容を表示",
            "more/less": "ファイルの内容をページ単位で表示",
            "head/tail": "ファイルの先頭/末尾部分を表示",
            "find": "ファイルを検索",
            "locate": "インデックスを使用してファイルを高速検索",
            "du": "ディスク使用量を表示",
            "df": "ファイルシステムのディスク使用量を表示",
            "chmod": "ファイルのアクセス許可を変更",
            "chown": "ファイルの所有者を変更",
            "ln": "ハードリンクまたはシンボリックリンクを作成",
            "grep": "テキストを検索",
            "awk": "テキストを処理",
            "sed": "ストリームエディタ（テキストの置換など）",
            "sort": "テキストを並べ替え",
            "uniq": "重複行を削除",
            "wc": "行数、単語数、バイト数をカウント",
            "cut": "テキストを分割",
            "paste": "テキストを結合",
            "tr": "文字の置換・削除",
            "ps": "現在のプロセスを表示",
            "top/htop": "リアルタイムでプロセス情報を表示",
            "kill": "プロセスを終了",
            "killall": "プロセス名でプロセスを終了",
            "uptime": "システムの稼働時間を表示",
            "uname": "システム情報を表示",
            "free": "メモリ使用量を表示",
            "iostat": "I/O統計情報を表示",
            "vmstat": "仮想メモリの統計情報を表示",
            "lsof": "開いているファイルの一覧を表示",
            "dmesg": "カーネルのメッセージを表示",
            "service": "サービスを管理",
            "systemctl": "systemdサービスを管理",
            "ping": "ネットワーク接続を確認",
            "traceroute": "パケットの経路を追跡",
            "ifconfig/ip": "ネットワークインターフェースの設定を表示・管理",
            "netstat/ss": "ネットワーク接続、ルーティングテーブルなどを表示",
            "scp": "セキュアコピー",
            "rsync": "リモートおよびローカル間でファイルを同期",
            "wget": "ファイルをダウンロード",
            "curl": "データを転送",
            "tar": "アーカイブを作成・展開",
            "gzip/gunzip": "ファイルを圧縮/展開",
            "zip/unzip": "ファイルを圧縮/展開",
            "chgrp": "ファイルのグループを変更",
            "passwd": "パスワードを変更",
            "useradd/userdel": "ユーザーを追加/削除",
            "usermod": "ユーザー情報を変更",
            "groupadd/groupdel": "グループを追加/削除",
            "groups": "ユーザーが所属するグループを表示",
            "echo": "メッセージを表示",
            "date": "日付と時刻を表示・設定",
            "cal": "カレンダーを表示",
            "who/w": "ログインしているユーザーを表示",
            "man": "マニュアルページを表示",
            "alias/unalias": "コマンドのエイリアスを設定/削除",
            "history": "コマンド履歴を表示",
            "crontab": "定期的にコマンドを実行するスケジュールを設定",
            "at": "指定した時刻にコマンドを実行",
            "nohup": "コマンドを終了してもバックグラウンドで実行し続ける",
        }
        print("init -> ShellCog")

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
                        "content": message.content,
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
                webhook_ = Webhook.from_url(dbfind.get("WebHook"), session=session)
                if data.get("exception", None):
                    return await webhook_.send(
                        embed=discord.Embed(
                            title="Python実行結果",
                            description=f"```{data.get('exception', '出力なし')}```",
                            color=discord.Color.red(),
                        ),
                        username="PythonShell",
                        avatar_url="https://images.icon-icons.com/112/PNG/512/python_18894.png",
                    )
                await webhook_.send(
                    embed=discord.Embed(
                        title="Python実行結果",
                        description=f"```{data.get('stdout', '出力なし')}```",
                        color=discord.Color.blue(),
                    ),
                    username="PythonShell",
                    avatar_url="https://images.icon-icons.com/112/PNG/512/python_18894.png",
                )
                return
            
    @commands.Cog.listener("on_message")
    async def on_message_nodejs_shell(self, message: discord.Message):
        if message.author.bot:
            return

        db = self.bot.async_db["MainTwo"].NodeJsShell
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
                        "content": message.clean_content,
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
                webhook_ = Webhook.from_url(dbfind.get("WebHook"), session=session)
                if data.get("exception", None):
                    return await webhook_.send(
                        embed=discord.Embed(
                            title="NodeJS実行結果",
                            description=f"```{data.get('exception', '出力なし')}```",
                            color=discord.Color.red(),
                        ),
                        username="NodeJsShell",
                        avatar_url="https://images-cdn.openxcell.com/wp-content/uploads/2024/07/25090553/nodejs-inner.webp",
                    )
                await webhook_.send(
                    embed=discord.Embed(
                        title="NodeJS実行結果",
                        description=f"```{data.get('stdout', '出力なし')}```",
                        color=discord.Color.blue(),
                    ),
                    username="NodeJsShell",
                    avatar_url="https://images-cdn.openxcell.com/wp-content/uploads/2024/07/25090553/nodejs-inner.webp",
                )
                return

    shell = app_commands.Group(name="shell", description="プログラム系のコマンドです。")

    @shell.command(name="python", description="pythonシェルを使用します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def python_shell(self, interaction: discord.Interaction, 有効化するか: bool):
        db = self.bot.async_db["Main"].PythonShell
        if 有効化するか:
            web = await interaction.channel.create_webhook(name="PythonShell")
            await db.update_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
                {
                    "$set": {
                        "Guild": interaction.guild.id,
                        "Channel": interaction.channel.id,
                        "WebHook": web.url,
                    }
                },
                upsert=True,
            )
            return await interaction.response.send_message(
                embed=make_embed.success_embed(title="Pythonシェルを有効化しました。")
            )
        else:
            result = await db.delete_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
            )
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=make_embed.error_embed(
                        title="Pythonシェルは有効ではありません。"
                    )
                )
            return await interaction.response.send_message(
                embed=make_embed.success_embed(title="Pythonシェルを無効化しました。")
            )
        
    @shell.command(name="nodejs", description="nodejsシェルを使用します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nodejs_shell(self, interaction: discord.Interaction, 有効化するか: bool):
        db = self.bot.async_db["MainTwo"].NodeJsShell
        if 有効化するか:
            web = await interaction.channel.create_webhook(name="NodeJsShell")
            await db.update_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
                {
                    "$set": {
                        "Guild": interaction.guild.id,
                        "Channel": interaction.channel.id,
                        "WebHook": web.url,
                    }
                },
                upsert=True,
            )
            return await interaction.response.send_message(
                embed=make_embed.success_embed(title="NodeJSシェルを有効化しました。")
            )
        else:
            result = await db.delete_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
            )
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=make_embed.error_embed(
                        title="NodeJSシェルは有効ではありません。"
                    )
                )
            return await interaction.response.send_message(
                embed=make_embed.success_embed(title="NodeJSシェルを無効化しました。")
            )

    @shell.command(name="math", description="計算式を計算します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def compile_math(self, interaction: discord.Interaction, 計算式: str):
        await interaction.response.defer()
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
                        "content": f"print(eval('{計算式}'))",
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
                ans = data.get("stdout", "出力なし")
                await interaction.followup.send(
                    embed=make_embed.success_embed(title="計算結果")
                    .add_field(name="計算式", value=f"```{計算式}```", inline=False)
                    .add_field(name="計算結果", value=f"```{ans}```", inline=False)
                )

    @shell.command(name="linux", description="Linuxコマンドを検索します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def linux_search(
        self, interaction: discord.Interaction, コマンド名: str = None, 説明: str = None
    ):
        if コマンド名 is None and 説明 is None:
            await interaction.response.send_message(
                ephemeral=True,
                content="`/shell linux [コマンド名|説明]` で使用できます。",
            )
            return
        await interaction.response.defer()
        cmds = self.shell_commands
        for k, v in cmds.items():
            if not コマンド名 is None:
                if コマンド名 in k:
                    return await interaction.followup.send(
                        embed=make_embed.success_embed(title="Linuxコマンド検索結果")
                        .add_field(name="コマンド名", value=k, inline=False)
                        .add_field(name="説明", value=v, inline=False)
                    )
            if not 説明 is None:
                if 説明 in v:
                    return await interaction.followup.send(
                        embed=make_embed.success_embed(title="Linuxコマンド検索結果")
                        .add_field(name="コマンド名", value=k, inline=False)
                        .add_field(name="説明", value=v, inline=False)
                    )

        return await interaction.followup.send(
            embed=make_embed.error_embed(title="検索結果が見つかりません。")
        )

    @shell.command(name="compile", description="プログラムをコンパイルします。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        言語=[
            app_commands.Choice(name="python", value="python"),
            app_commands.Choice(name="nodejs", value="nodejs"),
            app_commands.Choice(name="c++", value="cpp"),
            app_commands.Choice(name="c#", value="csharp"),
        ]
    )
    async def compile_(
        self, interaction: discord.Interaction, 言語: app_commands.Choice[str]
    ):
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
