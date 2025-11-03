import { NextRequest, NextResponse } from "next/server";
import { connectDB } from "@/lib/mongodb";
import { randomUUID } from "crypto";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const code = searchParams.get("code");

  const redirect_url_base = "https://dashboard.sharkbot.xyz";

  if (!code) return NextResponse.redirect(`${redirect_url_base}/`);

  const tokenData = new URLSearchParams({
    client_id: process.env.DISCORD_CLIENT_ID!,
    client_secret: process.env.DISCORD_CLIENT_SECRET!,
    grant_type: "authorization_code",
    code,
    redirect_uri: process.env.DISCORD_REDIRECT_URI!,
  });

  const tokenResponse = await fetch("https://discord.com/api/oauth2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: tokenData,
  });

  const token = await tokenResponse.json();
  if (!token.access_token) return NextResponse.redirect(new URL("/error", request.url));

  const userRes = await fetch("https://discord.com/api/users/@me", {
    headers: { Authorization: `${token.token_type} ${token.access_token}` },
  });
  const user = await userRes.json();

  const guildRes = await fetch("https://discord.com/api/users/@me/guilds", {
    headers: { Authorization: `${token.token_type} ${token.access_token}` },
  });
  const guilds = await guildRes.json();

  const db = await connectDB();
  const sessionId = randomUUID();

  await db.db("Dashboard").collection("Sessions").insertOne({
    session_id: sessionId,
    user,
    guilds,
    createdAt: new Date(),
  });

  const origin = request.nextUrl.origin;
  const response = NextResponse.redirect(`${redirect_url_base}/dashboard`);
  response.cookies.set("session_id", sessionId, {
    path: "/",
    httpOnly: true,
    sameSite: "lax",
    maxAge: 60 * 60 * 24,
  });

  return response;
}