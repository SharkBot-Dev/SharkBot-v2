import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import { revalidatePath } from "next/cache";

export default async function StarBoardPage({ params }: { params: { guildid: string } }) {
    async function addStarBoard(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("channel_select")?.toString();
        const emoji = formData.get("emoji")?.toString();
        if (!channel || !emoji) return;

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

        await db
            .db("Main")
            .collection("ReactionBoard")
            .updateOne(
                {
                    Guild: Long.fromString(guildid),
                    Channel: Long.fromString(channel),
                },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        Channel: Long.fromString(channel),
                        Emoji: emoji,
                    }
                },
                { upsert: true }
            );

        revalidatePath(`/dashboard/settings/${guildid}/starboard`);
    }

    async function deleteStarBoard(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("channel")?.toString();
        if (!channel) return;

        const db = await connectDB();

        await db
            .db("Main")
            .collection("ReactionBoard")
            .deleteOne({
                Guild: Long.fromString(guildid),
                Channel: Long.fromString(channel),
            });

        revalidatePath(`/dashboard/settings/${guildid}/starboard`);
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

    const db = await connectDB();
    const finded_reactionboard = await db
        .db("Main")
        .collection("ReactionBoard")
        .find({ Guild: Long.fromString(guildid) })
        .toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のスターボード</h1>

            {/* 登録一覧 */}
            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">登録済みスターボード</h2>
                {finded_reactionboard.length > 0 ? (
                    <ul className="border rounded divide-y divide-gray-700">
                        {finded_reactionboard.map((item) => {
                            const channel = channelsData?.find(
                                (ch: any) => ch.id === item.Channel.toString()
                            );

                            return (
                                <li key={item.Channel.toString()} className="p-3 flex justify-between items-center">
                                    <span>
                                        {channel ? channel.name : "不明なチャンネル"}（{item.Emoji}）
                                    </span>

                                    <form action={deleteStarBoard}>
                                        <input
                                            type="hidden"
                                            name="channel"
                                            value={item.Channel.toString()}
                                        />
                                        <button className="bg-red-600 hover:bg-red-500 text-white px-3 py-1 rounded">
                                            ❌
                                        </button>
                                    </form>
                                </li>
                            );
                        })}
                    </ul>
                ) : (
                    <p className="text-gray-400">設定がありません。</p>
                )}
            </div>

            {/* 新規登録 */}
            <form action={addStarBoard} className="flex flex-col gap-3">
                <span className="font-semibold mb-1">チャンネルを選択</span>

                <select
                    name="channel_select"
                    className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                        <option key={ch.id} value={ch.id}>
                            {ch.name}
                        </option>
                    ))}
                </select>

                <span className="font-semibold mb-1">絵文字</span>
                <input
                    type="text"
                    name="emoji"
                    className="border p-2"
                    placeholder="⭐"
                    defaultValue="⭐"
                />

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>
        </div>
    );
}