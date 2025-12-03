import { cookies } from "next/headers";
import { getGuild, getChannels, sendMessage } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";

const cooldowns = new Map<string, number>();

export default async function LockMessagePage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const now = Date.now();
        const lastTime = cooldowns.get(sessionId) ?? 0;
        const cooldownMs = 10 * 1000;

        if (now - lastTime < cooldownMs) {
            return;
        }

        cooldowns.set(sessionId, now);

        const db = await connectDB();

        const title = (formData.get("title") as string)?.slice(0, 100);
        const desc = (formData.get("desc") as string)?.slice(0, 500);
        const channel = formData.get("channel") as string;

        if (!title || !desc || !channel) return;

        const embed: any = {
            title,
            description: desc,
            color: 0x57f287,
        };

        const components = [
            {
                type: 1,
                components: [
                    {
                        type: 2,
                        style: 4,
                        label: "削除",
                        custom_id: `lockmessage_delete+`,
                    },
                    {
                        type: 2,
                        style: 1,
                        label: "削除",
                        custom_id: `lockmessage_edit+`,
                    },
                ]
            }
        ]

        try {
            const msg = await sendMessage(channel, {
                embeds: [embed],
                components,
            });

            await db.db("Main").collection("LockMessage").updateOne(
                { Guild: new Long(guildid), Channel: new Long(channel) },
                {
                    $set: {
                        Guild: new Long(guildid),
                        Title: title,
                        Desc: desc,
                        Channel: new Long(channel),
                        UpdatedAt: new Date(),
                        MessageID: new Long(msg?.data?.id as string)
                    },
                },
                { upsert: true }
            );
        } catch {
            return;
        }
    }

    async function DeleteMessage(formData: FormData) {
        "use server";

        const { guildid } = await params;

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const name = formData.get("name");
        if (!name) return;

        const db = await connectDB();

        const col = db.db('Main').collection('LockMessage');

        await col.deleteOne(
            {
                Guild: new Long(guildid),
                Title: name
            }
        )
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
    const find_setting = await db.db("Main").collection("LockMessage").find({Guild: new Long(guildid)}).toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の固定メッセージ</h1>

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">
                    固定メッセージ一覧
                </h2>
                {find_setting.length > 0 ? (
                    <ul className="border rounded divide-y divide-gray-700">
                        {find_setting.map((item) => (
                            <li
                                key={item.Title}
                                className="p-3 flex justify-between items-center"
                            >
                                <span>
                                    <strong>
                                        {item.Title}
                                    </strong>
                                </span>
                                <form action={DeleteMessage}>
                                    <input
                                        type="hidden"
                                        name="name"
                                        value={item.Title}
                                    />
                                    <button
                                        type="submit"
                                        className="bg-red-600 hover:bg-red-500 text-white font-semibold py-1 px-3 rounded"
                                    >
                                        ❌
                                    </button>
                                </form>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-400">設定がまだありません。</p>
                )}
            </div>

            <form action={sendData} className="flex flex-col gap-2">
                <span className="font-semibold mb-1">タイトル</span>
                <input
                type="text"
                name="title"
                className="border p-2"
                placeholder="タイトル"
                />
                <span className="font-semibold mb-1">説明</span>
                <textarea
                name="desc"
                className="border p-2"
                placeholder="説明"
                />

                <span className="font-semibold mb-1">送信先チャンネル</span>
                <select name="channel" className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500">
                {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                    <option key={ch.id} value={ch.id}>
                    {ch.name}
                    </option>
                ))}
                </select>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded">
                設定
                </button>
            </form>
        </div>
    );
}