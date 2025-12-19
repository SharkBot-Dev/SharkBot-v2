import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";
import LineAndTextLayout from "@/app/components/LineAndTextLayout";
import { revalidatePath } from "next/cache";
import ItemBox from "@/app/components/ItemBox";
import ItemRow from "@/app/components/ItemRow";
import Form from "@/app/components/Form";

export default async function AutoModerationPage({ params }: { params: { guildid: string } }) {
    async function setAutoMod(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const invite = formData.get("invite") === "true" || formData.get("invite") === "on";
        const token = formData.get("token") === "true" || formData.get("token") === "on";
        const emojis = formData.get("emojis") === "true" || formData.get("emojis") === "on";

        const db = await connectDB();
        const guildFilter = { Guild: Long.fromString(guildid) };

        const invite_col = db.db("Main").collection("InviteBlock");
        if (invite) {
            await invite_col.updateOne(guildFilter, { $set: guildFilter }, { upsert: true });
        } else {
            await invite_col.deleteOne(guildFilter);
        }

        const token_col = db.db("Main").collection("TokenBlock");
        if (token) {
            await token_col.updateOne(guildFilter, { $set: guildFilter }, { upsert: true });
        } else {
            await token_col.deleteOne(guildFilter);
        }

        const automods_col = db.db("MainTwo").collection("AutoMods");

        if (emojis) {
            await automods_col.updateOne(
                guildFilter,
                { $addToSet: { AutoMods: "emojis" } },
                { upsert: true }
            );
        } else {
            await automods_col.updateOne(
                guildFilter,
                { $pull: { AutoMods: "emojis" } as any },
                { upsert: true }
            );
        }

        revalidatePath(`/dashboard/settings/${guildid}/automod`);
    }

    async function setWhiteListChannel(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("channel");
        if (!channel) return;

        const exists = channelsData.some((c: any) => c.id === channel);

        if (!exists) {
            console.error("チャンネルが存在しません");
            return;
        }

        const db = await connectDB();
        const col = db.db("Main").collection("UnBlockChannel");

        await col.updateOne(
            {
                Guild: Long.fromString(guildid),
                Channel: Long.fromString(channel as string)
            },
            {
                $set: {
                    Guild: Long.fromString(guildid),
                    Channel: Long.fromString(channel as string)
                }
            },
            { upsert: true }
        );

        revalidatePath(`/dashboard/settings/${guildid}/automod`);
    }

    async function deleteWhiteListChannel(formData: FormData) {
        "use server";

        const { guildid } = await params;
        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const guild = await getGuild(sessionId, guildid);
        if (!guild) return;

        const channel = formData.get("name");
        if (!channel) return;

        const db = await connectDB();
        const col = db.db("Main").collection("UnBlockChannel");

        await col.deleteOne({
            Guild: Long.fromString(guildid),
            Channel: Long.fromString(channel as string)
        });

        revalidatePath(`/dashboard/settings/${guildid}/automod`);
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

    if (!channelsData) return <p>チャンネルの取得失敗</p>

    const db = await connectDB();
    const inviteDoc = await db.db("Main").collection("InviteBlock").findOne({ Guild: new Long(guildid) });
    const EnabledInviteBlock = !!inviteDoc;

    const tokenDoc = await db.db("Main").collection("TokenBlock").findOne({ Guild: new Long(guildid) });
    const EnabledTokenBlock = !!tokenDoc;

    const emojisDoc = await db.db("MainTwo").collection("AutoMods").findOne({ Guild: new Long(guildid) });
    const emojiDocCheck = !!emojisDoc;

    let EnabledEmojisBlock: Boolean | undefined = undefined;

    if (emojiDocCheck) {
        if (emojisDoc.AutoMods) {
            if (emojisDoc.AutoMods.includes('emojis')) {
                EnabledEmojisBlock = true;
            } else {
                EnabledEmojisBlock = false;
            }
        } else {
            EnabledEmojisBlock = false;
        }
    } else {
        EnabledEmojisBlock = false;
    }

    const whitelist_channel = await db.db("Main").collection("UnBlockChannel").find({Guild: new Long(guildid)}).toArray();

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">{guild.name} の自動モデレート機能</h1>

            <LineAndTextLayout text="基本的な設定" />

            <Form action={setAutoMod} buttonlabel="設定を保存">
                <ItemRow>
                    <ItemBox title="招待リンクブロック">
                        <p className="text-sm text-gray-400 mt-1">自動的に招待リンク(discord.ggなど)を削除します。</p><br/>
                        <ToggleButton name="invite" defaultValue={EnabledInviteBlock} />
                    </ItemBox>

                    <ItemBox title="Tokenブロック">
                        <p className="text-sm text-gray-400 mt-1">自動的にTokenを削除します。</p><br/>
                        <ToggleButton name="token" defaultValue={EnabledTokenBlock} />
                    </ItemBox>

                    <ItemBox title="10個以上の絵文字ブロック">
                        <p className="text-sm text-gray-400 mt-1">自動的に10個以上の絵文字を削除します。</p><br/>
                        <ToggleButton name="emojis" defaultValue={EnabledEmojisBlock as boolean} />
                    </ItemBox>
                </ItemRow>
            </Form>

            <LineAndTextLayout text="ホワイトリストのチャンネル" />

            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">ホワイトリストにあるチャンネル</h2>
                {whitelist_channel.length > 0 ? (
                <ul className="border rounded divide-y divide-gray-700">
                    {whitelist_channel.map((item) => {
                    const ch = channelsData.find((ch: any) => ch.id === item.Channel.toString());
                    return (
                        <li key={item.Channel.toString()} className="p-3 flex justify-between items-center">
                        <span><strong>{ch ? ch.name : "不明なチャンネル"}</strong></span>
                        <form action={deleteWhiteListChannel}>
                            <input type="hidden" name="name" value={item.Channel.toString()} />
                            <button type="submit" className="bg-red-600 hover:bg-red-500 text-white font-semibold py-1 px-3 rounded">❌</button>
                        </form>
                        </li>
                    );
                    })}
                </ul>
                ) : <p className="text-gray-400">設定がまだありません。</p>}
            </div>

            <form action={setWhiteListChannel} className="flex flex-col gap-3">
                <select name="channel" className="border p-2 rounded bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-black-500">
                {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                    <option key={ch.id} value={ch.id}>
                    {ch.name}
                    </option>
                ))}
                </select>

                <button type="submit" className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
                    ホワイトリストに追加
                </button>
            </form>
        </div>
    );
}