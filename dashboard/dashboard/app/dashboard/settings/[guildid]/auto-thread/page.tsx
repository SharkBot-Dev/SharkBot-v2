import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

export default async function AutoTheradPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const name = (formData.get("name") as string)?.slice(0, 20);
        const channel = formData.get("channel") as string;

        if (!name || !channel) return;

        const db = await connectDB();
        const db_datas = db.db("MainTwo");
        const g = await db_datas.collection("AutoThread").findOne({Guild: Number(guildid)});
        let channels: Record<string, { ThreadName: string }> = {};
        if (g) {
            channels = g.Channels as Record<string, { ThreadName: string }>;
        }
        channels[channel] = {
            'ThreadName': name
        }
        
        await db_datas.collection("AutoThread").updateOne(
            { Guild: new Long(guildid) },
            {
                $set: {
                    Guild: new Long(guildid),
                    Channels: channels,
                    UpdatedAt: new Date(),
                },
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/settings/${guildid}/auto-thread`);
    }

    async function deleteData(formData: FormData) {
        "use server";

        const { guildid } = await params;

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("channel") as string;

        if (!channel) return;

        const db = await connectDB();
        const db_datas = db.db("MainTwo");
        const g = await db_datas.collection("AutoThread").findOne({Guild: Number(guildid)});
        let channels: Record<string, { ThreadName: string }> = {};
        if (g) {
            channels = g.Channels as Record<string, { ThreadName: string }>;
        }
        delete channels[channel];
        
        await db_datas.collection("AutoThread").updateOne(
            { Guild: new Long(guildid) },
            {
                $set: {
                    Guild: new Long(guildid),
                    Channels: channels,
                    UpdatedAt: new Date(),
                },
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/settings/${guildid}/auto-thread`);
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

    const channelsData = (() => {
        if (!guild_channels) return null;
        if (Array.isArray((guild_channels as any).data)) return (guild_channels as any).data;
        if (Array.isArray(guild_channels)) return guild_channels as any;
        return null;
    })();

    if (!channelsData) return <p>サーバーのチャンネルを取得できませんでした。</p>;

    const db = await connectDB();
    const find_setting = await db.db("MainTwo").collection("AutoThread").findOne({Guild: new Long(guildid)});

    const entries = find_setting?.Channels ? Object.entries(find_setting.Channels) as [string, { ThreadName: string }][] : [];

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の自動スレッド設定</h1>

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">登録済み設定</h2>
                {entries.length > 0 ? (
                    <ul className="border rounded divide-y divide-gray-700">
                        {entries.map(([channelId, info]: [string, { ThreadName: string }]) => (
                            <li key={channelId} className="p-3 flex justify-between items-center">
                                <span>
                                    <strong>{info.ThreadName}</strong>
                                    <span className="text-gray-400 text-sm ml-2">
                                        <form action={deleteData}>
                                            <button
                                                type="submit"
                                                className="bg-red-600 hover:bg-red-500 text-white font-semibold py-1 px-3 rounded"
                                            >
                                                ❌
                                            </button>
                                            <input name="channel" defaultValue={channelId} hidden></input>
                                            {channelsData.map((ch: any) => ch.id === channelId ? `${ch.name}` : '')}
                                        </form>
                                    </span>
                                </span>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-400">設定がまだありません。</p>
                )}
            </div>

            <form action={sendData} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                <label className="flex flex-col">
                    <span className="font-semibold mb-1">スレッド名</span>
                    <input
                        type="text"
                        name="name"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="スレッド名を入力"
                        required
                    />
                </label>

                <label className="flex flex-col">
                    <span className="font-semibold mb-1">チャンネルを選択</span>
                    <select
                        name="channel"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        required
                    >
                        {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                            <option key={ch.id} value={ch.id}>
                                {ch.name}
                            </option>
                        ))}
                    </select>
                </label>

                <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-500 transition text-white font-semibold py-2 rounded"
                >
                    追加
                </button>
            </form>
        </div>
    );
}