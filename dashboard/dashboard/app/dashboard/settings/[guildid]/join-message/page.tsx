import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import Form from "@/app/components/Form";

export default async function JoinMessagePage({ params }: { params: { guildid: string } }) {
    async function sendData(formData: FormData) {
        "use server";

        const { guildid } = await params;

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const checkenable = formData.get("checkenable") === "true" || formData.get("checkenable") === "on";

        const db = await connectDB();

        const guild_channels = await getChannels(guildid);

        const channelsData = (() => {
            if (!guild_channels) return null;
            if (Array.isArray((guild_channels as any).data)) return (guild_channels as any).data;
            if (Array.isArray(guild_channels)) return guild_channels as any;
            return null;
        })();

        if (!checkenable) {
            await db.db("Main").collection("WelcomeMessage").deleteOne({ Guild: Long.fromString(guildid) });
            return;
        }

        const title = (formData.get("title") as string)?.slice(0, 100);
        const desc = (formData.get("desc") as string)?.slice(0, 500);
        const channel = formData.get("channel") as string;

        if (!title || !desc || !channel) return;

        const exists = channelsData.some((c: any) => c.id === channel);

        if (!exists) {
            return;
        }

        await db.db("Main").collection("WelcomeMessage").updateOne(
            { Guild: new Long(guildid), Channel: new Long(channel) },
            {
                $set: {
                    Guild: new Long(guildid),
                    Title: title,
                    Description: desc,
                    Channel: new Long(channel),
                    UpdatedAt: new Date(),
                },
            },
            { upsert: true }
        );
    }

    const { guildid } = await params;

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) {
        return <p>ログイン情報が見つかりません。</p>;
    }

    const guild = await getGuild(sessionId, guildid);
    if (!guild) {
        return <p>セッションが無効です。</p>;
    }

    const guild_channels = await getChannels(guildid);

    const channelsData = (() => {
        if (!guild_channels) return null;
        if (Array.isArray((guild_channels as any).data)) return (guild_channels as any).data;
        if (Array.isArray(guild_channels)) return guild_channels as any;
        return null;
    })();

    if (!channelsData) return <p>サーバーのチャンネルを取得できませんでした。</p>;

    const db = await connectDB();
    const find_setting = await db.db("Main").collection("WelcomeMessage").findOne({Guild: new Long(guildid)});

    let title: string | undefined = undefined;
    let desc: string | undefined = undefined;

    const enabled = !!find_setting;

    if (find_setting != null) {

        title = find_setting.Title;
        desc = find_setting.Description;

        if (!title) {
            title = '<name> さん、よろしく！'
        }

        if (!desc) {
            desc = 'あなたは <count> 人目のメンバーです！';
        }
    }

    return (
        <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">{guild.name} のよろしくメッセージ</h1>

        <Form action={sendData} buttonlabel="設定する">
            <span className="font-semibold mb-1">機能を有効にする</span>
            <ToggleButton name="checkenable" defaultValue={enabled} />

            <span className="font-semibold mb-1">タイトル</span>
            <input
            type="text"
            name="title"
            className="border p-2"
            placeholder="タイトル"
            defaultValue={title}
            />
            <span className="font-semibold mb-1">説明</span>
            <textarea
            name="desc"
            className="border p-2"
            placeholder="説明"
            defaultValue={desc}
            />

            <span className="font-semibold mb-1">送信先チャンネル</span>
            <select name="channel" className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500">
            {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                <option key={ch.id} value={ch.id}>
                {ch.name}
                </option>
            ))}
            </select>

            <span className="font-semibold mb-1">使える関数</span>
            <div className="flex flex-col gap-3 bg-gray-900 p-4 rounded-lg shadow">
                {"<name> .. 名前を埋め込みます。"}<br/>
                {"<count> .. 現在の人数を埋め込みます。"}<br/>
                {"<guild> .. サーバーの名前を埋め込みます。"}<br/>
                {"<createdat> .. アカウント作成日を埋め込みます。"}<br/>
            </div>
        </Form>
        </div>
    );
}