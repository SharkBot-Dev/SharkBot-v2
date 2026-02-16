import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import Builder from "./Builder";

const triggers = new Map<string, string>([
    ["on_message", "メッセージが送信された時"]
]);

const ifs = new Map<string, string>([
    ["if_included", "本文にキーワードを含む"],
    ["if_equal", "本文が完全に一致する"],
    ["is_channel", "特定のチャンネル内"]
]);

const actions = new Map<string, string>([
    ["sendmsg", "メッセージを送信"],
    ["reply", "メッセージに返信"],
    ["delmsg", "メッセージの削除"],
    ["add_reaction", "リアクションを追加"]
]);

export default async function AutoMationPage({ params }: { params: { guildid: string } }) {
    const db_Name = "AutoMationV2";
    const { guildid } = await params;

    async function createAutoMation(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const db = await connectDB();
        const db_datas = db.db("MainTwo");

        const currentCount = await db_datas.collection(db_Name).countDocuments({
            Guild: new Long(guildid)
        });

        if (currentCount >= 25) {
            return;
        }

        const trigger = formData.get("trigger") as string;
        
        const conditions = [];
        let cIndex = 0;
        while (formData.has(`condition_type_${cIndex}`)) {
            if (cIndex >= 5) break;
            const type = formData.get(`condition_type_${cIndex}`) as string;
            const value = formData.get(`condition_value_${cIndex}`) as string;
            if (type && value) conditions.push({ type, value });
            cIndex++;
        }

        const actions = [];
        let aIndex = 0;
        while (formData.has(`action_type_${aIndex}`)) {
            if (aIndex >= 5) break;
            const type = formData.get(`action_type_${aIndex}`) as string;
            const value = formData.get(`action_value_${aIndex}`) as string;
            if (type && value) actions.push({ type, value });
            aIndex++;
        }

        if (conditions.length === 0 || actions.length === 0) return;

        await db_datas.collection(db_Name).insertOne({
            Guild: new Long(guildid),
            Trigger: trigger,
            Conditions: conditions,
            Actions: actions,
            CreatedAt: new Date(),
        });

        revalidatePath(`/dashboard/settings/${guildid}/automation`);
    }

    async function deleteData(formData: FormData) {
        "use server";
        const id = formData.get("id") as string;
        if (!id) return;

        const db = await connectDB();
        const { ObjectId } = require("mongodb");
        await db.db("MainTwo").collection(db_Name).deleteOne({
            _id: new ObjectId(id)
        });

        revalidatePath(`/dashboard/settings/${guildid}/automation`);
    }

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p>セッションが無効です。</p>;

    const guild_channels = await getChannels(guildid);
    const channelsData = Array.isArray(guild_channels) ? guild_channels : (guild_channels as any)?.data || [];

    const db = await connectDB();
    const settings = await db.db("MainTwo").collection(db_Name).find({ Guild: new Long(guildid) }).toArray();

    const currentCount = settings.length;
    const limit = 25;

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の自動化設定</h1>

            <div className="mb-8">
                <h2 className="text-lg font-semibold mb-4">登録済み設定一覧</h2>
                <span className="text-sm font-semibold">
                    使用状況: <span className={currentCount >= limit ? "text-red-500" : "text-green-400"}>
                        {currentCount} / {limit}
                    </span>
                </span>

                {settings.length > 0 ? (
                    <div className="grid gap-4">
                        {settings.map((set) => (
                            <div key={set._id.toString()} className="p-4 bg-gray-800 rounded-lg border border-gray-700 flex justify-between items-start">
                                <div>
                                    <div className="text-blue-400 text-sm font-bold">トリガー: {triggers.get(set.Trigger)}</div>
                                    <div className="mt-2">
                                        <p className="text-xs text-gray-400">条件:</p>
                                        <ul className="list-disc list-inside text-sm">
                                            {set.Conditions.map((c: any, i: number) => (
                                                <li key={i}>{ifs.get(c.type)}: <span className="text-green-400">{c.value}</span></li>
                                            ))}
                                        </ul>
                                    </div>
                                    <div className="mt-2">
                                        <p className="text-xs text-gray-400">実行:</p>
                                        <ul className="list-disc list-inside text-sm">
                                            {set.Actions.map((a: any, i: number) => (
                                                <li key={i}>{actions.get(a.type)}: <span className="text-yellow-400">{a.value}</span></li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                                <form action={deleteData}>
                                    <input name="id" defaultValue={set._id.toString()} hidden />
                                    <button className="bg-red-600 hover:bg-red-500 p-2 rounded text-white transition">削除</button>
                                </form>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-400 text-sm italic">設定されている自動化はありません。</p>
                )}
            </div>

            <hr className="border-gray-700 mb-8" />
            <h2 className="text-lg font-semibold mb-4">＋ 新しい自動化を追加</h2>
            {currentCount < limit ? (
                    <Builder guild={guild} channels={channelsData} sendData={createAutoMation} />
                ): (
                    <p className="text-gray-400">自動化作成の上限（{limit}個）に達しました。</p>
                )
            }
        </div>
    );
}