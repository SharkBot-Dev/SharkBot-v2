import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import Image from "next/image";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";
import Form from "@/app/components/Form";

export default async function DicePage({ params }: { params: { guildid: string } }) {
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

        if (!checkenable) {
            await db.db("MainTwo").collection("Dice").deleteOne({
                Guild: new Long(guildid)
            })
            return;
        }

        await db.db("MainTwo").collection("Dice").updateOne({
            Guild: new Long(guildid)
        }, {
            $set: {
                Guild: new Long(guildid)
            }
        }, {
            upsert: true
        })
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
    const find_setting = await db.db("MainTwo").collection("Dice").findOne({Guild: new Long(guildid)});

    let enabled: boolean | undefined = undefined;

    if (find_setting != null) {
        enabled = true;
    }

    return (
        <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">{guild.name} のダイス</h1>

        <LineAndTextLayout text="主な説明"/>
        <div className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow break-all">
            10d8, ddなどと送信すると、<br/>
            Botがダイスを振ってくれます。
        </div>

        <Form action={sendData} buttonlabel="設定">
            <LineAndTextLayout text="基本設定"></LineAndTextLayout>
            <span className="font-semibold mb-1">機能を有効にする</span>
            <ToggleButton name="checkenable" defaultValue={enabled} /><br />

            <div className="font-semibold mb-1">ダイスに反応する言葉の例: 10d8, dd, ダイス, 🎲, チンチロ</div><br />
        </Form>
        </div>
    );
}