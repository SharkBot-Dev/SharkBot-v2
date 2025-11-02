import { getGuild, getGuildRequest } from "@/lib/discord/fetch";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function Home({ params }: { params: { guildid: string } }) {
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

    const fetch_guild = await getGuildRequest(guildid);
    if (!fetch_guild) {
      redirect(
        "https://discord.com/oauth2/authorize?client_id=1322100616369147924&permissions=8&integration_type=0&scope=bot+applications.commands"
      );
    }

    return (
      <main className="flex flex-col items-center justify-center h-screen">
        <h1 className="text-3xl mb-6">左のメニューから操作してください。</h1>
      </main>
    );
}