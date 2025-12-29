import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { connectDB } from "@/lib/mongodb";
import { getLoginUser } from "@/lib/discord/fetch";
import { decrypt } from "@/lib/crypto";

export const runtime = "nodejs";

type PageProps = {
  params: { appid: string };
};

export default async function CommandsPage({ params }: PageProps) {
  const { appid } = await params;

  const cookieStore = await cookies();
  const sessionId = cookieStore.get("session_id")?.value;
  if (!sessionId) return <p>ログイン情報がありません。</p>;

  const user = await getLoginUser(sessionId);
  if (!user) return <p>ログイン情報がありません。</p>;

  const db = await connectDB();
  const app = await db
    .db("UserInstall")
    .collection("Apps")
    .findOne({ User: user.id, AppID: appid });

  if (!app) return <p>アプリが見つかりません。</p>;

  return (
    <div className="p-6 space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold">
        ダッシュボード（App ID: {appid}）
      </h1>

      <div className="border rounded p-3 flex justify-between items-center">
        注意！<br/>
        このサービスを使ってコマンドを実行する際には、<br/>
        以下のURLを、「Interactions Endpoint URL」に<br/>登録する必要があります。<br/>
        {`https://dashboard.sharkbot.xyz/api/usi/${appid}`}<br/>
      </div>
    </div>
  );
}
