import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import Form from "@/app/components/Form";

export default async function AuthPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const auth = formData.get("auth") === "true" || formData.get("auth") === "on";
        const absauth = formData.get("absauth") === "true" || formData.get("absauth") === "on";
        const webauth = formData.get("webauth") === "true" || formData.get("webauth") === "on";

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

        await updateToggle(auth, "panel auth auth");
        await updateToggle(absauth, "panel auth abs-auth");
        await updateToggle(webauth, "panel auth webauth");
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
            <h1 className="text-2xl font-bold mb-4">{guild.name} の認証設定</h1>

            <Form action={sendData} buttonlabel="設定を保存">
                <span className="font-semibold mb-1">ワンクリック認証 (/panel auth auth)</span>
                <ToggleButton name="auth" defaultValue={!disabled_commands.includes('panel auth auth')} />

                <span className="font-semibold mb-1">計算認証 (/panel auth abs-auth)</span>
                <ToggleButton name="absauth" defaultValue={!disabled_commands.includes('panel auth abs-auth')} />

                <span className="font-semibold mb-1">Web認証 (/panel auth webauth)</span>
                <ToggleButton name="webauth" defaultValue={!disabled_commands.includes('panel auth webauth')} />
            </Form>
        </div>
    );
}