import { getGuild, getGuildRequest } from "@/lib/discord/fetch";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";

export default async function Home({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const db = await connectDB();

        const prefix = formData.get("prefix");

        await db.db("DashboardBot").collection("CustomPrefixBot").updateOne(
            { Guild: new Long(guildid) },
            { $set: { Prefix: prefix } },
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

    const fetch_guild = await getGuildRequest(guildid);
    if (!fetch_guild) {
      redirect(
        "https://discord.com/oauth2/authorize?client_id=1322100616369147924&permissions=8&integration_type=0&scope=bot+applications.commands"
      );
    }

    const db = await connectDB();
    const prefix_findone = await db.db("DashboardBot").collection("CustomPrefixBot").findOne({ Guild: new Long(guildid) });

    let prefix: string | undefined = undefined;

    if (prefix_findone != null) {
      prefix = prefix_findone.Prefix;
    } else {
      prefix = "!."
    } 

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の基本設定</h1>

            <form action={sendData} className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                <label className="flex flex-col">
                    <span className="font-semibold mb-1">頭文字 (Prefix) を設定</span>
                    <input
                        type="text"
                        name="prefix"
                        className="border border-gray-700 bg-gray-800 text-white p-2 rounded"
                        placeholder="頭文字を設定"
                        defaultValue={prefix}
                        required
                    />
                </label>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form><br/>
        </div>
    );
}