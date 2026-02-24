import { cookies } from "next/headers";
import { getGuild } from "@/lib/discord/fetch";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function SearchPage({ 
    params 
}: { 
    params: Promise<{ guildid: string }>
}) {
    const { guildid } = await params;
    
    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;

    if (!sessionId) {
        return (
            <div className="p-4 text-red-500">
                ログイン情報が見つかりません。再ログインしてください。
            </div>
        );
    }

    const guild = await getGuild(sessionId, guildid);

    if (!guild) {
        return (
            <div className="p-4">
                <p>セッションが無効、またはサーバーが見つかりませんでした。</p>
            </div>
        );
    }

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-6">{guild.name} のセットアップ</h1>

            <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-semibold mb-4">使ってみたい機能はありますか？</h3>
                
                <div>
                    <Link
                        href={`/dashboard/settings/${guildid}/rolepanel`}
                        className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
                    >
                        🧙ロールパネル
                    </Link><br/><br/>
                    <Link
                        href={`/dashboard/settings/${guildid}/level`}
                        className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
                    >
                        🏆レベル
                    </Link><br/><br/>
                    <Link
                        href={`/dashboard/settings/${guildid}/achievement`}
                        className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
                    >
                        🏅実績
                    </Link><br/><br/>
                    <Link
                        href={`/dashboard/settings/${guildid}/economy`}
                        className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
                    >
                        💰経済
                    </Link>
                </div>
            </div><br/><br/>

            <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-semibold mb-4">サポートサーバーに参加しませんか？</h3>
                
                <div>
                    <Link
                        href="https://dashboard.sharkbot.xyz/servers/1343124570131009579"
                        className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
                    >
                        参加する
                    </Link>
                </div>
            </div>
        </div>
    );
}