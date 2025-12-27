import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import Form from "@/app/components/Form";
import { revalidatePath } from "next/cache";

export default async function CountPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("channel_select")?.toString();
        if (!channel) return;

        const guild_channels = await getChannels(guildid);
        const channelsData =
            Array.isArray((guild_channels as any).data)
                ? (guild_channels as any).data
                : guild_channels;

        const exists = channelsData.some((c: any) => c.id === channel);

        if (!exists) {
            return;
        }

        const db = await connectDB();

        await db
            .db("Main")
            .collection("Counting")
            .updateOne(
                {
                    Guild: Long.fromString(guildid),
                    Channel: Long.fromString(channel),
                },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        Channel: Long.fromString(channel),
                        Count: 0,
                    }
                },
                { upsert: true }
            );

        revalidatePath(`/dashboard/settings/${guildid}/count`);
    }

    async function deleteCount(formData: FormData) {
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
            .collection("Counting")
            .deleteOne({
                Guild: Long.fromString(guildid),
                Channel: Long.fromString(channel),
            });

        revalidatePath(`/dashboard/settings/${guildid}/starboard`);
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

    const guild_channels = await getChannels(guildid);

    const channelsData = Array.isArray(guild_channels?.data)
        ? guild_channels.data
        : Array.isArray(guild_channels)
        ? guild_channels
        : null;

    const db = await connectDB();
    const counts = await db.db("Main").collection("Counting").find({Guild: new Long(guildid)}).toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のカウントゲーム設定</h1>

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">登録済みカウント設定</h2>
                {counts.length > 0 ? (
                    <ul className="border rounded divide-y divide-gray-700">
                        {counts.map((item) => {
                            const channel = channelsData?.find(
                                (ch: any) => ch.id === item.Channel.toString()
                            );

                            return (
                                <li key={item.Channel.toString()} className="p-3 flex justify-between items-center">
                                    <span>
                                        {channel ? channel.name : "不明なチャンネル"}（{item.Now ? item.Now : "0"}回のカウント）
                                    </span>

                                    <form action={deleteCount}>
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

            <Form action={sendData} buttonlabel="設定を保存">
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
            </Form>
        </div>
    );
}