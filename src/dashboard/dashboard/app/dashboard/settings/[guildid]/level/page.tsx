import { cookies } from "next/headers";
import { getGuild, getChannels, getRoles } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import { revalidatePath } from "next/cache";
import Form from "@/app/components/Form";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";

export default async function LevelPage({ params }: { params: { guildid: string } }) {
    const { guildid } = await params;

    async function sendData(formData: FormData) {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const checkenable = formData.get("checkenable") === "true" || formData.get("checkenable") === "on";
        const is_slient = formData.get("is_slient") === "true" || formData.get("is_slient") === "on";
        const channel = formData.get("levelupchannel") as string;
        
        const totalMsg = formData.get("msg_Total") as string;
        const textMsg = formData.get("msg_Text") as string;
        const voiceMsg = formData.get("msg_Voice") as string;

        const db = await connectDB();

        if (checkenable) {
            await db.db("Main").collection("LevelingSetting").updateOne(
                { Guild: Long.fromString(guildid) },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        UpdatedAt: new Date(),
                        TotalMessage: totalMsg,
                        TextMessage: textMsg,
                        VoiceMessage: voiceMsg,
                        Silent: is_slient
                    },
                },
                { upsert: true }
            );

            await db.db("Main").collection("LevelingUpAlertChannel").updateOne(
                { Guild: Long.fromString(guildid) },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        Channel: Long.fromString(channel)
                    },
                },
                { upsert: true }
            );
        } else {
            await db.db("Main").collection("LevelingSetting").deleteOne({ Guild: Long.fromString(guildid) });
            await db.db("Main").collection("LevelingUpAlertChannel").deleteOne({ Guild: Long.fromString(guildid) });
        }
        revalidatePath(`/dashboard/settings/${guildid}/level`);
    }

    async function leveluprole_set(formData: FormData) {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        try {
            const role = formData.get("role") as string;
            const level = formData.get("level") as string;
            const category = formData.get("category") as string;

            const db = await connectDB();
            await db.db("Main").collection("LevelingUpRole").updateOne(
                { Guild: Long.fromString(guildid), Level: Long.fromString(level), Category: category },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        Level: Long.fromString(level),
                        Role: Long.fromString(role),
                        Category: category
                    },
                },
                { upsert: true }
            );
            revalidatePath(`/dashboard/settings/${guildid}/level`);
        } catch { return; }
    }

    async function deleteLevel(formData: FormData) {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const level = formData.get('level');
        const category = formData.get('category');

        const db = await connectDB();
        await db.db("Main").collection("LevelingUpRole").deleteOne({
            Guild: Long.fromString(guildid), 
            Level: Long.fromString(level as string),
            Category: category
        });

        revalidatePath(`/dashboard/settings/${guildid}/level`);
    }

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p>セッションが無効です。</p>;

    const guild_channels = await getChannels(guildid);
    const channelsData = (Array.isArray((guild_channels as any).data) ? (guild_channels as any).data : guild_channels) || [];
    const guild_roles = await getRoles(guildid);
    const RolesData = (Array.isArray((guild_roles as any).data) ? (guild_roles as any).data : guild_roles) || [];

    const db = await connectDB();
    const setting = await db.db("Main").collection("LevelingSetting").findOne({ Guild: Long.fromString(guildid) });
    const alertChannel = await db.db("Main").collection("LevelingUpAlertChannel").findOne({ Guild: Long.fromString(guildid) });
    const rewards = await db.db("Main").collection("LevelingUpRole").find({ Guild: Long.fromString(guildid) }).sort({ Level: 1 }).toArray();

    const enabled = !!setting;
    const isslient_enabled = setting?.Silent ? setting?.Silent : false;
    const selectedChannel = alertChannel?.Channel ? String(alertChannel.Channel) : "";

    return (
        <div className="p-4 flex flex-col gap-6 text-gray-200">
            <h1 className="text-2xl font-bold">{guild.name} のレベル設定</h1>

            <LineAndTextLayout text="基本設定"/>
            <Form action={sendData} buttonlabel="設定を保存">
                <div className="flex items-center gap-4 mb-4">
                    <span className="font-semibold">機能を有効にする</span>
                    <ToggleButton name="checkenable" defaultValue={enabled} />
                </div>

                <div className="flex items-center gap-4 mb-4">
                    <span className="font-semibold">通知を無効化するか</span>
                    <ToggleButton name="is_slient" defaultValue={isslient_enabled} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                        { id: "Total", label: "📊 総合レベル通知", val: setting?.TotalMessage || setting?.Message },
                        { id: "Text", label: "💬 テキストレベル通知", val: setting?.TextMessage },
                        { id: "Voice", label: "🔊 ボイスレベル通知", val: setting?.VoiceMessage }
                    ].map(item => (
                        <div key={item.id} className="flex flex-col gap-2">
                            <span className="text-sm font-bold text-gray-400">{item.label}</span>
                            <textarea
                                name={`msg_${item.id}`}
                                className="border p-2 rounded bg-gray-800 text-white h-24 text-sm"
                                defaultValue={item.val || "{user}さんの {category}レベルが {newlevel} に上がったよ！"}
                                required
                            />
                        </div>
                    ))}
                </div>

                <div className="mt-4 p-3 bg-gray-900 rounded text-xs text-gray-400">
                    変数: {"{user}"} (名前) / {"{newlevel}"} (新レベル) / {"{category}"} (種類)
                </div>

                <span className="font-semibold mt-4 block">通知先チャンネル</span>
                <select name="levelupchannel" defaultValue={selectedChannel} className="border p-2 rounded bg-gray-800 text-white w-full max-w-xs">
                    {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                        <option key={ch.id} value={ch.id}># {ch.name}</option>
                    ))}
                </select>
            </Form>

            <LineAndTextLayout text="報酬ロール設定"/>
            <div className="bg-gray-800 p-4 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                        <h2 className="font-bold mb-3">現在の報酬一覧</h2>
                        {rewards.length > 0 ? (
                            <div className="flex flex-col gap-2">
                                {rewards.map((item) => {
                                    const role = RolesData.find((ro: any) => String(ro.id) === String(item.Role));
                                    return (
                                        <div key={`${item.Category}-${item.Level}`} className="flex justify-between items-center bg-gray-700 p-2 rounded">
                                            <div className="text-sm">
                                                <span className="bg-blue-600 px-2 py-0.5 rounded text-[10px] mr-2 uppercase">{item.Category || "Total"}</span>
                                                <strong>Lv.{String(item.Level)}</strong> → {role?.name || "不明なロール"}
                                            </div>
                                            <form action={deleteLevel}>
                                                <input type="hidden" name="level" value={String(item.Level)} />
                                                <input type="hidden" name="category" value={item.Category || "Total"} />
                                                <button type="submit" className="text-red-400 hover:text-red-300">❌</button>
                                            </form>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : <p className="text-gray-500 text-sm">設定なし</p>}
                    </div>

                    <div className="border-l border-gray-700 pl-8">
                        <h2 className="font-bold mb-3">報酬を追加</h2>
                        <Form action={leveluprole_set} buttonlabel="報酬を追加">
                            <span className="text-sm">対象カテゴリ</span>
                            <select name="category" className="p-2 rounded bg-gray-700 text-sm mb-3">
                                <option value="Total">総合 (Total)</option>
                                <option value="Text">テキスト (Text)</option>
                                <option value="Voice">ボイス (Voice)</option>
                            </select>

                            <span className="text-sm">到達レベル</span>
                            <input type="number" name="level" className="p-2 rounded bg-gray-700 text-sm mb-3" required />

                            <span className="text-sm">付与ロール</span>
                            <select name="role" className="p-2 rounded bg-gray-700 text-sm mb-3">
                                {RolesData?.map((ro: any) => (
                                    <option key={ro.id} value={ro.id}>{ro.name}</option>
                                ))}
                            </select>
                        </Form>
                    </div>
                </div>
            </div>
        </div>
    );
}