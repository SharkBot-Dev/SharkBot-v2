import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";

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

            <form action={sendData} className="flex flex-col gap-3">
                <span className="font-semibold mb-1">まとめてDiscord上のアイテムを検索 (/search multi)</span>
                <ToggleButton name="multi" defaultValue={!disabled_commands.includes('search multi')} />

                <span className="font-semibold mb-1">Discordユーザーを検索 (/search user)</span>
                <ToggleButton name="user" defaultValue={!disabled_commands.includes('search user')} />

                <span className="font-semibold mb-1">{guild.name}を検索 (/search server)</span>
                <ToggleButton name="server" defaultValue={!disabled_commands.includes('search server')} />

                <span className="font-semibold mb-1">サーバータグを検索 (/search tag)</span>
                <ToggleButton name="tag" defaultValue={!disabled_commands.includes('search tag')} />

                <span className="font-semibold mb-1">サーバーチャンネルを検索 (/search channel)</span>
                <ToggleButton name="channel" defaultValue={!disabled_commands.includes('search channel')} />

                <span className="font-semibold mb-1">このサーバーでBanされた人を検索 (/search ban)</span>
                <ToggleButton name="ban" defaultValue={!disabled_commands.includes('search ban')} />

                <span className="font-semibold mb-1">このサーバーにいるBotを検索 (/search bot)</span>
                <ToggleButton name="bot" defaultValue={!disabled_commands.includes('search bot')} />

                <span className="font-semibold mb-1">サーバーの招待リンクを検索 (/search invite)</span>
                <ToggleButton name="invite" defaultValue={!disabled_commands.includes('search invite')} />

                <span className="font-semibold mb-1">ユーザーのアバターを検索 (/search avatar)</span>
                <ToggleButton name="avatar" defaultValue={!disabled_commands.includes('search avatar')} />

                <span className="font-semibold mb-1">ユーザーのバナーを検索 (/search banner)</span>
                <ToggleButton name="banner" defaultValue={!disabled_commands.includes('search banner')} />

                <span className="font-semibold mb-1">様々なサーバーの絵文字検索 (/search emoji)</span>
                <ToggleButton name="emoji" defaultValue={!disabled_commands.includes('search emoji')} />

                <span className="font-semibold mb-1">メンバーの聞いている曲を取得 (/search spotify)</span>
                <ToggleButton name="spotify" defaultValue={!disabled_commands.includes('search spotify')} />

                <span className="font-semibold mb-1">SnowFlakeを検索する (/search snowflake)</span>
                <ToggleButton name="snowflake" defaultValue={!disabled_commands.includes('search snowflake')} />

                <span className="font-semibold mb-1">Wikipediaを検索する (/search web wikipedia)</span>
                <ToggleButton name="wikipedia" defaultValue={!disabled_commands.includes('search web wikipedia')} />

                <span className="font-semibold mb-1">気になったアニメを検索する (/search web anime)</span>
                <ToggleButton name="anime" defaultValue={!disabled_commands.includes('search web anime')} />

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>
        </div>
    );
}