import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long, ObjectId } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import CommandList from "./CommandList";

export default async function CommandPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const db = await connectDB();

        const commands = formData.getAll("commands") as string[];

        const allCommands = (await db.db("DashboardBot").collection("Commands").find().toArray())
            .map((doc: any) => doc.name);

        const disabledCommands: string[] = [];

        for (const cmd of allCommands) {
            const val = formData.get(cmd);
            if (val === "false") {
                disabledCommands.push(cmd);
            }
        }

        await db.db("DashboardBot").collection("CommandDisabled").updateOne(
            { Guild: new Long(guildid) },
            { $set: { commands: disabledCommands } },
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
    const commands = (await db.db("DashboardBot").collection("Commands").find().toArray())
        .map((doc: any) => {
            const parts = doc.name?.split(" ") || [];
            const category = parts.length > 1 ? parts[0] : "その他";

            return {
                name: doc.name,
                description: doc.description || "説明が設定されていません。",
                category: category,
            };
        });

    const disabledDoc = await db.db("DashboardBot").collection("CommandDisabled").findOne({ Guild: new Long(guildid) });
    const disabled_commands: string[] = disabledDoc?.commands || [];

    const groupedCommands = commands.reduce((acc: any, cmd: any) => {
        if (!acc[cmd.category]) acc[cmd.category] = [];
        acc[cmd.category].push(cmd);
        return acc;
    }, {});

    return (
        <div className="p-6">
            <h1 className="text-3xl font-bold mb-6 text-white">
                {guild.name} のコマンド設定
            </h1>

            <form action={sendData} className="grid grid-cols-1 gap-4">
                <CommandList
                    commands={commands}
                    disabledCommands={disabled_commands}
                />

                <div className="sticky bottom-4 flex justify-end">
                    <button
                        type="submit"
                        className="bg-blue-500 text-white px-6 py-2 rounded shadow-lg hover:bg-blue-600 transition"
                    >
                        設定を保存
                    </button>
                </div>
            </form>
        </div>
    );
}