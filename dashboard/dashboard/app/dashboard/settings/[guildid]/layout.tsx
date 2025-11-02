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
      <aside className="w-64 bg-black border-r border-gray-200 p-4">
        <h1 className="text-2xl mt-3">SharkBot</h1>
        <nav className="space-y-2">
          <a
            href={`/dashboard/`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            サーバー選択
          </a>
        </nav>
        <nav className="space-y-2">
          <a
            href={`/dashboard/settings/${guildid}`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            ホーム
          </a>
        </nav>
        <nav className="space-y-2">
          <a
            href={`/dashboard/settings/${guildid}/commands`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            コマンド一覧
          </a>
        </nav>
        <nav className="space-y-2">
          <a
            href={`/dashboard/settings/${guildid}/join-message`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            よろしくメッセージ
          </a>
        </nav>
        <nav className="space-y-2">
          <a
            href={`/dashboard/settings/${guildid}/leave-message`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            さようならメッセージ
          </a>
        </nav>
        <nav className="space-y-2">
          <a
            href={`/dashboard/settings/${guildid}/auto-thread`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            自動スレッド作成
          </a>
        </nav>
        <nav className="space-y-2">
          <a
            href={`/dashboard/settings/${guildid}/expand`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            メッセージ展開
          </a>
        </nav>
        <nav className="space-y-2">
          <a
            href={`/dashboard/settings/${guildid}/level`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            レベル
          </a>
        </nav>
        <nav className="space-y-2">
          <a
            href={`/dashboard/settings/${guildid}/economy`}
            className="block p-2 rounded hover:bg-gray-100"
          >
            サーバー内経済
          </a>
        </nav>
      </aside>

      {/* メインコンテンツ */}
      <main className="flex-1 p-6 bg-black">{children}</main>
    </div>
  );
}