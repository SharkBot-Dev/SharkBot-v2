import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import ItemBox from "@/app/components/ItemBox";
import ItemRow from "@/app/components/ItemRow";

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

            <form action={sendData} className="flex flex-col gap-6">

                <ItemRow>

                    <ItemBox title="音楽を再生可能か (/music play)">
                        <ToggleButton name="play" defaultValue={!disabled_commands.includes('music play')} />
                    </ItemBox>

                    <ItemBox title="音楽を停止可能か (/music stop)">
                        <ToggleButton name="stop" defaultValue={!disabled_commands.includes('music stop')} />
                    </ItemBox>

                    <ItemBox title="音楽をスキップ可能か (/music skip)">
                        <ToggleButton name="skip" defaultValue={!disabled_commands.includes('music skip')} />
                    </ItemBox>

                    <ItemBox title="音楽のキューを確認可能か (/music queue)">
                        <ToggleButton name="queue" defaultValue={!disabled_commands.includes('music queue')} />
                    </ItemBox>

                    <ItemBox title="音量の調節が可能か (/music volume)">
                        <ToggleButton name="volume" defaultValue={!disabled_commands.includes('music volume')} />
                    </ItemBox>

                    <ItemBox title="低音ブーストが可能か (/music boost)">
                        <ToggleButton name="boost" defaultValue={!disabled_commands.includes('music boost')} />
                    </ItemBox>

                </ItemRow>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>
        </div>
    );

}