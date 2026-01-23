import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import Form from "@/app/components/Form";

export default async function ReportPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const check_enable = formData.get("checkenable") === "true" || formData.get("checkenable") === "on";

        const db = await connectDB();

        if (!check_enable) {
            await db.db("Main").collection("ReportChannel").deleteOne({ Guild: Long.fromString(guildid) });
            return;
        }

        const channel = formData.get("channel") as string;

        const guild_channels = await getChannels(guildid);
        const channelsData =
            Array.isArray((guild_channels as any).data)
                ? (guild_channels as any).data
                : guild_channels;

        const exists = channelsData.some((c: any) => c.id === channel);

        if (!exists) {
            console.error("チャンネルが存在しません");
            return;
        }

        await db.db("Main").collection("ReportChannel").updateOne(
            { Guild: new Long(guildid) },
            {
                $set: {
                    Guild: new Long(guildid),
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
    const find_setting = await db.db("Main").collection("ReportChannel").findOne({Guild: new Long(guildid)});

    const enabled = !!find_setting;

    return (
        <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">{guild.name} の通報機能</h1>

        <Form action={sendData} buttonlabel="設定">
            <span className="font-semibold mb-1">機能を有効にする</span>
            <ToggleButton name="checkenable" defaultValue={enabled} />

            <span className="font-semibold mb-1">通報の受付先チャンネル</span>
            <select
                name="channel"
                className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500"
            >
                {channelsData
                    ?.filter((ch: any) => ch.type === 0)
                    .map((ch: any) => (
                        <option
                            key={ch.id}
                            value={ch.id}
                            selected={enabled && String(find_setting?.Channel) === String(ch.id)}
                        >
                            {ch.name}
                        </option>
                    ))}
            </select>
        </Form>
        </div>
    );
}