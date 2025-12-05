import { cookies } from "next/headers";
import { getGuild, getChannels, createWebHook } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import { revalidatePath } from "next/cache";

const cooldowns = new Map<string, number>();

export default async function StarBoardPage({ params }: { params: { guildid: string } }) {
    async function createTimer(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("channel_select")?.toString();
        const interval = Number(formData.get("interval"));
        const message = formData.get("message")?.toString();
        if (!channel || !interval || !message) return;

        if (interval < 3) return;

        // クールダウン
        const now = Date.now();
        const lastTime = cooldowns.get(sessionId) ?? 0;
        const cooldownMs = 10 * 1000;

        if (now - lastTime < cooldownMs) {
            return;
        }

        cooldowns.set(sessionId, now);

        const guild_channels = await getChannels(guildid);
        const channelsData =
            Array.isArray((guild_channels as any).data)
                ? (guild_channels as any).data
                : guild_channels;

        const exists = channelsData.some((c: any) => c.id === channel);

        if (!exists) {
            console.error("チャンネルが存在しません");
            return;
        }

        const db = await connectDB();

        const count = await db
            .db("MainTwo")
            .collection("ServerTimer")
            .countDocuments({ guild_id: Long.fromString(guildid) });

        if (count >= 3) return;

        try {
            const wh = await createWebHook(channel, {
                name: "SharkBot-Timer"
            });

            await db
                .db("MainTwo")
                .collection("ServerTimer")
                .updateOne(
                    {
                        guild_id: Long.fromString(guildid),
                        channel_id: Long.fromString(channel),
                    },
                    {
                        $set: {
                            guild_id: Long.fromString(guildid),
                            channel_id: Long.fromString(channel),
                            message: message,
                            interval: interval,
                            webhook_url: wh?.data?.url
                        }
                    },
                    { upsert: true }
                );

            revalidatePath(`/dashboard/settings/${guildid}/timer`);
        } catch (e) {
            console.log(e)
            return;
        }
    }

    async function deleteTimer(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("channel_id")?.toString();
        if (!channel) return;

        const db = await connectDB();

        await db
            .db("MainTwo")
            .collection("ServerTimer")
            .deleteOne({
                guild_id: Long.fromString(guildid),
                channel_id: Long.fromString(channel),
            });

        revalidatePath(`/dashboard/settings/${guildid}/timer`);
    }

    const { guildid } = await params;
    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;

    if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p>セッションが無効です。</p>;

    const guild_channels = await getChannels(guildid);

    const channelsData = Array.isArray(guild_channels?.data)
        ? guild_channels.data
        : Array.isArray(guild_channels)
        ? guild_channels
        : null;

    if (!channelsData) return <p>チャンネルが見つかりません。</p>

    const db = await connectDB();
    const timers = await db
        .db("MainTwo").collection('ServerTimer')
        .find({ guild_id: new Long(guildid) })
        .toArray();

    function getChannelName(channels: any[], id: string | number | null) {
        if (!id) return "未設定";

        const c = channels.find((ch) => ch.id === String(id));
        return c ? `# ${c.name}` : `不明なチャンネル (${id})`;
    }

    return (
        <div className="flex flex-col gap-5">

            {/* timer create form */}
            <form action={createTimer} className="p-4 border rounded-lg flex flex-col gap-3">
                <h2 className="text-xl font-semibold mb-2">タイマー作成</h2>

                <label>チャンネル</label>
                <select
                    name="channel_select"
                    className="border p-2 rounded bg-gray-800 text-white w-full mt-1"
                    required
                >
                    {channelsData.filter((ch: any) => ch.type === 0).map((c) => (
                        <option key={c.id} value={c.id}>
                            {c.name}
                        </option>
                    ))}
                </select>

                <label>間隔（分）</label>
                <input
                    name="interval"
                    type="number"
                    min={3}
                    className="p-2 border rounded"
                    required
                />

                <label>メッセージ</label>
                <textarea
                    name="message"
                    className="p-2 border rounded"
                    rows={3}
                    required
                />

                <button className=" bg-blue-600 hover:bg-blue-500 text-white p-2 rounded">
                    作成
                </button>
            </form>

            {/* timers list */}
            <div className="p-4 border rounded-lg">
                <h2 className="text-xl font-semibold">タイマー一覧</h2>

                {timers.length === 0 && <p className="text-gray-500">タイマーはありません。</p>}

                <div className="mt-3 flex flex-col gap-3">
                    {timers.map((timer) => (
                        <form
                            key={timer.channel_id.toString()}
                            action={deleteTimer}
                            className="border p-3 rounded flex flex-col gap-1"
                        >
                            <p>
                                <strong>チャンネル:</strong> <span>{getChannelName(channelsData, timer.channel_id.toString())}</span>
                            </p>
                            <p>
                                <strong>間隔:</strong> {timer.interval} 分
                            </p>
                            <p>
                                <strong>メッセージ:</strong> {timer.message}
                            </p>

                            <input
                                type="hidden"
                                name="channel_id"
                                value={timer.channel_id.toString()}
                            />

                            <button className="mt-2 bg-red-600 hover:bg-red-500 text-white p-2 rounded">
                                削除
                            </button>
                        </form>
                    ))}
                </div>
            </div>
        </div>
    );
}