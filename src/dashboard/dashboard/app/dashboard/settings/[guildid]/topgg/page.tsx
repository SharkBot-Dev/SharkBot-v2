import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import { revalidatePath } from "next/cache";

export default async function TopggPage({ params }: { params: { guildid: string } }) {
    const { guildid } = await params;

    async function setTopGG(formData: FormData) {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("channel_select")?.toString();
        const text = formData.get("text")?.toString();
        const apikey = formData.get("apikey")?.toString();
        if (!channel || !text || !apikey) return;

        const guild_channels = await getChannels(guildid);
        const channelsData = Array.isArray((guild_channels as any).data)
            ? (guild_channels as any).data
            : guild_channels;

        if (!channelsData.some((c: any) => c.id === channel)) return;

        const db = await connectDB();
        await db.db("MainTwo").collection("TopggVoteAlert").updateOne(
            { guild_id: Long.fromString(guildid) },
            {
                $set: {
                    guild_id: Long.fromString(guildid),
                    channel_id: Long.fromString(channel),
                    text: text,
                    apikey: apikey
                }
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/settings/${guildid}/topgg`);
    }

    async function deleteAlert() {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const db = await connectDB();
        await db.db("MainTwo").collection("TopggVoteAlert").deleteOne({
            guild_id: Long.fromString(guildid)
        });

        revalidatePath(`/dashboard/settings/${guildid}/topgg`);
    }

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return <p className="p-4 text-red-500">ログイン情報が見つかりません。</p>;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p className="p-4 text-red-500">セッションが無効、または権限がありません。</p>;

    const guild_channels = await getChannels(guildid);
    const channelsData = Array.isArray(guild_channels?.data)
        ? guild_channels.data
        : Array.isArray(guild_channels)
        ? guild_channels
        : [];

    const db = await connectDB();
    const setting = await db.db("MainTwo").collection("TopggVoteAlert").findOne({
        guild_id: Long.fromString(guildid)
    });

    const defaultText = setting?.text || "{user}さんがVoteしてくれました！";
    const defaultChannel = setting?.channel_id ? setting.channel_id.toString() : "";

    return (
        <div className="p-6 max-w-2xl">
            <h1 className="text-2xl font-bold mb-6">{guild.name} のTop.gg Vote通知設定</h1>

            <div className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                先に、Topggのサーバー設定のサイトにアクセスし、<br/>
                {`https://dashboard.sharkbot.xyz/api/topgg/${guildid}`}<br/>をWebhookとして設定し、<br/>APIKeyをコピーしておいてください。
            </div><br/>

            {setting && (
                <div className="mb-8 p-4 border border-red-900/50 bg-red-900/10 rounded-lg">
                    <p className="text-sm text-gray-400 mb-2">現在、通知は有効です。</p>
                    <form action={deleteAlert}>
                        <button
                            type="submit"
                            className="bg-red-500/80 text-white px-4 py-2 rounded text-sm hover:bg-red-600 transition"
                        >
                            設定を削除する
                        </button>
                    </form>
                </div>
            )}

            <form action={setTopGG} className="space-y-6">
                <div>
                    <label className="block font-semibold mb-2 text-gray-200">
                        通知するチャンネルを選択
                    </label>
                    <select
                        name="channel_select"
                        defaultValue={defaultChannel}
                        className="w-full border border-gray-700 p-2.5 rounded bg-gray-900 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                        <option value="" disabled>チャンネルを選択してください</option>
                        {channelsData
                            .filter((ch: any) => ch.type === 0)
                            .map((ch: any) => (
                                <option key={ch.id} value={ch.id}>
                                    #{ch.name}
                                </option>
                            ))}
                    </select>
                </div>

                <div>
                    <label className="block font-semibold mb-2 text-gray-200">
                        通知メッセージ
                    </label>
                    <textarea
                        name="text"
                        rows={4}
                        className="w-full border border-gray-700 p-2.5 rounded bg-gray-900 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="例: {user}さんが投票しました！"
                        defaultValue={defaultText}
                        required
                    />
                    <div className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                        {"{user} .. ユーザーのメンションを埋め込みます。"}
                    </div>
                </div>

                <div>
                    <label className="block font-semibold mb-2 text-gray-200">
                        先ほどコピーしたAPIKey
                    </label>
                    <input
                        name="apikey"
                        className="w-full border border-gray-700 p-2.5 rounded bg-gray-900 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="ここにAPIKeyを入力"
                        type="text"
                        required
                    />
                </div>

                <button
                    type="submit"
                    className="w-full sm:w-auto bg-blue-600 text-white px-8 py-2.5 rounded font-medium hover:bg-blue-700 transition shadow-lg"
                >
                    設定を保存
                </button>
            </form>
        </div>
    );
}