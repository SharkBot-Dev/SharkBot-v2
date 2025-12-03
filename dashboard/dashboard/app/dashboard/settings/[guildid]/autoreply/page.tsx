import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long, ObjectId } from "mongodb";
import { revalidatePath } from "next/cache";

export default async function AutoReplyPage({ params }: { params: { guildid: string } }) {
    async function addAutoreply(formData: FormData) {
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
        const reply = formData.get("reply")?.toString();
        if (!reply) return;

        const db = await connectDB();

        await db.db("Main").collection("AutoReply").updateOne(
            { Guild: new Long(guildid), Word: word },
            {
                $set: {
                    Guild: new Long(guildid),
                    Word: word,
                    ReplyWord: reply,
                    TextChannel: 0,
                    Roles: []
                },
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/settings/${guildid}/autoreply`);
    }

    async function DeleteAutoreply(formData: FormData) {
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

        await db.db("Main").collection("AutoReply").deleteOne({
            Guild: new Long(guildid), Word: n
        })

        revalidatePath(`/dashboard/settings/${guildid}/autoreply`);
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

    const autoreplys = await db.db("Main").collection("AutoReply").find({Guild: new Long(guildid)}).toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の自動返信</h1>

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">自動返信一覧</h2>
                {autoreplys.length > 0 ? (
                <ul className="border rounded divide-y divide-gray-700">
                    {autoreplys.map((item) => (
                    <li key={item.Word} className="p-3 flex justify-between items-center">
                        <span>
                        <strong>
                            {item.Word} — {item.ReplyWord}
                        </strong>
                        </span>
                        <form action={DeleteAutoreply}>
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

            <form action={addAutoreply} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
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
                    <span className="font-semibold mb-1">反応した際に返信する発言</span>
                    <input
                        type="text"
                        name="reply"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="発言を入力"
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