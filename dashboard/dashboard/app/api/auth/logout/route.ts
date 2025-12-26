import { NextRequest, NextResponse } from "next/server";
import { connectDB } from "@/lib/mongodb";

export async function GET(request: NextRequest) {
    const session_id = request.cookies.get("oauth_state")?.value;

    const db = await connectDB();
    await db.db("Dashboard").collection("Sessions").deleteOne({
        session_id: session_id
    })

    const redirect_url_base = "https://dashboard.sharkbot.xyz";

    const response = NextResponse.redirect(redirect_url_base);
    response.cookies.delete("session_id");
    response.cookies.delete("oauth_state");

    return response;
}