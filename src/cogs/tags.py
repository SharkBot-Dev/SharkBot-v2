import asyncio
import random
import time
import discord
from discord.ext import commands
from discord import app_commands

# import TagScriptEngine as tse
from consts import badword
import io

import re

from models import make_embed

cooldown_tags = {}


class Paginator(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current = 0

    async def update_message(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.embeds[self.current], view=self
        )

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current = (self.current - 1) % len(self.embeds)
        await self.update_message(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = (self.current + 1) % len(self.embeds)
        await self.update_message(interaction)

class TagParser:
    def evaluate_condition(self, condition: str) -> bool:
        operators = [">=", "<=", "==", "!=", ">", "<"]
        
        for op in operators:
            if op in condition:
                left_raw, right_raw = condition.split(op, 1)
                left = left_raw.strip()
                right = right_raw.strip()

                try:
                    l_val = float(left)
                    r_val = float(right)
                    if op == "==": return l_val == r_val
                    if op == "!=": return l_val != r_val
                    if op == ">":  return l_val > r_val
                    if op == "<":  return l_val < r_val
                    if op == ">=": return l_val >= r_val
                    if op == "<=": return l_val <= r_val
                except ValueError:
                    if op == "==": return left == right
                    if op == "!=": return left != right
                    return False
        return False

    def parse_if_blocks(self, text: str) -> str:
        """{if} {elif} {else} {endif} を解析する"""
        pattern = r"\{if:?([^{}]+)\}(.*?)\{endif\}"
        
        while True:
            match = re.search(pattern, text, re.DOTALL)
            if not match:
                break
            
            condition = match.group(1)
            full_content = match.group(2)
            
            parts = re.split(r"\{(elif:?[^{}]+|else)\}", full_content)
            
            res = ""
            if self.evaluate_condition(condition):
                res = parts[0]
            else:
                found = False
                for i in range(1, len(parts), 2):
                    tag = parts[i]
                    content = parts[i+1] if i+1 < len(parts) else ""
                    
                    if tag.startswith("elif"):
                        elif_cond = re.sub(r"^elif:?\s*", "", tag)
                        if self.evaluate_condition(elif_cond):
                            res = content
                            found = True
                            break
                    elif tag == "else":
                        res = content
                        found = True
                        break
                if not found:
                    res = ""

            text = text[:match.start()] + res + text[match.end():]
        return text

    def process_variables(self, text: str) -> str:
        """{set:変数名|値} と {get:変数名} を処理する"""
        variables = {}

        def set_var(match):
            var_name = match.group(1).strip()
            value = match.group(2).strip()
            variables[var_name] = value
            return ""

        text = re.sub(r"\{set:([^|]+)\|([^}]+)\}", set_var, text)

        for _ in range(5):
            changed = False
            for var_name, value in variables.items():
                placeholder = f"{{get:{var_name}}}"
                if placeholder in text:
                    text = text.replace(placeholder, value)
                    changed = True
            if not changed: break
        return text

    async def parse_tags(self, text: str, args: str, author: discord.Member, guild: discord.Guild):
        placeholders = {
            "{args}": args or "",
            "{author}": author.display_name,
            "{author_id}": str(author.id),
            "{author_mention}": author.mention,
            "{guild_name}": guild.name,
            "{count}": str(guild.member_count)
        }
        for placeholder, value in placeholders.items():
            text = text.replace(placeholder, value)

        def replace_random(match):
            try:
                parts = re.split(r'[~,]', match.group(1))
                low, high = int(parts[0]), int(parts[1])
                return str(random.randint(min(low, high), max(low, high)))
            except: return "0"
        text = re.sub(r'\{random:(-?\d+[~,]-?\d+)\}', replace_random, text)

        text = self.process_variables(text)

        text = self.parse_if_blocks(text)

        text = re.sub(r'\{choice:(.*?)\}', lambda m: random.choice(m.group(1).split('|')), text)

        role_pattern = r"\{addrole:(\d+)\}"
        role_ids = set(re.findall(role_pattern, text))
        for role_id in role_ids:
            try:
                role = guild.get_role(int(role_id))
                if role:
                    await author.add_roles(role, reason="Tag execution")
                    await asyncio.sleep(0.2)
            except: pass

        text = re.sub(role_pattern, "", text)
        return text.strip()

class TagsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> TagsCog")

    def evaluate_condition(self, condition: str) -> bool:
        if "==" in condition:
            left, right = condition.split("==", 1)
            return left.strip() == right.strip()
        elif "!=" in condition:
            left, right = condition.split("!=", 1)
            return left.strip() != right.strip()
        return False

    def parse_if_blocks(self, text: str) -> str:
        """
        {if:条件} ... {elif:条件} ... {else} ... {endif} を解析する
        """
        pattern = r"\{if:?([^{}]+)\}(.*?)\{endif\}"
        
        while True:
            match = re.search(pattern, text, re.DOTALL)
            if not match:
                break
            
            condition = match.group(1)
            full_content = match.group(2)
            
            parts = re.split(r"\{(elif:?[^{}]+|else)\}", full_content)
            
            res = ""
            if self.evaluate_condition(condition):
                res = parts[0]
            else:
                found = False
                for i in range(1, len(parts), 2):
                    tag = parts[i]
                    content = parts[i+1] if i+1 < len(parts) else ""
                    
                    if tag.startswith("elif"):
                        elif_cond = re.sub(r"^elif:?\s*", "", tag)
                        if self.evaluate_condition(elif_cond):
                            res = content
                            found = True
                            break
                    elif tag == "else":
                        res = content
                        found = True
                        break
                if not found:
                    res = ""

            text = text[:match.start()] + res + text[match.end():]
            
        return text

    def process_variables(self, text: str) -> str:
        """{set:変数名|値} を処理し、{get:変数名} を置換する"""
        
        variables = {}

        def set_var(match):
            var_name = match.group(1).strip()
            value = match.group(2).strip()
            variables[var_name] = value
            return ""

        text = re.sub(r"\{set:([^|]+)\|([^}]+)\}", set_var, text)

        for _ in range(5):
            changed = False
            for var_name, value in variables.items():
                placeholder = f"{{get:{var_name}}}"
                if placeholder in text:
                    text = text.replace(placeholder, value)
                    changed = True
            if not changed: break
            
        return text

    async def parse_tags(self, text: str, args: str, author: discord.Member, guild: discord.Guild):
        placeholders = {
            "{args}": args or "引数なし",
            "{author}": author.display_name,
            "{author_id}": str(author.id),
            "{author_mention}": author.mention,
            "{guild_name}": guild.name,
            "{count}": str(guild.member_count)
        }

        for placeholder, value in placeholders.items():
            text = text.replace(placeholder, value)

        def replace_random(match):
            try:
                parts = re.split(r'[~,]', match.group(1))
                val1 = int(parts[0])
                val2 = int(parts[1])

                limit = 1_000
                val1 = max(min(val1, limit), -limit)
                val2 = max(min(val2, limit), -limit)

                low = min(val1, val2)
                high = max(val1, val2)

                return str(random.randint(low, high))
            except (ValueError, IndexError, OverflowError):
                return "0"
        
        text = re.sub(r'\{random:(-?\d+[~,]-?\d+)\}', replace_random, text)
        text = re.sub(r'\{choice:(.*?)\}', lambda m: random.choice(m.group(1).split('|')), text)

        text = self.process_variables(text)

        text = self.parse_if_blocks(text)

        role_pattern = r"\{addrole:(\d+)\}"
        role_ids = set(re.findall(role_pattern, text))
        for role_id in role_ids:
            try:
                role = guild.get_role(int(role_id))
                if role:
                    await author.add_roles(role, reason="Tag execution")
                    await asyncio.sleep(0.2)
            except:
                pass

        text = re.sub(role_pattern, "", text)

        return text.strip()

    tag = app_commands.Group(name="tag", description="タグスクリプトを設定します。")

    @tag.command(name="create", description="tagを作成します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tag_create(self, interaction: discord.Interaction, 名前: str):
        class TagCreateModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Tagを作成する。", timeout=180)

            code = discord.ui.Label(
                text="コードを入力",
                description="コードを入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.long, required=True
                ),
            )

            desc = discord.ui.Label(
                text="説明を入力",
                description="説明を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True, default="なし"
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                assert isinstance(self.code.component, discord.ui.TextInput)
                assert isinstance(self.desc.component, discord.ui.TextInput)
                lower_script = self.code.component.value.lower()
                for word in badword.badwords:
                    if word.lower() in lower_script:
                        embed = make_embed.error_embed(title="Tag作成に失敗しました。")
                        return await interaction_.response.send_message(embed=embed)

                db = interaction.client.async_db["Main"].Tags
                await db.update_one(
                    {"command": 名前, "guild_id": interaction_.guild.id},
                    {
                        "$set": {
                            "tagscript": self.code.component.value,
                            "text": self.desc.component.value,
                        }
                    },
                    upsert=True,
                )
                embed = make_embed.success_embed(title="Tagを作成しました。")
                await interaction_.response.send_message(embed=embed)

        await interaction.response.send_modal(TagCreateModal())

    @tag.command(name="delete", description="tagを削除します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tag_delete(self, interaction: discord.Interaction, 名前: str):
        db = self.bot.async_db["Main"].Tags
        doc = await db.find_one({"guild_id": interaction.guild.id, "command": 名前})
        if not doc:
            embed = make_embed.error_embed(title="そのTagは存在しません。")
            return await interaction.response.send_message(embed=embed)

        await db.delete_one({"guild_id": interaction.guild.id, "command": 名前})

        embed = make_embed.success_embed(title="Tagを削除しました。")

        await interaction.response.send_message(embed=embed)

    @tag.command(name="tags", description="タグリストを表示します。")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tags_list(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db_prefix = self.bot.async_db["DashboardBot"].CustomPrefixBot
        doc = await db_prefix.find_one({"Guild": interaction.guild.id})
        PREFIX = doc.get("Prefix", "!.") if doc else "!."

        db_tags = self.bot.async_db["Main"].Tags
        cursor = db_tags.find({"guild_id": interaction.guild.id})
        tags = [doc async for doc in cursor]

        if not tags:
            return await interaction.followup.send(
                "このサーバーにはタグが登録されていません。"
            )

        em_s = []
        c = 1

        for start in range(0, len(tags), 10):
            embed = discord.Embed(
                title=f"{interaction.guild.name} のタグ一覧", color=discord.Color.blue()
            )
            for cmd in tags[start : start + 10]:
                embed.add_field(
                    name=cmd["command"] + f" ({cmd.get('used', 0)}回)", value=cmd.get("text", "説明なし"), inline=False
                )

            embed.set_footer(text=f"{c} ページ目 / Prefix: {PREFIX}")
            c += 1

            em_s.append(embed)

        await interaction.followup.send(embed=em_s[0], view=Paginator(em_s))

    @tag.command(name="use", description="tagを使用します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tags_use(
        self, interaction: discord.Interaction, コマンド名: str, 引数: str = "No Args."
    ):
        await interaction.response.defer()
        db_tags = self.bot.async_db["Main"].Tags
        doc = await db_tags.find_one(
            {"guild_id": interaction.guild.id, "command": コマンド名}
        )
        if doc:
            try:
                ts_script = doc["tagscript"]

                await interaction.followup.send(
                    await TagParser().parse_tags(ts_script, 引数, interaction.user, interaction.guild)
                )
            except Exception as e:
                return await interaction.followup.send("エラーが発生しました。")
            
            await db_tags.update_one({
                "guild_id": interaction.guild.id, "command": コマンド名
            }, {
                "$inc": {
                    "used": 1
                }
            })
        else:
            await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="Tagが見つかりません。",
                    description=f"`/tag create`で作成できます。",
                )
            )

    @tag.command(name="export", description="タグをエクスポートします。")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tags_export(self, interaction: discord.Interaction, 名前: str):
        db_tags = self.bot.async_db["Main"].Tags
        doc = await db_tags.find_one(
            {"guild_id": interaction.guild.id, "command": 名前}
        )
        if doc:
            i = io.StringIO(str(doc.get("tagscript", "None")))
            await interaction.response.send_message(
                file=discord.File(i, filename="tag.txt")
            )
            i.close()
        else:
            await interaction.response.send_message(
                content="そのタグが見つかりません。", ephemeral=True
            )
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        db_prefix = self.bot.async_db["DashboardBot"].CustomPrefixBot
        doc_prefix = await db_prefix.find_one({"Guild": message.guild.id})
        
        custom_prefix = doc_prefix.get("Prefix") if doc_prefix else None
        
        default_prefixes = self.bot.command_prefix
        if callable(default_prefixes):
            default_prefixes = default_prefixes(self.bot, message)
        
        if isinstance(default_prefixes, str):
            default_prefixes = [default_prefixes]

        valid_prefixes = set(default_prefixes)
        if custom_prefix:
            valid_prefixes.add(custom_prefix)

        used_prefix = None
        for p in valid_prefixes:
            if message.content.startswith(p):
                used_prefix = p
                break
        
        if not used_prefix:
            return

        content_no_prefix = message.content[len(used_prefix):].lstrip()
        parts = content_no_prefix.split()
        if not parts:
            return
            
        cmd_name = parts[0]
        args = " ".join(parts[1:]) if len(parts) > 1 else ""

        db_tags = self.bot.async_db["Main"].Tags
        doc_tag = await db_tags.find_one(
            {"guild_id": message.guild.id, "command": cmd_name}
        )

        if doc_tag:
            try:
                current_time = time.time()
                last_message_time = cooldown_tags.get(message.guild.id, 0)
                if current_time - last_message_time < 3:
                    return
                cooldown_tags[message.guild.id] = current_time

                ts_script = doc_tag["tagscript"]
                parsed_content = await TagParser().parse_tags(ts_script, args, message.author, message.guild)

                if parsed_content.strip():
                    await message.channel.send(parsed_content)

                await db_tags.update_one(
                    {"guild_id": message.guild.id, "command": cmd_name},
                    {"$inc": {"used": 1}}
                )
            except Exception as e:
                embed = make_embed.error_embed(
                    title="Tagでエラーが発生しました。", 
                    description=f"```{e}```"
                )
                await message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            a = None
            return a


async def setup(bot):
    await bot.add_cog(TagsCog(bot))
