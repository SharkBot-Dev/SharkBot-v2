import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { connectDB } from "@/lib/mongodb";
import { getLoginUser } from "@/lib/discord/fetch";
import { decrypt } from "@/lib/crypto";
import { revalidatePath } from "next/cache";

export const runtime = "nodejs";

type PageProps = {
  params: { appid: string };
};

const cooldowns = new Map<string, number>();

export default async function CommandsPage({ params }: PageProps) {
  const { appid } = await params;

  async function createCommand(formData: FormData) {
    "use server";

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return;

    const user = await getLoginUser(sessionId);
    if (!user) return;

    const name = formData.get("name")?.toString();
    const description = formData.get("description")?.toString();
    const replyText = formData.get("replytext")?.toString();
    if (!name || !description || !replyText) return;

    const db = await connectDB();
    const app = await db
      .db("UserInstall")
      .collection("Apps")
      .findOne({ User: user.id, AppID: appid });

    if (!app) return;

    const now = Date.now();
    const lastTime = cooldowns.get(sessionId) ?? 0;
    if (now - lastTime < 3000) return;
    cooldowns.set(sessionId, now);

    const token = decrypt(app.Token);

    const res = await fetch(
      `https://discord.com/api/v10/applications/${appid}/commands`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          description,
          type: 1,
        }),
      }
    );

    if (!res.ok) {
      return;
    }

    const json = await res.json()

    await db
      .db("UserInstall")
      .collection("Commands").updateOne({
        commandId: json.id
      }, {$set: {
        commandId: json.id,
        replyText: replyText,
        name: name,
        AppID: appid
      }}, {
        upsert: true
      })

    revalidatePath(`/dashboard/userinstall/${appid}/commands`);
  }

  async function deleteCommand(formData: FormData) {
    "use server";

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return;

    const user = await getLoginUser(sessionId);
    if (!user) return;

    const commandId = formData.get("command_id")?.toString();
    if (!commandId) return;

    const db = await connectDB();
    const app = await db
      .db("UserInstall")
      .collection("Apps")
      .findOne({ User: user.id, AppID: appid });

    if (!app) return;

    const now = Date.now();
    const lastTime = cooldowns.get(sessionId) ?? 0;
    if (now - lastTime < 3000) return;
    cooldowns.set(sessionId, now);
    
    const token = decrypt(app.Token);

    const res = await fetch(
      `https://discord.com/api/v10/applications/${appid}/commands/${commandId}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!res.ok) {
      return;
    }

    await db
      .db("UserInstall")
      .collection("Commands")
      .deleteOne({
        commandId: commandId, AppID: appid
      })

    revalidatePath(`/dashboard/userinstall/${appid}/commands`);
  }

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

  const token = decrypt(app.Token);

  const commandsRes = await fetch(
    `https://discord.com/api/v10/applications/${appid}/commands`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      next: {
        revalidate: 60,
      },
    }
  );

  let commands: any[] = [];
  if (commandsRes.ok) {
    commands = await commandsRes.json();
  } else {
    console.error(
      "Fetch commands error",
      commandsRes.status,
      await commandsRes.text()
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold">
        コマンド登録（App ID: {appid}）
      </h1>

      <ul className="space-y-2">
        {commands.map((cmd) => (
          <li
            key={cmd.id}
            className="border rounded p-3 flex justify-between items-center"
          >
            <div>
              <p className="font-mono text-sm">
                /{cmd.name}
              </p>
              <p className="text-xs text-gray-600">
                {cmd.description || "説明なし"}
              </p>
            </div>

            <form action={deleteCommand}>
              <input
                type="hidden"
                name="command_id"
                value={cmd.id}
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

      <form action={createCommand} className="space-y-4">
        <div>
          <label className="font-semibold">コマンド名</label>
          <input
            name="name"
            placeholder="ping"
            className="border p-2 w-full"
            required
          />
        </div>

        <div>
          <label className="font-semibold">説明</label>
          <input
            name="description"
            placeholder="Botの応答を確認します"
            className="border p-2 w-full"
            required
          />
        </div>

        <div>
          <label className="font-semibold">返信内容</label>
          <textarea
            name="replytext"
            placeholder="Botの応答を確認します"
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
    </div>
  );
}
