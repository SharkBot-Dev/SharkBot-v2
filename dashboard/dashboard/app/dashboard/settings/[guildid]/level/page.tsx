import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";

export default async function LevelPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const checkenable = formData.get("checkenable") === "true" || formData.get("checkenable") === "on";
        const channel = formData.get("levelupchannel") as string;
        const levelupmessage = formData.get("levelupmessage") as string;

        const db = await connectDB();

        if (checkenable) {
            await db.db("Main").collection("LevelingSetting").updateOne(
                { Guild: Long.fromString(guildid) },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        UpdatedAt: new Date(),
                        Message: levelupmessage
                    },
                },
                { upsert: true }
            );

            await db.db("Main").collection("LevelingUpAlertChannel").updateOne(
                { Guild: Long.fromString(guildid) },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        Channel: Long.fromString(channel)
                    },
                },
                { upsert: true }
            );
        } else {
            // 無効化する場合は設定を削除
            await db.db("Main").collection("LevelingSetting").deleteOne({ Guild: Long.fromString(guildid) });
            await db.db("Main").collection("LevelingUpAlertChannel").deleteOne({ Guild: Long.fromString(guildid) });
        }
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
    const leveling_setting_findone = await db.db("Main").collection("LevelingSetting").findOne({ Guild: Long.fromString(guildid) });
    const leveling_channel_findone = await db.db("Main").collection("LevelingUpAlertChannel").findOne({ Guild: Long.fromString(guildid) });

    const enabled = !!leveling_setting_findone;
    const desc = leveling_setting_findone?.Message ?? "`{user}`さんの\nレベルが「{newlevel}」になったよ！";
    const selectedChannel = leveling_channel_findone?.Channel ? String(leveling_channel_findone.Channel) : "";

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のレベルアップメッセージ設定</h1>

            <form action={sendData} className="flex flex-col gap-3">
                <span className="font-semibold mb-1">機能を有効にする</span>
                <ToggleButton name="checkenable" defaultValue={enabled} />

                <span className="font-semibold mb-1">レベルアップメッセージ</span>
                <textarea
                    name="levelupmessage"
                    className="border p-2 rounded bg-gray-800 text-white"
                    placeholder="レベルアップメッセージ"
                    defaultValue={desc}
                    required
                />

                <span className="font-semibold mb-1">レベルアップ通知チャンネル</span>
                <select
                    name="levelupchannel"
                    defaultValue={selectedChannel}
                    className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {channelsData.map((ch: any) => (
                        <option key={ch.id} value={ch.id}>
                            {ch.name}
                        </option>
                    ))}
                </select>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>
        </div>
    );
}