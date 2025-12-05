import { cookies } from "next/headers";
import { getGuild, getChannels } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import ToggleButton from "@/app/components/ToggleButton";

export default async function LoggingPage({ params }: { params: { guildid: string } }) {
  const events = [
    { name: "メッセージ削除", value: "message_delete" },
    { name: "メッセージ編集", value: "message_edit" },
    { name: "メンバーBAN", value: "member_ban" },
    { name: "メンバー参加", value: "member_join" },
    { name: "メンバー退出", value: "member_remove" },
    { name: "メンバー更新", value: "member_update" },
    { name: "ロール作成", value: "role_create" },
    { name: "ロール削除", value: "role_delete" },
    { name: "チャンネル作成", value: "channel_create" },
    { name: "チャンネル削除", value: "channel_delete" },
    { name: "招待リンク作成", value: "invite_create" },
    { name: "AutoModアクション", value: "automod_action" },
    { name: "VC参加", value: "vc_join" },
    { name: "VC退出", value: "vc_leave" },
    { name: "Bot導入", value: "bot_join" },
  ];

  async function sendData(formData: FormData) {
    "use server";
    const { guildid } = await params;
    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) return;

    const guild = await getGuild(sessionId, guildid);
    if (!guild) return;

    const db = await connectDB();
    const col = db.db("Main").collection("EventLoggingChannel");

    const guild_channels = await getChannels(guildid);
    const channelsData =
            Array.isArray((guild_channels as any).data)
                ? (guild_channels as any).data
                : guild_channels;

    for (const event of events) {
      const enabled = formData.get(event.value) === "true";
      const channel = formData.get("channel_" + event.value);
      const existing = await col.findOne({
        Guild: Long.fromString(guildid),
        Event: event.value,
      });

      if (enabled && channel) {
        const exists = channelsData.some((c: any) => c.id === channel);
        if (!exists) {
          console.error("チャンネルが存在しません");
          return;
        }

        const updateData: any = {
          Guild: Long.fromString(guildid),
          Channel: Long.fromString(channel as string),
          Event: event.value,
        };

        if (existing?.Webhook && existing.Webhook !== null) {
          updateData.Webhook = existing.Webhook;
        } else {
          updateData.Webhook = null;
        }

        await col.updateOne(
          { Guild: Long.fromString(guildid), Event: event.value },
          { $set: updateData },
          { upsert: true }
        );
      } else if (!enabled && existing) {
        await col.deleteOne({
          Guild: Long.fromString(guildid),
          Event: event.value,
        });
      }
    }
  }

  const { guildid } = await params;
  const cookieStore = await cookies();
  const sessionId = cookieStore.get("session_id")?.value;
  if (!sessionId) return <p>ログイン情報が見つかりません。</p>;

  const guild = await getGuild(sessionId, guildid);
  if (!guild) return <p>セッションが無効です。</p>;

  const channels = await getChannels(guildid);
  if (!channels) return <p>セッションが無効です。</p>;

  const channelsData = (() => {
        if (!channels) return null;
        if (Array.isArray((channels as any).data)) return (channels as any).data;
        if (Array.isArray(channels)) return channels as any;
        return null;
    })();

  const db = await connectDB();
  const col = db.db("Main").collection("EventLoggingChannel");
  const enabledEvents = await col
    .find({ Guild: Long.fromString(guildid) })
    .toArray();

  const enabledEventNames = enabledEvents.map((e) => e.Event);

  const eventChannelMap: Record<string, string | null> = {};
  for (const e of enabledEvents) {
    eventChannelMap[e.Event] = e.Channel?.toString() ?? null;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">{guild.name} のログ設定</h1>

      <form action={sendData} className="flex flex-col gap-5">
        <div>
          <h2 className="text-xl font-semibold text-white mt-6 mb-2 border-b border-gray-700 pb-1">
            イベント一覧
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {events.map((event, idx) => (
              <div
                key={idx}
                className="flex flex-col justify-between bg-gray-900 p-4 rounded-lg shadow-md border border-gray-700"
              >
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    {event.name}
                  </h3>
                  <p className="text-sm text-gray-400 mt-1">
                    {event.name.replace("_", " ")} のログを記録します
                  </p>

                  <p className="text-sm text-gray-400 mt-1">
                    ログ送信先チャンネル：
                  </p>

                  <select
                    name={"channel_" + event.value}
                    className="bg-gray-800 text-white p-2 rounded mt-1 w-full"
                    defaultValue={eventChannelMap[event.value] ?? ""}
                  >
                    <option value="">未選択</option>
                    {channelsData?.filter((ch: any) => ch.type === 0).map((ch: any) => (
                      <option key={ch.id} value={ch.id}>
                        {ch.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end mt-3">
                  <ToggleButton
                    name={event.value}
                    defaultValue={enabledEventNames.includes(event.value)}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          type="submit"
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 mt-4"
        >
          設定を保存
        </button>
      </form>
    </div>
  );
}