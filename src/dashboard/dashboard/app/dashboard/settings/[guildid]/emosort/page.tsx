import { cookies } from "next/headers";
import { getGuild, fetchEmojis } from "@/lib/discord/fetch";
import { sendEmojiSort } from "./Action";
import { EmojiToggle } from "@/app/components/EmojiToggle";

function hasPrefix(name: string) {
  return /^\d{2}_/.test(name);
}

export default async function EmoSortPage({
  params
}: {
  params: { guildid: string };
}) {
  const { guildid } = await params;

  const cookieStore =await cookies();
  const sessionId = cookieStore.get("session_id")?.value;
  if (!sessionId) {
    return <p>ログイン情報が見つかりません。</p>;
  }

  const guild = await getGuild(sessionId, guildid);
  if (!guild) {
    return <p>セッションが無効です。</p>;
  }

  const emojis = await fetchEmojis(guildid);
  if (!emojis) {
    return <p>サーバーの絵文字を取得できませんでした。</p>;
  }
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">
        {guild.name} の絵文字の順序上げ
      </h1>

      <h3>有効にした絵文字の順序が上がります。</h3>
      <h6>※ このページは常に最新ではありません。<br/>※ 反映には10秒のクールダウンがあります。</h6>

      <form action={sendEmojiSort.bind(null, guildid)} className="space-y-2">
        {emojis.data.map(e => (
          <label key={e.id} className="flex items-center gap-3">
            <EmojiToggle
              emojiId={e.id as string}
              defaultOn={hasPrefix(e.name as string)}
            />

            <img
              src={`https://cdn.discordapp.com/emojis/${e.id}.${e.animated ? "gif" : "png"}`}
              alt={e.name as string}
              width={32}
              height={32}
            />

            <span>{e.name}</span>
          </label>
        ))}

        <button
          type="submit"
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
        >
          選択した絵文字を上にする
        </button>
      </form>
    </div>
  );
}
