import { cookies } from "next/headers";
import { getGuild, getChannels, getRoles } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long, ObjectId } from "mongodb";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";
import ToggleButton from "@/app/components/ToggleButton";

const events = {
    "say": "回話すと",
    "react": "回リアクションすると"
}

export default async function AchievementPage({ params }: { params: { guildid: string } }) {
    async function setEnabled(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const enable = formData.get("checkenable") === "on";

        const db = await connectDB();

        await db.db("Main").collection("AchievementsSettings").updateOne(
            { Guild: new Long(guildid) },
            { $set: { Guild: new Long(guildid), Enabled: enable } },
            { upsert: true }
        );
    }

    async function addData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const item = formData.get('name');
        const count = formData.get('count');
        const role = formData.get('role');
        const event = formData.get('events')

        if (!item || !count || !event) return;

        const db = await connectDB();

        await db.db("Main").collection("Achievements").updateOne({
            Guild: new Long(guildid),
            Name: item
        }, {$set: {
            Guild: new Long(guildid),
            Name: item,
            Role: role? new Long(role as string) : 0,
            If: event,
            Value: Number(count)
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

        const item = formData.get('name');
        if (!item) return;

        await db.db("Main").collection("Achievements").deleteOne({
            Guild: new Long(guildid),
            Name: item
        });
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
    const is_enabled = await db.db("Main").collection("AchievementsSettings").findOne({Guild: new Long(guildid)});

    const enabled = !!is_enabled;

    const achievements = await db.db("Main").collection("Achievements").find({Guild: new Long(guildid)}).toArray();

    const guild_roles = await getRoles(guildid);
    const RolesData = Array.isArray((guild_roles as any).data)
        ? (guild_roles as any).data
        : guild_roles;

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の実績機能</h1>

            <LineAndTextLayout text="機能の有効化・無効化" />

            <form action={setEnabled} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                <span className="font-semibold mb-1">機能を有効にする</span>
                <ToggleButton name="checkenable" defaultValue={enabled} />

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>

            <LineAndTextLayout text="実績の追加・削除" />

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">実績一覧</h2>
                {achievements.length > 0 ? (
                <ul className="border rounded divide-y divide-gray-700">
                    {achievements.map((item) => (
                    <li key={item.Name} className="p-3 flex justify-between items-center">
                        <span>
                        <strong>
                            {item.Name} ー {String(item.Value)} {(events as Record<string, string>)[item.If as string] ?? ""}
                        </strong>
                        </span>
                        <form action={deleteData}>
                        <input type="hidden" name="name" value={item.Name} />
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

            <form action={addData} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                <label className="flex flex-col">
                    <span className="font-semibold mb-1">実績名</span>
                    <input
                        type="name"
                        name="name"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="実績名を入力"
                        required
                    />
                </label>

                <label className="flex flex-col">
                    <span className="font-semibold mb-1">達成するために必要な行動</span>
                    <select
                        name="events"
                        className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option key="say" value="say">
                            話す
                        </option>
                        <option key="react" value="react">
                            リアクションする
                        </option>
                    </select>
                </label>

                <label className="flex flex-col">
                    <span className="font-semibold mb-1">達成するために必要な行動の回数</span>
                    <input
                        type="number"
                        name="count"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="回数を入力"
                        required
                    />
                </label>

                <label className="flex flex-col">
                    <span className="font-semibold mb-1">達成時に付与するロール</span>
                    <select
                        name="role"
                        className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {RolesData?.map((ch: any) => (
                            <option key={ch.id} value={ch.id}>
                                {ch.name}
                            </option>
                        ))}
                    </select>
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