import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import ItemRow from "@/app/components/ItemRow";
import ItemBox from "@/app/components/ItemBox";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";
import Form from "@/app/components/Form";
import ModuleToggle from "@/app/components/ModuleToggle";

export default async function SearchPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const translate = formData.get("translate") === "true" || formData.get("translate") === "on";

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

        await updateToggle(translate, "search web translate");
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
            <h1 className="text-2xl font-bold mb-4">{guild.name} の翻訳</h1>
            <ModuleToggle guild_id={guildid} module_name="translate"/>

            <Form action={sendData} buttonlabel="設定を保存">
                <LineAndTextLayout text="コマンド設定" />
                <ItemRow>
                    <ItemBox title="翻訳コマンドを使用可能か (/search web translate)">
                        <ToggleButton name="translate" defaultValue={!disabled_commands.includes('search web translate')} />
                    </ItemBox>
                </ItemRow>
            </Form>
        </div>
    );
}