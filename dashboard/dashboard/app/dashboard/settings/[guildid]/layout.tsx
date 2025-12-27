import { cookies } from "next/headers";
import { getGuild } from "@/lib/discord/fetch";
import ClientLayout from "@/app/components/ClientLayout";
import ToastProvider from "@/app/components/ToastProvider";
import ToastContainer from "@/app/components/ToastContainer";

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

  if (!guild) {
    return <p className="text-center text-red-400 mt-10">セッションが無効です。</p>;
  }

  return <ClientLayout guildid={guildid}><ToastProvider>
    <ToastContainer />
    {children}
  </ToastProvider></ClientLayout>
}