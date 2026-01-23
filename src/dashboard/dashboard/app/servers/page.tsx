import { connectDB } from "@/lib/mongodb";

export const revalidate = 60;

export default async function ServersPage() {
  const db = await connectDB();
  const cp = db.db("Main").collection("Register");

  const pipeline = [
    {
      $addFields: {
        has_up: {
          $cond: [{ $ifNull: ["$Up", false] }, 1, 0],
        },
      },
    },
    {
      $sort: {
        has_up: -1,
        Up: -1,
      },
    },
  ];

  const servers = await cp.aggregate(pipeline).toArray();

  return (
    <main className="px-4 py-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-center">
        Discordサーバー掲示板
      </h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {servers.map((server: any) => (
          <div
            key={server._id.toString()}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-3 shadow-md"
          >
            <div className="flex items-center gap-3">
              <img
                src={server.Icon}
                alt=""
                className="w-12 h-12 rounded-full bg-zinc-700"
              />
              <div className="flex-1">
                <h2 className="font-semibold text-lg leading-tight">
                  {server.Name}
                </h2>
              </div>
            </div>

            <p className="text-sm text-zinc-300 line-clamp-3">
              {server.Description || "説明はありません"}
            </p>

            <a
              href={server.Invite}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-auto text-center bg-indigo-600 hover:bg-indigo-500 transition rounded-lg py-2 text-sm font-medium"
            >
              サーバーに参加
            </a>
          </div>
        ))}
      </div>
    </main>
  );
}
