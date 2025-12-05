import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import ItemRow from "@/app/components/ItemRow";
import ItemBox from "@/app/components/ItemBox";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";

export default async function PollPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const checkenable = formData.get("checkenable") === "true" || formData.get("checkenable") === "on";

        const db = await connectDB();

        if (checkenable) {
            await db.db("DashboardBot").collection("CommandDisabled").updateOne(
                { Guild: new Long(guildid) },
                { $pull: { commands: "panel poll" as any } },
                { upsert: true }
            );
            return;
        }

        await db.db("DashboardBot").collection("CommandDisabled").updateOne(
            { Guild: new Long(guildid) },
            { $addToSet: { commands: "panel poll" } },
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

    const db = await connectDB();
    const disabledDoc = await db.db("DashboardBot").collection("CommandDisabled").findOne({ Guild: new Long(guildid) });
    const disabled_commands: string[] = disabledDoc?.commands || [];

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の投票設定</h1>

            <LineAndTextLayout text="コマンド設定" />

            <form action={sendData} className="flex flex-col gap-3">
                <ItemRow>
                    <ItemBox title="投票コマンドを有効化する (/panel poll)">
                        <ToggleButton name="checkenable" defaultValue={!disabled_commands.includes('panel poll')} />
                    </ItemBox>
                </ItemRow>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>
        </div>
    );
}