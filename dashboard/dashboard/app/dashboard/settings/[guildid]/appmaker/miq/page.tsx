import { getLoginUser } from "@/lib/discord/fetch";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { connectDB } from "@/lib/mongodb";
import { encrypt } from "@/lib/crypto";

export const runtime = "nodejs";

const cooldowns = new Map<string, number>();

export default async function UserInstallMiq({
    params,
}: {
    params: { guildid: string };
}) {
    const { guildid } = await params;
    
    async function createNewApp(formData: FormData) {
        "use server";

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const user = await getLoginUser(sessionId);
        if (!user) return;

        const cid = formData.get("cid")?.toString();
        const csc = formData.get("csc")?.toString();
        const pubk = formData.get("pubk")?.toString();
        if (!cid || !csc || !pubk) return;

        const now = Date.now();
        const lastTime = cooldowns.get(sessionId) ?? 0;
        if (now - lastTime < 10_000) return;
        cooldowns.set(sessionId, now);

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
                Buffer.from(`${cid}:${csc}`).toString("base64"),
            },
            body,
            cache: "no-store",
        });

        if (!res.ok) {
            console.error("Discord OAuth Error:", res.status, await res.text());
            return;
        }

        const json = await res.json();

        const expiresAt = new Date(Date.now() + json.expires_in * 1000);

        const db = await connectDB();
        await db
        .db("UserInstall")
        .collection("MiqApps")
        .updateOne(
            { User: user.id, AppID: cid },
            {
            $set: {
                User: user.id,
                AppID: cid,
                Token: encrypt(json.access_token),
                ClientSecret: encrypt(csc),
                PublicKey: pubk,
                UpdatedAt: new Date(),
                TokenExpiresAt: expiresAt
            },
            $setOnInsert: {
                CreatedAt: new Date(),
            },
            },
            { upsert: true }
        );

        const response = await fetch(`https://discord.com/api/v10/applications/${cid}/commands`, {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${json.access_token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify([
            {
              name: "Make it a quote",
              type: 3,
            }
          ]),
        });

        redirect(`/dashboard/settings/${guildid}/appmaker/miq/settings/${cid}`);
    }

    async function deleteApp(formData: FormData) {
        "use server";

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const user = await getLoginUser(sessionId);
        if (!user) return;

        const appId = formData.get("appid")?.toString();
        if (!appId) return;

        const db = await connectDB();
        await db
            .db("UserInstall")
            .collection("MiqApps")
            .deleteOne({
                User: user.id,
                AppID: appId,
            });

        redirect(`/dashboard/settings/${guildid}/appmaker/miq/`);
    }

  const cookieStore = await cookies();
  const sessionId = cookieStore.get("session_id")?.value;
  if (!sessionId) {
    return <p>ログイン情報が見つかりません。</p>;
  }

  const user = await getLoginUser(sessionId);
  if (!user) {
    return <p>ログイン情報が見つかりません。</p>;
  }

  const db = await connectDB();
  const apps = await db
    .db("UserInstall")
    .collection("MiqApps")
    .find({ User: user.id })
    .sort({ CreatedAt: -1 })
    .toArray();

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-2xl font-bold">
        {user.username} のMiqBot
      </h1>

      <form action={createNewApp} className="space-y-3 max-w-md">
        <div>
          <span className="font-semibold">Client ID</span>
          <input
            name="cid"
            placeholder="Client ID"
            className="border p-2 w-full"
            required
          />
        </div>

        <div>
          <span className="font-semibold">Client シークレット</span>
          <input
            name="csc"
            placeholder="Client Secret"
            type="password"
            className="border p-2 w-full"
            required
          />
        </div>

        <div>
          <span className="font-semibold">Public Key</span>
          <input
            name="pubk"
            placeholder="Public Key"
            type="password"
            className="border p-2 w-full"
            required
          />
        </div>

        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          登録
        </button>
      </form>

      <div>
        <h2 className="text-xl font-semibold mb-2">登録済みMiqアプリ</h2>

        {apps.length === 0 ? (
          <p className="text-gray-500">まだアプリが登録されていません。</p>
        ) : (
          <ul className="space-y-2">
            {apps.map((app) => (
              <li
                key={app._id.toString()}
                className="border rounded p-3 flex justify-between items-center"
              >
                <a href={`/dashboard/settings/${guildid}/appmaker/miq/settings/${app.AppID}`}><div>
                  <p className="font-mono text-sm">
                    App ID: {app.AppID}
                  </p>
                  <p className="text-xs text-gray-500">
                    登録日:{" "}
                    {app.CreatedAt
                      ? new Date(app.CreatedAt).toLocaleString()
                      : "不明"}
                  </p>
                </div></a>

                <form action={deleteApp}>
                    <input
                    type="hidden"
                    name="appid"
                    value={app.AppID}
                    />
                    <button
                    type="submit"
                    className="bg-red-600 text-white px-3 py-1 rounded text-sm"
                    >
                    削除
                    </button>
                </form>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}