import io
import re
import aiohttp
from deep_translator import GoogleTranslator
from discord.ext import commands
import discord
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import datetime
from models import make_embed
from models.permissions_text import PERMISSION_TRANSLATIONS
import asyncio


async def fetch_avatar(user: discord.User):
    if user.avatar:
        url_a = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar.key}"
    else:
        url_a = user.default_avatar.url
    async with aiohttp.ClientSession() as session:
        async with session.get(url_a, timeout=10) as resp:
            return await resp.read()


def wrap_text_with_ellipsis(text, font, draw, max_width, max_height, line_height):
    lines = []
    for raw_line in text.split("\n"):
        current_line = ""
        for char in raw_line:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char

            if len(lines) * line_height >= max_height - line_height * 2:
                ellipsis = "…"
                while True:
                    bbox = draw.textbbox((0, 0), current_line + ellipsis, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        break
                    if len(current_line) == 0:
                        break
                    current_line = current_line[:-1]
                lines.append(current_line + ellipsis)
                return lines

        if current_line:
            lines.append(current_line)

    return lines


def create_quote_image(author, text, avatar_bytes, background, textcolor, color: bool):
    width, height = 800, 400
    background_color = background
    text_color = textcolor

    img = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(img)

    avatar_size = (400, 400)
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar = avatar.resize(avatar_size)

    mask = Image.new("L", avatar_size, 255)
    for x in range(avatar_size[0]):
        alpha = (
            255
            if x < avatar_size[0] // 2
            else int(255 * (1 - (x - avatar_size[0] // 2) / (avatar_size[0] / 2)))
        )
        for y in range(avatar_size[1]):
            mask.putpixel((x, y), alpha)
    avatar.putalpha(mask)

    img.paste(avatar, (0, height - avatar_size[1]), avatar)

    try:
        font = ImageFont.truetype("data/DiscordFont.ttf", 30)
        name_font = ImageFont.truetype("data/DiscordFont.ttf", 20)
    except:
        font = ImageFont.load_default()
        name_font = ImageFont.load_default()

    text_x = 420
    max_text_width = width - text_x - 50

    max_text_height = height - 80
    line_height = font.size + 10

    lines = wrap_text_with_ellipsis(
        text, font, draw, max_text_width, max_text_height, line_height
    )

    total_lines = len(lines)
    line_height = font.size + 10
    text_block_height = total_lines * line_height
    text_y = (height - text_block_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        draw.text(
            ((width + text_x - 50 - line_width) // 2, text_y + i * line_height),
            line,
            fill=text_color,
            font=font,
        )

    author_text = f"- {author}"
    bbox = draw.textbbox((0, 0), author_text, font=name_font)
    author_width = bbox[2] - bbox[0]
    author_x = (width + text_x - 50 - author_width) // 2
    author_y = text_y + len(lines) * line_height + 10

    draw.text((author_x, author_y), author_text, font=name_font, fill=text_color)

    draw.text((700, 0), "SharkBot", font=name_font, fill=text_color)

    if color:
        return img
    else:
        return img.convert("L")


class ContextCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> ContextCog")


async def setup(bot: commands.Bot):
    await bot.add_cog(ContextCog(bot))

    @app_commands.context_menu(name="Make it a quote")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def make_it_a_quote(
        interaction: discord.Interaction, message: discord.Message
    ):
        await interaction.response.defer()
        av = message.author.avatar if message.author.avatar else message.author.default_avatar
        av = await av.read()
        color = True
        back = (0, 0, 0)
        text = (255, 255, 255)
        c = 0
        content = message.content

        pattern = r"<(@!?|#|@&)(\d+)>"

        def replacer(match):
            type_, id_ = match.groups()
            obj_id = int(id_)

            if type_.startswith("@"):
                user = bot.get_user(obj_id)
                return f"@{user.display_name}" if user else "@不明ユーザー"
            elif type_ == "@&":
                role = message.guild.get_role(obj_id)
                return f"@{role.name}" if role else "@不明ロール"
            elif type_ == "#":
                channel = bot.get_channel(obj_id)
                return f"#{channel.name}" if channel else "#不明チャンネル"
            return match.group(0)
        
        content = re.sub(pattern, replacer, content)

        while True:
            if c > 8:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="予期しないエラーが発生しました。",
                        color=discord.Color.red(),
                    )
                )
            miq = await asyncio.to_thread(
                create_quote_image,
                message.author.display_name,
                content,
                av,
                back,
                text,
                color,
            )
            image_binary = io.BytesIO()
            await asyncio.to_thread(miq.save, image_binary, "PNG")
            image_binary.seek(0)
            try:
                file = discord.File(fp=image_binary, filename="quote.png")
                await interaction.followup.send(
                    file=file, content=f"-# {c}回再試行しました。"
                )
            except:
                c += 1
                image_binary.close()
                await asyncio.sleep(0.5)
                continue
            image_binary.close()
            return

    @app_commands.context_menu(name="通報")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def report(interaction: discord.Interaction, message: discord.Message):
        if message.author.guild_permissions.administrator:
            return await interaction.response.send_message(
                ephemeral=True, content="管理者は通報できません。"
            )
        # await interaction.response.defer(ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        db = bot.async_db["Main"].ReportChannel
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except:
            return await interaction.followup.send(
                content="通報するチャンネルが見つかりませんでした", ephemeral=True
            )
        if dbfind is None:
            return await interaction.followup.send(
                content="通報するチャンネルが見つかりませんでした", ephemeral=True
            )
        channel = bot.get_channel(dbfind.get("Channel", None))
        if not channel:
            return await interaction.followup.send(
                content="通報するチャンネルが見つかりませんでした", ephemeral=True
            )

        await channel.send(
            embed=discord.Embed(
                title=f"{interaction.user.name} が通報しました。",
                color=discord.Color.yellow(),
            )
            .add_field(
                name="通報されたメッセージ", value=message.jump_url, inline=False
            )
            .add_field(
                name="通報されたメッセージのあるチャンネル",
                value=message.channel.mention,
                inline=False,
            )
            .add_field(
                name="通報された人",
                value=f"{message.author.mention} ({message.author.id})",
                inline=False,
            )
            .add_field(
                name="通報した人",
                value=f"{interaction.user.mention} ({interaction.user.id})",
                inline=False,
            )
            .set_thumbnail(
                url=message.author.avatar.url
                if message.author.avatar
                else message.author.default_avatar.url
            )
        )

        return await interaction.followup.send(
            content="通報が完了しました。\n運営が確認しますので、しばらくお待ちください。",
            ephemeral=True,
        )

    @app_commands.context_menu(name="メッセージ固定")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def message_pin(interaction: discord.Interaction, message: discord.Message):
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.red,
                label="削除",
                custom_id="lockmessage_delete+",
            )
        )

        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.blurple,
                label="編集",
                custom_id="lockmessage_edit+",
            )
        )

        if not message.content:
            if not message.embeds:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="メッセージの内容がありません。",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            else:
                msg = await interaction.channel.send(
                    embed=discord.Embed(
                        title=message.embeds[0].title,
                        description=message.embeds[0].description,
                        color=discord.Color.random(),
                    ),
                    view=view,
                )
                db = interaction.client.async_db["Main"].LockMessage
                await db.replace_one(
                    {"Channel": interaction.channel.id, "Guild": interaction.guild.id},
                    {
                        "Channel": interaction.channel.id,
                        "Guild": interaction.guild.id,
                        "Title": message.embeds[0].title,
                        "Desc": message.embeds[0].description,
                        "MessageID": msg.id,
                    },
                    upsert=True,
                )
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="メッセージ固定を有効化しました。",
                        color=discord.Color.green(),
                    ),
                    ephemeral=True,
                )
        msg = await interaction.channel.send(
            embed=discord.Embed(
                title="固定済みメッセージ",
                description=message.content[:1500],
                color=discord.Color.random(),
            ),
            view=view,
        )
        db = interaction.client.async_db["Main"].LockMessage
        await db.replace_one(
            {"Channel": interaction.channel.id, "Guild": interaction.guild.id},
            {
                "Channel": interaction.channel.id,
                "Guild": interaction.guild.id,
                "Title": "固定済みメッセージ",
                "Desc": message.content[:1500],
                "MessageID": msg.id,
            },
            upsert=True,
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="メッセージ固定を有効化しました。", color=discord.Color.green()
            ),
            ephemeral=True,
        )

    @app_commands.context_menu(name="翻訳-Translate")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def message_translate(
        interaction: discord.Interaction, message: discord.Message
    ):
        class TranslateMessageCommand(discord.ui.View):
            def __init__(self, message: discord.Message):
                super().__init__(timeout=None)
                self.message = message

            @discord.ui.select(
                cls=discord.ui.Select,
                placeholder="翻訳先を選択",
                options=[
                    discord.SelectOption(label="日本語へ (to ja)"),
                    discord.SelectOption(label="英語へ (to en)"),
                ],
            )
            async def select(
                self, interaction: discord.Interaction, select: discord.ui.Select
            ):
                if select.values[0] == "日本語へ (to ja)":
                    await interaction.response.defer()

                    if not message.content:
                        if not message.embeds:
                            embed = discord.Embed(
                                title="翻訳に失敗しました", color=discord.Color.red()
                            )
                            await interaction.followup.send(embed=embed)
                            return

                        if not message.embeds[0].description:
                            embed = discord.Embed(
                                title="翻訳に失敗しました", color=discord.Color.red()
                            )
                            await interaction.followup.send(embed=embed)
                            return

                        try:
                            translator = GoogleTranslator(source="auto", target="ja")
                            translated_text = translator.translate(
                                message.embeds[0].description
                            )

                            embed = discord.Embed(
                                title="翻訳 (日本語 へ)",
                                description=f"{translated_text}",
                                color=discord.Color.green(),
                            )
                            await message.reply(embed=embed)

                        except Exception:
                            embed = discord.Embed(
                                title="翻訳に失敗しました", color=discord.Color.red()
                            )
                            await interaction.followup.send(embed=embed)
                        return

                    try:
                        translator = GoogleTranslator(source="auto", target="ja")
                        translated_text = translator.translate(message.content)

                        embed = discord.Embed(
                            title="翻訳 (日本語 へ)",
                            description=f"{translated_text}",
                            color=discord.Color.green(),
                        )
                        await message.reply(embed=embed)

                    except Exception:
                        embed = discord.Embed(
                            title="翻訳に失敗しました", color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                elif select.values[0] == "英語へ (to en)":
                    await interaction.response.defer()

                    if not message.content:
                        if not message.embeds:
                            embed = discord.Embed(
                                title="翻訳に失敗しました", color=discord.Color.red()
                            )
                            await interaction.followup.send(embed=embed)
                            return

                        if not message.embeds[0].description:
                            embed = discord.Embed(
                                title="翻訳に失敗しました", color=discord.Color.red()
                            )
                            await interaction.followup.send(embed=embed)
                            return

                        try:
                            translator = GoogleTranslator(source="auto", target="en")
                            translated_text = translator.translate(
                                message.embeds[0].description
                            )

                            embed = discord.Embed(
                                title="翻訳 (英語 へ)",
                                description=f"{translated_text}",
                                color=discord.Color.green(),
                            )
                            await message.reply(embed=embed)

                        except Exception:
                            embed = discord.Embed(
                                title="翻訳に失敗しました", color=discord.Color.red()
                            )
                            await interaction.followup.send(embed=embed)
                        return

                    try:
                        translator = GoogleTranslator(source="auto", target="en")
                        translated_text = translator.translate(message.content)

                        embed = discord.Embed(
                            title="翻訳 (英語 へ)",
                            description=f"{translated_text}",
                            color=discord.Color.green(),
                        )
                        await message.reply(embed=embed)

                    except Exception:
                        embed = discord.Embed(
                            title="翻訳に失敗しました", color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)

        await interaction.response.send_message(
            ephemeral=True,
            view=TranslateMessageCommand(message),
            embed=discord.Embed(
                title="翻訳先を選択してください",
                description="Please select Language.",
                color=discord.Color.blue(),
            ).set_footer(text=f"mid:{message.id}"),
        )

    @app_commands.context_menu(name="ユーザー情報")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def user_info(interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()
        JST = datetime.timezone(datetime.timedelta(hours=9))

        if interaction.is_user_integration() and not interaction.is_guild_integration():
            embed = make_embed.success_embed(
                title=f"{member.display_name}の情報"
            )

            if member.bot:
                isbot = "はい"
            else:
                isbot = "いいえ"

            embed.add_field(
                name="基本情報",
                value=f"ID: **{member.id}**\nユーザーネーム: **{member.name}#{member.discriminator}**\n作成日: **{member.created_at.astimezone(JST)}**\nBot？: **{isbot}**\n認証Bot？: **{'はい' if member.public_flags.verified_bot else 'いいえ'}**",
            )

            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

            await interaction.followup.send(embed=embed)

            return

        if interaction.guild.get_member(member.id):
            isguild = "います。"
        else:
            isguild = "いません。"
        if member.bot:
            isbot = "はい"
        else:
            isbot = "いいえ"
        embed = discord.Embed(
            title=f"{member.display_name}の情報 (ページ1)", color=discord.Color.green()
        )
        embed.add_field(
            name="基本情報",
            value=f"ID: **{member.id}**\nユーザーネーム: **{member.name}#{member.discriminator}**\n作成日: **{member.created_at.astimezone(JST)}**\nこの鯖に？: **{isguild}**\nBot？: **{isbot}**\n認証Bot？: **{'はい' if member.public_flags.verified_bot else 'いいえ'}**",
        )
        if member.avatar:
            await interaction.followup.send(
                embed=embed.set_thumbnail(url=member.avatar.url)
            )
        else:
            await interaction.followup.send(
                embed=embed.set_thumbnail(url=member.default_avatar.url)
            )

    @app_commands.context_menu(name="アバター表示")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def avatar_show(interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()
        if member.avatar == None:

            class AvatarLayout(discord.ui.LayoutView):
                container = discord.ui.Container(
                    discord.ui.TextDisplay(
                        f"### {member.name}さんのアバター",
                    ),
                    discord.ui.TextDisplay(
                        f"ダウンロード\n[.png]({member.default_avatar.with_format('png').url})",
                    ),
                    discord.ui.Separator(),
                    discord.ui.MediaGallery(
                        discord.MediaGalleryItem(member.default_avatar.url)
                    ),
                    accent_colour=discord.Colour.green(),
                )

            await interaction.followup.send(view=AvatarLayout())

        else:

            class AvatarLayout(discord.ui.LayoutView):
                container = discord.ui.Container(
                    discord.ui.TextDisplay(
                        f"### {member.name}さんのアバター",
                    ),
                    discord.ui.TextDisplay(
                        f"ダウンロード\n[.png]({member.avatar.with_format('png').url}) [.jpg]({member.avatar.with_format('jpg').url}) [.webp]({member.avatar.with_format('webp').url})",
                    ),
                    discord.ui.Separator(),
                    discord.ui.MediaGallery(
                        discord.MediaGalleryItem(member.avatar.url)
                    ),
                    discord.ui.Separator(),
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            label="デフォルトアバターURL",
                            url=member.default_avatar.url,
                        )
                    ),
                    accent_colour=discord.Colour.green(),
                )

            await interaction.followup.send(view=AvatarLayout())

        return

    @app_commands.context_menu(name="権限を見る")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def permissions_check(
        interaction: discord.Interaction, member: discord.Member
    ):
        await interaction.response.defer()
        try:
            user_perms = [
                PERMISSION_TRANSLATIONS.get(perm, perm)
                for perm, value in member.guild_permissions
                if value
            ]
            user_perms_str = ", ".join(user_perms)
            avatar = member.avatar.url if member.avatar else member.display_avatar.url
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{member.name}さんの権限",
                    description=user_perms_str,
                    color=discord.Color.green(),
                ).set_thumbnail(url=avatar)
            )
        except Exception as e:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{member.name}さんの権限",
                    description=f"権限の取得に失敗しました。\n`{e}`",
                    color=discord.Color.red(),
                )
            )

    # メッセージに使うコマンド
    bot.tree.add_command(make_it_a_quote)
    bot.tree.add_command(report)
    bot.tree.add_command(message_pin)
    bot.tree.add_command(message_translate)

    # ユーザーに使うコマンド
    bot.tree.add_command(user_info)
    bot.tree.add_command(avatar_show)
    bot.tree.add_command(permissions_check)
