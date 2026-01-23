import { cookies } from "next/headers";
import { getGuild, getLoginUser } from "@/lib/discord/fetch";
import UserInstallLayout from "@/app/components/UserInstallLayout";
import { connectDB } from "@/lib/mongodb";
import { decrypt, encrypt } from "@/lib/crypto";

function isTokenExpired(expiresAt?: Date) {
  if (!expiresAt) return true;

  const margin = 5 * 60 * 1000;
  return Date.now() + margin >= new Date(expiresAt).getTime();
}

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

    const db = await connectDB();
    const app = await db
        .db("UserInstall")
        .collection("Apps")
        .findOne({ User: user.id, AppID: appid });
    
    if (!app) return <p>アプリが見つかりません。</p>;

    if (!app.ClientSecret) return <p>サーバー側の仕様が変わったため、<br/>再度アプリの登録をお願いします。<br/>コマンドデータなどは残っています。</p>

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
            console.error("Discord OAuth Error:", res.status, await res.text());
            throw new Error("Discord token refresh failed");
        }

        const json = await res.json();

        await db.db("UserInstall").collection("Apps").updateOne(
            { User: user.id, AppID: appid },
            {
            $set: {
                Token: encrypt(json.access_token),
                TokenExpiresAt: new Date(Date.now() + json.expires_in * 1000),
            },
            }
        );
    }
    return <UserInstallLayout clientid={appid}>{children}</UserInstallLayout>
}