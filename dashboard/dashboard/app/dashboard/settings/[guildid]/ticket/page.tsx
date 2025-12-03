import { cookies } from "next/headers";
import { getGuild, getChannels, getRoles, sendMessage } from "@/lib/discord/fetch";
import ToggleButton from "@/app/components/ToggleButton";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";

const cooldowns = new Map<string, number>();

export default async function TicketPanelPage({
    params,
}: {
    params: { guildid: string };
}) {

    async function createTicketPanel(formData: FormData) {
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

        const embed: any = {
            title,
            description,
            color: 0x57f287,
        };

        const components = [
            {
                type: 1,
                components: [
                    {
                        type: 2,
                        style: 1,
                        label: "チケットを作成",
                        custom_id: "ticket_v1",
                    },
                ],
            },
        ];

        const msg = await sendMessage(channel, {
            embeds: [embed],
            components,
        });

        const category = formData.get("category_select")?.toString();
        if (!category) return;

        if (msg?.data?.id) {
            const db = await connectDB();
            await db.db("Main").collection("TicketCategory").updateOne({
                Message: new Long(msg.data?.id as string)
            }, {
                $set: {
                    Channel: new Long(category),
                    Message: new Long(msg.data.id as string)
                }
            }, {
                upsert: true
            })
            // console.log('カテゴリが保存されました。')
        }
    }

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

    if (!channelsData) return <p>サーバーのチャンネルを取得できませんでした。</p>;

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のチケット</h1>

            <form action={createTicketPanel} className="flex flex-col gap-3">

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

                <span className="font-semibold mb-1">チケットを作成するカテゴリチャンネル</span>
                <select
                    name="category_select"
                    className="border p-2 rounded bg-gray-800 text-white"
                >
                    {channelsData
                        ?.filter((ch: any) => ch.type === 4)
                        .map((ch: any) => (
                            <option key={ch.id} value={ch.id}>
                                {ch.name}
                            </option>
                            ))}
                </select>

                {/* 送信するチャンネル選択 */}
                <span className="font-semibold mb-1">パネルを送信するチャンネル</span>

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

                <button type="submit" className="bg-blue-500 text-white p-2 rounded">
                    チケットパネルを送信する
                </button>
            </form>
        </div>
    );
}