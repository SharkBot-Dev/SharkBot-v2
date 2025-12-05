import { NextResponse } from "next/server";
import { randomUUID } from "crypto";

export async function GET() {
    const state = randomUUID();

    const redirect_url = new URL("https://discord.com/oauth2/authorize");
    redirect_url.searchParams.set("client_id", process.env.DISCORD_CLIENT_ID!);
    redirect_url.searchParams.set("redirect_uri", process.env.DISCORD_REDIRECT_URI!);
    redirect_url.searchParams.set("response_type", "code");
    redirect_url.searchParams.set("scope", "identify guilds");
    redirect_url.searchParams.set("state", state);

    const res = NextResponse.redirect(redirect_url.toString());
    res.cookies.set("oauth_state", state, {
        path: "/",
        httpOnly: true,
        sameSite: "lax",
        secure: true,
        maxAge: 60 * 5,
    });

    return res;
}