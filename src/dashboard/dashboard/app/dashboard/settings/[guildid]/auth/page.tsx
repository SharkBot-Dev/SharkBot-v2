import { cookies } from "next/headers";
import { getChannels, getGuild, getRoles, sendMessage } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import Form from "@/app/components/Form";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";
import { revalidatePath } from "next/cache";

const cooldowns = new Map<string, number>();

export default async function AuthPage({ params }: { params: { guildid: string } }) {
    const { guildid } = await params;
    async function setCommands(formData: FormData) {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

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

    async function setServerBan(formData: FormData) {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const gtext = formData.get('banserverlist') as string;
        const db = await connectDB();
        const col = db.db("Main").collection("GuildBAN");

        await col.deleteMany({ Guild: guildid });

        if (gtext && gtext.trim().length > 0) {
            const gids = gtext.split("\n").map(id => id.trim()).filter(id => id !== "");
            for (const value of gids) {
                await col.updateOne(
                    { Guild: guildid, BANGuild: value },
                    { $set: { Guild: guildid, BANGuild: value } },
                    { upsert: true }
                );
            }
        }

        revalidatePath(`/dashboard/settings/${guildid}/auth`);
    }

    async function createAuthPanel(formData: FormData) {
        "use server";
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const now = Date.now();
        const lastTime = cooldowns.get(sessionId) ?? 0;
        if (now - lastTime < 10000) return;
        cooldowns.set(sessionId, now);

        const channelId = formData.get("channel_select")?.toString();
        const roleId = formData.get("role_id")?.toString();
        const auth_type = formData.get("auth_type")?.toString();
        
        if (!channelId || !roleId) return;

        const channelsData = (() => {
            if (!guild_channels) return null;
            if (Array.isArray((guild_channels as any).data)) return (guild_channels as any).data;
            if (Array.isArray(guild_channels)) return guild_channels as any;
            return null;
        })();

        const exists = channelsData.some((c: any) => c.id === channelId);

        if (!exists) {
            return;
        }

        const idMap: Record<string, string> = {
            "auth": `authpanel_v2+${roleId}`,
            "abs-auth": `authpanel_v1+${roleId}`,
            "web-auth": `boostauth+${roleId}`
        };

        const customId = idMap[auth_type || "auth"];
        const title = formData.get("title")?.toString() || "Web認証";
        const description = formData.get("description")?.toString() || "下のボタンを押して認証を開始してください。";

        try {
            await sendMessage(channelId, {
                embeds: [{ 
                    title, 
                    description, 
                    color: 0x57f287
                }],
                components: [{
                    type: 1,
                    components: [{
                        type: 2,
                        style: 1,
                        label: "認証",
                        custom_id: customId
                    }]
                }],
            });
        } catch (error) {
            return;
        }
    }

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p>セッションが無効です。</p>;

    const db = await connectDB();
    const disabledDoc = await db.db("DashboardBot").collection("CommandDisabled").findOne({ Guild: new Long(guildid) });
    const disabled_commands: string[] = disabledDoc?.commands || [];
    const banguildDoc = await db.db("Main").collection("GuildBAN").find({ Guild: guildid }).toArray();
    const banguildsString = banguildDoc.map(doc => doc.BANGuild).join("\n");

    const [rolesData, guild_channels] = await Promise.all([
        getRoles(guildid),
        getChannels(guildid)
    ]);

    const roles = Array.isArray(rolesData) ? rolesData : (rolesData as any).data || [];
    const selectableRoles = roles.filter((role: any) => role.name !== "@everyone");
    const channelsData = Array.isArray((guild_channels as any).data) ? (guild_channels as any).data : guild_channels;

    return (
        <div className="p-4 flex flex-col gap-8">
            <h1 className="text-2xl font-bold">{guild.name} の認証設定</h1>

            <section>
                <LineAndTextLayout text="認証パネルを作成する"/>
                <Form action={createAuthPanel} buttonlabel="送信する">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                        <div>
                            <label className="font-semibold text-sm">タイトル</label>
                            <input name="title" className="border p-2 w-full bg-gray-800 text-white rounded mt-1" defaultValue="認証をする" />
                        </div>
                        <div>
                            <label className="font-semibold text-sm">認証完了時に付与するロール</label>
                            <select name="role_id" className="p-2 border rounded w-full bg-gray-800 text-white mt-1">
                                <option value="">ロールを選択してください</option>
                                {selectableRoles.map((role: any) => (
                                    <option key={role.id} value={role.id}>{role.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="md:col-span-2">
                            <label className="font-semibold text-sm">説明</label>
                            <textarea name="description" className="border p-2 w-full bg-gray-800 text-white rounded mt-1 h-20" defaultValue="下のボタンを押して認証を開始してください。" />
                        </div>
                        <div className="md:col-span-2">
                            <label className="font-semibold text-sm">認証タイプ</label>
                            <select name="auth_type" className="border p-2 rounded bg-gray-800 text-white w-full mt-1" required>
                                <option value="auth">ワンクリック認証</option>
                                <option value="abs-auth">計算認証</option>
                                <option value="web-auth">Web認証</option>
                            </select>
                        </div>
                        <div className="md:col-span-2">
                            <label className="font-semibold text-sm">送信チャンネル</label>
                            <select name="channel_select" className="border p-2 rounded bg-gray-800 text-white w-full mt-1" required>
                                {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                                    <option key={ch.id} value={ch.id}>#{ch.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </Form>
            </section>

            <section>
                <LineAndTextLayout text="Web認証時に参加していると拒否するサーバーの一覧"/>
                <Form action={setServerBan} buttonlabel="設定を保存">
                    <textarea 
                        name="banserverlist" 
                        className="border p-2 w-full bg-gray-800 text-white rounded mt-1 h-32 font-mono text-sm"
                        defaultValue={banguildsString}
                        placeholder={"サーバーIDを改行区切りで入力..."}
                    />
                </Form>
            </section>

            <section>
                <LineAndTextLayout text="認証を作成できるコマンドの設定"/>
                <Form action={setCommands} buttonlabel="設定を保存">
                    <div className="flex flex-col gap-4">
                        {['panel auth auth', 'panel auth abs-auth', 'panel auth webauth'].map((cmd) => (
                            <div key={cmd} className="flex flex-col border-b border-gray-700 pb-2">
                                <span className="font-semibold text-sm mb-1">{cmd.replace('panel auth ', '').toUpperCase()} 認証</span>
                                <ToggleButton name={cmd.replace('panel auth ', '').replace('-', '')} defaultValue={!disabled_commands.includes(cmd)} />
                            </div>
                        ))}
                    </div>
                </Form>
            </section>

            <div className="bg-blue-900/30 p-4 rounded-md border border-blue-500/50">
                <span className="font-semibold mb-2 block text-blue-300">その他の設定</span>
                <a href={`/dashboard/settings/${guildid}/commands`} className="inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                    コマンドの設定に移動する
                </a>
            </div>
        </div>
    );
}