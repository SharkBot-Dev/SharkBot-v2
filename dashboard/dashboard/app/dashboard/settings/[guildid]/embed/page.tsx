import { cookies } from "next/headers";
import { getGuild, getChannels, sendMessage } from "@/lib/discord/fetch";
import ColorPalette from "@/app/components/ColorPicker";

const cooldowns = new Map<string, number>();

export default async function EmbedPage({ params }: { params: { guildid: string } }) {

    // --- サーバーアクション ---
    async function sendData(formData: FormData) {
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
        if (now - lastTime < cooldownMs) return;
        cooldowns.set(sessionId, now);

        const channel = formData.get("channel")?.toString();
        if (!channel) return;

        const title = formData.get("title")?.toString() ?? "";
        const description = formData.get("desc")?.toString() ?? "";
        const color = formData.get("color")?.toString() ?? "#57f287";

        const imageUrl = formData.get("image_url")?.toString() ?? undefined;
        const thumbnailUrl = formData.get("thumbnail_url")?.toString() ?? undefined;

        const guild_channels = await getChannels(guildid);
        const channelsData = Array.isArray((guild_channels as any).data)
            ? (guild_channels as any).data
            : guild_channels;

        const exists = channelsData.some((c: any) => c.id === channel);
        if (!exists) return;

        const embed: any = {
            title,
            description,
            color: parseInt(color.replace("#", ""), 16),

            footer: {
                text: `${guild.name} / ${guild.id}`,
                icon_url: guild.icon
                    ? `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`
                    : "https://cdn.discordapp.com/embed/avatars/0.png",
            },

            image: imageUrl ? { url: imageUrl } : undefined,
            thumbnail: thumbnailUrl ? { url: thumbnailUrl } : undefined,
        };

        await sendMessage(channel, { embeds: [embed] });
    }

    const { guildid } = await params;
    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return <p>セッションが無効です。</p>;

    const guild_channels = await getChannels(guildid);

    const channelsData = Array.isArray((guild_channels as any).data)
        ? (guild_channels as any).data
        : guild_channels;

    if (!channelsData) return <p>サーバーのチャンネルを取得できませんでした。</p>;

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の埋め込み作成</h1>

            <form action={sendData} className="flex flex-col gap-2">
                <span className="font-semibold mb-1">タイトル・説明</span>
                <input type="text" name="title" placeholder="タイトル" className="border p-2" />
                <textarea name="desc" placeholder="説明" className="border p-2" />

                <span className="font-semibold mb-1">色</span>
                <ColorPalette name="color" />

                <span className="font-semibold mb-1">画像・サムネイル</span>
                <input type="text" name="image_url" placeholder="画像URL" className="border p-2" />
                <input type="text" name="thumbnail_url" placeholder="サムネイルURL" className="border p-2" />

                <span className="font-semibold mb-1">送信先チャンネル</span>
                <select
                    name="channel"
                    className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500"
                >
                    {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                        <option key={ch.id} value={ch.id}>
                            {ch.name}
                        </option>
                    ))}
                </select>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded">
                    送信する
                </button>
            </form>
        </div>
    );
}