import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";

export default async function MusicPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const play = formData.get("play") === "true" || formData.get("play") === "on";
        const stop = formData.get("stop") === "true" || formData.get("stop") === "on";
        const skip = formData.get("skip") === "true" || formData.get("skip") === "on";
        const queue = formData.get("queue") === "true" || formData.get("queue") === "on";
        const volume = formData.get("volume") === "true" || formData.get("volume") === "on";
        const boost = formData.get("boost") === "true" || formData.get("boost") === "on";

        const db = await connectDB();
        const col = db.db("DashboardBot").collection("CommandDisabled");
        const guildFilter = { Guild: new Long(guildid) };

        async function updateToggle(flag: boolean, command: string) {
            if (flag) {
                await col.updateOne(guildFilter, { $pull: { commands: command } as any }, { upsert: true });
            } else {
                await col.updateOne(guildFilter, { $addToSet: { commands: command } }, { upsert: true });
            }
        }

        await updateToggle(play, "music play");
        await updateToggle(stop, "music stop");
        await updateToggle(skip, "music skip");
        await updateToggle(queue, "music queue");
        await updateToggle(volume, "music volume");
        await updateToggle(boost, "music boost");
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
    const disabledDoc = await db.db("DashboardBot").collection("CommandDisabled").findOne({ Guild: new Long(guildid) });
    const disabled_commands: string[] = disabledDoc?.commands || [];

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の音楽設定</h1>

            <form action={sendData} className="flex flex-col gap-3">
                <span className="font-semibold mb-1">音楽を再生可能か (/music play)</span>
                <ToggleButton name="play" defaultValue={!disabled_commands.includes('music play')} />

                <span className="font-semibold mb-1">音楽を停止可能か (/music stop)</span>
                <ToggleButton name="stop" defaultValue={!disabled_commands.includes('music stop')} />

                <span className="font-semibold mb-1">音楽をスキップ可能か (/music skip)</span>
                <ToggleButton name="skip" defaultValue={!disabled_commands.includes('music skip')} />

                <span className="font-semibold mb-1">音楽のキューを確認可能か (/music queue)</span>
                <ToggleButton name="queue" defaultValue={!disabled_commands.includes('music queue')} />

                <span className="font-semibold mb-1">音楽の音量を調節可能か (/music volume)</span>
                <ToggleButton name="volume" defaultValue={!disabled_commands.includes('music volume')} />

                <span className="font-semibold mb-1">音楽の低音ブースト可能か (/music boost)</span>
                <ToggleButton name="boost" defaultValue={!disabled_commands.includes('music boost')} />

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>
        </div>
    );
}