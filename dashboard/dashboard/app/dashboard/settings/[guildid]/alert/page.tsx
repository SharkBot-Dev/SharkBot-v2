import { cookies } from "next/headers";
import { getGuild } from "@/lib/discord/fetch";
import { connectDB } from "@/lib/mongodb";
import { Long, ObjectId } from "mongodb";

type AlertDoc = {
    _id: ObjectId;
    Title: string;
    Content?: string;
    CreatedAt?: Date;
};

export default async function AlertPage({
    params,
}: {
    params: { guildid: string };
}) {
    const { guildid } = await params;

    const cookieStore = await cookies();
    const sessionId = cookieStore.get("session_id")?.value;

    if (!sessionId) {
        return (
            <div className="p-6 text-red-400">
                ログイン情報が見つかりません。
            </div>
        );
    }

    const guild = await getGuild(sessionId, guildid);
    if (!guild) {
        return (
            <div className="p-6 text-red-400">
                セッションが無効です。
            </div>
        );
    }

    const db = await connectDB();
    const alerts = (await db
        .db("DashboardBot")
        .collection<AlertDoc>("Alert")
        .find({ Guild: Long.fromString(guildid) })
        .sort({ CreatedAt: -1 })
        .toArray()) ?? [];

    return (
        <div className="p-4">
            <h1 className="text-3xl font-bold mb-6 text-white">
                {guild.name} の通知
            </h1>

            {alerts.length === 0 && (
                <p className="text-gray-400">
                    通知はまだありません。
                </p>
            )}

            <div className="space-y-4">
                {alerts.map((alert) => (
                    <div
                        key={alert._id.toString()}
                        className="rounded-lg border border-gray-700 bg-gray-900 p-4"
                    >
                        <div className="flex justify-between items-center mb-2">
                            <h2 className="text-lg font-semibold text-white">
                                {alert.Title}
                            </h2>

                            {alert.CreatedAt && (
                                <span className="text-sm text-gray-400">
                                    {new Date(alert.CreatedAt).toLocaleString()}
                                </span>
                            )}
                        </div>

                        {alert.Content && (
                            <p className="text-gray-300 whitespace-pre-wrap">
                                {alert.Content}
                            </p>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
