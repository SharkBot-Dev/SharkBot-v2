import { cookies } from "next/headers";
import { getGuild, getRoles } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import CommandList from "./CommandList";

export default async function CommandPage({ params }: { params: { guildid: string } }) {
    const { guildid } = await params;

    async function sendData(formData: FormData) {
        "use server";

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId || !guildid) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const disabledCommandsRaw = formData.get("disabledCommands") as string;
        const roleRestrictionsRaw = formData.get("roleRestrictions") as string;

        const disabledCommands: string[] = JSON.parse(disabledCommandsRaw || "[]");
        const roleRestrictions: Record<string, string> = JSON.parse(roleRestrictionsRaw || "{}");

        const db = await connectDB();
        const col = db.db("DashboardBot").collection("CommandDisabled");

        await col.updateOne(
            { Guild: new Long(guildid) },
            { 
                $set: { 
                    commands: disabledCommands,
                    roleRestrictions: roleRestrictions,
                    updatedAt: new Date()
                } 
            },
            { upsert: true }
        );
    }

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return <p className="text-white">ログイン情報が見つかりません。</p>;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p className="text-white">セッションが無効、またはサーバーが見つかりません。</p>;

    const db = await connectDB();
    
    const allCommandsDoc = await db.db("DashboardBot").collection("Commands").find().toArray();
    const commands = allCommandsDoc.map((doc: any) => {
        const parts = doc.name?.split(" ") || [];
        const category = parts.length > 1 ? parts[0] : "その他";
        return {
            name: doc.name,
            description: doc.description || "説明が設定されていません。",
            category: category,
        };
    });

    const configDoc = await db.db("DashboardBot").collection("CommandDisabled").findOne({ 
        Guild: new Long(guildid) 
    });
    
    const disabled_commands: string[] = configDoc?.commands || [];
    const role_restrictions: Record<string, string> = configDoc?.roleRestrictions || {};

    const guild_roles = await getRoles(guildid);
    const RolesData = Array.isArray((guild_roles as any).data)
        ? (guild_roles as any).data
        : (Array.isArray(guild_roles) ? guild_roles : []);

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のコマンド設定</h1>

            <form action={sendData}>
                <CommandList
                    commands={commands}
                    disabledCommands={disabled_commands}
                    initialRoleRestrictions={role_restrictions} 
                    roles={RolesData}
                />

                <div className="fixed bottom-8 right-8 z-50">
                    <button
                        type="submit"
                        className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-3 rounded-full shadow-2xl transition-all transform hover:scale-105 active:scale-95 flex items-center gap-2"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        設定を保存する
                    </button>
                </div>
            </form>
        </div>
    );
}