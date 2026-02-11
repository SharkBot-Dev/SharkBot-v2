import { redirect } from "next/navigation";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";

type PageProps = {
  params: { guildid: string };
};

export default async function ServerRedirectPage({ params }: PageProps) {
    const { guildid } = await params;

    const db = await connectDB();
    const cp = db.db("Main").collection("Register");

    const doc = await cp.findOne({
        Guild: Long.fromString(guildid)
    })

    let inviteUrl: string | null = null;

    try {
        if (doc?.Invite) {
            inviteUrl = doc.Invite;
        }
    } catch (e) {}

    if (inviteUrl) {
        redirect(inviteUrl);
    } else {
        redirect("/servers");
    }
}