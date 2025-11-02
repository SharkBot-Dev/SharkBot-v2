import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long, ObjectId } from "mongodb";

export default async function EconomyPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;
        const name = (formData.get("c_name") as string)?.slice(0, 20);

        const db = await connectDB();

        await db.db("Main").collection("ServerMoneyCurrency").updateOne(
            { _id: guildid as any },
            {
                $set: {
                    _id: guildid,
                    UpdatedAt: new Date(),
                    Name: name
                },
            },
            { upsert: true }
        );
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
    const c_name_findone = await db.db("Main").collection("ServerMoneyCurrency").findOne({ Guild: Long.fromString(guildid) });

    let c_name: string | undefined = undefined;

    if (c_name_findone != null) {
        c_name = c_name_findone.Title;
    } else {
        c_name = "🪙"
    }

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の経済機能</h1>

            <form action={sendData} className="flex flex-col gap-3">
                <label className="flex flex-col">
                    <span className="font-semibold mb-1">通貨名</span>
                    <input
                        type="text"
                        name="c_name"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="通貨名を入力"
                        defaultValue={c_name}
                        required
                    />
                </label>


                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>
        </div>
    );
}