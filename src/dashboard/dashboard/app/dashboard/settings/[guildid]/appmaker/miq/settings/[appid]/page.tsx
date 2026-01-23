import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { connectDB } from "@/lib/mongodb";
import { getLoginUser } from "@/lib/discord/fetch";
import { decrypt, encrypt } from "@/lib/crypto";

export const runtime = "nodejs";

type PageProps = {
  params: { guildid: string, appid: string };
};

function isTokenExpired(expiresAt?: Date) {
  if (!expiresAt) return true;

  const margin = 5 * 60 * 1000;
  return Date.now() + margin >= new Date(expiresAt).getTime();
}

export default async function MiqMainPage({ params }: PageProps) {
    const { appid } = await params;

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return <p>ログイン情報がありません。</p>;

    const user = await getLoginUser(sessionId);
    if (!user) return <p>ログイン情報がありません。</p>;

    const db = await connectDB();
    const app = await db
        .db("UserInstall")
        .collection("MiqApps")
        .findOne({ User: user.id, AppID: appid });

    if (!app) return <p>アプリが見つかりません。</p>;

    if (isTokenExpired(app.TokenExpiresAt)) {
        const body = new URLSearchParams({
            grant_type: "client_credentials",
            scope: "applications.commands.update identify",
        });

        const res = await fetch("https://discord.com/api/v10/oauth2/token", {
            method: "POST",
            headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            Authorization:
                "Basic " +
                Buffer.from(
                `${appid}:${decrypt(app.ClientSecret)}`
                ).toString("base64"),
            },
            body,
            cache: "no-store",
        });

        if (!res.ok) {
            return <p>致命的なエラーが出ました。</p>;
        }

        const json = await res.json();

        await db.db("UserInstall").collection("MiqApps").updateOne(
            { User: user.id, AppID: appid },
            {
                $set: {
                    Token: encrypt(json.access_token),
                    TokenExpiresAt: new Date(Date.now() + json.expires_in * 1000),
                },
            }
        );
    }

    return (
        <div className="p-6 space-y-6 max-w-xl">
        <h1 className="text-2xl font-bold">
            ダッシュボード（App ID: {appid}）
        </h1>

        <div className="border rounded p-3 flex justify-between items-center">
            注意！<br/>
            このサービスを使ってコマンドを実行する際には、<br/>
            以下のURLを、「Interactions Endpoint URL」に<br/>登録する必要があります。<br/>
            {`https://dashboard.sharkbot.xyz/api/apps/miq/${appid}`}<br/>
        </div>
        </div>
    );
}
