import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long, ObjectId } from "mongodb";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";

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

    async function sendShopData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const item = formData.get('name');
        const money = formData.get('money');

        if (!item || !money) return;

        const db = await connectDB();

        await db.db("Main").collection("ServerMoneyItems").updateOne({
            Guild: new Long(guildid),
            ItemName: item
        }, {$set: {
            Guild: new Long(guildid),
            ItemName: item,
            Role: 0,
            DM: "なし",
            Money: new Long(Number(money))
        }}, {
            upsert: true
        })
    }

    async function deleteData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const db = await connectDB();

        const find_item = db.db("Main").collection("ServerMoneyItems");

        const item = formData.get('name');

        if (!item) return;

        find_item.deleteOne({Guild: new Long(guildid), ItemName: item})
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
    const c_name_findone = await db.db("Main").collection("ServerMoneyCurrency").findOne({ _id: guildid as any });

    let c_name: string | undefined = undefined;

    if (c_name_findone != null) {
        c_name = c_name_findone.Name;
    } else {
        c_name = "コイン"
    } 

    const finded_items = await db.db("Main").collection("ServerMoneyItems").find({Guild: new Long(guildid)}).toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の経済機能</h1>

            <LineAndTextLayout text="通貨名・アイテム設定" />

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">アイテム一覧</h2>
                {finded_items.length > 0 ? (
                <ul className="border rounded divide-y divide-gray-700">
                    {finded_items.map((item) => (
                    <li key={item.ItemName} className="p-3 flex justify-between items-center">
                        <span>
                        <strong>
                            {item.ItemName} — {new String(item.Money)}
                            {c_name}
                        </strong>
                        </span>
                        <form action={deleteData}>
                        <input type="hidden" name="name" value={item.ItemName} />
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

            <form action={sendData} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
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
            </form><br/>

            <form action={sendShopData} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                <label className="flex flex-col">
                    <span className="font-semibold mb-1">アイテム名</span>
                    <input
                        type="text"
                        name="name"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="アイテム名を入力"
                        required
                    />
                </label>

                <label className="flex flex-col">
                    <span className="font-semibold mb-1">値段</span>
                    <input
                        type="number"
                        name="money"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="値段を入力"
                        required
                    />
                </label>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    作成
                </button>
            </form>

            <LineAndTextLayout text="コマンド設定" />
            <span className="font-semibold mb-1">以下のボタンのページから設定できます。</span><br /><br />
            <a
                href={`/dashboard/settings/${guildid}/commands`}
                className="bg-blue-600 text-white px-4 py-2 rounded-md"
            >
                コマンドの設定に移動する
            </a>
        </div>
    );
}