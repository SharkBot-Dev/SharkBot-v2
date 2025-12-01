import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";

export default async function ModerationPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const kick = formData.get("kick") === "true" || formData.get("kick") === "on";
        const timeout = formData.get("timeout") === "true" || formData.get("timeout") === "on";
        const untimeout = formData.get("untimeout") === "true" || formData.get("untimeout") === "on";
        const ban = formData.get("ban") === "true" || formData.get("ban") === "on";
        const massban = formData.get("massban") === "true" || formData.get("massban") === "on";
        const unban = formData.get("unban") === "true" || formData.get("unban") === "on";

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

        await updateToggle(kick, "moderation kick");
        await updateToggle(timeout, "moderation timeout");
        await updateToggle(untimeout, "moderation untimeout");
        await updateToggle(ban, "moderation ban ban");
        await updateToggle(massban, "moderation ban massban");
        await updateToggle(unban, "moderation ban unban");
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
            <h1 className="text-2xl font-bold mb-4">{guild.name} のモデレーション設定</h1>

            <form action={sendData} className="flex flex-col gap-3">
                <LineAndTextLayout text="キック"></LineAndTextLayout>
                <span className="font-semibold mb-1">Kickコマンドを使えるか (/moderation kick)</span>
                <ToggleButton name="kick" defaultValue={!disabled_commands.includes('moderation kick')} />

                <LineAndTextLayout text="タイムアウト"></LineAndTextLayout>
                <span className="font-semibold mb-1">タイムアウトコマンドが使えるか (/moderation timeout)</span>
                <ToggleButton name="timeout" defaultValue={!disabled_commands.includes('moderation timeout')} />
                <span className="font-semibold mb-1">タイムアウト解除コマンドが使えるか (/moderation untimeout)</span>
                <ToggleButton name="untimeout" defaultValue={!disabled_commands.includes('moderation untimeout')} />

                <LineAndTextLayout text="ユーザーBan"></LineAndTextLayout>
                <span className="font-semibold mb-1">ユーザーBanコマンドが使えるか (/moderation ban ban)</span>
                <ToggleButton name="ban" defaultValue={!disabled_commands.includes('moderation ban ban')} />
                <span className="font-semibold mb-1">ユーザー複数Banコマンドが使えるか (/moderation ban massban)</span>
                <ToggleButton name="massban" defaultValue={!disabled_commands.includes('moderation ban massban')} />
                <span className="font-semibold mb-1">ユーザーBan解除コマンドが使えるか (/moderation ban unban)</span>
                <ToggleButton name="unban" defaultValue={!disabled_commands.includes('moderation ban unban')} />

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    設定を保存
                </button>
            </form>
        </div>
    );
}