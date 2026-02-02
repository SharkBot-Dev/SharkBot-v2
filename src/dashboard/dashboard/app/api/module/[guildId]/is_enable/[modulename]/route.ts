import { NextResponse } from "next/server";
import { getGuild } from "@/lib/discord/fetch";
import { cookies } from "next/headers";
import { is_enabled } from "@/lib/modules";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ guildId: string, modulename: string }> }
) {
  const { guildId, modulename } = await params;

  const cookieStore = await cookies();
  const sessionId = cookieStore.get("session_id")?.value;

  if (!sessionId) {
    return NextResponse.json({
      error: "ログイン情報が見つかりません。"
    })
  }

  const guild = await getGuild(sessionId, guildId);
  if (!guild) {
    return NextResponse.json({
      error: "ログイン情報が見つかりません。"
    })
  }

  const is_enable = await is_enabled(guildId, modulename);

  return NextResponse.json({
    enabled: is_enable,
    name: modulename
  })
}