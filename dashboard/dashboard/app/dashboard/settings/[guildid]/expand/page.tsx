import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";

export default async function JoinMessagePage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const checkenable = formData.get("checkenable") === "true" || formData.get("checkenable") === "on";
        const gaibuenbale = formData.get("gaibuenbale") === "true" || formData.get("gaibuenbale") === "on";

        const db = await connectDB();

        if (!checkenable) {
            await db.db("Main").collection("ExpandSettings").updateOne({
                Guild: new Long(guildid)
            }, {
                $set: {
                    "Enabled": false,
                    "Outside": gaibuenbale
                }
            }, {
                upsert: true
            })
            return;
        }

        await db.db("Main").collection("ExpandSettings").updateOne({
            Guild: new Long(guildid)
        }, {
            $set: {
                "Enabled": true,
                "Outside": gaibuenbale
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
    const find_setting = await db.db("Main").collection("ExpandSettings").findOne({Guild: new Long(guildid)});

    let enabled: boolean | undefined = undefined;
    let gaibu_enabled: boolean | undefined = undefined;
    
    if (find_setting != null) {
        enabled = find_setting.Enabled ? find_setting.Enabled : false;
        gaibu_enabled = find_setting.Outside ? find_setting.Outside : false;
    }

    return (
        <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">{guild.name} のメッセージ展開</h1>

        <form action={sendData} className="flex flex-col gap-2">
            <span className="font-semibold mb-1">機能を有効にする</span>
            <ToggleButton name="checkenable" defaultValue={enabled} />

            <span className="font-semibold mb-1">外部への展開を許可するか</span>
            <ToggleButton name="gaibuenbale" defaultValue={gaibu_enabled} />

            <button type="submit" className="bg-blue-500 text-white p-2 rounded">
            設定
            </button>
        </form>
        </div>
    );
}