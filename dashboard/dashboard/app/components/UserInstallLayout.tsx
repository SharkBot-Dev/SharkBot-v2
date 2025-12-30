"use client";

import { useState, useEffect } from "react";
import LineAndtextLayout from "@/app/components/LineAndTextLayout";
import Badge from "./Badge";

export default function ClientLayout({
  children,
  clientid,
}: {
  children: React.ReactNode;
  clientid: string;
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
          <a href={`/dashboard/userinstall/`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🦈アプリを選ぶ
          </a>
          <a href={`/dashboard/userinstall/${clientid}`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🏠ホーム
          </a>
          <a href={`/dashboard/userinstall/${clientid}/commands`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            💬コマンド作成
          </a>
          <a href={`/dashboard/userinstall/${clientid}/buttons`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🔳ボタン作成
          </a>
          <a href={`/dashboard/userinstall/${clientid}/modal`} className="block p-2 rounded hover:bg-gray-700 text-gray-200">
            🖊️モーダル作成
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