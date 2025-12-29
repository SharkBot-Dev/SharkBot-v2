import { NextResponse } from "next/server";
import {
  InteractionType,
  InteractionResponseType,
  verifyKey,
} from "discord-interactions";
import { connectDB } from "@/lib/mongodb";
import { buttonsToComponents } from "@/lib/discord/buttons";

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
    .collection("Apps")
    .findOne({ AppID: clientid });

  if (!app?.PublicKey) {
    return new NextResponse("Invalid application", { status: 401 });
  }

  const isValidRequest = await verifyKey(
    rawBody,
    signature,
    timestamp,
    app.PublicKey
  );

  if (!isValidRequest) {
    return new NextResponse("Invalid request signature", { status: 401 });
  }

  const interaction = JSON.parse(rawBody);

  if (interaction.type === InteractionType.PING) {
    return NextResponse.json({
      type: InteractionResponseType.PONG,
    });
  }

  if (interaction.type === InteractionType.APPLICATION_COMMAND) {
    const commandName = interaction.data.name;

    const command = await db
      .db("UserInstall")
      .collection("Commands")
      .findOne({
        name: commandName,
        AppID: clientid,
      });

    if (!command) {
      return NextResponse.json({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: {
          content: "このコマンドは無効化されています。",
          flags: 64,
        },
      });
    }

    const components = buttonsToComponents(command.Buttons);

    return NextResponse.json({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: {
            content: command.replyText,
            components,
        },
    });
  } else if (interaction.type === InteractionType.MESSAGE_COMPONENT) {
    const button = await db
    .db("UserInstall")
    .collection("Buttons")
    .findOne({
        AppID: clientid,
        customid: interaction.data.custom_id,
    });

    if (!button) return NextResponse.json(
        { error: "Error." },
        { status: 400 }
    );

    return NextResponse.json({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: {
            content: button.replyText,
            flags: 64,
        },
    });
  }

  return NextResponse.json(
    { error: "Unknown interaction type" },
    { status: 400 }
  );
}
