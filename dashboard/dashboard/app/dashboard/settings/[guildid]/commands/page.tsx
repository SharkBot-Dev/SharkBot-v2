import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long, ObjectId } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";

export default async function EconomyPage({ params }: { params: { guildid: string } }) {
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
        .map((doc: any) => ({
            name: doc.name,
            description: doc.description || "説明が設定されていません。",
        }));

    const disabledDoc = await db.db("DashboardBot").collection("CommandDisabled").findOne({ Guild: new Long(guildid) });
    const disabled_commands: string[] = disabledDoc?.commands || [];


    return (
        <div className="p-6">
            <h1 className="text-3xl font-bold mb-6 text-white">{guild.name} のコマンド設定</h1>

            <form action={sendData} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {commands.map((cmd, idx) => (
                    <div
                        key={idx}
                        className="flex flex-col justify-between bg-gray-900 p-4 rounded-lg shadow-md border border-gray-700"
                    >
                        <div>
                            <h2 className="text-lg font-semibold text-white">{cmd.name}</h2>
                            <p className="text-sm text-gray-400 mt-1">{cmd.description}</p>
                        </div>

                        <div className="flex justify-end mt-3">
                            <ToggleButton
                                name={cmd.name}
                                defaultValue={!disabled_commands.includes(cmd.name)}
                            />
                        </div>
                    </div>
                ))}

                <div className="col-span-full flex justify-end mt-4">
                    <button
                        type="submit"
                        className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 transition"
                    >
                        設定を保存
                    </button>
                </div>
            </form>
        </div>
    );
}