"use client";

import { useState, useEffect } from "react";
import LineAndtextLayout from "@/app/components/LineAndTextLayout";
import Badge from "./Badge";

export default function ClientLayout({
  children,
  guildid,
}: {
  children: React.ReactNode;
  guildid: string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (window.innerWidth >= 768) setIsOpen(true);
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-100 text-white">

      <aside
        className={`fixed top-0 left-0 h-screen bg-black border-r border-gray-800 p-4 overflow-y-auto 
        transform transition-transform duration-300 ease-in-out
        w-64 z-40
        ${isOpen ? "translate-x-0" : "-translate-x-full"}
        md:translate-x-0 md:w-64`}
      >
        <h1 className="text-2xl mt-3 ml-10">SharkBot</h1>

        <nav className="space-y-2 mt-6">
          <a href={`/dashboard/`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🦈サーバー選択
          </a>
          <a href={`/dashboard/settings/${guildid}`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🏠ホーム
          </a>

          <a href={`/dashboard/settings/${guildid}/alert`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            📢通知
          </a>
          <a href={`/dashboard/settings/${guildid}/commands`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            💬コマンド一覧
          </a>

          <LineAndtextLayout text="サーバー管理" />

          <a href={`/dashboard/settings/${guildid}/join-message`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🤝よろしくメッセージ
          </a>
          <a href={`/dashboard/settings/${guildid}/leave-message`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            👋さようならメッセージ
          </a>
          <a href={`/dashboard/settings/${guildid}/automod`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🤖自動モデレート <Badge text="NEW" color="bg-green-600" />
          </a>
          <a href={`/dashboard/settings/${guildid}/moderation`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🔨モデレーション
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
          <a href={`/dashboard/settings/${guildid}/tags`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🏷️カスタムコマンド
          </a>
          <a href={`/dashboard/settings/${guildid}/report`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🔔サーバー内通報
          </a>
          <a href={`/dashboard/settings/${guildid}/logging`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🪵ログ
          </a>

          <LineAndtextLayout text="ツール" />

          <a href={`/dashboard/settings/${guildid}/embed`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🟫埋め込み作成
          </a>
          <a href={`/dashboard/settings/${guildid}/lockmessage`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            📌固定メッセージ
          </a>
          <a href={`/dashboard/settings/${guildid}/timer`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            ⏲️タイマー
          </a>
          <a href={`/dashboard/settings/${guildid}/expand`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            💬メッセージ展開
          </a>
          <a href={`/dashboard/settings/${guildid}/poll`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🗳️投票
          </a>
          <a href={`/dashboard/settings/${guildid}/translate`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🔠翻訳
          </a>
          <a href={`/dashboard/settings/${guildid}/search`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🔎なんでも検索
          </a>

          <LineAndtextLayout text="面白い・楽しい" />

          <a href={`/dashboard/settings/${guildid}/level`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🏆レベル
          </a>
          <a href={`/dashboard/settings/${guildid}/achievement`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🏅サーバー内実績 <Badge text="NEW" color="bg-green-600" />
          </a>
          <a href={`/dashboard/settings/${guildid}/economy`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🪙サーバー内経済
          </a>
          <a href={`/dashboard/settings/${guildid}/starboard`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            ⭐スターボード
          </a>
          <a href={`/dashboard/settings/${guildid}/count`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            💯カウントゲーム
          </a>
          <a href={`/dashboard/settings/${guildid}/music`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🎵音楽 <Badge text="NEW" color="bg-green-600" />
          </a>
          <a href={`/dashboard/settings/${guildid}/dice`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🎲ダイス
          </a>
        </nav>
      </aside>

      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 bg-gray-800 p-2 rounded-md hover:bg-gray-700 transition z-50 md:hidden"
      >
        {isOpen ? "❌" : "☰"}
      </button>

      <main
        className={`flex-1 p-6 bg-black min-h-screen transition-all duration-300
          ${isOpen ? "md:ml-64" : "md:ml-64"}`}
      >
        {children}
      </main>
    </div>
  );
}