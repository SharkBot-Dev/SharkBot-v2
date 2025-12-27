import { cookies } from "next/headers";
import { getGuild } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import Form from "@/app/components/Form";
import { revalidatePath } from "next/cache";

export default async function TagsPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const cmd_name = formData.get("cmd_name");
        const text = formData.get("text");
        const tagscript = formData.get("tagscript");
        if (!cmd_name || !text || !tagscript) return;

        const db = await connectDB();

        await db.db("Main").collection("Tags").updateOne(
            { command: cmd_name, guild_id: guildid },
            {
                $set: {
                    command: cmd_name,
                    guild_id: new Long(guildid),
                    text,
                    tagscript,
                },
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/settings/${guildid}/tags`);
    }

    async function deleteTags(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const cmd_name = formData.get("cmd_name")?.toString();
        if (!cmd_name) return;

        const db = await connectDB();

        await db.db("Main").collection("Tags").deleteOne({
            command: cmd_name,
            guild_id: new Long(guildid),
        });

        revalidatePath(`/dashboard/settings/${guildid}/tags`);
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
    const counts = await db.db("Main").collection("Tags").find({guild_id: new Long(guildid)}).toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のカスタムコマンド（タグ）設定</h1>

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">登録済みカスタムコマンド</h2>
                {counts.length > 0 ? (
                    <ul className="border rounded divide-y divide-gray-700">
                        {counts.map((item) => {
                            return (
                                <li key={item.command} className="p-3 flex justify-between items-center">
                                    <span>
                                        {item.command} - {item.text}
                                    </span>

                                    <form action={deleteTags}>
                                        <input
                                            type="hidden"
                                            name="cmd_name"
                                            value={item.command}
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
                <span className="font-semibold mb-1">コマンド名</span>
                <input
                    type="text"
                    name="cmd_name"
                    className="border p-2"
                    placeholder="tableflip"
                />

                <span className="font-semibold mb-1">コマンドの説明</span>
                <input
                    type="text"
                    name="text"
                    className="border p-2"
                    placeholder="テーブルフリップをします。"
                />

                <span className="font-semibold mb-1">返信する内容</span>
                <input
                    type="text"
                    name="tagscript"
                    className="border p-2"
                    placeholder="(╯°□°)╯︵ ┻━┻"
                />
            </Form>
        </div>
    );
}