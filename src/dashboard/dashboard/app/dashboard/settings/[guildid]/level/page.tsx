import { cookies } from "next/headers";
import { getGuild, getChannels, getRoles } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import { revalidatePath } from "next/cache";
import Form from "@/app/components/Form";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";

export default async function LevelPage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const checkenable = formData.get("checkenable") === "true" || formData.get("checkenable") === "on";
        const channel = formData.get("levelupchannel") as string;
        const levelupmessage = formData.get("levelupmessage") as string;

        const guild_channels = await getChannels(guildid);
        const channelsData =
            Array.isArray((guild_channels as any).data)
                ? (guild_channels as any).data
                : guild_channels;

        const exists = channelsData.some((c: any) => c.id === channel);

        if (!exists) {
            console.error("チャンネルが存在しません");
            return;
        }

        const db = await connectDB();

        if (checkenable) {
            await db.db("Main").collection("LevelingSetting").updateOne(
                { Guild: Long.fromString(guildid) },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        UpdatedAt: new Date(),
                        Message: levelupmessage
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
            // 無効化する場合は設定を削除
            await db.db("Main").collection("LevelingSetting").deleteOne({ Guild: Long.fromString(guildid) });
            await db.db("Main").collection("LevelingUpAlertChannel").deleteOne({ Guild: Long.fromString(guildid) });
        }
    }

    async function leveluprole_set(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        try {
            const role = formData.get("role") as string;
            const level = formData.get("level") as string;

            const db = await connectDB();

            await db.db("Main").collection("LevelingUpRole").updateOne(
                { Guild: Long.fromString(guildid), Level: Long.fromString(level) },
                {
                    $set: {
                        Guild: Long.fromString(guildid),
                        Level: Long.fromString(level),
                        Role: Long.fromString(role)
                    },
                },
                { upsert: true }
            );

            revalidatePath(`/dashboard/settings/${guildid}/level`);
        } catch {
            return;
        }
    }

    async function deleteLevel(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        if (!guildid) return;

        const db = await connectDB();

        const find_item = db.db("Main").collection("LevelingUpRole");

        const level = formData.get('level');

        if (!level) return;

        find_item.deleteOne({Guild: new Long(guildid), Level: Long.fromString(level as any)})

        revalidatePath(`/dashboard/settings/${guildid}/level`);
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

    const guild_channels = await getChannels(guildid);

    const channelsData = (() => {
        if (!guild_channels) return null;
        if (Array.isArray((guild_channels as any).data)) return (guild_channels as any).data;
        if (Array.isArray(guild_channels)) return guild_channels as any;
        return null;
    })();

    if (!channelsData) return <p>サーバーのチャンネルを取得できませんでした。</p>;

    const guild_roles = await getRoles(guildid);

    const RolesData = (() => {
        if (!guild_roles) return null;
        if (Array.isArray((guild_roles as any).data)) return (guild_roles as any).data;
        if (Array.isArray(guild_roles)) return guild_roles as any;
        return null;
    })();

    if (!RolesData) return <p>サーバーのロールを取得できませんでした。</p>;

    const db = await connectDB();
    const leveling_setting_findone = await db.db("Main").collection("LevelingSetting").findOne({ Guild: Long.fromString(guildid) });
    const leveling_channel_findone = await db.db("Main").collection("LevelingUpAlertChannel").findOne({ Guild: Long.fromString(guildid) });

    const enabled = !!leveling_setting_findone;
    const desc = leveling_setting_findone?.Message ?? "`{user}`さんの\nレベルが「{newlevel}」になったよ！";
    const selectedChannel = leveling_channel_findone?.Channel ? String(leveling_channel_findone.Channel) : "";

    const leveling_role_find = await db.db("Main").collection("LevelingUpRole").find({Guild: new Long(guildid)}).toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のレベル</h1>

            <LineAndTextLayout text="メイン設定"/>

            <Form action={sendData} buttonlabel="設定を保存">
                <span className="font-semibold mb-1">機能を有効にする</span>
                <ToggleButton name="checkenable" defaultValue={enabled} />

                <span className="font-semibold mb-1">レベルアップメッセージ</span>
                <textarea
                    name="levelupmessage"
                    className="border p-2 rounded bg-gray-800 text-white"
                    placeholder="レベルアップメッセージ"
                    defaultValue={desc}
                    required
                />

                <span className="font-semibold mb-1">レベルアップ通知チャンネル</span>
                <select
                    name="levelupchannel"
                    defaultValue={selectedChannel}
                    className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                        <option key={ch.id} value={ch.id}>
                            {ch.name}
                        </option>
                    ))}
                </select>
            </Form><br/>

            <LineAndTextLayout text="レベルアップ時に追加するロール"/>

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">
                    レベルアップ時に追加するロール
                </h2>
                {leveling_role_find.length > 0 ? (
                    <ul className="border rounded divide-y divide-gray-700">
                        {leveling_role_find.map((item) => {
                            const role = RolesData.find(
                                (ro: any) =>
                                    String(ro.id) === String(item.Role)
                            );
                            return (
                                <li
                                    key={String(item.Role)}
                                    className="p-3 flex justify-between items-center"
                                >
                                    <span>
                                        <strong>
                                            {role
                                                ? role.name
                                                : "不明なロール"}{" "}
                                            - {String(item.Level)}レベル
                                        </strong>
                                    </span>
                                    <form action={deleteLevel}>
                                        <input
                                            type="hidden"
                                            name="level"
                                            value={String(item.Level)}
                                        />
                                        <button
                                            type="submit"
                                            className="bg-red-600 hover:bg-red-500 text-white font-semibold py-1 px-3 rounded"
                                        >
                                            ❌
                                        </button>
                                    </form>
                                </li>
                            );
                        })}
                    </ul>
                ) : (
                    <p className="text-gray-400">設定がまだありません。</p>
                )}
            </div>

            <div className="mb-6">

                <Form action={leveluprole_set} buttonlabel="追加する">
                    <span className="font-semibold mb-1">ロールを選択</span>
                    <select
                        name="role"
                        className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {RolesData?.map((ch: any) => (
                            <option key={ch.id} value={ch.id}>
                                {ch.name}
                            </option>
                        ))}
                    </select>

                    <span className="font-semibold mb-1">レベルを入力</span>
                    <input
                    type="number"
                    name="level"
                    className="border p-2"
                    />

                </Form>
            </div>
        </div>
    );
}