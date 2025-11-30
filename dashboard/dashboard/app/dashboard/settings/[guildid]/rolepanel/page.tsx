import { cookies } from "next/headers";
import { getGuild, getChannels, getRoles, sendMessage } from "@/lib/discord/fetch";
import ToggleButton from "@/app/components/ToggleButton";

const cooldowns = new Map<string, number>();

export default async function RolePanelPage({
    params,
}: {
    params: { guildid: string };
}) {

    // -------------------------------------------------------
    // Server Action（ロールパネル作成）
    // -------------------------------------------------------
    async function createRolePanel(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        // クールダウン
        const now = Date.now();
        const lastTime = cooldowns.get(sessionId) ?? 0;
        const cooldownMs = 10 * 1000;

        if (now - lastTime < cooldownMs) {
            return;
        }

        cooldowns.set(sessionId, now);

        const channel = formData.get("channel_select")?.toString();
        if (!channel) return;

        const title = formData.get("title")?.toString() ?? "";
        const description = formData.get("description")?.toString() ?? "";
        const showMention = formData.get("showMention") === "true" || formData.get("showMention") === "on";

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

        const guild_roles = await getRoles(guildid);
        const RolesData =
            Array.isArray((guild_roles as any).data)
                ? (guild_roles as any).data
                : guild_roles;

        if (!RolesData) {
            console.error("ロール取得失敗");
            return;
        }

        const RoleMap = new Map<string, string>();
        for (const r of RolesData) {
            RoleMap.set(r.id, r.name);
        }

        const roles: string[] = [];

        for (let i = 1; i <= 10; i++) {
            const id = formData.get(`role${i}`)?.toString();
            if (id) roles.push(id);
        }

        const embed: any = {
            title,
            description,
            color: 0x57f287,
        };

        if (showMention && roles.length > 0) {
            embed.fields = [
                {
                    name: "ロール一覧",
                    value: roles.map((id) => `<@&${id}>`).join("\n"),
                },
            ];
        }

        function chunk<T>(arr: T[], size: number): T[][] {
            const chunks = [];
            for (let i = 0; i < arr.length; i += size) {
                chunks.push(arr.slice(i, i + size));
            }
            return chunks;
        }

        const components = chunk(roles, 5).map(chunkedIds => ({
            type: 1,
            components: chunkedIds.map(id => ({
                type: 2,
                style: 1,
                label: RoleMap.get(id) ?? `ロール: ${id}`,
                custom_id: `rolepanel_v1+${id}`,
            }))
        }));

        await sendMessage(channel, {
            embeds: [embed],
            components,
        });
    }

    // -------------------------------------------------------
    // ページ表示部
    // -------------------------------------------------------

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;

    if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

    const { guildid } = await params;
    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p>セッションが無効です。</p>;

    const guild_channels = await getChannels(guildid);
    const channelsData =
        Array.isArray((guild_channels as any).data)
            ? (guild_channels as any).data
            : guild_channels;

    const guild_roles = await getRoles(guildid);
    const RolesData =
        Array.isArray((guild_roles as any).data)
            ? (guild_roles as any).data
            : guild_roles;

    if (!RolesData) return <p>サーバーのロールを取得できませんでした。</p>;

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のロールパネル</h1>

            <form action={createRolePanel} className="flex flex-col gap-3">

                {/* タイトル */}
                <label>
                    タイトル
                    <input
                        name="title"
                        className="border p-2 w-full bg-gray-800 text-white"
                        placeholder="タイトルを入力"
                        required
                    />
                </label>

                {/* 説明 */}
                <label>
                    説明
                    <textarea
                        name="description"
                        className="border p-2 w-full bg-gray-800 text-white"
                        placeholder="説明を入力"
                    />
                </label>

                {/* メンション表示 */}
                <label className="flex gap-2 items-center">
                    ロールのメンションを表示する
                    <ToggleButton name="showMention" defaultValue={false} />
                </label>

                {/* チャンネル選択 */}
                <label>
                    パネルを送信するチャンネル
                    <select
                        name="channel_select"
                        className="border p-2 rounded bg-gray-800 text-white"
                        required
                    >
                        {channelsData
                            ?.filter((ch: any) => ch.type === 0)
                            .map((ch: any) => (
                                <option key={ch.id} value={ch.id}>
                                    {ch.name}
                                </option>
                            ))}
                    </select>
                </label>

                {/* ロール選択（1〜10） */}
                <span className="font-semibold">ロール（最大 10 個）</span>
                {Array.from({ length: 10 }).map((_, i) => (
                    <label key={i}>
                        ロール {i + 1}: 
                        <select
                            name={`role${i + 1}`}
                            className="border p-2 rounded bg-gray-800 text-white"
                            {...(i === 0 ? { required: true } : {})}
                        >
                            <option value="">選択しない</option>
                            {RolesData?.map((r: any) => (
                                <option key={r.id} value={r.id}>
                                    {r.name}
                                </option>
                            ))}
                        </select>
                    </label>
                ))}

                <button type="submit" className="bg-blue-500 text-white p-2 rounded">
                    ロールパネルを作成する
                </button>
            </form>
        </div>
    );
}