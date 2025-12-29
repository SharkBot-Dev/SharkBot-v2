import { cookies } from "next/headers";
import { getGuild, getLoginUser } from "@/lib/discord/fetch";
import ClientLayout from "@/app/components/ClientLayout";
import ToastProvider from "@/app/components/ToastProvider";
import ToastContainer from "@/app/components/ToastContainer";
import UserInstallLayout from "@/app/components/UserInstallLayout";

export default async function GuildLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: any;
}) {
  const { appid } = await params;

  const cookieStore = await cookies();
  const sessionId = cookieStore.get("session_id")?.value;
  if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

  const user = await getLoginUser(sessionId);
  if (!user) return <p>ログイン情報がありません。</p>;

  return <UserInstallLayout clientid={appid}>{children}</UserInstallLayout>
}