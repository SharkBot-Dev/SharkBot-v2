import { cookies } from "next/headers";
import { getLoginUser } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long } from "mongodb";
import RankCardBuilder from "./RankCardBuilder";

export default async function RankCardEditPage() {
    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;
    if (!sessionId) {
        return <p>ログイン情報が見つかりません。</p>;
    }

    async function setRankColor(formData: FormData) {
        "use server";

        const cookieStore = await cookies();
        const sessionId = cookieStore.get("session_id")?.value;
        if (!sessionId) return;

        const loginuser = await getLoginUser(sessionId);
        if (!loginuser) {
            return;
        }

        const color = formData.get("selected_color");
        if (!color) return;

        const db = await connectDB();

        await db.db("Main").collection("RankColor").updateOne(
            { User: new Long(loginuser.id) },
            { $set: { Color: color } },
            { upsert: true }
        );

        return;
    }

    const loginuser = await getLoginUser(sessionId);
    if (!loginuser) {
        return <p>ログイン情報が見つかりません。</p>;
    }

    const db = await connectDB();
    const find = await db.db("Main").collection("RankColor").findOne({
        User: new Long(loginuser.id)
    })

    let color = "gray";
    if (find) {
        color = find.Color;
    }

    return (
        <RankCardBuilder initialData={{
            username: loginuser.username,
            level: 1,
            xp: 1,
            avatarUrl: `https://cdn.discordapp.com/avatars/${loginuser.id}/${loginuser.avatar}.png`,
            color: color
        }} action={setRankColor}></RankCardBuilder>
    );
}