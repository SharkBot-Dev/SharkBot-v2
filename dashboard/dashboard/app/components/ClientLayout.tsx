"use client";

import { useState } from "react";

export default function ClientLayout({
  children,
  guildid,
}: {
  children: React.ReactNode;
  guildid: string;
}) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex min-h-screen bg-gray-100 text-white">
      {/* サイドバー */}
      <aside
        className={`fixed top-0 left-0 h-screen bg-black border-r border-gray-800 p-4 overflow-y-auto transform transition-transform duration-300 ease-in-out
        ${isOpen ? "translate-x-0 w-64" : "-translate-x-full w-64"}`}
      >
        {/* ロゴを少し右に寄せる */}
        <h1 className="text-2xl mt-3 ml-10">SharkBot</h1>

        <nav className="space-y-2 mt-6">
          <a href={`/dashboard/`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🦈サーバー選択
          </a>
          <a href={`/dashboard/settings/${guildid}`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🏠ホーム
          </a>
          <a href={`/dashboard/settings/${guildid}/commands`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            💬コマンド一覧
          </a>
          <a href={`/dashboard/settings/${guildid}/join-message`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🤝よろしくメッセージ
          </a>
          <a href={`/dashboard/settings/${guildid}/leave-message`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            👋さようならメッセージ
          </a>
          <a href={`/dashboard/settings/${guildid}/rolepanel`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🧙ロールパネル
          </a>
          <a href={`/dashboard/settings/${guildid}/auth`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            ✅認証
          </a>
          <a href={`/dashboard/settings/${guildid}/ticket`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🎫チケット
          </a>
          <a href={`/dashboard/settings/${guildid}/auto-thread`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            📖自動スレッド作成
          </a>
          <a href={`/dashboard/settings/${guildid}/autoreply`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🚗自動返信
          </a>
          <a href={`/dashboard/settings/${guildid}/autoreact`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            😆自動リアクション
          </a>
          <a href={`/dashboard/settings/${guildid}/expand`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            💬メッセージ展開
          </a>
          <a href={`/dashboard/settings/${guildid}/embed`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🟫埋め込み作成
          </a>
          <a href={`/dashboard/settings/${guildid}/poll`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🗳️投票
          </a>
          <a href={`/dashboard/settings/${guildid}/translate`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🔠翻訳
          </a>
          <a href={`/dashboard/settings/${guildid}/logging`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🪵ログ
          </a>
          <a href={`/dashboard/settings/${guildid}/level`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🏆レベル
          </a>
          <a href={`/dashboard/settings/${guildid}/economy`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🪙サーバー内経済
          </a>
          <a href={`/dashboard/settings/${guildid}/starboard`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            ⭐スターボード
          </a>
          <a href={`/dashboard/settings/${guildid}/search`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🔎なんでも検索
          </a>
          <a href={`/dashboard/settings/${guildid}/music`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🎵音楽
          </a>
          <a href={`/dashboard/settings/${guildid}/dice`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🎲ダイス
          </a>
        </nav>
      </aside>

      {/* ハンバーガーボタン */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 bg-gray-800 p-2 rounded-md hover:bg-gray-700 transition"
        style={{ zIndex: 100 }}
      >
        {isOpen ? "❌" : "☰"}
      </button>

      {/* メイン */}
      <main
        className={`flex-1 p-6 bg-black min-h-screen transition-all duration-300 ${
          isOpen ? "ml-64" : "ml-0"
        }`}
      >
        {children}
      </main>
    </div>
  );
}