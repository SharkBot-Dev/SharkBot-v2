from discord.ext import commands
from discord import app_commands
import discord
from models import make_embed
import io


class GroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> GroupCog")

    group = app_commands.Group(name="group", description="グループ関連のコマンドです。")

    @group.command(name="create", description="グループを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_create(
        self, interaction: discord.Interaction, グループ名: str, 説明: str
    ):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名})

        if dbfing:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="そのグループはすでに存在しています。",
                    description="別の名前を指定してください。",
                )
            )

        await db.update_one(
            {"Name": グループ名},
            {
                "$set": {"Owner": interaction.user.id, "Text": 説明},
                "$addToSet": {"Member": interaction.user.id},
            },
            upsert=True,
        )

        return await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="グループを作成しました。",
                description="フレンドをグループに誘ってみよう！",
            )
        )

    @group.command(
        name="setrule", description="グループのルールを設定します（オーナー専用）。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_setrule(
        self, interaction: discord.Interaction, グループ名: str, ルール: str
    ):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名})

        if dbfing is None:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="そのグループは存在しません。",
                    description="ルールを設定できません。",
                )
            )

        if dbfing["Owner"] != interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="権限がありません。",
                    description="ルールを変更できるのはグループのオーナーだけです。",
                )
            )

        await db.update_one({"Name": グループ名}, {"$set": {"Rules": ルール}})

        return await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"グループ「{グループ名}」のルールを更新しました。",
                description=ルール,
            )
        )

    @group.command(name="rules", description="グループのルールを表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_rules(self, interaction: discord.Interaction, グループ名: str):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名})

        if dbfing is None:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="そのグループは存在しません。",
                    description="ルールを表示できません。",
                )
            )

        rules = dbfing.get("Rules", "ルールは設定されていません。")
        return await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"グループ「{グループ名}」のルール", description=rules
            )
        )

    @group.command(name="info", description="グループの情報を表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_info(self, interaction: discord.Interaction, グループ名: str):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名})

        if dbfing is None:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="そのグループは存在しません。",
                    description="ルールを表示できません。",
                )
            )

        if interaction.user.id not in dbfing.get("Member", []):
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="参加していません。",
                    description="参加していないグループの情報は表示できません。",
                ),
            )

        rules = dbfing.get("Rules", "ルールは設定されていません。")
        return await interaction.response.send_message(
            embed=make_embed.success_embed(title=f"グループ「{グループ名}」の情報")
            .add_field(name="説明", value=dbfing.get("Text", "説明なし"), inline=False)
            .add_field(name="ルール", value=rules, inline=False)
        )

    @group.command(name="delete", description="グループを削除します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_delete(self, interaction: discord.Interaction, グループ名: str):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名, "Owner": interaction.user.id})

        if dbfing is None:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのグループはありません。",
                    description="削除できるのはあなたがオーナーのグループだけです。",
                ),
            )

        await db.delete_one({"Name": グループ名, "Owner": interaction.user.id})
        await interaction.response.send_message(
            embed=make_embed.success_embed(title="グループを削除しました。")
        )

    @group.command(name="join", description="グループに参加します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_join(self, interaction: discord.Interaction, グループ名: str):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名})

        if dbfing is None:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのグループはありません。",
                    description="グループが見つからないため参加できません。",
                ),
            )

        await db.update_one(
            {"Name": グループ名}, {"$addToSet": {"Member": interaction.user.id}}
        )

        return await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="グループに参加しました。",
                description="まずはグループのルールを確認してみよう！",
            )
        )

    @group.command(name="leave", description="グループから退出します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_leave(self, interaction: discord.Interaction, グループ名: str):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名})

        if dbfing is None:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのグループはありません。",
                    description="グループが見つからないため退出できません。",
                ),
            )

        if dbfing["Owner"] == interaction.user.id:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="オーナーは退出できません。",
                    description="オーナーは退出できません。\n退出したい場合はグループを削除してください。",
                ),
            )

        if interaction.user.id not in dbfing.get("Member", []):
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="参加していません。",
                    description="参加していないグループからは退出できません。",
                ),
            )

        await db.update_one(
            {"Name": グループ名}, {"$pull": {"Member": interaction.user.id}}
        )

        return await interaction.response.send_message(
            embed=make_embed.success_embed(title="グループから退出しました。")
        )

    @group.command(
        name="kick", description="グループからメンバーを退出させます（オーナー専用）。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_kick(
        self, interaction: discord.Interaction, グループ名: str, ユーザー: discord.User
    ):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名})

        if dbfing is None:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのグループはありません。",
                    description="グループが見つからないためキックできません。",
                ),
            )

        if dbfing["Owner"] != interaction.user.id:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="権限がありません。",
                    description="メンバーをキックできるのはグループのオーナーだけです。",
                ),
            )

        if dbfing["Owner"] == ユーザー.id:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(title="オーナーはキックできません。"),
            )

        if ユーザー.id not in dbfing.get("Member", []):
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのユーザーは参加していません。",
                    description="別のユーザーを指定してください。",
                ),
            )

        await db.update_one({"Name": グループ名}, {"$pull": {"Member": ユーザー.id}})

        return await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"{ユーザー.display_name} をグループから退出させました。"
            )
        )

    @group.command(name="list", description="参加しているグループを表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_list(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].Group
        cursor = db.find({"Member": interaction.user.id})

        groups = [doc async for doc in cursor]
        if not groups:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="グループが見つかりません。",
                    description="まだどのグループにも参加していません。",
                )
            )

        description = "\n".join(
            [f"・**{g['Name']}** - {g.get('Text', '説明なし')}" for g in groups]
        )
        return await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"{interaction.user.display_name}さんの参加グループ一覧",
                description=description,
            )
        )

    @group.command(
        name="members", description="参加しているグループのメンバーを表示します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def group_members(self, interaction: discord.Interaction, グループ名: str):
        db = self.bot.async_db["Main"].Group
        dbfing = await db.find_one({"Name": グループ名})

        if dbfing is None:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのグループはありません。",
                    description="グループが存在しないため表示できません。",
                ),
            )

        if interaction.user.id not in dbfing.get("Member", []):
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="参加していません。",
                    description="参加していないグループのメンバーは確認できません。",
                ),
            )

        members = dbfing.get("Member", [])
        if not members:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="メンバーがいません。",
                    description="このグループにはまだメンバーがいません。",
                )
            )

        member_mentions = []
        for mid in members:
            user = interaction.guild.get_member(mid)
            member_mentions.append(
                f"{user.name} ({mid})" if user else f"Unknown ({mid})"
            )

        description = io.StringIO("\n".join(member_mentions))
        await interaction.response.send_message(
            file=discord.File(description, "members.txt")
        )
        description.close()


async def setup(bot):
    await bot.add_cog(GroupCog(bot))
