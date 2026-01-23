import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { connectDB } from "@/lib/mongodb";
import { getLoginUser } from "@/lib/discord/fetch";
import { decrypt } from "@/lib/crypto";
import { revalidatePath } from "next/cache";
import CreateModal from "./CreateModal";

export const runtime = "nodejs";

type PageProps = {
  params: { appid: string };
};

const cooldowns = new Map<string, number>();

export default async function ModalsPage({ params }: PageProps) {
    const { appid } = await params;

    async function createCommand(formData: FormData) {
        "use server";

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const user = await getLoginUser(sessionId);
        if (!user) return;

        const title = formData.get("title")?.toString();
        const customid = formData.get("cid")?.toString();
        const replyText = formData.get("replytext")?.toString();

        if (!title || !customid || !replyText) return;

        const inputs = [];

        for (let i = 1; i <= 5; i++) {
            const label = formData.get(`input${i}`)?.toString();
            const cid = formData.get(`customid${i}`)?.toString();

            if (!label || !cid) continue;

            inputs.push({
            label,
            customid: cid,
            style: 1, // SHORT
            required: i === 1,
            });
        }

        if (inputs.length === 0) return;

        const db = await connectDB();

        await db.db("UserInstall").collection("Modals").updateOne(
            {
            User: user.id,
            AppID: appid,
            customid,
            },
            {
            $set: {
                User: user.id,
                AppID: appid,
                customid,
                title,
                replyText,
                inputs,
                disabled: false,
            },
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/userinstall/${appid}/modals`);
    }

    async function deleteCommand(formData: FormData) {
    "use server";

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return;

    const user = await getLoginUser(sessionId);
    if (!user) return;

    const customid = formData.get("customid")?.toString();
    if (!customid) return;

    const db = await connectDB();

    await db.db("UserInstall").collection("Modals").deleteOne({
        User: user.id,
        AppID: appid,
        customid,
    });

    revalidatePath(`/dashboard/userinstall/${appid}/modals`);
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

    const modals = await db
    .db("UserInstall")
    .collection("Modals")
    .find({ User: user.id, AppID: appid })
    .toArray();

    return (
        <div className="p-6 space-y-6 max-w-xl">
            <h1 className="text-2xl font-bold">
                モーダル登録（App ID: {appid}）
            </h1>

            <ul className="space-y-2">
                {modals.map((m) => (
                    <li
                    key={m._id.toString()}
                    className="border rounded p-3 flex justify-between items-center"
                    >
                    <div>
                        <p className="font-mono text-sm">{m.title}</p>
                        <p className="text-xs text-gray-500">{m.customid}</p>
                    </div>

                    <form action={deleteCommand}>
                        <input type="hidden" name="customid" value={m.customid} />
                        <button className="bg-red-600 text-white px-3 py-1 rounded text-sm">
                        削除
                        </button>
                    </form>
                    </li>
                ))}
            </ul>

            <CreateModal createCommand={createCommand}></CreateModal>
        </div>
    );
}
