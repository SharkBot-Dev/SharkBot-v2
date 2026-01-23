import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import ItemBox from "@/app/components/ItemBox";
import ItemRow from "@/app/components/ItemRow";
import Form from "@/app/components/Form";

export default async function SearchPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const user = formData.get("user") === "true" || formData.get("user") === "on";
        const server = formData.get("server") === "true" || formData.get("server") === "on";
        const tag = formData.get("tag") === "true" || formData.get("tag") === "on";
        const channel = formData.get("channel") === "true" || formData.get("channel") === "on";
        const ban = formData.get("ban") === "true" || formData.get("ban") === "on";
        const bot = formData.get("bot") === "true" || formData.get("bot") === "on";
        const invite = formData.get("invite") === "true" || formData.get("invite") === "on";
        const avatar = formData.get("avatar") === "true" || formData.get("avatar") === "on";
        const banner = formData.get("banner") === "true" || formData.get("banner") === "on";
        const emoji = formData.get("emoji") === "true" || formData.get("emoji") === "on";
        const spotify = formData.get("spotify") === "true" || formData.get("spotify") === "on";
        const snowflake = formData.get("snowflake") === "true" || formData.get("snowflake") === "on";
        const wikipedia = formData.get("wikipedia") === "true" || formData.get("wikipedia") === "on";
        const anime = formData.get("anime") === "true" || formData.get("anime") === "on";
        const multi = formData.get("multi") === "true" || formData.get("multi") === "on";

        const db = await connectDB();
        const col = db.db("DashboardBot").collection("CommandDisabled");
        const guildFilter = { Guild: new Long(guildid) };

        async function updateToggle(flag: boolean, command: string) {
            if (flag) {
                await col.updateOne(guildFilter, { $pull: { commands: command } as any }, { upsert: true });
            } else {
                await col.updateOne(guildFilter, { $addToSet: { commands: command } }, { upsert: true });
            }
        }

        await updateToggle(user, "search user");
        await updateToggle(server, "search server");
        await updateToggle(tag, "search tag");
        await updateToggle(channel, "search channel");
        await updateToggle(ban, "search ban");
        await updateToggle(bot, "search bot");
        await updateToggle(invite, "search invite");
        await updateToggle(avatar, "search avatar");
        await updateToggle(banner, "search banner");
        await updateToggle(emoji, "search emoji");
        await updateToggle(spotify, "search spotify");
        await updateToggle(snowflake, "search snowflake");
        await updateToggle(wikipedia, "search web wikipedia");
        await updateToggle(anime, "search web anime");
        await updateToggle(multi, "search multi");
    }

    const { guildid } = await params;
    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) {
        return <p>ログイン情報が見つかりません。</p>;
    }

    const guild = await getGuild(sessionId, guildid);
    if (!guild) {
        return <p>セッションが無効です。</p>;
    }

    const db = await connectDB();
    const disabledDoc = await db.db("DashboardBot").collection("CommandDisabled").findOne({ Guild: new Long(guildid) });
    const disabled_commands: string[] = disabledDoc?.commands || [];

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のなんでも検索設定</h1>

            <Form action={sendData} buttonlabel="設定を保存">

                <ItemRow>
                    <ItemBox title="まとめてDiscord上のアイテムを検索 (/search multi)">
                        <ToggleButton name="multi" defaultValue={!disabled_commands.includes('search multi')} />
                    </ItemBox>

                    <ItemBox title="Discordユーザーを検索 (/search user)">
                        <ToggleButton name="user" defaultValue={!disabled_commands.includes('search user')} />
                    </ItemBox>

                    <ItemBox title="{guild.name}を検索 (/search server)">
                        <ToggleButton name="server" defaultValue={!disabled_commands.includes('search server')} />
                    </ItemBox>

                    <ItemBox title="サーバータグを検索 (/search tag)">
                        <ToggleButton name="tag" defaultValue={!disabled_commands.includes('search tag')} />
                    </ItemBox>

                    <ItemBox title="サーバーチャンネルを検索 (/search channel)">
                        <ToggleButton name="channel" defaultValue={!disabled_commands.includes('search channel')} />
                    </ItemBox>

                    <ItemBox title="Banされた人を検索 (/search ban)">
                        <ToggleButton name="ban" defaultValue={!disabled_commands.includes('search ban')} />
                    </ItemBox>

                    <ItemBox title="Botを検索 (/search bot)">
                        <ToggleButton name="bot" defaultValue={!disabled_commands.includes('search bot')} />
                    </ItemBox>

                    <ItemBox title="招待リンクを検索 (/search invite)">
                        <ToggleButton name="invite" defaultValue={!disabled_commands.includes('search invite')} />
                    </ItemBox>

                    <ItemBox title="アバターを検索 (/search avatar)">
                        <ToggleButton name="avatar" defaultValue={!disabled_commands.includes('search avatar')} />
                    </ItemBox>

                    <ItemBox title="バナーを検索 (/search banner)">
                        <ToggleButton name="banner" defaultValue={!disabled_commands.includes('search banner')} />
                    </ItemBox>

                    <ItemBox title="絵文字検索 (/search emoji)">
                        <ToggleButton name="emoji" defaultValue={!disabled_commands.includes('search emoji')} />
                    </ItemBox>

                    <ItemBox title="Spotifyの曲を取得 (/search spotify)">
                        <ToggleButton name="spotify" defaultValue={!disabled_commands.includes('search spotify')} />
                    </ItemBox>

                    <ItemBox title="SnowFlakeを検索 (/search snowflake)">
                        <ToggleButton name="snowflake" defaultValue={!disabled_commands.includes('search snowflake')} />
                    </ItemBox>

                    <ItemBox title="Wikipediaを検索 (/search web wikipedia)">
                        <ToggleButton name="wikipedia" defaultValue={!disabled_commands.includes('search web wikipedia')} />
                    </ItemBox>

                    <ItemBox title="アニメを検索 (/search web anime)">
                        <ToggleButton name="anime" defaultValue={!disabled_commands.includes('search web anime')} />
                    </ItemBox>
                </ItemRow>
            </Form>
        </div>
    );

}