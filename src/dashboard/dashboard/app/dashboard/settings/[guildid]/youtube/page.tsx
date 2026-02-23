import { cookies } from "next/headers";
import { getGuild, getChannels, createWebHook } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import { revalidatePath } from "next/cache";

async function subscribeChannel(channelId: string): Promise<number> {
    const topic = `https://www.youtube.com/xml/feeds/videos.xml?channel_id=${channelId}`;
    const hubUrl = "https://pubsubhubbub.appspot.com/subscribe";

    const params = new URLSearchParams();
    params.append("hub.mode", "subscribe");
    params.append("hub.topic", topic);
    params.append("hub.callback", process.env.YT_CALLBACK as string);
    params.append("hub.verify", "async");
    params.append("hub.secret", process.env.HMAC_SECRET as string);

    try {
        const response = await fetch(hubUrl, {
            method: 'POST',
            body: params,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        return response.status;
    } catch (error) {
        console.error("Subscription request failed:", error);
        throw error;
    }
}

export default async function YoutubeAlertPage({ params }: { params: { guildid: string } }) {
    const { guildid } = await params;

    async function addYoutubeAlert(formData: FormData) {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const discordChannelId = formData.get("channel_select")?.toString();
        const ytChannelId = formData.get('yt_channel')?.toString();
        if (!discordChannelId || !ytChannelId) return;

        if (!/^UC[\w-]{22}$/.test(ytChannelId)) {
            return;
        }

        const db = await connectDB();
        const collection = db.db("MainTwo").collection("YoutubeAlert");

        const count = await collection.countDocuments({ guild_id: Long.fromString(guildid) });
        if (count >= 3) return;

        const wh = await createWebHook(discordChannelId, { name: "SharkBot-Youtube" });
        if (!wh?.data?.url) return;

        await collection.updateOne(
            { guild_id: Long.fromString(guildid), channel_id: ytChannelId },
            {
                $set: {
                    guild_id: Long.fromString(guildid),
                    channel_id: ytChannelId,
                    discord_channel_id: discordChannelId,
                    webhook_url: wh.data.url
                }
            },
            { upsert: true }
        );

        await subscribeChannel(ytChannelId);
        revalidatePath(`/dashboard/settings/${guildid}/youtube`);
    }

    async function deleteAlert(formData: FormData) {
        "use server";
        const yt_channel = formData.get('yt_channel')?.toString();
        if (!yt_channel) return;

        const db = await connectDB();
        await db.db("MainTwo").collection("YoutubeAlert").deleteOne({
            guild_id: Long.fromString(guildid),
            channel_id: yt_channel
        });

        revalidatePath(`/dashboard/settings/${guildid}/youtube`);
    }

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return <p className="p-4 text-red-500">ログイン情報が見つかりません。</p>;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p className="p-4 text-red-500">権限がありません。</p>;

    const guild_channels = await getChannels(guildid);
    const channelsData = Array.isArray(guild_channels?.data) ? guild_channels.data : (Array.isArray(guild_channels) ? guild_channels : []);

    const db = await connectDB();
    const activeAlerts = await db.db("MainTwo").collection("YoutubeAlert").find({
        guild_id: Long.fromString(guildid)
    }).toArray();

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-6">{guild.name} のYoutube通知設定</h1>

            <div className="mb-10">
                <h2 className="text-lg font-semibold mb-4 text-gray-300">登録済みの通知 ({activeAlerts.length}/3)</h2>
                {activeAlerts.length === 0 ? (
                    <p className="text-gray-500 italic">登録されている通知はありません。</p>
                ) : (
                    <div className="grid gap-4">
                        {activeAlerts.map((alert) => (
                            <div key={alert.channel_id} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg border border-gray-700">
                                <div>
                                    <p className="text-blue-400 font-mono text-sm">YouTube ID: {alert.channel_id}</p>
                                    <p className="text-gray-400 text-xs">Discord Channel ID: {alert.discord_channel_id}</p>
                                </div>
                                <form action={deleteAlert}>
                                    <input type="hidden" name="yt_channel" value={alert.channel_id} />
                                    <button className="text-red-400 hover:text-red-300 text-sm font-medium transition">削除</button>
                                </form>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <hr className="border-gray-800 mb-10" />

            {activeAlerts.length < 3 && (
                <form action={addYoutubeAlert} className="space-y-6 bg-gray-900/50 p-6 rounded-xl border border-gray-800">
                    <h2 className="text-lg font-semibold text-gray-200">新しく通知を追加</h2>
                    <div>
                        <label className="block font-semibold mb-2 text-gray-300">通知を送信するDiscordチャンネル</label>
                        <select
                            name="channel_select"
                            className="w-full border border-gray-700 p-2.5 rounded bg-gray-900 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                            required
                        >
                            <option value="">選択してください</option>
                            {channelsData
                                .filter((ch: any) => ch.type === 0)
                                .map((ch: any) => (
                                    <option key={ch.id} value={ch.id}>#{ch.name}</option>
                                ))}
                        </select>
                    </div>

                    <div>
                        <label className="block font-semibold mb-2 text-gray-300">YouTube チャンネルID</label>
                        <input
                            name="yt_channel"
                            className="w-full border border-gray-700 p-2.5 rounded bg-gray-900 text-white ..."
                            placeholder="例: UCSnCdVxxIwuw7RPGxx6XjGg"
                            type="text"
                            required
                            pattern="^UC[\w-]{22}$"
                            minLength={24}
                            maxLength={24}
                            title="UCから始まる24文字のチャンネルIDを入力してください"
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full sm:w-auto bg-blue-600 text-white px-8 py-2.5 rounded font-medium hover:bg-blue-700 transition shadow-lg"
                    >
                        通知を追加
                    </button>
                </form>
            )}
        </div>
    );
}