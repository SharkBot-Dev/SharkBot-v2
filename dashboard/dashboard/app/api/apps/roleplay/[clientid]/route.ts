import { NextResponse } from "next/server";
import {
  InteractionType,
  InteractionResponseType,
  verifyKey,
} from "discord-interactions";
import { connectDB } from "@/lib/mongodb";
import { decrypt } from "@/lib/crypto";
import { is_cooldown } from "@/lib/ai_cooldown";

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
    .collection("RolePlayApps")
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

  if (interaction.type === InteractionType.APPLICATION_COMMAND) {
    const userId = interaction.member?.user?.id || interaction.user?.id;
    const is_c = await is_cooldown(userId, "roleplay", 3000);

    if (!is_c) {
      return NextResponse.json({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: {
          content: "AIには、3秒間のクールダウンがあります。",
          flags: 64,
        }
      });
    }

    const processGemini = async () => {
      try {
        const MODEL_NAME = "gemma-3-27b-it"; 
        const apiKey = decrypt(app.GeminiAPIKey);
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL_NAME}:generateContent?key=${apiKey}`;
        
        const prompt = `# Roleplay Settings
${app.Prompt}

以下は、ユーザーからの会話です。
${interaction.data.options[0].value}`;

        const geminiRes = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }]
          }),
        });

        const data = await geminiRes.json();
        const generatedText = data.candidates?.[0]?.content?.parts?.[0]?.text || "応答を生成できませんでした。";

        await fetch(
          `https://discord.com/api/v10/webhooks/${clientid}/${interaction.token}/messages/@original`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content: generatedText,
            }),
          }
        );
      } catch (error) {
        console.error("Error processing Gemini/Discord:", error);
        await fetch(
          `https://discord.com/api/v10/webhooks/${clientid}/${interaction.token}/messages/@original`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content: "応答を生成できませんでした。",
            }),
          }
        );
      }
    };

    processGemini();

    return NextResponse.json({
      type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
    });
  }

  return NextResponse.json({ error: "Unhandled interaction" }, { status: 400 });
}