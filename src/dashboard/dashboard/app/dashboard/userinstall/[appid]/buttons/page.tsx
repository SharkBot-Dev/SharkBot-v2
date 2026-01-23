import { cookies } from "next/headers";
import { connectDB } from "@/lib/mongodb";
import { getLoginUser } from "@/lib/discord/fetch";
import { revalidatePath } from "next/cache";

export const runtime = "nodejs";

type PageProps = {
  params: { appid: string };
};

const cooldowns = new Map<string, number>();

export default async function ButtonsPage({ params }: PageProps) {
  const { appid } = await params;

  async function createCommand(formData: FormData) {
    "use server";

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return;

    const user = await getLoginUser(sessionId);
    if (!user) return;

    const label = formData.get("label")?.toString();
    const customid = formData.get("customid")?.toString() || undefined;
    const url = formData.get("url")?.toString() || undefined;
    const style = Number(formData.get("style"));
    const replyText = formData.get("replytext")?.toString();

    if (!label || !replyText) return;
    if (![1, 2, 3, 4, 5].includes(style)) return;

    if (style === 5 && !url) return;
    if (style !== 5 && !customid) return;

    const db = await connectDB();
    const app = await db
        .db("UserInstall")
        .collection("Apps")
        .findOne({ User: user.id, AppID: appid });

    if (!app) return;

    const query =
        style === 5
        ? { User: user.id, AppID: appid, url }
        : { User: user.id, AppID: appid, customid };

    await db
        .db("UserInstall")
        .collection("Buttons")
        .updateOne(
        query,
        {
            $set: {
            User: user.id,
            AppID: appid,
            style,
            label,
            customid: style === 5 ? undefined : customid,
            url: style === 5 ? url : undefined,
            replyText,
            disabled: false,
            },
        },
        { upsert: true }
        );

    revalidatePath(`/dashboard/userinstall/${appid}/buttons`);
  }

  async function deleteCommand(formData: FormData) {
    "use server";

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return;

    const user = await getLoginUser(sessionId);
    if (!user) return;

    const customid = formData.get("customid")?.toString() || undefined;
    const url = formData.get("url")?.toString() || undefined;

    if (!customid && !url) return;

    const db = await connectDB();

    await db
        .db("UserInstall")
        .collection("Buttons")
        .deleteOne({
        User: user.id,
        AppID: appid,
        ...(customid ? { customid } : { url }),
        });

    revalidatePath(`/dashboard/userinstall/${appid}/buttons`);
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

  const buttons = await db
    .db("UserInstall")
    .collection("Buttons")
    .find({ User: user.id, AppID: appid }).toArray();

  return (
    <div className="p-6 space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold">
        ボタン登録（App ID: {appid}）
      </h1>

      <ul className="space-y-2">
        {buttons.map((cmd) => (
        <li
            key={cmd._id.toString()}
            className="border rounded p-3 flex justify-between items-center"
        >
            <div>
            <p className="font-mono text-sm">{cmd.label}</p>
            <p className="text-xs text-gray-500">
                {cmd.style === 5 ? cmd.url : cmd.customid}
            </p>
            </div>

            <form action={deleteCommand}>
            {cmd.customid && (
                <input type="hidden" name="customid" value={cmd.customid} />
            )}
            {cmd.url && (
                <input type="hidden" name="url" value={cmd.url} />
            )}
            <button className="bg-red-600 text-white px-3 py-1 rounded text-sm">
                削除
            </button>
            </form>
        </li>
        ))}
      </ul>

      <form action={createCommand} className="space-y-4">
        <div>
            <label>スタイル</label>
            <select name="style"  className="border p-2 w-full" required>
                <option value="1">Primary</option>
                <option value="2">Secondary</option>
                <option value="3">Success</option>
                <option value="4">Danger</option>
                <option value="5">Link (URL)</option>
            </select>
        </div>

        <div>
            <label>ラベル</label>
            <input name="label" className="border p-2 w-full"  required />
        </div>

        <div>
            <label>カスタムID（Link以外）</label>
            <input className="border p-2 w-full" name="customid" />
        </div>

        <div>
            <label>URL（Linkのみ）</label>
            <input className="border p-2 w-full" name="url" />
        </div>

        <span className="font-semibold mb-1">返信する内容</span>
        <textarea name="replytext" required className="border p-2 w-full" />

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
