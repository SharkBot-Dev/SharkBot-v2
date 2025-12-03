import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long, ObjectId } from "mongodb";
import { revalidatePath } from "next/cache";

export default async function AutoReactPage({ params }: { params: { guildid: string } }) {
    async function addAutoReactionforWord(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const word = formData.get("word")?.toString();
        if (!word) return;
        const emoji = formData.get("emoji")?.toString();
        if (!emoji) return;

        const db = await connectDB();

        await db.db("Main").collection("AutoReactionWord").updateOne(
            { Guild: new Long(guildid), Word: word },
            {
                $set: {
                    Guild: new Long(guildid),
                    Word: word,
                    Emoji: emoji
                },
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/settings/${guildid}/autoreact`);
    }

    async function deleteAutoReactionforWord(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const n = formData.get('name');

        if (!n) return;

        const db = await connectDB();

        await db.db("Main").collection("AutoReactionWord").deleteOne({
            Guild: new Long(guildid), Word: n
        })

        revalidatePath(`/dashboard/settings/${guildid}/autoreact`);
    }

    async function addAutoReactionforChannel(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const channel = formData.get("channel")?.toString();
        if (!channel) return;
        const emoji = formData.get("emoji")?.toString();
        if (!emoji) return;

        const db = await connectDB();

        await db.db("Main").collection("AutoReactionChannel").updateOne(
            { Guild: new Long(guildid), Channel: new Long(channel as string) },
            {
                $set: {
                    Guild: new Long(guildid),
                    Channel: new Long(channel as string),
                    Emoji: emoji
                },
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/settings/${guildid}/autoreact`);
    }

    async function deleteAutoReactionforChannel(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const n = formData.get('name');

        if (!n) return;

        const db = await connectDB();

        await db.db("Main").collection("AutoReactionChannel").deleteOne({
            Guild: new Long(guildid), Channel: new Long(n as string)
        })

        revalidatePath(`/dashboard/settings/${guildid}/autoreact`);
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

    const a_r = await db.db("Main").collection("AutoReactionWord").find({Guild: new Long(guildid)}).toArray();
    const a_r_channel = await db.db("Main").collection("AutoReactionChannel").find({Guild: new Long(guildid)}).toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の自動リアクション</h1>

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">特定ワードに対してリアクションする設定一覧</h2>
                {a_r.length > 0 ? (
                <ul className="border rounded divide-y divide-gray-700">
                    {a_r.map((item) => (
                    <li key={item.Word} className="p-3 flex justify-between items-center">
                        <span>
                        <strong>
                            {item.Word} — {item.Emoji}
                        </strong>
                        </span>
                        <form action={deleteAutoReactionforWord}>
                        <input type="hidden" name="name" value={item.Word} />
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

            <form action={addAutoReactionforWord} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                <label className="flex flex-col">
                    <span className="font-semibold mb-1">反応する条件</span>
                    <input
                        type="text"
                        name="word"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="条件を入力"
                        required
                    />
                </label>

                <label className="flex flex-col">
                    <span className="font-semibold mb-1">反応した際にリアクションする絵文字</span>
                    <input
                        type="text"
                        name="emoji"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="絵文字を入力"
                        required
                    />
                </label>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    追加する
                </button>
            </form>

            <br/>
            <hr/>
            <br/>

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">指定チャンネルに対してリアクションする設定一覧</h2>
                {a_r_channel.length > 0 ? (
                <ul className="border rounded divide-y divide-gray-700">
                    {a_r_channel.map((item) => {
                    const ch = channelsData.find((ch: any) => ch.id === item.Channel.toString());
                    return (
                        <li key={item.Channel.toString()} className="p-3 flex justify-between items-center">
                        <span><strong>{ch ? ch.name : "不明なチャンネル"} — {item.Emoji}</strong></span>
                        <form action={deleteAutoReactionforChannel}>
                            <input type="hidden" name="name" value={item.Channel.toString()} />
                            <button type="submit" className="bg-red-600 hover:bg-red-500 text-white font-semibold py-1 px-3 rounded">❌</button>
                        </form>
                        </li>
                    );
                    })}
                </ul>
                ) : <p className="text-gray-400">設定がまだありません。</p>}
            </div>

            <form action={addAutoReactionforChannel} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                <label className="flex flex-col">
                    <span className="font-semibold mb-1">反応するチャンネル</span>
                    <select name="channel" className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500">
                    {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                        <option key={ch.id} value={ch.id}>
                        {ch.name}
                        </option>
                    ))}
                    </select>
                </label>

                <label className="flex flex-col">
                    <span className="font-semibold mb-1">反応した際にリアクションする絵文字</span>
                    <input
                        type="text"
                        name="emoji"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="絵文字を入力"
                        required
                    />
                </label>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    追加する
                </button>
            </form>
        </div>
    );
}