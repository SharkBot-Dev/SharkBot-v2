import { NextResponse } from "next/server";
import {
  InteractionType,
  InteractionResponseType,
  verifyKey,
} from "discord-interactions";
import { connectDB } from "@/lib/mongodb";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ clientid: string }> }
) {
  const { clientid } = await params;
  const signature = req.headers.get("X-Signature-Ed25519");
  const timestamp = req.headers.get("X-Signature-Timestamp");

  if (!signature || !timestamp) {
    return new NextResponse("Missing signature headers", { status: 401 });
  }

  const rawBody = await req.text();
  const db = await connectDB();
  const app = await db
    .db("UserInstall")
    .collection("MiqApps")
    .findOne({ AppID: clientid });

  if (!app?.PublicKey) {
    return new NextResponse("Invalid application", { status: 401 });
  }

  const isValidRequest = await verifyKey(rawBody, signature, timestamp, app.PublicKey);
  if (!isValidRequest) {
    return new NextResponse("Invalid request signature", { status: 401 });
  }

  const interaction = JSON.parse(rawBody);

  if (interaction.type === InteractionType.PING) {
    return NextResponse.json({ type: InteractionResponseType.PONG });
  }

  if (
    interaction.type === InteractionType.APPLICATION_COMMAND &&
    interaction.data.type === 3
  ) {
    const targetId = interaction.data.target_id;
    const messageData = interaction.data.resolved.messages[targetId];
    const author = messageData.author;

    const avatarUrl = `https://cdn.discordapp.com/avatars/${author.id}/${author.avatar}.png`

    const interactionToken = interaction.token;

    (async () => {
      try {
        const payload = {
          username: author.username,
          display_name: author.global_name || author.username,
          text: messageData.content || "",
          avatar: avatarUrl,
          color: true,
        };

        const fakeQuoteRes = await fetch("https://api.voids.top/fakequote", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const result = await fakeQuoteRes.json();
        const imageUrl = result.url;

        if (!imageUrl) throw new Error("画像URLの取得に失敗しました。");

        const imageResponse = await fetch(imageUrl);
        const imageBlob = await imageResponse.blob();

        const formData = new FormData();
        formData.append("files[0]", imageBlob, "quote.png");

        await fetch(
          `https://discord.com/api/v10/webhooks/${clientid}/${interactionToken}/messages/@original`,
          {
            method: "PATCH",
            body: formData,
          }
        );

      } catch (error) {}
    })();

    return NextResponse.json({
      type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
    });
  }

  return NextResponse.json({ error: "Unhandled interaction" }, { status: 400 });
}