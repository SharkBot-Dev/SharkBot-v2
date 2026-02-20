import { cookies } from "next/headers";
import { getGuild } from "@/lib/discord/fetch";

export default async function CustomBot({ params }: { params: { guildid: string } }) {
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

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} のカスタムBot設定</h1>

            
        </div>
    );
}