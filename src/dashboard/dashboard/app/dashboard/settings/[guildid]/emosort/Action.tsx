"use server";

import { cookies } from "next/headers";
import { fetchEmojis, getGuild, renameEmoji } from "@/lib/discord/fetch";
import sleep from "@/lib/sleep";

const cooldowns = new Map<string, number>();

function stripPrefix(name: string) {
  return name.replace(/^\d{2}_/, "");
}

export async function sendEmojiSort(
  guildid: string,
  formData: FormData
) {
  const cookieStore = await cookies();
  const sessionId = cookieStore.get("session_id")?.value;
  if (!sessionId) return;

  const guild = await getGuild(sessionId, guildid);
  if (!guild) return;
  
  const now = Date.now();
  const lastTime = cooldowns.get(sessionId) ?? 0;
  const cooldownMs = 10 * 1000;

  if (now - lastTime < cooldownMs) {
    return;
  }
  cooldowns.set(sessionId, now);

  const selectedIds = new Set(
    formData.getAll("emoji") as string[]
  );

  const emojis = await fetchEmojis(guildid);
  if (!emojis) return;

  let index = 1;

  for (const emoji of emojis.data) {
    const baseName = stripPrefix(emoji.name as string);
    const isSelected = selectedIds.has(emoji.id as string);

    if (isSelected) {
      const newName =
        `${String(index).padStart(2, "0")}_${baseName}`;

      if (emoji.name !== newName) {
        await renameEmoji(guildid, emoji.id as string, newName);
        await sleep(500);
      }

      index++;
      continue;
    }

    if (emoji.name !== baseName) {
      await renameEmoji(guildid, emoji.id as string, baseName);
      await sleep(500);
    }
  }
}