import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";

export default async function JoinMessagePage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const title = (formData.get("title") as string)?.slice(0, 100);
        const desc = (formData.get("desc") as string)?.slice(0, 500);
        const channel = formData.get("channel") as string;

        if (!title || !desc || !channel) return;

        const db = await connectDB();
        await db.db("Main").collection("WelcomeMessage").updateOne(
            { Guild: new Long(guildid), Channel: new Long(channel) },
            {
                $set: {
                    Guild: new Long(guildid),
                    Title: title,
                    Description: desc,
                    Channel: new Long(channel),
                    UpdatedAt: new Date(),
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

    const guild_channels = await getChannels(guildid);

    const channelsData = (() => {
        if (!guild_channels) return null;
        if (Array.isArray((guild_channels as any).data)) return (guild_channels as any).data;
        if (Array.isArray(guild_channels)) return guild_channels as any;
        return null;
    })();

    if (!channelsData) return <p>サーバーのチャンネルを取得できませんでした。</p>;

    const db = await connectDB();
    const find_setting = await db.db("Main").collection("WelcomeMessage").findOne({Guild: new Long(guildid)});

    let title: string | undefined = undefined;
    let desc: string | undefined = undefined;

    if (find_setting != null) {

        title = find_setting.Title;
        desc = find_setting.Description;

        if (!title) {
            title = '<name> さん、よろしく！'
        }

        if (!desc) {
            desc = 'あなたは <count> 人目のメンバーです！';
        }
    }

    return (
        <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">{guild.name} の挨拶メッセージ設定</h1>

        <form action={sendData} className="flex flex-col gap-2">
            <input
            type="text"
            name="title"
            className="border p-2"
            placeholder="タイトル"
            defaultValue={title}
            required
            />
            <textarea
            name="desc"
            className="border p-2"
            placeholder="説明"
            defaultValue={desc}
            required
            />

            <select name="channel" className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500">
            {channelsData.map((ch: any) => (
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