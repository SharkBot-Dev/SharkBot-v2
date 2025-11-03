import { getGuild } from '@/lib/discord/fetch';
import { cookies } from "next/headers";

export default async function GuildLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: any;
}) {
  const { guildid } = await params;

  const cookieStore = await cookies();
  const sessionId = cookieStore.get("session_id")?.value;
  if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

  const guild = await getGuild(sessionId, guildid);

  if (!guild) return <p>セッションが無効です。</p>;

  return (
    <div className="flex min-h-screen bg-gray-100">
      <aside className="fixed top-0 left-0 h-screen w-64 bg-black border-r border-gray-200 p-4 overflow-y-auto">
        <h1 className="text-2xl mt-3 text-white">SharkBot</h1>

        <nav className="space-y-2 mt-6">
          <a href={`/dashboard/`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            サーバー選択
          </a>
          <a href={`/dashboard/settings/${guildid}`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            ホーム
          </a>
          <a href={`/dashboard/settings/${guildid}/commands`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            コマンド一覧
          </a>
          <a href={`/dashboard/settings/${guildid}/join-message`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            よろしくメッセージ
          </a>
          <a href={`/dashboard/settings/${guildid}/leave-message`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            さようならメッセージ
          </a>
          <a href={`/dashboard/settings/${guildid}/auto-thread`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            自動スレッド作成
          </a>
          <a href={`/dashboard/settings/${guildid}/expand`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            メッセージ展開
          </a>
          <a href={`/dashboard/settings/${guildid}/poll`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            投票
          </a>
          <a href={`/dashboard/settings/${guildid}/level`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            レベル
          </a>
          <a href={`/dashboard/settings/${guildid}/economy`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            サーバー内経済
          </a>
        </nav>
      </aside>

      <main className="flex-1 p-6 bg-black ml-64 text-white overflow-y-auto min-h-screen">
        {children}
      </main>
    </div>
  );
}